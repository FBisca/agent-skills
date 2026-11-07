"""Shared fixtures for the driver tests: a fake agent-runtime, a temp git repo with an origin, a temp plan."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "orchestrate.py"

FAKE_RUNTIME = '''#!/usr/bin/env python3
"""Records every call; spawn answers a canned worker, wait pops the next scripted answer."""
import json, os, subprocess, sys
home = os.environ["FAKE_RUNTIME_HOME"]
argv = sys.argv[1:]
tool = argv[1]
lead = argv[argv.index("--lead") + 1] if "--lead" in argv else None
args = json.loads(argv[argv.index("--json") + 1]) if "--json" in argv else {}
events_path = os.environ.get("FAKE_EVENTS", "")
seen = open(events_path).read().splitlines() if events_path and os.path.exists(events_path) else []
with open(os.path.join(home, "calls.jsonl"), "a") as log:
    log.write(json.dumps({"tool": tool, "lead": lead, "args": args, "events": seen}) + "\\n")
rows = [json.loads(line) for line in open(os.path.join(home, "calls.jsonl"))]
nth = sum(1 for r in rows if r["tool"] == tool and r["args"].get("name") == args.get("name"))
if tool == "spawn":
    if args["name"] in json.load(open(os.path.join(home, "refuse.json"))):
        print(json.dumps({"content": [{"type": "text", "text": "name_taken"}], "isError": True}))
        sys.exit(1)
    stopped_path = os.path.join(home, "stopped.json")  # a name the driver stopped is live again once it is spawned
    stopped = json.load(open(stopped_path)) if os.path.exists(stopped_path) else []
    if args["name"] in stopped:
        states = json.load(open(os.path.join(home, "states.json")))
        states.pop(args["name"], None)
        json.dump(states, open(os.path.join(home, "states.json"), "w"))
        json.dump([n for n in stopped if n != args["name"]], open(stopped_path, "w"))
    print(json.dumps({"worker_id": "w-" + args["name"], "assignment_id": "a-%s%s" % (args["name"], "" if nth == 1 else "-%d" % nth),
                      "name": args["name"], "address": "term-" + args["name"], "parent": "driver"}))
elif tool == "wait":
    queue_path = os.path.join(home, "waits.json")
    queue = json.load(open(queue_path))
    step = queue.pop(0) if queue else {}
    json.dump(queue, open(queue_path, "w"))
    for path, text in step.pop("write", []):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if "@HEAD" in text:  # the sha the unit's checkout is at now, as a reviewer would read it
            text = text.replace("@HEAD", subprocess.run(["git", "-C", os.environ["FAKE_CHECKOUT"], "rev-parse", "HEAD"],
                                                        capture_output=True, text=True).stdout.strip())
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
    states = json.load(open(os.path.join(home, "states.json")))
    states[args["name"]] = "exited"
    json.dump(states, open(os.path.join(home, "states.json"), "w"))
    stopped_path = os.path.join(home, "stopped.json")
    stopped = json.load(open(stopped_path)) if os.path.exists(stopped_path) else []
    json.dump(stopped + [args["name"]], open(stopped_path, "w"))
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
"""A fake `gh`. Every call is logged with the plan as it stands.

