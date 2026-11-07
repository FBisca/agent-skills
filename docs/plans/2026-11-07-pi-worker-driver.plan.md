# Plan: The Orchestrate Driver on Pi Workers with a Codex Terra Brain

Slug: `pi-worker-driver`. Living spec: `docs/specs/harness-portability.md`. Status: APPROVED 2026-11-07

## Why now

The runtime plan (`agent-runtime/docs/plans/2026-11-07-pi-worker.plan.md`) makes Pi a worker backend. Until the driver
can route to it, that backend is unreachable: `--cli` accepts only `claude` and `codex`, the class→model table has no
Pi column (any non-Claude backend silently takes the Codex column), and the reviewer — the merge gate — asks for class
`large`, which on a Pi backend would be a MiniMax model rather than the one model the user allows as the brain. The
user's decision (2026-11-07): workers run on Pi/MiniMax, the two review gates run on `gpt-6.1-terra`, and nothing
bigger.

## Sources

| Source | What it settles |
|---|---|
| `agent-runtime/docs/plans/2026-11-07-pi-worker.plan.md` (2026-11-07) | The runtime side: Pi as a native family, the tools from Pi's MCP registration, the role in the task text. |
| Gatherer run (codex `gpt-6.1-terra`, fresh context, read-only, 2026-11-07) | The driver's touchpoints, the model-table rule, the tier that asks for class `large`, the open decisions. |
| `skills/orchestrate/scripts/orchestrate.py:115-116,320-321,514-530,727,1271-1273,1845-1854,2298-2304,2423,2691-2701` | `class_models` (Claude column 1, every other backend column 2), `MATRIX`, the reviewer spawn, the gaps-reviewer spawn, the archive worker, `spawn_args`, `--cli` and `--models-file`. |
| `~/.claude/CLAUDE.md` (symlink → `~/developer/dotfiles/agents/.claude/CLAUDE.md`) | The "Model classes" table: `medium` on the Codex column is `gpt-6.1-terra`. |
| `docs/specs/harness-portability.md` | The living spec this plan updates. |
| `docs/plans/2026-11-07-orchestration-baselines.plan.md` | The parked run this work unblocks (its worker ran on Claude, not MiniMax). |
| User answers (2026-11-07, Q1–Q9) | The review gates run on `gpt-6.1-terra`; the Pi model column falls back to the skill's own table; the scope is the Pi worker. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | `--cli` gains `pi`; the spawn carries `cli=pi` and the runtime resolves it as a family. | A `--profile pi`; keeping the Pi worker behind a profile name. | Pi is a native family in the runtime (its plan, D1); the driver forwards the family name unchanged (`spawn_args`). | User Q1; runtime plan D1 |
| D2 | The Pi class→model mapping lives in the skill's own table (`skills/orchestrate/references/models.md`), with `minimax/MiniMax-M3.1-Flash` for every class; a Pi column in `--models-file` wins when it is there. | Only the dotfiles table; only a `--pi-model` flag. | The build fences paths to its own repo, so the plan cannot depend on a file in the dotfiles repo; the skill-local table keeps the run reproducible, and the canonical table stays canonical once its commit lands. | User Q9 (c) |
| D3 | The review gates — the reviewer and the gaps reviewer — spawn on the brain backend (`codex`) with its **medium** model, `gpt-6.1-terra`. | Letting the gates run on the worker backend; a per-tier model flag. | The user allows `gpt-6.1-terra` and nothing bigger; the gates decide merges, so they belong on the brain tier. | User Q5, Q8 (a) |
| D4 | The implementer, the archive worker and the lookup keep the worker backend and its class model; the effort still varies by class. | One backend for every tier. | The bulk of the work is what Pi/MiniMax is for; the gates are the only decider-ish tiers. | User Q8 (a) |
| D5 | With `--cli claude` or `--cli codex`, every tier keeps today's backend and model. | Changing the defaults for the existing backends. | The change is additive; the Claude and Codex runs must not move. | User Q5 |

## Scenarios

- **S1** WHEN the driver runs with `--cli pi`, THEN each class resolves to the Pi column's model and the worker's spawn carries `cli=pi`.
- **S2** WHEN the models file has no Pi column, THEN the driver resolves the Pi models from the skill's own table (`minimax/MiniMax-M3.1-Flash` for every class) and the run starts.
- **S3** WHEN the reviewer tier spawns, THEN it spawns on the brain backend (`codex`) with `gpt-6.1-terra` and never on a larger model.
- **S4** WHEN the gaps reviewer spawns, THEN it spawns on the brain backend with `gpt-6.1-terra`.
- **S5** WHEN the implementer or the archive worker spawns, THEN it spawns on the worker backend with that class's model.
- **S6** WHEN the worker backend is `claude` or `codex`, THEN every tier keeps its current backend and model.

## Out of scope

- The runtime side of the Pi worker: `agent-runtime/docs/plans/2026-11-07-pi-worker.plan.md`.
- The dotfiles commit that adds a Pi column to `~/.claude/CLAUDE.md`; the skill-local table answers until it lands.
- Relaunching the parked `orchestration-baselines` run on the Pi backend: the scope of this plan is the Pi worker itself.
- Any change to the escalation menu, the fix rounds or the gates' acceptance rules.

## Risks

- **Security:** the driver never picks a provider on the model's behalf: the brain backend is an explicit argument and the worker backend is the `--cli` the operator named.
- **Performance:** the gates run on `gpt-6.1-terra` at the same effort as before; the workers run on MiniMax. No extra spawns.
- **Migration:** none — the Claude and Codex runs keep their backend, model and effort (S6).
- **Rollback:** the Pi column and the brain-backend routing are one file and one flag; dropping them restores today's behaviour.

## Seams

- `skills/orchestrate/tests/test_run.py` (model selection and the spawn the driver sends) and `skills/orchestrate/tests/test_gates.py` (the reviewer and gaps-reviewer spawns), beside the existing fakes.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | The Pi backend is routable: `--cli` accepts `pi`, the class→model resolution reads the Pi column from the models file when present and from the skill's own table otherwise, and the worker's spawn carries `cli=pi` | S1, S2 | none | `skills/orchestrate/scripts/orchestrate.py`, `skills/orchestrate/references/models.md`, `skills/orchestrate/tests/` | regular | simple | agent | TO-DO |
| T2 | The brain tier: the reviewer and the gaps reviewer spawn on the brain backend with `gpt-6.1-terra`, while the implementer and the archive worker stay on the worker backend, and a Claude or Codex run changes nothing | S3, S4, S5, S6 | T1 | `skills/orchestrate/scripts/orchestrate.py`, `skills/orchestrate/tests/` | regular | simple | agent | TO-DO |
