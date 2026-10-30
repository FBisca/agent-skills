---
name: orchestrate
description: Build an approved plan's tickets with implementer agents, gate each one on its scenarios, and archive the plan into the living spec. Use when the user says /orchestrate or wants an approved plan, or its next ticket, implemented.
---

# Orchestrate

**Input:** an approved plan (`docs/plans/*.plan.md`) with these fields: `Slug: <slug>`; `Living spec: docs/specs/<area>.md`; `Status: APPROVED`; a Decisions table; scenario lines `- **S<n>** WHEN …, THEN …`; a `## Tickets` table whose IDs are `T<n>` with the columns Satisfies, Blocked by, Paths, Owner and Status.
**Output:** each ticket merged and COMPLETE, the scenarios archived into the living spec, and the plan set to `Status: ARCHIVED`.
**Hand-off:** new scope goes back to `/start-planning`.

Arguments: `[plan-path-or-active-plan] [T<n>|next]`.

Own ticket selection, dependencies, worker assignments, and integration. Delegate code changes to `implementer`. Implement locally only when delegation is unavailable; report that fallback.

## Gate

- When the plan is missing, unapproved, or lacks any Input field, refuse: name what is missing and point the user to `/start-planning`. Plan nothing and build nothing yourself. A PRD, Linear issue or vault note is a source, not a plan.
- The plan is the ledger of scope and decisions. When the user decides something or adds scope mid-run, write it into the plan (a Decisions row, or a new ticket with its scenarios) before any work on it.
- Answer status questions from the plan, after updating each ticket's Status.

## 1. Build

- Reuse the active plan and previous user choices. `next` means the next TO-DO ticket whose Blocked by tickets are COMPLETE and merged.
- A ticket owned by a person (prod data apply, sign-off, deploy) is theirs: tell them what it needs and wait for their confirmation before marking it COMPLETE.
- Execute only the requested scope. Within that scope, select independent tickets without another confirmation. Ask only when the plan, scope, or a material decision is unresolved.
- Use the assigned checkout. A blocked ticket branches from `main` after its blockers merge; stacked branches break under squash merge. Use isolated worktrees for concurrent tickets. Preserve existing user changes.
- Verify predecessor behavior in the **actual implementation checkout**. A completion message or commit in another checkout is insufficient.
- Set file or directory ownership per worker. Serialize overlapping edits in one checkout. Assign an integration owner for changes across branches or repositories.
- Existing authorization persists. Starting a worker does not authorize commits, PRs, merges, cleanup, or work beyond the selected scope.

## Select the execution mode

| Work | Mode |
| --- | --- |
| Related sequential work in the same subsystem and checkout | Resume the existing implementer after the context check below. |
| Independent work with little shared context | Start a focused implementer with a compact packet. |
| Independent workers that need repeated coordination | Use agent-runtime `message` and the `task` tool for shared tasks. |
| Existing sessions in different repositories | Use available cross-session messaging with the assigned sessions. Otherwise relay through the orchestrator. |

