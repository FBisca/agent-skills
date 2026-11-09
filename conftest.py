"""The pytest wiring for the repo's suites.

The suites live in `tests/` and in each skill's own `tests/` folder, and they import their
neighbours by name (`from fixtures import ...`, `from test_archive import ...`). pytest runs with
`--import-mode=importlib` so that two files with the same name in different skills
(`test_skill_contract.py`) do not collide; this file puts every suite folder on `sys.path` so those
plain imports still resolve.

It also keeps the partition honest: every test carries exactly one of `unit` and `integration`, so
the fast suite never quietly loses a test and the full suite never runs one twice.

Finally it polices the run itself. A run ends with a failing status, and says why, when:

- the fast suite (the default selection) takes as long as its budget or longer;
- the run leaves a temporary entry behind: the run hands every temporary file it makes to one
  directory of its own, and that directory must be empty when the run ends;
- a `unit` test is skipped, or any test is skipped without a reason.

Each check is a pure function (`budget_problem`, `close_session_temp`, `skip_problem`) that the
session hooks call; `tests/test_repo.py` tests those functions, not a wall clock.
"""

from collections import namedtuple
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import pytest

ROOT = Path(__file__).resolve().parent

# The fast suite must finish in under this many seconds (AGENTS.md: "under 3 seconds").
FAST_SUITE_BUDGET_SECONDS = 3.0

# Set by the run that owns the temporary directory. An xdist worker inherits it and uses the same
# directory; only the owner checks it, once every worker has finished.
TEMP_ENV = "AGENT_SKILLS_SUITE_TEMP"

Skip = namedtuple("Skip", "nodeid reason unit")


class Run:
    """What this process's run owns and has seen."""

    def __init__(self):
        self.owner = False
        self.temp = None  # the directory this run hands to its temporary files
        self.saved = None  # the settings the run replaced, restored at the end
        self.started = None  # perf_counter at the session start
        self.skips = []  # one Skip per skipped test report
        self.problems = []  # what ends the run, as messages


RUN = Run()


def suite_folders():
    """Every folder holding a suite of this repo."""
    folders = [ROOT / "tests"]
    folders.extend(sorted(ROOT.glob("skills/*/tests")))
    return [folder for folder in folders if folder.is_dir()]


for folder in suite_folders():
    path = str(folder)
    if path not in sys.path:
        sys.path.insert(0, path)


def names_a_path(config):
    """Did the user name a file or a folder to run?

    `config.args` cannot answer it: pytest fills it with `testpaths` when the user names
    nothing. The original command line can: a token that is a path in the working directory
    is the user choosing what runs.
    """
    base = Path(str(config.invocation_params.dir))
    for token in config.invocation_params.args or ():
        token = str(token)
        if token.startswith("-"):
            continue
        if (base / token).exists():
            return True
    return False


def is_fast_run(config):
    """The default run: the fast suite, with no marker expression and no file named."""
    return not config.getoption("markexpr", "") and not names_a_path(config)


def pytest_collection_modifyitems(config, items):
    """Every test is either a unit test or an integration test, and never both."""
    unmarked = []
    for item in items:
        unit = item.get_closest_marker("unit") is not None
        integration = item.get_closest_marker("integration") is not None
        if unit == integration:  # neither or both
            unmarked.append(item.nodeid)
    if unmarked:
        raise pytest.UsageError(
            "every test must carry exactly one of the markers `unit` and `integration`:\n  "
            + "\n  ".join(sorted(unmarked))
        )
    if config.getoption("markexpr", "") or names_a_path(config):
        return  # the user chose the selection: `-m ...` or a file to run
    keep = [item for item in items if item.get_closest_marker("unit") is not None]
    if len(keep) == len(items):
        return
    deselected = [item for item in items if item.get_closest_marker("unit") is None]
    config.hook.pytest_deselected(items=deselected)
    items[:] = keep


