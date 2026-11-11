# Chunked dispatch

**The driver does not run chunked units.** `orchestrate.py run` refuses a plan with a `big` ticket: split it in the plan. This file describes a hand-driven run only; its wait, timer and checkpoint steps are manual commands, not driver behavior.

A small model is a good **typist** and a poor planner. So a large **planner** designs once and writes one **brief** per chunk, and each chunk's worker types its brief with no reconnaissance. [Routing](routing.md) decides which units are chunked and routes each chunk. The planner is the cost to watch: on the calibration round it used ~339k tokens for 20 briefs.

## 1. Plan

One fresh-context large-class planner reads the findings, the gap review, the Decisions, the scenarios and the code. It writes briefs only under `<run>/<unit>/chunks/`. It owns no files, so it never enters the ledger; only chunks do. Its output:
- `Cnn.md`: one brief per chunk, each within the `small` size;
- `README.md`: the index, holding:
  - the order and dependencies;
  - each chunk's difficulty;
  - the final gate chunk;
- **Points to know**: brief↔scenario conflicts and judgement calls.

Resolve every Point inside its brief before the first chunk runs. The scenario wins unless the user decides otherwise.

Done when every finding or scenario sits in a chunk and no Point is open.

## 2. Brief

A brief is complete: the worker reads only the contract, the brief and the files the brief names. It runs to ~60 lines, or ~100 with verbatim code.

```
# Cnn — <change>
Contract: <run>/contract.md   (read first)
Task: <unit>-Cnn · Needs: <chunks> · Difficulty: simple|complex
Files: `a.rs`, `b.rs`   (edit only these)
Why: <finding or scenario id>
1. Red: exact edits at line anchors (current code quoted); test named with its S-ID; setup copied from <test>; the command that must fail
2. Fix: exact code, or full pseudo-code where subtle
3. Green: the focused command, plus the linter on the touched module
Commit: git add <Files> && git commit -m "<msg>" -- <Files>   (no push)
Report: <run>/<unit>/chunks/Cnn.report.json in the contract's shape; its checks are the Red and Green commands
```

- A **guard test** covers behaviour that should already pass. Mark it "expected green; red means stop and report".
- Restore old test names from `git show origin/main:<file>`.

## 3. Run chunks in sequence

Chunks run one at a time in the unit's checkout, in index order. A test command compiles shared source, so concurrent chunks would break each other's builds.

For each chunk:
1. **Reserve**: task `<unit>-Cnn` with `unit: <unit>`. Its `owns` is the brief's Files, its `checks` are the brief's Red and Green commands, and its route comes from the chunk's cell.
2. **Spawn** the cell's worker with: "Read <brief path> and follow it. You have 10 minutes." Bind the runtime ID.
3. **Wait** with `wait(all)` and a 10-minute background timer as the **cutoff**. A message reaches a worker only on its next runtime tool call, so only the timer enforces the cutoff.
4. **Check** with git, no model. A miss fails the chunk.
   - the commit's files are within Files (`git show --name-only --format= <sha>`);
   - the S-ID test is in the diff;
   - `git status --porcelain` is empty.
5. **Close**: `checkpoint --report <run>/<unit>/chunks/Cnn.report.json`. If the helper rejects the report, send its error to the worker and wait again. Stop the worker once the checkpoint is COMPLETE.

**When the cutoff hits:**
1. Stop the worker.
2. Save its diff as `chunks/Cnn.timeout.patch`.
3. Restore the last chunk commit.
4. Release the task with `--cutoff`.
5. The planner re-splits the chunk once.
6. When `show --unit` reports `escalate`, follow [escalation](routing.md#escalation).

## 4. Final gate

Run the full formatter, linter and suite, check the diff stays in the ticket's Paths, then push (never forced). The large review and CI follow. Their findings are a fix round for the same unit.

Done when the gate passes and every chunk is COMPLETE.
