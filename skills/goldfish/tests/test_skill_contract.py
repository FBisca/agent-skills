import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel):
    return (ROOT / rel).read_text()


def skill_text():
    return read("SKILL.md") + "\n" + read("reader.md")


class GoldfishContract(unittest.TestCase):
    def test_S15c_manual_only_invocation(self):
        self.assertRegex(read("SKILL.md"), r"(?m)^disable-model-invocation: true$")
        self.assertRegex(read("agents/openai.yaml"), r"(?m)^\s+allow_implicit_invocation: false$")

    def test_S18_reader_contract(self):
        reader = read("reader.md")
        for p in ("Open only the one file", "CANNOT PARAPHRASE", "**Blocker**",
                  "Quote the statement", "Undefined terms", "What this says"):
            self.assertIn(p, reader)
        skill = read("SKILL.md")
        self.assertIn("fresh subagent", skill)
        self.assertIn("never edits the doc", skill)
        self.assertIn("Blocker", skill)

    def test_S19_apache_attribution(self):
        t = read("NOTICE.md")
        for s in ("Apache-2.0", "elephant-goldfish-model", "agents/comprehension.md", "modified"):
            self.assertIn(s, t)
        first = read("reader.md").splitlines()[0]
        for x in ("Apache-2.0", "agents/comprehension.md", "modified", "NOTICE.md"):
            self.assertIn(x, first)
        self.assertIn("2026-10-29", t)
        self.assertNotIn("Felippe Bisca's setup", t)
        self.assertTrue((ROOT / "LICENSE").exists())
        self.assertIn("Apache License", read("LICENSE"))

    def test_S32_names_no_person(self):
        hits = [p.name for p in ROOT.rglob("*.md") if "felippe" in p.read_text().lower()]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
