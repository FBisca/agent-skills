"""The fake agent-runtime: the runtime the driver talks to, answered in process.

The driver asks the runtime through one seam (`runtime_process` in `orchestrate.py`), so the tests answer it here
instead of starting a process per call. The executable the fixture puts on PATH is a wrapper around this module: one
contract, two ways to reach it.

The state lives in files under `FAKE_RUNTIME_HOME`, so a run can be scripted before it starts and read after it ends:
`calls.jsonl` (every call), `waits.json` (the scripted wait steps), `states.json` (the agents' states), `refuse.json`
(the names the runtime refuses to spawn) and `stopped.json` (the names the driver stopped).
"""

import json
import os
import subprocess
import sys


class Completed:
    """What `subprocess.run` returns: the exit code and the two streams."""

    def __init__(self, argv, returncode=0, stdout="", stderr=""):
        self.args = argv
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def read_lines(path):
    """The file's lines, or nothing when it is not there."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as stream:
        return stream.read().splitlines()


def read_json(path, default=None):
    """The file's JSON, or the default when it is not there."""
    if not os.path.exists(path):
        return default if default is not None else []
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path, value):
    """The file's new content."""
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(value, stream)


def answer(name, assignment_id):
    """The agent's answer: its worker id, assignment id, name, address and parent."""
    return {"worker_id": "w-" + name, "assignment_id": assignment_id, "name": name,
            "address": "term-" + name, "parent": "driver"}


def process(argv, timeout=None):
    """The answer to one `agent-runtime call <tool> --lead <lead> --json <arguments>` argv (without the program name)."""
    home = os.environ["FAKE_RUNTIME_HOME"]
    tool = argv[1]
    lead = argv[argv.index("--lead") + 1] if "--lead" in argv else None
    args = json.loads(argv[argv.index("--json") + 1]) if "--json" in argv else {}
    events_path = os.environ.get("FAKE_EVENTS", "")
    seen = read_lines(events_path) if events_path and os.path.exists(events_path) else []
    with open(os.path.join(home, "calls.jsonl"), "a", encoding="utf-8") as log:
        log.write(json.dumps({"tool": tool, "lead": lead, "args": args, "events": seen}) + "\n")
    rows = [json.loads(line) for line in read_lines(os.path.join(home, "calls.jsonl"))]
    nth = sum(1 for r in rows if r["tool"] == tool and r["args"].get("name") == args.get("name"))
    if tool == "spawn":
        if args["name"] in read_json(os.path.join(home, "refuse.json")):
            return Completed(argv, 1, json.dumps({"content": [{"type": "text", "text": "name_taken"}], "isError": True}))
        stopped_path = os.path.join(home, "stopped.json")  # a name the driver stopped is live again once it is spawned
        stopped = read_json(stopped_path)
        if args["name"] in stopped:
            states = read_json(os.path.join(home, "states.json"))
            states.pop(args["name"], None)
            write_json(os.path.join(home, "states.json"), states)
            write_json(stopped_path, [n for n in stopped if n != args["name"]])
        return Completed(argv, 0, json.dumps(answer(args["name"], "a-%s%s" % (args["name"], "" if nth == 1 else "-%d" % nth))))
    if tool == "wait":
        queue_path = os.path.join(home, "waits.json")
        queue = read_json(queue_path)
        step = queue.pop(0) if queue else {}
        write_json(queue_path, queue)
        for path, text in step.pop("write", []):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if "@HEAD" in text:  # the sha the unit's checkout is at now, as a reviewer would read it
                text = text.replace("@HEAD", subprocess.run(["git", "-C", os.environ["FAKE_CHECKOUT"], "rev-parse", "HEAD"],
                                                            capture_output=True, text=True).stdout.strip())
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(text)
        for path, old, new in step.pop("replace", []):
            with open(path, encoding="utf-8") as stream:
                text = stream.read()
            assert old in text, old
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(text.replace(old, new, 1))
        for command in step.pop("run", []):
            subprocess.run(command, check=True, capture_output=True)
        return Completed(argv, 0, json.dumps(dict({"reason": "empty", "reports": [], "unfinished": []}, **step)))
    if tool == "status":
        states = read_json(os.path.join(home, "states.json"))
        state = states.get(args["name"], "idle")
        if state == "error":
            return Completed(argv, 1, "", "the runtime does not know this agent")
        return Completed(argv, 0, json.dumps({"name": args["name"], "state": state}))
    if tool == "stop":
        states = read_json(os.path.join(home, "states.json"))
        states[args["name"]] = "exited"
        write_json(os.path.join(home, "states.json"), states)
        stopped_path = os.path.join(home, "stopped.json")
        write_json(stopped_path, read_json(stopped_path) + [args["name"]])
        return Completed(argv, 0, json.dumps({"name": args["name"], "state": "exited"}))
    if tool == "resume":
        return Completed(argv, 0, json.dumps(answer(args["name"], "r%d-%s" % (nth, args["name"]))))
    return Completed(argv, 0, json.dumps({}))


def main(argv):
    """The executable on PATH: answer one call and exit with its code."""
    result = process(argv)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode
