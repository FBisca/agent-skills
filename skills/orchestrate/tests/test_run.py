"""The dispatch loop against a fake agent-runtime, a temp git repo with an origin, and a temp plan."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "orchestrate.py"

FAKE_RUNTIME = '''#!/usr/bin/env python3
"""Records every call; spawn answers a canned worker, wait pops the next scripted answer."""
import json, os, sys
home = os.environ["FAKE_RUNTIME_HOME"]
argv = sys.argv[1:]
tool = argv[1]
lead = argv[argv.index("--lead") + 1] if "--lead" in argv else None
args = json.loads(argv[argv.index("--json") + 1]) if "--json" in argv else {}
with open(os.path.join(home, "calls.jsonl"), "a") as log:
    log.write(json.dumps({"tool": tool, "lead": lead, "args": args}) + "\\n")
if tool == "spawn":
    if args["name"] in json.load(open(os.path.join(home, "refuse.json"))):
        print(json.dumps({"content": [{"type": "text", "text": "name_taken"}], "isError": True}))
        sys.exit(1)
    print(json.dumps({"name": args["name"], "address": "term-" + args["name"], "parent": "driver",
                      "assignment_id": "a-" + args["name"]}))
elif tool == "wait":
    queue_path = os.path.join(home, "waits.json")
    queue = json.load(open(queue_path))
    step = queue.pop(0) if queue else {}
    json.dump(queue, open(queue_path, "w"))
    for path, old, new in step.pop("replace", []):
        text = open(path).read()
        assert old in text, old
        open(path, "w").write(text.replace(old, new, 1))
    print(json.dumps(dict({"reason": "empty", "reports": [], "unfinished": []}, **step)))
else:
    print(json.dumps({}))
'''

HEADER = """# Plan: demo

Slug: `demo`. Living spec: `docs/specs/demo.md`. Status: {status} 2026-11-06.

## Decisions

| # | Choice |
|---|---|
| D1 | keep it small |

## Scenarios

- **S1** WHEN a THEN b.
- **S2** WHEN c THEN d.
- **S3** WHEN e THEN f.

## Seams

