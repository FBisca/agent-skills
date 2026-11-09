"""The vocabulary the idea skills document against the vocabulary the gate enforces (test-suite/R3).

The gate is the machine that decides; the two skills are the documents an agent reads. A value the
script accepts and no document names is a trap for the agent, and a value a document names and the
script rejects is a broken instruction. The two must hold the same vocabulary, in both directions.
"""

import importlib.util
from pathlib import Path
import re
import unittest

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "idea-frame" / "scripts" / "idea_check.py"
DOCS = (ROOT / "skills" / "idea-frame" / "SKILL.md", ROOT / "skills" / "idea-answer" / "SKILL.md")
PROSE_DOCS = DOCS + (ROOT / "skills" / "idea-answer" / "prep.md",)

# The group a skill names, and the constant of the script that holds the same vocabulary.
GROUPS = {
    "stages": "VALID_STAGES",
    "columns": "COLUMNS",
    "answer fields": "ANSWER_FIELDS",
    "test types": "TEST_TYPES",
    "result values": "RESULT_VALUES",
}


def load():
    spec = importlib.util.spec_from_file_location("idea_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def vocabulary(text):
    """{group: [values]} the skill documents, from the block under its vocabulary heading."""
    out = {}
    for heading in re.finditer(r"(?im)^#+\s*.*vocabulary.*$", text):
        block = re.search(r"```[a-z]*\n(.*?)```", text[heading.end():], re.S)
        if not block:
            continue
        for line in block.group(1).splitlines():
            line = line.strip()
            if not line:
                continue
            key, sep, values = line.partition(":")
            assert sep, f"a vocabulary line names no group: {line!r}"
            out[key.strip()] = [v.strip() for v in values.split("|")]
    return out


class IdeaVocabulary(unittest.TestCase):
    def test_the_skills_document_exactly_the_gate_vocabulary(self):
        """test-suite/R3: the documented vocabulary is the script's, in both directions."""
        script = load()
        documented = set()
        for path in DOCS:
            groups = vocabulary(path.read_text(encoding="utf-8"))
            self.assertTrue(groups, f"{path.parent.name} documents no vocabulary")
            for group, values in groups.items():
                self.assertIn(group, GROUPS, f"{path.parent.name}: unknown group {group!r}")
                constant = getattr(script, GROUPS[group])
                expected = list(constant)
                self.assertEqual(sorted(values), sorted(expected),
                                 f"{path.parent.name}: {group} is not the script's {GROUPS[group]}")
                documented.add(group)
        self.assertEqual(documented, set(GROUPS), "every group of the gate's vocabulary is documented")

        for path in PROSE_DOCS:
            text = path.read_text(encoding="utf-8")
            for stage in re.findall(r"stage: ([a-z0-9]+)", text):
                self.assertIn(stage, script.VALID_STAGES, f"{path.name} names the unknown stage {stage!r}")


if __name__ == "__main__":
    unittest.main()