def budget_problem(elapsed, budget=FAST_SUITE_BUDGET_SECONDS):
    """The message when a fast run took as long as its budget or longer, else None."""
    if elapsed < budget:
        return None
    return "the fast suite took %.2f s, over its %.0f-second budget (AGENTS.md: under 3 seconds)" % (elapsed, budget)


def open_session_temp(root):
    """A fresh directory under `root` that this run gives its temporary files."""
    return Path(tempfile.mkdtemp(prefix="agent-skills-suite-", dir=str(root)))


def close_session_temp(base):
    """Remove the run's temporary directory; name what was left in it, or None when it was empty."""
    left = sorted(entry.name for entry in base.iterdir())
    shutil.rmtree(base, ignore_errors=True)
    if not left:
        return None
    return "the run left temporary entries behind: " + ", ".join(left)


def skip_problem(skips):
    """The messages for a skipped unit test and for a skip with no reason, or None."""
    problems = []
    for skip in skips:
        if skip.unit:
            problems.append("unit test skipped: %s (%s)" % (skip.nodeid, skip.reason or "no reason given"))
        elif not skip.reason:
            problems.append("skipped without a reason: %s" % skip.nodeid)
    return "; ".join(problems) or None


def skip_lines(skips):
    """The line the run prints for each skipped test: the test and the reason it gave."""
    return ["SKIPPED %s: %s" % (skip.nodeid, skip.reason) for skip in skips]


def skip_reason(report):
    longrepr = report.longrepr
    text = longrepr[2] if isinstance(longrepr, tuple) and len(longrepr) == 3 else longrepr
    return str(text or "").removeprefix("Skipped: ")


def pytest_configure(config):
    global RUN
    RUN = Run()
    inherited = os.environ.get(TEMP_ENV)
    if inherited:  # an xdist worker: its controller owns the directory
        tempfile.tempdir = inherited
        return
    RUN.owner = True
    # pytest's own tmp_path root stays where it was: pytest keeps its last runs there on purpose.
    os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", tempfile.gettempdir())
    RUN.temp = open_session_temp(tempfile.gettempdir())
    RUN.saved = (tempfile.tempdir, os.environ.get("TMPDIR"), os.environ.get(TEMP_ENV))
    tempfile.tempdir = str(RUN.temp)
    os.environ["TMPDIR"] = str(RUN.temp)
    os.environ[TEMP_ENV] = str(RUN.temp)


def pytest_sessionstart(session):
    if RUN.owner:
        RUN.started = time.perf_counter()


def pytest_runtest_logreport(report):
    if report.skipped and not hasattr(report, "wasxfail"):
        RUN.skips.append(Skip(report.nodeid, skip_reason(report), "unit" in report.keywords))


def pytest_sessionfinish(session):
    if not RUN.owner:
        return
    problems = []
    if RUN.started is not None and is_fast_run(session.config):
        problems.append(budget_problem(time.perf_counter() - RUN.started))
    problems.append(close_session_temp(RUN.temp))
    problems.append(skip_problem(RUN.skips))
    RUN.problems = [problem for problem in problems if problem]
    if RUN.problems and session.exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter):
    if RUN.skips:
        terminalreporter.write_sep("=", "skipped tests")
        for line in skip_lines(RUN.skips):
            terminalreporter.write_line(line)
    if RUN.problems:
        terminalreporter.write_sep("=", "suite checks")
        for problem in RUN.problems:
            terminalreporter.write_line("SUITE CHECK FAILED: " + problem, red=True)


def pytest_unconfigure(config):
    if not RUN.owner:
        return
    if RUN.temp is not None and RUN.temp.exists():  # the run ended before its session finished
        close_session_temp(RUN.temp)
    tempfile.tempdir, tmpdir, inherited = RUN.saved
    for name, value in (("TMPDIR", tmpdir), (TEMP_ENV, inherited)):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    RUN.owner = False
