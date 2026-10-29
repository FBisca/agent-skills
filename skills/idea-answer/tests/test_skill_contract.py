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
            "only after Felippe's yes",
            "never sends",
            "Felippe's summary",
            "no message bodies, no client or investor names",
            "`Source: unknown`",
            "`entry: decided`",
            "/prototype",
            "90-templates/project.md",
            "`[[assumptions]] [[answers]] [[gates]]` under `## Notes`",
            "`type: note`, `area`, `project: \"[[<Title>]]\"`, `created`, `updated`, `tags: []`",
            "add `[[answers]]` to the index note's `## Notes`",
            "under `## Hours` in the index note",
            "`Owner: <role>`, `Date: YYYY-MM-DD`, `Link: <link>`, `Summary:`",
            "`accepted by <decider role>: engineering, to /start-planning Gather`",
            "`Summary: open → PRD Open Questions`",
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


if __name__ == "__main__":
    unittest.main()
