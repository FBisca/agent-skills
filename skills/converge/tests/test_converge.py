"""converge.py checks against throwaway git repos; scenario IDs name the tests."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "converge.py"
spec = importlib.util.spec_from_file_location("converge", SCRIPT)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

PLAN = """# Plan
Slug: `p`. Living spec: x. Status: APPROVED 2026-10-28 (test)
## Scenarios
- **S1** WHEN a THEN b.
- **S12** WHEN c THEN d.
- **S2a** WHEN e THEN f.

## Tickets
| # | What | Satisfies | Blocked by | Paths (under x/) | Owner | Status |
|---|---|---|---|---|---|---|
| T1 | one | S1, S12 | none | src/, `docs/*.txt` | agent | TO-DO |
| T2 | two | S2a | T1 | tests/test_a.py, lib/*.py | agent | TO-DO |
"""
GOOD_TEST = """def test_S1_a():
    pass

def test_S12_b():
    '''S2a: docstring carries the ID'''
"""


class ConvergeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q", "-b", "main")
        self.write("docs/plans/p.plan.md", PLAN)
        self.write("tests/test_a.py", GOOD_TEST)
        self.write("src/a.py", "x = 1\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "work")  # base stays on main; tests change things since it

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=T", "-c", "user.email=t@e.invalid", *args],
                       check=True, capture_output=True)

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_converge(self, *extra):
        if not {"--ticket", "--final"} & set(extra):
            extra = (*extra, "--final")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = app.main([str(self.repo / "docs/plans/p.plan.md"), "--repo", str(self.repo), *extra])
        return code, out.getvalue()

    def line(self, out, check):
        return next(line for line in out.splitlines() if check in line)

    # S17a
    @pytest.mark.integration
    def test_S17a_reports_scenario_without_test(self):
        self.write("tests/test_a.py", "def test_S1_a():\n    pass\n")
        self.commit("drop")
        code, out = self.run_converge()
        self.assertTrue(self.line(out, "coverage").startswith("FAIL"))
        self.assertIn("S12", self.line(out, "coverage"))
        self.assertIn("S2a", self.line(out, "coverage"))

    @pytest.mark.integration
    def test_S17a_id_matches_whole_token_only(self):
        self.write("tests/test_a.py", "def test_S12_b():\n    pass\n")
        self.commit("only 12")
        _, out = self.run_converge()
        cov = self.line(out, "coverage")
        self.assertIn("S1,", cov + ",")  # S1 reported missing though S12 exists
        self.assertNotIn("S12", cov)

    @pytest.mark.integration
    def test_S17a_reads_js_test_names(self):
        self.write("tests/test_a.py", "")
        self.write("web/a.test.ts", "describe('S1 x', () => { it('S12 y', () => {}); test(\"S2a z\", () => {}) })\n")
        self.commit("js")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "coverage").startswith("PASS"))

    # S17b
    @pytest.mark.integration
    def test_rust_tagged_check_sees_added_fn_or_test_attribute(self):
        self.write("docs/specs/evidence.md", "Paths: src/\n- R4 search shows citations\n")
        self.commit("spec")
        for path, before, after, expected in (
                ("tests/new.rs", None, "#[test]\nfn untagged() {}\n", "FAIL"),
                ("src/lib.rs", None, "#[cfg(test)]\nmod tests {\n#[test]\nfn untagged() {}\n}\n", "FAIL"),
                ("crates/x/tests/cli.rs", "#[test]\nfn S1_old() {}\n",
                 "#[test]\nfn untagged() {}\n", "FAIL"),
                ("tests/attribute.rs", "fn untagged() {}\n",
                 "#[tokio::test]\nfn untagged() {}\n", "FAIL"),
                ("tests/stable.rs", "/// evidence/R4: search shows citations\n#[test]\nfn old() {}\n",
                 "/// evidence/R4: search shows citations\n#[test]\nfn search_citations() {}\n", "PASS"),
                ("tests/body.rs", "#[test]\nfn untagged() {\n    old();\n}\n",
                 "#[test]\nfn untagged() {\n    new();\n}\n", "PASS"),
                ("tests/unchanged.rs", "#[test]\nfn untagged() {}\n",
                 "#[test]\nfn untagged() {}\n#[test]\nfn S1_new() {}\n", "PASS")):
            with self.subTest(path=path):
                if before is not None:
                    self.write(path, before)
                    self.commit("before Rust test change")
                self.git("branch", "-f", "main", "HEAD")
                self.write(path, after)
                _, out = self.run_converge("--ticket", "T1")
                self.assertTrue(self.line(out, "tagged").startswith(expected), out)
                if expected == "FAIL":
                    self.assertIn("untagged", self.line(out, "tagged"))
                self.commit("Rust test change")
                _, out = self.run_converge("--ticket", "T1")
                self.assertTrue(self.line(out, "tagged").startswith(expected), out)

    @pytest.mark.integration
    def test_S17b_reports_changed_test_without_id(self):
        self.write("tests/test_a.py", GOOD_TEST + "\ndef test_untagged_thing():\n    pass\n")
        _, out = self.run_converge()
        line = self.line(out, "tagged")
        self.assertTrue(line.startswith("FAIL"))
        self.assertIn("test_untagged_thing", line)

    @pytest.mark.integration
    def test_S17b_accepts_stable_spec_id_and_ignores_unchanged_tests(self):
        self.write("docs/specs/auth.md", "Paths: src/*\n- **auth/R3** WHEN x THEN y\n")
        self.commit("spec")
        self.write("tests/test_a.py", GOOD_TEST + "\nit('auth/R3 works')\n\ndef test_ok():\n    \'\'\'auth/R3: python docstring\'\'\'\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "tagged").startswith("PASS"), out)

    @pytest.mark.integration
    def test_S17b_sees_committed_changes_since_base(self):
        self.git("checkout", "-q", "-b", "feat")
        self.write("tests/test_a.py", GOOD_TEST + "\ndef test_bare():\n    pass\n")
        self.commit("feat")
        _, out = self.run_converge()
        self.assertIn("test_bare", self.line(out, "tagged"))

    @pytest.mark.integration
    def test_S17f_bare_R_id_fails_tagging_and_names_test(self):
        self.write("docs/specs/auth.md", "Paths: src/*\n- **auth/R3** WHEN x THEN y\n")
        self.commit("spec")
        self.write("tests/test_a.py", GOOD_TEST + "\ndef test_R3_bare():\n    pass\n")
        _, out = self.run_converge()
        line = self.line(out, "tagged")
        self.assertTrue(line.startswith("FAIL"))
        self.assertIn("test_R3_bare", line)

    @pytest.mark.integration
    def test_S17f_qualified_id_in_python_docstring_first_line_passes(self):
        self.write("docs/specs/auth.md", "Paths: src/*\n- **R3** WHEN x THEN y\n")
        self.commit("spec")
        self.write("tests/test_a.py", GOOD_TEST + "\ndef test_ok():\n    \'\'\'auth/R3: works\'\'\'\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "tagged").startswith("PASS"), out)

    # S17a, per ticket
    @pytest.mark.integration
    def test_S17a_ticket_checks_only_its_satisfies(self):
        self.write("tests/test_a.py", "def test_S1_a():\n    pass\n\ndef test_S12_b():\n    pass\n")
        self.commit("t1 only")
        code, out = self.run_converge("--ticket", "T1")
        self.assertTrue(self.line(out, "coverage").startswith("PASS"), out)
        _, out = self.run_converge("--ticket", "T2")
        self.assertIn("S2a", self.line(out, "coverage"))

    @pytest.mark.integration
    def test_S17a_ranges_expand_over_declared_ids_in_order(self):
        plan = PLAN.replace("| S1, S12 |", "| S1\u2013S2a |")
        self.write("docs/plans/p.plan.md", plan)
        self.write("tests/test_a.py", "def test_S1_a():\n    pass\n")
        self.commit("range")
        _, out = self.run_converge("--ticket", "T1")
        cov = self.line(out, "coverage")
        self.assertIn("S12", cov)
        self.assertIn("S2a", cov)

    @pytest.mark.integration
    def test_S17a_one_of_ticket_or_final_is_required(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            app.main([str(self.repo / "docs/plans/p.plan.md"), "--repo", str(self.repo)])

    # S17c
    @pytest.mark.integration
    def test_S17c_reports_file_outside_ticket_paths(self):
        self.write("src/a.py", "x = 2\n")
        self.write("infra/deploy.sh", "echo\n")
        self.write("docs/notes.txt", "ok\n")
        _, out = self.run_converge()
        line = self.line(out, "scope")
        self.assertTrue(line.startswith("FAIL"))
        self.assertIn("infra/deploy.sh", line)
        self.assertNotIn("src/a.py", line)
        self.assertNotIn("docs/notes.txt", line)

    @pytest.mark.integration
    def test_S17c_ignores_plan_and_specs(self):
        self.write("docs/plans/p.plan.md", PLAN + "\nmore\n")
        self.write("docs/specs/auth.md", "Paths: nothing/*\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "scope").startswith("PASS"))

    @pytest.mark.integration
    def test_S17c_ticket_scope_uses_only_that_tickets_paths(self):
        self.write("lib/x.py", "y = 1\n")
        _, out = self.run_converge("--ticket", "T1")
        self.assertIn("lib/x.py", self.line(out, "scope"))
        _, out = self.run_converge("--ticket", "T2")
        self.assertTrue(self.line(out, "scope").startswith("PASS"), out)

    # S17d
    @pytest.mark.integration
    def test_S17d_ticket_run_skips_spec_check(self):
        self.write("docs/specs/auth.md", "Paths: `src/*`\n")
        self.commit("spec")
        self.write("src/a.py", "x = 3\n")
        code, out = self.run_converge("--ticket", "T1")
        self.assertTrue(self.line(out, "spec").startswith("SKIPPED"), out)
        self.assertEqual(code, 0, out)

    @pytest.mark.integration
    def test_S17d_reports_area_whose_spec_did_not_change(self):
        self.write("docs/specs/auth.md", "# Auth\nPaths: `src/*`, lib/*.py\n")
        self.commit("spec")
        self.git("branch", "-f", "main", "HEAD")  # the spec predates the change under test
        self.write("src/a.py", "x = 3\n")
        _, out = self.run_converge()
        line = self.line(out, "spec")
        self.assertTrue(line.startswith("FAIL"))
        self.assertIn("auth", line)

    @pytest.mark.integration
    def test_S17d_passes_when_spec_changed_too(self):
        self.write("docs/specs/auth.md", "Paths: src/*\n")
        self.commit("spec")
        self.write("src/a.py", "x = 3\n")
        self.write("docs/specs/auth.md", "Paths: src/*\nedited\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "spec").startswith("PASS"))

    @pytest.mark.integration
    def test_S17d_no_specs_dir_passes_with_note(self):
        _, out = self.run_converge()
        line = self.line(out, "spec")
        self.assertTrue(line.startswith("PASS"))
        self.assertIn("no specs", line)

    # S17g
    @pytest.mark.integration
    def test_S17g_default_base_is_origin_head_target(self):
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        self.assertEqual(app.default_base(self.repo), "origin/trunk")

    @pytest.mark.integration
    def test_S17g_default_base_falls_back_to_main(self):
        self.assertEqual(app.default_base(self.repo), "main")

    @pytest.mark.integration
    def test_S17g_omitted_base_diffs_against_origin_head(self):
        self.git("update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
        self.git("checkout", "-q", "-b", "feat")
        self.write("tests/test_a.py", GOOD_TEST + "\ndef test_bare():\n    pass\n")
        self.commit("feat")
        self.git("branch", "-f", "main", "HEAD")  # main moved; only origin/HEAD is the right base
        _, out = self.run_converge()
        self.assertIn("test_bare", self.line(out, "tagged"))

    # S17e
    @pytest.mark.integration
    def test_S17e_exit_zero_when_all_pass(self):
        self.write("tests/test_a.py", GOOD_TEST + "\n# touched\n")  # bare S-IDs count only in changed files
        code, out = self.run_converge()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("PASS"), 4)

    @pytest.mark.integration
    def test_S17e_exit_nonzero_on_any_failure_via_cli(self):
        self.write("infra/x.sh", "echo\n")
        proc = subprocess.run([sys.executable, str(SCRIPT), str(self.repo / "docs/plans/p.plan.md"),
                               "--repo", str(self.repo), "--final"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FAIL", proc.stdout)

    # S17h
    def refuse(self, plan, *extra):
        self.write("docs/plans/p.plan.md", plan)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = app.main([str(self.repo / "docs/plans/p.plan.md"), "--repo", str(self.repo), *(extra or ("--final",))])
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()

    def assert_refused(self, plan, word, *extra):
        code, out, err = self.refuse(plan, *extra)
        self.assertNotIn(code, (0, None))
        self.assertNotIn("PASS", out + err)
        self.assertNotIn("FAIL", out + err)
        self.assertIn(word, out + err)

    @pytest.mark.integration
    def test_S17h_refuses_plan_not_approved(self):
        self.assert_refused(PLAN.replace("APPROVED", "DRAFT"), "APPROVED")

    @pytest.mark.integration
    def test_S17h_refuses_plan_without_status(self):
        self.assert_refused(PLAN.replace("Status: APPROVED", "Stat: APPROVED"), "Status")

    @pytest.mark.integration
    def test_S17h_status_must_not_merely_mention_approved(self):
        self.assert_refused(PLAN.replace("Status: APPROVED", "Status: DRAFT (was APPROVED)"), "APPROVED")

    @pytest.mark.integration
    def test_final_accepts_an_archived_plan(self):
        """code-driven-orchestrator/S15"""
        code, out, err = self.refuse(PLAN.replace("APPROVED", "ARCHIVED"))
        self.assertNotIn("REFUSED", out + err)
        self.assertIn(code, (0, 1))

    @pytest.mark.integration
    def test_ticket_and_other_statuses_still_refuse_under_the_archived_rule(self):
        """code-driven-orchestrator/S15"""
        self.assert_refused(PLAN.replace("APPROVED", "ARCHIVED"), "ARCHIVED", "--ticket", "T1")
        self.assert_refused(PLAN.replace("APPROVED", "DRAFT"), "DRAFT", "--final")

    @pytest.mark.integration
    def test_final_exempts_exactly_the_plan_file_from_scope_when_the_plan_lives_elsewhere(self):
        """code-driven-orchestrator/S15"""
        with tempfile.TemporaryDirectory() as other:
            plan = Path(other) / "p.plan.md"
            plan.write_text(PLAN.replace("APPROVED", "ARCHIVED"))
            self.write("docs/plans/p.plan.md", PLAN.replace("APPROVED", "ARCHIVED"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                app.main([str(plan), "--repo", str(self.repo), "--final"])
            self.assertIn("PASS scope", out.getvalue())
            self.write("docs/plans/other.plan.md", "x\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                app.main([str(plan), "--repo", str(self.repo), "--final"])
            self.assertIn("FAIL scope: docs/plans/other.plan.md", out.getvalue())

    @pytest.mark.integration
    def test_S17h_refuses_plan_without_scenarios(self):
        self.assert_refused(PLAN.replace("- **S", "- S"), "scenario")

    @pytest.mark.integration
    def test_S17h_refuses_plan_without_tickets_table(self):
        self.assert_refused(PLAN.split("## Tickets")[0], "Tickets")

    @pytest.mark.integration
    def test_S17h_refuses_with_ticket_flag_too(self):
        self.assert_refused(PLAN.replace("APPROVED", "DRAFT"), "APPROVED", "--ticket", "T1")

    @pytest.mark.integration
    def test_S17h_cli_exits_nonzero(self):
        self.write("docs/plans/p.plan.md", PLAN.replace("APPROVED", "DRAFT"))
        proc = subprocess.run([sys.executable, str(SCRIPT), str(self.repo / "docs/plans/p.plan.md"),
                               "--repo", str(self.repo), "--final"], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("APPROVED", proc.stdout + proc.stderr)

    # S17i
    RENAMED = ("def test_one():\n    '''auth/R4: one'''\n\n"
               "def test_two():\n    '''auth/R5: two'''\n\n"
               "def test_three():\n    '''auth/R6: three'''\n")

    def renamed(self, spec_lines, tests):
        self.write("docs/specs/auth.md", "Paths: src/*\n" + spec_lines)
        self.write("tests/test_a.py", tests)
        self.commit("renamed")

    @pytest.mark.integration
    def test_S17i_final_counts_spec_provenance_as_coverage(self):
        self.renamed("- **R4** WHEN a THEN b (from p/S1)\n- R5 WHEN c THEN d (from p/S12)\n"
                     "- **R6** WHEN e THEN f (from p/S2a)\n", self.RENAMED)
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "coverage").startswith("PASS"), out)

    @pytest.mark.integration
    def test_S17i_provenance_from_another_plan_does_not_count(self):
        self.renamed("- **R4** WHEN a THEN b (from other/S1)\n- R5 WHEN c THEN d (from p/S12)\n"
                     "- **R6** WHEN e THEN f (from p/S2a)\n", self.RENAMED)
        _, out = self.run_converge()
        cov = self.line(out, "coverage")
        self.assertTrue(cov.startswith("FAIL"), out)
        self.assertIn("S1", cov.replace("S12", ""))
        self.assertNotIn("S12", cov)

    @pytest.mark.integration
    def test_S17i_test_must_carry_the_matching_area_and_R(self):
        self.renamed("- **R4** WHEN a THEN b (from p/S1)\n- R5 WHEN c THEN d (from p/S12)\n"
                     "- **R6** WHEN e THEN f (from p/S2a)\n",
                     "def test_one():\n    '''auth/R4: one'''\n")
        _, out = self.run_converge()
        cov = self.line(out, "coverage")
        self.assertIn("S12", cov)
        self.assertIn("S2a", cov)
        self.assertNotIn("S1,", cov + ",")

    @pytest.mark.integration
    def test_S17i_ticket_mode_keeps_bare_names_anywhere(self):
        _, out = self.run_converge("--ticket", "T1")
        self.assertTrue(self.line(out, "coverage").startswith("PASS"), out)

    @pytest.mark.integration
    def test_S17i_final_bare_name_in_unchanged_file_does_not_count(self):
        _, out = self.run_converge()
        cov = self.line(out, "coverage")
        self.assertTrue(cov.startswith("FAIL"), out)
        for sid in ("S1", "S12", "S2a"):
            self.assertIn(sid, cov)

    @pytest.mark.integration
    def test_S17i_final_bare_name_in_changed_file_counts(self):
        self.write("tests/test_a.py", GOOD_TEST + "\n# touched\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "coverage").startswith("PASS"), out)

    @pytest.mark.integration
    def test_S17i_final_bare_name_added_since_base_counts(self):
        self.write("tests/test_a.py", "")
        self.write("tests/test_b.py", GOOD_TEST)
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "coverage").startswith("PASS"), out)

    # S17j
    @pytest.mark.integration
    def test_S17j_spec_without_paths_line_fails_and_names_file(self):
        self.write("docs/specs/auth.md", "# Auth\n- **R1** WHEN a THEN b\n")
        _, out = self.run_converge()
        line = self.line(out, "spec")
        self.assertTrue(line.startswith("FAIL"), out)
        self.assertIn("docs/specs/auth.md", line)

    @pytest.mark.integration
    def test_S17j_empty_paths_line_fails(self):
        self.write("docs/specs/auth.md", "Paths:\n- **R1** WHEN a THEN b\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "spec").startswith("FAIL"), out)
        self.assertIn("docs/specs/auth.md", self.line(out, "spec"))

    @pytest.mark.integration
    def test_S17j_prose_after_paths_is_unparseable(self):
        self.write("docs/specs/auth.md", "Paths: the auth code\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "spec").startswith("FAIL"), out)

    @pytest.mark.integration
    def test_S17j_documented_form_with_backticks_passes(self):
        self.write("docs/specs/auth.md", "Paths: `a/`, src/**/*.ts\n")
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "spec").startswith("PASS"), out)

    # S17k
    @pytest.mark.integration
    def test_S17k_tagging_check_sees_next_line_docstring(self):
        """S31: the tagging check reads the docstring's first text line."""
        self.write("tests/test_a.py", GOOD_TEST + '\ndef test_ok():\n    """\n    S1 next line\n    """\n')
        _, out = self.run_converge()
        self.assertTrue(self.line(out, "tagged").startswith("PASS"), out)


