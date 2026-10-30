import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel):
    return (ROOT / rel).read_text()


def skill_text():
    text = read("SKILL.md")
    prep = ROOT / "prep.md"
    return text + ("\n" + prep.read_text() if prep.exists() else "")


class IdeaAnswerContract(unittest.TestCase):
    def test_S15b_manual_only_invocation(self):
        self.assertRegex(read("SKILL.md"), r"(?m)^disable-model-invocation: true$")
        self.assertRegex(read("agents/openai.yaml"), r"(?m)^\s+allow_implicit_invocation: false$")

    def test_S17_routing_and_handoff(self):
        t = skill_text()
        for p in (
            "operator/user, finance, compliance, decider, engineering",
            "handed to `/start-planning` Gather",
            "only after the user's yes",
            "never sends",
            "the user's summary",
            "no message bodies, no client or investor names",
            "`Source: unknown`",
            "`entry: decided`",
            "/prototype",
            "90-templates/project.md",
            "`[[assumptions]] [[answers]] [[gates]]` under `## Notes`",
            "`type: note`, `area`, `project: \"[[<Title>]]\"`, `created`, `updated`, `tags: []`",
            "add `[[answers]]` to the index note's `## Notes`",
            "under `## Hours` in the index note",
            "`Owner: <type> (<role>)` (the type first, so the cap counts it), `Date: YYYY-MM-DD`, `Link: <link>`, `Summary:`",
            "`accepted by <decider role>: engineering, to /start-planning Gather`",
            "`Summary: open → PRD Further Notes`",
            "the index note (`<Title>.md`, the one root-level note with `type: project`)",
            "`type: project`, `status: idea`, `stage: answering`, `entry: decided`, `decider: <role>`",
            "idea-check only needs a non-empty result",
            "python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 2",
            "gate2: pass by <role>: <reason>",
        ):
            self.assertIn(p, t)
        self.assertLess(t.rindex("`/to-spec`"), t.rindex("`/goldfish <folder>/PRD.md`"))
        self.assertRegex(read("SKILL.md"), r"(?s)Hand-off:\*\*.*`/to-spec`.*`/goldfish")
        self.assertNotIn("idea.md", t)
        self.assertLessEqual(len(read("SKILL.md").splitlines()), 120)


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
        self.assertIn("`Owner: <type> (<role>)`", text)
        self.assertLessEqual(len(text.splitlines()), 120)

    def test_S31_asks_which_three_to_five_items_and_routes_only_those(self):
        text = read("SKILL.md")
        for p in ("Show the open items in that order and ask the user which 3–5 to take to people",
                  "Route and prepare only those",
                  "The rest stay in `assumptions.md` untouched until gate 2",
                  "after `/to-spec` writes `PRD.md`, set `stage: prd`",
                  "`accepted by <decider role>: low priority, not asked`",
                  "except items not picked",
                  "`people-cap` above 12"):
            self.assertIn(p, text)

    def test_S32_names_no_person(self):
        hits = [p.name for p in ROOT.rglob("*.md") if "felippe" in p.read_text().lower()]
        self.assertEqual(hits, [])

    def test_S34_ethical_owner_guidance(self):
        self.assertIn("- ethical risk (could it harm someone, would users object if they knew): compliance, or the decider when it is a product call", read("SKILL.md"))
        self.assertNotIn("- ethical:", read("SKILL.md"))

    def test_S36_tests_use_type_criterion_and_prep_uses_criterion(self):
        t = skill_text()
        self.assertIn("test as `<type>: <success criterion>`", t)
        self.assertIn("for an `A<n>` row the bar is its test criterion: missing it kills or changes the idea", t)
        self.assertNotIn("the row's criterion is the answer that kills", t)
        prep = read("prep.md")
        self.assertIn("Passes if: <the row's test criterion, verbatim>", prep)
        self.assertIn("Kills the idea: <criterion missed:", prep)
        self.assertIn("data or spike: no conversation", prep)
        self.assertIn("level definitions in the `idea_check.py` docstring", read("SKILL.md"))

    def test_S35_ranking_follows_row_order(self):
        t = read("SKILL.md")
        self.assertIn("Rank in `assumptions.md` row order (agreed at gate 1); unknown frame questions by importance", t)


if __name__ == "__main__":
    unittest.main()
