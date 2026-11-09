"""Repo-level contracts: skill metadata, the upstream lock and the VAULT_DIR requirement."""

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import pytest

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
    "tdd", "to-tickets", "triage", "impeccable",
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
            self.assertNotEqual(unset.returncode, 0)
            self.assertIn("VAULT_DIR", unset.stdout + unset.stderr)
            slug = self.run_check({"VAULT_DIR": tmp}, "demo")
            self.assertEqual(slug.returncode, 0, slug.stdout + slug.stderr)
            self.assertIn("PASS", slug.stdout)
            missing = self.run_check({"VAULT_DIR": str(Path(tmp) / "nope")}, "demo")
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("VAULT_DIR", missing.stdout + missing.stderr)

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
        self.assertNotEqual(unset.returncode, 0)
        self.assertIn("VAULT_DIR", unset.stdout + unset.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            env["VAULT_DIR"] = tmp
            ok = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env)
            self.assertEqual(ok.returncode, 0, ok.stderr)


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


if __name__ == "__main__":
    unittest.main()
