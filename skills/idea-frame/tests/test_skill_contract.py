import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
        self.assertIn("`unknown` is recorded as `Source: unknown` and becomes an assumption to test", skill)
        self.assertIn("never forced into a decision", skill)
        for p in ("Heilmeier", "What are you trying to do", "How is success measured",
                  "Internal FAQ", "value", "usability", "feasibility", "viability", "ethical"):
            self.assertIn(p, seeds)

    def test_S16_writes_files_runs_gate_and_hands_off(self):
        skill = read("SKILL.md")
        for p in ("frame.md", "assumptions.md", "premortem.md", "gates.md",
                  "~/.claude/skills/idea-frame/scripts/idea_check.py",
                  "idea_check.py <folder> --gate 1"):
            self.assertIn(p, skill)
        last = skill.rstrip().splitlines()[-1]
        self.assertTrue(last.startswith("Done when"))
        self.assertIn("`/idea-answer <folder>`", last)
        self.assertLessEqual(len(skill.splitlines()), 120)

    def test_S16_uses_vault_template_and_notes(self):
        skill = read("SKILL.md")
        for p in ("~/developer/vault/90-templates/project.md", "`## Now`", "`## Notes`",
                  "[[frame]] [[assumptions]] [[premortem]] [[gates]]",
                  "`type: note`", 'project: "[[<Title>]]"',
                  "`Q<n>` keeps counting across rounds",
                  "append to `gates.md`, never overwrite",
                  "`stage: gate1`"):
            self.assertIn(p, skill)


    def test_S28_owner_guidance_and_cap(self):
        text = read("SKILL.md")
        for p in ("**Owner guidance**",
                  'finance: business and finance rules, e.g. "what fee must this clear?"; ask the ops owner of that rule; record owner finance',
                  "compliance: legal, security, data access, e.g. ",
                  "engineering: how the system behaves, e.g. ",
                  "never operators; goes to `/start-planning` Gather",
                  "operator/user: how people react to or use it, e.g. ",
                  "decider: scope and priority, e.g. ",
                  "product-behaviour rules (what the product does in a case): the person who owns that behaviour"):
            self.assertIn(p, text)
        self.assertIn("Every `Source: unknown` question gets an `Owner: <type>` line", text)

    def test_S30_continue_hands_off_to_to_spec_then_optional_answer_round(self):
        skill = read("SKILL.md")
        last = skill.rstrip().splitlines()[-1]
        self.assertIn("**Hand-off:** on continue, `/to-spec` with the idea folder loaded", skill)
        self.assertIn("after `/to-spec` writes `PRD.md`, set `stage: prd`", skill)
        self.assertIn("read `frame.md` and `assumptions.md` into the conversation", skill)
        self.assertIn("Further Notes must list every open assumption (`A<n>`, risk, owner type) as an open question", skill)
        self.assertIn("`/to-spec` with the idea folder loaded (Further Notes list each open assumption with its owner)", last)
        self.assertIn("`/idea-answer <folder>` only for the 3–5 items they pick", last)

    def test_S32_names_no_person(self):
        hits = [p.name for p in ROOT.rglob("*.md") if "felippe" in p.read_text().lower()]
        self.assertEqual(hits, [])

    def test_S33_story_map_pass_in_seeds_and_skill(self):
        skill, seeds = read("SKILL.md"), read("seeds.md")
        for p in ("## Story map", "actors", "user, system, our team", "what must be true here?", "not a lookup"):
            self.assertIn(p, seeds)
        self.assertIn("assumption row", seeds)
        self.assertIn("story-map pass", skill)

    def test_S34_seeds_has_ethical_branch_and_owner_guidance(self):
        seeds, skill = read("seeds.md"), read("SKILL.md")
        self.assertIn("**ethical**", seeds)
        self.assertIn("- ethical risk (could it harm someone, would users object if they knew): compliance, or the decider when it is a product call", skill)
        self.assertNotIn("- ethical:", skill)
        self.assertIn("compliance, or the decider when it is a product call", skill)

    def test_S35_levels_defined_and_map_reordered_before_gate_1(self):
        skill = read("SKILL.md")
        check = read("scripts/idea_check.py")
        for p in ("importance high: the idea dies if false; med: it changes the design; low: a detail",
                  "evidence high: a lookup or data; med: one first-hand report; low: an opinion, including the user's own"):
            self.assertIn(p, check)
            self.assertNotIn(p, skill)
        self.assertIn("level definitions in the `idea_check.py` docstring", skill)
        for p in ("sorted by importance high→low, then evidence low→high",
                  "the user reorders the rows",
                  "row order in `assumptions.md`",
                  "top 3 assumptions are the first 3 rows",
                  "from belief (not a lookup) gets evidence low",
                  "`<type>: <success criterion>`", "interview, prototype, data, survey, spike"):
            self.assertIn(p, skill)


if __name__ == "__main__":
    unittest.main()
