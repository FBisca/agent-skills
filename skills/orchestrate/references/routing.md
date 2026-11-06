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
- **chunked**: a large planner splits the unit into small chunks ([chunked dispatch](chunked-dispatch.md)). Each chunk then routes through the **small** row on its own difficulty.
  - A chunk of a complex unit stays complex.
  - The planner marks a chunk simple only when the chunk touches nothing sensitive.
- Implementers are small or medium. The large class plans, reviews and decides.

## Class to model

Resolve a class to spawn arguments in this order:
1. what the user said in this session;
2. the "Model classes" map in the session's loaded instructions (`AGENTS.md` / `CLAUDE.md`);
3. the session's own model.

Pass the cell's effort as `effort`. The model is chosen at spawn, the cache boundary, so resume a worker only for a unit in the same cell.

## Escalation

A **unit** keeps one ID across every attempt at it: the first build, each fix round, each chunk. `show --unit <id>` sums its failed review rounds and cutoffs over all attempts. When it reports `escalate` (two of either), stop the worker and ask the user. Bring:
- the evidence: findings, cutoffs, usage;
- the options: one class up, re-plan with the large planner, or split the unit.

The user picks. Release the attempt and reclaim the unit under a new task ID with the chosen route; the new packet's `escalation` field records the choice.

## Changing a cell

Ledger rows record each unit's cell, model, review rounds and usage. Once at least 3 completed units in one cell show a better route, propose the change to the user with those rows. This file changes on their approval.
