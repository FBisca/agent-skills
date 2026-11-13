#!/usr/bin/env python3
"""Format a Python acceptance file as the repository's ruff formats the file it is promoted to.

An acceptance file lives in its plan folder's `acceptance/` until archive promotes it, byte-identical,
to `<package>/<acceptance.dir>/<domain>/<file>`. The repository's format gate then reads that copy,
so the file is formatted at planning time, before `plan check` and `plan approve` digest it, and
under its destination path, so ruff applies the configuration (per-file rules, line length) that
governs that path.

    format_acceptance.py --repo <repo> <acceptance file> <destination dir>

The destination dir is `<package>/<acceptance.dir>/<domain>/`, repo-relative. Only ruff is run, and
only when the repository configures it (`[tool.ruff` in `pyproject.toml`, or a `ruff.toml`/
`.ruff.toml`); any other repository or language keeps the file as written. The repository's own
ruff (`.venv/bin/ruff`) answers first, so the version is the one its gate runs; else `ruff` on PATH.

Exit 0: formatted, unchanged, or nothing to format (not a Python file, no ruff configured).
Exit 1: ruff refused the file (a syntax error); the file is left as it was.
Exit 2: ruff is configured but not installed; the way out is named.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", required=True, help="The repository the file is promoted into")
    parser.add_argument("file", help="The acceptance file, in the plan folder's acceptance/")
    parser.add_argument("destination", help="Where archive promotes it: <package>/<acceptance.dir>/<domain>/")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    file = Path(args.file)
    if file.suffix != ".py":
        print("%s: not a Python file, nothing to format" % file)
        return 0
    if not configured(repo):
        print("%s: the repository configures no ruff, nothing to format" % file)
        return 0
    program = ruff(repo)
    if program is None:
        print(
            "%s configures ruff but no ruff is installed: run `uv sync` in it, or put ruff on PATH"
            % repo,
            file=sys.stderr,
        )
        return 2
    target = Path(args.destination) / file.name
    before = file.read_text(encoding="utf-8")
    done = subprocess.run(
        [program, "format", "--stdin-filename", str(repo / target), "-"],
        input=before,
        capture_output=True,
        text=True,
        cwd=repo,
    )
    if done.returncode != 0:
        print("%s: ruff refused it as %s:\n%s" % (file, target, done.stderr.strip()), file=sys.stderr)
        return 1
    if done.stdout == before:
        print("%s: already formatted as %s" % (file, target))
        return 0
    file.write_text(done.stdout, encoding="utf-8")
    print("%s: formatted as %s" % (file, target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
