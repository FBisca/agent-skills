# Execution Efficiency

**Question:** Did the agent take a direct, evidence-driven path to a sufficiently verified result without avoidable tool cost, looping, context waste or human rework?

| Label | Score | Decision anchor |
|---|---:|---|
| highly_efficient | 1.0 | Relevant inspection, purposeful operations, targeted checks, proportionate final verification, minimal rework. |
| mostly_efficient | 0.8 | One or two minor detours with no meaningful knock-on cost. |
| inefficient | 0.4 | Repeated reads/runs, preventable mistakes, unnecessary broad tests or retries with material cost. |
| wasteful | 0.2 | Extended loops, repeated unchanged failures, major rework or overhead dominates the run. |

## Assess (each applicable criterion)

1. **Targeted investigation:** Did the agent inspect task instructions, relevant code, patterns and test entry points **before** consequential edits? Penalise speculative implementation that necessitated avoidable rework, not deliberate quick inspection.
2. **Repeated reads:** Flag reopening the same unchanged file/output without a new question or changed state. Reading again after a relevant edit or to inspect another section is legitimate.
3. **Test selection:** During iteration, prefer narrow checks that can answer the current question. Use broader/full-suite checks for integration confidence, required CI, release safety, or final validation as justified by the change. Full-suite runs are not inherently waste.
4. **Failure diagnosis and retry:** After failure, does the next action test a new hypothesis or change a relevant condition? Repeating a failing command with no meaningful change is a loop. A controlled retry for documented flakiness may be warranted.
5. **Independent work batching:** Could independent file reads, searches, checks, or edits be combined safely without obscuring feedback? Do not reward parallel work that introduces races, hides failure signals, or breaks ordered dependencies.
6. **Context and tool economy:** Detect irrelevant wide file dumps, excessive searches, verbose tool outputs, or unnecessary agent delegation. Prefer bounded reads and targeted symbols when possible; do not penalise sufficient context gathering.
7. **Avoidable rework:** Identify edits reverted due to overlooked constraints, missed existing abstractions, or failure to inspect an error. Distinguish exploration that revealed new evidence from preventable churn.
8. **Human intervention burden:** Did the agent repeatedly ask settled questions, need avoidable corrections, or hand back solvable issues? Separate missing user decisions from failures the agent should resolve autonomously.
9. **Cost and verification balance:** Consider time, tokens, commands and number of correction cycles **only when evidenced**. An agent that skips essential tests is not highly efficient merely because it used fewer steps.

## Exceptions / non-penalties

- TDD red-green-refactor cycles, provided each repeated run is tied to a code change or diagnostic hypothesis.
- New error information, changed files, flaky external systems, or necessary environment recovery justifying a retry.
- Safety-critical investigation, mandatory checks, and broad final verification proportional to risk.
- Work caused by changed requirements, unavailable access, or external failure; attribute correctly.

## Calibration examples

- **1.0:** Reads relevant code once, edits narrowly, runs focused tests during iteration and broad checks at completion.
- **0.8:** Repeats one small search and an early test run; no material delay.
- **0.4:** Runs a six-minute suite after every tiny edit despite a sufficient ten-second focused test.
- **0.2:** Repeats the same failing command for several cycles without changing inputs or diagnosing the failure.

## Required evidence

Give the **ordered action sequence** (commands/messages) establishing avoidable work and the counterfactual efficient path. Quote actual costs when known; do not infer minutes or tokens from a transcript lacking metrics.

## Scoring protocol

Score **observed behaviour**, not presumed intentions. Use only `1.0`, `0.8`, `0.4`, `0.2`, or `N/A` (`insufficient_evidence`). Choose the **lowest anchor supported by material evidence**; multiple minor issues may become material if their combined cost is significant. Never average subchecks or invent unobserved failures. For every deduction, cite a message, action, command, file/line, or test and explain its consequence. Separate **observed failure** from **potential risk**. Mark an inapplicable subcheck `not_applicable`, not a defect. A passing outcome alone does not prove a good process; a failed outcome alone does not prove a bad process. A critical safety/integrity breach is handled by the agent skill's hard gates, independent of this score.
