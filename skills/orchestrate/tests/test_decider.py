"""The decider, the pause with attention.md, person-owned tickets, and a loop that never spins on a paused unit."""

import json
import os
import sys
import unittest
from unittest import mock

from fixtures import ROWS, RunFixture, assignment, load_script, plan_text, report_wait, resume_id, spawn_id, wait_result


class DeciderFixture(RunFixture):
    def setUp(self):
        super().setUp()
        self.plan.write_text(plan_text(rows=("T1",)), encoding="utf-8")
        self.run_dir = self.state_dir / "demo"
        self.worktree = self.root / "repo.worktrees" / "demo-t1"

    def report(self, task_id, **over):
        return json.dumps(dict({"contract": 1, "task_id": task_id, "status": "COMPLETE", "summary": "done",
                                "acceptance_met": True, "files": [], "decisions": [], "interfaces": [],
                                "remaining": [], "checks": [], "review_rounds": 0, "usage": "unknown",
                                "head": "abc1234", "pr": None}, **over))

    def failing_report(self, task_id):
        """The worker says complete with no test: converge fails on the scenario coverage."""
        fix_round = int(task_id.split("r")[1]) if "r" in task_id else 0
        step = report_wait("demo-t1", "complete", id=resume_id("demo-t1", fix_round) if fix_round else spawn_id("demo-t1"))
        step["write"] = [[str(self.run_dir / task_id / "report.json"), self.report(task_id)]]
        return step

    def blocked(self, kind="blocked", text="cannot reach the database", id=None):
        return report_wait("demo-t1", kind, text, id=id)

    def decided(self, action=None, raw=None, unit="t1", name="demo-t1-decide", **over):
        body = raw if raw is not None else json.dumps(dict({"contract": 1, "action": action, "reason": "because"}, **over))
        step = report_wait(name, "complete")
        step["write"] = [] if action is None and raw is None else [[str(self.run_dir / unit / "decision.json"), body]]
        return step

    def task(self, task_id="t1"):
        return self.ledger()["tasks"][task_id]

    def spawned(self):
        return [c["args"]["name"] for c in self.calls("spawn")]

    def plan_status(self, row="T1"):
        for line in self.plan.read_text(encoding="utf-8").splitlines():
            if line.startswith("| %s |" % row):
                return line.rstrip(" |").rsplit("|", 1)[1].strip()

    def attention_md(self):
        path = self.run_dir / "attention.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""


