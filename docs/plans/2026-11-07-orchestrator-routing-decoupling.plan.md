# Plan: Decouple Orchestrator Model Routing From Claude

Slug: `orchestrator-routing-decoupling`. Living spec: `docs/specs/orchestration-routing.md`. Status: **APPROVED — READY FOR EXECUTION**.

## Why now

The Python driver currently resolves model classes from a Markdown table in `~/.claude/CLAUDE.md` and only knows Claude and Codex CLI families. Once Pi runs and one orchestration vertical slice is repaired, remove the Claude-specific routing config dependency. This is a correctness/maintainability change and need not await comparative performance benchmarks. Do not rewrite the deterministic state machine.

## Sources

| Source | What it settles |
|---|---|
| https://raw.githubusercontent.com/FBisca/agent-skills/main/skills/orchestrate/references/routing.md | Existing size/difficulty matrix; class-to-model parsing and review constraints. |
| https://github.com/FBisca/agent-skills/blob/main/skills/orchestrate/scripts/orchestrate.py | Current driver and fixed CLI selection. |
| Repair plan `2026-11-07-orchestration-baselines.plan.md` | A passing vertical slice required before this config refactor; comparative benchmark is later. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | Extract typed provider/harness route config with legacy config compatibility for one release. | Read model classes forever from Claude instructions. | Config should not belong to a single harness. | routing.md |
| D2 | Preserve deterministic driver transitions; change only route selection and worker launch adapter. | Replace Python with a model-written scheduler. | Deterministic code should own state and gates. | User request; existing driver |
| D3 | Add Pi worker routes only after runtime supports safe Pi worker launch, or retain Pi as lead-only until then. | Invent Pi worker support from a Pi lead connection. | Real compatibility and safety. | Runtime adapter plan |
| D4 | Keep existing size/difficulty classes unless benchmarks justify new cells. | Rewrite route matrix based on token-price claims. | Measured successful work matters. | routing.md |

## Binding P4 contract — Q20, Q24–Q27, Q32, Q34, Q41–Q43

- **Format ownership:** YAML only for human-authored `routes`/risk policies. JSON/JSONL for worker packets, terminal results, events and state; TOML for Python package metadata. No global JSON→YAML conversion.
- **Schema:** versioned strict Pydantic v2 contracts belong to the prospective orchestrator package; while in `agent-skills`, introduce a small typed compatibility seam and explicit schema tests without creating parallel sources of truth. Route resolution order: explicit CLI override → repo policy → user default → built-in safe default; **invalid explicit routes fail**, never silently select another billable model.
- **Route capability:** separate provider/harness/model ID from quota, company-use eligibility and capabilities; Pi is a **lead only** until Pi worker launch is separately enabled. A `--cli pi` worker route must fail clearly if unsupported.
- **Risk:** objective high-risk triggers for auth, payments, destructive operations, migrations and permission boundaries; human approval at sensitive transitions. Unknown risk defaults medium; model can only raise risk.
- **Task packet:** versioned objective, allowed/forbidden paths, acceptance, constraints, source refs/revision, output contract and verification. Reject unrecognised machine fields and protect source revisions.
- **Compatibility:** maintain the legacy driver CLI and reading of its existing policy for a bounded transition period, but produce an explicit warning and test that the new config, when chosen, wins; phase out legacy only after callers migrate.

## Scenarios

- **S1** WHEN an existing Claude/Codex plan runs with no new routing config, THEN the same model-class decisions apply as before.
- **S2** WHEN a route is configured for a supported harness/model/effort combination, THEN dispatch chooses that combination with explicit validation and logs the selected route.
- **S3** WHEN a route references an unsupported backend or missing class, THEN launch fails before spawning any worker, explaining the invalid config.
- **S4** WHEN provider and role routing changes, THEN the plan schema and deterministic gate/review/PR state machine remain stable.

## Out of scope

- Adaptive review graphs, context summarisation, Pi worker-launch implementation in agent-runtime.

## Risks

- **Security:** validation must reject unexpected commands or arbitrary executable paths in untrusted config.
- **Performance:** route lookup must be cheap and deterministic.
- **Migration:** legacy Claude Markdown table remains as a fallback until consumers migrate and tests pass.
- **Rollback:** select legacy config and disable new route fields without changing plan state.

## Seams

- Existing `class_models`/routing tests and worker dispatch fakes in `skills/orchestrate/tests/`.
- Plan parser and validated route-schema unit tests.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | Add typed route schema/validation and legacy `CLAUDE.md` compatibility with focused tests. | S1, S3 | none | `skills/orchestrate/scripts/`, `skills/orchestrate/tests/`, `skills/orchestrate/references/routing.md` | regular | complex | agent | TO-DO |
| T2 | Add config-driven backend/model/effort selection, route ledger fields and end-to-end regression fakes. | S2, S3, S4 | T1 | `skills/orchestrate/scripts/`, `skills/orchestrate/tests/` | regular | complex | agent | TO-DO |
| T3 | Approve fail-closed routing compatibility without changing the existing size/class matrix; defer outcome-driven model-route tuning to P5. | S1, S2, S4 | T2 | `docs/`, `skills/orchestrate/references/routing.md` |  |  | user | TO-DO |

**Dependency:** P3 T2 repaired vertical slice; no comparative benchmark is required for a safe typed configuration. Keep current class choices until P5 produces evidence for tuning.


## P4 new acceptance paths

- WHEN routing config is malformed, unknown, or asks to spend from a provider not authorised for the task, THEN resolve fails before worker creation.
- WHEN an unsupported Pi-as-worker route is selected, THEN error is explicit and neither Codex nor Claude launches as fallback.
- WHEN a route's risk tier requires review, THEN model suggestion cannot lower it and CI/gates cannot be bypassed.
- WHEN the future monorepo extraction runs, THEN the schema and config golden fixtures remain byte-for-byte compatible and no duplicate routing implementation survives.

**Dependency:** P3 T2 verified vertical slice, not P3 T4 comparative study. **Status: APPROVED — READY FOR EXECUTION.**
