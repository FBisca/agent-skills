"""idea_check.py (contract v2) against throwaway idea folders; scenario IDs name the tests."""

import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "idea_check.py"


def load():
    spec = importlib.util.spec_from_file_location("idea_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha12(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:12]


BRIEF = "# Brief\nWe sync the ledger.\n## Terms\n| term | meaning |\n|---|---|\n| Sync date | last ledger sync |\n"
GATES = (
    "- 2026-10-10 gate1: continue: top assumptions ready\n"
    "- 2026-10-25 gate2: pass by CFO: all closed\n"
    f"- 2026-10-26 cold-read: pass {sha12(BRIEF)}\n"
)
HOURS = "- 2026-10-01 framing 2h\n- 2026-10-10 answering 3h"
IDEA = """---
type: project
status: idea
stage: {stage}
entry: {entry}
decider: CFO
---
# Idea
## Hours
{hours}
## Gates
{gates}
"""
COLS = ("id", "assumption", "if wrong", "owner", "source", "test", "result")
ROWS = [
    ("A1", "Clients want it", "no demand", "operator", "Q1", "interview: 3 of 5 ops leads describe it", "confirmed"),
    ("A2", "API exists", "rebuild", "engineering", "docs", "spike: API returns the sync date", "changed: use export"),
    ("A3", "Cost fits", "too dear", "finance", "me", "data: cost under the fee cap",
     "accepted by CFO: small spend; revisit: Q1 review"),
    ("A4", "Easy", "training", "decider", "me", "", "killed"),
]
ANSWERS = "## Q2 cost\nOwner: finance\nDate: 2026-10-20\nLink: https://example.com/a\nSummary: costs ok\n"


def table(rows, cols=COLS):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(r) + " |\n" for r in rows)


class IdeaCheckTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name) / "idea"
        self.dir.mkdir()
        self.app = load()
        self.idea()
        self.write("assumptions.md", table(ROWS))
        self.write("answers.md", ANSWERS)
        self.write("Brief.md", BRIEF)

    def write(self, name, text):
        (self.dir / name).write_text(text)

    def idea(self, stage="prd", entry="raw", hours=HOURS, gates=GATES):
        self.write("Robo-Doc.md", IDEA.format(stage=stage, entry=entry, hours=hours, gates=gates))

    def run_check(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.app.main([str(self.dir), *args])
        return code, out.getvalue(), err.getvalue()

    def rows(self, **edits):
        """ROWS with test/result/owner replaced on row A1 (dict of column -> value)."""
        row = dict(zip(COLS, ROWS[0]), **edits)
        self.write("assumptions.md", table([tuple(row[c] for c in COLS), *ROWS[1:]]))

    # --- index note discovery
    def test_S1_missing_index_note_is_refused(self):
        (self.dir / "Robo-Doc.md").unlink()
        code, out, err = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", out + err)

    def test_S1_two_index_notes_are_refused(self):
        self.write("Other.md", IDEA.format(stage="prd", entry="raw", hours=HOURS, gates=GATES))
        self.assertEqual(self.run_check()[0], 2)

    def test_S1_notes_without_type_project_do_not_count(self):
        self.write("Notes.md", "---\ntype: note\n---\nhi\n")
        self.assertEqual(self.run_check()[0], 0)

    def test_S1_side_files_with_type_project_are_not_candidates(self):
        self.write("assumptions.md", "---\ntype: project\n---\n" + table(ROWS))
        self.write("Brief.md", "---\ntype: project\n---\n" + BRIEF)
        self.assertEqual(self.run_check("--gate", "2")[0], 0)

    def test_S1_bom_directory_and_binary_md_are_tolerated(self):
        path = self.dir / "Robo-Doc.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        (self.dir / "folder.md").mkdir()
        (self.dir / "bin.md").write_bytes(b"\xff\xfe\x00bad")
        self.assertEqual(self.run_check()[0], 0)

    def test_S2_bad_stage_fails_and_quoted_stage_passes(self):
        self.idea(stage="done")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("FAIL stage-value", out)
        self.idea(stage='"prd"')
        self.assertIn("PASS stage-value", self.run_check()[1])

    # --- S38
    def test_S38_cut_checks_never_print_and_absent_files_do_not_fail(self):
        for name in ("premortem.md", "gates.md", "frame.md"):
            self.assertFalse((self.dir / name).exists())
        for args in ((), ("--gate", "1"), ("--gate", "2")):
            code, out, _ = self.run_check(*args)
            self.assertEqual(code, 0, out)
            for cut in ("assumption-values", "premortem-links", "frame-sources", "frame-terms", "frame-language",
                        "unknown-to-assumption", "top3-ready", "people-cap", "frame-owners"):
                self.assertNotIn(cut, out)

    def test_S38_check_names_per_gate(self):
        names = lambda *a: [l.split()[1].rstrip(":") for l in self.run_check(*a)[1].splitlines()]
        base = ["stage-value", "gate-reason", "hours-logged"]
        g1 = base + ["question-owners", "test-criterion"]
        self.assertEqual(names(), base)
        self.assertEqual(names("--gate", "1"), g1)
        self.assertEqual(names("--gate", "2"), g1 + ["assumptions-closed", "answers-sourced",
                                                      "decider-signoff", "brief-read"])

    def test_S38_all_pass_at_gate_2(self):
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 0, out)
        self.assertTrue(all(l.startswith("PASS ") for l in out.splitlines()), out)

    # --- S39
    def test_S39_kill_or_reshape_without_reason_fails_gate_reason(self):
        for line in ("- 2026-10-26 gate1: kill", "- 2026-10-27 gate2: reshape:  "):
            self.idea(gates=GATES + line + "\n")
            code, out, _ = self.run_check()
            self.assertEqual(code, 1)
            self.assertIn("FAIL gate-reason", out)

    def test_S39_kill_with_reason_and_no_gates_section_pass(self):
        self.idea(gates=GATES + "- 2026-10-26 gate1: kill: no demand\n")
        self.assertIn("PASS gate-reason", self.run_check()[1])
        self.write("Robo-Doc.md", "---\ntype: project\nstage: framing\n---\n# Idea\n")
        self.assertIn("PASS gate-reason", self.run_check()[1])

    def test_S39_gate_lines_outside_the_gates_section_are_ignored(self):
        text = (self.dir / "Robo-Doc.md").read_text() + "## Notes\n- 2026-10-26 gate1: kill\n"
        self.write("Robo-Doc.md", text)
        self.assertIn("PASS gate-reason", self.run_check()[1])

    def test_S39_malformed_gate_lines_fail_gate_reason(self):
        for line in ("- 2026-10-27 gate1: Kill", "- 2026-10-27 gate1: killed: dead", "- 2026-10-27 GATE2: KILL",
                     "- 2026-10-27 gate1: maybe"):
            self.idea(gates=GATES + line + "\n")
            code, out, _ = self.run_check()
            self.assertEqual(code, 1, line)
            self.assertIn("FAIL gate-reason", out)

    def test_S39_gates_heading_is_case_insensitive_and_all_sections_read(self):
        text = (self.dir / "Robo-Doc.md").read_text().replace("## Gates", "## gates")
        self.write("Robo-Doc.md", text + "## Gates\n- 2026-10-27 gate1: kill\n")
        self.assertIn("FAIL gate-reason", self.run_check()[1])

    def test_S45_later_kill_in_any_case_cancels_pass(self):
        for line in ("- 2026-10-27 gate1: KILL: dead", "- 2026-10-27 Gate1: Reshape: new"):
            self.idea(gates=GATES + line + "\n")
            self.assertIn("FAIL decider-signoff", self.run_check("--gate", "2")[1])

    def test_S43_accepted_needs_non_blank_role(self):
        for result in ("accepted by : x; revisit: later", "accepted by  : x; revisit: later"):
            self.rows(result=result)
            self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL assumptions-closed.*A1")

    # --- S40
    def test_S40_no_positive_hours_line_fails_past_framing(self):
        for hours in ("", "- 2026-10-01 framing 0h", "no hours here"):
            self.idea(hours=hours)
            code, out, _ = self.run_check()
            self.assertEqual(code, 1, hours)
            self.assertIn("FAIL hours-logged", out)

    def test_S40_any_label_counts_and_no_per_stage_line_is_required(self):
        self.idea(stage="prd", hours="- 2026-10-01 whatever 1.5h")
        self.assertIn("PASS hours-logged", self.run_check()[1])

    def test_S40_framing_stage_needs_no_hours(self):
        self.idea(stage="framing", hours="")
        self.assertIn("PASS hours-logged", self.run_check()[1])

    # --- S41
    def test_S41_empty_result_and_empty_owner_fails_naming_row(self):
        self.rows(owner="", result="")
        for gate in ("1", "2"):
            code, out, _ = self.run_check("--gate", gate)
            self.assertEqual(code, 1)
            self.assertRegex(out, r"FAIL question-owners.*A1")

    def test_S41_owner_or_result_present_passes(self):
        self.rows(owner="", result="confirmed")
        self.assertIn("PASS question-owners", self.run_check("--gate", "1")[1])
        self.rows(owner="finance", result="")
        self.assertIn("PASS question-owners", self.run_check("--gate", "1")[1])

    def test_S41_columns_match_by_name_in_any_order(self):
        cols = tuple(reversed(COLS))
        row = tuple(reversed(("A1", "x", "y", "", "q", "", "")))
        self.write("assumptions.md", table([row], cols))
        self.assertRegex(self.run_check("--gate", "1")[1], r"FAIL question-owners.*A1")

    def test_S41_empty_or_tableless_assumptions_fail_at_gate_2(self):
        for text in ("", "no table here\n", table([], COLS)):
            self.write("assumptions.md", text)
            for gate in ("1", "2"):
                code, out, _ = self.run_check("--gate", gate)
                self.assertEqual(code, 1, (text, gate))
                self.assertRegex(out, r"FAIL question-owners: (missing columns|no questions recorded)")
            self.assertRegex(out, r"FAIL assumptions-closed")

    def test_S41_header_only_table_says_no_questions_recorded(self):
        self.write("assumptions.md", table([], COLS))
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL question-owners: no questions recorded")

    def test_S41_missing_header_column_fails_naming_it(self):
        cols = tuple(c for c in COLS if c != "if wrong")
        self.write("assumptions.md", table([tuple(r[i] for i, c in enumerate(COLS) if c != "if wrong") for r in ROWS], cols))
        for gate in ("1", "2"):
            out = self.run_check("--gate", gate)[1]
            self.assertRegex(out, r"FAIL question-owners.*if wrong")
            self.assertRegex(out, r"FAIL test-criterion.*if wrong")

    def test_S41_row_with_empty_id_is_named_by_number(self):
        self.write("assumptions.md", table([("", "x", "y", "", "me", "", ""), ROWS[0]]))
        self.assertRegex(self.run_check("--gate", "1")[1], r"FAIL question-owners.*row 1")

    def test_S41_decided_entry_still_runs_question_owners(self):
        self.idea(entry="decided")
        self.rows(owner="", result="")
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL question-owners.*A1")

    # --- S42
    def test_S42_malformed_test_fails_naming_row(self):
        for test in ("ask people", "chat: ask", "interview:", "interview: "):
            self.rows(test=test)
            code, out, _ = self.run_check("--gate", "1")
            self.assertEqual(code, 1, test)
            self.assertRegex(out, r"FAIL test-criterion.*A1")

    def test_S42_valid_types_and_empty_test_pass(self):
        for test in ("Interview: five calls", "prototype: it clicks", "data: x", "survey: y", "spike: z", ""):
            self.rows(test=test)
            self.assertIn("PASS test-criterion", self.run_check("--gate", "1")[1], test)

    def test_S42_every_row_with_a_test_is_checked(self):
        self.write("assumptions.md", table([("A9", "x", "y", "ops", "me", "free text", "")]))
        self.assertRegex(self.run_check("--gate", "1")[1], r"FAIL test-criterion.*A9")

    # --- S43
    def test_S43_bad_results_fail_naming_row(self):
        for result in ("", "not tested", "ok", "accepted by CFO", "accepted by CFO: small spend",
                       "accepted by CFO: ; revisit: later", "accepted by CFO: x; revisit:", "changed:"):
            self.rows(result=result)
            code, out, _ = self.run_check("--gate", "2")
            self.assertEqual(code, 1, result)
            self.assertRegex(out, r"FAIL assumptions-closed.*A1")

    def test_S43_good_results_pass(self):
        for result in ("confirmed", "Killed", "changed: use the export",
                       "accepted by CFO: small spend; revisit: Q1 review"):
            self.rows(result=result)
            self.assertIn("PASS assumptions-closed", self.run_check("--gate", "2")[1], result)

    def test_S43_not_checked_at_gate_1(self):
        self.rows(result="")
        self.assertNotIn("assumptions-closed", self.run_check("--gate", "1")[1])

    def test_S43_escaped_pipe_does_not_shift_columns(self):
        self.rows(assumption=r"See [[note\|alias]]", result="")
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL assumptions-closed.*A1")

    def test_S43_missing_assumptions_file_fails_at_a_gate(self):
        (self.dir / "assumptions.md").unlink()
        self.assertIn("FAIL assumptions-closed", self.run_check("--gate", "2")[1])

    # --- S44
    def test_S44_entry_missing_a_field_fails_naming_entry(self):
        for field in ("Owner", "Date", "Link", "Summary"):
            text = "\n".join(l for l in ANSWERS.splitlines() if not l.startswith(field)) + "\n"
            self.write("answers.md", text)
            code, out, _ = self.run_check("--gate", "2")
            self.assertEqual(code, 1, field)
            self.assertRegex(out, r"FAIL answers-sourced.*Q2")

    def test_S44_empty_values_fail(self):
        self.write("answers.md", ANSWERS.replace("Summary: costs ok", "Summary:  "))
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL answers-sourced.*Q2")

    def test_S44_date_must_be_real_and_not_future(self):
        for date in ("2026-13-45", "2999-01-01", "20/10/2026", "soon"):
            self.write("answers.md", ANSWERS.replace("2026-10-20", date))
            self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL answers-sourced.*Q2", date)

    def test_S44_today_is_allowed(self):
        import datetime
        self.write("answers.md", ANSWERS.replace("2026-10-20", datetime.date.today().isoformat()))
        self.assertIn("PASS answers-sourced", self.run_check("--gate", "2")[1])

    def test_S44_absent_answers_file_has_no_entries(self):
        (self.dir / "answers.md").unlink()
        self.assertIn("PASS answers-sourced", self.run_check("--gate", "2")[1])

    # --- S45
    def test_S45_latest_gate2_line_must_be_pass_by_decider(self):
        bad = (GATES.replace("pass by CFO", "pass by CPO"),
               "- 2026-10-10 gate1: continue: ok\n",
               GATES + "- 2026-10-27 gate2: continue\n",
               GATES + "- 2026-10-27 gate2: kill: dead\n")
        for gates in bad:
            self.idea(gates=gates)
            code, out, _ = self.run_check("--gate", "2")
            self.assertEqual(code, 1, gates)
            self.assertIn("FAIL decider-signoff", out)

    def test_S45_later_kill_or_reshape_cancels_pass(self):
        for line in ("- 2026-10-27 gate1: reshape: new angle", "- 2026-10-27 gate1: kill: dead"):
            self.idea(gates=GATES + line + "\n")
            self.assertIn("FAIL decider-signoff", self.run_check("--gate", "2")[1])

    def test_S45_earlier_kill_does_not_cancel_a_later_pass(self):
        self.idea(gates="- 2026-10-01 gate1: kill: r\n" + GATES)
        self.assertIn("PASS decider-signoff", self.run_check("--gate", "2")[1])

    def test_S45_role_matches_case_insensitively_and_empty_decider_fails(self):
        self.idea(gates=GATES.replace("pass by CFO", "pass by cfo"))
        self.assertIn("PASS decider-signoff", self.run_check("--gate", "2")[1])
        text = (self.dir / "Robo-Doc.md").read_text().replace("decider: CFO\n", "")
        self.write("Robo-Doc.md", text)
        self.assertIn("FAIL decider-signoff", self.run_check("--gate", "2")[1])

    def test_S45_decided_entry_still_runs_signoff(self):
        self.idea(entry="decided", gates="")
        self.assertIn("FAIL decider-signoff", self.run_check("--gate", "2")[1])

    # --- S46
    def cold(self, line):
        self.idea(gates=GATES.split("- 2026-10-26")[0] + line + "\n")

    def test_S46_pass_and_accepted_with_current_sha_pass(self):
        sha = sha12(BRIEF)
        for line in (f"- 2026-10-26 cold-read: pass {sha}", f"- 2026-10-26 cold-read: accepted {sha} by user"):
            self.cold(line)
            code, out, _ = self.run_check("--gate", "2")
            self.assertEqual(code, 0, out)
            self.assertIn("PASS brief-read", out)

    def test_S46_missing_wrong_or_unattributed_line_fails_with_current_sha(self):
        sha = sha12(BRIEF)
        for line in ("", "- 2026-10-26 cold-read: pass aaaaaaaaaaaa", f"- 2026-10-26 cold-read: accepted {sha}",
                     f"- 2026-10-26 cold-read: accepted {sha} by", f"- 2026-10-26 cold-read: blocked {sha}"):
            self.cold(line)
            code, out, _ = self.run_check("--gate", "2")
            self.assertEqual(code, 1, line)
            self.assertRegex(out, rf"FAIL brief-read.*{sha}")

    def test_S46_only_the_latest_cold_read_line_counts(self):
        sha = sha12(BRIEF)
        self.cold(f"- 2026-10-26 cold-read: pass {sha}\n- 2026-10-27 cold-read: blocked {sha}")
        self.assertIn("FAIL brief-read", self.run_check("--gate", "2")[1])
        self.cold(f"- 2026-10-26 cold-read: blocked {sha}\n- 2026-10-27 cold-read: pass {sha}")
        self.assertIn("PASS brief-read", self.run_check("--gate", "2")[1])

    def test_S46_brief_missing_or_without_terms_fails(self):
        (self.dir / "Brief.md").unlink()
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL brief-read.*Brief.md missing")
        brief = "# Brief\nno terms\n"
        self.write("Brief.md", brief)
        self.cold(f"- 2026-10-26 cold-read: pass {sha12(brief)}")
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL brief-read.*## Terms")

    def test_S46_brief_is_found_by_exact_filename(self):
        (self.dir / "Brief.md").unlink()
        self.write("brief.md", BRIEF)
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL brief-read.*Brief.md missing")
        self.write("brief.md", "---\ntype: project\n---\n" + BRIEF)
        self.assertNotEqual(self.run_check("--gate", "2")[0], 2)

    def test_S46_sha_ignores_frontmatter_and_outer_whitespace(self):
        self.write("Brief.md", "---\ntags: [x]\n---\n" + BRIEF + "\n\n")
        self.assertIn("PASS brief-read", self.run_check("--gate", "2")[1])

    def test_S46_edited_brief_fails(self):
        self.write("Brief.md", BRIEF + "More.\n")
        self.assertIn("FAIL brief-read", self.run_check("--gate", "2")[1])


if __name__ == "__main__":
    unittest.main()
