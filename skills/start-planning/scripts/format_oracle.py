#!/usr/bin/env python3
"""Format a Python oracle as the repository's formatter formats the file it is promoted to.

An oracle is promoted byte-identical at archive: `<plan>.oracle/test_x.py.oracle` is copied to
`<place>/test_x.py`. The repository's format gate then reads that copy, so the oracle is formatted at
planning time, before `plan check` and `plan approve` digest it, and under its promoted name, so the
formatter applies the configuration (per-file rules, line length) that governs that path.

    format_oracle.py --repo <repo> <oracle file> <place>

The formatter is ruff, when the repository configures it (`[tool.ruff` in `pyproject.toml`, or a
`ruff.toml`/`.ruff.toml`). The repository's own ruff (`.venv/bin/ruff`) answers first, so the
version is the one its gate runs; else `ruff` on PATH.

Exit 0: formatted, unchanged, or nothing to format (not a Python oracle, no formatter configured).
Exit 1: the formatter refused the file (a syntax error); the file is left as it was.
Exit 2: the formatter is configured but not installed; the way out is named.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

SUFFIX = ".oracle"


def configured(repo):
    """Whether the repository configures ruff, the formatter its gate runs."""
    if (repo / "ruff.toml").is_file() or (repo / ".ruff.toml").is_file():
        return True
    pyproject = repo / "pyproject.toml"
    return pyproject.is_file() and "[tool.ruff" in pyproject.read_text(encoding="utf-8")


def ruff(repo):
    """The repository's ruff, else the one on PATH, else None."""
    local = repo / ".venv" / "bin" / "ruff"
    if local.is_file():
        return str(local)
    return shutil.which("ruff")


def promoted(oracle, place):
    """The repo-relative path the oracle is copied to at archive: the `.oracle` suffix dropped."""
    return Path(place) / oracle.name[: -len(SUFFIX)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", required=True, help="The repository the oracle is promoted into")
    parser.add_argument("oracle", help="The oracle file, `<name>.py.oracle`")
    parser.add_argument("place", help="The evidence's `place`: the repo directory it is copied to")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    oracle = Path(args.oracle)
    if not oracle.name.endswith(".py" + SUFFIX):
        print("%s: not a Python oracle, nothing to format" % oracle)
        return 0
    if not configured(repo):
        print("%s: the repository configures no formatter, nothing to format" % oracle)
        return 0
    program = ruff(repo)
    if program is None:
        print(
            "%s configures ruff but no ruff is installed: run `uv sync` in it, or put ruff on PATH"
            % repo,
            file=sys.stderr,
        )
        return 2
    target = promoted(oracle, args.place)
    before = oracle.read_text(encoding="utf-8")
    done = subprocess.run(
        [program, "format", "--stdin-filename", str(repo / target), "-"],
        input=before,
        capture_output=True,
        text=True,
        cwd=repo,
    )
    if done.returncode != 0:
        print("%s: ruff refused it as %s:\n%s" % (oracle, target, done.stderr.strip()), file=sys.stderr)
        return 1
    if done.stdout == before:
        print("%s: already formatted as %s" % (oracle, target))
        return 0
    oracle.write_text(done.stdout, encoding="utf-8")
    print("%s: formatted as %s" % (oracle, target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
