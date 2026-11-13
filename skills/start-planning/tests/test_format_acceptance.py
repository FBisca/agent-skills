"""plan-layout/S14: a Python acceptance file is formatted as the repository's ruff formats its destination.

The formatter is a fake `ruff` in the repository's `.venv`: it records how it was called and
double-quotes its input, so a test can tell what it was asked and whether its answer was kept.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pytest


pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "format_acceptance.py"
DESTINATION = "pkg/acceptance/flows/"

FAKE_RUFF = """#!{python}
import json, os, sys
text = sys.stdin.read()
with open(os.path.join(os.path.dirname(__file__), "calls.jsonl"), "a") as log:
    log.write(json.dumps({{"argv": sys.argv[1:], "cwd": os.getcwd()}}) + "\\n")
if "syntax error" in text:
    sys.stderr.write("error: invalid syntax\\n")
    sys.exit(2)
sys.stdout.write(text.replace("'", '"'))
"""


class FormatAcceptanceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "repo"
        self.bin = self.repo / ".venv" / "bin"
        self.bin.mkdir(parents=True)
        ruff = self.bin / "ruff"
        ruff.write_text(FAKE_RUFF.format(python=sys.executable), encoding="utf-8")
        ruff.chmod(0o755)
        self.file = self.repo / "docs" / "plans" / "2026-11-13-demo" / "acceptance" / "test_demo.py"
        self.file.parent.mkdir(parents=True)
        self.file.write_text("x = 'a'\n", encoding="utf-8")

    def configure(self):
        (self.repo / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")

    def run_script(self, file=None, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--repo", str(self.repo), str(file or self.file), DESTINATION],
            capture_output=True, text=True, timeout=60, env=env,
        )

    def calls(self):
        log = self.bin / "calls.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def test_S14_the_acceptance_file_is_formatted_under_its_destination(self):
        self.configure()
        done = self.run_script()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), 'x = "a"\n')
        [call] = self.calls()
        self.assertEqual(
            call["argv"][:3],
            ["format", "--stdin-filename", str(self.repo.resolve() / DESTINATION / "test_demo.py")],
        )
        self.assertEqual(Path(call["cwd"]).resolve(), self.repo.resolve())
        self.assertIn("formatted as pkg/acceptance/flows/test_demo.py", done.stdout)

    def test_S14_a_repository_without_ruff_leaves_the_file_as_written(self):
        done = self.run_script()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "x = 'a'\n")
        self.assertEqual(self.calls(), [])
        self.assertIn("configures no ruff", done.stdout)

    def test_S14_a_file_that_is_not_python_is_left_as_written(self):
        self.configure()
        other = self.file.with_name("demo.test.ts")
        other.write_text("const a = 'a'\n", encoding="utf-8")
        done = self.run_script(other)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(other.read_text(encoding="utf-8"), "const a = 'a'\n")
        self.assertEqual(self.calls(), [])

    def test_S14_a_file_ruff_refuses_is_left_as_written_and_fails(self):
        self.configure()
        self.file.write_text("syntax error 'a'\n", encoding="utf-8")
        done = self.run_script()
        self.assertEqual(done.returncode, 1)
        self.assertIn("invalid syntax", done.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "syntax error 'a'\n")

    def test_S14_a_configured_ruff_that_is_not_installed_names_the_way_out(self):
        self.configure()
        (self.bin / "ruff").unlink()
        done = self.run_script(env={"PATH": str(self.repo / "nowhere")})
        self.assertEqual(done.returncode, 2)
        self.assertIn("uv sync", done.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), "x = 'a'\n")


if __name__ == "__main__":
    unittest.main()
