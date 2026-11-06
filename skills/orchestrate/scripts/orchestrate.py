#!/usr/bin/env python3
"""Small orchestration records and the `run` dispatch driver.

No model calls and no shell evaluation. Only `run` starts workers, and only through `agent-runtime call`."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    with open(path, encoding="utf-8") as stream:
        raw = stream.read(65537)
    require(len(raw) <= 65536, "Input exceeds 64 KiB; provide a compact record, not a transcript")
    return json.loads(raw)


def run(argv, timeout=15):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, result.stderr.strip() or "Command failed: " + argv[0])
    return result.stdout.strip()


def checkout_snapshot(path):
    root = Path(path).resolve(strict=True)
    actual = Path(run(["git", "-C", str(root), "rev-parse", "--show-toplevel"])).resolve()
    require(root == actual, "checkout must be the repository/worktree root")
    return {
        "checkout": str(root),
        "head": run(["git", "-C", str(root), "rev-parse", "HEAD"]),
        "branch": run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"]),
        # This is an inventory, NOT a content fingerprint. Re-read affected source.
        "worktree_status": run(["git", "-C", str(root), "status", "--porcelain=v1"]),
    }


def owned_paths(packet):
    root = Path(packet["checkout"]).resolve()
    owned = packet.get("owns")
    require(isinstance(owned, list) and owned, "owns must contain relative files or directories")
    paths = []
    for item in owned:
        require(isinstance(item, str) and item and not any(c in item for c in "*?[]"),
                "owns requires literal paths, not glob patterns")
        rel = Path(item)
        require(not rel.is_absolute() and ".." not in rel.parts, "ownership must stay inside checkout")
        target = (root / rel).resolve()
        require(target.is_relative_to(root), "ownership follows a symlink outside checkout")
        paths.append(target)
    return paths


@contextmanager
def ledger(path):
    path = Path(path).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), "ledger must not be a symlink")
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("ledger busy; inspect or retry after the other update") from None
        if path.exists():
            with path.open(encoding="utf-8") as stream:
                data = json.load(stream)
        else:
            data = {"version": 1, "tasks": {}}
        require(data.get("version") == 1 and isinstance(data.get("tasks"), dict), "invalid ledger")
        before = json.dumps(data, sort_keys=True)
        yield data
        if json.dumps(data, sort_keys=True) != before:
            tmp_fd, tmp_path = tempfile.mkstemp(prefix=".orchestrate-", dir=path.parent)
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as stream:
                    json.dump(data, stream, indent=2)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(tmp_path, path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)


ROUTE = {"size": ("small", "regular", "big"), "difficulty": ("simple", "complex"),
         "class": ("small", "medium", "large"), "effort": ("low", "medium", "high", "xhigh", "max")}


def routed(packet):
    """A packet opts into routing with a cell key; model or effort alone stay legacy metadata."""
    return any(key in packet for key in ("size", "difficulty", "class"))


def whole(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def claim(data, packet):
    require(isinstance(packet, dict), "packet must be an object")
    for key in ("task_id", "worker", "plan", "objective", "checkout", "backend"):
        require(isinstance(packet.get(key), str) and packet[key].strip(), "missing " + key)
    require(packet["backend"] in ("codex", "claude"), "backend must be codex or claude")
    require(isinstance(packet.get("acceptance"), list) and packet["acceptance"], "acceptance is required")
    require(isinstance(packet.get("checks"), list), "checks must be a list")
    require(all(isinstance(c, str) and c.strip() for c in packet["checks"]), "invalid check command")
    require(all(isinstance(c, str) and c.strip() for c in packet["acceptance"]), "invalid acceptance criterion")
    require(isinstance(packet.get("depends_on", []), list)
            and all(isinstance(c, str) for c in packet.get("depends_on", [])), "invalid dependency list")
    if routed(packet):
        for key, allowed in ROUTE.items():
            require(packet.get(key) in allowed, key + " must be one of " + ", ".join(allowed))
        require(isinstance(packet.get("model"), str) and packet["model"].strip(), "a routed packet needs its model")
        require(isinstance(packet.get("unit"), str) and packet["unit"].strip(), "a routed packet needs its unit")
    snapshot = checkout_snapshot(packet["checkout"])
    packet = dict(packet, checkout=snapshot["checkout"])
    paths = owned_paths(packet)
    task_id = packet["task_id"]
    tasks = data["tasks"]
    if task_id in tasks:
        require(tasks[task_id]["packet"] == packet, "task ID already has a different assignment")
        return {"action": "existing", "task": tasks[task_id]}
    for dep in packet.get("depends_on", []):
        require(dep in tasks and tasks[dep]["status"] == "COMPLETE", "dependency not complete: " + dep)
    for task in tasks.values():
        if task["status"] in ("COMPLETE", "RELEASED"):
            continue
        other = task["packet"]
        require(other["worker"] != packet["worker"], "worker already has an unfinished assignment")
        for left in paths:
            for right in owned_paths(other):
                require(not (left.is_relative_to(right) or right.is_relative_to(left)),
                        "ownership overlaps task " + other["task_id"])
    tasks[task_id] = {"packet": packet, "status": "RESERVED", "runtime_id": None,
                      "started_at": now(), "checkout_at_claim": snapshot}
    return {"action": "reserved", "task": tasks[task_id]}


def bind(data, task_id, runtime_id):
    task = data["tasks"][task_id]
    require(task["status"] not in ("COMPLETE", "RELEASED"), "assignment is closed")
    require(runtime_id.strip(), "runtime ID is empty")
    require(task["runtime_id"] in (None, runtime_id), "assignment already belongs to another runtime agent")
    for other_id, other in data["tasks"].items():
        if other_id != task_id and other["status"] not in ("COMPLETE", "RELEASED"):
            require(other["runtime_id"] != runtime_id, "runtime agent already has an unfinished assignment")
    task.update(runtime_id=runtime_id, status="ACTIVE")
    return task


def checkpoint(data, task_id, report):
    task = data["tasks"][task_id]
    require(isinstance(report, dict), "report must be an object")
    require(task["status"] not in ("COMPLETE", "RELEASED"), "assignment is closed")
    require(report.get("task_id") == task_id, "report task ID does not match")
    status = report.get("status")
    require(status in ("PARTIAL", "BLOCKED", "COMPLETE"), "invalid result status")
    require(isinstance(report.get("summary"), str) and report["summary"].strip(), "summary is required")
    for key in ("files", "decisions", "interfaces", "remaining", "checks"):
        require(isinstance(report.get(key), list), key + " must be a list")
    checks = report["checks"]
    for check in checks:
        require(isinstance(check, dict) and isinstance(check.get("command"), str), "invalid check")
        require(check.get("outcome") in ("passed", "failed", "not_run"), "invalid check outcome")
        require(check.get("outcome") == "passed" or check.get("reason"), "failed or omitted check needs a reason")
    require("review_rounds" not in report or whole(report["review_rounds"]), "review_rounds must be a whole number")
    if status == "COMPLETE":
        require(task["runtime_id"], "bind the runtime agent before completion")
        require(report.get("acceptance_met") is True, "acceptance criteria are not confirmed")
        require(not report["remaining"], "complete result has remaining work")
        require(all(c["outcome"] == "passed" for c in checks), "complete result has failed or omitted checks")
        passed = {c["command"] for c in checks if c["outcome"] == "passed"}
        require(set(task["packet"]["checks"]).issubset(passed), "required checks are missing")
        if routed(task["packet"]):
            require("review_rounds" in report, "a routed task needs review_rounds")
            require(isinstance(report.get("usage"), str) and report["usage"].strip(),
                    "a routed task needs usage (the runtime's metric line, or unknown)")
        task["finished_at"] = now()
    elif status == "BLOCKED":
        require(report.get("blocker") and report["remaining"], "blocked result needs a blocker and next action")
    task.update(status=status, report=report, updated_at=now(),
                checkout_at_checkpoint=checkout_snapshot(task["packet"]["checkout"]))
    return task


def release(data, task_id, reason, cutoff=False):
    task = data["tasks"][task_id]
    require(reason.strip(), "release requires a reason")
    require(task["status"] != "COMPLETE", "completed task cannot be released")
    task.update(status="RELEASED", release_reason=reason, cutoff=cutoff, updated_at=now())
    return task


def unit_summary(data, unit):
    """Failed reviews and cutoffs summed over every attempt at one logical unit."""
    attempts = [t for t in data["tasks"].values() if t["packet"].get("unit") == unit]
    require(attempts, "no attempts for unit " + unit)
    failed = sum((t.get("report") or {}).get("review_rounds", 0) for t in attempts)
    cutoffs = sum(1 for t in attempts if t.get("cutoff"))
    return {"unit": unit, "attempts": [task_summary(t) for t in attempts], "failed_reviews": failed,
            "cutoffs": cutoffs, "escalate": failed >= 2 or cutoffs >= 2}


def task_summary(task):
    summary = {"task_id": task["packet"]["task_id"], "worker": task["packet"]["worker"],
               "status": task["status"], "runtime_id": task["runtime_id"]}
    for key in ("unit", *ROUTE, "model"):
        if key in task["packet"]:
            summary[key] = task["packet"][key]
    return summary


def context_verdict(sample, reserve, max_age=300):
    """Evaluate reported occupancy only; relevance remains an orchestrator decision."""
    require(isinstance(sample, dict), "context sample must be an object")
    require(reserve >= 0 and max_age > 0, "reserve must be nonnegative; max age must be positive")
    unknown = {"status": "unknown", "reason": "missing, stale, or unsupported context measurement"}
    if sample.get("kind") != "current_context" or not sample.get("source") or not sample.get("model"):
        return unknown
    try:
        observed = datetime.fromisoformat(sample["observed_at"])
        age = (datetime.now(timezone.utc) - observed).total_seconds()
    except (KeyError, TypeError, ValueError):
        return unknown
    used, window = sample.get("context_tokens"), sample.get("effective_window")
    if (type(used) is not int or type(window) is not int or not 0 <= used <= window
            or window <= 0 or not 0 <= age <= max_age):
        return unknown
    available = window - used
    return {"status": "checkpoint" if reserve >= available else "room_available",
            "remaining_tokens": available, "next_task_reserve": reserve,
            "model": sample["model"], "source": sample["source"],
            "note": "capacity check only; verify relevance and checkout before reuse"}


def metrics(samples):
    """Normalize per-request observations. Never price tokens using guessed rates."""
    require(isinstance(samples, list), "metrics input must be a list of per-request records")
    fields = ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "cost_usd", "duration_seconds")
    seen, groups = set(), {}
    for sample in samples:
        require(isinstance(sample, dict) and sample.get("kind") == "request", "only per-request records are accepted")
        for key in ("id", "source", "backend", "model", "strategy", "actor"):
            require(isinstance(sample.get(key), str) and sample[key], "missing metric " + key)
        identity = (sample["source"], sample["id"])
        require(identity not in seen, "duplicate usage record")
        seen.add(identity)
        key = (sample["strategy"], sample["actor"], sample["backend"], sample["model"])
        group = groups.setdefault(key, {"requests": 0, "totals": dict.fromkeys(fields, 0),
                                        "observations": dict.fromkeys(fields, 0)})
        group["requests"] += 1
        for field in fields:
            value = sample.get(field)
            if value is not None:
                require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
                        "invalid metric " + field)
                group["totals"][field] += value
                group["observations"][field] += 1
    output = []
    for key, group in groups.items():
        for field in fields:
            if not group["observations"][field]:
                group["totals"][field] = None
        output.append(dict(zip(("strategy", "actor", "backend", "model"), key), **group))
    return {"groups": output, "note": "partial observations are not full workflow cost; include orchestrator and workers; summed request duration is not parallel wall time"}


def resolve_runtime():
    """Ask the agent-runtime CLI which runtime this session runs in; never fail inspect.

    Resolution order: `$AGENT_RUNTIME_HOME/server/agent_runtime.py`, then `agent-runtime` on PATH.
    """
    home = os.environ.get("AGENT_RUNTIME_HOME")
    script = Path(home).expanduser() / "server" / "agent_runtime.py" if home else None
    if home and not (script and script.is_file()):
        print(f"warning: AGENT_RUNTIME_HOME={home} has no server/agent_runtime.py; falling back to agent-runtime on PATH",
              file=sys.stderr)
    argv = [sys.executable, str(script)] if script and script.is_file() else ["agent-runtime"]
    try:
        return json.loads(run(argv + ["resolve", "--json"]))
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return {"runtime": "unknown"}


class PlanError(ValueError):
    """The plan cannot be run as written; `run` exits 2 and starts nothing."""


TICKET_COLUMNS = ("#", "What it delivers", "Satisfies", "Blocked by", "Paths", "Size", "Difficulty", "Owner", "Status")
MATRIX = {("small", "simple"): ("small", "low"), ("small", "complex"): ("medium", "medium"),
          ("regular", "simple"): ("medium", "medium"), ("regular", "complex"): ("medium", "high")}
CONTRACT = """# Contract for every task in this run

