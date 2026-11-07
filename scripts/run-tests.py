#!/usr/bin/env python3
"""Run the repo contract tests and every skill's unittest suite, one process per test file.

Each test file gets its own process, so a file that hangs cannot take the others down, and the files run in
parallel: the whole gate is the wall clock of the slowest file, not the sum of them. `JOBS` limits the workers.

Usage: `python3 scripts/run-tests.py` (the gate is `scripts/run-tests.sh`).
"""

import os
from pathlib import Path
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]


def suites():
    """Every suite of the repo: the contract tests and each skill's own tests."""
    directories = [ROOT / "tests"] + sorted(ROOT.glob("skills/*/tests"))
    for directory in directories:
        if directory.is_dir():
            yield directory


def files():
    """Every test file of every suite, as (directory, file name)."""
    for directory in suites():
        for path in sorted(directory.glob("test_*.py")):
            yield directory, path.name


def run(directory, name):
    """One test file in its own process: (directory, name, the finished process)."""
    argv = [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(directory), "-t", str(directory), "-p", name]
    return directory, name, subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True)


def main():
    jobs = int(os.environ.get("JOBS", "0")) or (os.cpu_count() or 4)
    every = list(files())
    print("== %d test files on %d workers" % (len(every), jobs))
    started = time.monotonic()
    failed = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for directory, name, result in pool.map(lambda item: run(*item), every):
            if result.returncode != 0:
                failed.append((directory, name, result))
                print("FAIL %s/%s" % (directory.relative_to(ROOT), name))
    for directory, name, result in failed:
        print("---- %s/%s" % (directory.relative_to(ROOT), name))
        print(result.stdout + result.stderr)
    print("== %d files, %d failed, %ds" % (len(every), len(failed), round(time.monotonic() - started)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
