"""The start-planning contract, as it must read from every harness.

S1: the planning contract survives the portability work, and Pi has a native invocation.
S2: the two steps that need another context (gather, grill) have a Pi path that runs or
fails loudly; neither may be skipped.
S3: the Claude Code and Codex paths are still there, unchanged in substance.
"""

from pathlib import Path
import re
import unittest

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")

PLAN_HEADINGS = ("Why now", "Sources", "Decisions", "Scenarios", "Out of scope", "Risks",
                 "Seams", "Tickets")
TICKET_HEADER = ("| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty "
                  "| Owner | Status |")

# The contract the skill had before the portability work, sentence by sentence. A sentence
# that disappears is a behaviour that changed under Claude Code or Codex.
CLAUDE_CODEX_CONTRACT = (
    "**Input:** a feature, idea or task",
    "**Output:** one approved **plan** at `docs/plans/YYYY-MM-DD-<slug>.plan.md`",
    "**Hand-off:** `/orchestrate <plan-path>` builds it.",
    "A PRD is not a gate.",
    "It lists every source with its link (the request, the PRD if any, the Linear project and "
    "issues, the vault project note and its decision notes, RFCs, the living spec for the area)",
    "extracts each decision they already settle with its source, and reads the code the "
    "feature touches",
    "it runs read-only queries and returns the counts and edge cases: empty sets, conflicts, "
    "departed or archived owners",
    "on the decisions the sources leave open or contradict, bringing Gather's counts and edge "
    "cases into the questions",
    "Settled decisions enter the plan unasked, with their source.",
    "Each ticket is a **tracer bullet**",
    "**Satisfies**: the S-IDs the ticket makes true",
    "**Owner**: `agent` for code.",
    "then stop for one approval. Build nothing at this point.",
    "On approval, set `Status: APPROVED <date>` and hand off to `/orchestrate <plan-path>`.",
)


class PlanContract(unittest.TestCase):
    def test_S1_the_plan_headings_are_kept(self):
        """S1: the plan keeps the headings other skills parse."""
        headings = [line[3:].strip() for line in TEXT.splitlines() if line.startswith("## ")]
        for heading in PLAN_HEADINGS:
            self.assertTrue(any(item.startswith(heading) for item in headings),
                            "missing plan heading: %s" % heading)

    def test_S1_the_ticket_columns_are_kept(self):
        """S1: the ticket table keeps its columns, in order."""
        self.assertIn(TICKET_HEADER, TEXT)

    def test_S1_the_scenario_shape_is_kept(self):
        """S1: scenarios stay WHEN/THEN lines with S-ids."""
        self.assertIn("- **S1** WHEN <condition>, THEN <observable outcome>.", TEXT)
        self.assertRegex(TEXT, r"`S<n>`")

    def test_S1_the_status_starts_as_awaiting_approval(self):
        """S1: the plan stops for one approval before anything is built."""
        self.assertIn("Status: AWAITING APPROVAL", TEXT)
        self.assertIn("then stop for one approval", TEXT)

    def test_S1_pi_discovers_the_skill_natively(self):
        """S1: the frontmatter is what Pi routes on; the body carries no invocation syntax."""
        self.assertRegex(TEXT, r"description:.*Plan one feature")
        self.assertNotIn("/skill:", TEXT)


class Delegation(unittest.TestCase):
    """The skill states the requirement; the reference carries the per-harness detail."""

    def test_S2_the_gather_has_an_adapter(self):
        """S2: the fresh-context gather runs through the adapter the skill ships."""
        self.assertIn("scripts/fresh_context.py", TEXT)
        self.assertTrue((SKILL.parent / "scripts" / "fresh_context.py").is_file())
        self.assertTrue((SKILL.parent / "references" / "gather-packet.md").is_file())

    def test_S2_the_gather_may_not_be_skipped_when_it_fails(self):
        """S2: a failed, timed-out or malformed gather stops the plan."""
        self.assertIn("never continue into the plan on evidence it did not produce", TEXT)

    def test_S2_a_delegation_must_be_bounded_and_explicit(self):
        """S2: the requirement holds whatever mechanism the harness uses."""
        self.assertIn("no inherited context", TEXT)
        self.assertIn("timeout", TEXT)
        self.assertIn("structured findings", TEXT)
        self.assertIn("fails loudly", TEXT)

    def test_S2_a_missing_grilling_stops_the_plan(self):
        """S2: no silent skip of the grill."""
        self.assertIn("never skip the grill", TEXT)
        self.assertIn("never answer its questions yourself", TEXT)

    def test_S2_the_dependency_check_ships_with_the_skill(self):
        """S2: the missing dependency is detected by a script, not by hope."""
        self.assertTrue((SKILL.parent / "scripts" / "check_deps.py").is_file())

    def test_S3_the_claude_and_codex_paths_are_kept(self):
        """S3: Claude Code keeps the Task subagent and the Skill tool; Codex keeps its skill."""
        reference = (SKILL.parent / "references" / "delegation.md").read_text(encoding="utf-8")
        self.assertIn("Task subagent", reference)
        self.assertIn("the Skill tool with `grilling`", reference)
        self.assertIn("Codex", reference)

    def test_S3_the_pre_portability_contract_is_unchanged(self):
        """S3: every sentence the skill had before the portability work is still there."""
        for sentence in CLAUDE_CODEX_CONTRACT:
            self.assertIn(sentence, TEXT, sentence)

    def test_every_script_the_skill_names_exists(self):
        """The skill names scripts that exist: a broken path is a broken step."""
        for name in set(re.findall(r"scripts/[A-Za-z_]+\.py", TEXT)):
            self.assertTrue((SKILL.parent / name).is_file(), name)

    def test_the_reference_carries_the_harness_detail_not_the_skill(self):
        """The per-harness dispatch lives in the reference, so the main context stays small."""
        reference = (SKILL.parent / "references" / "delegation.md").read_text(encoding="utf-8")
        self.assertIn("Claude Code", reference)
        self.assertIn("Pi", reference)
        self.assertNotIn("Task subagent", TEXT)
        self.assertNotIn("Claude Code", TEXT)


if __name__ == "__main__":
    unittest.main()