- Write your result to the report path your task.md names, as JSON in this shape:
  {"task_id","status":"COMPLETE|PARTIAL|BLOCKED","summary","acceptance_met":bool,"files":[],"decisions":[],"interfaces":[],"remaining":[],"checks":[{"command","outcome":"passed|failed|not_run","reason?"}],"review_rounds":0,"usage":"unknown","context":{"status":"unknown"}}
  BLOCKED needs "blocker" and a next action in "remaining".
- Prose, if any, goes in report.md beside it. Files are write-once: a later attempt writes report.2.json.
- Your agent-runtime `report` call carries ONE line: status + report path. Use kind=complete, blocked or decision.
- Red-first: one test per scenario, named with its S-ID, seen failing before the code exists.
- Fix the class, not the instance: when you fix a defect, search for every other place with the same pattern.
- Edit only the Paths your task owns. Never touch other worktrees or the main checkout.
- Commit with Conventional Commits and push the branch. Describe behaviour, not plan ticket numbers.
"""


def worker_name(slug, number):
    """`<slug>-t<n>` within agent-runtime's 32-character name limit; the `-t<n>` suffix always survives."""
    suffix = "-t" + str(number)
    return slug[:32 - len(suffix)].rstrip("-_") + suffix


def split_row(line):
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        return None
    return [cell.strip() for cell in line[1:-1].split("|")]


