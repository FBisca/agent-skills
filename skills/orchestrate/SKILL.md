---
name: orchestrate
description: Execute selected units from an implementation plan with focused implementer agents. Reuse related workers and coordinate independent work across repositories.
---

# Orchestrate

Arguments: `[plan-path-or-active-plan] [Phase|Chunk|Deliverable N|next]`.

Own task selection, dependencies, worker assignments, and integration. Delegate code changes to `implementer`. Implement locally only when delegation is unavailable; report that fallback.

## Select the work

- Reuse the active plan and previous user choices. `next` means the next uncompleted unit whose dependencies are ready.
- Execute only the requested scope. Within that scope, select independent work without another confirmation. Ask only when the plan, scope, or a material decision is unresolved.
- Use the assigned checkout, including the current branch when appropriate. Use isolated worktrees for concurrent changes that need separate checkouts. Preserve existing user changes.
- Verify predecessor behavior in the **actual implementation checkout**. A predecessor need not be on `main`. A completion message or commit in another checkout is insufficient.
- Set file or directory ownership per worker. Serialize overlapping edits in one checkout. Assign an integration owner for changes across branches or repositories.
- Existing authorization persists. Starting a worker does not authorize commits, PRs, merges, cleanup, or work beyond the selected scope.

## Select the execution mode

| Work | Mode |
| --- | --- |
| Related sequential work in the same subsystem and checkout | Resume the existing implementer after the context check below. |
| Independent work with little shared context | Start a focused implementer with a compact packet. |
| Independent workers that need repeated coordination | Use available native peer messaging; use Claude Agent Teams when its shared tasks and teammates help. |
| Existing sessions in different repositories | Use available cross-session messaging with the assigned sessions. Otherwise relay through the orchestrator. |

Inspect the tools exposed in this session before choosing calls. Do not infer capabilities from a feature flag alone.

- **Codex / MultiAgent V2:** select `agent_type: implementer` and, when available, `fork_turns: none`. Verify Terra/high in exposed runtime configuration. Full-history forks can inherit the parent's model and effort; existing sessions may retain old role definitions. Report mismatches instead of silently selecting another model.
- Use the runtime's follow-up/resume operation for an idle worker. In a surface with separate tools, `send_message` steers a running worker and `followup_task` starts another turn. Do not assume that a message wakes an idle agent on every runtime.
- **Claude:** use the `implementer` type for either a subagent or teammate. Resume by the returned agent ID. A fresh spawn with the same name is not resumption.
- For visible Claude teammates, use the existing Herdmates integration. Read [runtime guidance](references/runtimes.md) before pane work or cross-repository execution. Do not start a second worker to display an existing one.
- Honor runtime concurrency limits. Parallel execution can reduce elapsed time while increasing token use.

## Check context before reuse

Check the worker's subsystem, checkout state, last result, and available context telemetry at each task boundary. Read the pane's own measurement first (`herdr` in the state helper) before deciding resume versus fresh; a worker's self-reported `unknown` is not a reading. Record `unknown` only when that read fails.

- Resume when retained knowledge helps the next task and there is room for its expected reads, results, and reasoning.
- Use the **child's effective context window**. Current context occupancy, cumulative token use, and cached input are different measurements.
- Record unavailable measurements as `unknown`. Do not estimate occupancy from transcript bytes, task count, or an agent's unsupported percentage claim.
- Before compaction or replacement, save the objective, ownership, decisions, interface revisions, files, checks, and unresolved work.
- Prefer a new worker when the subsystem changes, assumptions are stale, or repeated errors show lost context. Compaction alone does not require replacement; verify what survived.
- After compaction or external edits, recheck affected files and constraints. A Git HEAD alone does not identify uncommitted changes.
- Do not apply a universal task-count or percentage cutoff. When measured context plus the estimated next-task reserve exceeds the effective window, checkpoint and compact through a supported runtime operation or use a fresh worker.

## Prepare and dispatch

Give each new worker a compact packet containing:

1. Task ID, purpose, selected plan excerpt, and acceptance criteria.
2. Exact checkout, branch, file ownership, and exclusions.
3. Relevant files and symbols, established decisions, and dependency evidence.
4. Checks to run, assigned peers, and integration owner.

Give a resumed worker only the new task, changed constraints, relevant peer updates, and changed checkout state. Do not repeat the full plan or broad discovery. The orchestrator maps scope; the worker reads implementation details.

Use [the state helper](references/state.md) to reserve assignments before dispatch and bind returned runtime IDs afterward. Keep one ledger per active plan, outside tracked product files; share its absolute path across repositories. The helper validates records, not code behavior, and never spawns agents.

If spawn delivery is uncertain, inspect the runtime and reservation before retrying. Never turn a timeout into a duplicate assignment. A blocked worker retains its assignment until resumed or explicitly released after it has stopped.

## Communicate and verify

- Send messages only when they unblock work, change an interface, report a failure, or deliver a result. Prefer direct assigned-peer messages to broadcasts.
- Include task ID, repository, interface revision or checkout evidence, the change or question, and the needed action. Messages do not transfer files or expand edit authority.
- Let workers ask focused questions. The orchestrator owns scope changes and resolves incompatible interface decisions.
- Prefer native completion notifications or blocking event waits. Avoid repeated status polling and repeated unchanged reports.
- Workers run relevant checks and return commands, outcomes, and omissions. Inspect their diff and evidence; rerun checks only for changed inputs, integration, failures, or unresolved risk.
- Require verification on the combined result when repositories or branches interact. A pane state of `idle` or `done` is not evidence of task completion.
- Record the result and handoff. Use available runtime usage data for comparisons; include parent and worker costs, cache use, time, and correctness. Never claim measured savings without measurements.

## Report

Report the result, checkout/branch, checks, and blockers briefly. Keep worker IDs and detailed state in the ledger. Continue within the authorized scope; stop at its boundary.

When a finished worker is shut down, prune its worktree in the same step: first prove the checkout is clean (`git status --porcelain` empty — no modified, staged, or untracked files) and its branch is pushed or merged; then `git worktree remove <path>` and `git worktree prune`. Anything uncommitted stops the removal — report it and leave the worktree in place. Never `--force`, never remove a worktree a live worker still holds, and never delete the branch.

A worker is **finished** when its task is checkpointed COMPLETE and its successor task is assigned to a different worker (or there is none). Send a finished worker a shutdown request and say so in the report, then prune its worktree as above; an idle finished worker is clutter and cached context, not capacity. Keep a worker alive only while it holds the next assigned unit, or while its PR is under review and a correction round is plausible — and state which reason applies.

Never mention plan phases, chunks, or deliverable numbers in product code, commit messages, or PR descriptions. Describe the implemented behavior.
