"""The start-planning contract, as it must read from every harness.

S1: the planning contract survives the portability work, and Pi has a native invocation.
S2: the two steps that need another context (gather, grill) have a Pi path that runs or
fails loudly; neither may be skipped.
S3: the Claude Code and Codex paths are still there, unchanged in substance.
test-suite/R2: the plan the skill documents is the plan the engine reads.
yaml-eec/S26: the plan is the engine's YAML contract and its brief.
plan-layout/S14: the plan is one folder with its acceptance tests and a domain, and a Python
acceptance file is formatted under its destination before the plan is checked and approved.
"""

import pytest
from pathlib import Path
import re
import unittest


pytestmark = pytest.mark.unit

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")

REFERENCE = (SKILL.parent / "references" / "plan-yaml.md").read_text(encoding="utf-8")

# The brief's headings: the plan's diff in plain words; the scenarios and tickets live in the contract alone.
PLAN_HEADINGS = ("What changes", "Decisions", "Out of scope", "Risks")

# The engine (agent-runtime's `plan/1` loader) reads the contract the skill writes: its top-level
# keys, the scenario and ticket fields, and the values it accepts for size and difficulty.
TOP_KEYS = ("schema", "slug", "goal", "spec", "domain", "archive", "outcome", "scenarios", "tickets")
SCENARIO_KEYS = ("id", "when", "then", "evidence")
EVIDENCE_KEYS = ("check", "baseline", "acceptance", "package", "timeout", "env", "negative", "human")
TICKET_KEYS = ("id", "delivers", "satisfies", "paths", "size", "difficulty", "blocked_by", "owner",
               "risk", "evidence_waiver", "repo")
SIZE_VALUES = ("small", "regular")
DIFFICULTY_VALUES = ("simple", "complex")

# The contract the skill had before the portability work, sentence by sentence. A sentence
# that disappears is a behaviour that changed under Claude Code or Codex.
CLAUDE_CODEX_CONTRACT = (
    "**Input:** a feature, idea or task",
    "**Output:** one approved **plan**: one folder in the repository's plan directory",
    "**Hand-off:** `/orchestrate <plan.yaml>` builds it.",
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
    "**`satisfies`**: the scenario IDs the ticket makes true.",
    "**`owner`**: `agent` for code.",
    "then stop for one approval. Build nothing at this point.",
    "On the user's yes, run `<engine> plan approve <plan.yaml>`.",
    "Then hand off to `/orchestrate <plan.yaml>`.",
)


class PlanContract(unittest.TestCase):
    def test_S1_the_plan_headings_are_kept(self):
        """S1: the plan keeps the headings other skills parse."""
        headings = [line[3:].strip() for line in TEXT.splitlines() if line.startswith("## ")]
        for heading in PLAN_HEADINGS:
            self.assertTrue(any(item.startswith(heading) for item in headings),
                            "missing plan heading: %s" % heading)

    def test_S1_the_plan_writes_a_brief_not_a_narrative(self):
        """S1: the third plan file is the brief, the plan's diff in plain words."""
        self.assertIn("`brief.md`", TEXT)
        self.assertNotIn("plan.md`", TEXT)
        for heading in ("Why now", "Sources", "Seams"):
            self.assertNotIn("## " + heading, TEXT)

    def test_S1_the_scenario_shape_is_kept(self):
        """S1: scenarios stay WHEN/THEN with S-ids."""
        self.assertIn("    when: <condition>\n    then: <observable outcome>", REFERENCE)
        self.assertRegex(TEXT, r"`S<n>`")

    def test_S1_the_plan_stops_for_one_approval_and_the_engine_approves_it(self):
        """S1: the plan stops for one approval before anything is built; `plan approve` records it."""
        self.assertIn("then stop for one approval", TEXT)
        self.assertIn("plan approve <plan.yaml>", TEXT)
        self.assertIn("Never write `approval`", REFERENCE)

    def test_S14_a_python_acceptance_file_is_formatted_before_the_plan_is_checked(self):
        """plan-layout/S14: the evidence step formats under the destination before `plan check` and approval."""
        self.assertIn(
            "scripts/format_acceptance.py --repo <repo> <file> <package>/<acceptance.dir>/<domain>/", TEXT
        )
        self.assertLess(TEXT.index("format_acceptance.py"), TEXT.index("plan check <plan.yaml>"))

    def test_S14_the_plan_is_one_folder_named_by_the_repo_config(self):
        """plan-layout/S14: the plan folder lives under the repo config's plans dir, with its acceptance tests."""
        self.assertIn(".orchestrate/config.yaml", TEXT)
        self.assertIn("`<plans.dir>/YYYY-MM-DD-<slug>/`", TEXT)
        for part in ("`plan.yaml`", "`brief.md`", "`acceptance/`"):
            self.assertIn(part, TEXT)

    def test_S14_the_plan_proposes_a_domain_reusing_an_existing_one(self):
        """plan-layout/S14: a promoting plan names its domain, reusing a folder under the acceptance dir."""
        self.assertIn("`domain`", TEXT)
        self.assertIn("`<package>/<acceptance.dir>/`", TEXT)
        self.assertRegex(TEXT, r"[Rr]euse an existing")

    def test_S14_neither_the_skill_nor_the_skeleton_names_oracles(self):
        """plan-layout/S14: the tests are acceptance tests; the old word is gone."""
        self.assertNotIn("oracle", TEXT.lower())
        self.assertNotIn("oracle", REFERENCE.lower())


class EngineContract(unittest.TestCase):
    """test-suite/R2: the plan the skill documents is the plan the engine reads."""

    def test_the_documented_plan_carries_the_engine_contract(self):
        """test-suite/R2: the documented contract is the `plan/1` the engine reads."""
        skeleton = re.search(r"```yaml\n(.*?)```", REFERENCE, re.S).group(1)
        top = re.findall(r"^([a-z_]+):", skeleton, re.M)
        self.assertEqual(top, list(TOP_KEYS), "the top-level keys, in order")
        self.assertIn("schema: plan/1\n", skeleton)
        nested = set(re.findall(r"^ {2,6}(?:- )?([a-z_]+):", skeleton, re.M))
        for key in SCENARIO_KEYS + EVIDENCE_KEYS + TICKET_KEYS:
            self.assertIn(key, nested, "the documented field %s" % key)
        for column, values in (("size", SIZE_VALUES), ("difficulty", DIFFICULTY_VALUES)):
            found = re.search(r"\*\*`%s`\*\* \(`([^`]+)`\)" % column, TEXT)
            self.assertIsNotNone(found, "the documented %s vocabulary" % column)
            documented = [value.strip() for value in found.group(1).split("|")]
            self.assertEqual(documented, list(values),
                             "%s: the documented vocabulary is the engine's" % column)


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
        for name in set(re.findall(r"(?:\.\./[a-z-]+/)?scripts/[A-Za-z_]+\.py", TEXT)):
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
