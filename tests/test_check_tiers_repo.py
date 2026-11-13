"""agent-skills declares its own check tiers, so an orchestrate run briefs its workers with them."""

from pathlib import Path
import tomllib
import unittest

import pytest
import yaml

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]


class CheckTiersTests(unittest.TestCase):
    def test_S9_the_repo_config_declares_fast_affected_through_pytest_impacted_and_a_parallel_full(self):
        config = yaml.safe_load((ROOT / ".orchestrate" / "config.yaml").read_text())
        checks = config["checks"]
        self.assertEqual(checks["fast"], "uv run pytest")
        self.assertIn("--impacted", checks["affected"])
        self.assertIn("{base}", checks["affected"])
        self.assertEqual(checks["full"]["run"], 'uv run pytest -m "" -n auto')


# The skills' scripts run as files (a subprocess, or loaded by path), so pytest-impacted's import
# analysis selects no test for a change to one: the map routes each source to its tests.
SOURCE_GLOBS = ("scripts/*", "skills/*/scripts/*")


def _source_files():
    yield ROOT / "conftest.py"
    for pattern in SOURCE_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file():
                yield path


class AffectedTierSelectsTests(unittest.TestCase):
    def setUp(self):
        self.ini = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["pytest"][
            "ini_options"
        ]

    def test_the_affected_tier_names_a_module_so_pytest_impacted_runs(self):
        module = self.ini.get("impacted_module")
        self.assertTrue(module, "pytest-impacted refuses to run without impacted_module")
        self.assertTrue((ROOT / module.replace(".", "/")).is_dir())

    def test_every_source_file_maps_to_an_existing_test_path(self):
        from pytest_impacted.file_map import parse_file_map
        from pytest_impacted.strategies import matches_any_glob

        pairs = parse_file_map(self.ini.get("impacted_map", []))
        for target in {path for _, path in pairs}:
            self.assertTrue((ROOT / target).exists(), f"impacted_map target {target} is missing")
        unmapped = [
            path.relative_to(ROOT).as_posix()
            for path in _source_files()
            if not matches_any_glob(path.relative_to(ROOT).as_posix(), [g for g, _ in pairs])
        ]
        self.assertEqual(unmapped, [], "a change to these would select no test under --impacted")
