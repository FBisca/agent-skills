---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", wants integration tests, or when you are about to add, extend or prune tests.
---

# Test-Driven Development

TDD is the red → green loop, and it asks for **evidence** of behaviour, not a new test per change: the most regression protection for the least test code, maintenance and run time. Every section applies on every cycle: consult them before and during the loop, not after.

When exploring the codebase, read `GLOSSARY.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam a one-line note on what it catches and what it misses.

### The cheapest level

Each seam sits at a level; pick the lowest that reliably shows the behaviour:

- **Unit**: local decisions (state transitions, parsing, validation, scheduling and retry policies), in process.
- **Integration**: real boundaries (a subprocess, persistence, IPC, a server, the network), with fakes behind them.
- **End to end**: a few representative journeys that prove the whole system completes.

A higher level proves its boundary and leaves the cases to the level below: ten validation cases are one parametrised unit test plus one integration test showing a refusal crosses the boundary. Overlap across levels earns its place only when each level proves a different real boundary.

## Test admission

Before you write a test, answer each of these in one line:

1. Which observable behaviour or credible failure mode does it protect, tied to a requirement or a real risk?
2. Is it already covered: the same guarantee at the same boundary? Search the existing tests.
3. Can an existing test be extended or parametrised instead?
4. Is this the cheapest reliable level?
5. Would it fail on a regression someone could plausibly ship?

Admit the test only when all five hold; otherwise extend an existing test, or write none. When you report, name for each new test the behaviour it protects and why its level is the cheapest.

Before admitting a borderline test, or deleting, merging or moving any test, read [rules.md](rules.md): the admission and cost rules, each with its nuance.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed. An internal sequence is fair to assert when the sequence is the requirement ("refuse before anything launches").
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.
- **Proliferation**: tests that re-prove a guarantee another test already holds, often at a costlier level. The tell: the suite grows faster than the behaviour.

## Rules of the loop

- **Red before green.** Make a test go red first (a new admitted test, or an existing one extended), then write only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (see the `code-review` skill), not the red → green implementation cycle.
