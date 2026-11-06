"""CI, merge and cleanup: wait-checks, the merge poll, COMPLETE and dependents, worker stop and worktree removal."""

import json
import os
import sys
import unittest
from unittest import mock

from fixtures import load_script, plan_text, recorded_idles
from test_gates import GateFixture, MAJOR

PR = "https://github.com/o/r/pull/7"


class MergeTests(GateFixture, unittest.TestCase):
    def commit(self, push=True):
        """Wait-step commands: commit the worker's test in its checkout, optionally push the branch."""
        wt = str(self.worktree)
        git = ["git", "-C", wt, "-c", "user.name=T", "-c", "user.email=t@example.invalid"]
        steps = [git + ["add", "."], git + ["commit", "-q", "-m", "work"]]
        return steps + ([["git", "-C", wt, "push", "-q", "origin", "HEAD:feat/demo-t1"]] if push else [])

    def worker_committed(self, push=True):
        step = self.worker_done(tests=True)
        step["run"] = self.commit(push)
        return step

    def test_S8_a_passing_review_runs_wait_checks_on_the_reports_pr(self):
        """code-driven-orchestrator/S8"""
        self.waits([self.worker_done(tests=True), self.reviewer_done()])
        self.run_driver()
        self.assertEqual(self.wait_checks_log(), ["o/r#7"])
        self.assertEqual(self.calls("resume"), [])

    def test_S8_a_failing_check_sends_the_failed_log_to_the_worker_as_a_fix_round(self):
        """code-driven-orchestrator/S8"""
        self.checks([[1, "FAIL o/r#7\nunit tests: boom at line 3"], [0, "PASS o/r#7"]])
        self.waits([self.worker_done(tests=True), self.reviewer_done(), self.worker_done("t1r1")])
        self.run_driver()
        findings = json.loads((self.run_dir / "t1r1" / "findings.json").read_text(encoding="utf-8"))
        self.assertEqual((findings["source"], findings["attempt"]), ("ci", 1))
        self.assertEqual([(i["check"], i["excerpt"]) for i in findings["items"]], [("ci", "unit tests: boom at line 3")])
        self.assertIn("boom at line 3", (self.run_dir / "t1r1" / "task.md").read_text(encoding="utf-8"))
        self.assertEqual([r["args"]["name"] for r in self.calls("resume")], ["demo-t1"])
        self.assertEqual(self.wait_checks_log(), ["o/r#7", "o/r#7"])
        self.assertEqual(self.task("t1")["report"]["review_rounds"], 1)
        # the fix round opened no PR of its own; the gate finds the unit's earlier one, and converge alone gates it
        self.assertEqual(self.task("t1r1")["status"], "COMPLETE")

    def test_S9_the_ticket_reads_awaiting_merge_until_gh_reports_it_merged(self):
        """code-driven-orchestrator/S9"""
        self.prs(["OPEN", "OPEN", "MERGED"])
        self.waits([self.worker_done(tests=True), self.reviewer_done()])
        self.run_driver()
        calls = self.gh_log()
        self.assertEqual(calls[0]["argv"], ["pr", "view", PR, "--json", "state,mergeCommit"])
        self.assertGreaterEqual(len(calls), 3)
        for call in calls[:2]:
            self.assertIn("| IN PROGRESS · awaiting merge (%s) |" % PR, call["plan"])
        text = self.plan.read_text(encoding="utf-8")
        self.assertIn("| COMPLETE 2026-", text)
        self.assertIn("merged " + PR, text)
        self.assertEqual(self.task()["status"], "COMPLETE")
        self.assertEqual(self.wait_checks_log(), ["o/r#7"])

    def test_S9_an_unmerged_pr_backs_off_instead_of_spinning_on_gh(self):
        """code-driven-orchestrator/S9"""
        self.prs(["OPEN"] * 6 + ["MERGED"])
        self.waits([self.worker_done(tests=True), self.reviewer_done()])
        spec = load_script()
        env = dict(os.environ, PATH=str(self.home) + os.pathsep + os.environ["PATH"],
                   FAKE_RUNTIME_HOME=str(self.home), FAKE_PLAN=str(self.plan), FAKE_CHECKOUT=str(self.worktree))
        argv = ["orchestrate", "run", str(self.plan), "--state-dir", str(self.state_dir),
                "--models-file", str(self.models), "--wait-seconds", "1", "--idle-interval", "30"]
        with mock.patch.dict(os.environ, env), mock.patch.object(sys, "argv", argv), \
                recorded_idles(spec) as idles:
            spec.main()
        polls = len([c for c in self.gh_log() if c["argv"][:2] == ["pr", "view"]])
        self.assertEqual(polls, 7)
        # the fake wait returns at once, so every no-progress poll must be followed by the idle sleep
        self.assertGreaterEqual(len(idles), 5)
        self.assertEqual(set(idles), {30})
        self.assertEqual(self.task()["status"], "COMPLETE")

    def test_S9_a_merged_ticket_makes_its_dependents_dispatchable(self):
        """code-driven-orchestrator/S9"""
        self.plan.write_text(plan_text(rows=("T1", "T2")), encoding="utf-8")
        self.prs(["OPEN", "MERGED"])
        self.waits([self.worker_done(tests=True), self.reviewer_done()])
        self.run_driver()
        self.assertEqual(self.spawned(), ["demo-t1", "demo-t1-review", "demo-t2"])
        self.assertIn("| IN PROGRESS |", self.plan.read_text(encoding="utf-8"))

    def test_S10_a_clean_pushed_checkout_is_stopped_and_removed_but_the_branch_stays(self):
        """code-driven-orchestrator/S10"""
        self.waits([self.worker_committed(), self.reviewer_done()])
        self.run_driver()
        self.assertEqual([c["args"] for c in self.calls("stop")], [{"name": "demo-t1"}])
        self.assertFalse(self.worktree.exists())
        self.assertIn("feat/demo-t1", self.git(self.repo, "branch", "--list", "feat/demo-t1"))
        self.assertNotIn("demo-t1", self.git(self.repo, "worktree", "list"))
        self.assertEqual(self.task()["gate"], "done")

    def test_S10_a_dirty_checkout_is_left_in_place_with_the_reason_recorded(self):
        """code-driven-orchestrator/S10"""
        self.waits([self.worker_done(tests=True), self.reviewer_done()])
        self.run_driver()
        self.assertEqual(self.calls("stop"), [])
        self.assertTrue(self.worktree.exists())
        self.assertIn("uncommitted", self.task()["cleanup"])

    def test_S10_unpushed_commits_are_left_in_place_with_the_reason_recorded(self):
        """code-driven-orchestrator/S10"""
        self.waits([self.worker_committed(push=False), self.reviewer_done()])
        self.run_driver()
        self.assertEqual(self.calls("stop"), [])
        self.assertTrue(self.worktree.exists())
        self.assertIn("neither pushed nor merged", self.task()["cleanup"])

    def test_D2_review_rounds_comes_from_the_drivers_gate_history_not_the_worker(self):
        """code-driven-orchestrator/S6"""
        self.waits([self.worker_done(tests=True, report=self.report("t1", review_rounds=5)), self.reviewer_done()])
        self.run_driver()
        self.assertEqual(self.task()["report"]["review_rounds"], 0)

    def test_D5_a_review_of_another_commit_is_a_contract_error(self):
        """code-driven-orchestrator/S6a"""
        self.waits([self.worker_done(tests=True), self.reviewer_done(self.review(commit="deadbee")), self.skipped()])
        self.run_driver()
        self.assertEqual(self.request()["event"], "review")
        self.assertIn("deadbee", self.request()["reason"])
        self.assertEqual(self.wait_checks_log(), [])

    def test_a_blocking_review_never_reaches_wait_checks(self):
        """code-driven-orchestrator/S8"""
        review = self.review(verdict="block", major=[MAJOR])
        self.waits([self.worker_done(tests=True), self.reviewer_done(review)])
        self.run_driver()
        self.assertEqual(self.wait_checks_log(), [])


if __name__ == "__main__":
    unittest.main()