def parse_plan(text):
    """Slug, status, scenarios and the Tickets table (with each row's line index) of a plan."""
    lines = text.splitlines()
    head = text.split("\n## ", 1)[0]
    slug = re.search(r"Slug:\s*`([^`]+)`", head)
    status = re.search(r"Status:\s*([A-Za-z-]+)", head)
    scenarios = {}
    for line in lines:
        found = re.match(r"- \*\*(S\d+[a-z]?)\*\*\s", line)
        if found:
            scenarios[found.group(1)] = line
    tickets, columns = [], None
    for index, line in enumerate(lines):
        cells = split_row(line)
        if cells is None:
            columns = columns if tickets else None
            continue
        if columns is None:
            if all(name in cells for name in TICKET_COLUMNS):
                columns = {name: cells.index(name) for name in TICKET_COLUMNS}
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if len(cells) == len(columns) or len(cells) > max(columns.values()):
            tickets.append({"line": index, **{name: cells[at] for name, at in columns.items()}})
    return {"slug": slug.group(1) if slug else None, "status": status.group(1).upper() if status else None,
            "scenarios": scenarios, "tickets": tickets, "has_table": bool(tickets) or columns is not None}


def is_done(ticket):
    return ticket["Status"].strip().upper().startswith("COMPLETE")


