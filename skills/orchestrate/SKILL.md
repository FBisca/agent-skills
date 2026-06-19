---
name: orchestrate
description: Orchestrate execution of one phase, chunk, or deliverable from an implementation plan using a focused implementation subagent.
argument-hint: "[plan-path-or-active-plan] [Phase|Chunk|Deliverable N]"
---

---

Orchestrate the implementation of an existing markdown implementation plan

It should not do the implementation itself unless delegation is unavailable.

It should prepare a clean implementation packet and delegate the actual code work to the `implementer` subagent.

## Responsibilities

This skill owns:

1. Identify the plan.
2. Identify the exact units to orchestrate and units that can be parellelized.
3. Reuse the active plan from this chat when possible.
4. Build a compact implementation packet.
5. Delegate to `implementer`.
6. Report the final result to the user.

The subagent owns:

1. Reading the focused code context.
2. Implementing the selected unit.
3. Running relevant checks and quality gates.
4. Communicating blockers if they arise.
5. Returning a structured result when complete.

## Active Plan Reuse

Keep a compact ledger in the main chat so the user can run:

```text
/orchestrate apps/api/plans/example.plan.md Phase 1
/orchestrate Phase 2
/orchestrate Phase 3
```

without rereading the whole codebase each time.

If the user invokes this skill with only `Phase 2`, `Chunk 3`, `next`, or similar, reuse the active plan from the ledger.
If there is no active plan and the user did not provide a plan path or plan content, ask for the plan.
If the user did not provide the exact unit, ask for the exact unit.

## Intake

1. Resolve the plan source:
   - explicit plan path
   - pasted plan content
   - active plan from the ledger

2. Resolve the target unit:
   - `Phase 1`
   - `Chunk 2`
   - `Deliverable 3`
   - equivalent heading

3. Identify parallelizable units if the plan allows for it.

4. Confirm which units to execute with the user, if not specified and there are multiple units that can be done in parallel.
   (e.g. "Phase 2, Chunk 2 and Chunk 3 can be done in either order or in parallel. Which would you like to do?").

5. Confirm with the user, if not specified, how the work should be built, using worktrees or in the current branch.

6. If worktrees are used, confirm if the implementers should open a Pull Request when the implementation is complete.

7. After confirmation, start delegation.

## Verify Predecessor

Before delegating, verify that the previous unit is already on `main`.

Examples:

```text
Phase 2 depends on Phase 1
Chunk 3 depends on Chunk 2
Deliverable 2 depends on Deliverable 1
```

If this is the first unit, record:

```text
No predecessor verification required.
```

If there is a predecessor, verify it using concrete checks on latest `main`:

- expected files exist
- expected symbols exist
- expected routes, schemas, migrations, or tests exist
- expected behavior appears in code or test coverage

If the predecessor is missing or uncertain, stop and report the blocker.

Do not delegate implementation when predecessor verification failed.

## Instructions for Implementer

The `implementer` subagent may run on a cheap mini model.

Before delegating, make the packet extra explicit:

- exact selected unit
- worktree path
- branch
- what to change
- what not to change
- relevant plan excerpt
- checks to run

Do not delegate vague architecture, broad refactors, or unclear tasks to `implementer`.

If the unit is too broad or unclear, stop and report the blocker instead of delegating.

## Delegate

Delegate to:

```text
implementer
```

Tell the subagent:

```text
Implement only the selected unit from this plan.

## INSTRUCTIONS AND CONTEXT
${IMPLEMENTATION_CONTEXT}

## WHAT TO CHANGE
${WHAT_TO_CHANGE}

## WHAT NOT TO CHANGE
${WHAT_NOT_TO_CHANGE}

## RELEVANT PLAN EXCERPT
${RELEVANT_PLAN_EXCERPT}

## CHECKS TO RUN
${CHECKS_TO_RUN}
```

## Final Response

After the subagent returns, tell the user:

1. Plan path.
2. Selected unit.
3. Worktree path.
4. Branch.
5. Quality gate result.
6. Whether the worktree was deleted.
7. Any blockers or manual follow-up.
8. Updated active plan ledger summary.

## Implementation Follow-ups

When the implementation is complete, update the active plan ledger and offer the user the option to orchestrate the next unit in the plan.

## Mandatory Rules

- Never mention in the code, Pull Requests or commits the Plan, Phases, Chunks, or Deliverable. The code should be unaware of the plan structure, instead use meaningful wording that describes the actual implementation.
