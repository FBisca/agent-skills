# Plan: code-driven orchestrator

Slug: `code-driven-orchestrator`. Living spec: `docs/specs/orchestrate.md`. Status: APPROVED 2026-11-06.

## Why now

One orchestrate run spent 220M cache-read tokens in the lead: 1,232 Opus turns at a 181k mean context, while all tool results together were ~204k tokens (user-measured, 2026-11-06). Cost is turns × context, and the turns are bookkeeping the skill already states as rules. Move the loop into `orchestrate.py run`; call a model only for judgment, each time with a fresh small packet. Matches the fleet v2 decision: deterministic steps in code, model only for judgment.

## Sources

| Source | What it settles |
|---|---|
| This conversation (2026-11-06) | Token measurement; grilling Q1–Q9 answers below |
| skills/orchestrate/SKILL.md, references/{state,routing}.md | Gates, run directory, ledger, routing, escalation after 2 failed rounds |
| skills/orchestrate/scripts/orchestrate.py | Ledger helper (claim, bind, checkpoint, release, metrics); never spawns |
| skills/converge/scripts/converge.py | Gate 1 is a script: `--ticket T<n>` / `--final`, exit 0/1/2 |
| ~/bin/wait-checks | CI gate is a script: PASS/FAIL line per PR |
| ~/developer/agent-runtime plan `call-cli` | `agent-runtime call <tool> --lead <id> --json` |
| ~/developer/herdr-app-mods/plans/RECIPE.md | Plans panel reads plan Status cells; a worker named with a ticket id (`<slug>-t4`) sits on that ticket; its parent shows as lead |
| vault: Decision - fleet v2 moves fetch and checks into code | Principle, per-step metrics, 3-week kill rule |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | Driver calls agent-runtime through `agent-runtime call` | import `hc_tools`; MCP stdio | Stable boundary | grilling Q1 |
| D2 | `/orchestrate` validates the plan, starts `orchestrate.py run` in a Herdr pane `orchestrate:<slug>`, and its session ends; the same command runs by hand | LLM lead keeps the loop; launchd | Pane gives hc identity and Herdr visibility; no lead tokens | grilling Q2 |
| D3 | Three tiers: known gate failures handled in code (≤2 fix rounds); unknown or ambiguous states and 3rd failures go to a fresh large-class **decider** that picks one action from a fixed menu; scope/product questions go to the user | user-only escalation; LLM lead | Keeps judgment for the unforeseen at ~15k tokens per event | grilling Q3 (revised) |
| D4 | Gaps review runs once at archive, findings to `<run>/gaps.md` for the user | per ticket | Gaps become plan edits, a judgment call | grilling Q4 |
| D5 | Archive runs as a final worker unit, then `converge.py --final` in code | lead edits the spec | Same path as tickets | grilling Q5 |
| D6 | Fix round to a dead pane → fresh worker with original `task.md` + findings path | session-id resume | No new runtime work | grilling Q6 |
| D7 | Driver keeps no state in memory: ledger + runtime store; fixed lead id `orchestrate:<slug>` stored in the ledger; every step idempotent | in-memory loop | Restart re-attaches | grilling Q7 |
| D8 | COMPLETE = converge PASS + no blocking review + CI green + PR **merged** (checked with `gh`); then dependents unblock | complete on green CI | User merges; blocked tickets branch from main after merge | grilling Q8 |
| D9 | "Needs you" surfaces in the ticket's Status cell (`IN PROGRESS · needs you: <reason>`), `<run>/attention.md`, and the driver pane | new notification mechanism | Herdr already renders the Status cell; no `hc` notify command found | gather |
| D12 | Speed mode for this plan's build (user, 2026-11-06): one review per ticket, blocking only on major defects (wrong behaviour, data loss, a scenario not really tested); fix rounds are gated by converge and CI only; the lead merges PRs; other findings go to `<run>/deferred.md` for a major review once the driver ships; no gaps review | full review loop | Ship the token-efficient driver first, then optimise the review on it | user |
| D10 | Class → model resolved per routing.md; the CLAUDE.md "Model classes" table is parsed from `~/.claude/CLAUDE.md` | a second config file | One source | routing.md |
| D13 | Every agent → driver handoff is a versioned JSON file (`"contract": 1`) validated in code (`skills/orchestrate/scripts/contracts.py`, stdlib only); the driver never parses markdown or the one-line `report` text, which only wakes it. Files: `report.json` (worker: checkpoint shape + `head` sha + `pr`), `review.json` (reviewer: `verdict` pass/block, `major[]` {id, file, line, problem, fix}, `deferred[]` {id, note}, `commit` reviewed; `block` iff `major` non-empty), `findings.json` (driver → fix round: `source` converge/review/ci, the blocking items verbatim, `attempt`), `decision.json` (decider: `action` from the S11 menu, `reason`, optional `question`). Markdown stays for prose to people and LLMs (`task.md`, `review.md`, `attention.md`). A missing or invalid file counts as no report | markdown with parsed headings; free-text report lines | Deterministic driver needs machine-checked handoffs; matches fleet v2 "handoffs JSON-validated" | user, 2026-11-06 |
| D14 | A pause is answered through the plan: Status `TO-DO` → the driver stops the held worker, releases it and dispatches a fresh attempt with the same unit; `COMPLETE` → unblocks dependents; the decider is one-shot and takes no answers | a reply channel to the decider; COMPLETE-only | S4 promises plan edits drive the run; no new channel needed | T6 review M2 |
| D11 | Success: lead tokens 0 on a failure-free run and < 1M per run including deciders, vs 220M; escalations per ticket in `metrics`; fleet v2 3-week kill rule | no measure | Never claim savings without measurement | grilling Q9 |