def is_agent(ticket):
    return ticket["Owner"].strip().lower() == "agent"


def satisfied(ticket, scenarios):
    """Scenario IDs a ticket makes true; a range covers every ID numbered inside it."""
    found, missing = [], []
    for token in re.split(r"[,\s]+", ticket["Satisfies"].strip()):
        if not token or token.lower() == "none":
            continue
        ends = re.fullmatch(r"S(\d+)[a-z]?[–-]S?(\d+)[a-z]?", token)
        if ends:
            low, high = int(ends.group(1)), int(ends.group(2))
            ids = [sid for sid in scenarios if low <= int(re.match(r"S(\d+)", sid).group(1)) <= high]
        else:
            ids = [token] if token in scenarios else []
        (found if ids else missing).extend(ids or [token])
    return found, missing


def check_plan(plan):
    """Every reason `run` cannot start, so one exit names them all."""
    problems = []
    if plan["status"] != "APPROVED":
        problems.append("plan Status is %s, not APPROVED" % (plan["status"] or "missing"))
    if not plan["slug"] or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", plan["slug"]):
        problems.append("plan has no valid Slug (lowercase letters, digits, hyphens)")
    if not plan["tickets"]:
        problems.append("plan has no Tickets table with the fixed columns (" + " | ".join(TICKET_COLUMNS) + ")")
    seen = set()
    for ticket in plan["tickets"]:
        name = ticket["#"]
        if not re.fullmatch(r"T\d+", name) or name in seen:
            problems.append("ticket id %r is not a unique T<n>" % name)
        seen.add(name)
    for ticket in plan["tickets"]:
        if not is_agent(ticket) or is_done(ticket):
            continue
        name = ticket["#"]
        found, missing = satisfied(ticket, plan["scenarios"])
        if not found and not missing:
            problems.append("%s: Satisfies is empty" % name)
        problems += ["%s: scenario %s is not in the plan" % (name, sid) for sid in missing]
        paths = [p.strip() for p in ticket["Paths"].split(",") if p.strip()]
        if not paths:
            problems.append("%s: Paths is empty" % name)
        for path in paths:
            if any(c in path for c in "*?[]") or Path(path).is_absolute() or ".." in Path(path).parts:
                problems.append("%s: Paths entry %r must be a literal path inside the repository" % (name, path))
        for column, allowed in (("Size", ("small", "regular")), ("Difficulty", ("simple", "complex"))):
            value = ticket[column].strip()
            if not value:
                problems.append("%s: %s is empty" % (name, column))
            elif value not in allowed + (("big",) if column == "Size" else ()):
                problems.append("%s: %s %r is not one of %s" % (name, column, value, ", ".join(allowed)))
        if ticket["Size"].strip() == "big":
            problems.append("%s: a big ticket needs chunked dispatch, which `run` does not do; split it" % name)
        for blocker in re.split(r"[,\s]+", ticket["Blocked by"].strip()):
            if blocker and blocker.lower() != "none" and blocker not in {t["#"] for t in plan["tickets"]}:
                problems.append("%s: Blocked by %s is not a ticket" % (name, blocker))
    if problems:
        raise PlanError("; ".join(problems))


