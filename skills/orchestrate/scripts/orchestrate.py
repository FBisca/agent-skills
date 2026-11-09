#!/usr/bin/env python3
"""The orchestrate skill's entry point: the engine lives in the member, not here.

The driver — the plan parser, the dispatcher, the gates, the ledger — is the `agent-orchestrator`
member of `agent-runtime`. This script resolves that member's CLI and hands it the command. It holds
no engine code, so the two can never drift.

Resolution order:

1. `$AGENT_RUNTIME_HOME`, the checkout of agent-runtime: the member's console script when the
   environment is synced, else `uv run` inside that checkout.
2. `agent-orchestrator` on `PATH`.

The checkout wins, because it is the one the user named: an older install on `PATH` must not shadow
it. When neither answers, the skill refuses, names the way out and exits 2. It never falls back to a
second engine — a fallback copy is the drift this repository is removing.
"""

import os
from pathlib import Path
import shutil
import sys

MEMBER = "agent-orchestrator"
CHECKOUT = "AGENT_RUNTIME_HOME"


def candidates(env):
    """Every way to reach the member's CLI, in the order the skill tries them.

    Each candidate is (program, arguments): the program to run, and the arguments that come before
    the skill's own. A candidate that cannot be run is skipped, and the next one answers.
    """
    home = env.get(CHECKOUT)
    if home:
        checkout = Path(home).expanduser()
        console = checkout / ".venv" / "bin" / MEMBER
        if console.is_file():
            yield str(console), []
        uv = shutil.which("uv")
        if uv and (checkout / ".venv").is_dir():
            yield uv, ["run", "--project", str(checkout), "--no-sync", "--package", MEMBER, MEMBER]
    found = shutil.which(MEMBER)
    if found:
        yield found, []


def refusal(env):
    """What the user gets when no member answers: the reason, and the way out."""
    home = env.get(CHECKOUT)
    lines = [
        "the orchestrate skill needs the engine, and it is not installed.",
        "",
        "The engine is the `%s` member of agent-runtime. Give the skill one of:" % MEMBER,
        "",
        "  1. a checkout, named by %s:" % CHECKOUT,
        "       cd <agent-runtime checkout>",
        "       uv sync --frozen --all-packages",
        "       export %s=<agent-runtime checkout>" % CHECKOUT,
        "",
        "  2. the member on PATH:",
        "       uv tool install <agent-runtime checkout>/packages/%s" % MEMBER,
        "",
        "The skill refuses rather than run a second engine: two copies drift.",
    ]
    if home:
        lines.insert(1, "%s=%s names no member: %s is missing." % (
            CHECKOUT, home, Path(home).expanduser() / ".venv" / "bin" / MEMBER))
    return "\n".join(lines)


def main(argv=None):
    """Hand the command to the member's CLI and answer with its exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    env = dict(os.environ)
    for program, prefix in candidates(env):
        try:
            os.execvpe(program, [program, *prefix, *args], env)
        except OSError:
            continue  # this candidate cannot run; the next one answers
    print(refusal(env), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
