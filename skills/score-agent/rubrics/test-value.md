# Test Value and Redundancy

**Question:** Does the test change provide distinct, risk-proportionate confidence at an appropriate level and maintenance/runtime cost, without sacrificing meaningful coverage?

| Label | Score | Decision anchor |
|---|---:|---|
| purposeful | 1.0 | Each meaningful test protects a distinct behaviour, boundary, or risk at the cheapest sufficient level; feedback is reliable. |
| mostly_purposeful | 0.8 | Minor overlapping coverage or extra setup without material runtime/maintenance cost or gaps. |
| redundant | 0.4 | Multiple duplicative invariants, excessive integration-level tests, brittle internals, or meaningful feedback cost. |
| excessive_or_weak | 0.2 | Test proliferation dominates, suite becomes impractical, or critical behaviour is left unprotected despite high test volume. |

## Assess (each applicable criterion)

1. **Behavioural uniqueness:** For each added/modified test, identify the **behaviour, invariant, boundary, risk, or regression** it protects. Two tests are redundant only when they prove essentially the same guarantee at the same effective boundary and neither adds meaningful independent signal. Merely using different input data does not imply independent value; parameterised edge cases may all be valuable.
2. **Level selection:** Use unit tests for local decisions, integration tests for real interfaces/boundaries, E2E for critical journeys. Flag expensive integration/E2E tests that only re-prove local pure logic with no additional boundary confidence.
3. **Duplication and ownership:** Detect repeated assertions across nearby cases, multiple suites asserting the same invariant, repeated fixtures/setup, and redundant snapshots. Explain **which tests could be merged or moved** and what confidence would remain.
4. **Implementation coupling:** Prefer public behaviour and contracts over private methods, incidental mocking, exact call ordering, or internal data layouts unless the internal sequence itself is the requirement.
5. **Execution cost:** Compare incremental runtime, resource use, flakiness, and maintenance cost against risk protected. Use measured timings when available; otherwise describe cost qualitatively and mark uncertainty. Distinguish slow tests from wasteful *repeated execution* (the latter belongs primarily to efficiency).
6. **Coverage sufficiency:** Check meaningful happy paths, negative paths, invalid inputs, boundaries, error handling, state transitions, concurrency or regressions **when relevant**. High coverage percentage alone does not establish good tests.
7. **Determinism and isolation:** Identify network/time/order-dependent tests, shared state, unbounded waits, arbitrary sleeps and fragile fixtures. Check if a simpler fake or deterministic clock would preserve intent.
8. **Proportionality:** Is infrastructure justified for the change size and risk? Do not impose test count quotas or demand one test per line/function.

## Exceptions / non-penalties

- Deliberately overlapping tests at **different real boundaries** (e.g. unit contract + one API integration + a critical E2E flow).
- Regression tests for separately observed failures, even with superficially similar assertions.
- TDD's repeated **runs** do not imply redundant **test cases**; score those runs in efficiency.
- Required safety/contract/E2E coverage, even when slower; deleting useful coverage to optimise speed is not an improvement.
- A documentation-only change with legitimately no new tests: assess whether tests were actually warranted; mark unrelated checks not applicable.

## Calibration examples

- **1.0:** Two parameterised unit cases for local validation and one integration test for the service boundary, with distinct failure signals.
- **0.8:** One overlapping negative case adds little but is cheap and does not obscure the suite.
- **0.4:** Six slow integration tests each duplicate a local validation invariant; one boundary test plus fast unit cases would preserve confidence.
- **0.2:** Dozens of brittle tests assert mocks' call sequences but miss an important user-visible failure case and materially slow the suite.

## Required evidence

Name specific test cases/files and their protected guarantees. For alleged redundancy, show **overlap and retained confidence**; for gaps, tie the missing case to a real requirement/risk. Record timing only if observed.

## Scoring protocol

Score **observed behaviour**, not presumed intentions. Use only `1.0`, `0.8`, `0.4`, `0.2`, or `N/A` (`insufficient_evidence`). Choose the **lowest anchor supported by material evidence**; multiple minor issues may become material if their combined cost is significant. Never average subchecks or invent unobserved failures. For every deduction, cite a message, action, command, file/line, or test and explain its consequence. Separate **observed failure** from **potential risk**. Mark an inapplicable subcheck `not_applicable`, not a defect. A passing outcome alone does not prove a good process; a failed outcome alone does not prove a bad process. A critical safety/integrity breach is handled by the agent skill's hard gates, independent of this score.
