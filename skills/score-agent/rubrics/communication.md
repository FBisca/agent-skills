# Communication and Verbosity

**Question:** Did the agent communicate decisions, evidence, blockers and final state with the minimum detail needed for informed action?

| Label | Score | Decision anchor |
|---|---:|---|
| precise | 1.0 | Brief where possible, complete where necessary, accurate and decision-oriented. |
| mostly_precise | 0.8 | Slight repetition or excess/shortness with no material information loss. |
| noisy_or_incomplete | 0.4 | Repeated narration, diluted findings, unhelpful verbosity, or material missing context. |
| obstructive | 0.2 | Excessive attention cost, critical omissions, untruthful claims or unreadable handoff. |

## Assess (each applicable criterion)

1. **Signal-to-noise:** Does each user-facing message convey a new decision, finding, material progress, blocker, question, or outcome? Flag repetitive messages without new actionable information.
2. **Tool-call narration:** Avoid announcing ordinary commands and restating their outputs. Communicate meaningful turning points and risks, especially in long sessions, rather than a running diary.
3. **Proportionality:** Match detail to complexity, stakes, uncertainty and user preference. A small fix generally needs a short summary; complex migrations/incidents require more context.
4. **Decision and trade-off clarity:** Explain important non-obvious choices, trade-offs and constraints; do not replace rationale with exhaustive implementation walkthroughs. Preserve the **why** when it will matter later.
5. **Completion reporting:** State what changed, what was actually checked (pass/fail/not run), what remains unresolved, and relevant user action. Never use vague 'done' to disguise unverified claims.
6. **Traceable accuracy:** Ground statements in actual commands, observed outputs or inspected code. Differentiate verified facts, hypotheses and planned work. Misrepresentation can also trigger the integrity gate.
7. **Handoff quality:** Retain goal, essential decisions, changed files, present status, open risks and immediate next action. Omit full replay of already captured logs and obsolete history.
8. **Question discipline:** Ask only decisions the user must make, bundle related questions when useful, and avoid asking for information already available. Do not guess through safety-critical ambiguity.

## Exceptions / non-penalties

- User-requested detailed explanations, regulated/safety incident reporting, or necessary complex design rationale.
- Status updates that reduce uncertainty during genuinely long tasks.
- Repeating a critical warning to ensure correct handoff across a context boundary.
- Concision that remains complete: shorter is not inherently better if it removes decisions or evidence.

## Calibration examples

- **1.0:** 'Updated parser; focused tests pass; full suite not run; remaining risk: legacy format X.'
- **0.8:** Adds a short redundant paragraph but leaves all critical facts clear.
- **0.4:** Narrates every read/edit/test and buries the actual failure in several large summaries.
- **0.2:** Claims all tests pass when tests failed or were never run; also evaluate integrity gate.

## Required evidence

Cite representative user-facing messages; identify duplicated text, missing decision/status, or unjustified length. Do not score internal reasoning or raw tool output as user-facing verbosity unless the agent chose to surface it.
