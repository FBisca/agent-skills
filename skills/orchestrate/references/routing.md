# Routing

Every unit of work (a ticket, a review fix round, a chunk) routes by its **size** and **difficulty** to a **mode**, a model **class** and an **effort**. This file is the only place those terms are defined.

## Size

- **small**: fits one chunk: ≤~80 changed lines, ≤3 files, nothing to read beyond them.
- **regular**: within the ticket cap: ≤~800 lines, ≤~10 files.
- **big**: past either limit, or cutting across modules.

Calibration, 2026-11-06:
- Small models finished small units in 1–9 min each, red-first.
- A ticket of ~2,000 lines over 38 files cost a medium model 101M input tokens, with a 372k peak context.
- That ticket's fix round (17 findings over the same files) was given to a small model as one unit: 45 min, 0 edits.

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

The driver parses the "Model classes" table in `~/.claude/CLAUDE.md` (`--models-file`) and passes the cell's effort as `effort`. A class missing from the table is an error, not a fallback. The model is chosen at spawn, the cache boundary, so a fix round for a live worker keeps its model; a dead pane gets a fresh worker in the same cell.

## Escalation

A **unit** keeps one ID across every attempt at it: the first build and each fix round. The driver handles a known gate failure itself, up to two fix rounds. The unit's third failed gate, a worker that blocks or exits without a report, or conflicting reports go to a fresh large-class **decider**, which writes `decision.json` with one action from a fixed menu (the menu and schema live in `scripts/contracts.py`). The driver validates and applies it. A unit gets at most two decider calls; after that, and for any scope or product question, the ticket pauses for the user (`needs you: …` in its Status, and `attention.md`).

The user picks among the options in `attention.md`: one class up, re-plan, or split the unit. They answer by editing the plan.

`show --unit <id>` still sums a unit's failed review rounds and cutoffs for diagnosis.

## Changing a cell

Ledger rows record each unit's cell, model, review rounds and usage. Once at least 3 completed units in one cell show a better route, propose the change to the user with those rows. This file changes on their approval.
