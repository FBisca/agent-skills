"""The suite's own runner: it names the file that never finished.

`scripts/run-tests.py` runs every test file of the repository in its own process. A file that
hangs must not take the run with it: the runner kills it at `TEST_TIMEOUT`, names it, and exits
non-zero. The test points the runner at a fixture suite so the hang is a fixture, not the
repository.
"""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-tests.py"
TIMEOUT = 3


def load_runner():
    """The runner module, loaded in process: its `main` is the seam the refusal tests call."""
    spec = importlib.util.spec_from_file_location("run_tests", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_S36_the_runner_refuses_a_root_that_is_no_test_suite(tmp_path, capsys):
    """A root that is not a directory, a directory with no test file, and `--help` each exit non-zero and name what they were given."""
    runner = load_runner()
    missing = tmp_path / "no-such-root"
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "README.md").write_text("no tests here\n", encoding="utf-8")
    cases = [str(missing), str(tmp_path / "notes"), "--help"]

    for given in cases:
        code = runner.main([given])
        captured = capsys.readouterr()
        assert code != 0, "the runner must refuse %r, it exited %s" % (given, code)
        assert given in captured.out + captured.err, "the refusal must name %r:\n%s" % (given, captured.out + captured.err)
        assert "test files" not in captured.out, "the runner must not report a run for %r" % given


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
