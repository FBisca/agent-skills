import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel):
    return (ROOT / rel).read_text()


def skill_text():
    return read("SKILL.md") + "\n" + read("prep.md")


class IdeaAnswerContract(unittest.TestCase):
    def test_S15b_manual_only_invocation(self):
        self.assertRegex(read("SKILL.md"), r"(?m)^disable-model-invocation: true$")
        self.assertRegex(read("agents/openai.yaml"), r"(?m)^\s+allow_implicit_invocation: false$")

    def test_S17_routing_and_records(self):
        t = skill_text()
        for p in ("only after the user's yes", "never sends", "no message bodies, no client or investor names",
                  "`entry: decided`", "/prototype", "90-templates/project.md",
                  "`type: project`, `status: idea`, `stage: answering`, `entry: decided`, `decider: <role>`",
                  "`type: note`", "`Owner:`, `Date: YYYY-MM-DD`, `Link:`, `Summary:`",
                  "python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 2"):
            self.assertIn(p, t)
        self.assertLessEqual(len(read("SKILL.md").splitlines()), 120)

    def test_S32_names_no_person(self):
        hits = [p.name for p in ROOT.rglob("*.md") if "felippe" in p.read_text().lower()]
        self.assertEqual(hits, [])

    def test_S48_routes_every_open_row_with_no_pick_or_cap(self):
        t = skill_text()
        self.assertIn("every open row", t)
        self.assertIn("no pick, no cap", t)
        for gone in ("3–5", "people-cap", "low priority, not asked", "12 items", "12-cap"):
            self.assertNotIn(gone, t)

    def test_S48_teammates_may_ask_owners(self):
        self.assertIn("teammates may ask the owner", read("SKILL.md"))

    def test_S48_mom_test_only_for_user_behaviour(self):
        t = skill_text()
        self.assertIn("Mom Test only for how users behave", t)
        self.assertIn("a policy or rule owner is asked for the current rule", t)
        self.assertNotIn("Questions in Mom Test form", t)

    def test_S48_rows_close_as_answered_or_accepted_with_revisit(self):
        t = read("SKILL.md")
        for p in ("`confirmed`, `killed`, `changed: <what>` or `accepted by <role>: <reason>; revisit: <trigger>`",
                  "`answers.md`", "`Owner:`, `Date: YYYY-MM-DD`, `Link:`, `Summary:`"):
            self.assertIn(p, t)

    def test_S48_keeps_the_brief_current_with_terms(self):
        t = read("SKILL.md")
        for p in ("`Brief.md`", "1-2 pages", "problem and who has it", "observable success", "appetite",
                  "solution sketch", "no-gos", "open questions with owners and answers", "`## Terms`",
                  "revised as answers land", "published by the user"):
            self.assertIn(p, t)

    def test_S48_cold_read_on_the_brief_then_commitment_in_the_index_gates(self):
        t = read("SKILL.md")
        self.assertIn("`/cold-read <folder>/Brief.md`", t)
        self.assertNotIn("/cold-read <folder>/PRD.md", t)
        self.assertIn("`- YYYY-MM-DD cold-read: pass <sha12>` or `accepted <sha12> by <role>`", t)
        self.assertIn("`- YYYY-MM-DD gate2: pass by <decider role>`", t)
        self.assertIn("no separate meeting", t)
        self.assertLess(t.index("`/cold-read <folder>/Brief.md`"), t.index("gate2: pass by"))

    def test_S48_names_to_spec_from_the_final_brief(self):
        done = next(l for l in read("SKILL.md").splitlines() if l.startswith("Done when"))
        self.assertIn("`/to-spec` is named from the final Brief", done)
        self.assertIn("final Brief", read("SKILL.md"))

    def test_S48_no_stale_files_or_terms(self):
        t = skill_text().lower()
        for gone in ("premortem", "gates.md", "pre-mortem", "importance", "evidence"):
            self.assertNotIn(gone, t)


if __name__ == "__main__":
    unittest.main()
