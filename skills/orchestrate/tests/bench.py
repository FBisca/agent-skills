"""A bounded benchmark runner: every run gets a budget, and a run that overruns it is stopped and recorded.

S3: WHEN a test run stalls or exceeds a declared budget, THEN the benchmark terminates it and records a failure
instead of running indefinitely.

The runner starts the command in its own process group. A run that overruns its budget is stopped: the command
itself is killed, so the run costs the budget and never the suite. Every run leaves one record: the outcome, the
reason, the budget it ran under and the source revision it ran on.
"""

import json
import os
import subprocess
import time


DEFAULT_BUDGET = 30.0


def read_records(path):
    """The records a benchmark run left behind."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as stream:
        return [json.loads(line) for line in stream.read().splitlines() if line.strip()]


def drain(proc):
    """What the command wrote before it was stopped: the pipes are read without waiting for the end."""
    chunks = []
    for pipe in (proc.stdout, proc.stderr):
        try:
            os.set_blocking(pipe.fileno(), False)
            chunks.append(os.read(pipe.fileno(), 65536).decode("utf-8", "replace"))
        except (OSError, ValueError):
            chunks.append("")
        finally:
            pipe.close()
    return chunks[0], chunks[1]


def run_budgeted(argv, env=None, cwd=None, budget_seconds=DEFAULT_BUDGET, label="", revision=None, records=None,
                 tail=4000):
    """Run `argv` under a budget and return its record.

    The record says `pass` when the command ended by itself with exit code 0, and `failure` when it exited with
    another code or overran the budget (in which case it is stopped first). `records` is a path: the record is
    appended to it as one JSON line, so a benchmark run leaves its evidence behind.
    """
    started = time.monotonic()
    proc = subprocess.Popen(argv, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    record = {"label": label, "revision": revision, "budget_seconds": budget_seconds, "argv": list(argv)}
    try:
        out, err = proc.communicate(timeout=budget_seconds)
        record["outcome"] = "pass" if proc.returncode == 0 else "failure"
        record["returncode"] = proc.returncode
        record["reason"] = "" if proc.returncode == 0 else "the run exited %s" % proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()  # the command itself; what it started is left behind
        proc.wait(timeout=10)
        out, err = drain(proc)
        record["outcome"] = "failure"
        record["returncode"] = None
        record["reason"] = "the run was stopped"
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    record["stdout"] = (out or "")[-tail:]
    record["stderr"] = (err or "")[-tail:]
    if records:
        with open(records, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record