`pr view` answers the PR's state: `view-early.json` when the test scripted one (a state before `gh pr ready`), else the
next state of prs.json (the last repeats, MERGED by default). The state never depends on the PR being a draft: a driver
that does not run `gh pr ready` still sees the merge instead of polling a PR that will never open. The draft itself is
reported: a PR is a draft unless the worker opened it ready (`ready.flag`). `pr checks` pops checks-pr.json
([exit, stdout, stderr]), `pr update-branch` pops update.json ([exit, stderr]), `pr ready` marks the PR ready and
`pr ready --undo` drafts it again.
"""
import json, os, sys
home = os.environ["FAKE_RUNTIME_HOME"]
argv = sys.argv[1:]
with open(os.path.join(home, "gh.log"), "a") as log:
    log.write(json.dumps({"argv": argv, "plan": open(os.environ["FAKE_PLAN"]).read()}) + "\\n")


def pop(name, default=None):
    """The next item of a scripted queue (the last one repeats); the default when there is none."""
    path = os.path.join(home, name)
    if not os.path.exists(path):
        return default
    queue = json.load(open(path))
    if not queue:
        return default
    item = queue.pop(0) if len(queue) > 1 else queue[0]
    json.dump(queue, open(path, "w"))
    return item


ready = os.path.join(home, "ready.flag")
if argv[:2] == ["pr", "checks"]:
    code, out, err = pop("checks-pr.json", [0, "[]", ""])
    print(out)
    print(err, file=sys.stderr)
    sys.exit(code)
elif argv[:2] == ["pr", "ready"]:
    if "--undo" in argv:
        if os.path.exists(ready):
            os.remove(ready)
    else:
        open(ready, "w").write("1")
elif argv[:2] == ["pr", "update-branch"]:
    code, err = pop("update.json", [0, ""])
    print(err, file=sys.stderr)
    sys.exit(code)
else:
    state = pop("view-early.json")
    if state is None:
        state = pop("prs.json", "MERGED")
    row = {"state": state} if isinstance(state, str) else dict(state)
    row.setdefault("isDraft", not os.path.exists(ready))
    row.setdefault("mergeStateStatus", "CLEAN")
    row.setdefault("mergeable", "MERGEABLE")
    if row["state"] == "MERGED":
        row.setdefault("mergeCommit", {"oid": "f" * 40})
    else:
        row.setdefault("mergeCommit", None)
    print(json.dumps(row))
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


def wait_result(assignments=(), messages=(), write=(), replace=(), run=(), reason=None):
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
    if run:
        step["run"] = [list(r) for r in run]
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

    def pr_checks(self, answers):
        """What `gh pr checks` answers on its next calls ([exit code, stdout, stderr]; the last repeats)."""
        (self.home / "checks-pr.json").write_text(json.dumps(answers), encoding="utf-8")

    def prs(self, states):
        (self.home / "prs.json").write_text(json.dumps(states), encoding="utf-8")

    def early(self, states):
        """PR states `gh pr view` answers before and regardless of `gh pr ready` (a merge by hand)."""
        (self.home / "view-early.json").write_text(json.dumps(states), encoding="utf-8")

    def updates(self, answers):
        """What `gh pr update-branch` answers: [exit code, stderr] per call (the last repeats)."""
        (self.home / "update.json").write_text(json.dumps(answers), encoding="utf-8")

    def born_ready(self):
        """The worker opened the PR ready for review, not as a draft."""
        (self.home / "ready.flag").write_text("1", encoding="utf-8")

    def gh_log(self):
        path = self.home / "gh.log"
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def gh_calls(self, *prefix):
        """The argv of every logged gh call that starts with `prefix`."""
        return [c["argv"] for c in self.gh_log() if c["argv"][:len(prefix)] == list(prefix)]

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

    def env(self):
        return dict(os.environ, PATH=str(self.home) + os.pathsep + os.environ["PATH"],
                    FAKE_RUNTIME_HOME=str(self.home), FAKE_PLAN=str(self.plan),
                    FAKE_CHECKOUT=str(self.root / "repo.worktrees" / "demo-t1"),
                    FAKE_EVENTS=str(self.state_dir / "demo" / "events.jsonl"))

    def cli(self, *args, timeout=60):
        """A subcommand of the script run as the Lead would run it; the caller checks the exit code."""
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True, text=True,
                              env=self.env(), timeout=timeout)

    def decide_argv(self, unit, action, reason="because", answer=None):
        return [sys.executable, "-B", str(SCRIPT), "decide", str(self.plan), unit, action, "--reason", reason,
                "--state-dir", str(self.state_dir), *(["--answer", answer] if answer else [])]

    def decide_step(self, unit, action, reason="because", answer=None, **extra):
        """A wait step during which the Lead runs `decide`: the fake runtime runs it when the driver calls wait."""
        return wait_result(run=[self.decide_argv(unit, action, reason, answer)], **extra)

    def wakes(self):
        path = self.state_dir / "demo" / "wakes.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return rows

    def wake_lines(self, kind=None):
        return [w["text"] for w in self.wakes() if kind in (None, w["kind"])]

    def run_driver(self, *extra, plan=None, expect=0):
        env = self.env()
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "run", str(plan or self.plan), "--state-dir", str(self.state_dir),
             "--models-file", str(self.models), "--wait-seconds", "1", "--idle-interval", "0", *extra],
            capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def ledger(self):
        return json.loads((self.state_dir / "demo.json").read_text(encoding="utf-8"))

    def events(self, *kinds):
        """The run's events.jsonl as dicts, optionally only the given kinds."""
        path = self.state_dir / "demo" / "events.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        return [r for r in rows if not kinds or r["kind"] in kinds]

    def assert_intents_precede_spawns(self):
        """D11: every spawn call went through ensure_agent, so its intent was already in events.jsonl."""
        spawns = self.calls("spawn")
        self.assertTrue(spawns)
        for call in spawns:
            logged = [json.loads(line) for line in call["events"]]
            self.assertIn(call["args"]["name"], [e.get("name") for e in logged if e["kind"] == "intent"],
                          "no intent event before the spawn of %s" % call["args"]["name"])


def load_script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("orchestrate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def recorded_idles(spec):
    """Replace `Driver.idle` with a recorder of its interval. Patching `time.sleep` itself would also hit
    `subprocess` (its timeout loop sleeps ~1 ms), which makes the count and the interval flaky."""
    intervals = []
    with mock.patch.object(spec.Driver, "idle", lambda driver: intervals.append(driver.args.idle_interval)):
        yield intervals
