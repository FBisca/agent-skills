# Plan: Experiment With Adaptive Reviews and Context Budgets

Slug: `adaptive-graph-experiment`. Living spec: `docs/specs/orchestration-evaluation.md`. Status: **APPROVED — READY FOR EXECUTION**.

## Why now

Only after P3 has restored correct execution and gathered usable evidence should the deterministic graph be experimentally simplified. The 2026-11-06 routing calibration notes highlight oversized ticket and fix rounds; the goal is fewer failed verified attempts, not simply fewer tokens or more agents.

## Sources

| Source | What it settles |
|---|---|
| https://raw.githubusercontent.com/FBisca/agent-skills/main/skills/orchestrate/references/routing.md | Existing ticket-size caps, class selection, fix rounds, escalation and observed oversized failures. |
| https://raw.githubusercontent.com/FBisca/agent-skills/main/skills/orchestrate/SKILL.md | Driver has deterministic gates, structured contracts and per-ticket metrics. |
| Repair/evaluation plan `2026-11-07-orchestration-baselines.plan.md` | First restore verified execution; then compare a frozen baseline before adaptive optimisation. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | Make one benchmark-backed graph change at a time behind an explicit opt-in flag. | General graph rewrite. | Isolate causality and preserve rollback. | Benchmark requirement |
| D2 | Keep deterministic gate enforcement; vary only review entry conditions or context packets. | Let agent self-certify success. | Reliable observable correctness. | orchestrate skill |
| D3 | Do not optimize away meaningful architecture context solely to reduce tokens. | Aggressive automatic context stripping. | Task completeness depends on relevant context. | User goal; routing calibration |

## Binding P5 contract — Q16–Q23, Q27–Q30, Q35, Q38–Q43

- Keep model action proposal bounded by a deterministic, transition-validated graph. Risk-tier review skipping is opt-in and never bypasses authentication/payment/migration/destructive checks. No unconstrained recursive subagent orchestration.
- A context packet references source revisions and prior decisions; worker source browsing on demand, with provenance and measured rediscovery overhead. Preserve context that affects correctness; never optimise for minimum tokens alone.
- One corrective attempt per evidence-classified failure; no automatic replay of identical stuck tool calls; clear escalation/stop semantics. Compare verified success, elapsed time, human rescues and **actual** usage before selecting a strategy.
- Preserve a known-good non-adaptive strategy and saved run/state compatibility. Rollback via flag disables changed scheduling/review logic without requiring state migrations. Failed tests, unsafe risk and absent evaluation data fall back to conservative graph behaviour.
- Make the experiment **optional**; do not delay P0–P4c for graph enhancements. No guaranteed numeric savings claims without trial evidence.

## Scenarios

- **S1** WHEN a task is low-risk and the benchmark-backed opt-in condition applies, THEN the experimental graph omits only eligible redundant steps while retaining required deterministic gates.
- **S2** WHEN a task is sensitive or its tests fail, THEN baseline review/escalation paths are preserved regardless of the experiment flag.
- **S3** WHEN context packet composition changes, THEN its source files/decisions and size are logged, and scenarios still pass.
- **S4** WHEN the experiment produces worse verified completion, intervention, or latency, THEN disabling the flag restores the original graph with no data migration.

## Out of scope

- Replacing Python orchestration with agent discretion, changing runtime durable store, broad multi-provider pricing experimentation.

## Risks

- **Security:** never skip required reviews for permission, auth, money, personal data or migration changes.
- **Performance:** logging is bounded and non-blocking; keep existing timeout/stop behavior.
- **Migration:** additive feature flag, no plan-schema migration.
- **Rollback:** flag off restores existing path, verified by test.

## Seams

- `skills/orchestrate/tests/` fake runtime/gh and fixed plan-scenario gates.
- Benchmark runner from prior plan, with paired clean-worktree runs.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | Add opt-in graph or packet strategy seam with no change to default behavior and test coverage for sensitive tasks. | S1, S2, S4 | none | `skills/orchestrate/scripts/`, `skills/orchestrate/tests/` | regular | complex | agent | TO-DO |
| T2 | Add bounded provenance and outcome metrics for the chosen experiment; validate default rollback. | S3, S4 | T1 | `skills/orchestrate/scripts/`, `skills/orchestrate/tests/`, `docs/` | regular | simple | agent | TO-DO |
| T3 | Run paired real tasks, approve continuation only if measured quality/cost threshold improves. | S1, S2, S3, S4 | T2 | `docs/` |  |  | user | TO-DO |

**Dependency:** finish orchestration baselines and routing decoupling; postpone indefinitely if the measured default graph is already good enough.


## P5 reviewer adversarial cases

- WHEN the model misclassifies a high-risk change as low-risk, THEN deterministic risk triggers enforce review/approval.
- WHEN a context packet omits a referenced source at its pinned revision, THEN execution fails explicitly instead of inventing missing context.
- WHEN an experiment worsens verification, human-rescue rate or failure recovery, THEN disabling its flag returns the previously verified route and state semantics.
- WHEN benchmark input/output/cache counts are missing or billed differently across subscriptions, THEN reports mark metrics incomparable rather than imputing $ cost or zero usage.

**Status: APPROVED — READY FOR EXECUTION. Graph changes not yet made.**