def set_status(plan_path, ticket_id, status):
    """Rewrite one ticket row's Status cell; every other line stays byte-identical."""
    require("|" not in status and "\n" not in status, "status must be one table cell")
    path = Path(plan_path)
    with path.open(encoding="utf-8", newline="") as stream:
        text = stream.read()
    ticket = next((t for t in parse_plan(text)["tickets"] if t["#"] == ticket_id), None)
    require(ticket is not None, "plan has no ticket " + ticket_id)
    lines = text.splitlines(keepends=True)
    line = lines[ticket["line"]]
    body = line.rstrip("\r\n")
    eol = line[len(body):]
    trimmed = body.rstrip()
    cut = trimmed.rfind("|", 0, len(trimmed) - 1)
    lines[ticket["line"]] = trimmed[:cut + 1] + " " + status + " |" + body[len(trimmed):] + eol
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".orchestrate-", dir=path.parent)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as stream:
            stream.write("".join(lines))
        shutil.copymode(path, tmp_path)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def class_models(path, backend):
    """Resolve each class to a model from the 'Model classes' table of the instructions file."""
    try:
        text = Path(path).expanduser().read_text(encoding="utf-8")
    except OSError as error:
        raise PlanError("cannot read the Model classes table: %s" % error) from None
    section = re.split(r"^## Model classes\s*$", text, maxsplit=1, flags=re.M)
    models = {}
    for line in (section[1].split("\n## ", 1)[0].splitlines() if len(section) > 1 else []):
        cells = split_row(line)
        if cells and len(cells) >= 3 and cells[0] in ROUTE["class"]:
            value = cells[1 if backend == "claude" else 2].strip("`")
            quoted = re.search(r'"([^"]+)"', value)
            models[cells[0]] = quoted.group(1) if quoted else value
    missing = [c for c in ROUTE["class"] if not models.get(c)]
    if missing:
        raise PlanError("%s lacks a %s model for class %s" % (path, backend, ", ".join(missing)))
    return models


