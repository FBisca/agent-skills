"""The agent -> driver handoff files: versioned JSON, validated in code."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import contracts  # noqa: E402


def report(**over):
    return dict({"contract": 1, "task_id": "t1", "status": "COMPLETE", "summary": "done", "acceptance_met": True,
                 "files": [], "decisions": [], "interfaces": [], "remaining": [], "checks": [],
                 "head": "abc1234", "pr": None}, **over)


MAJOR = {"id": "M1", "file": "a.py", "line": 3, "problem": "wrong", "fix": "right"}


def review(**over):
    return dict({"contract": 1, "verdict": "pass", "major": [], "deferred": [], "commit": "abc1234"}, **over)


class ContractTests(unittest.TestCase):
    def rejects(self, validate, value, needle):
        with self.assertRaises(contracts.ContractError) as caught:
            validate(value)
        self.assertIn(needle, str(caught.exception))

    def test_S6a_report_accepts_the_checkpoint_shape_with_head_and_pr(self):
        """code-driven-orchestrator/S6a"""
        self.assertEqual(contracts.validate_report(report(pr="https://example.invalid/pr/1"))["head"], "abc1234")

    def test_S6a_report_rejects_a_missing_version_head_or_bad_pr(self):
        """code-driven-orchestrator/S6a"""
        bare = report()
        del bare["contract"]
        self.rejects(contracts.validate_report, bare, "contract")
        self.rejects(contracts.validate_report, report(contract=2), "contract")
        for key in ("head", "task_id", "summary"):
            broken = report()
            del broken[key]
            self.rejects(contracts.validate_report, broken, key)
        self.rejects(contracts.validate_report, report(pr=7), "pr")
        self.rejects(contracts.validate_report, report(status="DONE"), "status")
        self.rejects(contracts.validate_report, report(files="x"), "files")
        self.rejects(contracts.validate_report, [], "object")

    def test_S6a_review_block_holds_exactly_when_major_is_not_empty(self):
        """code-driven-orchestrator/S6a"""
        contracts.validate_review(review())
        contracts.validate_review(review(verdict="block", major=[MAJOR], deferred=[{"id": "D1", "note": "n"}]))
        self.rejects(contracts.validate_review, review(verdict="block"), "block")
        self.rejects(contracts.validate_review, review(verdict="pass", major=[MAJOR]), "pass")
        self.rejects(contracts.validate_review, review(verdict="maybe"), "verdict")

    def test_S6a_review_items_need_every_field(self):
        """code-driven-orchestrator/S6a"""
        for key in MAJOR:
            item = {k: v for k, v in MAJOR.items() if k != key}
            self.rejects(contracts.validate_review, review(verdict="block", major=[item]), key)
        self.rejects(contracts.validate_review, review(deferred=[{"id": "D1"}]), "note")
        self.rejects(contracts.validate_review, review(commit=""), "commit")

    def test_S6a_findings_carry_a_source_an_attempt_and_the_blocking_items(self):
        """code-driven-orchestrator/S6a"""
        good = contracts.make_findings("converge", 1, ["FAIL coverage: S1"])
        self.assertEqual(good, {"contract": 1, "source": "converge", "attempt": 1, "items": ["FAIL coverage: S1"]})
        contracts.make_findings("review", 2, [MAJOR])
        contracts.make_findings("ci", 1, ["FAIL pr 4"])
        self.rejects(lambda v: contracts.make_findings(*v), ("lint", 1, ["x"]), "source")
        self.rejects(lambda v: contracts.make_findings(*v), ("converge", 0, ["x"]), "attempt")
        self.rejects(lambda v: contracts.make_findings(*v), ("converge", 1, []), "items")
        self.rejects(lambda v: contracts.make_findings(*v), ("review", 1, ["text"]), "items")
        self.rejects(lambda v: contracts.make_findings(*v), ("converge", 1, [MAJOR]), "items")

    def test_S6a_load_names_a_missing_unparseable_or_oversized_file(self):
        """code-driven-orchestrator/S6a"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "review.json"
            self.rejects(lambda p: contracts.load(p, contracts.validate_review), path, "review.json")
            path.write_text("{not json", encoding="utf-8")
            self.rejects(lambda p: contracts.load(p, contracts.validate_review), path, "review.json")
            path.write_text(json.dumps(review()), encoding="utf-8")
            self.assertEqual(contracts.load(path, contracts.validate_review)["verdict"], "pass")
            path.write_text(json.dumps(review(commit="x" * 70000)), encoding="utf-8")
            self.rejects(lambda p: contracts.load(p, contracts.validate_review), path, "64 KiB")


    def test_S11_a_decision_names_one_action_from_the_menu(self):
        """code-driven-orchestrator/S11"""
        for action in ("retry", "retry one class up", "fresh worker", "mark blocked", "skip", "ask user"):
            decision = {"contract": 1, "action": action, "reason": "because"}
            self.assertEqual(contracts.validate_decision(decision)["action"], action)
        ask = {"contract": 1, "action": "ask user", "reason": "scope", "question": "which API?"}
        self.assertEqual(contracts.validate_decision(ask)["question"], "which API?")
        self.rejects(contracts.validate_decision, {"contract": 1, "action": "retry now", "reason": "x"}, "action")
        self.rejects(contracts.validate_decision, {"contract": 1, "action": "skip"}, "reason")
        self.rejects(contracts.validate_decision, {"contract": 2, "action": "skip", "reason": "x"}, "contract")
        self.rejects(contracts.validate_decision, {"contract": 1, "action": "skip", "reason": "x", "question": 3}, "question")
        self.rejects(contracts.validate_decision, ["skip"], "object")


if __name__ == "__main__":
    unittest.main()
