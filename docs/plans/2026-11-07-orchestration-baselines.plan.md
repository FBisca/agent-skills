# Plan: Restore a Verified Orchestration Workflow, Then Measure Alternatives

Slug: `orchestration-baselines`. Living spec: `docs/specs/orchestration-evaluation.md`. Status: APPROVED

## Why now

The current orchestration path is reported broken. First capture reproducible failure cases and repair one complete ticket vertical slice; **do not require a healthy baseline as a prerequisite for correctness repair**. Only after verified operation collect telemetry and compare against strong single-agent alternatives. Routing notes (2026-11-06) report oversized context and a fix round with no edits; treat those as leads to investigate, not proof of a universal model/harness defect.

## Sources

| Source | What it settles |
|---|---|
| https://raw.githubusercontent.com/FBisca/agent-skills/main/skills/orchestrate/references/routing.md | Size/difficulty routing rules, 2026-11-06 failed calibration examples, threshold of 3 completed units before route changes. |
| https://raw.githubusercontent.com/FBisca/agent-skills/main/skills/orchestrate/SKILL.md | Existing `metrics.json`, structured contracts and gates. |
| User request, 2026-11-07 | Assess graph/context engineering against modern strong single agents; preserve quality and efficiency. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | Make a failing end-to-end regression for the current broken dispatch → edit → verification → completion path; repair to fixed scenarios before comparative benchmarking. | Gate bug fixes on a functioning historical benchmark. | Correctness is a precondition for meaningful comparison. | User decision Q30/Q35 |
| D2 | Report verified completion first, then intervention count, elapsed time, input/output/cache tokens and reruns. | Optimise context size in isolation. | Context only matters insofar as it improves results. | Routing calibration |
| D3 | Separate repair and instrumentation from the later paired comparison. Once repaired, freeze a revision and run counterfactual experiments without simultaneous graph tuning. | Compare moving targets. | Interpretability without blocking recovery. | Q30/Q35 |
| D4 | Ticket cells carry machine-readable values only: `Status: APPROVED`, `Blocked by` holds ticket IDs of this plan (cross-plan dependencies stay in prose), `Satisfies` holds scenario IDs, `Difficulty` is `simple`/`complex`, `Owner` is `agent` or `user`. T1 is not blocked (its offline fixture may begin independently of P0/P1); T3 is `complex` because `metrics.json` is a public contract; T4 is `agent`-owned and runs on the loop's own model (`pi` with `minimax`); the owner approved it on 2026-11-08 (no extra budget, no other provider access to approve). | Leaving the prose in the cells; treating the plan as free text. | The driver validates these columns; prose in a cell reads as a ticket or scenario that does not exist. | Driver schema check, 2026-11-07 |

## Binding P3 contract — Q19, Q21–Q22, Q28–Q30, Q35, Q38–Q43

**Mandatory stages (not interchangeable):**
1. RED: pin a pre-repair Git revision or issue fixture; reproduce at least one *specific* broken vertical flow via deterministic test with fake terminal/provider, including partial report, retry and restart corner cases.
2. GREEN: repair one end-to-end approved plan ticket (dispatch, worktree, report, verification, terminal state), preserving current safety and PR semantics. Fix the bug, not the whole architecture.
3. OBSERVE: record per-attempt, schema-versioned telemetry (harness, provider, task/source revision, times, tool/model calls, input/output/cache token counts when available, retries, loops, human rescues, gate outcomes) with unknown cost/usage **null, not zero**. Keep old `metrics.json` consumers working.
4. COMPARE: only after green, same-task clean-worktree single-agent and orchestrated runs; no hidden automatic provider fallback and no use of company-funded provider without permission. Do not invent API dollar cost for subscription quotas.

**Guardrails:** Small-task Pi experiment cap remains 15 minutes or 30 iterations, not a global production timeout. Every attempt has a bounded budget. Preserve observed failures as evidence. A run is only `VERIFIED` when deterministic checks pass and a source revision+artifact manifest is recorded.

## Scenarios

- **S0** WHEN a known orchestration failure is reproduced on an isolated fixture, THEN the test fails before repair and passes afterwards under the same fixed acceptance criteria; only a deterministic validator marks the source revision verified.
- **S1** WHEN a repaired workflow is later compared with a single agent on clean worktrees, THEN the report records identical source commit, scenario gate and task scope for both.
- **S2** WHEN a run succeeds or fails, THEN results include verified completion, elapsed time, intervention and tool-loop/retry counts, with token figures labelled input/output/cached and unavailable fields left blank.
- **S3** WHEN a test run stalls or exceeds a declared budget, THEN the benchmark terminates it and records a failure instead of running indefinitely.
- **S4** WHEN at least three representative tasks have been measured per candidate route after correctness restoration, THEN a read-only recommendation identifies which graph/context changes have evidence behind them.

## Out of scope

- New agent backends, edits to runtime worker-state semantics, experimental routing changes during measurement.

## Risks

- **Security:** run in disposable worktrees with secrets excluded and explicit agent permissions.
- **Performance:** bounded spend, time, parallel workers and retry counts prevent unbounded trials.
- **Migration:** targeted correctness repairs are allowed under regression tests and rollback, but no unauthorised durable-state migration.
- **Rollback:** remove benchmark scripts/results without altering production orchestration.

## Seams

- Existing `metrics.json` parser, plan scenario gates and fake runtime/gh tests.
- A small fixed corpus of real, permission-safe tasks recorded in a manifest with pinned commits.

## Tickets (final implementation order)

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | Reproduce a failing end-to-end dispatch/verification test, including report timing and restart, before changing graph logic; the offline fixture may begin independently of P0/P1, live Pi runs wait on them | S0, S3 | none | `skills/orchestrate/tests/`, `tests/` | regular | complex | agent | COMPLETE 2026-11-07 (PR #31, squash e0abe0f) |
| T2 | Repair one complete ticket from clean worktree to verified terminal state, preserving Claude/Codex behaviour and approved transitions; reconcile any overlapping runtime edit with #39/#45 before merge, in a separate runtime PR if needed | S0 | T1 | `skills/orchestrate/scripts/`, `skills/orchestrate/tests/` | regular | complex | agent | COMPLETE 2026-11-07 (PR #31, squash e0abe0f) |
| T3 | Add schema-versioned attempt evidence with existing `metrics.json` compatibility; unknown measurements remain null | S2 | T2 | `skills/orchestrate/scripts/`, `skills/orchestrate/tests/`, `benchmarks/` | regular | complex | agent | COMPLETE 2026-11-08 (PR #34, squash 95dd013) |
| T4 | Compare at least three real tasks per candidate route with pinned revisions and acceptance checks, single-agent versus orchestrated execution, plus a failure report; it runs on the loop's own model (`pi` with `minimax`), so there is no provider spend beyond it for the user to approve | S1–S4 | T3 | `benchmarks/`, `docs/` | regular | complex | agent | TO-DO |

**Dependency:** P0/P1, plus P2 for Pi delegation. P3 T2 is the gate for P4/P4b; P3 T4 only gates P5 optimisation, not correctness or typed routing. **Status: APPROVED — READY FOR EXECUTION.**