def runtime_call(lead, tool, arguments, timeout=120):
    result = subprocess.run(["agent-runtime", "call", tool, "--lead", lead, "--json", json.dumps(arguments)],
                            capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise ValueError("agent-runtime %s failed (exit %d): %s"
                         % (tool, result.returncode, (result.stderr.strip() or result.stdout.strip())[:500]))
    return json.loads(result.stdout)


def event(message):
    print("[orchestrate] " + message, file=sys.stderr, flush=True)


class Driver:
    """The dispatch loop. It keeps no state of its own: the plan, the ledger and the runtime hold it."""

    def __init__(self, args):
        self.args = args
        self.plan_path = Path(args.plan).resolve(strict=True)
        self.repo = Path(args.repo).resolve() if args.repo else Path(
            run(["git", "-C", str(self.plan_path.parent), "rev-parse", "--show-toplevel"])).resolve()
        self.errors = []
        self.spawned = []
        self.failed = set()
        self.receipt = None

    def read_plan(self):
        plan = parse_plan(self.plan_path.read_text(encoding="utf-8"))
        check_plan(plan)
        return plan

    def start(self):
        plan = self.read_plan()
        self.slug = plan["slug"]
        self.models = class_models(self.args.models_file, self.args.cli)
        state_dir = Path(self.args.state_dir).expanduser()
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.ledger_path = state_dir / (self.slug + ".json")
        self.run_dir = state_dir / self.slug
        self.run_dir.mkdir(exist_ok=True, mode=0o700)
        contract = self.run_dir / "contract.md"
        if not contract.exists():
            contract.write_text(CONTRACT, encoding="utf-8")
        with ledger(self.ledger_path) as data:
            self.lead = data.setdefault("lead", "orchestrate:" + self.slug)

    def loop(self):
        idle = False
        while True:
            try:
                plan = self.read_plan()
            except PlanError as error:
                event("plan not runnable, nothing dispatched this round: %s" % error)
                plan = None
            dispatched = self.dispatch_ready(plan) if plan else 0
            if idle and not dispatched:
                return
            wait = {"target": "all", "timeout": self.args.wait_seconds}
            if self.receipt:
                wait["receipt"] = self.receipt
            result = runtime_call(self.lead, "wait", wait, timeout=self.args.wait_seconds + 60)
            self.receipt = result.get("receipt")
            idle = not result.get("unfinished")

    def dispatch_ready(self, plan):
        with ledger(self.ledger_path) as data:
            tasks = data["tasks"]
            unfinished = sum(1 for t in tasks.values() if t["status"] not in ("COMPLETE", "RELEASED"))
        by_id = {t["#"]: t for t in plan["tickets"]}
        count = 0
        for ticket in plan["tickets"]:
            task_id = ticket["#"].lower()
            if (not is_agent(ticket) or not ticket["Status"].strip().upper().startswith("TO-DO")
                    or task_id in self.failed
                    or not all(is_done(by_id[b]) for b in re.split(r"[,\s]+", ticket["Blocked by"].strip())
                               if b and b.lower() != "none")):
                continue
            held = tasks.get(task_id)
            if held and held["runtime_id"]:
                continue
            if not held and unfinished >= self.args.max_workers:
                continue
            try:
                self.dispatch(plan, ticket)
            except (ValueError, OSError, subprocess.TimeoutExpired) as error:
                self.failed.add(task_id)
                self.errors.append("%s: %s" % (ticket["#"], error))
                event("%s not dispatched: %s" % (ticket["#"], error))
                unfinished += 0 if held else 1
                continue
            unfinished += 0 if held else 1
            count += 1
        return count

    def dispatch(self, plan, ticket):
        number = ticket["#"][1:]
        task_id, name = "t" + number, worker_name(plan["slug"], number)
        size, difficulty = ticket["Size"].strip(), ticket["Difficulty"].strip()
        klass, effort = MATRIX[(size, difficulty)]
        checkout = self.worktree(name, "feat/" + name)
        scenarios = [plan["scenarios"][sid] for sid in satisfied(ticket, plan["scenarios"])[0]]
        packet = {"task_id": task_id, "worker": name, "plan": str(self.plan_path), "objective": ticket["What it delivers"],
                  "checkout": str(checkout), "backend": self.args.cli,
                  "owns": [p.strip() for p in ticket["Paths"].split(",") if p.strip()],
                  "acceptance": [re.sub(r"^- \*\*(S\d+[a-z]?)\*\*", r"\1:", s) for s in scenarios],
                  "checks": list(self.args.gate), "depends_on": [], "unit": task_id, "size": size,
                  "difficulty": difficulty, "class": klass, "effort": effort, "model": self.models[klass]}
        with ledger(self.ledger_path) as data:
            claim(data, packet)
        task_dir = self.run_dir / task_id
        task_dir.mkdir(exist_ok=True, mode=0o700)
        task_md = task_dir / "task.md"
        if not task_md.exists():
            task_md.write_text(self.task_text(plan, ticket, packet, scenarios, task_dir), encoding="utf-8")
        spawned = runtime_call(self.lead, "spawn", {
            "kind": "worker", "name": name, "task": "Read %s and follow it." % task_md, "cwd": str(checkout),
            "cli": self.args.cli, "model": packet["model"], "effort": effort})
        runtime_id = spawned.get("address") or spawned.get("assignment_id") or name
        with ledger(self.ledger_path) as data:
            bind(data, task_id, str(runtime_id))
        set_status(self.plan_path, ticket["#"], "IN PROGRESS")
        self.spawned.append(name)
        event("spawned %s (%s, %s, %s)" % (name, klass, packet["model"], effort))

    def worktree(self, name, branch):
        path = self.repo.parent / (self.repo.name + ".worktrees") / name
        remote, _, ref = self.args.base.partition("/")
        run(["git", "-C", str(self.repo), "fetch", "-q", remote, ref], timeout=120)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            exists = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "--verify", "-q", "refs/heads/" + branch],
                                    capture_output=True).returncode == 0
            run(["git", "-C", str(self.repo), "worktree", "add", *([] if exists else ["-b", branch]), str(path),
                 *([branch] if exists else [self.args.base])])
        return path

    def task_text(self, plan, ticket, packet, scenarios, task_dir):
        gate = self.args.gate or ["the repository's full CI gate (see its AGENTS.md / CLAUDE.md)"]
        return "\n".join([
            "Contract: %s" % (self.run_dir / "contract.md"),
            "Report: %s" % (task_dir / "report.json"),
            "",
            "# %s: %s" % (ticket["#"], ticket["What it delivers"]),
            "",
            "Plan: %s (read its Decisions and Seams)." % self.plan_path,
            "Checkout: %s on branch feat/%s (new, from %s). Work only here." % (
                packet["checkout"], packet["worker"], self.args.base),
            "Owns (edit nothing else): %s." % ", ".join(packet["owns"]),
            "Shared databases are read-only; schema changes go through migrations in your own branch.",
            "",
            "Scenarios, verbatim. Work red-first: one test per scenario, named with its S-ID, seen failing before the code exists.",
            "",
            *scenarios,
            "",
            "Before you report COMPLETE, run: " + "; ".join(gate) + ".",
            "Then open a pull request against %s." % self.args.base.partition("/")[2],
            ""])


