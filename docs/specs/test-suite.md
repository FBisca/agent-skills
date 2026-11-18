# Test-Suite

Paths: scripts/, tests/, conftest.py, pyproject.toml, skills/idea-frame/, skills/idea-answer/, skills/start-planning/, AGENTS.md, README.md

What the test suite guarantees: a fast unit suite that runs offline, fails loudly instead of hanging, and tests machine-read contracts rather than prose. This is the living spec of the test-suite plan, `docs/plans/2026-11-09-test-suite.plan.md`.

## Requirements

### Requirement: Plan ticket table contract
A plan the engine reads SHALL carry the nine ticket-table headers it requires (`#`, `What it delivers`, `Satisfies`, `Blocked by`, `Paths`, `Size`, `Difficulty`, `Owner`, `Status`) with `Status` last, a backticked `Slug:` and an unbolded `Status: APPROVED` in its head, and the engine's `Size`/`Difficulty` vocabulary (`small|regular`, `simple|complex`).

#### Scenario: the engine reads a plan
- WHEN the engine reads a plan
- THEN the ticket table carries the nine header names it requires (`#`, `What it delivers`, `Satisfies`, `Blocked by`, `Paths`, `Size`, `Difficulty`, `Owner`, `Status`) with `Status` last, the head carries a backticked `Slug:` and an unbolded `Status: APPROVED`, and `Size`/`Difficulty` are the engine's vocabulary (`small|regular`, `simple|complex`)

### Requirement: Idea vocabulary matches the gate
A vocabulary the idea skills document and the gate enforces SHALL be exactly the script's, in both directions.

#### Scenario: the idea skills document a vocabulary the gate enforces
- WHEN the idea skills document a vocabulary the gate enforces (the stages, the assumption columns, the answer entry fields, the test types, the result values)
- THEN that vocabulary is exactly the script's, in both directions: the script knows no value the document omits, and the document names no value the script rejects

### Requirement: Lint refuses each named defect
The lint SHALL refuse each frontmatter defect it names with the message it names, and every refusal it can produce SHALL be asserted by a test.

#### Scenario: a skill's frontmatter carries each defect the lint names
- WHEN a skill's frontmatter carries each defect the lint names
- THEN the lint refuses it with the message it names, and every refusal it can produce is asserted by a test

### Requirement: Lint exit codes
The lint SHALL exit 1 when it finds problems, 2 when the path is not a directory, and 0 when the skills are clean.

#### Scenario: the lint runs over a folder of skills
- WHEN the lint runs over a folder of skills
- THEN it exits 1 when it finds problems, 2 when the path is not a directory, and 0 when the skills are clean

### Requirement: A hanging test file is named
The runner SHALL name a test file that hangs, exit non-zero, and end the run within `TEST_TIMEOUT`.

#### Scenario: a test file hangs
- WHEN a test file hangs
- THEN the runner names that file, exits non-zero, and the run ends within `TEST_TIMEOUT`

### Requirement: A missing VAULT_DIR exits 3
`idea_check.py` and `excali.vault_dir()` SHALL exit 3 and name `VAULT_DIR` when it is unset or not a directory.

#### Scenario: `VAULT_DIR` is unset or is not a directory
- WHEN `VAULT_DIR` is unset or is not a directory
- THEN `idea_check.py` and `excali.vault_dir()` exit 3 and name `VAULT_DIR` in the message

### Requirement: Fast suite budget
The unit suite SHALL finish in under 3 seconds on a fresh clone, and a run that takes longer SHALL fail and say so.

#### Scenario: the unit suite runs on a fresh clone
- WHEN the unit suite runs on a fresh clone
- THEN it finishes in under 3 seconds, and a run that takes longer fails and says so

### Requirement: No temporary entry left behind
The suite SHALL leave behind no temporary directory it created.

#### Scenario: the suite ends
- WHEN the suite ends
- THEN no temporary directory it created is left behind

### Requirement: Skips are reported and unit skips fail
The run SHALL report every skip with the reason that names the missing dependency, and a skipped `unit` test SHALL fail the run.

#### Scenario: a test is skipped
- WHEN a test is skipped
- THEN the run reports it as skipped, with the reason that names the missing dependency, and a skipped `unit` test fails the run

### Requirement: Dates are injected
A check that compares a date against today SHALL take the date injected, so its result does not change when the run crosses midnight.

#### Scenario: a check compares a date against today
- WHEN a check compares a date against today
- THEN the date is injected, so the result does not change when the run crosses midnight

### Requirement: Unit and integration markers
`unit` SHALL mean in-process and inside the test's own temporary directory, `integration` SHALL mean a real boundary, and every test that guards pure logic SHALL carry `unit` and sit in the fast suite.

#### Scenario: the marker text and the suite are read together
- WHEN the marker text and the suite are read together
- THEN `unit` means in-process and inside the test's own temporary directory, `integration` means a real boundary, and every test that guards pure logic carries `unit` and sits in the fast suite

### Requirement: Lint names skill hygiene defects
The lint SHALL name the file and the line of a skill that hardcodes a skill path, carries an invocation syntax, holds an absolute user path or is a symlink.

#### Scenario: a skill hardcodes a skill path, carries an invocation syntax, holds an absolute user path or is a symlink
- WHEN a skill hardcodes a skill path, carries an invocation syntax, holds an absolute user path or is a symlink
- THEN the lint names the file and the line

### Requirement: Skills without executable behaviour are named
The repository SHALL name the skills that have no executable behaviour and state that a Markdown document is not a test.

#### Scenario: a reader asks which skills have executable behaviour
- WHEN a reader asks which skills have executable behaviour
- THEN the repository names the ones that have none, and states that a Markdown document is not a test

### Requirement: One frontmatter test over all skills
One test over all skills SHALL check that each skill's name matches its folder and its description is text.

#### Scenario: the frontmatter of every skill in this repository is linted
- WHEN the frontmatter of every skill in this repository is linted
- THEN each skill's name matches its folder and its description is text, one test over all skills, not one per skill

### Requirement: Pi discovers every skill
Pi SHALL discover every skill of this repository with no problem reported, checked by one test over all skills.

#### Scenario: Pi discovers the skills of this repository
- WHEN Pi discovers the skills of this repository
- THEN every skill is discovered and reports no problem, one test over all skills

### Requirement: The runner refuses an empty root
The suite runner SHALL refuse a root that is not a directory, or a directory that holds no test file, and name what it was given.

#### Scenario: the suite runner is handed a root that is not a directory, or a directory that holds no test file
- WHEN the suite runner is handed a root that is not a directory, or a directory that holds no test file
- THEN it refuses and names what it was given instead of reporting a green run of zero files

### Requirement: The idea gate suite loads the script once
The idea gate's suite SHALL run the gate script once per module, and every test SHALL clean up the temporary directory it made.

#### Scenario: the idea gate's suite loads the gate script
- WHEN the idea gate's suite loads the gate script
- THEN the script runs once for the whole module and every test cleans up the temporary directory it made, so the suite's cost is the tests and not the setup
