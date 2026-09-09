#!/usr/bin/env python3
"""Small orchestration records. No model calls, shell evaluation, or agent spawns."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
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


def run(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
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
    if status == "COMPLETE":
        require(task["runtime_id"], "bind the runtime agent before completion")
        require(report.get("acceptance_met") is True, "acceptance criteria are not confirmed")
        require(not report["remaining"], "complete result has remaining work")
        require(all(c["outcome"] == "passed" for c in checks), "complete result has failed or omitted checks")
        passed = {c["command"] for c in checks if c["outcome"] == "passed"}
        require(set(task["packet"]["checks"]).issubset(passed), "required checks are missing")
        task["finished_at"] = now()
    elif status == "BLOCKED":
        require(report.get("blocker") and report["remaining"], "blocked result needs a blocker and next action")
    task.update(status=status, report=report, updated_at=now(),
                checkout_at_checkpoint=checkout_snapshot(task["packet"]["checkout"]))
    return task


def task_summary(task):
    return {"task_id": task["packet"]["task_id"], "worker": task["packet"]["worker"],
            "status": task["status"], "runtime_id": task["runtime_id"]}


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


def herdr_snapshot(pane, session):
    require(os.environ.get("HERDR_ENV") == "1", "Herdr inspection requires a Herdr-managed caller")
    require(os.environ.get("HERDR_SOCKET_PATH") and os.environ.get("HERDR_PANE_ID"), "missing Herdr caller identity")
    require(session and session.strip(), "supply the exact Herdr session name")
    inherited = os.environ.get("HERDR_SESSION")
    require(not inherited or inherited == session, "session differs from caller's session")
    target = pane or os.environ["HERDR_PANE_ID"]
    require(not target.startswith("-"), "invalid pane ID")
    # Return raw structured evidence; do not guess registration field names across versions.
    result = json.loads(run(["herdr", "pane", "get", target, "--session", session]))
    return {"session": session, "pane": target, "snapshot": result,
            "note": "read only; verify live agent identity before mapping a task to this pane"}


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
        if name == "claim":
            sub.add_argument("--packet", required=True)
        if name == "bind":
            sub.add_argument("--runtime-id", required=True)
        if name == "checkpoint":
            sub.add_argument("--report", required=True)
        if name == "release":
            sub.add_argument("--reason", required=True)
            sub.add_argument("--stopped", action="store_true", help="Assert runtime confirms the worker stopped")
    sub = commands.add_parser("context")
    sub.add_argument("--sample", required=True)
    sub.add_argument("--reserve-tokens", type=int, required=True)
    sub.add_argument("--max-age-seconds", type=int, default=300)
    commands.add_parser("metrics").add_argument("--samples", required=True)
    sub = commands.add_parser("herdr", help="Read one pane; never create, attach, or close an agent")
    sub.add_argument("--pane")
    sub.add_argument("--session", required=True)
    args = parser.parse_args()
    if args.command == "inspect":
        return {**checkout_snapshot(args.checkout),
                "executables": {c: shutil.which(c) for c in ("codex", "claude", "herdr", "herdmates")},
                "herdr_caller": os.environ.get("HERDR_ENV") == "1",
                "native_agent_capabilities": "inspect this session's tool schema",
                "context": "unknown; supply current child runtime telemetry"}
    if args.command == "context":
        return context_verdict(read_json(args.sample), args.reserve_tokens, args.max_age_seconds)
    if args.command == "metrics":
        return metrics(read_json(args.samples))
    if args.command == "herdr":
        return herdr_snapshot(args.pane, args.session)
    with ledger(args.state) as data:
        if args.command == "claim":
            result = claim(data, read_json(args.packet))
            return {"action": result["action"], **task_summary(result["task"])}
        if args.command == "bind":
            return task_summary(bind(data, args.task, args.runtime_id))
        if args.command == "checkpoint":
            return task_summary(checkpoint(data, args.task, read_json(args.report)))
        if args.command == "release":
            require(args.stopped and args.reason.strip(), "release requires --stopped and a reason")
            task = data["tasks"][args.task]
            require(task["status"] != "COMPLETE", "completed task cannot be released")
            task.update(status="RELEASED", release_reason=args.reason, updated_at=now())
            return task_summary(task)
        return data["tasks"][args.task] if args.task else [task_summary(t) for t in data["tasks"].values()]


if __name__ == "__main__":
    try:
        print(json.dumps(main(), separators=(",", ":")))
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(1)
