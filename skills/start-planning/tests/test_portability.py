"""The start-planning contract the engine and every harness read.

The plan the skill documents is the `plan/2` the engine reads; the steps that need another context
ship what they run. The skill's prose is not tested here: a Markdown sentence is not behaviour.
"""

import pytest
from pathlib import Path
import re
import unittest

import yaml


pytestmark = pytest.mark.unit

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")

REFERENCE = (SKILL.parent / "references" / "plan-yaml.md").read_text(encoding="utf-8")

# The engine (agent-runtime's `plan/2` loader) reads the contract the skill writes: its top-level
# keys, the requirement, scenario and ticket fields, and the values it accepts for size and difficulty.
TOP_KEYS = ["schema", "slug", "goal", "spec", "archive", "requirements", "tickets"]
CHANGE_KEYS = {"added", "modified", "removed"}
REQUIREMENT_KEYS = {"title", "shall", "scenarios"}
REMOVAL_KEYS = {"title", "why"}
SCENARIO_KEYS = {"id", "name", "when", "then"}
TICKET_KEYS = {"id", "delivers", "satisfies", "paths", "size", "difficulty", "blocked_by", "owner",
               "risk", "repo"}
SIZE_VALUES = ["small", "regular"]
DIFFICULTY_VALUES = ["simple", "complex"]


def skeleton():
    return yaml.safe_load(re.search(r"```yaml\n(.*?)```", REFERENCE, re.S).group(1))


class EngineContract(unittest.TestCase):
    def test_the_documented_skeleton_is_the_plan_2_the_engine_reads(self):
        plan = skeleton()
        self.assertEqual(list(plan), TOP_KEYS, "the top-level keys, in order")
        self.assertEqual(plan["schema"], "plan/2")
        changes = plan["requirements"]
        self.assertEqual(set(changes), CHANGE_KEYS)
        requirements = changes["added"] + changes["modified"]
        self.assertTrue(requirements)
        for requirement in requirements:
            self.assertEqual(set(requirement), REQUIREMENT_KEYS)
            self.assertIn("SHALL", requirement["shall"])
            self.assertTrue(1 <= len(requirement["scenarios"]) <= 3)
        scenarios = [s for r in requirements for s in r["scenarios"]]
        self.assertEqual(set().union(*map(set, scenarios)), SCENARIO_KEYS, "every scenario field, no other")
        for removal in changes["removed"]:
            self.assertEqual(set(removal), REMOVAL_KEYS)
        self.assertEqual(set().union(*map(set, plan["tickets"])), TICKET_KEYS, "every ticket field, no other")
        ids = {s["id"] for s in scenarios}
        for ticket in plan["tickets"]:
            self.assertLessEqual(set(ticket["satisfies"]), ids, "a ticket satisfies declared scenarios")

    def test_the_documented_size_and_difficulty_are_the_engines_vocabulary(self):
        for column, values in (("size", SIZE_VALUES), ("difficulty", DIFFICULTY_VALUES)):
            found = re.search(r"\*\*`%s`\*\* \(`([^`]+)`\)" % column, TEXT)
            self.assertIsNotNone(found, "the documented %s vocabulary" % column)
            documented = [value.strip() for value in found.group(1).split("|")]
            self.assertEqual(documented, values, "%s: the documented vocabulary is the engine's" % column)


class Delegation(unittest.TestCase):
    def test_the_gather_packet_and_the_dependency_check_ship_with_the_skill(self):
        self.assertTrue((SKILL.parent / "references" / "gather-packet.md").is_file())
        self.assertTrue((SKILL.parent / "scripts" / "check_deps.py").is_file())

    def test_every_script_the_skill_names_exists(self):
        """A broken path is a broken step."""
        for name in set(re.findall(r"(?:\.\./[a-z-]+/)?scripts/[A-Za-z_]+\.py", TEXT)):
            self.assertTrue((SKILL.parent / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
