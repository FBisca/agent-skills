# Chunked dispatch

A cheap model makes a good **typist** and a poor planner. A strong planner does all the design once and writes one complete **chunk brief** per change. Each `brief`-tier worker then executes one brief with no reconnaissance. Use this for `brief`-tier tickets and for any review fix round with more than ~5 findings.

Evidence (Rastro, 2026-11-06): one MiniMax worker given a whole 17-finding fix round ran 45 min, used ~180k thinking tokens and made 0 edits. The same round, split by an Opus planner into 20 chunks, landed each chunk in 1–9 min, red-first, touching only its own files. The planner itself took ~339k tokens and 27 min. Whether the total costs less is unproven until the ledger shows it.

## 1. Plan

Dispatch one fresh-context Opus subagent as the **planner**. It reads the review findings, the gap review, the plan's Decisions and scenarios, and the code. It edits nothing. It writes, into the scratchpad:

- one brief per chunk, `Cnn.md`;
- an index `README.md` with the order, dependencies, serial chains per shared file, parallel waves (at most 3 chunks each), each chunk's scheduling class, and a final gate chunk;
- a "Points to know" list: anything where a brief and a scenario disagree, or where a fix depends on a judgement call.

Rules the planner follows:
- It designs the hard fixes itself, so they ship as concrete steps.
- It splits any chunk that would change more than ~80 lines or touch more than 2–3 files.
- Briefs stay under ~60 lines. Briefs that carry subtle code verbatim may reach ~100.

Plan the whole round before the first wave starts. Read "Points to know" and resolve every brief↔scenario conflict in the brief before dispatch. The scenario wins unless you take it to the user.

Done when every finding is in some chunk and every conflict on the list is resolved.

## 2. The brief

Each brief carries everything the worker needs:

```
# Cnn — <one-line change>
Checkout …  Needs: <chunks>.  Class: S | T | L.  No reconnaissance.
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

- A **guard test** covers behaviour that should already work. It is marked "expected green; if red, stop and report".
- Restored test names come from `git show origin/main:<file>`.
- The commit is `git add <files> && git commit -m "<msg>" -- <files>`. The pathspec keeps parallel commits apart.

## 3. Schedule

"Files don't overlap" is not enough, because a test command compiles shared source. Each chunk gets a class in the index:

- **S**: edits shared or core source (the planner names those modules for this repo). It runs alone, since a half-edited S chunk breaks every build running beside it.
- **T**: edits test files only. It may run beside another T or an L.
- **L**: edits one leaf module and its tests. At most one L per leaf at a time.
- Chunks that touch the same file form a serial chain in index order.

## 4. Dispatch loop

Per chunk:

1. **Reserve** it in the ledger. The packet's `owns` is the brief's `Files:` line, `tier` is `brief`, and `model` and `effort` are what the spawn uses.
2. **Spawn** with `spawn(kind="worker", cli="minimax", effort="low", cwd=<worktree>, task=…)` and the task text: "Do exactly what <brief path> says. Read only that file and the files it names. The brief is complete: edit right away. Touch only your files; commit with the pathspec. You have 10 minutes. Report complete or blocked with the red line, green summary and sha." Bind the runtime ID.
3. **Wait** with `wait(all)` and a background 10-minute timer. A message reaches the worker only when it next calls a runtime tool, so the timer is the cutoff, not a message.
4. **Check** the chunk mechanically, with no model:
   - `git show --name-only --format= <sha>` lists only the brief's `Files:`;
   - the S-ID test name appears in the diff;
   - `git status --porcelain` is empty.
   Any miss sends the chunk back as failed.
5. **Close**: stop the worker, checkpoint `COMPLETE <sha>` with `review_rounds: 0` and its usage line, then reserve the next chunk.

**On timeout:**
1. Stop the worker.
2. Save its uncommitted diff to the scratchpad as `Cnn.timeout.patch`, then restore the worktree to the last chunk commit.
3. Have the planner re-split that chunk once.
4. If a re-split chunk also times out, run it at the `standard` tier.

## 5. Final gate chunk

Run the full formatter, linter and test suite, then `converge --ticket T<n>`, then push (never forced). The Opus review and CI follow as usual. The review's own findings start a new round at step 1.

Done when the final gate passes and every chunk is COMPLETE in the ledger.
