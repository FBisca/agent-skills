import pytest
import unittest
from pathlib import Path


pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parent.parent


def read(rel):
    return (ROOT / rel).read_text()


class ColdReadContract(unittest.TestCase):
    def test_S15c_manual_only_invocation(self):
        self.assertRegex(read("SKILL.md"), r"(?m)^disable-model-invocation: true$")
        self.assertRegex(read("agents/openai.yaml"), r"(?m)^\s+allow_implicit_invocation: false$")


if __name__ == "__main__":
    unittest.main()
