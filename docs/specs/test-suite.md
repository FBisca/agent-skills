# Test-Suite

Paths: scripts/, tests/, conftest.py, pyproject.toml, skills/idea-frame/, skills/idea-answer/, skills/start-planning/, AGENTS.md, README.md

What the test suite guarantees: a fast unit suite that runs offline, fails loudly instead of hanging, and tests machine-read contracts rather than prose. This is the living spec of the test-suite plan, `docs/plans/2026-11-09-test-suite.plan.md`.

- **R1** Retired: the converge gate and its plan reader are removed; the engine's `plan check` reads a plan. (from test-suite/S20; retired by yaml-eec/S26)
- **R2** WHEN the engine reads a plan, THEN the ticket table carries the nine header names it requires (`#`, `What it delivers`, `Satisfies`, `Blocked by`, `Paths`, `Size`, `Difficulty`, `Owner`, `Status`) with `Status` last, the head carries a backticked `Slug:` and an unbolded `Status: APPROVED`, and `Size`/`Difficulty` are the engine's vocabulary (`small|regular`, `simple|complex`). (from test-suite/S21)
- **R3** WHEN the idea skills document a vocabulary the gate enforces (the stages, the assumption columns, the answer entry fields, the test types, the result values), THEN that vocabulary is exactly the script's, in both directions: the script knows no value the document omits, and the document names no value the script rejects. (from test-suite/S22)
- **R4** WHEN a skill's frontmatter carries each defect the lint names, THEN the lint refuses it with the message it names, and every refusal it can produce is asserted by a test. (from test-suite/S23)
- **R5** WHEN the lint runs over a folder of skills, THEN it exits 1 when it finds problems, 2 when the path is not a directory, and 0 when the skills are clean. (from test-suite/S24)
- **R6** WHEN a test file hangs, THEN the runner names that file, exits non-zero, and the run ends within `TEST_TIMEOUT`. (from test-suite/S25)
- **R7** WHEN `VAULT_DIR` is unset or is not a directory, THEN `idea_check.py` and `excali.vault_dir()` exit 3 and name `VAULT_DIR` in the message. (from test-suite/S26)
- **R8** WHEN the unit suite runs on a fresh clone, THEN it finishes in under 3 seconds, and a run that takes longer fails and says so. (from test-suite/S27)
- **R9** WHEN the suite ends, THEN no temporary directory it created is left behind. (from test-suite/S28)
- **R10** WHEN a test is skipped, THEN the run reports it as skipped, with the reason that names the missing dependency, and a skipped `unit` test fails the run. (from test-suite/S29)
- **R11** WHEN a check compares a date against today, THEN the date is injected, so the result does not change when the run crosses midnight. (from test-suite/S30)
- **R12** WHEN the marker text and the suite are read together, THEN `unit` means in-process and inside the test's own temporary directory, `integration` means a real boundary, and every test that guards pure logic carries `unit` and sits in the fast suite. (from test-suite/S31)
- **R13** WHEN a skill hardcodes a skill path, carries an invocation syntax, holds an absolute user path or is a symlink, THEN the lint names the file and the line. (from test-suite/S32)
- **R14** WHEN a reader asks which skills have executable behaviour, THEN the repository names the ones that have none, and states that a Markdown document is not a test. (from test-suite/S33)
- **R15** WHEN the frontmatter of every skill in this repository is linted, THEN each skill's name matches its folder and its description is text, one test over all skills, not one per skill. (from test-suite/S34)
- **R16** WHEN Pi discovers the skills of this repository, THEN every skill is discovered and reports no problem, one test over all skills. (from test-suite/S35)
- **R17** WHEN the suite runner is handed a root that is not a directory, or a directory that holds no test file, THEN it refuses and names what it was given instead of reporting a green run of zero files. (from test-suite/S36)
- **R18** WHEN the idea gate's suite loads the gate script, THEN the script runs once for the whole module and every test cleans up the temporary directory it made, so the suite's cost is the tests and not the setup. (from test-suite/S37)
