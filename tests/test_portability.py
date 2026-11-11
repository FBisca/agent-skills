"""Harness portability at the repo level: discovery, the shared skills' own contracts, the plan format.

S3: the shared skills keep the Claude Code and Codex behaviour they had.
S4: the test suite runs offline and enforces the Markdown plan contract.
test-suite/R2: the engine reads the plans this repository tracks.
yaml-eec/S26: the tree carries no converge skill; the engine's `plan check` reads a YAML plan.
"""

import importlib.util
import pytest
from pathlib import Path
import re
import subprocess
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

# These read the plans through `git ls-files`: a subprocess, so an integration boundary (test-suite/R12).
GIT_READERS = {
    "test_S4_every_tracked_plan_keeps_the_plan_contract",
    "test_the_engine_reads_every_tracked_plan",
}

PLAN_HEADINGS = ("Why now", "Sources", "Decisions", "Scenarios", "Out of scope", "Risks",
                 "Seams", "Tickets")

# The engine (agent-runtime's driver) reads the plan: these are the column names it requires,
# in the order this repository writes them (Status last), and the values it accepts.
TICKET_COLUMNS = ("#", "What it delivers", "Satisfies", "Blocked by", "Paths", "Size",
                  "Difficulty", "Owner", "Status")
TICKET_HEADER = "| " + " | ".join(TICKET_COLUMNS) + " |"
SIZE_VALUES = ("small", "regular")
DIFFICULTY_VALUES = ("simple", "complex")


def ticket_table(text):
    """A Markdown plan's Tickets table, as the engine reads it: the header cells and each row."""
    section = re.split(r"(?m)^## Tickets[^\n]*\n", text, maxsplit=1)
    if len(section) < 2:
        return [], []
    body = re.split(r"(?m)^## ", section[1], maxsplit=1)[0]
    lines = [line for line in body.splitlines() if line.startswith("|")]
    if len(lines) < 2:
        return [], []

    def cells(line):
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    header = cells(lines[0])
    return header, [dict(zip(header, cells(line))) for line in lines[2:]]

# The harness-specific instructions each shared skill carries, and must keep.
SHARED_CONTRACTS = {
    "cold-read": ("Claude:", "Codex:"),
    "orchestrate": ("<engine> launch <plan>", "plan approve"),
    "start-planning": ("scripts/fresh_context.py", "references/delegation.md"),
}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return fields