Delegate only through the `agent-runtime` tools: `spawn` (kind `lookup` is rejected: use the CLI's own subagent tool; `worker` for implementation, long tasks, Codex, or anything the user should watch), `message`, `resume`, `wait`, `task`, `status`, `list`, `collect`, `stop`. Implementation goes to `implementer` as a `worker`. Resume an idle worker with `resume`; a fresh spawn with the same name is not resumption. Do not assume a message wakes it. `spawn` and `resume` return promptly: dispatch every worker, then make one `wait(all)` per work period and read reports, assignment states and peer messages from its result, passing the returned `receipt` on the next call. `status`/`collect` are a fallback for diagnosing a silent worker, not the normal flow. Read [cross-repository work](references/cross-repository.md) before execution across repositories.

- Honor runtime concurrency limits. Parallel execution can reduce elapsed time while increasing token use.

## Check context before reuse

Check the worker's subsystem, checkout state, last result, and available context telemetry at each task boundary. Read worker state from the latest `wait` result, or the `status` tool (or `list`) as a fallback, and the assignment `state`/`runtime_state` fields first, before deciding resume versus fresh; a worker's self-reported `unknown` is not a reading. Record `unknown` only when that read fails.

- Resume when retained knowledge helps the next task and there is room for its expected reads, results, and reasoning.
- Use the **child's effective context window**. Current context occupancy, cumulative token use, and cached input are different measurements.
- Record unavailable measurements as `unknown`. Do not estimate occupancy from transcript bytes, task count, or an agent's unsupported percentage claim.
- Before compaction or replacement, save the objective, ownership, decisions, interface revisions, files, checks, and unresolved work.
- Prefer a new worker when the subsystem changes, assumptions are stale, or repeated errors show lost context. Compaction alone does not require replacement; verify what survived.
- After compaction or external edits, recheck affected files and constraints. A Git HEAD alone does not identify uncommitted changes.
- Do not apply a universal task-count or percentage cutoff. When measured context plus the estimated next-task reserve exceeds the effective window, checkpoint and compact through a supported runtime operation or use a fresh worker.

## Prepare and dispatch

Give each new worker a compact packet containing:

1. Ticket ID, purpose, and its scenarios verbatim, with the **red-first** rule: one test per scenario, named with its S-ID (`it('S3: …')`, `def test_S3_…`), seen failing before the code exists.
2. Exact checkout, branch, the ticket's Paths as file ownership, and exclusions. Shared databases are read-only for workers; schema changes go through migrations in the worker's own branch.
3. Relevant files and symbols, the plan's Decisions, and dependency evidence.
4. The repo's full CI gate (types, lint, tests as CI runs them), assigned peers, and integration owner.

Give a resumed worker only the new task, changed constraints, relevant peer updates, and changed checkout state. Do not repeat the full plan or broad discovery. The orchestrator maps scope; the worker reads implementation details.

Use [the state helper](references/state.md) to reserve assignments before dispatch and bind returned runtime IDs afterward. Keep one worker ledger per active plan, outside tracked product files; share its absolute path across repositories. The worker ledger tracks agents; the plan tracks scope, decisions and ticket status. The helper validates records, not code behavior, and never spawns agents.

If spawn delivery is uncertain, inspect the runtime and reservation before retrying. Never turn a timeout into a duplicate assignment. A blocked worker retains its assignment until resumed or explicitly released after it has stopped.

## Communicate and verify

- Send messages only when they unblock work, change an interface, report a failure, or deliver a result. Prefer direct assigned-peer messages to broadcasts.
- Include task ID, repository, interface revision or checkout evidence, the change or question, and the needed action. Messages do not transfer files or expand edit authority.
- Let workers ask focused questions. The orchestrator owns scope changes and resolves incompatible interface decisions.
- Prefer one blocking `wait(all)` per work period over native notifications. Avoid repeated status polling and repeated unchanged reports.
- Wait for PR checks with `~/bin/wait-checks <owner>/<repo>#<pr> ...` (full path: shells started before `~/bin` existed don't have it on PATH), run in the background: one PASS/FAIL line per PR, plus the failed log on FAIL. Do not write ad-hoc watch loops.
- Workers run relevant checks and return commands, outcomes, and omissions. Inspect their diff and evidence. Rerun checks only for changed inputs, integration, failures, or unresolved risk.
- Require verification on the combined result when repositories or branches interact. A pane state of `idle` or `done` is not evidence of task completion.
- Record the result and handoff. Use available runtime usage data for comparisons; include parent and worker costs, cache use, time, and correctness. Never claim measured savings without measurements.

## 2. Gate each ticket

When a worker reports a ticket done, run three gates in the implementation checkout. Any FAIL or blocking finding sends the failing lines back to the worker (return to step 1).

1. **Converge:** call the Skill tool with `converge` for this ticket (`--ticket T<n>`). Its checks: every scenario has a test named with its S-ID, every changed test carries an ID, and the diff stays inside the ticket's Paths. Any FAIL blocks.
2. **Review:** dispatch a fresh-context reviewer subagent (Opus) with only the ticket, its scenarios, the plan's Decisions, the diff, and the repo's AGENTS.md / CLAUDE.md. It checks correctness and the repo's conventions, plus a security lens when the diff touches auth, permissions or personal data. Its blocking findings go back to the worker.
3. **Gaps (advice):** a fresh-context subagent compares the plan with the diff and classifies each gap as missing, partial, contradicts or unrequested. Each gap becomes a new ticket. It never blocks and never edits code.

A ticket is COMPLETE when converge passes, the review has no blocking finding, and CI is green on its PR. Record the commands and results in its row.

## 3. Archive

When every ticket is COMPLETE, open one archive PR:
- Create the plan's living spec `docs/specs/<area>.md` if it is missing. Its first lines are `# <Area>` and `Paths: src/area/, tests/area/**`: the comma-separated code paths the area covers. Converge fails a spec without a parseable `Paths:` line.
- Append each scenario as a requirement with the next free number and its provenance: `- **R4** WHEN …, THEN … (from <slug>/S3)`.
- Rename each test's `S3` to `<area>/R4`: in the test name, or in a Python test's docstring first line, since Python names can't hold `/`.
- Call the Skill tool with `converge` with `--final`. It maps renamed tests back to their scenarios through the provenance, and checks that the living spec changed wherever its area's code did. Any FAIL blocks the archive.
- Run the advisory gap review (gate 3) on the whole plan against the final diff.
- Set the plan's `Status: ARCHIVED <date>`.

## Report

Report the result, checkout/branch, checks, and blockers briefly. Keep worker IDs and detailed state in the ledger. Continue within the authorized scope; stop at its boundary.

When a finished worker is shut down, prune its worktree in the same step: first prove the checkout is clean (`git status --porcelain` empty — no modified, staged, or untracked files) and its branch is pushed or merged; then `git worktree remove <path>` and `git worktree prune`. Anything uncommitted stops the removal — report it and leave the worktree in place. Never `--force`, never remove a worktree a live worker still holds, and never delete the branch.

A worker is **finished** when its task is checkpointed COMPLETE and its successor task is assigned to a different worker (or there is none). Send a finished worker a shutdown request and say so in the report, then prune its worktree as above; an idle finished worker is clutter and cached context, not capacity. Keep a worker alive only while it holds the next assigned unit, or while its PR is under review and a correction round is plausible — and state which reason applies.

Plan ticket numbers stay out of product code, commit messages, and PR descriptions; describe the implemented behavior. Scenario and requirement IDs belong only in test names or a Python test's docstring first line.
