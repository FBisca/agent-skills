---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", wants integration tests, or when you are about to add, extend or prune tests.
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, which tests earn admission, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

TDD asks for **evidence** of behaviour, not a new test for every change. The goal is the most regression protection for the least test code, maintenance and run time. A red that comes from extending an existing test is as good as a red from a new one.

When exploring the codebase, read `GLOSSARY.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam a one-line note on what it catches and what it misses.

### The cheapest level that proves it

Each seam sits at a level. Pick the lowest level that reliably shows the behaviour:

- **Unit**: local decisions — state transitions, parsing, validation, policies, classification. In process, no process started.
- **Integration**: real boundaries — a subprocess, persistence, IPC, a server, the network. Fakes behind the boundary are fine.
- **End to end**: a few representative journeys that prove the whole system completes.

A higher level proves its boundary, and leaves the cases to the level below. Ten validation cases belong in one parametrised unit test plus one integration test that shows a refusal crosses the boundary, not in ten integration tests. Expensive setup (a server, a repo, a full lifecycle) is built once and shared by the tests that only read its result.

## Test admission

Before you write a test, answer these five, one line each:

1. Which observable behaviour, or credible failure mode, does it protect? Tie it to a requirement or a real risk.
2. Is that behaviour already covered? Search the existing tests for it first.
3. Can an existing test be extended or parametrised instead?
4. Is this the cheapest level that shows it reliably?
5. Would it fail on a regression someone could plausibly ship?

Admit the test only when all five hold up; otherwise extend the existing test, or write none. When you report the work, name for each new test the behaviour it protects and why its level is the cheapest.

[rules.md](rules.md) holds the rules behind admission, each with the nuance that keeps it from being applied as a blunt count, plus the cost rules for shared setup, waits and seeded state. Read it before you admit a test whose answers are not clear-cut, and before you delete, merge or move any test.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.
- **Proliferation**: a new test per change, each re-proving a guarantee another test already holds, often at a costlier level. The tell: the suite grows faster than the behaviour, and its run time becomes the bottleneck.

## Rules of the loop

- **Red before green.** Make a test fail first — a new admitted test, or an existing one extended — then write only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (see the `code-review` skill), not the red → green implementation cycle.