## Scenarios

- **S1** WHEN `orchestrate.py run <plan>` runs on an APPROVED plan, THEN for each TO-DO agent ticket whose blockers are COMPLETE, up to `--max-workers` (default 3), it claims the assignment, creates a worktree on a new branch from `origin/main`, writes `<run>/<task>/task.md`, and spawns a worker named `<slug>-t<n>` through `agent-runtime call spawn` with the routed model and effort.
- **S2** WHEN the plan is not APPROVED or lacks a required field, THEN `run` exits 2 naming what is missing and spawns nothing.
- **S3** WHEN the driver dispatches, pauses or completes a ticket, THEN it writes the new Status into that ticket's row of the plan file and changes no other line.
- **S4** WHEN the plan file changes during a run (a new ticket, a Status the user edited), THEN the next loop iteration acts on the new content.
- **S5** WHEN a worker reports complete, THEN the driver checkpoints its `report.json` and runs `converge.py --ticket T<n>`; on FAIL it resumes the same worker with a new task directory holding the failing lines and raises `review_rounds` by one.
- **S6** WHEN converge passes, THEN the driver spawns a fresh large-class reviewer with paths only; a `review.json` with verdict `block` becomes a fix round whose `findings.json` and `task.md` carry only its `major` items.
- **S6a** WHEN a `report.json`, `review.json` or `findings.json` is missing or fails its contract (D13), THEN the driver does not advance the ticket and records the contract error as the unit's attention event.
- **S7** WHEN a fix round targets a worker whose pane is gone, THEN the driver spawns a fresh worker with the original `task.md` and the findings path.
- **S8** WHEN the review has no blocking finding, THEN the driver runs `wait-checks` on the ticket's PR; FAIL sends the failed log to the worker as a fix round.
- **S9** WHEN checks pass and `gh` reports the PR merged, THEN the ticket becomes COMPLETE in ledger and plan, and its dependents become dispatchable; before the merge its Status reads `IN PROGRESS · awaiting merge (<PR>)`.
- **S10** WHEN a COMPLETE ticket's worker holds no next unit, THEN the driver stops it and removes its worktree only when the checkout is clean and the branch is pushed or merged; otherwise it leaves it and records why.
- **S11** WHEN a unit fails a gate a 3rd time, or a worker reports `blocked`/`decision`, exits without a report, or reports conflict, THEN the driver spawns a fresh large-class decider with a packet (event, ledger slice, paths) that writes `decision.json` with one action from {retry, retry one class up, fresh worker, mark blocked, skip, ask user}.
- **S12** WHEN `decision.json` is missing, invalid, or names `ask user`, THEN the ticket pauses with `needs you: <reason>` in its Status and an entry in `<run>/attention.md`, and the other tickets keep running.
- **S13** WHEN a person-owned ticket becomes ready, THEN its Status reads `needs you: <what it needs>` and it waits until the user sets it COMPLETE in the plan.
- **S14** WHEN the driver restarts on a plan with a ledger, THEN it reuses the stored lead id, re-attaches to live assignments through `wait`, and spawns nothing already bound.
- **S15** WHEN every agent ticket is COMPLETE, THEN the driver spawns the archive worker and the gaps reviewer (`<run>/gaps.md`), and runs `converge.py --final` on the archive branch; FAIL is a fix round for the archive worker.
- **S16** WHEN a run stops (all COMPLETE, or everything left paused), THEN `metrics` reports per ticket the route, review rounds, escalations, decider calls and worker usage, and the lead's own model turns as 0.
- **S17** WHEN the user runs `/orchestrate <plan>`, THEN the skill runs `orchestrate.py launch <plan>`, which validates the plan and starts `run` in a Herdr pane named `orchestrate:<slug>`, and the skill reports the pane name and ends.

