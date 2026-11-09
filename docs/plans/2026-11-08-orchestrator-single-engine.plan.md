# Plan: One engine — the skill delegates to the member

Slug: `orchestrator-single-engine`. Living spec: `docs/specs/orchestrator-single-engine.md`. Status: **APPROVED**
(the owner approved the action plan `2026-11-08-remaining-work.action-plan.md`, W1/PR-2, on 2026-11-08).

## Why

The engine — the plan parser, the dispatcher, the gates, the ledger — exists twice. This repository carries a
copy of it under `skills/orchestrate/scripts/` (2,970 lines in `orchestrate.py` plus five modules), and
`agent-runtime` carries the canonical one in its `agent-orchestrator` member. The two drift: the member is typed
and its suite now lives with it (`agent-runtime` PR #65), but `/orchestrate` runs the copy that lives here.

Every fix lands in the member and the skill keeps running the older one. That is the drift this workstream
removes, and it ends here: the skill's script becomes a shim that hands the command to the member's CLI, and
this repository stops carrying the engine.

## Sources

- `agent-runtime`: `packages/agent-orchestrator/` (the member), `packages/agent-orchestrator/tests/` (the
  engine's suite, moved by PR #65), `docs/specs/orchestrator-engine.md` (what the member guarantees).
- `agent-runtime`: `docs/plans/2026-11-08-remaining-work.action-plan.md` — W1/PR-2, and the decisions A1–A6.
- `agent-runtime`: `docs/plans/2026-11-08-engine-suite-handoff.md` — the state this plan starts from.
- This repository: `skills/orchestrate/scripts/`, `skills/orchestrate/tests/`, `skills/orchestrate/SKILL.md`.

## Decisions

| # | Choice | Rejected | Why | Status |
|---|---|---|---|---|
| D1 | The skill's script holds no engine code: it resolves the member's CLI and hands it the arguments. | Keeping the copy and syncing it by hand. | Two copies drift; the drift is the risk this workstream removes. | Requested |
| D2 | The resolution order is `$AGENT_RUNTIME_HOME` first, then `agent-orchestrator` on `PATH`. | `PATH` first. | `AGENT_RUNTIME_HOME` is this repository's documented way to name a checkout, and the engine already resolves the runtime that way (`$AGENT_RUNTIME_HOME/server/agent_runtime.py`, then `agent-runtime` on `PATH`). A checkout the user named must not be shadowed by an older install on `PATH`. | Requested |
| D3 | Inside the named checkout: the member's console script when the environment is synced, else `uv run` in that checkout. | `uv run` only. | `uv run` re-resolves the environment; the synced console script is the same member, already installed, and it starts faster. | Requested |
| D4 | When no member answers, the skill refuses with the way out and exits 2. It never falls back to a second engine. | Falling back to this repository's old copy. | A fallback copy is the drift. Failing closed names the fix (decision A3 of the action plan). | Requested |
| D5 | The engine's internal tests leave this repository; they live with the engine. | Keeping a second copy of the suite here. | A suite that runs against a copy tests the copy. They moved in `agent-runtime` PR #65. | Requested |
| D6 | The guard names the engine by what it is — a module that parses a plan and checks it — not by a file list. | A list of forbidden file names. | A renamed copy is still a copy. The fingerprint is the behaviour, so it survives a rename. | Requested |
| D7 | The plans that describe the engine point at the engine's new home and say what moved. | Rewriting them here. | Their implemented scenarios are archived in `agent-runtime`'s `docs/specs/orchestrator-engine.md`; this repository no longer owns the engine's behaviour. | Requested |

## Scenarios

- **S1** WHEN the orchestrate skill runs, THEN it drives the member, and the skill's tree carries no copy of
  the engine.
- **S2** WHEN the member is not installed, THEN the skill refuses with an actionable message naming the install
  command and the `AGENT_RUNTIME_HOME` escape hatch — it never falls back to a second engine.
- **S3** WHEN the skill's suite runs, THEN it holds the skill's own behaviour, and the engine's internals are
  tested where the engine lives.
- **S4** WHEN the delegation is exercised, THEN the member's CLI answers with the same commands, exit codes and
  ledger as the copy it replaces.
- **S5** WHEN the skill's documents are read, THEN the seam, the resolution order and the way out are named, and
  `AGENT_RUNTIME_HOME` keeps its documented meaning.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | The skill's engine copy is gone; `skills/orchestrate/scripts/orchestrate.py` delegates to the member's CLI, resolving it through `AGENT_RUNTIME_HOME` and then `PATH`, and refusing with the way out when neither answers. | S1, S2, S4 | none | `skills/orchestrate/scripts/`, `skills/orchestrate/SKILL.md` | regular | complex | agent | COMPLETE 2026-11-09 |
| T2 | The engine's internal tests leave the skill's suite — they moved with the engine — and the skill's own suite (frontmatter, portability, repository checks) stays green. | S3 | none | `skills/orchestrate/tests/`, `tests/` | regular | simple | agent | COMPLETE 2026-11-09 |
| T3 | The delegation is tested with a fake member (hermetic, no network, no second checkout), the guard fails if a copy of the engine reappears under `skills/`, and the skill's documents name the seam, the resolution order and the way out. | S1, S2, S4, S5 | T1 | `skills/orchestrate/tests/`, `skills/orchestrate/references/`, `skills/orchestrate/SKILL.md`, `README.md`, `AGENTS.md`, `docs/plans/` | regular | simple | agent | COMPLETE 2026-11-09 |

## Out of scope

- The engine's behaviour: it lives in `agent-runtime`, and its scenarios are archived in that repository's
  `docs/specs/orchestrator-engine.md`.
- The engine's remaining backlog (the `orchestrate-lean-loop` tickets still `TO-DO`): it is the member's work,
  and it moves with the member.
- Installing the member on `PATH`: `install.sh` still links only the `agent-runtime*` shims. Until it links an
  `agent-orchestrator` one, the `PATH` candidate answers only for an install the user made themselves.
- The other plans in the action plan (P4c, routing, baselines): they are W2, W3 and W4.

## Risks / rollback

- The skill stops working the moment the member is missing. That is the point (D4), and the refusal names the
  two ways out: a synced checkout named by `AGENT_RUNTIME_HOME`, or the member on `PATH`.
- `uv run` inside a checkout whose environment is not synced fails. The refusal and the message name
  `uv sync --frozen --all-packages` as the first step of the way out.
- Rollback is one revert: this repository carried the engine before, and the member still does.