- the CLI.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
"""

ROWS = {
    "T1": "| T1 | first | S1 | none | src/a/ | small | simple | agent | TO-DO |",
    "T2": "| T2 | second | S2 | T1 | src/b/ | regular | complex | agent | TO-DO |",
    "T3": "| T3 | third | S3 | none | src/c/ | regular | simple | agent | TO-DO |",
    "T4": "| T4 | sign-off | none | none | | | | Felippe | TO-DO |",
    "T5": "| T5 | fifth | S1 | none | src/e/ | small | complex | agent | TO-DO |",
}


def plan_text(rows=("T1", "T2", "T3", "T4", "T5"), status="APPROVED"):
    return HEADER.format(status=status) + "\n".join(ROWS[r] for r in rows) + "\n"


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.origin = self.root / "origin.git"
        self.repo = self.root / "repo"
        self.git(self.root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(self.root, "init", "-q", "-b", "main", str(self.repo))
        self.git(self.repo, "remote", "add", "origin", str(self.origin))
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "fixture")
        self.git(self.repo, "push", "-q", "origin", "main")
        self.base = self.git(self.repo, "rev-parse", "HEAD")
        self.plan = self.repo / "docs" / "plans" / "demo.plan.md"
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text(plan_text(), encoding="utf-8")
        self.state_dir = self.root / "state"
        self.home = self.root / "fake"
        self.home.mkdir()
        fake = self.home / "agent-runtime"
        fake.write_text(FAKE_RUNTIME, encoding="utf-8")
        fake.chmod(0o755)
        self.refuse([])
        self.waits([])
        models = self.root / "CLAUDE.md"
        models.write_text("## Model classes\n\n| Class | Claude | Codex |\n|---|---|---|\n"
                          "| small | `model: \"haiku\"` | `gpt-s` |\n| medium | `model: \"sonnet\"` | `gpt-m` |\n"
                          "| large | `model: \"opus\"` | `gpt-l` |\n", encoding="utf-8")
        self.models = models

    def git(self, cwd, *args):
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def refuse(self, names):
        (self.home / "refuse.json").write_text(json.dumps(names), encoding="utf-8")

    def waits(self, steps):
        (self.home / "waits.json").write_text(json.dumps(steps), encoding="utf-8")

    def calls(self, tool=None):
        path = self.home / "calls.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return [r for r in rows if tool in (None, r["tool"])]

    def run_driver(self, *extra, plan=None, expect=0):
        env = dict(os.environ, PATH=str(self.home) + os.pathsep + os.environ["PATH"],
                   FAKE_RUNTIME_HOME=str(self.home))
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "run", str(plan or self.plan), "--state-dir", str(self.state_dir),
             "--models-file", str(self.models), "--wait-seconds", "1", *extra],
            capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def ledger(self):
        return json.loads((self.state_dir / "demo.json").read_text(encoding="utf-8"))

    def test_S1_dispatches_ready_agent_tickets_up_to_the_cap(self):
        """code-driven-orchestrator/S1"""
        self.run_driver("--max-workers", "2")
        spawns = self.calls("spawn")
        self.assertEqual([c["args"]["name"] for c in spawns], ["demo-t1", "demo-t3"])
        first = spawns[0]["args"]
        self.assertEqual((first["kind"], first["cli"], first["model"], first["effort"]), ("worker", "claude", "haiku", "low"))
        second = spawns[1]["args"]
        self.assertEqual((second["model"], second["effort"]), ("sonnet", "medium"))
        run_dir = self.state_dir / "demo"
        self.assertEqual(first["task"], "Read %s and follow it." % (run_dir / "t1" / "task.md"))
        worktree = Path(first["cwd"])
        self.assertEqual(self.git(worktree, "rev-parse", "HEAD"), self.base)
        self.assertEqual(self.git(worktree, "branch", "--show-current"), "feat/demo-t1")
        task_md = (run_dir / "t1" / "task.md").read_text(encoding="utf-8")
        for needle in ("contract.md", str(run_dir / "t1" / "report.json"), "S1", "WHEN a THEN b.",
                       "red-first", "src/a/", str(worktree), "feat/demo-t1"):
            self.assertIn(needle, task_md)
        tasks = self.ledger()["tasks"]
        self.assertEqual(set(tasks), {"t1", "t3"})
        self.assertEqual((tasks["t1"]["status"], tasks["t1"]["runtime_id"]), ("ACTIVE", "term-demo-t1"))
        self.assertEqual((tasks["t1"]["packet"]["class"], tasks["t1"]["packet"]["unit"]), ("small", "t1"))
        self.assertEqual(tasks["t1"]["packet"]["owns"], ["src/a/"])

    def test_S1_worktree_branches_from_the_fetched_origin_main(self):
        """code-driven-orchestrator/S1"""
        other = self.root / "other"
        self.git(self.root, "clone", "-q", str(self.origin), str(other))
        (other / "new.txt").write_text("remote\n", encoding="utf-8")
        self.git(other, "add", ".")
        self.git(other, "-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "remote")
        self.git(other, "push", "-q", "origin", "main")
        remote_head = self.git(other, "rev-parse", "HEAD")
        (self.repo / "local.txt").write_text("local\n", encoding="utf-8")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "local")
        self.assertNotEqual(self.git(self.repo, "rev-parse", "origin/main"), remote_head)
        self.plan.write_text(plan_text(rows=("T1",)), encoding="utf-8")
        self.run_driver()
        worktree = Path(self.calls("spawn")[0]["args"]["cwd"])
        self.assertEqual(self.git(worktree, "rev-parse", "HEAD"), remote_head)
        self.assertTrue((worktree / "new.txt").exists())
        self.assertFalse((worktree / "local.txt").exists())

    def test_S1_long_slug_gets_a_valid_worker_name_ending_in_the_ticket(self):
        """code-driven-orchestrator/S1"""
        slug = "parallel-wait-and-cli-profiles"
        self.assertEqual(len(slug), 30)
        self.plan.write_text(plan_text(rows=("T1", "T3")).replace("`demo`", "`%s`" % slug), encoding="utf-8")
        self.run_driver()
        names = [c["args"]["name"] for c in self.calls("spawn")]
        self.assertEqual(len(names), 2)
        for name, ticket in zip(names, ("t1", "t3")):
            self.assertRegex(name, r"^[a-z0-9][a-z0-9_-]{0,31}$")
            self.assertTrue(name.endswith("-" + ticket), name)
            self.assertTrue(name.startswith("parallel-wait-and-cli-profil"), name)
        self.assertEqual(importlib_load().worker_name("a" * 27 + "-bcd", 12), "a" * 27 + "-t12")

    def test_S1_default_cap_is_three(self):
        """code-driven-orchestrator/S1"""
        self.run_driver()
        self.assertEqual([c["args"]["name"] for c in self.calls("spawn")], ["demo-t1", "demo-t3", "demo-t5"])

    def test_S1_codex_backend_picks_the_codex_model(self):
        """code-driven-orchestrator/S1"""
        self.run_driver("--cli", "codex")
        first = self.calls("spawn")[0]["args"]
        self.assertEqual((first["cli"], first["model"]), ("codex", "gpt-s"))

    def test_S2_unapproved_plan_exits_2_and_spawns_nothing(self):
        """code-driven-orchestrator/S2"""
        self.plan.write_text(plan_text(status="DRAFT"), encoding="utf-8")
        result = self.run_driver(expect=2)
        self.assertIn("APPROVED", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.state_dir / "demo.json").exists())

    def test_S2_missing_field_names_the_ticket_and_field(self):
        """code-driven-orchestrator/S2"""
        broken = plan_text().replace("| src/a/ | small |", "| src/a/ | |")
        self.plan.write_text(broken, encoding="utf-8")
        result = self.run_driver(expect=2)
        self.assertIn("T1", result.stderr)
        self.assertIn("Size", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_S2_unknown_scenario_and_missing_table_exit_2(self):
        """code-driven-orchestrator/S2"""
        self.plan.write_text(plan_text().replace("| S1 | none |", "| S9 | none |"), encoding="utf-8")
        self.assertIn("S9", self.run_driver(expect=2).stderr)
        self.plan.write_text("# Plan\n\nSlug: `demo`. Status: APPROVED.\n", encoding="utf-8")
        self.assertIn("Tickets", self.run_driver(expect=2).stderr)
        self.assertEqual(self.calls(), [])

    def test_S3_dispatch_changes_only_the_status_cell_of_dispatched_rows(self):
        """code-driven-orchestrator/S3"""
        before = self.plan.read_text(encoding="utf-8").splitlines()
        self.run_driver("--max-workers", "2")
        after = self.plan.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(before), len(after))
        changed = {b: a for b, a in zip(before, after) if a != b}
        self.assertEqual(changed, {ROWS["T1"]: ROWS["T1"].replace("TO-DO", "IN PROGRESS"),
                                   ROWS["T3"]: ROWS["T3"].replace("TO-DO", "IN PROGRESS")})

    def test_S3_pause_and_complete_write_one_row_too(self):
        """code-driven-orchestrator/S3"""
        spec = importlib_load()
        for status in ("IN PROGRESS · needs you: pick a name", "COMPLETE 2026-11-07"):
            before = self.plan.read_text(encoding="utf-8").splitlines()
            spec.set_status(self.plan, "T2", status)
            after = self.plan.read_text(encoding="utf-8").splitlines()
            diff = [(b, a) for b, a in zip(before, after) if a != b]
            self.assertEqual(len(before), len(after))
            self.assertEqual(len(diff), 1)
            self.assertTrue(diff[0][1].startswith("| T2 | second | S2 | T1 | src/b/ | regular | complex | agent | " + status))

    def test_S4_next_iteration_acts_on_the_edited_plan(self):
        """code-driven-orchestrator/S4"""
        self.plan.write_text(plan_text(rows=("T1", "T2")), encoding="utf-8")
        new_row = ROWS["T3"].replace("| T3 | third", "| T6 | sixth")
        self.waits([{"reason": "timeout", "unfinished": ["demo-t1"],
                     "replace": [[str(self.plan), "| T1 | first | S1 | none | src/a/ | small | simple | agent | IN PROGRESS |",
                                  "| T1 | first | S1 | none | src/a/ | small | simple | agent | COMPLETE 2026-11-07 |\n" + new_row]]},
                    {"reason": "empty", "unfinished": []}])
        self.run_driver()
        self.assertEqual(sorted(c["args"]["name"] for c in self.calls("spawn")), ["demo-t1", "demo-t2", "demo-t6"])
        self.assertEqual(len(self.calls("wait")), 2)

    def test_S14_restart_reuses_the_lead_and_spawns_nothing_bound(self):
        """code-driven-orchestrator/S14"""
        self.run_driver()
        first_calls = len(self.calls("spawn"))
        self.assertEqual(self.ledger()["lead"], "orchestrate:demo")
        self.assertTrue(all(c["lead"] == "orchestrate:demo" for c in self.calls()))
        data = self.ledger()
        data["lead"] = "orchestrate:stored"
        (self.state_dir / "demo.json").write_text(json.dumps(data), encoding="utf-8")
        self.plan.write_text(self.plan.read_text(encoding="utf-8").replace("IN PROGRESS", "TO-DO"), encoding="utf-8")
        self.calls_reset = len(self.calls())
        self.run_driver()
        self.assertEqual(len(self.calls("spawn")), first_calls)
        later = self.calls()[self.calls_reset:]
        self.assertTrue(later and all(c["lead"] == "orchestrate:stored" for c in later))
        self.assertIn("wait", [c["tool"] for c in later])

    def test_S14_restart_with_status_reset_to_todo_does_not_respawn_a_bound_ticket(self):
        """code-driven-orchestrator/S14"""
        self.run_driver("--max-workers", "1")
        self.plan.write_text(self.plan.read_text(encoding="utf-8").replace("IN PROGRESS", "TO-DO"), encoding="utf-8")
        self.run_driver("--max-workers", "1")
        names = [c["args"]["name"] for c in self.calls("spawn")]
        self.assertEqual(names.count("demo-t1"), 1)

    def test_a_refused_spawn_keeps_the_reservation_and_exits_1(self):
        """code-driven-orchestrator/S14"""
        self.refuse(["demo-t1"])
        self.plan.write_text(plan_text(rows=("T1",)), encoding="utf-8")
        result = self.run_driver(expect=1)
        self.assertIn("T1 not dispatched", result.stderr)
        self.assertEqual(self.ledger()["tasks"]["t1"]["status"], "RESERVED")
        self.assertIn("TO-DO", self.plan.read_text(encoding="utf-8"))
        self.refuse([])
        self.run_driver()
        self.assertEqual(self.ledger()["tasks"]["t1"]["status"], "ACTIVE")


def importlib_load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("orchestrate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
