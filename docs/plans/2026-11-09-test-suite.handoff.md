# Handoff — the test-suite plan, mid-drive

**State:** the drive is **live** (`hc` pane `orchestrate-test-suite`), building **T12**. Its draft PR **#67** is open with
CI running. Eleven of thirteen tickets are merged. **T5 never ran** (its blocker T4 is marked `SKIPPED` but its PR is
merged). After T12 and T5: **archive** the plan into `docs/specs/test-suite.md`.

**Plan:** `docs/plans/2026-11-09-test-suite.plan.md` — `Status: APPROVED 2026-11-09`. It is the ledger: edit its Status
cells and Decisions rows, never a worker's artifact, and never the plan's scenarios to fit what was built.

---

## 1. What is done

| Ticket | PR | What landed |
|---|---|---|
| T1 | #56 | 31 prose tests + 5 duplicates deleted; one Pi discovery test over every skill (S35) |
| T2 | #58 | converge's own reader parses every tracked plan; the engine's 9 columns asserted by name (S20, S21) |
| T3 | #57 | `idea_check.py` names its vocabulary; `IDEA_CHECK_TODAY`; both skills document the same vocabulary (S22, S30) |
| T4 | #59 | the lint refuses every defect it names, exit codes 1/2/0 (S23, S24, S34) |
| T6 | #60 | the runner names the file that hangs (S25) |
| T7 | #61 | the VAULT_DIR checks assert **exit 3** (S26) |
| T8 | #62 | the gate script loads once per module; temp dirs cleaned (S37) |
| T9 | #63 | converge's pure-logic tests leave the git fixture (S31) |
| T10 | #64 | `unit` means in-process + own temp dir; marker text says so (S31) |
| T11 | #66 | conftest polices itself: budget, temp leaks, skips (S27, S28, S29) |
| T13 | #65 | the runner refuses a false green: non-directory root, or no test file (S36) |

Suite now: **fast 144 tests in 2.22 s** (budget 3 s, enforced), full suite green on 3.11/3.12/3.13.

## 2. What is left — in order

1. **T12** — PR **#67** (draft). Read it, `gh pr ready 67`, merge when CI is green. Then set its cell to
   `COMPLETE 2026-11-09 · merged <pr> (<sha>)`. Its test must be the **invariant** (the skills README names == the skills
   with no `scripts/`, both directions), never a sentence.
2. **T4 → COMPLETE.** Its cell says `SKIPPED · the pull request was merged before the unit finished`, but **#59 is
   merged**. Fix the cell to `COMPLETE 2026-11-09 · merged https://github.com/FBisca/agent-skills/pull/59 (2f28d1b)`.
   Until it says COMPLETE, **T5 stays blocked** (Blocked by: T4).
3. **T5** — the hygiene rules become lint problems naming file+line (S32). Relaunch the drive; it dispatches T5.
   Paths: `scripts/lint_skills.py`, `tests/test_skill_frontmatter.py`, `tests/test_repo.py`, `tests/test_portability.py`.
   Note: the three `test_S32_names_no_person` tests are deleted by this ticket, and `AGENTS.md` states the rule instead —
   `AGENTS.md` is **not** in T5's Paths, so either add it to the row or let the rule live in the lint's docstring.
4. **Archive** — the driver archives when every ticket is COMPLETE: it writes `docs/specs/test-suite.md`, renames the
   tests to the spec's R-IDs, and sets the plan to `ARCHIVED`. `docs/specs/test-suite.md` does not exist yet; the archive
   worker creates it.

## 3. How to drive it

```bash
cd /Users/fbisca/developer/agent-skills
hc read orchestrate-test-suite            # what the driver last said
hc ls | grep test-suite                   # the driver: `orchestrate-test-suite`, workers: `test-suite-t<n>`
```

Relaunch after an edit (the driver re-reads the plan and the ledger):

```bash
cd /Users/fbisca/developer/agent-skills
hc run --bg --name orchestrate-test-suite --cwd "$PWD" --json -- \
  /Users/fbisca/developer/agent-runtime.worktrees/drive/.venv/bin/python -m agent_orchestrator run \
  "$PWD/docs/plans/2026-11-09-test-suite.plan.md" --repo "$PWD" --max-workers 1 \
  --routes-file ~/.config/orchestrate/routes-claude-haiku.json \
  --cli claude --brain-cli claude --gate "scripts/checks.sh" --notify-terminal "$HC_TERMINAL_ID"
```

Answer a paused unit (the menu: `retry`, `retry one class up`, `fresh worker`, `mark blocked`, `skip`, `answer`):

```bash
/Users/fbisca/developer/agent-runtime.worktrees/drive/.venv/bin/agent-orchestrator decide \
  docs/plans/2026-11-09-test-suite.plan.md t12 answer --reason "<why>" --answer "<what the worker must do>"
```

