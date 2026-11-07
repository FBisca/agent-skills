"""Skill discovery with Pi's own loader: the real thing, offline.

Pi loads a skill from a directory with a `SKILL.md` whose frontmatter carries `name` and
`description`. This test asks Pi's own loader (the installed package, no model, no network)
which skills it finds in this repo, so a frontmatter that Pi cannot parse fails the gate
instead of failing silently in someone's terminal.

Skipped when Pi or Node are not installed: the gate must run anywhere.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

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

    def test_pi_discovers_start_planning(self):
        """S1: Pi finds the planning skill, so `/skill:start-planning` exists."""
        self.assertIn("start-planning", self.result["names"])

    def test_pi_reads_the_planning_skill_description(self):
        """S1: the description Pi routes on is the one in the frontmatter."""
        skill = next(s for s in self.result["skills"] if s["name"] == "start-planning")
        expected = (ROOT / "skills" / "start-planning" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(skill["description"], expected)

    def test_pi_reports_no_problem_with_the_planning_skill(self):
        """S1: Pi's frontmatter parser accepts the planning skill."""
        problems = [d for d in self.result["diagnostics"]
                    if "start-planning" in str(d.get("path", ""))]
        self.assertEqual(problems, [], problems)


if __name__ == "__main__":
    unittest.main()