class PureLogicTests(unittest.TestCase):
    """Pure functions of converge.py: in process, reading only files in their own temp directory, no git."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    @pytest.mark.unit
    def test_rust_names_require_test_attributes(self):
        """S31: the Rust test names are the functions that carry a test attribute."""
        names = app.names_in([
            "fn helper() {}", "#[test_case(1)]", "fn parameterized() {}",
            "#[test]", "fn S1_plain() {}",
            "#[ignore]", "#[tokio::test]", "#[should_panic]", "pub fn S12_public() {}",
            "#[some::runtime::test(flavor = \"current_thread\")]", "async fn S2a_async() {}",
        ])
        self.assertEqual(names, ["S1_plain", "S12_public", "S2a_async"])

    @pytest.mark.unit
    def test_rust_doc_comment_first_line_carries_stable_id(self):
        """S31: a Rust doc comment's first line carries the stable ID."""
        self.assertEqual(app.names_in([
            "/// evidence/R4: search shows citations", "/// S12 later does not count",
            "#[ignore]", "#[test]", "#[should_panic]", "fn search_citations() {}",
            "/// detached/R5", "", "#[test]", "fn S1_detached() {}",
            "/// helper/R6", "fn helper() {}", "#[test]", "fn S2a_next() {}",
        ]), ["search_citations evidence/R4: search shows citations", "S1_detached", "S2a_next"])

    @pytest.mark.unit
    def test_rust_test_file_discovery(self):
        """S31: a Rust file is a test file when it is under tests/ or holds cfg(test)."""
        for path, source, expected in (
                ("tests/cli.rs", "", True),
                ("crates/x/tests/cli.rs", "", True),
                ("src/lib.rs", "#[cfg(test)]\nmod tests {}", True),
                ("src/main.rs", "fn main() {}", False)):
            with self.subTest(path=path):
                self.write(path, source)
                self.assertEqual(app.is_test_file(self.repo / path), expected)

    # S17k
    @pytest.mark.unit
    def test_S17k_id_on_line_after_opening_quotes_is_seen(self):
        names = app.names_in(["def test_x():", '    """', "    S1 does a thing", '    """'])
        self.assertTrue(any(app.has_id(n, "S1") for n in names), names)

    @pytest.mark.unit
    def test_S17k_blank_lines_before_text_are_skipped(self):
        names = app.names_in(["def test_x():", "    '''", "", "    auth/R3 text", "    '''"])
        self.assertTrue(any("auth/R3" in n for n in names), names)

    @pytest.mark.unit
    def test_S17k_only_the_first_text_line_counts(self):
        names = app.names_in(["def test_x():", '    """', "    nothing here", "    S1 later", '    """'])
        self.assertFalse(any(app.has_id(n, "S1") for n in names), names)

    @pytest.mark.unit
    def test_S17k_following_code_is_not_a_docstring(self):
        names = app.names_in(["def test_x():", "    value = 'S1'", "    pass"])
        self.assertFalse(any(app.has_id(n, "S1") for n in names), names)

    # S31
    @pytest.mark.unit
    def test_S31_pure_logic_tests_carry_unit_and_no_repository(self):
        for name in ("test_rust_names_require_test_attributes", "test_rust_doc_comment_first_line_carries_stable_id",
                     "test_rust_test_file_discovery", "test_S17k_id_on_line_after_opening_quotes_is_seen",
                     "test_S17k_blank_lines_before_text_are_skipped", "test_S17k_only_the_first_text_line_counts",
                     "test_S17k_following_code_is_not_a_docstring"):
            self.assertTrue(hasattr(PureLogicTests, name), name)
            self.assertFalse(hasattr(ConvergeTests, name), name)
        for name in (name for name in vars(PureLogicTests) if name.startswith("test_")):
            marks = {mark.name for mark in getattr(getattr(PureLogicTests, name), "pytestmark", [])}
            self.assertEqual(marks, {"unit"}, name)


if __name__ == "__main__":
    unittest.main()