**The Lead merges; the driver never does.** A ticket stops at `IN PROGRESS · awaiting merge (<PR>)` until you merge.

## 4. Where the engine is

The driver the run uses is **not** the released one:

| Tree | What it is |
|---|---|
| `~/developer/agent-runtime.worktrees/drive` (branch `local/drive-engine`) | what the live run executes: lead-alerts + task_id + R16 + the assignment fix. Local only, **not pushed**. |
| PR **#74** (`feat/orchestrator-payload-race`) | the publishable R16 work (payload race + warn-the-sender + assignment id), 935 passed / 4 skipped, ruff clean |
| PR **#72** (`feat/orchestrator-report-task-id`) | R15: the unit brief names the `task_id` its report must carry |
| PR #69 (`fix/orchestrator-lead-alerts`) | someone else's: wake alerts, `--notify-terminal`, tree timeouts |

**Merge order: #69, then #72, then #74** — all three touch `driver.py`; that order is what `drive` actually contains.
`#69` carries `--notify-terminal`, without which the relaunch command above fails with exit 2.

## 5. Five defects this run found (all fixed, and worth knowing)

1. **`report task_id 'T3' is not t3`** — the unit brief named the report's *path* but never the id, while its heading
   showed the *plan's* `T3`. Workers wrote `T3`; the driver refused. → **#72** (R15), and the brief now says
   `Report with task_id \`t3\``.
2. **A `pass` verdict lost to a write race** — a reviewer reported at 13:38:35 and wrote `review.json` at 13:40:44; the
   driver had already asked the Lead, and the later report hit "matches no open gate". → **#74** (R16): a bounded grace
   (5 s), then **warn the agent that sent it** (twice at most, gate kept open), then the Lead with the count. It also
   covers a payload that is *there but unusable* (a missing `answer_required`, a `task_id` of the wrong kind).
   **It self healed three times in this run** (`T11`, `T13`, and T12's retry) where T2/T3 had cost a Lead round each.
3. **The warned agent returns as a new assignment** — the task still named the old one, so its next report matched no
   gate; the payload was written and never read. Fixed in #74: a warning records the assignment it resumed.
4. **The runner could report a false green** (`--help`, a typo, an empty folder → `0 test files`, exit 0). Caught by
   T10's reviewer, built as **T13/#65**.
5. **`not_run` is documented but refused** — a `COMPLETE` report that honestly marks a check `not_run` is rejected by
   the ledger ("complete result has failed or omitted checks"), so the merged unit gets auto-`SKIPPED` and a dependent
   stays blocked. **Not fixed.** T11 paid it: its cell had to be set by hand. Worth an engine ticket: either accept
   `not_run` with a reason on a `COMPLETE` report, or drop it from the contract's vocabulary.

## 6. Environment traps (all hit during this run)

- **`hc` panes start with a clean environment.** A spawned `pi` had no `MINIMAX_API_KEY`, so every worker died before its
  first turn ("No API key found for minimax"). Fixed by storing the key in **pi's own store**
  (`~/.pi/agent/auth.json`, mode 600); `pi` then authenticates from disk. `claude` needs nothing.
- **Model routes.** `minimax/*` is out of token-plan credits (429). `ollama-cloud/minimax-m3.1-flash` answered a
  one-shot prompt but its workers died ("runtime state error"). The run is on **`claude/haiku`** via
  `~/.config/orchestrate/routes-claude-haiku.json`.
- **Never name a route file `~/.config/orchestrate/routes.json`.** That is the engine's *default* lookup path: it leaked
  into every run on the machine and turned the engine's own suite red (`test_default_run_names_the_cli_family`). The
  files are `routes-<what>.json`; pass them with `--routes-file`.
- **A retry keeps the model pinned in the ledger.** To move a unit to another model you must clear its ledger rows
  (driver stopped) and set the plan cell to `TO-DO`, so it dispatches fresh. That is how t7 moved off minimax.
- **The driver auto-`SKIP`s a merged PR** whose report the ledger rejects. `SKIPPED` blocks nothing but *unblocks*
  nothing either: a dependent ticket stays stuck until the cell says `COMPLETE`. Set it by hand.
- **Ledger surgery** (driver stopped) is allowed for a machine artifact; backups are
  `~/.local/state/orchestrate/test-suite.json.bak-{t7,t10}`. A worker's `review.json` was completed by hand once
  (`answer_required: false` on a deferred item) because the reviewer's pane was already gone.

## 7. Tests this plan must not undo

`docs/specs/harness-portability.md` R2/R3 and `docs/specs/orchestrator-single-engine.md` R5 are enforced by prose tests
that this plan **kept on purpose** (decision D3). The 24 prose tests that no living spec names are gone. If a later change
deletes `test_S5_the_documents_name_the_seam_the_order_and_the_way_out` or the R2/R3 tests in
`skills/start-planning/tests/test_portability.py`, a requirement loses its only enforcement.
