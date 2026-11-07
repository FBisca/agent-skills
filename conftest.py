"""The pytest wiring for the repo's suites.

The suites live in `tests/` and in each skill's own `tests/` folder, and they import their
neighbours by name (`from fixtures import ...`, `from test_archive import ...`). pytest runs with
`--import-mode=importlib` so that two files with the same name in different skills
(`test_skill_contract.py`) do not collide; this file puts every suite folder on `sys.path` so those
plain imports still resolve.

It also keeps the partition honest: every test carries exactly one of `unit` and `integration`, so
the fast suite never quietly loses a test and the full suite never runs one twice.
"""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent


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
