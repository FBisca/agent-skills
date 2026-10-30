"""Behavior checks in temporary repositories; no agents or Herdr servers start."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "orchestrate.py"
spec = importlib.util.spec_from_file_location("orchestrate", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        for args in (["init", "-q"], ["-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                                     "commit", "-q", "--allow-empty", "-m", "fixture"]):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)
        self.state = self.root / "state.json"
        self.packet = {"task_id": "validation", "worker": "api", "plan": "plan.md",
                       "objective": "Validate input", "checkout": str(self.repo), "backend": "codex",
                       "owns": ["src/validation"], "acceptance": ["Invalid input is rejected"],
                       "checks": ["unit-check"], "depends_on": []}
        self.data = {"version": 1, "tasks": {}}

    def save(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def report(self, status="COMPLETE"):
        return {"task_id": "validation", "status": status, "summary": "Implemented validation",
                "files": ["src/validation/input.py"], "acceptance_met": True,
                "decisions": ["Keep error format"], "interfaces": [], "remaining": [],
                "checks": [{"command": "unit-check", "outcome": "passed"}]}

    def test_round_trip_reuse_and_dependency(self):
        packet_path = self.save("packet.json", self.packet)
        first = self.cli("claim", "--state", str(self.state), "--packet", packet_path)
        self.assertEqual(first["action"], "reserved")
        again = self.cli("claim", "--state", str(self.state), "--packet", packet_path)
        self.assertEqual(again["action"], "existing")
        self.cli("bind", "--state", str(self.state), "--task", "validation", "--runtime-id", "codex:parent:child")
        self.cli("checkpoint", "--state", str(self.state), "--task", "validation",
                 "--report", self.save("report.json", self.report()))
        followup = dict(self.packet, task_id="validation-followup", depends_on=["validation"])
        result = self.cli("claim", "--state", str(self.state), "--packet", self.save("next.json", followup))
        self.assertEqual(result["action"], "reserved")
        result = self.cli("bind", "--state", str(self.state), "--task", "validation-followup",
                          "--runtime-id", "codex:parent:child")
        self.assertEqual(result["runtime_id"], "codex:parent:child")
        stored = self.cli("show", "--state", str(self.state), "--task", "validation")
        self.assertEqual(stored["report"]["decisions"], ["Keep error format"])

    def test_conflicts_and_invalid_dependencies(self):
        app.claim(self.data, self.packet)
        for candidate in (dict(self.packet, task_id="other"),
                          dict(self.packet, task_id="other", worker="other", owns=["src"]),
                          dict(self.packet, task_id="other", worker="other", owns=["tests"], depends_on=["validation"])):
            with self.assertRaises(ValueError):
                app.claim(self.data, candidate)
        result = app.claim(self.data, dict(self.packet, task_id="other", worker="other", owns=["tests"]))
        self.assertEqual(result["action"], "reserved")

    def test_symlink_and_path_escape(self):
        (self.repo / "escape").symlink_to(self.root, target_is_directory=True)
        for owns in (["../outside"], ["escape/file"], [str(self.root)], ["src/**"]):
            with self.assertRaises(ValueError):
                app.claim(self.data, dict(self.packet, owns=owns))

    def test_independent_checkouts_can_own_same_relative_path(self):
        app.claim(self.data, self.packet)
        other = self.root / "other"
        subprocess.run(["git", "-C", str(self.repo), "worktree", "add", "--detach", str(other)],
                       check=True, capture_output=True)
        result = app.claim(self.data, dict(self.packet, task_id="other", worker="other", checkout=str(other)))
        self.assertEqual(result["action"], "reserved")

    def test_completion_requires_evidence(self):
        app.claim(self.data, self.packet)
        with self.assertRaises(ValueError):
            app.checkpoint(self.data, "validation", self.report())
        app.bind(self.data, "validation", "child")
        invalid = [dict(self.report(), checks=[]), dict(self.report(), acceptance_met=False),
                   dict(self.report(), remaining=["finish tests"]),
                   dict(self.report(), checks=[{"command": "unit-check", "outcome": "failed", "reason": "broken"}])]
        for report in invalid:
            with self.assertRaises(ValueError):
                app.checkpoint(self.data, "validation", report)
        self.assertEqual(self.data["tasks"]["validation"]["status"], "ACTIVE")

    def test_blocked_retains_ownership_and_release_requires_stopped(self):
        app.claim(self.data, self.packet)
        app.bind(self.data, "validation", "child")
        report = dict(self.report("BLOCKED"), blocker="Need interface decision", remaining=["Ask peer"])
        app.checkpoint(self.data, "validation", report)
        with self.assertRaises(ValueError):
            app.claim(self.data, dict(self.packet, task_id="replacement", worker="new"))
        self.state.write_text(json.dumps(self.data), encoding="utf-8")
        self.cli("release", "--state", str(self.state), "--task", "validation", "--reason", "replace", ok=False)
        self.cli("release", "--state", str(self.state), "--task", "validation", "--reason", "confirmed stopped", "--stopped")
        self.cli("claim", "--state", str(self.state), "--packet",
                 self.save("replace.json", dict(self.packet, task_id="replacement", worker="new")))

    def test_runtime_id_cannot_own_two_active_tasks(self):
        app.claim(self.data, self.packet)
        app.bind(self.data, "validation", "same-child")
        app.claim(self.data, dict(self.packet, task_id="other", worker="other", owns=["tests"]))
        with self.assertRaises(ValueError):
            app.bind(self.data, "other", "same-child")

    def test_failed_update_preserves_ledger(self):
        with app.ledger(self.state) as data:
            app.claim(data, self.packet)
        before = self.state.read_bytes()
        with self.assertRaises(RuntimeError):
            with app.ledger(self.state) as data:
                data["tasks"].clear()
                raise RuntimeError("interrupted update")
        self.assertEqual(self.state.read_bytes(), before)

    def test_concurrent_claims_have_one_owner(self):
        packets = [self.packet, dict(self.packet, task_id="other", worker="other")]
        processes = [subprocess.Popen([sys.executable, "-B", str(SCRIPT), "claim", "--state", str(self.state),
                                      "--packet", self.save(f"claim-{i}.json", packet)],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for i, packet in enumerate(packets)]
        for process in processes:
            process.communicate(timeout=20)
        self.assertEqual(sorted(p.returncode for p in processes), [0, 1])
        self.assertEqual(len(json.loads(self.state.read_text())["tasks"]), 1)


class ContextAndTransportTests(unittest.TestCase):
    def sample(self):
        return {"kind": "current_context", "model": "child-model", "context_tokens": 70,
                "effective_window": 100, "observed_at": app.now(), "source": "child event"}

    def test_context_reserve_boundary_and_unknown(self):
        self.assertEqual(app.context_verdict(self.sample(), 20)["status"], "room_available")
        self.assertEqual(app.context_verdict(self.sample(), 30)["status"], "checkpoint")
        stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        for sample in ({}, dict(self.sample(), kind="cumulative_usage"),
                       dict(self.sample(), observed_at=stale), dict(self.sample(), context_tokens=101),
                       dict(self.sample(), effective_window=None), dict(self.sample(), source="")):
            self.assertEqual(app.context_verdict(sample, 20)["status"], "unknown")

    def test_metrics_preserve_unknowns_and_reject_duplicate_usage(self):
        sample = {"kind": "request", "id": "1", "source": "trace", "backend": "codex", "model": "terra",
                  "strategy": "reuse", "actor": "worker", "input_tokens": 100, "output_tokens": 10}
        result = app.metrics([sample, dict(sample, id="2", input_tokens=200, cost_usd=0.2)])
        group = result["groups"][0]
        self.assertEqual(group["totals"]["input_tokens"], 300)
        self.assertIsNone(group["totals"]["cached_input_tokens"])
        self.assertEqual(group["observations"]["cost_usd"], 1)
        with self.assertRaises(ValueError):
            app.metrics([sample, deepcopy(sample)])
        with self.assertRaises(ValueError):
            app.metrics([dict(sample, kind="cumulative")])

    def test_inspect_includes_resolver_and_herdr_subcommand_is_gone(self):
        """agent-runtime/R23"""
        def cli(*argv):
            return subprocess.run([sys.executable, "-B", str(SCRIPT), *argv],
                                  capture_output=True, text=True,
                                  env={"PATH": os.environ["PATH"]})
        result = cli("inspect", "--checkout", str(SCRIPT.parents[5]))
        self.assertEqual(result.returncode, 0, result.stderr)
        info = json.loads(result.stdout)
        self.assertEqual(info["agent_runtime"]["runtime"], "native")
        self.assertNotIn("herdr", info["executables"])
        self.assertNotEqual(cli("herdr", "--session", "x").returncode, 0)
        self.assertFalse(hasattr(app, "herdr_snapshot"))

    def test_inspect_survives_resolver_failure(self):
        """agent-runtime/R23"""
        with patch.object(app, "run", side_effect=ValueError("boom")):
            self.assertEqual(app.resolve_runtime(), {"runtime": "unknown"})

    def test_bodies_name_no_runtime_outside_agent_runtime_pointer(self):
        """agent-runtime/R22"""
        agents = Path(__file__).resolve().parents[4]
        files = [Path(__file__).resolve().parents[1] / "SKILL.md",
                 agents / ".claude" / "agents" / "implementer.md",
                 agents / ".codex" / "agents" / "implementer.toml"]
        for path in files:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".md":
                parts = text.split("---", 2)
                text = parts[2] if len(parts) == 3 else text
            for line in text.splitlines():
                if "agent-runtime" in line:
                    continue
                self.assertIsNone(re.search(r"\b(hc|herdmates|herdr)\b", line, re.I),
                                  "%s: %s" % (path.name, line))


if __name__ == "__main__":
    unittest.main()
