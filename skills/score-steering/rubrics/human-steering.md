# Human Steering Quality (advisory; independent)

**Question:** Did the human's **controllable** instructions and interventions help the coding agent converge while preserving appropriate autonomy, clarity and verification?

| Label | Score | Decision anchor |
|---|---:|---|
| effective | 1.0 | Clear outcome and constraints; sensible delegation; well-timed evidence-based interventions. |
| mostly_effective | 0.8 | Minor controllable ambiguity or unnecessary intervention with limited observable impact. |
| counterproductive | 0.4 | Vague corrections, inconsistent direction or micromanagement causes material avoidable rework. |
| disruptive | 0.2 | Repeated contradictions/interventions derail work or make completion materially less likely. |

## Assess (each applicable criterion)

1. **Intent clarity:** Does the instruction express the desired outcome, business/engineering problem, and what success would look like? Outcomes can be clear without specifying implementation steps. Do not penalise an appropriately exploratory task.
2. **Constraints and invariants:** Did the human state *non-obvious, known, material* requirements (e.g. preserve coverage; do not change public API) when they mattered? Do not require the user to restate basic engineering obligations, repo guidance, or facts the agent could discover.
3. **Context quality:** Did they supply necessary domain knowledge, decisions and access while avoiding irrelevant prompt dumps or contradictory rules? Evaluate available context at the time, not an ideal omniscient prompt.
4. **Intervention timing:** Did a correction follow new evidence, observed risk or a real blockage? Penalise interruptions only when they demonstrably redirected productive work or increased cost. An intervention preventing harm is valid even if inconvenient.
5. **Appropriate autonomy:** Did the user delegate reversible implementation details while retaining high-stakes or irreversible decisions? Giving a specific implementation choice is not micromanagement when it reflects an intentional constraint.
6. **Feedback quality:** Did a correction describe the mismatch, evidence, or broken invariant rather than just 'wrong, redo'? When the issue is obvious, concise corrective feedback can be adequate.
7. **Decision consistency:** Were changed requirements explicitly identified, so the agent could distinguish new direction from previous constraints? Direction changes based on new discovery are legitimate.
8. **Verification discipline:** Did the user seek evidence proportional to risk before accepting? Avoid demanding redundant full suites or accepting obviously unverified critical changes. This is not a transfer of the agent's own duty to verify.
9. **Learning opportunity:** Identify one *controllable*, transferable improvement and propose the shortest better wording or action. If human steering was good, say 'none evidenced' rather than inventing criticism.

## Causality and responsibility rules

- Judge the human **only against information they reasonably knew at that turn**. Do not use hindsight from later failures as proof the initial instruction was defective.
- Attribute each observed issue as `human`, `agent`, `shared`, or `external`, with confidence (`high|medium|low`). A bad agent response does not itself prove bad steering.
- Distinguish **ambiguity** (multiple reasonable interpretations), **missing known constraint**, and **reasonable agent inference**. Show how the alternative wording would have prevented the specific observed detour; if speculative, mark low confidence.
- Do not reward long, overconstrained prompts. Do not penalise a human for expecting the agent to protect data, tests, or established repo contracts without being reminded.
- This score **never** contributes to agent weighted score, and **never** triggers automated prompt, skill or config changes.

## Calibration examples

- **1.0:** 'Reduce test feedback time while preserving behavioural coverage. Inspect test distribution and propose the smallest change.' Corrects only after observing a specific issue.
- **0.8:** 'Make tests faster' omits a project-specific requirement later clarified, causing a small avoidable detour; only deduct if there is evidence the user knew it mattered and the agent reasonably couldn't infer it.
- **0.4:** Repeatedly changes acceptance criteria without identifying the changes, causing the agent to revert completed work.
- **0.2:** Consistently issues mutually incompatible instructions and insists on unsafe shortcuts after risks are explained.

## Required evidence and output

Cite the human message and the **information available at that moment**, then link it to observed agent behaviour and consequences. Provide one effective choice, at most one improvement opportunity, a better concise intervention, responsibility and confidence. If no human-controlled problem is supported, give full credit or `N/A` depending on coverage; do not force a lesson.

## Scoring protocol

Score **observed behaviour**, not presumed intentions. Use only `1.0`, `0.8`, `0.4`, `0.2`, or `N/A` (`insufficient_evidence`). Choose the **lowest anchor supported by material evidence**; multiple minor issues may become material if their combined cost is significant. Never average subchecks or invent unobserved failures. For every deduction, cite a message, action, command, file/line, or test and explain its consequence. Separate **observed failure** from **potential risk**. Mark an inapplicable subcheck `not_applicable`, not a defect. A passing outcome alone does not prove a good process; a failed outcome alone does not prove a bad process. A critical safety/integrity breach is handled by the agent skill's hard gates, independent of this score.
