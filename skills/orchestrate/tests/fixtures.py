"""Shared fixtures for the driver tests: a fake agent-runtime, a temp git repo with an origin, a temp plan."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "orchestrate.py"

FAKE_RUNTIME = '''#!/usr/bin/env python3
"""Records every call; spawn answers a canned worker, wait pops the next scripted answer."""
import json, os, subprocess, sys
home = os.environ["FAKE_RUNTIME_HOME"]
argv = sys.argv[1:]
tool = argv[1]
lead = argv[argv.index("--lead") + 1] if "--lead" in argv else None
args = json.loads(argv[argv.index("--json") + 1]) if "--json" in argv else {}
with open(os.path.join(home, "calls.jsonl"), "a") as log:
    log.write(json.dumps({"tool": tool, "lead": lead, "args": args}) + "\\n")
rows = [json.loads(line) for line in open(os.path.join(home, "calls.jsonl"))]
nth = sum(1 for r in rows if r["tool"] == tool and r["args"].get("name") == args.get("name"))
if tool == "spawn":
    if args["name"] in json.load(open(os.path.join(home, "refuse.json"))):
        print(json.dumps({"content": [{"type": "text", "text": "name_taken"}], "isError": True}))
        sys.exit(1)
    print(json.dumps({"worker_id": "w-" + args["name"], "assignment_id": "a-%s%s" % (args["name"], "" if nth == 1 else "-%d" % nth),
                      "name": args["name"], "address": "term-" + args["name"], "parent": "driver"}))
elif tool == "wait":
    queue_path = os.path.join(home, "waits.json")
    queue = json.load(open(queue_path))
    step = queue.pop(0) if queue else {}
    json.dump(queue, open(queue_path, "w"))
    for path, text in step.pop("write", []):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(text)
    for path, old, new in step.pop("replace", []):
        text = open(path).read()
        assert old in text, old
        open(path, "w").write(text.replace(old, new, 1))
    for argv in step.pop("run", []):
        subprocess.run(argv, check=True, capture_output=True)
    print(json.dumps(dict({"reason": "empty", "reports": [], "unfinished": []}, **step)))
elif tool == "status":
    states = json.load(open(os.path.join(home, "states.json")))
    state = states.get(args["name"], "idle")
    if state == "error":
        sys.exit(1)
    print(json.dumps({"name": args["name"], "state": state}))
elif tool == "stop":
    print(json.dumps({"name": args["name"], "state": "exited"}))
elif tool == "resume":
    print(json.dumps({"worker_id": "w-" + args["name"], "assignment_id": "r%d-%s" % (nth, args["name"]),
                      "name": args["name"], "address": "term-" + args["name"], "parent": "driver"}))
else:
    print(json.dumps({}))
'''

FAKE_WAIT_CHECKS = '''#!/usr/bin/env python3
"""Logs its argument; answers from checks.json: a list of [exit code, stdout], popped per call (last one repeats)."""
import json, os, sys
home = os.environ["FAKE_RUNTIME_HOME"]
with open(os.path.join(home, "wait-checks.log"), "a") as log:
    log.write(sys.argv[1] + "\\n")
queue = json.load(open(os.path.join(home, "checks.json")))
code, out = queue.pop(0) if len(queue) > 1 else queue[0]
json.dump(queue, open(os.path.join(home, "checks.json"), "w"))
print(out)
sys.exit(code)
'''

FAKE_GH = '''#!/usr/bin/env python3
"""`gh pr view`: logs the plan as it stands at each call, answers the next PR state from prs.json (last repeats)."""
import json, os, sys
home = os.environ["FAKE_RUNTIME_HOME"]
with open(os.path.join(home, "gh.log"), "a") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "plan": open(os.environ["FAKE_PLAN"]).read()}) + "\\n")
queue = json.load(open(os.path.join(home, "prs.json")))
state = queue.pop(0) if len(queue) > 1 else queue[0]
json.dump(queue, open(os.path.join(home, "prs.json"), "w"))
print(json.dumps({"state": state, "mergeCommit": {"oid": "f" * 40} if state == "MERGED" else None}))
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


# ---- the real shapes of `wait` (agent-runtime server/dispatch_wait.py, dispatch_store.py) ---------------------------
# A result is {reason, messages, assignments, unfinished: [assignment_id], receipt, more}. An assignment entry is
# {assignment_id, worker_id, state: working|complete|blocked|decision|failed, name}, plus `runtime_state`
# (idle|done|unreported|error|...) when `wait` observed the terminal. A message envelope has no name: {message_id,
# team_id, worker_id, assignment_id, sender, recipient, kind: progress|complete|blocked|decision|failed, text}.

MESSAGES = iter(range(1, 10**6))
TURN_ENDED = ("idle", "done")
NEEDS_PERSON = ("unreported", "error")


def spawn_id(name, nth=1):
    """The assignment id the fake runtime gives the nth spawn of `name`."""
    return "a-" + name + ("" if nth == 1 else "-%d" % nth)


def resume_id(name, nth=1):
    """The assignment id the fake runtime gives the nth resume of `name`."""
    return "r%d-%s" % (nth, name)


def assignment(name, state="working", runtime_state=None, id=None):
    entry = {"assignment_id": id or spawn_id(name), "worker_id": "w-" + name, "state": state, "name": name}
    if runtime_state:
        entry["runtime_state"] = runtime_state
    return entry


def envelope(assignment_entry, kind, text=None):
    return {"message_id": "m%d" % next(MESSAGES), "team_id": "team", "worker_id": assignment_entry["worker_id"],
            "assignment_id": assignment_entry["assignment_id"], "sender": assignment_entry["worker_id"],
            "recipient": "lead", "kind": kind, "text": text or "%s - see run directory" % kind.upper()}


def wait_result(assignments=(), messages=(), write=(), replace=(), reason=None):
    """What `wait(all)` answers, with `reason` derived the way the runtime does unless given."""
    assignments = [dict(a) for a in assignments]
    unfinished = [a["assignment_id"] for a in assignments if a["state"] != "complete"]
    states = {a["state"] for a in assignments}
    ended = any(a["state"] == "working" and a.get("runtime_state") in TURN_ENDED + NEEDS_PERSON for a in assignments)
    if reason is None:
        if not assignments:
            reason = "messages" if messages else "empty"
        elif "failed" in states:
            reason = "failed"
        elif ended or states & {"blocked", "decision"}:
            reason = "attention"
        elif not unfinished:
            reason = "completed"
        else:
            reason = "messages" if messages else "timeout"
    step = {"reason": reason, "messages": list(messages), "assignments": assignments, "unfinished": unfinished,
            "receipt": "r%d" % next(MESSAGES), "more": False}
    if write:
        step["write"] = [list(w) for w in write]
    if replace:
        step["replace"] = [list(r) for r in replace]
    return step


def report_wait(name, kind="complete", text=None, id=None, **extra):
    """An agent reports `kind`: its assignment takes the matching state and the envelope names it by id."""
    entry = assignment(name, kind if kind in ("complete", "blocked", "decision", "failed") else "working", id=id)
    return wait_result([entry], [envelope(entry, kind, text)], **extra)


def plan_text(rows=("T1", "T2", "T3", "T4", "T5"), status="APPROVED"):
    return HEADER.format(status=status) + "\n".join(ROWS[r] for r in rows) + "\n"


class RunFixture:
    """Mixin for TestCase classes: temp repo with an origin, a plan, a fake agent-runtime on PATH."""

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
        for name, body in (("wait-checks", FAKE_WAIT_CHECKS), ("gh", FAKE_GH)):
            tool = self.home / name
            tool.write_text(body, encoding="utf-8")
            tool.chmod(0o755)
        self.checks([[0, "PASS o/r#7"]])
        self.prs(["MERGED"])
        self.refuse([])
        self.waits([])
        self.states({})
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

    def checks(self, answers):
        (self.home / "checks.json").write_text(json.dumps(answers), encoding="utf-8")

    def prs(self, states):
        (self.home / "prs.json").write_text(json.dumps(states), encoding="utf-8")

    def gh_log(self):
        path = self.home / "gh.log"
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def wait_checks_log(self):
        path = self.home / "wait-checks.log"
        return path.read_text(encoding="utf-8").split() if path.exists() else []

    def states(self, mapping):
        (self.home / "states.json").write_text(json.dumps(mapping), encoding="utf-8")

    def waits(self, steps):
        (self.home / "waits.json").write_text(json.dumps(steps), encoding="utf-8")

    def calls(self, tool=None):
        path = self.home / "calls.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return [r for r in rows if tool in (None, r["tool"])]

    def run_driver(self, *extra, plan=None, expect=0):
        env = dict(os.environ, PATH=str(self.home) + os.pathsep + os.environ["PATH"],
                   FAKE_RUNTIME_HOME=str(self.home), FAKE_PLAN=str(self.plan))
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "run", str(plan or self.plan), "--state-dir", str(self.state_dir),
             "--models-file", str(self.models), "--wait-seconds", "1", "--idle-interval", "0", *extra],
            capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def ledger(self):
        return json.loads((self.state_dir / "demo.json").read_text(encoding="utf-8"))


def load_script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("orchestrate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
