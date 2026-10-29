"""idea_check.py against throwaway idea folders; scenario IDs name the tests."""

import contextlib
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
## Q3 Is there data?
Source: lookup https://example.com/x
"""
ROWS = [
    ("A1", "value", "Clients want it (Q2)", "high", "low", "operator/user", "interview 5", "confirmed"),
    ("A2", "feasibility", "API exists", "high", "med", "engineering", "spike", "accepted by decider"),
    ("A3", "viability", "Cost fits", "high", "low", "finance", "model", "ok"),
    ("A4", "usability", "Easy", "low", "low", "decider", "", ""),
]
PREMORTEM = "# Pre-mortem\n- Nobody uses it → PRD: adoption plan\n- Cost blows up → A3\n"
ANSWERS = "## Q2\nOwner: finance\nDate: 2026-10-20\nSummary: costs ok\nLink: https://example.com/a\n"
GATES = (
    "- 2026-10-10 gate1: continue: top 3 ready\n"
    "- 2026-10-25 gate2: pass by CFO: all closed\n"
)
HOURS = "- 2026-10-01 framing 2h\n- 2026-10-05 gate1 1h\n- 2026-10-10 answering 3h\n- 2026-10-20 gate2 1h"


def table(rows):
    head = "| id | risk | assumption | importance | evidence | owner | test | result |\n|---|---|---|---|---|---|---|---|\n"
    return head + "".join("| " + " | ".join(r) + " |\n" for r in rows)


class IdeaCheckTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
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
        for name in ("frame-sources", "unknown-to-assumption", "top3-ready", "premortem-links"):
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
        self.assertEqual(len(names), 11)

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


if __name__ == "__main__":
    unittest.main()
