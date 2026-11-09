#!/usr/bin/env python3
"""Run every suite of the repo, one process per test file.

Each test file gets its own pytest process, so a file that hangs cannot take the others down, and the files run
in parallel: the whole gate is the wall clock of the slowest file, not the sum of them. `JOBS` limits the workers;
`TEST_TIMEOUT` sets seconds per file (default 120).

The runner runs every test, unit and integration: it is the gate, not the fast suite.

It walks the repository root by default; name another root to walk that one instead, which is how a
test points it at a fixture suite.

Usage: `uv run python scripts/run-tests.py [ROOT]` (the gate is `scripts/run-tests.sh`).
"""

import os
from pathlib import Path
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]


def suites(root):
    """Every suite of the root: the contract tests and each skill's own tests."""
    directories = [root / "tests"] + sorted(root.glob("skills/*/tests"))
    for directory in directories:
        if directory.is_dir():
            yield directory


def files(root):
    """Every test file of every suite, as (directory, file name)."""
    for directory in suites(root):
        for path in sorted(directory.glob("test_*.py")):
            yield directory, path.name


def run(root, directory, name, timeout):
    """One test file in its own process: (directory, name, the exit code, the output)."""
    argv = [sys.executable, "-m", "pytest", "-q", "--no-header", "-m", "", str(directory / name)]
    try:
        result = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, timeout=timeout)
        return directory, name, result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b"") + (exc.stderr or b"")
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return directory, name, 1, output + "\nTimed out after %ss\n" % timeout


def main(argv=None):
    """Walk the root named on the command line (the repository by default): the exit code."""
    argv = list(sys.argv[1:] if argv is None else argv)
    given = argv[0] if argv else str(ROOT)
    root = Path(given).resolve()
    jobs = int(os.environ.get("JOBS", "0")) or (os.cpu_count() or 4)
    timeout = float(os.environ.get("TEST_TIMEOUT", "120"))
    if jobs < 1 or timeout <= 0:
        raise ValueError("JOBS and TEST_TIMEOUT must be positive")
    if not root.is_dir():
        print("refused: %s is not a directory" % given, file=sys.stderr)
        return 2
    every = list(files(root))
    if not every:
        print("refused: no test file under %s" % given, file=sys.stderr)
        return 2
    print("== %d test files on %d workers (timeout: %ss)" % (len(every), jobs, timeout), flush=True)
    started = time.monotonic()
    failed = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(run, root, directory, name, timeout) for directory, name in every]
        for future in as_completed(futures):
            directory, name, code, output = future.result()
            label = "%s/%s" % (directory.relative_to(root), name)
            if code:
                failed.append(label)
                print("FAIL %s\n%s" % (label, output), flush=True)
            else:
                print("PASS %s" % label, flush=True)
    print("== %d files, %d failed, %ds" % (len(every), len(failed), round(time.monotonic() - started)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
