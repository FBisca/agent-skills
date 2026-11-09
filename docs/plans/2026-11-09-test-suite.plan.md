# Plan: the test suite earns its keep

Slug: `test-suite`. Living spec: `docs/specs/test-suite.md`. Status: APPROVED 2026-11-09.

## Why now

The request: this repository carries a lot of low-value skills, and its test suite should be judged by the rubric at
`skills/score-agent/rubrics/test-value.md`. The example the request gives is the smell itself: *"I see no value in
adding tests that test markdown."*

A fresh-context gatherer read the rubric, `AGENTS.md`, the two living specs, all 14 test files and the 6 production
scripts, and measured the suite. What it found:

- 212 tests in 14 files. **58 read a Markdown document**; 26 of those guard a machine-read contract (the frontmatter
  lint, Pi's own loader, the plan format) and **32 assert prose** — a sentence, a heading, a line count, a banned word,
  one verbatim 15-sentence block. 27 of the 32 are `unit`.
- **7 tests are provably redundant** — each one already covered by a broader test that stays (100% retained confidence
  if they are removed).
- The full suite takes 17.92 s, and `skills/converge/tests/test_converge.py` is 15.24 s of it (85%). Eight of its
  tests guard pure functions yet pay a git-repository fixture, so they are excluded from the fast suite for no boundary
  reason. Eighteen of the 19 `fresh_context` tests run in process yet are marked `integration`.
- The fast suite takes **3.90 s cold** (0.66–0.90 s warm) against the "under 3 seconds" that `AGENTS.md` L17 and
  `README.md` L116 promise. One line causes it: `test_idea_check.py` re-executes the gate script for each of its 52
  tests.
- The lint the gate depends on has **28 refusal sites and 7 refusal tests**. `scripts/run-tests.py`, `scripts/checks.sh`
  and `scripts/install-upstream.sh` have no test at all, although `AGENTS.md` L26-28 promises that the runner "names
  the file that never finished".
- Ten of the sixteen skills have no `tests/` folder. `cold-read` and `idea-answer` hold **only** Markdown tests and have
  no scripts, and `README.md` L7 lists them as skills with "gate and orchestration scripts".

So the suite is not short of tests; it is short of *distinct* guarantees. The plan below cuts the prose, keeps every
machine-read contract, moves each test to the level its behaviour has, and adds the behaviour the repository's own
documents already promise.

## Sources

| Source | What it settles |
|---|---|
| The request (the user) | The goal: raise the suite's test value against the rubric; the example of worthlessness is a test that asserts Markdown. The scope answer: the suite only, no skill is removed or merged. |
| `skills/score-agent/rubrics/test-value.md` | The criteria (behavioural uniqueness, level selection, duplication and ownership, implementation coupling, execution cost, coverage sufficiency, determinism and isolation, proportionality), the anchors 1.0/0.8/0.4/0.2, and the rule that overlap at different real boundaries is not redundancy. |
| `AGENTS.md` L7-11 | Unit is in-process, isolated and deterministic; integration drives a real boundary; classify by behaviour, never weaken or reclassify a test to go faster. |
| `AGENTS.md` L17, L24-28 | The fast suite is under 3 seconds; `scripts/checks.sh` is the gate CI runs; `run-tests.sh` names the file that never finished. |
| `AGENTS.md` L30-39 | The frontmatter lint's guarantees, and that the lint is stdlib-only so it runs on a bare Python. |
| `pyproject.toml`, `conftest.py` | The two markers, the strict-marker and import-mode flags, and the partition: every test carries exactly one marker, or collection fails. |
| `docs/specs/harness-portability.md` R1-R4 | The offline suite must enforce skill discovery, the plan Markdown contract and the portability contracts. R2 and R3 are enforced today **only** by prose assertions — those tests stay. |
| `docs/specs/orchestrator-single-engine.md` R5 | The documents must name the seam, the order and the way out — enforced today by one prose test, which stays. |
| `docs/workflow.md` steps 7-9 | Every scenario becomes a test that fails first; `converge` checks every scenario has a test and every changed test carries an ID; at archive the scenarios become the living spec's requirements and the tests are renamed to them. |
| `skills/converge/scripts/converge.py` | The plan reader the gate uses: `plan_data(text)` and `refusal(text)` are importable seams; `has_id` matches a scenario to a test by the ID in the test's name; the `scope` check fences every changed file to a ticket's `Paths`. |
| `agent-runtime/packages/agent-orchestrator/driver.py` (the engine, read read-only) | The plan is machine-read: the ticket table must carry the nine header names exactly, `Status` must be the last column, `Status:` must read `APPROVED` unbolded, `Slug:` must be backticked, `Size` is `small|regular` (the engine refuses `big`), and `WHEN`/`THEN` is never matched. |
| The gatherer's report (fresh context, read-only) | The counts, the timings, the 58/26/32 split, the 7 redundant tests, the level errors, the coverage gaps, the 10 skills without a suite and the 6 with only prose coverage. |
| `README.md` L7, L116 | Which skills claim a script suite they do not have, and the fast-suite budget. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | The plan rewrites the suite; no skill is removed, merged or renamed. | The plan also proposes removing the "useless skills". | One plan carries one size of change, and "useless skill" has no testable definition here. The skill list is a product call, planned on its own. | Grill Q1 |
| D2 | Rebalance: delete the prose tests, move the misplaced ones to the level their behaviour has, and add the behaviour tests the repository's own documents promise. | Delete only (leaves `AGENTS.md`'s and `README.md`'s promises untested) / grow only (keeps the 32 prose tests). | The rubric scores coverage sufficiency next to redundancy; one alone leaves half the problem standing. | Grill Q2 |
| D3 | Keep the 8 prose tests a living spec names — `harness-portability` R2/R3 and `orchestrator-single-engine` R5 — and delete the other 24. No spec is amended. | Delete all 32 and amend the two specs / keep all 32. | The specs' requirements are the contract; the sentences are not. Amending a spec to drop a requirement is a product decision this plan does not make. | Grill Q3 |
| D4 | A test that writes inside its own temporary directory is `unit`; one that touches the filesystem outside it is `integration`. The marker text in `pyproject.toml` and `AGENTS.md` says so. | "The filesystem is always a boundary" (`pyproject.toml`'s current text) / "the filesystem is never a boundary". | 64 `unit` tests write temp files today; either the marker text or 64 classifications is wrong. The temp directory is isolation, not a boundary. | Grill Q4 |
| D5 | The Pi discovery tests stay, and the gate reports them as skipped, with a reason, never as passed. | Install Pi in CI / drop them. | A silently skipped gate test is a false green; the frontmatter lint does not prove a harness can see the skill. | Grill Q5 |
| D6 | `scripts/checks.sh` is the gate; `scripts/run-tests.sh` is the diagnostic that names a hanging file. | `run-tests.sh` is the gate. | `checks.sh` is what CI runs and it lints; the runner is the tool for a wedged suite. | Grill Q6 |
| D7 | The plan-format checks stay and are made real: `converge.py`'s own reader parses every tracked plan, and the engine's nine columns are asserted by name. The SKILL.md format checks become a two-way vocabulary check against `idea_check.py`. | Keep all 11 as they are / delete all 11. | The engine reads the ticket table and the plan head; the wording of the same table does not matter. The current checks freeze sentences and do not detect the parser drifting from the document. | Grill Q7; `driver.py` 445-455, 492-499, 580-587 |
| D8 | The fast-suite budget is measured cold: a fresh clone finishes the unit suite in under 3 seconds, and the run fails when it does not. | Warm. | The promise sits next to "the fast suite (the unit tests): under 3 seconds", and a cold run is what CI and a new clone see. Today it is 3.90 s cold. | Grill Q8; `AGENTS.md` L17 |
| D9 | The mechanical hygiene rules become lint problems that name the file and the line; the "a skill names roles, never people" rule becomes a written rule. | Keep them as tests / delete them outright. | A lint failure names the file and the line; a test failure names a test. A person-name rule needs a name list, so it is a rule, not a machine check. | Grill Q9 |
| D10 | The engine is authoritative for the ticket vocabulary: `Size` is `small|regular` and `Difficulty` is `simple|complex`, and `skills/start-planning/SKILL.md` drops `big`. | The skill is authoritative and the engine changes in the other repository. | The engine is the machine that refuses the plan; a documented value the engine rejects is a trap, and this repository owns the document. | Grill Q10; `driver.py` 614-628 |
| D11 | The repository names the skills whose behaviour is prose only, so nobody later writes a Markdown test for them. | Say nothing. | One sentence closes the door on the exact waste the request complains about. | Grill Q11 |
| D12 | The scenario IDs start at S20. | S1, S2, S3… | `S1`-`S19` and `S32`-`S48` are already carried by test names from archived plans, and `converge` matches a scenario to a test by the ID in the test's name — a colliding ID would be "covered" by an unrelated old test. | `converge.py` 67 (`has_id`); the test names in the tree |
| D13 | The living spec of this area is `docs/specs/test-suite.md`, written at archive. | A ticket writes it now. | `docs/workflow.md` step 9 gives the archive that job, and the engine's archive worker is told to create the file if it is missing. | `docs/workflow.md` step 9; `driver.py` 3402-3405 |
| D14 | The deletion of the 24 prose tests and the 5 duplicated tests keeps every guarantee they carried: the machine-read contract each duplicate already had is asserted by the broader test that stays. | Deleting a test and accepting the loss. | The rubric asks for the overlap **and the retained confidence** to be shown, not assumed. Every deletion below names the test that keeps the guarantee. | `test-value.md` § Required evidence |
| D15 | The 3-second budget is enforced by the run's own session hook (T11); no test asserts a wall-clock time. T8 delivers and proves the *cause* instead: one script execution per module and no leftover temp directory (S37). | A test that spawns the cold unit suite and asserts `elapsed < 3` . | A wall-clock assertion fails on a loaded machine (T8 measured 2.7 s at load average ~18) — a flaky test is exactly what this plan removes. The hook fails the real run on the real machine, once, and names the budget. | Grill Q8; T8's report; `test-value.md` § Determinism |

## Scenarios

- **S20** WHEN every tracked plan is read by the plan reader the gate uses, THEN each plan yields its scenario ids and
  its ticket rows, and a plan whose Tickets table is missing or has no rows is refused.
- **S21** WHEN the engine reads a plan, THEN the ticket table carries the nine header names it requires (`#`, `What it
  delivers`, `Satisfies`, `Blocked by`, `Paths`, `Size`, `Difficulty`, `Owner`, `Status`) with `Status` last, the head
  carries a backticked `Slug:` and an unbolded `Status: APPROVED`, and `Size`/`Difficulty` are the engine's vocabulary
  (`small|regular`, `simple|complex`).
- **S22** WHEN the idea skills document a vocabulary the gate enforces — the stages, the assumption columns, the answer
  entry fields, the test types, the result values — THEN that vocabulary is exactly the script's, in both directions: the
  script knows no value the document omits, and the document names no value the script rejects.
- **S23** WHEN a skill's frontmatter carries each defect the lint names, THEN the lint refuses it with the message it
  names, and every refusal it can produce is asserted by a test.
- **S24** WHEN the lint runs over a folder of skills, THEN it exits 1 when it finds problems, 2 when the path is not a
  directory, and 0 when the skills are clean.
- **S25** WHEN a test file hangs, THEN the runner names that file, exits non-zero, and the run ends within
  `TEST_TIMEOUT`.
- **S26** WHEN `VAULT_DIR` is unset or is not a directory, THEN `idea_check.py` and `excali.vault_dir()` exit 3 and name
  `VAULT_DIR` in the message.
- **S27** WHEN the unit suite runs on a fresh clone, THEN it finishes in under 3 seconds, and a run that takes longer
  fails and says so.
- **S28** WHEN the suite ends, THEN no temporary directory it created is left behind.
- **S29** WHEN a test is skipped, THEN the run reports it as skipped, with the reason that names the missing dependency,
  and a skipped `unit` test fails the run.
- **S30** WHEN a check compares a date against today, THEN the date is injected, so the result does not change when the
  run crosses midnight.
- **S31** WHEN the marker text and the suite are read together, THEN `unit` means in-process and inside the test's own
  temporary directory, `integration` means a real boundary, and every test that guards pure logic carries `unit` and
  sits in the fast suite.
- **S32** WHEN a skill hardcodes a skill path, carries an invocation syntax, holds an absolute user path or is a
  symlink, THEN the lint names the file and the line.
- **S33** WHEN a reader asks which skills have executable behaviour, THEN the repository names the ones that have none,
  and states that a Markdown document is not a test.
- **S34** WHEN the frontmatter of every skill in this repository is linted, THEN each skill's name matches its folder
  and its description is text — one test over all skills, not one per skill.
- **S35** WHEN Pi discovers the skills of this repository, THEN every skill is discovered and reports no problem — one
  test over all skills.
- **S36** WHEN the suite runner is handed a root that is not a directory, or a directory that holds no test file,
  THEN it refuses and names what it was given instead of reporting a green run of zero files.
- **S37** WHEN the idea gate's suite loads the gate script, THEN the script runs once for the whole module and
  every test cleans up the temporary directory it made, so the suite's cost is the tests and not the setup.

## Out of scope

- Removing, merging or renaming a skill. The request's remark about "useless skills" is a product decision; this plan
  touches the suite (D1).
- Writing the six living specs that tracked plans name but that do not exist (`docs/specs/orchestrate.md` ×3,
  `orchestration-evaluation.md` ×2, `orchestration-routing.md` ×1). No machine reads that field — the engine only uses it
  when archiving — so it is a documentation task, not a test-value task.
- `skills/excalidraw/scripts/` and `skills/explain-video/scripts/` beyond `excali.vault_dir`. `README.md` L7 states that
  these two skills are checked by their own render loops, not by unit tests.
- `scripts/install-upstream.sh`. It reaches the network; the fakes in this repository stay offline.
- The engine's own parser. It lives in `agent-runtime`; this plan aligns this repository's documents and tests with it.
- Amending `docs/specs/harness-portability.md` or `docs/specs/orchestrator-single-engine.md`. Their requirements stay, and
  the tests that enforce them stay (D3).

## Risks

- **Security:** no new network access and no new credential handling. The hygiene lint reads the repository's own files;
  the hanging-file test spawns a local `sleep`; the Pi discovery tests keep their existing "no network" behaviour. The
  lint stays stdlib-only so it runs in CI on a bare Python. Covered.
- **Performance:** the full suite grows by roughly 30 tests (the lint's refusal table, the vocabulary drift, the runner
  harness) and the hanging-file test costs about `TEST_TIMEOUT` (2 s in the test). The fast suite must stay under 3 s
  cold, which S27 enforces; `converge`'s 15.24 s stays where it is — no ticket makes it slower. Covered.
- **Migration:** 29 tests are deleted (24 prose, 5 duplicated). Each deletion names the test that keeps its guarantee,
  and no living spec is amended, so R2, R3 and R5 keep their tests. The `Size` vocabulary change in
  `skills/start-planning/SKILL.md` touches a document the engine reads; the change is the engine's own vocabulary, so
  no plan stops being accepted. Covered.
- **Rollback:** every ticket is one PR and reverts on its own. The sharpest edge is the session hook that fails a run
  over budget (S27): its limit is a constant in `conftest.py` and reverting T11 removes it without touching a test.
  Covered.

## Seams

The highest existing seam for each area; the tests attach there and nowhere else.

| Area | Seam |
|---|---|
| The frontmatter lint | `scripts/lint_skills.py` — `lint_skill(path)`, `lint_dir(directory)`, `main(argv)` (in process) |
| The plan format | `skills/converge/scripts/converge.py` — `plan_data(text)`, `refusal(text)` (in process), plus the tracked plan documents they read |
| The idea gate | `skills/idea-frame/scripts/idea_check.py` — its vocabulary constants and `run(folder, gate)`; the CLI for the exit code |
| The excalidraw vault root | `skills/excalidraw/scripts/excali.py` — `vault_dir()` |
| The suite's own runner | `scripts/run-tests.py` — `run(directory, name, timeout)` and `main()`; it needs a root parameter to be pointed at a fixture suite |
| The gate's own behaviour | `conftest.py` — the session hooks (budget, leaks, skips) and the marker partition |

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | The 24 prose tests and the 5 duplicated tests are gone. The 8 tests a living spec names stay, unchanged in what they assert. Every deleted guarantee is asserted by the broader test that stays: `test_S35_pi_discovers_every_skill_of_this_repo` keeps the Pi discovery guarantee, `test_every_skill_of_this_repo_passes_the_frontmatter_lint` keeps the frontmatter guarantee, `test_every_skill_is_discoverable_and_portable` keeps the discovery guarantee, `test_S3_the_shared_skills_keep_their_harness_contracts` keeps the harness-contract guarantee. | S35 | none | tests/test_repo.py, tests/test_portability.py, tests/test_pi_discovery.py, skills/cold-read/tests/test_skill_contract.py, skills/idea-answer/tests/test_skill_contract.py, skills/idea-frame/tests/test_skill_contract.py, skills/start-planning/tests/test_portability.py | regular | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/56 (2a2e354) |
| T2 | Every tracked plan is read by `converge.py`'s own reader, and the engine's contract is asserted by name: the nine ticket columns with `Status` last, the backticked `Slug:`, the unbolded `Status: APPROVED`, `Size` in `small` or `regular` and `Difficulty` in `simple` or `complex`. `skills/start-planning/SKILL.md` drops `big` from the documented vocabulary. | S20, S21 | T1 | tests/test_portability.py, skills/start-planning/tests/test_portability.py, skills/start-planning/SKILL.md, skills/converge/scripts/converge.py | regular | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/58 (4ba133a) |
| T3 | The idea gate's contract is machine-checkable: `idea_check.py` names its answer-entry fields as a constant and takes the current date from `IDEA_CHECK_TODAY` when it is set; a new test compares the vocabulary the two skills document against the script's, in both directions, and another injects a fixed date. | S22, S30 | none | skills/idea-frame/scripts/idea_check.py, skills/idea-frame/SKILL.md, skills/idea-answer/SKILL.md, skills/idea-answer/prep.md, skills/idea-frame/tests/test_idea_check.py, tests/test_idea_vocabulary.py | regular | complex | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/57 (5d9aeb0) |
| T4 | The lint refuses every defect it names — the untested refusals (unclosed quote, undefined escape, text after the closing quote, the five flow-value errors, the reserved and structure starts, the tab, the malformed line, the missing or unclosed frontmatter, the empty name, the over-long description, the block scalar) — and its exit codes are asserted: 1 for problems, 2 for a path that is not a directory, 0 for a clean folder. | S23, S24, S34 | none | scripts/lint_skills.py, tests/test_skill_frontmatter.py | regular | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/59 (2f28d1b) |
| T5 | The hygiene rules are lint problems that name the file and the line: a hardcoded skill path, an invocation syntax, an absolute user path, a symlink, and a copied skill whose NOTICE does not name its upstream and licence. The three "names no person" tests go, and `AGENTS.md` states the rule instead. | S32 | T4 | scripts/lint_skills.py, tests/test_skill_frontmatter.py, tests/test_repo.py, tests/test_portability.py, AGENTS.md | regular | simple | agent | TO-DO |
| T6 | The runner names the file that hangs: `run-tests.py` takes the root it walks, and a test points it at a fixture suite with one fast file and one that sleeps, then asserts the hanging file is named, the exit code is non-zero, and the run ends inside `TEST_TIMEOUT`. | S25 | none | scripts/run-tests.py, tests/test_run_tests.py | small | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/60 (db3cc11) |
| T7 | The vault root is named when it is unset: the `VAULT_DIR` tests assert exit code 3 exactly, for `idea_check.py` and for `excali.vault_dir()`, instead of "some non-zero code". | S26 | T1 | tests/test_repo.py | small | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/61 (0bb04b3) |
| T8 | The fast suite is fast for a stated reason: the gate script runs once per module instead of once per test, and every test cleans up the temporary directory it makes, with a test that holds both (S37). The 3-second budget itself is enforced by T11's session hook. | S37 | none | skills/idea-frame/tests/test_idea_check.py, tests/test_skill_frontmatter.py, skills/start-planning/tests/test_check_deps.py | small | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/62 (525ddd8) |
| T9 | The pure-logic `converge` tests leave the git fixture: the eight that guard `names_in`, `has_id` and `is_test_file` run without a repository, carry `unit`, and sit in the fast suite with every assertion they made. | S31 | none | skills/converge/tests/test_converge.py | regular | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/63 (de47c92) |
| T10 | The in-process tests carry `unit` and the marker text says what that means: the eighteen `fresh_context` tests that use the in-process seam and the six `tests/test_portability.py` tests that only read files are re-marked, and `pyproject.toml` and `AGENTS.md` say that a temporary directory is not a boundary. | S31 | T2 | skills/start-planning/tests/test_fresh_context.py, tests/test_portability.py, pyproject.toml, AGENTS.md | regular | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/64 (26d5af4) |
| T11 | The suite polices itself: `conftest.py` ends a run that is over the fast-suite budget, a run that leaves a temporary directory behind, or a run that skipped a `unit` test — and each of those three checks is a unit test of the hook that makes it. | S27, S28, S29 | T7, T8, T9, T10 | conftest.py, tests/test_repo.py, AGENTS.md | regular | complex | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/66 (369c732) |
| T12 | The repository states its rules: `README.md` names the skills that have no executable behaviour and corrects the claim that `idea-answer` and `cold-read` have script suites, and `AGENTS.md` says that a Markdown document is not a test. | S33 | T10, T11 | README.md, AGENTS.md, tests/test_repo.py | small | simple | agent | IN PROGRESS |
| T13 | The runner refuses a false green: a root that is not a directory, or one holding no test file, exits non-zero and names what it was handed, so a mistyped path or `--help` cannot report a clean run of zero files. | S36 | T6 | scripts/run-tests.py, tests/test_run_tests.py | small | simple | agent | COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/65 (10cf85f) |
