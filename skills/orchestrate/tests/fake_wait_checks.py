"""The mock CI gate: what `wait_checks.wait` answers in the tests.

The driver imports the wait as a module (see `wait_checks` in `orchestrate.py`), so the tests answer it with this
mock instead of faking a whole executable. The contract is the real wait's: a `PASS <owner>/<repo>#<pr>` or
`FAIL <owner>/<repo>#<pr>` line, the failing checks and the tail of the failed log, and an exit code (0 passed,
1 failed). The answer is scripted by the fixture's `checks.json`: a list of [exit code, stdout]; the last one repeats.
"""

import json
import os


class Result:
    """What the CI gate reads: the exit code, what the wait printed, and whether it ran out of time."""

    def __init__(self, returncode=0, stdout="", stderr="", timed_out=False):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out


def wait(ref, timeout=None, **kwargs):
    """The scripted answer to the CI gate's wait for one pull request."""
    home = os.environ["FAKE_RUNTIME_HOME"]
    with open(os.path.join(home, "wait-checks.log"), "a") as log:
        log.write(str(ref) + "\n")
    queue = json.load(open(os.path.join(home, "checks.json")))
    code, out = queue.pop(0) if len(queue) > 1 else queue[0]
    json.dump(queue, open(os.path.join(home, "checks.json"), "w"))
    return Result(code, out)


def main(argv):
    """The executable on PATH: wait for one pull request and exit with its code."""
    if not argv:
        print("wait-checks: no pull request given", file=os.sys.stderr)
        return 2
    result = wait(argv[0])
    if result.stdout:
        print(result.stdout, end="")
    return result.returncode
