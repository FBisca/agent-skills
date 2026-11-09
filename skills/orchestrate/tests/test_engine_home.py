"""Where the engine lives: the skill's tree carries no copy of it.

The engine — the plan parser, the dispatcher, the gates, the ledger — is the `agent-orchestrator`
member of `agent-runtime`, and its suite lives there too. These checks are the drift guard: a copy of
the engine that reappears under `skills/`, or a suite that reaches for the engine's internals, would
let the two drift apart again without anything failing.
"""

import ast
from pathlib import Path
import unittest

import pytest


ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"

# The modules the engine is made of. A file that imports one of them is reaching for the engine.
ENGINE_MODULES = ("contracts", "evidence", "events", "routes", "wait_checks")

SKIPPED = {".git", ".venv", "__pycache__", "node_modules", ".ruff_cache", ".pytest_cache"}


def sources(folder):
    """Every Python file under a folder, except the ones a tool generated."""
    for path in sorted(folder.rglob("*.py")):
        if not any(part in SKIPPED for part in path.parts):
            yield path


class EngineHomeTests(unittest.TestCase):
    """S1: the skill's tree carries no copy of the engine."""

    @pytest.mark.unit
    def test_S1_the_skill_tree_carries_no_copy_of_the_engine(self):
        """S1: no file under `skills/` parses a plan and checks one: that is the engine."""
        copies = []
        for path in sources(SKILLS):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
            if "parse_plan" in names and "check_plan" in names:
                copies.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(copies, [])

    @pytest.mark.unit
    def test_S3_the_engine_internals_are_tested_where_the_engine_lives(self):
        """S3: this repository's suite holds the skill's behaviour, not the engine's internals."""
        reaching = []
        for path in sources(SKILLS):
            if "tests" not in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for name in names:
                    if name in ENGINE_MODULES:
                        reaching.append("%s: %s" % (path.relative_to(ROOT).as_posix(), name))
        self.assertEqual(reaching, [])

        # The skill's own suite stays: the frontmatter, the portability and the repository contracts.
        for name in ("test_skill_frontmatter.py", "test_portability.py", "test_repo.py"):
            self.assertTrue((ROOT / "tests" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
