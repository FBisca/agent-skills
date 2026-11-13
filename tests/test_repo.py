"""Repo-level contracts: skill metadata, the upstream lock and the VAULT_DIR requirement."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

import pytest

import conftest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

# Upstream skills this repo no longer carries; each must reinstall from the lock.
STRIPPED = {
    "diagnosing-bugs", "domain-modeling", "grilling", "prototype", "retro",
    "setup-matt-pocock-skills", "to-spec", "writing-for-agents",
    "hyperframes", "hyperframes-cli", "hyperframes-registry", "media-use",
}

# Skills dropped as unused: neither carried here nor installed from the lock.
REMOVED = {
    "caveman", "teach", "codebase-design", "improve-codebase-architecture",
    "to-tickets", "triage", "impeccable",
}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return fields


class SkillMetadata(unittest.TestCase):
    @pytest.mark.unit
    def test_derived_and_copied_skills_carry_a_notice(self):
        for name in ("handoff", "zoom-out", "cold-read"):
            self.assertTrue((SKILLS / name / "NOTICE.md").is_file(), name)
        self.assertFalse((SKILLS / "frontend-design").exists())

    @pytest.mark.unit
    def test_idea_frame_bundles_the_project_template(self):
        self.assertTrue((SKILLS / "idea-frame" / "templates" / "project.md").is_file())


class UpstreamLock(unittest.TestCase):
    @pytest.mark.unit
    def test_S7_public_skills_valid_and_dropped_upstreams_reinstallable(self):
        """S7: linked repo exposes every public skill; each dropped upstream reinstalls with the documented command."""
        public = {p.name for p in SKILLS.iterdir() if p.is_dir()}
        self.assertTrue(public)
        for name in public:
            self.assertIsNotNone(frontmatter(SKILLS / name / "SKILL.md"), name)
        lock = json.loads((ROOT / "skills.lock.json").read_text(encoding="utf-8"))
        entries = {e["name"]: e for e in lock["skills"]}
        self.assertTrue(STRIPPED <= set(entries), STRIPPED - set(entries))
        self.assertFalse(set(entries) & public, "locked upstreams must not also be vendored")
        for kept in lock["vendored_unmodified"]:
            self.assertIn(kept["name"], public, "unmodified upstream copies stay in the repo")
        for name, entry in entries.items():
            self.assertRegex(entry["install"], r"^npx skills add \S+ .*--skill " + re.escape(name) + r"(\s|$)", name)
            self.assertTrue(entry["source"], name)
        installer = (ROOT / "scripts" / "install-upstream.sh").read_text(encoding="utf-8")
        self.assertIn("skills.lock.json", installer)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add FBisca/agent-skills", readme)
        self.assertIn("install-upstream.sh", readme)


class SuiteMarkers(unittest.TestCase):
    """Every test in this repo carries exactly one of the markers `unit` and `integration`.

    `conftest.py` refuses a suite whose tests carry neither or both, so a file that forgets the marker does not
    fail its own test: it breaks the collection of the whole run. This test names the file instead.
    """

    MARKERS = ("unit", "integration")

    def suite_files(self):
        files = [path for path in (ROOT / "tests").glob("test_*.py")]
        files.extend(sorted((ROOT / "skills").glob("*/tests/test_*.py")))
        return files

    def markers_in(self, node):
        """The markers a node carries: its own decorators and the ones it inherits."""
        found = set()
        for decorator in getattr(node, "decorator_list", []):
            text = ast.unparse(decorator)
            for marker in self.MARKERS:
                if "pytest.mark.%s" % marker in text:
                    found.add(marker)
        return found

    @pytest.mark.unit
    def test_every_test_carries_exactly_one_marker(self):
        unmarked = []
        for path in self.suite_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            module = set()
            for statement in tree.body:
                if isinstance(statement, ast.Assign) and any(
                        getattr(t, "id", "") == "pytestmark" for t in statement.targets):
                    for marker in self.MARKERS:
                        if "pytest.mark.%s" % marker in ast.unparse(statement):
                            module.add(marker)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    inherited = module | self.markers_in(node)
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                            found = inherited | self.markers_in(item)
                            if len(found) != 1:
                                unmarked.append("%s:%s" % (path.relative_to(ROOT), item.name))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                    found = module | self.markers_in(node)
                    if len(found) != 1:
                        unmarked.append("%s:%s" % (path.relative_to(ROOT), node.name))
        self.assertEqual(sorted(set(unmarked)), [], "every test must carry exactly one of unit and integration")


class WorkflowDoc(unittest.TestCase):
    @pytest.mark.unit
    def test_S7a_workflow_doc_exists_and_readme_links_to_it(self):
        """S7a: the repo carries the workflow doc and the README links to it."""
        doc = ROOT / "docs" / "workflow.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertNotIn("agents/.agents", text)
        self.assertNotIn("workflow-evals", text)
        self.assertIn("(docs/workflow.md)", (ROOT / "README.md").read_text(encoding="utf-8"))


class VaultDir(unittest.TestCase):
    def run_check(self, env_extra, *args):
        env = {k: v for k, v in os.environ.items() if k != "VAULT_DIR"}
        env.update(env_extra)
        script = SKILLS / "idea-frame" / "scripts" / "idea_check.py"
        return subprocess.run([sys.executable, "-B", str(script), *args], capture_output=True, text=True, env=env)

    def make_vault(self, root):
        folder = Path(root) / "01-projects" / "demo"
        folder.mkdir(parents=True)
        (folder / "Demo.md").write_text(
            "---\ntype: project\nstatus: idea\nstage: framing\nentry: raw\ndecider: CFO\n---\n# Demo\n",
            encoding="utf-8")
        return folder

    @pytest.mark.integration
    def test_S8_idea_frame_fails_naming_vault_dir_when_unset_and_works_when_set(self):
        """S8: unset VAULT_DIR fails naming it; set, the script works (slug resolves under the vault)."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make_vault(tmp)
            unset = self.run_check({}, str(folder))
            self.assertEqual(unset.returncode, 3, unset.stdout + unset.stderr)
            self.assertIn("VAULT_DIR", unset.stdout + unset.stderr)
            slug = self.run_check({"VAULT_DIR": tmp}, "demo")
            self.assertEqual(slug.returncode, 0, slug.stdout + slug.stderr)
            self.assertIn("PASS", slug.stdout)
            missing = self.run_check({"VAULT_DIR": str(Path(tmp) / "nope")}, "demo")
            self.assertEqual(missing.returncode, 3, missing.stdout + missing.stderr)
            self.assertIn("VAULT_DIR", missing.stdout + missing.stderr)

    @pytest.mark.integration
    def test_idea_check_exits_3_naming_vault_dir_when_unset_or_not_a_directory(self):
        """test-suite/R7: WHEN VAULT_DIR is unset or is not a directory, THEN idea_check.py exits 3 and names VAULT_DIR."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make_vault(tmp)
            not_a_dir = Path(tmp) / "file.txt"
            not_a_dir.write_text("x", encoding="utf-8")
            for env in ({}, {"VAULT_DIR": str(not_a_dir)}):
                result = self.run_check(env, str(folder))
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("VAULT_DIR", result.stdout + result.stderr)

    @pytest.mark.integration
    def test_S8_idea_answer_and_excalidraw_name_vault_dir(self):
        """S8: idea-answer and excalidraw read the vault from VAULT_DIR, never a hardcoded path."""
        for skill in ("idea-frame", "idea-answer", "excalidraw", "explain-video"):
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("VAULT_DIR", text, skill)
            self.assertNotIn("~/developer/vault", text, skill)
            self.assertNotIn("Obsidian", text, skill)
        env = {k: v for k, v in os.environ.items() if k != "VAULT_DIR"}
        code = ("import sys; sys.dont_write_bytecode = True; sys.path.insert(0, %r); import excali; excali.vault_dir()"
                % str(SKILLS / "excalidraw" / "scripts"))
        unset = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env)
        self.assertEqual(unset.returncode, 3, unset.stdout + unset.stderr)
        self.assertIn("VAULT_DIR", unset.stdout + unset.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            env["VAULT_DIR"] = tmp
            ok = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env)
            self.assertEqual(ok.returncode, 0, ok.stderr)

    @pytest.mark.integration
    def test_excalidraw_vault_dir_exits_3_naming_vault_dir_when_unset_or_not_a_directory(self):
        """test-suite/R7: WHEN VAULT_DIR is unset or is not a directory, THEN excali.vault_dir() exits 3 and names VAULT_DIR."""
        code = ("import sys; sys.dont_write_bytecode = True; sys.path.insert(0, %r); import excali; excali.vault_dir()"
                % str(SKILLS / "excalidraw" / "scripts"))
        base = {k: v for k, v in os.environ.items() if k != "VAULT_DIR"}
        with tempfile.TemporaryDirectory() as tmp:
            not_a_dir = Path(tmp) / "file.txt"
            not_a_dir.write_text("x", encoding="utf-8")
            for extra in ({}, {"VAULT_DIR": str(not_a_dir)}):
                env = dict(base, **extra)
                result = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("VAULT_DIR", result.stdout + result.stderr)


class RemovedSkillsTest(unittest.TestCase):
    @pytest.mark.unit
    def test_unused_skills_are_neither_carried_nor_locked(self):
        lock = json.loads((ROOT / "skills.lock.json").read_text(encoding="utf-8"))
        locked = {e["name"] for e in lock["skills"] + lock["vendored_unmodified"]}
        for name in sorted(REMOVED):
            self.assertFalse((SKILLS / name).exists(), name)
            self.assertNotIn(name, locked, name)

    @pytest.mark.integration
    def test_S15_gh_implement_from_issue_is_absent_from_skills_catalog_marketplace_and_tests(self):
        name = "gh-implement-" + "from-issue"  # built, so this file does not mention it either
        self.assertFalse((SKILLS / name).exists())
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        for path in files:
            if not (ROOT / path).is_file():
                continue
            self.assertNotIn(name, path)
            try:
                text = (ROOT / path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn(name, text, path)
        for entry in json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())["plugins"]:
            self.assertNotIn(name, json.dumps(entry))


class ProseOnlySkills(unittest.TestCase):
    @pytest.mark.unit
    def test_readme_names_exactly_the_skills_without_a_scripts_folder(self):
        """test-suite/R14: readme names exactly the skills without a scripts folder."""
        # The fact: a skill has executable behaviour exactly when it ships a scripts/ folder.
        in_tree = {p.parent.name for p in SKILLS.glob("*/scripts") if p.is_dir()}
        without = {p.name for p in SKILLS.iterdir() if p.is_dir()} - in_tree
        # The README's list: the bullets under its "no executable behaviour" heading.
        lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("### ") and "executable behaviour" in line)
        named = set()
        for line in lines[start + 1:]:
            if line.startswith("#"):
                break
            match = re.match(r"- `([a-z0-9-]+)`\s*$", line)
            if match:
                named.add(match.group(1))
        self.assertEqual(named - without, set(), "README names a skill that has a scripts/ folder")
        self.assertEqual(without - named, set(), "README omits a skill that has no scripts/ folder")


class SuiteGuard(unittest.TestCase):
    """conftest.py ends a run that is over the fast-suite budget, one that leaves a temporary entry behind, or one
    that skipped a unit test. Each check is tested through the function its session hook calls."""

    @pytest.mark.unit
    def test_a_fast_run_at_or_over_the_budget_fails_and_one_under_it_passes(self):
        """test-suite/R8: a fast run at or over the budget fails and one under it passes."""
        self.assertIsNone(conftest.budget_problem(2.99))
        problem = conftest.budget_problem(3.25)
        self.assertIsNotNone(problem)
        self.assertIn("3.25", problem)
        self.assertIsNotNone(conftest.budget_problem(3.0), "under 3 seconds: exactly 3 is not under")

    @pytest.mark.unit
    def test_a_run_that_leaves_a_temporary_entry_fails_and_its_directory_is_removed(self):
        """test-suite/R9: a run that leaves a temporary entry fails and its directory is removed."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = conftest.open_session_temp(root)
            self.assertIsNone(conftest.close_session_temp(clean))
            self.assertFalse(clean.exists())
            leaky = conftest.open_session_temp(root)
            (leaky / "left-behind").mkdir()
            problem = conftest.close_session_temp(leaky)
            self.assertIn("left-behind", problem)
            self.assertFalse(leaky.exists())

    @pytest.mark.unit
    def test_a_skipped_unit_test_fails_the_run_and_every_skip_is_reported_with_its_reason(self):
        """test-suite/R10: a skipped unit fails the run and every skip is reported with its reason."""
        unit = conftest.Skip("tests/test_x.py::T::test_one", "Pi is not installed", True)
        integration = conftest.Skip("tests/test_y.py::T::test_two", "Node is not installed", False)
        self.assertIn("test_one", conftest.skip_problem([unit, integration]))
        self.assertNotIn("test_two", conftest.skip_problem([unit, integration]))
        self.assertIsNone(conftest.skip_problem([integration]))
        self.assertIsNotNone(conftest.skip_problem([conftest.Skip("tests/test_z.py::T::test_three", "", False)]))
        self.assertEqual(conftest.skip_lines([integration]),
                         ["SKIPPED tests/test_y.py::T::test_two: Node is not installed"])


