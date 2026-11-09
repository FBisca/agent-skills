"""The suite's own runner: it names the file that never finished.

`scripts/run-tests.py` runs every test file of the repository in its own process. A file that
hangs must not take the run with it: the runner kills it at `TEST_TIMEOUT`, names it, and exits
non-zero. The test points the runner at a fixture suite so the hang is a fixture, not the
repository.
"""

import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-tests.py"
TIMEOUT = 3


@pytest.mark.integration
def test_S25_the_runner_names_the_file_that_hangs(tmp_path):
    """A hanging file is named, fails the run, and does not outlive `TEST_TIMEOUT`."""
    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_fast.py").write_text("def test_fast():\n    assert True\n", encoding="utf-8")
    (suite / "test_hang.py").write_text(
        "import time\n\n\ndef test_hang():\n    time.sleep(300)\n", encoding="utf-8"
    )

    env = dict(os.environ, JOBS="2", TEST_TIMEOUT=str(TIMEOUT), PYTHONDONTWRITEBYTECODE="1")
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(RUNNER), str(tmp_path)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT * 10,
    )
    elapsed = time.monotonic() - started

    assert result.returncode != 0, "a hanging file must fail the run"
    assert "test_hang.py" in result.stdout, "the runner must name the file that hung:\n" + result.stdout
    assert "Timed out" in result.stdout, "the runner must say the file timed out:\n" + result.stdout
    assert "test_fast.py" in result.stdout, "the runner must report every file it ran:\n" + result.stdout
    assert elapsed < TIMEOUT + 10, "the run must end inside TEST_TIMEOUT, took %ss" % elapsed
