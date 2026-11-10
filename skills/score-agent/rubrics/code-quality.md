# Code Quality and Design

**Question:** Is the change correct, production-safe, traceable, explicit, maintainable, and conceptually economical within the project's architecture?

| Label | Score | Decision anchor |
|---|---:|---|
| excellent | 1.0 | Correct and coherent, meaningful contracts, justified concepts, observable failures, no material issues. |
| good | 0.8 | Sound and safe; only isolated review-level issues with negligible impact. |
| problematic | 0.4 | Material design, correctness-risk, contract, observability, or unnecessary complexity issue requiring rework. |
| unacceptable | 0.2 | Demonstrated serious defect, production hazard, untraceable critical behaviour, or pervasive architectural damage. |

## Assess (each applicable criterion)

1. **Correctness and resilience:** Compare changed behaviour with acceptance criteria. Check relevant boundary conditions, errors, cancellations, retries, concurrent access, data consistency, backwards compatibility, and regression paths. Specify which risks are applicable; do not demand every category in every diff.
2. **Production safety:** Does the change preserve uptime, security, privacy, and data integrity? Are potentially disruptive operations guarded or reversible when relevant? Known critical risks are a **hard gate**, not merely a score penalty.
3. **Traceability / durable why:** Can a reviewer trace non-obvious behaviour to an invariant, requirement, test, or brief decision rationale? Would the reason behind a significant deviation remain comprehensible after the chat is gone? Do not demand comments for obvious code.
4. **Types as contracts:** Where the language supports them, do types enforce domain constraints and prevent invalid states, rather than just annotate permissive structures? Do not penalise dynamic-language code for lacking static types if runtime validation/contracts are appropriate.
5. **State modelling:** Are implicit states named and invalid combinations addressed? When logic depends on three or more interacting booleans, explicitly examine whether a discriminated union, state enum, or state machine would make illegal states unrepresentable. This is a review trigger, **not** an automatic abstraction requirement.
6. **Semantic naming:** Do predicates, functions and modules express domain intent (`isUserOfAge`) rather than obscure mechanics (`age > 18` repeated across callers)? Avoid renaming established idioms without a substantive gain.
7. **Conceptual complexity:** Count *new concepts, coupling, variants and rules*, not lines. Does each new abstraction, configuration, dependency or layer pay for itself in clearer invariants, reuse, or reduced complexity? A one-liner isn't better merely because it is shorter.
8. **Composition and cohesion:** Were suitable existing primitives considered before creating new ones? Are modules cohesive? Do functions avoid mixing orchestration intent and low-level implementation detail? Avoid speculative DRY abstractions across unrelated concepts.
9. **Observability:** Can meaningful runtime failure/state transitions be understood through appropriate metrics, traces, structured events or diagnostic signals? Logging alone is insufficient when correlation or externally legible state is needed. Judge proportionally: a pure function need not gain telemetry.
10. **Scope / repo fit:** Does the implementation respect established patterns and solve the requested problem without unrelated refactoring, premature generalisation, or overengineering? A deliberately incremental fix may be fully acceptable.

## Exceptions / non-penalties

- Necessary complexity that models a genuinely complex domain; more lines that improve clarity.
- A constrained incremental solution that reaches a sound threshold without redesigning the whole system.
- Existing project debt outside the changed scope, unless the change worsens or relies unsafely on it.
- Missing abstractions, telemetry, documentation, or types without a demonstrable requirement or risk.

## Calibration examples

- **1.0:** Change composes existing primitives, models mutually exclusive states explicitly, covers failure behaviour, and explains a non-obvious invariant.
- **0.8:** Correct change with one slightly ambiguous local name and no discernible effect on maintenance or runtime behaviour.
- **0.4:** Adds a generic framework for a one-off workflow, obscuring failure paths and introducing unnecessary states.
- **0.2:** Known data-loss path or critical outage risk is introduced and left unmitigated; also trigger hard gate.

## Required evidence

Reference changed code and relevant task constraints, trace the consequence of each issue, and state whether the concern is **proven** or **risk-based**. For potential defects without execution evidence, do not assert they occurred.
