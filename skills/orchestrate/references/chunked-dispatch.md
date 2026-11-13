# Chunked dispatch

**Manual only.** `orchestrate.py run` refuses `big` tickets; split them in the plan. Waits, timers, and checkpoints below are manual.

A large **planner** designs once; small **typists** implement self-contained briefs without reconnaissance. [Routing](routing.md) selects/routes chunks. Watch planner cost: calibration used ~339k tokens for 20 briefs.

## 1. Plan

A fresh-context large planner reads findings, gaps, Decisions, scenarios, and code. It writes only `<run>/<unit>/chunks/` briefs; it has no file ownership/ledger entry. Output:
- `Cnn.md`: one brief per chunk, each within the `small` size;
- `README.md`: the index, holding:
  - the order and dependencies;
  - each chunk's difficulty;
  - the final gate chunk;
- **Points to know**: brief↔scenario conflicts and judgement calls.

Resolve every Point inside its brief before the first chunk runs. The scenario wins unless the user decides otherwise.

Done when every finding or scenario sits in a chunk and no Point is open.

## 2. Brief

A self-contained brief names all worker reads: contract, brief, and listed files. Target ~60 lines (~100 with verbatim code).

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

Run sequentially in index order in the unit's checkout; tests compile shared source, so concurrent chunks break builds.

For each chunk:
1. **Reserve**: task `<unit>-Cnn` with `unit: <unit>`. Its `owns` is the brief's Files, its `checks` are the brief's Red and Green commands, and its route comes from the chunk's cell.
2. **Spawn** the cell's worker with: "Read <brief path> and follow it. You have 10 minutes." Bind the runtime ID.
3. **Wait** with `wait(all)` plus a 10-minute background **cutoff** timer. Messages arrive only on runtime tool calls; the timer enforces cutoff.
4. **Check** with git, no model. A miss fails the chunk.
   - the commit's files are within Files (`git show --name-only --format= <sha>`);
   - the S-ID test is in the diff;
   - `git status --porcelain` is empty.
5. **Close**: `checkpoint --report <run>/<unit>/chunks/Cnn.report.json`. On rejection, send the error and wait again. Stop the worker after COMPLETE.

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