class SuiteHooks(unittest.TestCase):
    """The session hooks of conftest.py, called in process with fakes: the run state and the temporary-directory
    settings are swapped for each test and restored after it, so the run that executes these tests is untouched."""

    ENV = ("TMPDIR", conftest.TEMP_ENV, "PYTEST_DEBUG_TEMPROOT")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)  # runs last
        self.saved_run = conftest.RUN
        self.saved_tempdir = tempfile.tempdir
        self.saved_env = {name: os.environ.get(name) for name in self.ENV}
        self.addCleanup(self.restore)  # runs before the cleanup above
        for name in self.ENV:
            os.environ.pop(name, None)
        tempfile.tempdir = self.tmp.name
        conftest.RUN = conftest.Run()

    def restore(self):
        conftest.RUN = self.saved_run
        tempfile.tempdir = self.saved_tempdir
        for name, value in self.saved_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def own_run(self):
        """Start a run that owns a temporary directory, as pytest does; it is ended after the test."""
        conftest.pytest_configure(None)
        self.addCleanup(conftest.pytest_unconfigure, None)

    @staticmethod
    def session(exitstatus=pytest.ExitCode.OK):
        config = SimpleNamespace(getoption=lambda name, default=None: default,
                                 invocation_params=SimpleNamespace(dir=str(ROOT), args=()))
        return SimpleNamespace(config=config, exitstatus=exitstatus)

    @staticmethod
    def skipped(nodeid, longrepr, unit):
        return SimpleNamespace(skipped=True, nodeid=nodeid, longrepr=longrepr,
                               keywords={"unit": True} if unit else {})

    @pytest.mark.unit
    def test_the_session_end_fails_an_over_budget_fast_run(self):
        """test-suite/R8: the session end fails an over budget fast run."""
        self.own_run()
        session = self.session()
        conftest.RUN.started = time.perf_counter() - 3.5
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.TESTS_FAILED)
        self.assertIn("budget", conftest.RUN.problems[0])

    @pytest.mark.unit
    def test_the_session_end_keeps_an_under_budget_fast_run_green(self):
        """test-suite/R8: the session end keeps an under budget fast run green."""
        self.own_run()
        session = self.session()
        conftest.RUN.started = time.perf_counter() - 0.1
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.OK)
        self.assertEqual(conftest.RUN.problems, [])

    @pytest.mark.unit
    def test_a_failing_run_keeps_its_own_failing_status(self):
        """test-suite/R8: a failing run keeps its own failing status."""
        self.own_run()
        session = self.session(pytest.ExitCode.TESTS_FAILED)
        conftest.RUN.started = time.perf_counter() - 3.5
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.TESTS_FAILED)

    @pytest.mark.unit
    def test_configure_hands_the_run_its_own_directory_and_unconfigure_restores_the_temp_settings(self):
        """test-suite/R9: configure hands the run its own directory and unconfigure restores the temp settings."""
        before = tempfile.tempdir
        conftest.pytest_configure(None)
        self.assertTrue(conftest.RUN.owner)
        self.assertTrue(conftest.RUN.temp.is_dir())
        self.assertEqual(tempfile.tempdir, str(conftest.RUN.temp))
        self.assertEqual(os.environ["TMPDIR"], str(conftest.RUN.temp))
        self.assertEqual(os.environ[conftest.TEMP_ENV], str(conftest.RUN.temp))
        self.assertIn(Path(self.tmp.name), conftest.RUN.temp.parents)
        temp = conftest.RUN.temp
        conftest.pytest_unconfigure(None)
        self.assertEqual(tempfile.tempdir, before)
        self.assertNotIn(conftest.TEMP_ENV, os.environ)
        self.assertFalse(temp.exists())

    @pytest.mark.unit
    def test_the_session_end_fails_a_run_that_left_an_entry_behind(self):
        """test-suite/R9: the session end fails a run that left an entry behind."""
        self.own_run()
        (conftest.RUN.temp / "left-behind").mkdir()
        session = self.session()
        conftest.RUN.started = None
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.TESTS_FAILED)
        self.assertIn("left-behind", " ".join(conftest.RUN.problems))

    @pytest.mark.unit
    def test_a_skipped_unit_test_is_recorded_and_fails_the_session_end(self):
        """test-suite/R10: a skipped unit is recorded and fails the session end."""
        self.own_run()
        conftest.pytest_runtest_logreport(self.skipped("tests/x.py::T::test_one", ("tests/x.py", 3, "Skipped: needs pi"), True))
        self.assertEqual(conftest.RUN.skips, [conftest.Skip("tests/x.py::T::test_one", "needs pi", True)])
        session = self.session()
        conftest.RUN.started = None
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.TESTS_FAILED)

    @pytest.mark.unit
    def test_an_integration_skip_with_a_reason_is_recorded_and_does_not_fail(self):
        """test-suite/R10: an integration skip with a reason is recorded and does not fail."""
        self.own_run()
        conftest.pytest_runtest_logreport(self.skipped("tests/y.py::T::test_two", ("tests/y.py", 4, "Skipped: no node"), False))
        self.assertEqual(conftest.RUN.skips, [conftest.Skip("tests/y.py::T::test_two", "no node", False)])
        session = self.session()
        conftest.RUN.started = None
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.OK)

    @pytest.mark.unit
    def test_a_bare_skip_with_no_message_is_a_skip_without_a_reason(self):
        """test-suite/R10: a bare skip with no message is a skip without a reason."""
        self.own_run()
        conftest.pytest_runtest_logreport(self.skipped("tests/z.py::T::test_bare", ("tests/z.py", 5, "Skipped"), False))
        self.assertEqual(conftest.RUN.skips[0].reason, "")
        self.assertIsNotNone(conftest.skip_problem(conftest.RUN.skips))
        session = self.session()
        conftest.RUN.started = None
        conftest.pytest_sessionfinish(session)
        self.assertEqual(session.exitstatus, pytest.ExitCode.TESTS_FAILED)


if __name__ == "__main__":
    unittest.main()
