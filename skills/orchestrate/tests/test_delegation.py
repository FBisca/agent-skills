"""The seam between the skill and the engine: the delegation, its order and its way out.

The engine is the `agent-orchestrator` member of `agent-runtime`. The skill's script hands the command
to it; these tests drive that hand-off with a fake member, so nothing here starts an agent, a run or a
network call.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "orchestrate.py"
ROOT = Path(__file__).resolve().parents[3]

FAKE_MEMBER = """#!{python}
import json, os, sys
home = os.environ["FAKE_MEMBER_HOME"]
with open(os.path.join(home, "calls.jsonl"), "a") as log:
    log.write(json.dumps({{"argv": sys.argv[1:], "cwd": os.getcwd()}}) + "\\n")
print(json.dumps({{"member": "{name}", "argv": sys.argv[1:]}}))
sys.exit(int(os.environ.get("FAKE_MEMBER_EXIT", "0")))
"""


def fake_member(path, home, name="member"):
    """A member that records what it was asked and answers like the real one does.

    The name is baked into the fake, so two fakes answer differently and the test can tell which one
    ran.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(FAKE_MEMBER.format(python=sys.executable, name=name), encoding="utf-8")
    path.chmod(0o755)
    return {"FAKE_MEMBER_HOME": str(home)}


class DelegationTests(unittest.TestCase):
    """S4: the member answers with the same commands, exit codes and ledger."""

    def checkout(self, root, name="member"):
        """A checkout of agent-runtime whose synced member is a fake."""
        home = Path(root) / "home"
        home.mkdir(exist_ok=True)
        env = fake_member(home / ".venv" / "bin" / "agent-orchestrator", home, name)
        return home, env

    def run_skill(self, env, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                              capture_output=True, text=True, env=env, timeout=60)

    @pytest.mark.integration
    def test_S4_the_member_answers_with_the_same_commands_and_exit_codes(self):
        """S4: the command and the exit code are the member's, not the skill's."""
        with tempfile.TemporaryDirectory() as tmp:
            home, env = self.checkout(tmp)
            env = dict(env, AGENT_RUNTIME_HOME=str(home), PATH=str(Path(tmp) / "empty"))
            result = self.run_skill(env, "inspect", "--checkout", ".")
            self.assertEqual(result.returncode, 0, result.stderr)
            answer = json.loads(result.stdout)
            self.assertEqual(answer["member"], "member")
            self.assertEqual(answer["argv"], ["inspect", "--checkout", "."])

            calls = [json.loads(line) for line in
                     (home / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["argv"], ["inspect", "--checkout", "."])
            self.assertEqual(calls[0]["cwd"], os.getcwd())  # the member keeps the caller's directory

            failed = self.run_skill(dict(env, FAKE_MEMBER_EXIT="3"), "run", "plan.md")
            self.assertEqual(failed.returncode, 3, failed.stderr)

    @pytest.mark.integration
    def test_S4_the_named_checkout_wins_over_a_member_on_the_path(self):
        """S4: the checkout the user named is not shadowed by an older install on PATH."""
        with tempfile.TemporaryDirectory() as tmp:
            home, env = self.checkout(tmp, name="checkout")
            on_path = Path(tmp) / "bin"
            env = fake_member(on_path / "agent-orchestrator", home, name="path")
            env = dict(env, AGENT_RUNTIME_HOME=str(home), PATH=str(on_path))
            result = self.run_skill(env, "inspect")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["member"], "checkout")

    @pytest.mark.integration
    def test_S2_without_a_member_the_skill_refuses_and_names_the_way_out(self):
        """S2: no member means a refusal that names the way out, never a second engine."""
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "bin"
            empty.mkdir()
            result = self.run_skill({"PATH": str(empty), "HOME": tmp}, "launch", "plan.md")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("AGENT_RUNTIME_HOME", result.stderr)
            self.assertIn("uv sync --frozen --all-packages", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    @pytest.mark.integration
    def test_S2_a_checkout_without_a_member_is_named_in_the_refusal(self):
        """S2: a checkout that names no member is named, so the way out is concrete."""
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "bin"
            empty.mkdir()
            home = Path(tmp) / "checkout"
            home.mkdir()
            env = {"PATH": str(empty), "HOME": tmp, "AGENT_RUNTIME_HOME": str(home)}
            result = self.run_skill(env, "launch", "plan.md")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("AGENT_RUNTIME_HOME=%s" % home, result.stderr)


class DocumentedSeamTests(unittest.TestCase):
    """S5: the documents name the seam, the order and the way out."""

    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    @pytest.mark.unit
    def test_S5_the_documents_name_the_seam_the_order_and_the_way_out(self):
        """S5: the skill, the references and the README name the seam and the way out."""
        skill = self.read("skills/orchestrate/SKILL.md")
        self.assertIn("agent-orchestrator", skill)
        self.assertIn("AGENT_RUNTIME_HOME", skill)
        self.assertIn("uv sync --frozen --all-packages", skill)

        readme = self.read("README.md")
        self.assertIn("AGENT_RUNTIME_HOME", readme)
        self.assertIn("Checkout of [agent-runtime]", readme)

        for reference in ("state.md", "routing.md"):
            text = self.read("skills/orchestrate/references/%s" % reference)
            self.assertNotIn("scripts/contracts.py", text, reference)
            self.assertNotIn("scripts/routes.py", text, reference)


if __name__ == "__main__":
    unittest.main()
