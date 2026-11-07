"""The dependency check: `grilling` is installed elsewhere, so the plan must find it or stop."""

import pytest
import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
import json
from pathlib import Path
import tempfile
import unittest


pytestmark = pytest.mark.unit

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_deps.py"
spec = importlib.util.spec_from_file_location("check_deps", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

REPO_ROOT = Path(__file__).resolve().parents[3]


class DependencyCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def run_check(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = app.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_an_installed_skill_is_found_and_named(self):
        skills = self.dir / "skills"
        (skills / "grilling").mkdir(parents=True)
        (skills / "grilling" / "SKILL.md").write_text("---\nname: grilling\n---\n", encoding="utf-8")
        code, out, _ = self.run_check("grilling", "--skills-dir", str(skills), "--only-dirs")
        self.assertEqual(code, app.FOUND)
        self.assertIn("FOUND grilling", out)
        self.assertIn(str(skills / "grilling" / "SKILL.md"), out)

    def test_a_missing_skill_fails_with_the_install_command(self):
        code, _, err = self.run_check("grilling", "--skills-dir", str(self.dir / "empty"), "--only-dirs")
        self.assertEqual(code, app.MISSING)
        self.assertIn("MISSING grilling", err)
        self.assertIn("npx skills add mattpocock/skills --skill grilling", err)
        self.assertIn("scripts/install-upstream.sh grilling", err)

    def test_the_install_command_comes_from_the_upstream_lock(self):
        lock = json.loads((REPO_ROOT / "skills.lock.json").read_text(encoding="utf-8"))
        entry = next(item for item in lock["skills"] if item["name"] == "grilling")
        self.assertEqual(app.install_command("grilling"), entry["install"])

    def test_the_check_lists_everywhere_it_looked(self):
        code, _, err = self.run_check("grilling", "--skills-dir", str(self.dir / "empty"), "--only-dirs")
        self.assertEqual(code, app.MISSING)
        self.assertIn("searched:", err)
        self.assertIn(str(self.dir / "empty"), err)

    def test_the_repo_skills_are_searched_too(self):
        self.assertIn(REPO_ROOT / "skills", app.candidate_dirs())


if __name__ == "__main__":
    unittest.main()
