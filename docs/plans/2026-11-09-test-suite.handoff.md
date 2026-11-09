# The test-suite plan — done and archived

**State:** all thirteen tickets are `COMPLETE`, the archive is merged, and the plan is `ARCHIVED 2026-11-09`. Nothing is
left to drive. The driver pane is stopped and the run's worktrees and branches are removed.

**Plan:** `docs/plans/2026-11-09-test-suite.plan.md` · **Living spec:** `docs/specs/test-suite.md` (R1–R18, from S20–S37).

---

## What landed

| Ticket | PR | What landed |
|---|---|---|
| T1 | #56 | 31 prose tests + 5 duplicates deleted; one Pi discovery test over every skill |
| T2 | #58 | converge's own reader parses every tracked plan; the engine's 9 columns asserted by name |
| T3 | #57 | `idea_check.py` names its vocabulary; `IDEA_CHECK_TODAY`; both skills document it |
| T4 | #59 | the lint refuses every defect it names, exit codes 1/2/0 |
| T5 | #68 | skill hygiene is lint problems (hardcoded path, invocation syntax, absolute user path, symlink, NOTICE without upstream or licence), named with file and line; `AGENTS.md` states "skills name roles, never people" |
| T6 | #60 | the runner names the file that hangs |
| T7 | #61 | the `VAULT_DIR` checks assert **exit 3** |
| T8 | #62 | the gate script loads once per module; temp dirs cleaned |
| T9 | #63 | converge's pure-logic tests leave the git fixture |
| T10 | #64 | `unit` means in-process + own temp dir; the marker text says so |
| T11 | #66 | conftest polices itself: budget, temp leaks, skips |
| T12 | #67 | the README names the skills with no executable behaviour (asserted as an invariant, both directions); `AGENTS.md` says a Markdown document is not a test |
| T13 | #65 | the runner refuses a false green (non-directory root, or no test file) |
| archive | #69 | `docs/specs/test-suite.md` written, every test renamed to `test-suite/R<n>`, plan `ARCHIVED` |

Suite now: **207 tests** (144 in the fast suite), full gate `scripts/checks.sh` green on 3.11/3.12/3.13.

## Ledger surgery this run needed (all recorded here, none left open)

- **T4** read `SKIPPED · the pull request was merged before the unit finished` although #59 was merged; set to `COMPLETE`
  by hand (the ledger's auto-skip, defect 1 below).
- **T5's Paths** gained `AGENTS.md`, because the "names no person" rule has to be stated there once its three tests go
  (T1 had already deleted those tests).
- **T12's cell** was set by hand: the merge gate for `t12d1` ran after the driver had removed the worktree of the
  superseded attempt `t12`, so the gate raised `FileNotFoundError` (defect 2 below) and never wrote `COMPLETE`.

## Two engine defects this drive found (both in agent-runtime, both unfixed)

1. **A report the ledger rejects turns a merged unit into `SKIPPED`.** The archive reported `COMPLETE` with its two
   checks (`scripts/checks.sh`, `converge --final`, both passed) and the ledger still said "required checks are
   missing", so a unit whose pull request was merged got `SKIPPED`. Same cause as the earlier `not_run` case: a
   `COMPLETE` report whose `checks` list does not match the gate's expected set is refused, and the refusal is not
   told to anyone until the merge. Either accept a report whose checks passed under their own names, or refuse at the
   report, not at the merge.
2. **The merge gate runs in a worktree the driver may have deleted.** A superseded attempt (`t12` → `t12d1`) shares one
   worktree; when the released attempt is cleaned up, the live attempt's `awaiting-merge` gate dies on
   `FileNotFoundError` and the ticket never reads `COMPLETE`. Poll the merge from the repository, not the worktree, or
   skip the gate for a unit whose worktree is gone.

## Traps worth remembering

- **`hc` panes start with a clean environment**; store API keys in the agent's own store (`~/.pi/agent/auth.json`), not
  in the shell.
- **Never name a route file `~/.config/orchestrate/routes.json`** — that is the engine's default lookup path and it
  leaks into every run on the machine.
- **The budget is wall-clock.** Under this machine's load (other drives live: load average 16–19) the fast suite takes
  4–17 s and the `unit` run fails on its own budget while the gate (`-m ""`) stays green. That is the budget working,
  not a flaky test: judge the fast suite on an idle machine.
- **`uv run pytest | tail` hides the exit status** — a pipeline reports `tail`'s code. Read the log file instead.

## Tests this plan must not undo

`docs/specs/harness-portability.md` R2/R3 and `docs/specs/orchestrator-single-engine.md` R5 are enforced by prose tests
this plan kept on purpose (decision D3). The 24 prose tests that no living spec names are gone. If a later change
deletes `test_S5_the_documents_name_the_seam_the_order_and_the_way_out` or the R2/R3 tests in
`skills/start-planning/tests/test_portability.py`, a requirement loses its only enforcement.
