# Chunked dispatch

A small model is a good **typist** and a poor planner. So a large **planner** designs once and writes one **brief** per chunk, and each chunk's worker types its brief with no reconnaissance. [Routing](routing.md) sends `big` units here, and each chunk routes back through the `small` row. The planner is the cost to watch: on the calibration round it used ~339k tokens for 20 briefs.

## 1. Plan

One fresh-context large-class planner reads the findings, the gap review, the Decisions, the scenarios and the code. It edits nothing. It writes to the scratchpad:
- `Cnn.md`: one brief per chunk, each within the `small` size;
- `README.md`: the index, holding:
  - the order and dependencies;
  - **serial chains** (chunks that share a file);
  - **waves** of at most 3 chunks;
  - each chunk's schedule class and difficulty;
  - the final gate chunk;
- **Points to know**: brief↔scenario conflicts and judgement calls.

Resolve every Point inside its brief before the first wave. The scenario wins unless the user decides otherwise.

Done when every finding or scenario sits in a chunk and no Point is open.

## 2. Brief

A brief is complete: the worker reads only the brief and the files it names. It runs to ~60 lines, or ~100 with verbatim code.

```
# Cnn — <change>
Needs: <chunks> · Class: S|T|L · Difficulty: simple|complex
Files: `a.rs`, `b.rs`   (edit only these)
Why: <finding or scenario id>
1. Red: exact edits at line anchors (current code quoted); test named with its S-ID; setup copied from <test>; the command that must fail
2. Fix: exact code, or full pseudo-code where subtle
3. Green: the focused command, plus the linter on the touched module
Commit: git add <Files> && git commit -m "<msg>" -- <Files>   (no push)
Report: red line, green summary, sha
```

- A **guard test** covers behaviour that should already pass. Mark it "expected green; red means stop and report".
- Restore old test names from `git show origin/main:<file>`.

## 3. Schedule

A test command compiles shared source, so chunks with disjoint files can still collide:
- **S**: shared or core source, which the planner names for each repo. Runs alone.
- **T**: tests only. Runs beside a T or an L.
- **L**: one leaf module and its tests. One at a time per leaf.

## 4. Dispatch each chunk

1. **Reserve**: the packet's `owns` is the brief's Files, and its route comes from the chunk's cell.
2. **Spawn** the cell's worker with: "Do exactly what <brief path> says. The brief is complete: edit right away. You have 10 minutes. Report complete or blocked." Bind the runtime ID.
3. **Wait** with `wait(all)` and a 10-minute background timer as the **cutoff**. A message reaches a worker only on its next runtime tool call, so only the timer enforces the cutoff.
4. **Check** with git, no model. A miss fails the chunk.
   - the commit's files are within Files (`git show --name-only --format= <sha>`);
   - the S-ID test is in the diff;
   - `git status --porcelain` is empty.
5. **Close**: stop the worker, then checkpoint COMPLETE with the sha, `review_rounds: 0` and the chunk's usage.

**When the cutoff hits:**
1. Stop the worker.
2. Save its diff as `Cnn.timeout.patch`.
3. Restore the last chunk commit.
4. The planner re-splits the chunk once.
5. A second cutoff goes to [escalation](routing.md#escalation).

## 5. Final gate

Run the full formatter, linter and suite, then `converge --ticket T<n>`, then push (never forced). The large review and CI follow. Their findings form a new unit, routed afresh.

Done when the gate passes and every chunk is COMPLETE.
