# Chunked dispatch

A small model makes a good **typist** and a poor planner. So a large **planner** does all the design once and writes one complete **chunk brief** per change, and each chunk's worker executes its brief with no reconnaissance. [Routing](routing.md) sends `big` units here, and each chunk routes back through its small row.

The calibration is in [routing](routing.md#size). The planner is the cost to watch: on the calibration fix round it took ~339k tokens and 27 min to write 20 briefs. Whether the whole run costs less is open until the ledger shows it.

## 1. Plan

Dispatch one fresh-context large-class subagent as the planner. It reads the review findings, the gap review, the plan's Decisions and scenarios, and the code. It edits nothing. It writes, into the scratchpad:

- one brief per chunk, `Cnn.md`;
- an index `README.md` with:
  - the order and dependencies;
  - serial chains per shared file;
  - parallel waves, at most 3 chunks each;
  - each chunk's scheduling class and difficulty;
  - a final gate chunk;
- a "Points to know" list: anything where a brief and a scenario disagree, or where a fix depends on a judgement call.

The planner designs the hard fixes itself, so they ship as concrete steps. It splits any chunk that would grow past the `small` size. Briefs stay under ~60 lines, or ~100 when they carry subtle code verbatim.

Plan the whole unit before the first wave starts. Read "Points to know" and resolve every brief↔scenario conflict in the brief before dispatch. The scenario wins unless you take it to the user.

Done when every finding or scenario is in some chunk and every conflict on the list is resolved.

## 2. The brief

Each brief carries everything the worker needs:

```
# Cnn — <one-line change>
Checkout …  Needs: <chunks>.  Class: S | T | L.  Difficulty: simple | complex.  No reconnaissance.
Files (edit only these): `a.rs`, `b.rs`.
Why: <one sentence, with the finding or scenario id>
## Rules     red-first; pathspec commit; formatter; focused commands only; no push
## 1. Tests (red)   exact replace-this-with-that at line anchors, with the current code quoted;
                    test named with its S-ID; which existing test or helper to copy setup from;
                    the one command that must FAIL
## 2. Fix           exact code, or full pseudo-code where the logic is subtle
## 3. Green         the focused command that must pass, plus the linter on the touched module
Commit: `<conventional message>`   Report: red line, green summary, sha
```

- A **guard test** covers behaviour that should already work. Mark it "expected green; if red, stop and report".
- Restored test names come from `git show origin/main:<file>`.
- The commit is `git add <files> && git commit -m "<msg>" -- <files>`. The pathspec keeps parallel commits apart.

## 3. Schedule

A test command compiles shared source, so chunks that touch different files can still break each other. Each chunk gets a scheduling class in the index:

- **S** (shared or core source; the planner names those modules for the repo): runs alone. A half-edited S chunk breaks every build running beside it.
- **T** (test files only): may run beside another T or an L.
- **L** (one leaf module and its tests): at most one L per leaf at a time.
- Chunks touching the same file form a serial chain, in index order.

## 4. Dispatch loop

For each chunk:

1. **Reserve** it in the ledger. The packet's `owns` is the brief's `Files:` line; its route fields come from the chunk's cell.
2. **Spawn** a worker with the arguments that cell resolves to. Task text: "Do exactly what <brief path> says. Read only that file and the files it names. The brief is complete: edit right away. Touch only your files; commit with the pathspec. You have 10 minutes. Report complete or blocked with the red line, green summary and sha." Bind the runtime ID.
3. **Wait** with `wait(all)` plus a background 10-minute timer. A message reaches the worker only when it next calls a runtime tool, so the timer is the cutoff.
4. **Check** with git, no model:
   - `git show --name-only --format= <sha>` lists only the brief's `Files:`;
   - the S-ID test name appears in the diff;
   - `git status --porcelain` is empty.
   Any miss counts as a failed chunk.
5. **Close**: stop the worker, then checkpoint `COMPLETE <sha>` with `review_rounds: 0` and its usage line. Reserve the next chunk.

**On timeout:**
1. Stop the worker.
2. Save its uncommitted diff to the scratchpad as `Cnn.timeout.patch`.
3. Restore the worktree to the last chunk commit.
4. Have the planner re-split the chunk once.
5. If a re-split chunk times out too, follow [escalation](routing.md#escalation).

## 5. Final gate chunk

Run the full formatter, linter and test suite, then `converge --ticket T<n>`, then push (never forced). The large review and CI follow as usual. The review's findings form a new unit, routed afresh.

Done when the final gate passes and every chunk is COMPLETE in the ledger.
