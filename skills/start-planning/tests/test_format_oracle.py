"""yaml-eec/S30: a Python oracle is formatted as the repository's formatter formats its promoted path.

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

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "format_oracle.py"

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


class FormatOracleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "repo"
        self.bin = self.repo / ".venv" / "bin"
        self.bin.mkdir(parents=True)
        ruff = self.bin / "ruff"
        ruff.write_text(FAKE_RUFF.format(python=sys.executable), encoding="utf-8")
        ruff.chmod(0o755)
        self.oracle = self.repo / "docs" / "plans" / "demo.oracle" / "test_demo.py.oracle"
        self.oracle.parent.mkdir(parents=True)
        self.oracle.write_text("x = 'a'\n", encoding="utf-8")

    def configure(self):
        (self.repo / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")

    def run_script(self, oracle=None):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--repo", str(self.repo), str(oracle or self.oracle), "src/a/"],
            capture_output=True, text=True, timeout=60,
        )

    def calls(self):
        log = self.bin / "calls.jsonl"
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    def test_S30_the_oracle_is_formatted_under_its_promoted_path(self):
        self.configure()
        done = self.run_script()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.oracle.read_text(encoding="utf-8"), 'x = "a"\n')
        [call] = self.calls()
        self.assertEqual(call["argv"][:3], ["format", "--stdin-filename", str(self.repo.resolve() / "src/a/test_demo.py")])
        self.assertEqual(Path(call["cwd"]).resolve(), self.repo.resolve())
        self.assertIn("formatted as src/a/test_demo.py", done.stdout)

    def test_S30_a_repository_without_a_formatter_leaves_the_oracle_as_written(self):
        done = self.run_script()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.oracle.read_text(encoding="utf-8"), "x = 'a'\n")
        self.assertEqual(self.calls(), [])

    def test_S30_an_oracle_that_is_not_python_is_left_as_written(self):
        self.configure()
        other = self.oracle.with_name("check.sh.oracle")
        other.write_text("echo 'a'\n", encoding="utf-8")
        done = self.run_script(other)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(other.read_text(encoding="utf-8"), "echo 'a'\n")
        self.assertEqual(self.calls(), [])

    def test_S30_a_file_the_formatter_refuses_is_left_as_written_and_fails(self):
        self.configure()
        self.oracle.write_text("syntax error 'a'\n", encoding="utf-8")
        done = self.run_script()
        self.assertEqual(done.returncode, 1)
        self.assertIn("invalid syntax", done.stderr)
        self.assertEqual(self.oracle.read_text(encoding="utf-8"), "syntax error 'a'\n")

    def test_S30_a_configured_formatter_that_is_not_installed_names_the_way_out(self):
        self.configure()
        (self.bin / "ruff").unlink()
        done = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--repo", str(self.repo), str(self.oracle), "src/a/"],
            capture_output=True, text=True, timeout=60, env={"PATH": str(self.repo / "nowhere")},
        )
        self.assertEqual(done.returncode, 2)
        self.assertIn("uv sync", done.stderr)
        self.assertEqual(self.oracle.read_text(encoding="utf-8"), "x = 'a'\n")


if __name__ == "__main__":
    unittest.main()