class DeciderTests(DeciderFixture, unittest.TestCase):
    def test_S11_a_worker_reporting_blocked_gets_a_large_decider_with_a_packet(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.blocked()])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
        args = self.calls("spawn")[1]["args"]
        self.assertEqual((args["kind"], args["model"], args["effort"], args["cwd"]),
                         ("worker", "opus", "high", str(self.worktree)))
        task_md = self.run_dir / "t1-decide" / "task.md"
        self.assertEqual(args["task"], "Read %s and follow it." % task_md)
        text = task_md.read_text(encoding="utf-8")
        for needle in ("cannot reach the database", str(self.run_dir / "t1" / "task.md"), str(self.plan),
                       str(self.run_dir / "t1" / "decision.json"), "retry one class up", "fresh worker",
                       "mark blocked", "skip", "ask user", '"unit": "t1"', "scope"):
            self.assertIn(needle, text)
        self.assertEqual(self.task()["gate"], "deciding")

    def test_S11_a_decision_request_goes_to_the_decider_too(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.blocked("decision", "two ways to do it")])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
        self.assertIn("two ways to do it", (self.run_dir / "t1-decide" / "task.md").read_text(encoding="utf-8"))

    def test_S11_a_worker_whose_turn_ended_without_a_report_gets_a_decider(self):
        """code-driven-orchestrator/S11"""
        for runtime_state in ("idle", "done", "unreported", "error"):
            with self.subTest(runtime_state=runtime_state):
                self.setUp()
                self.waits([wait_result([assignment("demo-t1", "working", runtime_state)])])
                self.run_driver()
                self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
                self.assertIn("runtime state " + runtime_state, (self.run_dir / "t1-decide" / "task.md").read_text(encoding="utf-8"))
                self.assertEqual(self.task()["gate"], "deciding")

    def test_S11_a_failed_worker_gets_a_decider_once_by_state_and_message(self):
        """code-driven-orchestrator/S11"""
        self.waits([report_wait("demo-t1", "failed", "worker terminal exited before completion")])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
        self.assertIn("terminal exited", (self.run_dir / "t1-decide" / "task.md").read_text(encoding="utf-8"))

    def test_S11_a_working_assignment_without_an_ended_turn_is_not_an_event(self):
        """code-driven-orchestrator/S11"""
        self.waits([wait_result([assignment("demo-t1", "working")], reason="timeout")])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1"])
        self.assertEqual(self.task().get("gate"), None)

    def test_S11_a_superseded_assignment_reported_failed_is_not_an_event(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.failing_report("t1"), wait_result([assignment("demo-t1", "failed")])])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1"])
        self.assertEqual(self.task("t1r1")["assignment_id"], resume_id("demo-t1", 1))
        self.assertEqual(self.task("t1r1").get("gate"), None)

    def test_S11_a_third_failed_gate_gets_a_decider_with_the_ledger_slice(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.failing_report("t1"), self.failing_report("t1r1"), self.failing_report("t1r2")])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
        self.assertEqual(len(self.calls("resume")), 2)
        self.assertEqual(self.task("t1r2")["gate"], "deciding")
        text = (self.run_dir / "t1-decide" / "task.md").read_text(encoding="utf-8")
        for needle in ("failed its gates 3 times", "FAIL coverage: S1", '"failed_reviews": 3',
                       str(self.run_dir / "t1r2" / "report.json"), str(self.run_dir / "t1r2" / "findings.json")):
            self.assertIn(needle, text)

    def test_S11_retry_after_a_failed_gate_runs_one_more_fix_round(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.failing_report("t1"), self.failing_report("t1r1"), self.failing_report("t1r2"),
                    self.decided("retry", unit="t1")])
        self.run_driver()
        self.assertEqual(len(self.calls("resume")), 3)
        self.assertEqual(self.calls("resume")[2]["args"]["task"], "Read %s and follow it." % (self.run_dir / "t1r3" / "task.md"))
        findings = json.loads((self.run_dir / "t1r3" / "findings.json").read_text(encoding="utf-8"))
        self.assertEqual((findings["source"], findings["attempt"]), ("converge", 3))
        self.assertEqual((self.task("t1r3")["status"], self.task("t1r2")["status"]), ("ACTIVE", "RELEASED"))

    def test_S11_retry_resumes_a_live_worker_in_a_new_task_directory(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.blocked(), self.decided("retry", reason="the database is back")])
        self.run_driver()
        resumes = self.calls("resume")
        self.assertEqual([r["args"]["name"] for r in resumes], ["demo-t1"])
        self.assertEqual(resumes[0]["args"]["task"], "Read %s and follow it." % (self.run_dir / "t1d1" / "task.md"))
        text = (self.run_dir / "t1d1" / "task.md").read_text(encoding="utf-8")
        for needle in ("cannot reach the database", "the database is back", str(self.run_dir / "t1d1" / "report.json"),
                       str(self.run_dir / "t1" / "task.md"), "t1d1"):
            self.assertIn(needle, text)
        self.assertEqual((self.task("t1d1")["status"], self.task("t1")["status"]), ("ACTIVE", "RELEASED"))
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])

    def test_S11_retry_for_an_exited_worker_spawns_a_fresh_one(self):
        """code-driven-orchestrator/S11"""
        self.states({"demo-t1": "exited"})
        self.waits([self.blocked(), self.decided("retry")])
        self.run_driver()
        self.assertEqual(self.calls("resume"), [])
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide", "demo-t1"])

    def test_S11_fresh_worker_replaces_a_live_pane_with_the_same_class(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.blocked(), self.decided("fresh worker")])
        self.run_driver()
        self.assertEqual(self.calls("resume"), [])
        self.assertEqual([c["args"]["name"] for c in self.calls("stop")], ["demo-t1"])
        first, fresh = self.calls("spawn")[0]["args"], self.calls("spawn")[2]["args"]
        self.assertEqual((fresh["name"], fresh["model"], fresh["effort"]), ("demo-t1", first["model"], first["effort"]))
        self.assertIn(str(self.run_dir / "t1d1" / "task.md"), fresh["task"])
        self.assertEqual(self.task("t1d1")["status"], "ACTIVE")

    def test_S11_retry_one_class_up_spawns_a_fresh_worker_on_the_next_class(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.blocked(), self.decided("retry one class up")])
        self.run_driver()
        first, fresh = self.calls("spawn")[0]["args"], self.calls("spawn")[2]["args"]
        self.assertEqual((first["model"], fresh["model"]), ("haiku", "sonnet"))
        self.assertEqual(self.task("t1d1")["packet"]["class"], "medium")
        self.assertEqual(self.task("t1d1")["packet"]["model"], "sonnet")

    def test_S11_mark_blocked_and_skip_close_the_unit_in_ledger_and_plan(self):
        """code-driven-orchestrator/S11"""
        for action, status in (("mark blocked", "BLOCKED"), ("skip", "SKIPPED")):
            with self.subTest(action=action):
                self.setUp()
                self.waits([self.blocked(), self.decided(action, reason="not needed")])
                self.run_driver()
                self.assertTrue(self.plan_status().startswith(status + " · "), self.plan_status())
                self.assertIn("not needed", self.plan_status())
                self.assertEqual(self.calls("resume"), [])
                self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
                self.assertEqual(self.task()["gate"], status.lower())

    def test_S11_a_decider_gets_two_calls_per_unit_then_the_unit_pauses(self):
        """code-driven-orchestrator/S11"""
        self.waits([self.blocked(), self.decided("retry"),
                    self.blocked(text="still stuck", id=resume_id("demo-t1", 1)),
                    self.decided("retry", unit="t1d1", name="demo-t1-decide2"),
                    self.blocked(text="again", id=resume_id("demo-t1", 2))])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide", "demo-t1-decide2"])
        self.assertTrue(self.plan_status().startswith("IN PROGRESS · needs you:"), self.plan_status())

    def test_S11_decider_names_stay_within_32_characters(self):
        """code-driven-orchestrator/S11"""
        spec = load_script()
        name = spec.worker_name("a-very-long-plan-slug-that-keeps-going", 12, "-decide")
        self.assertLessEqual(len(name), 32)
        self.assertTrue(name.endswith("-t12-decide"))


