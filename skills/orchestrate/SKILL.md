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

Do not run the loop, wait on workers, write `task.md`, review or gate tickets, merge, or archive. The driver does all of it through the `agent-runtime` tools: dispatch, converge, review, fix rounds, CI, unblocking once you merge, archive. It never merges a PR. For its options and behavior: `orchestrate.py run --help`.

## The engine

The driver is not in this skill. It is the `agent-orchestrator` member of [agent-runtime](https://github.com/FBisca/agent-runtime), and `scripts/orchestrate.py` is a shim: it resolves that member's CLI and hands it the command. The engine's behaviour and its suite live in that repository, in `docs/specs/orchestrator-engine.md`.

The member is resolved in this order:

1. `$AGENT_RUNTIME_HOME` — the checkout of agent-runtime. Its `.venv/bin/agent-orchestrator` when the environment is synced, else `uv run` inside that checkout.
2. `agent-orchestrator` on `PATH`.

The checkout wins: a checkout the user named is never shadowed by an older install on `PATH`. When neither answers, the script exits 2 and names the way out — `uv sync --frozen --all-packages` in a checkout of agent-runtime, then `export AGENT_RUNTIME_HOME=<that checkout>`, or the member on `PATH`. It never falls back to a second engine: two copies drift.

The pane is named `orchestrate-<slug>` and nests under the Lead's terminal when launched inside Herdr, falling back to top-level if nesting fails. Herdr names allow only `a-z 0-9 - _`, so the hyphen replaces the colon.

## What the user sees

- The Herdr pane `orchestrate-<slug>` is the lead. Workers `<slug>-t<n>` nest under it and appear on their ticket rows in the Plans panel.
- Status cells of the plan. A ticket stops at `IN PROGRESS · awaiting merge (<PR>)` until the user merges its PR; the driver then marks it COMPLETE and unblocks the tickets that depend on it. Status also reads `IN PROGRESS · needs you: <reason>` when a ticket waits for a person.
- An `orphaned` task: a restarted drive found an open task whose agent the runtime no longer lists, and names it in an `orphaned` event. An implementer whose report never landed is dispatched again by itself — a new `t<N>o<k>` attempt, same worktree, branch and worker name.
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

The schemas and field lists live in the member's `contracts.py` only.

## When the run pauses

The driver pauses a ticket when it needs a person: a scope or product question, a person-owned ticket (prod data, sign-off, deploy), or a failure the decider could not settle. The decider is one-shot: it never takes a reply. Read `<run>/attention.md`, decide, and answer through the plan Status:

- `TO-DO`: retry. On its next round the driver stops the held worker if live, releases the assignment, and dispatches a fresh attempt of the same unit (escalation counts carry over). A note in the cell is fine: `TO-DO · retry` retries too.
- `COMPLETE <date>`: done by hand. Its dependents and the archive unblock.
- Any other edit leaves the ticket paused.

If the answer changes scope, add a Decisions row or a ticket (with its scenarios) to the plan first.

Two wakes report work the run could not do:

- `stranded <unit>`: the drive cannot tell what became of an open task's agent. Nothing was released or spawned and the run exits non-zero; the work may still be in its terminal — look at it, then restart the drive.
- `not-dispatched <ticket>`: the dispatch failed and its reason stays in the cell, `TO-DO · not dispatched: <reason>`, until it reads exactly `TO-DO` — that retry compares the whole cell, so the driver never reads its own note as yours.

When only paused tickets remain, the run exits. After editing the plan, run `launch` again: the driver re-reads the plan and the ledger, so it picks up where it stopped. A run still alive picks the edit up on its next round.

## References

- [Routing](references/routing.md): size and difficulty to class and effort; escalation; the idle window.
- [State helper](references/state.md): the ledger the driver writes, and the manual commands for diagnosis.
- [Chunked dispatch](references/chunked-dispatch.md), [cross-repository work](references/cross-repository.md): not done by the driver; manual use only.

Plan ticket numbers stay out of product code, commit messages, and PR descriptions; describe the implemented behavior. Scenario and requirement IDs belong only in test names or a Python test's docstring first line.
