"""Repo-level contracts: skill metadata, the upstream lock and the VAULT_DIR requirement."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

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


def repo_files():
    """The files this repo ships or is working on: tracked, plus untracked and not ignored.

    Ignored files (a local `.claude/settings.local.json`, caches) are the machine's, not the
    repo's, and must not decide whether the gate is green.
    """
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / name for name in listed]


class SkillMetadata(unittest.TestCase):
    def test_every_skill_has_matching_name_and_description(self):
        dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
        self.assertTrue(dirs)
        for d in dirs:
            meta = frontmatter(d / "SKILL.md") if (d / "SKILL.md").is_file() else None
            self.assertIsNotNone(meta, f"{d.name}: SKILL.md with frontmatter")
            self.assertEqual(meta.get("name"), d.name, f"{d.name}: name matches dir")
            self.assertTrue(meta.get("description"), f"{d.name}: description")

    def test_no_skill_text_hardcodes_a_claude_skills_path(self):
        for path in SKILLS.rglob("SKILL.md"):
            self.assertNotIn("~/.claude/skills/", path.read_text(encoding="utf-8"), str(path))

    def test_derived_and_copied_skills_carry_a_notice(self):
        for name in ("handoff", "zoom-out", "cold-read"):
            self.assertTrue((SKILLS / name / "NOTICE.md").is_file(), name)
        self.assertFalse((SKILLS / "frontend-design").exists())

    def test_idea_frame_bundles_the_project_template(self):
        self.assertTrue((SKILLS / "idea-frame" / "templates" / "project.md").is_file())

    def test_no_symlinks_or_absolute_user_paths(self):
        for path in repo_files():
            self.assertFalse(path.is_symlink(), f"symlink: {path}")
            if path.is_file() and path.suffix in {".md", ".py", ".json", ".sh", ".yml", ".yaml"} and path != Path(__file__):
                self.assertNotIn("/Users/", path.read_text(encoding="utf-8", errors="ignore"), str(path))


class UpstreamLock(unittest.TestCase):
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


class WorkflowDoc(unittest.TestCase):
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
    def test_unused_skills_are_neither_carried_nor_locked(self):
        lock = json.loads((ROOT / "skills.lock.json").read_text(encoding="utf-8"))
        locked = {e["name"] for e in lock["skills"] + lock["vendored_unmodified"]}
        for name in sorted(REMOVED):
            self.assertFalse((SKILLS / name).exists(), name)
            self.assertNotIn(name, locked, name)

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