class PauseTests(DeciderFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plan.write_text(plan_text(rows=("T1", "T3")), encoding="utf-8")

    def assert_paused(self, needle):
        status = self.plan_status()
        self.assertTrue(status.startswith("IN PROGRESS · needs you: "), status)
        self.assertIn(needle, status)
        self.assertIn(needle, self.attention_md())
        self.assertIn("T1", self.attention_md())
        self.assertEqual(self.task()["gate"], "attention")

    def test_S12_a_missing_decision_pauses_the_ticket_and_the_others_keep_running(self):
        """code-driven-orchestrator/S12"""
        self.waits([self.blocked(), self.decided()])
        self.run_driver()
        self.assert_paused("decision.json")
        self.assertEqual(self.plan_status("T3"), "IN PROGRESS")
        self.assertEqual(self.task("t3")["status"], "ACTIVE")
        self.assertEqual(self.calls("resume"), [])

    def test_S12_an_invalid_decision_pauses_the_ticket(self):
        """code-driven-orchestrator/S12"""
        for raw in ("{not json", json.dumps({"contract": 1, "action": "delete everything", "reason": "x"})):
            with self.subTest(raw=raw):
                self.setUp()
                self.waits([self.blocked(), self.decided(raw=raw)])
                self.run_driver()
                self.assert_paused("decision.json")
                self.assertEqual(self.calls("resume"), [])

    def test_S12_ask_user_pauses_with_the_question(self):
        """code-driven-orchestrator/S12"""
        self.waits([self.blocked(), self.decided("ask user", question="Should the API be public?")])
        self.run_driver()
        self.assert_paused("Should the API be public?")

    def test_S12_a_paused_plan_status_stays_one_table_cell(self):
        """code-driven-orchestrator/S12"""
        self.waits([self.blocked(), self.decided("ask user", question="a | b\nc " + "x" * 400)])
        self.run_driver()
        self.assertEqual(len(self.plan_status().split("|")), 1)
        self.assertLessEqual(len(self.plan_status()), 220)
        self.assertEqual(len(self.plan.read_text(encoding="utf-8").splitlines()), len(plan_text(rows=("T1", "T3")).splitlines()))

    def test_S12_a_contract_error_pauses_the_ticket_too(self):
        """code-driven-orchestrator/S12"""
        self.waits([report_wait("demo-t1", "complete")])
        self.run_driver()
        self.assert_paused("report.json")

    def test_S12_a_decider_that_reports_blocked_pauses_the_ticket(self):
        """code-driven-orchestrator/S12"""
        self.waits([self.blocked(), report_wait("demo-t1-decide", "blocked", "cannot read the ledger")])
        self.run_driver()
        self.assert_paused("cannot read the ledger")

    def test_S12_a_decider_that_cannot_be_spawned_pauses_the_ticket(self):
        """code-driven-orchestrator/S12"""
        self.refuse(["demo-t1-decide"])
        self.waits([self.blocked()])
        self.run_driver()
        self.assert_paused("decider")

    def test_S12_a_decider_whose_turn_ended_without_a_report_pauses_on_the_missing_decision(self):
        """code-driven-orchestrator/S12"""
        self.waits([self.blocked(), wait_result([assignment("demo-t1-decide", "working", "idle")])])
        self.run_driver()
        self.assert_paused("decision.json")
        self.assertEqual(self.calls("resume"), [])

    def test_S12_a_decider_that_wrote_its_file_but_never_reported_is_still_applied(self):
        """code-driven-orchestrator/S12"""
        done = wait_result([assignment("demo-t1-decide", "working", "done")],
                           write=[[str(self.run_dir / "t1" / "decision.json"),
                                   json.dumps({"contract": 1, "action": "ask user", "reason": "x", "question": "which way?"})]])
        self.waits([self.blocked(), done])
        self.run_driver()
        self.assert_paused("which way?")

    def test_S12_a_reviewer_whose_turn_ended_without_a_review_pauses_the_ticket(self):
        """code-driven-orchestrator/S12"""
        step = self.failing_report("t1")
        step["write"].append([str(self.worktree / "src" / "a" / "test_a.py"), 'def test_a():\n    """S1"""\n'])
        self.waits([step, wait_result([assignment("demo-t1-review", "working", "idle")])])
        self.run_driver()
        self.assert_paused("review.json")

    def test_S12_a_paused_ticket_neither_spins_the_loop_nor_gets_a_second_decider(self):
        """code-driven-orchestrator/S12"""
        parked = wait_result([assignment("demo-t1", "blocked")])
        again = report_wait("demo-t1", "blocked", "still blocked")
        self.plan.write_text(plan_text(rows=("T1",)), encoding="utf-8")
        self.waits([self.blocked(), self.decided("ask user", question="which way?"), parked, again, parked, parked, parked])
        self.assertEqual(parked["unfinished"], ["a-demo-t1"])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-decide"])
        self.assertEqual(len(self.calls("wait")), 3)
        self.assertEqual(self.task()["gate"], "attention")
        self.assertEqual(len(self.task()["attention"]), 1)

    def test_S12_a_parked_assignment_counts_as_no_progress_so_the_loop_backs_off(self):
        """code-driven-orchestrator/S12"""
        spec = load_script()
        busy = wait_result([assignment("demo-t1", "blocked"), assignment("demo-t3")], reason="timeout")
        self.waits([self.blocked(), self.decided("ask user", question="which way?")] + [busy] * 4
                   + [wait_result([assignment("demo-t3", "complete")])])
        env = dict(os.environ, PATH=str(self.home) + os.pathsep + os.environ["PATH"], FAKE_RUNTIME_HOME=str(self.home))
        argv = ["orchestrate", "run", str(self.plan), "--state-dir", str(self.state_dir), "--models-file", str(self.models),
                "--wait-seconds", "1", "--idle-interval", "30"]
        with mock.patch.dict(os.environ, env), mock.patch.object(sys, "argv", argv), mock.patch.object(spec.time, "sleep") as sleep:
            spec.main()
        self.assertGreaterEqual(sleep.call_count, 4)
        self.assertEqual({c.args[0] for c in sleep.call_args_list}, {30})
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t3", "demo-t1-decide"])

    def test_S12_another_units_open_assignment_still_counts_as_work(self):
        """code-driven-orchestrator/S12"""
        self.plan.write_text(plan_text(rows=("T1", "T3")), encoding="utf-8")
        parked = wait_result([assignment("demo-t1", "blocked"), assignment("demo-t3")], reason="timeout")
        self.waits([self.blocked(), self.decided("ask user", question="which way?"), parked, parked, wait_result([assignment("demo-t3", "complete")])])
        self.run_driver()
        self.assertEqual(len(self.calls("wait")), 5)


class PersonOwnedTests(DeciderFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plan.write_text(plan_text(rows=("T1", "T4")), encoding="utf-8")

    def test_S13_a_ready_person_owned_ticket_reads_needs_you_and_is_logged(self):
        """code-driven-orchestrator/S13"""
        self.run_driver()
        self.assertEqual(self.plan_status("T4"), "needs you: sign-off")
        self.assertIn("T4", self.attention_md())
        self.assertIn("sign-off", self.attention_md())
        self.assertEqual(self.spawned(), ["demo-t1"])
        self.assertEqual(self.plan_status("T1"), "IN PROGRESS")

    def test_S13_it_waits_until_the_user_sets_it_complete(self):
        """code-driven-orchestrator/S13"""
        self.run_driver()
        self.run_driver()
        self.assertEqual(self.plan_status("T4"), "needs you: sign-off")
        self.assertEqual(self.attention_md().count("sign-off"), 1)
        text = self.plan.read_text(encoding="utf-8").replace("needs you: sign-off", "COMPLETE 2026-11-07")
        self.plan.write_text(text, encoding="utf-8")
        self.run_driver()
        self.assertEqual(self.plan_status("T4"), "COMPLETE 2026-11-07")
        self.assertEqual(self.attention_md().count("sign-off"), 1)

    def test_S13_a_person_ticket_with_open_blockers_stays_to_do(self):
        """code-driven-orchestrator/S13"""
        row = ROWS["T4"].replace("| none | none |", "| none | T1 |")
        self.plan.write_text(plan_text(rows=("T1",)) + row + "\n", encoding="utf-8")
        self.run_driver()
        self.assertEqual(self.plan_status("T4"), "TO-DO")
        self.assertEqual(self.attention_md(), "")


if __name__ == "__main__":
    unittest.main()