def drive(args):
    require(args.max_workers >= 1, "--max-workers must be at least 1")
    driver = Driver(args)
    driver.start()
    driver.loop()
    return {"slug": driver.slug, "lead": driver.lead, "spawned": driver.spawned, "errors": driver.errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Read checkout identity and installed command paths")
    inspect.add_argument("--checkout", default=".")
    for name in ("claim", "bind", "checkpoint", "release", "show"):
        sub = commands.add_parser(name)
        sub.add_argument("--state", required=True, help="Shared ledger path outside tracked product files")
        if name in ("bind", "checkpoint", "release"):
            sub.add_argument("--task", required=True)
        if name == "show":
            sub.add_argument("--task", help="Show the full record for one task; otherwise show a compact index")
            sub.add_argument("--unit", help="Sum failed reviews and cutoffs over a unit's attempts")
        if name == "claim":
            sub.add_argument("--packet", required=True)
        if name == "bind":
            sub.add_argument("--runtime-id", required=True)
        if name == "checkpoint":
            sub.add_argument("--report", required=True)
        if name == "release":
            sub.add_argument("--reason", required=True)
            sub.add_argument("--stopped", action="store_true", help="Assert runtime confirms the worker stopped")
            sub.add_argument("--cutoff", action="store_true", help="The worker was stopped at its cutoff")
    sub = commands.add_parser("context")
    sub.add_argument("--sample", required=True)
    sub.add_argument("--reserve-tokens", type=int, required=True)
    sub.add_argument("--max-age-seconds", type=int, default=300)
    commands.add_parser("metrics").add_argument("--samples", required=True)
    sub = commands.add_parser("run", help="Dispatch an approved plan's ready agent tickets and wait for them")
    sub.add_argument("plan")
    sub.add_argument("--max-workers", type=int, default=3)
    sub.add_argument("--cli", choices=("claude", "codex"), default="claude")
    sub.add_argument("--base", default="origin/main", help="Remote branch each worktree starts from")
    sub.add_argument("--repo", help="Repository root; default the plan file's repository")
    sub.add_argument("--gate", action="append", default=[], help="CI command a worker must pass (repeatable)")
    sub.add_argument("--state-dir", default="~/.local/state/orchestrate", help="Holds <slug>.json and the <slug>/ run directory")
    sub.add_argument("--models-file", default="~/.claude/CLAUDE.md", help="File holding the 'Model classes' table")
    sub.add_argument("--wait-seconds", type=int, default=60, help="Longest one wait blocks before the plan is re-read")
    args = parser.parse_args()
    if args.command == "run":
        return drive(args)
    if args.command == "inspect":
        return {**checkout_snapshot(args.checkout),
                "executables": {c: shutil.which(c) for c in ("codex", "claude")},
                "agent_runtime": resolve_runtime(),
                "native_agent_capabilities": "inspect this session's tool schema",
                "context": "unknown; supply current child runtime telemetry"}
    if args.command == "context":
        return context_verdict(read_json(args.sample), args.reserve_tokens, args.max_age_seconds)
    if args.command == "metrics":
        return metrics(read_json(args.samples))
    with ledger(args.state) as data:
        if args.command == "claim":
            result = claim(data, read_json(args.packet))
            return {"action": result["action"], **task_summary(result["task"])}
        if args.command == "bind":
            return task_summary(bind(data, args.task, args.runtime_id))
        if args.command == "checkpoint":
            return task_summary(checkpoint(data, args.task, read_json(args.report)))
        if args.command == "release":
            require(args.stopped, "release requires --stopped")
            return task_summary(release(data, args.task, args.reason, args.cutoff))
        if args.unit:
            return unit_summary(data, args.unit)
        return data["tasks"][args.task] if args.task else [task_summary(t) for t in data["tasks"].values()]


if __name__ == "__main__":
    try:
        output = main()
        print(json.dumps(output, separators=(",", ":")))
        sys.exit(1 if isinstance(output, dict) and output.get("errors") else 0)
    except PlanError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(2)
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(1)