## Out of scope

- A model decider for scope or product questions (stays with the user).
- Session-id resume of dead panes.
- Changes to Herdr or the Plans panel.
- Migrating plans already in flight (they finish on the current skill).

## Risks

- Security: workers keep today's authority; the decider can only pick from the action menu, validated by code (S11, S12); worktree removal keeps the clean-and-pushed check (S10).
- Performance: covered by D11 and S16; worker and reviewer tokens are unchanged.
- Migration: ledger stays version-compatible; the driver adds fields, removes none. In-flight plans out of scope.
- Rollback: the old SKILL.md lead loop is one revert away; kill rule in D11.
- Overlap: agent-runtime plans `parallel-wait-and-cli-profiles` and `worker-token-metrics` are open; usage figures in S16 read whatever `wait`/`status` return, `unknown` otherwise.

## Seams

- `orchestrate.py run` against a fake `agent-runtime call` executable, a fake `gh`, a fake `wait-checks` and a temp git repo, in `skills/orchestrate/tests/`.
- `converge.py` runs for real in those tests.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T0 | agent-runtime `call-cli` plan merged and installed on this machine | none | none | | | | Felippe | COMPLETE 2026-11-06 · #46 merged (92b7682); the installed `agent-runtime` links the main checkout |
| T1 | `run`: plan check, ready-ticket selection, worktree, `task.md`, spawn through `agent-runtime call`, plan Status writes, plan re-read, restart re-attach | S1–S4, S14 | none | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged #9 (d94c780) |
| T2 | Gates converge → reviewer → fix rounds, dead-pane fresh worker; `contracts.py` for report, review, findings (D13) | S5–S7, S6a | T1 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged #10 (e498a1b) |
| T3 | CI and merge gate, COMPLETE + unblock, worker stop and worktree prune | S8–S10 | T2 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | simple | agent | COMPLETE 2026-11-06 · merged #11 (594f983) |
| T4 | Decider with action menu, pause and `attention.md`, person-owned tickets | S11–S13 | T2 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged #12 (f1ce1bc) |
| T5 | Archive unit, gaps at archive, `converge --final` (accepts the plan being archived: ARCHIVED status and its own plan file in scope), run metrics | S15, S16 | T3, T4 | skills/orchestrate/scripts/, skills/orchestrate/tests/, skills/converge/ | regular | simple | agent | COMPLETE 2026-11-06 · merged #13 (0304dd6) |
| T6 | `launch` subcommand; SKILL.md and references rewritten to the launcher + driver contract | S17 | T5 | skills/orchestrate/ | small | simple | agent | COMPLETE 2026-11-06 · merged #14 (ece48fd) |
| T7 | Live run in Herdr on a 1–2 ticket plan: driver pane + nested workers + Plans panel; lead tokens measured against D11 | none | T0, T6 | | | | Felippe | IN PROGRESS · needs you: run `/orchestrate` on a 1–2 ticket plan in Herdr |
