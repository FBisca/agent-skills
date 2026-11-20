# Routing

Route each unit (ticket, fix round, chunk) by **size** and **difficulty** to **mode**, model **class**, and **effort**. Definitions live here.

## Size

- **small**: fits one chunk: ≤~80 changed lines, ≤3 files, nothing to read beyond them.
- **regular**: within the ticket cap: ≤~800 lines, ≤~10 files.
- **big**: past either limit, or cutting across modules.

Calibration (2026-11-06): small units took small models 1–9 min, red-first. A ~2,000-line/38-file ticket cost medium 101M input tokens (372k peak context); its 17-finding fix round given whole to small took 45 min with 0 edits.

## Difficulty

- **simple**: the change is settled; the work is writing it down.
- **complex**: open design inside the unit, or **sensitive** code: concurrency, auth, permissions, personal data, data migration, money, a public interface.

## Matrix

| Size | simple | complex |
|---|---|---|
| **small** | straight · small · low | straight · medium · medium |
| **regular** | straight · medium · medium | straight · medium · high |
| **big** | chunked · large planner · high | chunked · large planner · high |

- **straight**: one worker takes the whole unit.
- **chunked**: a large planner splits the unit into small chunks ([chunked dispatch](chunked-dispatch.md)). The driver does not run chunked units: it refuses a plan with a `big` ticket, so split it in the plan. Each chunk then routes through the **small** row on its own difficulty.
  - A chunk of a complex unit stays complex.
  - The planner marks a chunk simple only when the chunk touches nothing sensitive.
- Implementers are small or medium. The large class plans, reviews and decides.

## Lane

A request's size and difficulty also pick its **lane**, before any plan exists:

| Size | simple | complex |
|---|---|---|
| **small** | Direct | Plan |
| **regular** | Plan | Plan |
| **big** | Plan | Plan |

- **Direct**: build it directly in this session (a red test, the fix, the spec's requirement change, one PR) with no plan.
- **Plan**: run start-planning.

Judge the request from the request itself plus a glance at the code it names, and state the cell and why in one line. A lane only moves up. Propose moving a cell only after several requests in it support the change; edit this file after the user approves.

## Class to model

The driver resolves each class to backend, model and effort from a typed route file and reads no model table: `--routes-file`, else the repository's `.orchestrate/routes.json`, else the user's profile for `--cli`; `--route CLASS=BACKEND/MODEL[@EFFORT]` and `--step STEP=BACKEND/MODEL[@EFFORT]` win over all of them. Backends are `claude`, `codex` and `pi`. `<engine> run --help` holds the file paths and the format. A run with no route file, or an invalid one, stops before any spawn, with no billable fallback.

Model selection occurs at spawn (the cache boundary). Live workers keep their model for fixes; dead panes get fresh workers in the same cell.

## Escalation

A **unit** retains its ID across build/fix attempts. The driver handles known gate failures for up to two fix rounds. A third failed gate, worker that blocks or exits without a report, or conflicting reports invokes a fresh large **decider**. It writes `decision.json` from the fixed `contracts.py` menu; the driver validates/applies it. After two decider calls, or any scope/product question, pause for the user (`needs you: …`, `attention.md`).

Answer through the skill's *Resolve pauses* menu (e.g. class up, re-plan, split). Legacy Markdown Status cells: `TO-DO` retries the same unit; `COMPLETE` records manual completion.

**Idle window:** runtime `working` starts a window on its first counted tick; ticks skip it until `--working-minutes` elapses. Any uncounted tick clears the window; restart resets it. Requests show duration. `--idle-minutes` sets ticks: no agent/CI progress means idle; two consecutive idle ticks ask the Lead.

`show --unit <id>` sums failed review rounds/cutoffs for diagnosis.

## Changing a cell

Ledger rows record cell, model, review rounds, and usage. After ≥3 completed units in a cell support a better route, propose it with those rows; edit this file after user approval.
