import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = "`id | assumption | if wrong | owner | source | test | result`"
ROADMAP = ("Never ask for roadmap end dates or a dated step sequence: they come after the PRD, once the product "
           "and outcomes are clear. Record a success horizon the user volunteers as given.")


def read(rel):
    return (ROOT / rel).read_text()


class IdeaFrameContract(unittest.TestCase):
    def test_S15a_manual_only_invocation(self):
        self.assertRegex(read("SKILL.md"), r"(?m)^disable-model-invocation: true$")
        self.assertRegex(read("agents/openai.yaml"), r"(?m)^\s+allow_implicit_invocation: false$")

    def test_S16_grills_with_seeds_and_unknown_rule(self):
        skill, seeds = read("SKILL.md"), read("seeds.md")
        self.assertIn("Call the Skill tool with `grilling`", skill)
        self.assertIn("[`seeds.md`](seeds.md)", skill)
        self.assertIn("`unknown` is recorded as `Source: unknown` and becomes a row in the map", skill)
        self.assertIn("never forced into a decision", skill)
        self.assertIn("look them up read-only", skill)
        for p in ("Heilmeier", "What are you trying to do", "How is success measured", "Internal FAQ"):
            self.assertIn(p, seeds)

    def test_S16_writes_files_runs_gate_and_hands_off(self):
        skill = read("SKILL.md")
        for p in ("frame.md", "assumptions.md", "~/.claude/skills/idea-frame/scripts/idea_check.py",
                  "idea_check.py <folder> --gate 1", "`## Gates`", "`## Hours`", "docstring"):
            self.assertIn(p, skill)
        last = skill.rstrip().splitlines()[-1]
        self.assertTrue(last.startswith("Done when"))
        self.assertIn("`/idea-answer <folder>`", last)
        self.assertLessEqual(len(skill.splitlines()), 120)

    def test_S16_uses_vault_template_and_notes(self):
        skill = read("SKILL.md")
        for p in ("~/developer/vault/90-templates/project.md", "`## Now`", "`## Notes`",
                  "[[frame]] [[assumptions]]", "`type: note`", 'project: "[[<Title>]]"',
                  "`stage: gate1`", "`stage: answering`"):
            self.assertIn(p, skill)

    def test_S32_names_no_person(self):
        hits = [p.name for p in ROOT.rglob("*.md") if "felippe" in p.read_text().lower()]
        self.assertEqual(hits, [])

    def test_S47_has_no_cut_steps(self):
        text = (read("SKILL.md") + read("seeds.md") + read("agents/openai.yaml")).lower()
        for cut in ("pre-mortem", "premortem", "terms", "reader", "top 3", "top-3", "story map", "story-map",
                    "importance", "evidence", "gates.md"):
            self.assertNotIn(cut, text)
        self.assertFalse((ROOT / "reader.md").exists())

    def test_S47_writes_the_v2_map(self):
        skill = read("SKILL.md")
        self.assertIn(MAP, skill)
        self.assertIn("owner is a free-text role", skill)
        self.assertIn("`<type>: <criterion>`", skill)
        self.assertIn("only for a real experiment", skill)

    def test_S47_gate_1_decision_goes_in_the_index_gates(self):
        skill = read("SKILL.md")
        self.assertIn("`- YYYY-MM-DD gate1: continue|kill|reshape: <reason>`", skill)
        self.assertIn("proposer alone below appetite, the decider above", skill)

    def test_S47_hands_off_to_idea_answer_for_every_open_row(self):
        skill = read("SKILL.md")
        self.assertIn("every open row", skill)
        self.assertIn("not optional", skill)
        self.assertNotIn("optional", skill.replace("not optional", ""))
        self.assertNotRegex(skill, r"3.5 items|pick")

    def test_S47_keeps_the_no_roadmap_dates_rule(self):
        self.assertIn(ROADMAP, read("SKILL.md"))


if __name__ == "__main__":
    unittest.main()
