# Plan: orchestrate smoke — one ticket through the new driver

Slug: `orchestrate-smoke`. Living spec: `docs/specs/orchestrate.md`. Status: APPROVED 2026-11-06.

## Why now

The `orchestrate-lean-loop` build is done and the new driver ships. Its last ticket (T8) asks for a first live run on a one- or two-ticket plan, so the run's `retro.md` can be compared with the build's own metrics.

This plan is that live run. It is deliberately tiny: one ticket, one file of code, one test. The point is the run, not the work.

## Sources

| Source | What it settles |
|---|---|
| `docs/plans/2026-11-06-orchestrate-lean-loop.plan.md` (T8) | The build this run follows, and its ask for a first live run. |
| `skills/orchestrate/scripts/orchestrate.py` | The driver the smoke ticket runs, and the `--version` output it prints. |
| `skills/orchestrate/SKILL.md` | The run's own harness: where `retro.md` lands and where the finished wake points. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | The ticket adds `orchestrate.py --version`, printing the contract version and the driver's git sha | A ticket that changes behaviour | A change of behaviour in the smoke run mixes the worker's risk with the driver's risk; `--version` cannot break a gate | Lead, 2026-11-06 |
| D2 | The run is launched from the same checkout the build used, with the same models file, so the retro compares like with like | A different repo or model class | The retro's numbers only mean something against the same baseline | Lead, 2026-11-06 |

## Scenarios

- **S1** WHEN `orchestrate.py --version` runs, THEN it prints the driver's contract version and exits 0.
- **S2** WHEN this run ends, THEN `<run>/retro.md` holds the per-unit table and the finished wake points at it.

## Out of scope

- Any behaviour change. The smoke ticket must not gate the driver's own behaviour.

## Risks

- **Behaviour:** the smoke ticket only prints a version; it cannot change what the driver does, so the run's own gates stay green.
- **Comparison:** the run uses the build's checkout and models file, so the retro compares like with like; a different repo would make the numbers meaningless.
- **Cost:** one ticket, one file of code, one test — the run cannot grow into a second build.

## Seams

- `orchestrate.py --version` runs as a subprocess.
- The run's own harness (`skills/orchestrate/tests/`) covers the ticket.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | `orchestrate.py --version` prints the contract version | S1 | none | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T2 | The smoke run's `retro.md` holds the per-unit table and the finished wake points at it | S2 | T1 | skills/orchestrate/ | small | simple | agent | TO-DO |
