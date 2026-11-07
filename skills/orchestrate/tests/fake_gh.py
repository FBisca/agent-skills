"""The fake `gh`: the GitHub CLI the driver polls, answered in process.

The driver asks `gh` through one seam (`gh_process` in `orchestrate.py`), so the tests answer it here instead of
starting a process per call. The executable the fixture puts on PATH is a wrapper around this module.

Every call is logged with the plan as it stands. `pr view` answers the PR's state: `view-early.json` when the test
scripted one (a state before `gh pr ready`), else the next state of prs.json (the last repeats, MERGED by default).
The state never depends on the PR being a draft: a driver that does not run `gh pr ready` still sees the merge
instead of polling a PR that will never open. The draft itself is reported: a PR is a draft unless the worker opened
it ready (`ready.flag`). `pr checks` pops checks-pr.json ([exit, stdout, stderr]), `pr update-branch` pops update.json
([exit, stderr]), `pr ready` marks the PR ready and `pr ready --undo` drafts it again.
"""

import json
import os
import sys


class Completed:
    """What `subprocess.run` returns: the exit code and the two streams."""

    def __init__(self, argv, returncode=0, stdout="", stderr=""):
        self.args = argv
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def pop(home, name, default=None):
    """The next item of a scripted queue (the last one repeats); the default when there is none."""
    path = os.path.join(home, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as stream:
        queue = json.load(stream)
    if not queue:
        return default
    item = queue.pop(0) if len(queue) > 1 else queue[0]
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(queue, stream)
    return item


def process(argv, timeout=None):
    """The answer to one `gh` argv (without the `gh` itself)."""
    home = os.environ["FAKE_RUNTIME_HOME"]
    with open(os.path.join(home, "gh.log"), "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": argv, "plan": open(os.environ["FAKE_PLAN"], encoding="utf-8").read()}) + "\n")
    ready = os.path.join(home, "ready.flag")
    if argv[:2] == ["pr", "checks"]:
        code, out, err = pop(home, "checks-pr.json", [0, "[]", ""])
        return Completed(argv, code, out, err)
    if argv[:2] == ["pr", "ready"]:
        if "--undo" in argv:
            if os.path.exists(ready):
                os.remove(ready)
        else:
            with open(ready, "w", encoding="utf-8") as stream:
                stream.write("1")
        return Completed(argv, 0, "")
    if argv[:2] == ["pr", "update-branch"]:
        code, err = pop(home, "update.json", [0, ""])
        return Completed(argv, code, "", err)
    state = pop(home, "view-early.json")
    if state is None:
        state = pop(home, "prs.json", "MERGED")
    row = {"state": state} if isinstance(state, str) else dict(state)
    row.setdefault("isDraft", not os.path.exists(ready))
    row.setdefault("mergeStateStatus", "CLEAN")
    row.setdefault("mergeable", "MERGEABLE")
    if row["state"] == "MERGED":
        row.setdefault("mergeCommit", {"oid": "f" * 40})
    else:
        row.setdefault("mergeCommit", None)
    return Completed(argv, 0, json.dumps(row))


def main(argv):
    """The executable on PATH: answer one call and exit with its code."""
    result = process(argv)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode
