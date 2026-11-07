"""Harness portability at the repo level: discovery, the shared skills' own contracts, the plan format.

S3: the shared skills keep the Claude Code and Codex behaviour they had.
S4: the test suite runs offline and enforces the Markdown plan contract.
"""

from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

PLAN_HEADINGS = ("Why now", "Sources", "Decisions", "Scenarios", "Out of scope", "Risks",
                 "Seams", "Tickets")
TICKET_HEADER = "| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |"

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

    def test_the_pi_invocation_name_of_start_planning_is_its_folder_name(self):
        """`/skill:start-planning` only exists when the skill is named start-planning."""
        meta = frontmatter(SKILLS / "start-planning" / "SKILL.md")
        self.assertEqual(meta["name"], "start-planning")


class SharedSkills(unittest.TestCase):
    def test_S3_the_shared_skills_keep_their_harness_contracts(self):
        """S3: the Pi work did not change what the other harnesses do."""
        for name, needles in SHARED_CONTRACTS.items():
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, "%s: %s" % (name, needle))

    def test_S3_the_shared_skills_still_name_claude_and_codex(self):
        """S3: the skills that support several harnesses still say so."""
        text = (SKILLS / "cold-read" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Claude", text)
        self.assertIn("Codex", text)


class NoHarnessInstructions(unittest.TestCase):
    """A skill body states the workflow; the harness's own discovery states the invocation."""

    def test_no_skill_body_carries_an_invocation_syntax(self):
        """Native discovery provides the invocation: restating it only pollutes the context."""
        for directory in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            text = (directory / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("/skill:", text, "%s: Pi invocation syntax" % directory.name)
            self.assertNotIn("Invoke it as", text, "%s: invocation instructions" % directory.name)

    def test_the_harness_detail_lives_in_a_reference(self):
        """The per-harness dispatch is loaded on demand, not with the skill."""
        reference = SKILLS / "start-planning" / "references" / "delegation.md"
        self.assertTrue(reference.is_file())
        text = reference.read_text(encoding="utf-8")
        for harness in ("Claude Code", "Codex", "Pi"):
            self.assertIn(harness, text)


class PlanContract(unittest.TestCase):
    """S4: the Markdown plan format other skills parse is enforced on the plans in this repo."""

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
            covered = self._covered(text)
            for scenario in scenarios:
                self.assertIn(scenario, covered, "%s: S%s is in no ticket" % (name, scenario))

    @staticmethod
    def _covered(text):
        """The scenario ids the tickets satisfy, ranges expanded."""
        covered = set()
        for line in text.splitlines():
            if not line.startswith("| T"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            for identifier in re.findall(r"S\d+[a-z]?", cells[2]):
                covered.add(identifier[1:])
            for first, last in re.findall(r"S(\d+)[–-]S(\d+)", cells[2]):
                covered.update(str(number) for number in range(int(first), int(last) + 1))
        return covered


if __name__ == "__main__":
    unittest.main()
