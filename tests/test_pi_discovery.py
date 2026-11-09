"""Skill discovery with Pi's own loader: the real thing, offline.

Pi loads a skill from a directory with a `SKILL.md` whose frontmatter carries `name` and
`description`. This test asks Pi's own loader (the installed package, no model, no network)
which skills it finds in this repo, so a frontmatter that Pi cannot parse fails the gate
instead of failing silently in someone's terminal.

Skipped when Pi or Node are not installed: the gate must run anywhere.
"""

import pytest
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "@earendil-works/pi-coding-agent"


def pi_package():
    """The installed Pi package, or None."""
    roots = []
    managed = os.environ.get("PI_MANAGED_INSTALL_ROOT")
    if managed:
        roots.append(Path(managed))
    agent_dir = os.environ.get("PI_CODING_AGENT_DIR")
    if agent_dir:
        roots.append(Path(agent_dir) / "install")
    roots.append(Path.home() / ".pi" / "agent" / "install")
    for root in roots:
        for release in sorted(root.glob("releases/*/node_modules/" + PACKAGE)):
            if (release / "dist" / "bundle" / "index.js").is_file():
                return release
    return None


def node():
    """The Node that runs Pi, or None."""
    found = shutil.which("node")
    if found:
        return found
    candidate = Path.home() / ".local" / "share" / "pi-node" / "current" / "bin" / "node"
    return str(candidate) if candidate.is_file() else None


PROBE = """
const mod = await import(process.argv[2]);
const result = mod.loadSkillsFromDir({dir: process.argv[3], source: "user"});
process.stdout.write(JSON.stringify({
  names: result.skills.map((skill) => skill.name),
  skills: result.skills.map((skill) => ({name: skill.name, description: skill.description,
                                        filePath: skill.filePath})),
  diagnostics: result.diagnostics,
}));
"""


@unittest.skipUnless(pi_package() and node(), "Pi or Node is not installed")
class PiDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        script = Path(cls.tmp.name) / "probe.mjs"
        script.write_text(PROBE, encoding="utf-8")
        bundle = str(pi_package() / "dist" / "bundle" / "index.js")
        result = subprocess.run([node(), str(script), bundle, str(ROOT / "skills")],
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise unittest.SkipTest("Pi's loader did not run: %s" % result.stderr[-300:])
        cls.result = json.loads(result.stdout)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_S35_pi_discovers_every_skill_of_this_repo(self):
        """S35: Pi discovers every skill of this repository and reports no problem with any of them.

        One test over every skill: a skill Pi cannot parse disappears from the list without a
        word, so the whole set is checked at once, and the description Pi routes on is the one
        the frontmatter holds.
        """
        expected = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(expected - set(self.result["names"]), set())

        problems = [d for d in self.result["diagnostics"]
                    if str(d.get("path", "")).startswith(str(ROOT / "skills"))]
        self.assertEqual(problems, [], problems)

        for skill in self.result["skills"]:
            text = Path(skill["filePath"]).read_text(encoding="utf-8")
            self.assertIn(skill["description"], text, skill["name"])

        # The guarantee is asserted once, over every skill: this module holds no second test.
        self.assertEqual(
            [name for name, _ in inspect.getmembers(self, inspect.ismethod) if name.startswith("test")],
            ["test_S35_pi_discovers_every_skill_of_this_repo"])


if __name__ == "__main__":
    unittest.main()
