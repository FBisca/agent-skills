"""`launch` validates the plan and starts the driver in a named Herdr terminal through a fake `hc`."""

import json
import os
import subprocess
import sys
import unittest

from fixtures import RunFixture, SCRIPT, plan_text

FAKE_HC = """#!/usr/bin/env python3
import json, os, sys
home = os.environ["FAKE_HC_HOME"]
with open(os.path.join(home, "hc.log"), "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1] == "ls":
    print(open(os.path.join(home, "live.json")).read())
elif sys.argv[1] == "run":
    print(json.dumps({"name": sys.argv[sys.argv.index("--name") + 1], "id": "t9"}))
"""


class LaunchTests(RunFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        hc = self.home / "hc"
        hc.write_text(FAKE_HC, encoding="utf-8")
        hc.chmod(0o755)
        self.live([])

    def live(self, names, state="live"):
        rows = [{"address": "t1", "agent": "claude-code", "cwd": "/x", "parent": "t0", "state": "live", "status": "working",
                 "turn": 0, "where": "w"}]  # a record without a name
        rows += [{"address": "t2", "name": n, "state": state, "status": "working"} for n in names]
        (self.home / "live.json").write_text(json.dumps({"terminals": rows, "hidden_finished": 3}), encoding="utf-8")

    def hc_calls(self):
        path = self.home / "hc.log"
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def launch(self, plan=None, expect=0):
        env = dict(os.environ, PATH=str(self.home) + os.pathsep + os.environ["PATH"], FAKE_HC_HOME=str(self.home))
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "launch", str(plan or self.plan)],
                                capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def test_S17_starts_run_in_a_named_pane(self):
        """code-driven-orchestrator/S17"""
        result = self.launch()
        self.assertEqual(json.loads(result.stdout)["pane"], "orchestrate-demo")
        starts = [c for c in self.hc_calls() if c[0] == "run"]
        self.assertEqual(len(starts), 1)
        argv = starts[0]
        self.assertEqual(argv[:2], ["run", "--bg"])
        self.assertEqual(argv[argv.index("--name") + 1], "orchestrate-demo")
        self.assertEqual(argv[argv.index("--cwd") + 1], str(self.repo))
        tail = argv[argv.index("--") + 1:]
        self.assertEqual([tail[0], tail[2], tail[3]], ["python3", "run", str(self.plan)])
        self.assertTrue(tail[1].endswith("orchestrate.py"))

    def test_S17_invalid_plan_exits_2_and_starts_nothing(self):
        """code-driven-orchestrator/S17"""
        self.plan.write_text(plan_text(status="DRAFT"), encoding="utf-8")
        result = self.launch(expect=2)
        self.assertIn("not APPROVED", result.stderr)
        self.assertEqual([c for c in self.hc_calls() if c[0] == "run"], [])

    def test_S17_live_driver_is_not_started_twice(self):
        """code-driven-orchestrator/S17"""
        self.live(["orchestrate-demo"])
        result = self.launch()
        out = json.loads(result.stdout)
        self.assertEqual((out["pane"], out["started"]), ("orchestrate-demo", False))
        self.assertEqual([c for c in self.hc_calls() if c[0] == "run"], [])

    def test_S17_exited_terminal_of_the_same_name_does_not_block(self):
        """code-driven-orchestrator/S17"""
        self.live(["orchestrate-demo"], state="exited")
        out = json.loads(self.launch().stdout)
        self.assertTrue(out["started"])
        self.assertEqual(len([c for c in self.hc_calls() if c[0] == "run"]), 1)


if __name__ == "__main__":
    unittest.main()
