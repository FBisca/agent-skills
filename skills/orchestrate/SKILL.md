---
name: orchestrate
description: Build an approved plan's tickets with implementer agents, gate each one on its scenarios, and archive the plan into the living spec. Use when the user says /orchestrate or wants an approved plan, or its next ticket, implemented.
---

# Orchestrate

**Input:** an approved plan (`docs/plans/*.plan.md`) with these fields: `Slug: <slug>`; `Living spec: docs/specs/<area>.md`; `Status: APPROVED`; a Decisions table; scenario lines `- **S<n>** WHEN …, THEN …`; a `## Tickets` table whose IDs are `T<n>` with the columns Satisfies, Blocked by, Paths, Owner and Status, plus Size and Difficulty (a plan without them reads every ticket as regular · simple).
**Output:** each ticket merged and COMPLETE, the scenarios archived into the living spec, and the plan set to `Status: ARCHIVED`.
**Hand-off:** new scope goes back to `/start-planning`.

Arguments: `<plan-path>`.

## Gate

- When the plan is missing, unapproved, or lacks any Input field, refuse: name what is missing and point the user to `/start-planning`. Plan nothing and build nothing yourself. A PRD, Linear issue or vault note is a source, not a plan.
- The plan is the ledger of scope and decisions. When the user decides something or adds scope mid-run, write it into the plan (a Decisions row, or a new ticket with its scenarios).

## What to do

You are a launcher. A Python driver runs the build, so the loop costs no model tokens.

1. Run `python3 <skill-dir>/scripts/orchestrate.py launch <plan>`.
2. Exit 2 means the plan is not runnable: relay what it says is missing and stop. Nothing was started.
3. Otherwise report the pane name it prints (`orchestrate-<slug>`) and end the turn. If a driver with that name is already live, `launch` starts no second one and prints the same name.

Do not run the loop, wait on workers, write `task.md`, review or gate tickets, merge, or archive. The driver does all of it through the `agent-runtime` tools: dispatch, converge, review, fix rounds, CI, merge, unblocking, archive. For its options and behavior: `orchestrate.py run --help`.

The pane is named `orchestrate-<slug>`: Herdr names allow only `a-z 0-9 - _`, so the hyphen replaces the colon.

## What the user sees

- The Herdr pane `orchestrate-<slug>` is the lead. Workers `<slug>-t<n>` nest under it and appear on their ticket rows in the Plans panel.
- Status cells of the plan, including `IN PROGRESS · needs you: <reason>` when a ticket waits for a person.
- `<run>/attention.md`: everything waiting for the user, with the question or action.
- `<run>/gaps.md`: the advisory gaps review of the whole plan, written once at archive. Gaps become plan edits, your call.
- `<run>/metrics.json`: per ticket the route, review rounds, escalations, decider calls and worker usage; lead model turns are 0. Written when the run stops.

`<run>` is `~/.local/state/orchestrate/<slug>/`.

## Contracts

Every agent-to-driver handoff is a versioned JSON file, validated in code; the driver never parses markdown or the one-line `report` text, which only wakes it. A missing or invalid file counts as no report.

| File | Written by |
|---|---|
| `<run>/contract.md` | driver: the rules every task shares |
| `<run>/<task>/task.md` | driver: the worker's packet |
| `<run>/<task>/report.json` | worker |
| `<run>/<task>/review.json` | reviewer |
| `<run>/<task>/findings.json` | driver, for a fix round |
| `<run>/<task>/decision.json` | decider |
| `<run>/attention.md`, `<run>/deferred.md`, `<run>/gaps.md`, `<run>/metrics.json` | driver (gaps.md: the gaps reviewer), for people |

The schemas and field lists live in `scripts/contracts.py` only.

## When the run pauses

The driver pauses a ticket when it needs a person: a scope or product question, a person-owned ticket (prod data, sign-off, deploy), or a failure the decider sends up. The user answers either way:

- edit the plan: set the ticket's Status, or add a Decisions row or a scenario; or
- answer the decider's question named in `attention.md`.

The driver re-reads the plan every round and picks the answer up; nothing needs to be re-launched. If the driver pane has ended, run `launch` again: all state is in the ledger and the plan, so it re-attaches.

## References

- [Routing](references/routing.md): size and difficulty to class and effort; escalation.
- [State helper](references/state.md): the ledger the driver writes, and the manual commands for diagnosis.
- [Chunked dispatch](references/chunked-dispatch.md), [cross-repository work](references/cross-repository.md): not done by the driver; manual use only.

Plan ticket numbers stay out of product code, commit messages, and PR descriptions; describe the implemented behavior. Scenario and requirement IDs belong only in test names or a Python test's docstring first line.