def tracked_plans():
    """The plans this repo tracks: the gate must not depend on untracked files."""
    listed = subprocess.run(["git", "ls-files", "docs/plans"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.split()
    return [ROOT / name for name in listed if name.endswith(".plan.md")]


class Discovery(unittest.TestCase):
    """Pi and the other harnesses discover a skill the same way: a directory with a SKILL.md."""

    @pytest.mark.unit
    def test_every_skill_is_discoverable_and_portable(self):
        names = {}
        for directory in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            skill = directory / "SKILL.md"
            self.assertTrue(skill.is_file(), "%s: SKILL.md" % directory.name)
            meta = frontmatter(skill)
            self.assertIsNotNone(meta, "%s: frontmatter" % directory.name)
            name = meta.get("name", "")
            self.assertEqual(name, directory.name, "%s: name matches the folder" % directory.name)
            self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$", "%s: portable name" % name)
            self.assertLessEqual(len(name), 64, "%s: name length" % name)
            description = meta.get("description", "")
            self.assertTrue(description.strip(), "%s: description" % directory.name)
            self.assertLessEqual(len(description), 1024, "%s: description length" % directory.name)
            self.assertNotIn(name, names, "%s: name collides with %s" % (name, names.get(name)))
            names[name] = directory.name


class SharedSkills(unittest.TestCase):
    @pytest.mark.unit
    def test_S3_the_shared_skills_keep_their_harness_contracts(self):
        """S3: the Pi work did not change what the other harnesses do."""
        for name, needles in SHARED_CONTRACTS.items():
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, "%s: %s" % (name, needle))


class NoHarnessInstructions(unittest.TestCase):
    """A skill body states the workflow; the harness's own discovery states the invocation."""

    @pytest.mark.unit
    def test_the_harness_detail_lives_in_a_reference(self):
        """The per-harness dispatch is loaded on demand, not with the skill."""
        reference = SKILLS / "start-planning" / "references" / "delegation.md"
        self.assertTrue(reference.is_file())
        text = reference.read_text(encoding="utf-8")
        for harness in ("Claude Code", "Codex", "Pi"):
            self.assertIn(harness, text)


class PlanContract(unittest.TestCase):
    """S4: the Markdown plan format other skills parse is enforced on the plans in this repo."""

    @pytest.mark.integration
    def test_S4_every_tracked_plan_keeps_the_plan_contract(self):
        plans = tracked_plans()
        self.assertTrue(plans)
        for plan in plans:
            text = plan.read_text(encoding="utf-8")
            name = plan.name
            self.assertRegex(text, r"(?m)^Slug: `[^`]+`", name)
            self.assertRegex(text, r"Living spec: `docs/specs/[^`]+`", name)
            self.assertRegex(text, r"Status: ", name)
            headings = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
            for heading in PLAN_HEADINGS:
                self.assertTrue(any(item.startswith(heading) for item in headings),
                                "%s: missing heading %s" % (name, heading))
            scenarios = set(re.findall(r"^- \*\*S(\d+[a-z]?)\*\* WHEN .*, THEN ", text, re.M))
            self.assertTrue(scenarios, "%s: no scenario lines" % name)
            self.assertIn(TICKET_HEADER, text, "%s: ticket columns" % name)


class EnginePlanContract(unittest.TestCase):
    """test-suite/R2: the engine reads the plans this repository tracks."""

    @pytest.mark.integration
    def test_the_engine_reads_every_tracked_plan(self):
        """test-suite/R2: the engine's contract, asserted by name, holds for every plan it reads."""
        for plan in tracked_plans():
            text = plan.read_text(encoding="utf-8")
            columns, rows = ticket_table(text)
            self.assertEqual(columns, list(TICKET_COLUMNS), "%s: ticket columns" % plan.name)
            self.assertEqual(columns[-1], "Status", "%s: Status is the last column" % plan.name)
            for row in rows:
                size = (row.get("Size") or "").strip()
                difficulty = (row.get("Difficulty") or "").strip()
                if (row.get("Owner") or "").strip().lower() != "agent":
                    # A person-owned ticket leaves both empty; the engine reads no route for it.
                    self.assertEqual((size, difficulty), ("", ""),
                                     "%s: %s is not a code ticket" % (plan.name, row.get("#")))
                    continue
                self.assertIn(size, SIZE_VALUES, "%s: %s Size" % (plan.name, row.get("#")))
                self.assertIn(difficulty, DIFFICULTY_VALUES,
                              "%s: %s Difficulty" % (plan.name, row.get("#")))
            lines = text.split("\n## ", 1)[0].splitlines()
            if not any(re.search(r"\bStatus: APPROVED\b", line) for line in lines):
                continue  # the engine runs no plan that is not approved
            self.assertTrue(any(re.match(r"^Slug: `[^`]+`", line) for line in lines),
                            "%s: no backticked Slug" % plan.name)
            self.assertTrue(any(re.match(r"^[^*]*Status: APPROVED\b", line) for line in lines),
                            "%s: no unbolded Status: APPROVED" % plan.name)


class NoConverge(unittest.TestCase):
    @pytest.mark.unit
    def test_S26_the_tree_carries_no_converge_skill(self):
        """yaml-eec/S26: converge's checks live in the engine's gates; no skill copy is left."""
        self.assertFalse((SKILLS / "converge").exists())
        for path in (ROOT / "README.md", ROOT / "docs" / "workflow.md"):
            text = path.read_text(encoding="utf-8")
            for name in ("/converge", "skills/converge", "converge.py"):
                self.assertNotIn(name, text, path.name)


class MarkerMeaning(unittest.TestCase):
    """test-suite/R12: the marker text and the suite agree on what `unit` and `integration` mean."""

    @staticmethod
    def kinds(function):
        """The partition markers a test function carries."""
        return {mark.name for mark in getattr(function, "pytestmark", [])} & {"unit", "integration"}

    @staticmethod
    def load(path):
        spec = importlib.util.spec_from_file_location("s31_" + path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @pytest.mark.unit
    def test_the_marker_text_and_the_suite_agree(self):
        """test-suite/R12: `unit` is in-process, inside the test's own temporary directory; `integration`
        is a real boundary; the tests that guard pure logic carry `unit`."""
        config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        markers = {text.split(":", 1)[0]: text for text in config["tool"]["pytest"]["ini_options"]["markers"]}
        self.assertIn("in process", markers["unit"])
        self.assertIn("temporary directory", markers["unit"])
        self.assertIn("a temporary directory is not a boundary", markers["unit"].lower())
        self.assertIn("real component boundary", markers["integration"])
        self.assertIn("A temporary directory is not a boundary.", (ROOT / "AGENTS.md").read_text(encoding="utf-8"))

        gatherer = self.load(SKILLS / "start-planning" / "tests" / "test_fresh_context.py").GathererTests
        for name in unittest.TestLoader().getTestCaseNames(gatherer):
            expected = {"integration"} if name.startswith("test_printed_answer") else {"unit"}
            self.assertEqual(self.kinds(getattr(gatherer, name)), expected, name)

        for case in (Discovery, SharedSkills, NoHarnessInstructions, PlanContract, EnginePlanContract, NoConverge):
            for name in unittest.TestLoader().getTestCaseNames(case):
                expected = {"integration"} if name in GIT_READERS else {"unit"}
                self.assertEqual(self.kinds(getattr(case, name)), expected, "%s.%s" % (case.__name__, name))


if __name__ == "__main__":
    unittest.main()

