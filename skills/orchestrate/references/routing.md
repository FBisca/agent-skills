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

## Class to model

Resolve class → backend/model/effort:

- **Typed config** (`--routes-file`): versioned JSON (YAML requires PyYAML), schema in engine `routes.py`. Unknown backends/classes/fields/efforts or missing classes stop the run before spawn, without billable fallback.

  ```json
  {"version": 1,
   "routes": [
     {"class": "small",  "backend": "claude", "model": "haiku",  "effort": "low"},
     {"class": "medium", "backend": "claude", "model": "sonnet", "effort": "medium"},
     {"class": "large",  "backend": "codex",  "model": "gpt-l",   "effort": "high"}
   ]}
  ```

  Workers support `claude` and `codex`. `pi` is lead-only; Pi worker routes fail explicitly without substitution. A named config is self-sufficient: the legacy table is never read or required.

- **Legacy default** (`--models-file`): `Model classes` in `~/.claude/CLAUDE.md`; used without `--routes-file`, with a deprecation notice. Effort comes from the matrix. Missing classes/backend columns—including `--brain-cli`'s—are errors.

Model selection occurs at spawn (the cache boundary). Live workers keep their model for fixes; dead panes get fresh workers in the same cell.

## Escalation

A **unit** retains its ID across build/fix attempts. The driver handles known gate failures for up to two fix rounds. A third failed gate, worker that blocks or exits without a report, or conflicting reports invokes a fresh large **decider**. It writes `decision.json` from the fixed `contracts.py` menu; the driver validates/applies it. After two decider calls, or any scope/product question, pause for the user (`needs you: …`, `attention.md`).

Answer through the skill's *Resolve pauses* menu (e.g. class up, re-plan, split). Legacy Markdown Status cells: `TO-DO` retries the same unit; `COMPLETE` records manual completion.

**Idle window:** runtime `working` starts a window on its first counted tick; ticks skip it until `--working-minutes` elapses. Any uncounted tick clears the window; restart resets it. Requests show duration. `--idle-minutes` sets ticks: no agent/CI progress means idle; two consecutive idle ticks ask the Lead.

`show --unit <id>` sums failed review rounds/cutoffs for diagnosis.

## Changing a cell

Ledger rows record cell, model, review rounds, and usage. After ≥3 completed units in a cell support a better route, propose it with those rows; edit this file after user approval.
