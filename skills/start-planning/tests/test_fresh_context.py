"""The Pi gatherer: isolation, bounded runtime, strict answers and clear failures."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fresh_context.py"
spec = importlib.util.spec_from_file_location("fresh_context", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

ANSWER = {
    "sources": [{"source": "docs/plans/demo.plan.md", "settles": "the scope"}],
    "decisions": [{"decision": "one plan file", "source": "the request", "status": "settled"}],
    "findings": ["the CLI parses the plan"],
    "counts": {"tickets": 3},
    "edge_cases": ["an empty plan"],
}


class GathererTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.packet = self.dir / "packet.md"
        self.packet.write_text("# Request\n\nplan the thing\n\n## Sources\n\n- the request\n",
                                encoding="utf-8")

    def runner_for(self, code=0, out="", err=""):
        """A fake pi: the seam the gatherer calls, answered in process."""
        calls = []

        def runner(argv, cwd, env, timeout):
            calls.append({"argv": argv, "cwd": cwd, "env": env, "timeout": timeout})
            return code, out, err

        runner.calls = calls
        return runner

    # ---- the happy path ------------------------------------------------------------------

    def test_valid_answer_is_returned_as_json(self):
        runner = self.runner_for(out=json.dumps(ANSWER))
        answer = app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(answer["sources"][0]["settles"], "the scope")
        self.assertEqual(answer["counts"], {"tickets": 3})

    def test_answer_wrapped_in_prose_or_fences_is_still_read(self):
        runner = self.runner_for(out="Here you go:\n```json\n%s\n```" % json.dumps(ANSWER))
        answer = app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(answer["findings"], ["the CLI parses the plan"])

    def test_printed_answer_goes_to_stdout_and_to_the_output_file(self):
        fake_pi = self.dir / "pi"
        fake_pi.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "sys.stdout.write('''%s''')\n" % json.dumps(ANSWER),
            encoding="utf-8")
        fake_pi.chmod(0o755)
        out = self.dir / "result.json"
        code = app.main(["--packet", str(self.packet), "--pi-bin", str(fake_pi), "--output", str(out)])
        self.assertEqual(code, app.OK)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["counts"], {"tickets": 3})

    # ---- isolation ----------------------------------------------------------------------

    def test_the_gatherer_session_inherits_no_parent_session(self):
        runner = self.runner_for(out=json.dumps(ANSWER))
        app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        argv = runner.calls[0]["argv"]
        self.assertIn("--no-session", argv)
        self.assertIn("--session-dir", argv)
        self.assertNotIn("--continue", argv)
        self.assertNotIn("--resume", argv)
        self.assertIn("--no-extensions", argv)
        self.assertIn("--no-mcp", argv)

    def test_the_gatherer_gets_read_only_tools_by_default(self):
        runner = self.runner_for(out=json.dumps(ANSWER))
        app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        argv = runner.calls[0]["argv"]
        tools = argv[argv.index("--tools") + 1]
        self.assertNotIn("bash", tools)
        self.assertNotIn("write", tools)
        self.assertNotIn("edit", tools)
        self.assertIn("read", tools)

    def test_bash_is_opt_in(self):
        runner = self.runner_for(out=json.dumps(ANSWER))
        app.gather(str(self.packet), pi_bin=sys.executable, allow_bash=True, runner=runner)
        argv = runner.calls[0]["argv"]
        self.assertIn("bash", argv[argv.index("--tools") + 1])

    def test_the_packet_travels_to_the_subprocess_and_the_environment_is_scrubbed(self):
        runner = self.runner_for(out=json.dumps(ANSWER))
        os.environ["SOME_OTHER_SECRET"] = "hunter2hunter2"
        self.addCleanup(os.environ.pop, "SOME_OTHER_SECRET", None)
        app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        argv = runner.calls[0]["argv"]
        prompt = argv[-1]
        self.assertIn("plan the thing", prompt)
        self.assertIn("## Return format", prompt)
        self.assertNotIn("hunter2hunter2", prompt)
        self.assertNotIn("SOME_OTHER_SECRET", runner.calls[0]["env"])

    def test_a_packet_with_a_credential_is_refused(self):
        self.packet.write_text("# Request\n\nuse the key sk-abcdefghijklmnopqrst\n", encoding="utf-8")
        runner = self.runner_for(out=json.dumps(ANSWER))
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.REFUSED)
        self.assertEqual(runner.calls, [], "a refused packet never reaches the subprocess")

    # ---- failures -----------------------------------------------------------------------

    def test_a_missing_pi_fails_with_the_reason(self):
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin="pi-that-is-not-installed", runner=self.runner_for())
        self.assertEqual(caught.exception.code, app.NO_PI)
        self.assertIn("pi not found", caught.exception.reason)

    def test_a_failed_subprocess_fails_with_the_reason(self):
        runner = self.runner_for(code=3, err="model unavailable")
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.PI_FAILED)
        self.assertIn("model unavailable", caught.exception.reason)

    def test_a_timeout_fails_with_the_reason(self):
        def runner(argv, cwd, env, timeout):
            raise subprocess.TimeoutExpired(argv, timeout)

        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.TIMEOUT)
        self.assertIn("timed out", caught.exception.reason)

    def test_a_missing_packet_fails_before_any_subprocess(self):
        runner = self.runner_for()
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.dir / "nope.md"), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.USAGE)
        self.assertEqual(runner.calls, [])

    def test_an_answer_without_json_is_malformed(self):
        runner = self.runner_for(out="I could not gather anything.")
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.MALFORMED)

    def test_an_answer_with_the_wrong_shape_is_malformed(self):
        broken = dict(ANSWER)
        broken["sources"] = []
        runner = self.runner_for(out=json.dumps(broken))
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.MALFORMED)
        self.assertIn("sources is empty", caught.exception.reason)

    def test_an_answer_with_unknown_keys_is_malformed(self):
        broken = dict(ANSWER)
        broken["notes"] = "extra"
        runner = self.runner_for(out=json.dumps(broken))
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.MALFORMED)
        self.assertIn("unknown keys", caught.exception.reason)

    def test_a_count_written_in_digits_is_the_same_count(self):
        """A count in digits is not a malformed answer: it is the same fact."""
        answer = dict(ANSWER)
        answer["counts"] = {"tickets": "3"}
        runner = self.runner_for(out=json.dumps(answer))
        gathered = app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(gathered["counts"], {"tickets": 3})

    def test_a_count_that_is_not_a_number_is_malformed(self):
        answer = dict(ANSWER)
        answer["counts"] = {"tickets": "three"}
        runner = self.runner_for(out=json.dumps(answer))
        with self.assertRaises(app.GatherError) as caught:
            app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(caught.exception.code, app.MALFORMED)

    def test_extra_annotations_inside_a_source_are_tolerated(self):
        """A source may carry extra notes; the result shape is what the plan reads."""
        answer = json.loads(json.dumps(ANSWER))
        answer["sources"][0]["settles_note"] = "a note"
        runner = self.runner_for(out=json.dumps(answer))
        gathered = app.gather(str(self.packet), pi_bin=sys.executable, runner=runner)
        self.assertEqual(gathered["sources"][0]["source"], "docs/plans/demo.plan.md")

    def test_the_command_line_reports_the_failure_and_exits_non_zero(self):
        with self.assertRaises(app.GatherError):
            app.gather(str(self.packet), pi_bin="pi-that-is-not-installed", runner=self.runner_for())
        code = app.main(["--packet", str(self.packet), "--pi-bin", "pi-that-is-not-installed"])
        self.assertNotEqual(code, app.OK)


if __name__ == "__main__":
    unittest.main()
