"""Harness portability at the repo level: discovery, the shared skills' own contracts, the plan format.

S3: the shared skills keep the Claude Code and Codex behaviour they had.
S4: the test suite runs offline and enforces the Markdown plan contract.
test-suite/R1: every tracked plan is read by the reader the gate uses.
test-suite/R2: the engine reads the plans this repository tracks.
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
    "test_the_gate_reader_reads_every_tracked_plan",
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


def load_converge():
    """The gate's own plan reader, in process: `converge.py` is the reader the gate uses."""
    script = SKILLS / "converge" / "scripts" / "converge.py"
    spec = importlib.util.spec_from_file_location("gate_converge", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


converge = load_converge()

# The harness-specific instructions each shared skill carries, and must keep.
SHARED_CONTRACTS = {
    "cold-read": ("Claude:", "Codex:"),
    "orchestrate": ("scripts/orchestrate.py launch", "Status: APPROVED"),
    "converge": ("scripts/converge.py", "REFUSED"),
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
            # The coverage the gate reads, with the gate's own reader.
            ids, tickets = converge.plan_data(text)
            covered = {identifier for satisfies, _ in tickets.values() for identifier in satisfies}
            for scenario in scenarios:
                self.assertIn("S" + scenario, covered, "%s: S%s is in no ticket" % (name, scenario))
            self.assertEqual(covered, set(ids), "%s: a ticket satisfies an undeclared scenario" % name)


class PlanReader(unittest.TestCase):
    """test-suite/R1: the plan format is read by the reader the gate uses."""

    HEAD = ("# Plan: the reader\n\nSlug: `reader`. Living spec: `docs/specs/reader.md`. "
            "Status: APPROVED 2026-11-09.\n\n## Scenarios\n\n"
            "- **S1** WHEN the gate reads a plan, THEN it yields the scenario ids and the "
            "ticket rows.\n\n")

    @pytest.mark.integration
    def test_the_gate_reader_reads_every_tracked_plan(self):
        """test-suite/R1: every tracked plan yields its scenario ids and its ticket rows; a plan
        whose Tickets table is missing or has no rows is refused."""
        plans = tracked_plans()
        self.assertTrue(plans)
        for plan in plans:
            text = plan.read_text(encoding="utf-8")
            ids, tickets = converge.plan_data(text)
            self.assertTrue(ids, "%s: no scenario ids" % plan.name)
            self.assertTrue(tickets, "%s: no ticket rows" % plan.name)
            rows = converge.plan_rows(text)
            self.assertEqual(len(rows), len(tickets), "%s: the reader's rows disagree" % plan.name)
        missing = self.HEAD + "## Tickets\n\nno table here\n"
        empty = self.HEAD + ("## Tickets\n\n" + TICKET_HEADER + "\n"
                             + "|---|---|---|---|---|---|---|---|---|\n")
        for text in (missing, empty):
            self.assertTrue(converge.refusal(text), "a plan without ticket rows is refused")


class EnginePlanContract(unittest.TestCase):
    """test-suite/R2: the engine reads the plans this repository tracks."""

    @pytest.mark.integration
    def test_the_engine_reads_every_tracked_plan(self):
        """test-suite/R2: the engine's contract, asserted by name, holds for every plan it reads."""
        for plan in tracked_plans():
            text = plan.read_text(encoding="utf-8")
            columns = converge.ticket_table(text)[0]
            self.assertEqual(columns, list(TICKET_COLUMNS), "%s: ticket columns" % plan.name)
            self.assertEqual(columns[-1], "Status", "%s: Status is the last column" % plan.name)
            for row in converge.plan_rows(text):
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
            head = converge.plan_head(text)
            if head["status"] != "APPROVED":
                # The engine reads no status out of this head; the gate refuses the plan too,
                # so it never reaches the engine.
                self.assertTrue(converge.refusal(text),
                                "%s: the gate accepts a plan the engine cannot read" % plan.name)
                continue
            lines = head["head"].splitlines()
            self.assertTrue(any(re.match(r"^Slug: `[^`]+`", line) for line in lines),
                            "%s: no backticked Slug" % plan.name)
            self.assertTrue(any(re.match(r"^[^*]*Status: APPROVED\b", line) for line in lines),
                            "%s: no unbolded Status: APPROVED" % plan.name)


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

        for case in (Discovery, SharedSkills, NoHarnessInstructions, PlanContract, PlanReader, EnginePlanContract):
            for name in unittest.TestLoader().getTestCaseNames(case):
                expected = {"integration"} if name in GIT_READERS else {"unit"}
                self.assertEqual(self.kinds(getattr(case, name)), expected, "%s.%s" % (case.__name__, name))


if __name__ == "__main__":
    unittest.main()
