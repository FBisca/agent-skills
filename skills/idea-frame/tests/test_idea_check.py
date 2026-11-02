"""idea_check.py against throwaway idea folders; scenario IDs name the tests."""

import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "idea_check.py"


def load():
    spec = importlib.util.spec_from_file_location("idea_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
"""
FRAME = """# Frame
## Q1 Who has the problem?
Source: me
## Q2 What does it cost?
Source: unknown
Owner: Finance
## Q3 Is there data?
Source: lookup https://example.com/x
## Terms
| term | meaning | link |
|---|---|---|
| Sync date | when the ledger last synced | https://example.com/sync |
"""
ROWS = [
    ("A1", "value", "Clients want it (Q2)", "high", "low", "operator/user", "interview: 3 of 5 ops leads describe it", "confirmed"),
    ("A2", "feasibility", "API exists", "high", "med", "engineering", "spike: API returns the sync date", "accepted by decider"),
    ("A3", "viability", "Cost fits", "high", "low", "finance", "data: cost under the fee cap", "ok"),
    ("A4", "usability", "Easy", "low", "low", "decider", "", ""),
]
PREMORTEM = "# Pre-mortem\n- Nobody uses it → PRD: adoption plan\n- Cost blows up → A3\n"
ANSWERS = "## Q2\nOwner: finance\nDate: 2026-10-20\nSummary: costs ok\nLink: https://example.com/a\n"
def sha12(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:12]


GATES = (
    "- 2026-10-10 gate1: continue: top 3 ready\n"
    "- 2026-10-25 gate2: pass by CFO: all closed\n"
    f"- 2026-10-26 language: pass {sha12(FRAME)}\n"
)
HOURS = "- 2026-10-01 framing 2h\n- 2026-10-05 gate1 1h\n- 2026-10-10 answering 3h\n- 2026-10-20 gate2 1h"


def table(rows):
    head = "| id | risk | assumption | importance | evidence | owner | test | result |\n|---|---|---|---|---|---|---|---|\n"
    return head + "".join("| " + " | ".join(r) + " |\n" for r in rows)


class IdeaCheckTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.dir = self.root / "idea"
        self.dir.mkdir()
        self.app = load()
        self.idea(stage="prd")
        self.write("frame.md", FRAME)
        self.write("assumptions.md", table(ROWS))
        self.write("premortem.md", PREMORTEM)
        self.write("answers.md", ANSWERS)
        self.write("gates.md", GATES)

    def write(self, name, text):
        (self.dir / name).write_text(text)

    def idea(self, stage="prd", entry="raw", hours=HOURS):
        self.write("Robo-Doc.md", IDEA.format(stage=stage, entry=entry, hours=hours))

    def run_check(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.app.main([str(self.dir), *args])
        return code, out.getvalue(), err.getvalue()

    def test_S1_missing_index_note_is_refused(self):
        (self.dir / "Robo-Doc.md").unlink()
        code, out, err = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", out + err)

    def test_S1_two_index_notes_are_refused(self):
        self.write("Other.md", IDEA.format(stage="prd", entry="raw", hours=HOURS))
        code, out, err = self.run_check()
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", out + err)

    def test_S1_notes_without_type_project_do_not_count(self):
        self.write("Notes.md", "---\ntype: note\n---\nhi\n")
        self.assertEqual(self.run_check()[0], 0)
        (self.dir / "Robo-Doc.md").unlink()
        self.assertEqual(self.run_check()[0], 2)

    def test_S2_bad_stage_fails(self):
        self.idea(stage="done")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("FAIL stage-value", out)

    def test_S3_question_without_source_fails_and_is_named(self):
        self.write("frame.md", FRAME + "## Q4 Who pays?\nno source here\n")
        code, out, _ = self.run_check("--gate", "1")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL frame-sources.*Q4")

    def test_S4_unknown_question_without_assumption_fails(self):
        rows = [(r[0], r[1], r[2].replace("(Q2)", ""), *r[3:]) for r in ROWS]
        self.write("assumptions.md", table(rows))
        code, out, _ = self.run_check("--gate", "1")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL unknown-to-assumption.*Q2")

    def test_S5_fewer_than_three_ready_high_assumptions_fails(self):
        rows = [r if r[0] != "A3" else (*r[:6], "", r[7]) for r in ROWS]
        self.write("assumptions.md", table(rows))
        code, out, _ = self.run_check("--gate", "1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL top3-ready", out)

    def test_S6_bad_risk_or_owner_fails(self):
        for col, val in ((1, "money"), (5, "intern")):
            rows = [(*ROWS[0][:col], val, *ROWS[0][col + 1:]), *ROWS[1:]]
            self.write("assumptions.md", table(rows))
            code, out, _ = self.run_check()
            self.assertEqual(code, 1)
            self.assertIn("FAIL assumption-values", out)

    def test_S7_premortem_item_without_link_fails(self):
        self.write("premortem.md", PREMORTEM + "- Regulators object\n")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("FAIL premortem-links", out)

    def test_S8_kill_without_reason_fails(self):
        self.write("gates.md", GATES + "- 2026-10-26 gate1: kill\n")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("FAIL gate-reason", out)

    def test_S8_reshape_without_reason_fails(self):
        self.write("gates.md", GATES + "- 2026-10-27 gate1: reshape:  \n")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("FAIL gate-reason", out)

    def test_S9_open_high_assumption_fails(self):
        rows = [(*ROWS[0][:7], ""), *ROWS[1:]]
        self.write("assumptions.md", table(rows))
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL assumptions-closed.*A1")

    def test_S10_answer_without_link_fails(self):
        self.write("answers.md", ANSWERS.replace("Link: https://example.com/a\n", ""))
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL answers-sourced.*Link")

    def test_S11_signoff_must_match_decider(self):
        self.write("gates.md", GATES.replace("pass by CFO", "pass by CPO"))
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertIn("FAIL decider-signoff", out)
        self.write("gates.md", "- 2026-10-10 gate1: continue: ok\n")
        self.assertIn("FAIL decider-signoff", self.run_check("--gate", "2")[1])

    def test_S12_completed_stage_without_hours_fails(self):
        self.idea(stage="prd", hours="- 2026-10-01 framing 2h")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL hours-logged.*gate1")

    def test_S13_decided_entry_skips_frame_and_premortem_checks(self):
        self.idea(entry="decided")
        (self.dir / "frame.md").unlink()
        (self.dir / "premortem.md").unlink()
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 0, out)
        for name in ("frame-sources", "frame-owners", "unknown-to-assumption", "top3-ready", "premortem-links",
                     "frame-terms", "frame-language"):
            self.assertIn(f"SKIPPED {name}", out)
        for name in ("assumptions-closed", "answers-sourced", "decider-signoff", "hours-logged"):
            self.assertIn(f"PASS {name}", out)

    def test_S13_decided_entry_still_runs_closing_checks(self):
        self.idea(entry="decided")
        self.write("gates.md", "")
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertIn("FAIL decider-signoff", out)

    def test_S14_all_pass_prints_one_pass_per_check(self):
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 0, out)
        lines = out.strip().splitlines()
        self.assertTrue(all(l.startswith("PASS ") for l in lines), out)
        names = [l.split()[1].rstrip(":") for l in lines]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 16)

    def test_S9_escaped_pipe_does_not_shift_columns(self):
        rows = [(ROWS[0][0], "value", r"See [[note\|alias]] (Q2)", *ROWS[0][3:7], ""), *ROWS[1:]]
        self.write("assumptions.md", table(rows))
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL assumptions-closed.*A1")

    def test_S3_wikilink_with_spaces_and_any_case_are_valid_sources(self):
        self.write("frame.md", "## Q1 a\nSource: lookup [[Idea to PRD - PRD]]\n## Q2 b\nSource: Unknown\n")
        code, out, _ = self.run_check("--gate", "1")
        self.assertIn("PASS frame-sources", out)
        self.assertIn("PASS unknown-to-assumption", out)

    def test_S2_quoted_frontmatter_value_is_accepted(self):
        self.write("Robo-Doc.md", (self.dir / "Robo-Doc.md").read_text().replace("stage: prd", 'stage: "prd"'))
        self.assertIn("PASS stage-value", self.run_check()[1])

    def test_S7_trailing_punctuation_after_assumption_link(self):
        self.write("premortem.md", "- Cost blows up → A3.\n")
        self.assertIn("PASS premortem-links", self.run_check()[1])

    def test_S7_link_to_unknown_assumption_fails(self):
        self.write("premortem.md", "- Cost blows up → A9\n")
        code, out, _ = self.run_check()
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL premortem-links.*A9")

    def test_S10_missing_answers_passes_when_nothing_is_open(self):
        (self.dir / "answers.md").unlink()
        self.write("frame.md", FRAME.replace("Source: unknown", "Source: me"))
        self.assertIn("PASS answers-sourced", self.run_check("--gate", "2")[1])

    def test_S10_missing_answers_fails_with_unknown_question(self):
        (self.dir / "answers.md").unlink()
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertIn("FAIL answers-sourced", out)

    def test_S10_missing_answers_fails_with_open_high_assumption(self):
        (self.dir / "answers.md").unlink()
        self.write("frame.md", FRAME.replace("Source: unknown", "Source: me"))
        self.write("assumptions.md", table([(*ROWS[0][:7], ""), *ROWS[1:]]))
        self.assertIn("FAIL answers-sourced", self.run_check("--gate", "2")[1])

    def test_S7_side_file_frontmatter_is_ignored(self):
        fm = "---\ntype: note\ntags:\n  - x\n---\n"
        for name in ("premortem.md", "gates.md", "frame.md", "answers.md"):
            self.write(name, fm + (self.dir / name).read_text())
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 0, out)

    def test_S1_side_file_with_type_project_is_not_a_candidate(self):
        self.write("frame.md", "---\ntype: project\n---\n" + FRAME)
        self.assertEqual(self.run_check()[0], 0)

    def test_S1_subfolder_note_with_type_project_is_ignored(self):
        (self.dir / "sub").mkdir()
        (self.dir / "sub" / "Other.md").write_text("---\ntype: project\n---\n")
        self.assertEqual(self.run_check()[0], 0)

    def test_S1_bom_directory_and_binary_md_are_tolerated(self):
        path = self.dir / "Robo-Doc.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        (self.dir / "folder.md").mkdir()
        (self.dir / "bin.md").write_bytes(b"\xff\xfe\x00bad")
        self.assertEqual(self.run_check()[0], 0)

    def test_S26_unknown_question_without_owner_fails_and_is_named(self):
        for frame in (FRAME.replace("Owner: Finance\n", ""), FRAME.replace("Owner: Finance", "Owner: intern")):
            self.write("frame.md", frame)
            for gate in ("1", "2"):
                code, out, _ = self.run_check("--gate", gate)
                self.assertEqual(code, 1)
                self.assertRegex(out, r"FAIL frame-owners.*Q2")

    def test_S26_owner_is_case_insensitive_and_only_unknowns_need_one(self):
        self.write("frame.md", FRAME.replace("Owner: Finance", "owner:  Operator/User"))
        self.assertIn("PASS frame-owners", self.run_check("--gate", "1")[1])

    def test_S26_decided_entry_skips_frame_owners(self):
        self.idea(entry="decided")
        self.write("frame.md", FRAME.replace("Owner: Finance\n", ""))
        self.assertIn("SKIPPED frame-owners", self.run_check("--gate", "2")[1])

    def test_S27_more_than_twelve_people_items_fails(self):
        def answers(n_people, n_eng):
            e = "## Q{i}\nOwner: {o}\nDate: 2026-10-20\nSummary: s\nLink: https://example.com/a\n"
            return "".join(e.format(i=i, o="finance") for i in range(n_people)) + \
                "".join(e.format(i=100 + i, o="Engineering") for i in range(n_eng))
        self.write("answers.md", answers(13, 5))
        code, out, _ = self.run_check("--gate", "2")
        self.assertEqual(code, 1)
        self.assertIn("FAIL people-cap", out)
        self.write("answers.md", answers(12, 5))
        self.assertIn("PASS people-cap", self.run_check("--gate", "2")[1])

    def test_S26_owner_matches_on_first_token(self):
        self.write("frame.md", FRAME.replace("Owner: Finance", "Owner: finance (role)"))
        self.assertIn("PASS frame-owners", self.run_check("--gate", "1")[1])

    def test_S27_owner_matches_on_first_token_and_missing_owner_counts(self):
        e = "## Q{i}\n{o}Date: 2026-10-20\nSummary: s\nLink: https://example.com/a\n"
        eng = "".join(e.format(i=i, o="Owner: Engineering via Gather\n") for i in range(20))
        self.write("answers.md", eng)
        self.assertIn("PASS people-cap", self.run_check("--gate", "2")[1])
        self.write("answers.md", eng + "".join(e.format(i=50 + i, o="") for i in range(13)))
        self.assertIn("FAIL people-cap", self.run_check("--gate", "2")[1])

    def test_S27_absent_answers_passes_people_cap(self):
        (self.dir / "answers.md").unlink()
        self.write("frame.md", FRAME.replace("Source: unknown", "Source: me"))
        self.assertIn("PASS people-cap", self.run_check("--gate", "2")[1])

    def test_S34_ethical_risk_passes_and_unknown_risk_fails(self):
        rows = [(ROWS[0][0], "ethical", *ROWS[0][2:]), *ROWS[1:]]
        self.write("assumptions.md", table(rows))
        self.assertIn("PASS assumption-values", self.run_check()[1])
        rows = [(ROWS[0][0], "legal", *ROWS[0][2:]), *ROWS[1:]]
        self.write("assumptions.md", table(rows))
        self.assertIn("FAIL assumption-values", self.run_check()[1])

    def test_S36_high_importance_test_needs_type_and_criterion(self):
        for bad in ("interview 5", "model", "interview:", "interview:  ", "poll: 5 of 10 say yes", ""):
            rows = [(*ROWS[0][:6], bad, ROWS[0][7]), ROWS[1], (*ROWS[2][:6], bad, ROWS[2][7]), ROWS[3]]
            self.write("assumptions.md", table(rows))
            for gate in ("1", "2"):
                code, out, _ = self.run_check("--gate", gate)
                self.assertEqual(code, 1, (bad, out))
                self.assertRegex(out, r"FAIL test-criterion.*A1, A3")
        for good in ("Interview: 3 of 5 leads", "prototype: 4 of 5 finish unaided", "survey: 20% reply",
                     "data: p50 under 2d", "spike: call returns in 1 try"):
            rows = [(*ROWS[0][:6], good, ROWS[0][7]), *ROWS[1:]]
            self.write("assumptions.md", table(rows))
            self.assertIn("PASS test-criterion", self.run_check("--gate", "1")[1])

    def test_S36_low_importance_free_text_and_decided_entry(self):
        rows = [*ROWS[:3], (*ROWS[3][:6], "just try it", ""),
                ("A5", "value", "Nice", "med", "low", "decider", "ask around", "")]
        self.write("assumptions.md", table(rows))
        self.assertIn("PASS test-criterion", self.run_check("--gate", "1")[1])
        self.idea(entry="decided")
        rows = [(*ROWS[0][:6], "free text", ROWS[0][7]), *ROWS[1:]]
        self.write("assumptions.md", table(rows))
        self.assertRegex(self.run_check("--gate", "2")[1], r"FAIL test-criterion.*A1")

    # --- frame-terms ---
    def terms(self, *rows, head="| term | meaning | link |\n|---|---|---|\n"):
        body = head + "".join(f"| {r} |\n" for r in rows)
        self.write("frame.md", FRAME.split("## Terms")[0] + "## Terms\n" + body)

    def terms_out(self, *rows, gate="1"):
        self.terms(*rows)
        return self.run_check("--gate", gate)

    def vault(self, *notes):
        (self.root / ".obsidian").mkdir(exist_ok=True)
        for n in notes:
            f = self.root / n
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("x\n")

    def test_S1_frame_without_terms_section_fails(self):
        self.write("frame.md", FRAME.split("## Terms")[0])
        for gate in ("1", "2"):
            code, out, _ = self.run_check("--gate", gate)
            self.assertEqual(code, 1)
            self.assertIn("FAIL frame-terms: no ## Terms", out)

    def test_S2_empty_meaning_fails_and_names_term(self):
        code, out, _ = self.terms_out("Sync date |  | https://x.io", "Ok | fine | ")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"FAIL frame-terms: Sync date")
        self.assertNotIn("Ok", out.split("frame-terms")[1].splitlines()[0])

    def test_S2_header_only_table_and_empty_link_pass(self):
        self.assertIn("PASS frame-terms", self.terms_out()[1])
        self.assertIn("PASS frame-terms", self.terms_out("Ok | fine | ")[1])

    def test_S3_wikilink_forms_pass_with_one_match(self):
        self.vault("sub/note.md")
        rows = ["A | m | [[note]]", r"B | m | [[note\|alias]]", "C | m | [[note#h]]"]
        self.assertIn("PASS frame-terms", self.terms_out(*rows)[1])
        self.assertEqual(self.app.link_problem("[[note|alias]]", self.dir), "")  # a raw pipe cannot sit in a table cell

    def test_S3_wikilink_zero_or_many_matches_fails(self):
        self.vault("a/note.md", "b/note.md")
        out = self.terms_out("Two | m | [[note]]", "None | m | [[ghost]]")[1]
        self.assertRegex(out, r"FAIL frame-terms: Two.*2.*; None.*0")

    def test_S3_wikilink_skips_trash_and_git(self):
        self.vault("a/note.md", ".trash/note.md", ".git/note.md")
        self.assertIn("PASS frame-terms", self.terms_out("A | m | [[note]]")[1])

    def test_S4_path_links_with_line(self):
        f = self.root / "src.py"
        f.write_text("a\nb\nc\n")
        ok = self.terms_out(f"A | m | {f}", f"B | m | {f}:3")[1]
        self.assertIn("PASS frame-terms", ok)
        out = self.terms_out(f"Far | m | {f}:4", f"Gone | m | {self.root}/nope.py")[1]
        self.assertRegex(out, r"FAIL frame-terms: Far.*; Gone")

    def test_S4_tilde_path_expands_home(self):
        (self.root / "n.txt").write_text("a\n")
        with mock.patch.dict(os.environ, {"HOME": str(self.root)}):
            self.assertIn("PASS frame-terms", self.terms_out("A | m | ~/n.txt:1")[1])

    def test_S4_line_zero_fails(self):
        (self.root / "n.txt").write_text("a\n")
        self.assertRegex(self.terms_out(f"Z | m | {self.root}/n.txt:0")[1], r"FAIL frame-terms: Z")

    def test_S4_unreadable_file_fails_without_crash(self):
        f = self.root / "n.txt"
        f.write_text("a\n")
        f.chmod(0)
        self.addCleanup(f.chmod, 0o600)
        self.assertRegex(self.terms_out(f"U | m | {f}:1")[1], r"FAIL frame-terms: U: cannot read")

    def test_S3_wikilink_is_case_insensitive_and_strips_md(self):
        self.vault("Sub/My Note.md")
        self.assertIn("PASS frame-terms", self.terms_out("A | m | [[my note]]", "B | m | [[MY NOTE.md]]")[1])

    def test_S3_wikilink_skips_every_dot_folder(self):
        self.vault(".hidden/note.md", "sub/note.md")
        self.assertIn("PASS frame-terms", self.terms_out("A | m | [[note]]")[1])

    def test_S1_prose_or_wrong_header_fails(self):
        for body in ("just words\n", "| name | definition | url |\n|---|---|---|\n| a | b | c |\n",
                     "| Term | Definition | Link |\n|---|---|---|\n| a | b | |\n"):
            self.write("frame.md", FRAME.split("## Terms")[0] + "## Terms\n" + body)
            self.assertIn("FAIL frame-terms: no term | meaning | link table", self.run_check("--gate", "1")[1])

    def test_S5_https_accepted_without_network(self):
        self.assertIn("PASS frame-terms", self.terms_out("A | m | https://unreachable.invalid/x")[1])

    def test_S6_two_links_in_one_cell_fail(self):
        out = self.terms_out("Two | m | https://a.io https://b.io")[1]
        self.assertRegex(out, r"FAIL frame-terms: Two: write as https URL, ~/path or \[\[note\]\]")

    def test_S6_other_link_forms_fail_with_hint(self):
        out = self.terms_out("Tick | m | H-8118", "Sha | m | f355ab6", "Rel | m | packages/x.ts")[1]
        line = [l for l in out.splitlines() if "frame-terms" in l][0]
        self.assertTrue(line.startswith("FAIL"), line)
        for t in ("Tick", "Sha", "Rel"):
            self.assertIn(t, line)
        self.assertEqual(line.count("write as https URL, ~/path or [[note]]"), 3)

    def test_S7_wikilink_without_vault_root_fails(self):
        out = self.terms_out("Note | m | [[note]]")[1]
        self.assertRegex(out, r"FAIL frame-terms: Note.*no vault root")

    def test_S13_docstring_documents_frame_terms(self):
        doc = self.app.__doc__
        for s in ("frame-terms", "## Terms", "https://", "~/", "[[note]]"):
            self.assertIn(s, doc)

    # --- frame-language ---
    def language(self, *lines):
        self.write("gates.md", GATES.split("- 2026-10-26 language")[0] + "".join(l + "\n" for l in lines))

    def test_S8_no_language_line_fails_and_prints_current_sha(self):
        self.language()
        for gate in ("1", "2"):
            code, out, _ = self.run_check("--gate", gate)
            self.assertEqual(code, 1)
            self.assertIn(f"FAIL frame-language: no pass for frame {sha12(FRAME)}", out)

    def test_S9_matching_latest_pass_passes(self):
        self.language("- 2026-10-01 language: pass aaaaaaaaaaaa", f"* 2026-10-02 language: pass {sha12(FRAME)}")
        self.assertIn("PASS frame-language", self.run_check("--gate", "1")[1])

    def test_S9_only_the_latest_language_line_counts(self):
        self.language(f"- 2026-10-01 language: pass {sha12(FRAME)}", "- 2026-10-02 language: pass aaaaaaaaaaaa")
        self.assertIn("FAIL frame-language", self.run_check("--gate", "1")[1])

    def test_S9_changed_frame_body_fails_with_new_sha(self):
        new = FRAME + "## Q4 Who pays?\nSource: me\n"
        self.write("frame.md", new)
        out = self.run_check("--gate", "1")[1]
        self.assertIn(f"FAIL frame-language: no pass for frame {sha12(new)}", out)

    def test_S10_frontmatter_only_change_still_passes(self):
        self.write("frame.md", "---\ntype: note\nupdated: 2026-11-02\n---\n" + FRAME)
        self.assertIn("PASS frame-language", self.run_check("--gate", "2")[1])

    def test_S11_decided_skips_both_and_raw_runs_both(self):
        self.idea(entry="decided")
        out = self.run_check("--gate", "2")[1]
        for name in ("frame-terms", "frame-language"):
            self.assertIn(f"SKIPPED {name}", out)
        self.idea(entry="raw")
        out = self.run_check("--gate", "2")[1]
        for name in ("frame-terms", "frame-language"):
            self.assertIn(f"PASS {name}", out)

    def test_S8_missing_gates_file_fails_and_prints_sha(self):
        (self.dir / "gates.md").unlink()
        self.assertIn(f"FAIL frame-language: gates.md missing; frame {sha12(FRAME)}", self.run_check("--gate", "1")[1])

    def test_S9_pass_detail_names_the_frame_sha(self):
        self.assertIn(f"PASS frame-language: frame {sha12(FRAME)}\n", self.run_check("--gate", "1")[1])

    def test_S9_newer_non_pass_or_placeholder_line_overrides_a_pass(self):
        good = f"- 2026-10-01 language: pass {sha12(FRAME)}"
        for newer in ("- 2026-10-02 language: blocked", "- 2026-10-02 language: pass <sha12>",
                      "- 2026-10-02 language: pass abc"):
            self.language(good, newer)
            self.assertIn("FAIL frame-language", self.run_check("--gate", "1")[1], newer)

    def test_S10_whitespace_and_empty_frontmatter_do_not_change_the_sha(self):
        for text in (FRAME + "\n\n", "---\ntype: note\n---\n\n" + FRAME, "---\n---\n" + FRAME,
                     "---\ntype: note\n---\n" + FRAME + "  \n"):
            self.write("frame.md", text)
            self.assertIn("PASS frame-language", self.run_check("--gate", "1")[1], repr(text[:30]))


if __name__ == "__main__":
    unittest.main()
