---
name: orchestrate
description: Build an approved plan's tickets with implementer agents, gate each one on its scenarios, verify the plan's outcome on the integrated tree, and archive it into the living spec. Use when the user says /orchestrate or wants an approved plan, or its next ticket, implemented.
---

# Orchestrate

**Input:** an approved plan: a plan folder's `plan.yaml` (`plan/1`) that `plan approve` has approved, with its brief `brief.md` and its acceptance tests `acceptance/` beside it. An older plan is `<name>.plan.yaml` with `<name>.brief.md` (or `<name>.plan.md`) and `<name>.oracle/` beside it, and still runs.
**Output:** each ticket merged and COMPLETE, the plan's outcome verified on the integrated tree, and the plan archived by its mode: `promote` writes its scenarios into the living spec and moves its acceptance tests into `<package>/<acceptance.dir>/<domain>/`; `discard` deletes the plan folder and writes nothing.
**Hand-off:** new scope goes back to `/start-planning`.

Arguments: `<plan-path>`.

`<engine>` below is `python3 <skill-dir>/scripts/orchestrate.py`, the hand-off to the engine; it passes every command and its arguments through unchanged.

## Gate

- When the plan is missing or unapproved, refuse: name what is missing and point the user to `/start-planning`. Plan nothing and build nothing yourself. A PRD, Linear issue or vault note is a source, not a plan. `<engine> plan check <plan>` names what a plan lacks.
- The plan is the ledger of scope and decisions, and its approval covers its bytes. When the user decides something or adds scope mid-run, write it into the plan (a decision line in the brief; a ticket, a scenario or a Paths change in the contract). A change to the contract or an acceptance file needs the user's yes, then `<engine> plan amend <plan> --reason "<why>"`. Keep the driver running: the edit drains it (it dispatches nothing new) until the amendment lands, then it adopts it on its next round, dispatches the new tickets and resumes a changed in-flight ticket on its new packet. A COMPLETE ticket and its scenarios' `when`/`then` are frozen: new scope on merged work is a new ticket. The brief is not digested, so a decision line alone needs none.

## What to do

You are a launcher. A Python driver runs the build, so the loop costs no model tokens.

1. Run `<engine> launch <plan>`.
2. Exit 2 means the plan is not runnable: relay what it says is missing and stop. Nothing was started.
3. Otherwise report the pane name it prints (`orchestrate-<slug>`) and end the turn. If a driver with that name is already live, `launch` starts no second one and prints the same name.

The driver does the build through the `agent-runtime` tools: dispatch, the ticket gates (scope, integrity, covers, evidence), review, fix rounds, CI, unblocking once the user merges, integration, outcome verification and archive. It never merges a PR. Your part is answering its requests and the person-owned tickets. For its options and behaviour: `<engine> run --help`.

## The engine

The driver is not in this skill. It is the `agent-orchestrator` member of [agent-runtime](https://github.com/FBisca/agent-runtime), and `scripts/orchestrate.py` is a shim: it resolves that member's CLI and hands it the command. The engine's behaviour and its suite live in that repository, in `docs/specs/orchestrator-engine.md` and `docs/specs/plan-contract.md`.

The member is resolved in this order:

1. `$AGENT_RUNTIME_HOME` — the checkout of agent-runtime. Its `.venv/bin/agent-orchestrator` when the environment is synced, else `uv run` inside that checkout.
2. `agent-orchestrator` on `PATH`.

The checkout wins: a checkout the user named is never shadowed by an older install on `PATH`. When neither answers, the script exits 2 and names the way out — `uv sync --frozen --all-packages` in a checkout of agent-runtime, then `export AGENT_RUNTIME_HOME=<that checkout>`, or the member on `PATH`. It never falls back to a second engine: two copies drift.

The pane is named `orchestrate-<slug>` and nests under the Lead's terminal when launched inside Herdr, falling back to top-level if nesting fails. Herdr names allow only `a-z 0-9 - _`, so the hyphen replaces the colon.

## What the user sees

- The Herdr pane `orchestrate-<slug>` is the lead. Workers `<slug>-t<n>` nest under it and appear on their ticket rows in the Plans panel.
- `<engine> status <plan>` (`--json` for the same as data): the plan's state and history, and each ticket's state, reason and PR. A ticket stops at `IN PROGRESS · awaiting merge (<PR>)` until the user merges its PR; the driver then marks it COMPLETE and unblocks the tickets that depend on it. It reads `needs you: <reason>` when it waits for a person.
- An `orphaned` task: a restarted drive found an open task whose agent the runtime no longer lists, and names it in an `orphaned` event. An implementer whose report never landed is dispatched again by itself — a new `t<N>o<k>` attempt, same worktree, branch and worker name.
- `<run>/attention.md`: everything waiting for the user, with the question or action.
- `<run>/gaps.md`: the advisory gaps review of the whole plan, written once at archive. Gaps become plan edits, your call.
- `<run>/metrics.json`: per ticket the route, review rounds, escalations, decider calls and worker usage; lead model turns are 0. Written when the run stops.

`<run>` is `~/.local/state/orchestrate/<repo-key>/<slug>/`; `status --json` prints it as `run_dir`.

## Contracts

Every agent-to-driver handoff is a versioned JSON file, validated in code; the driver never parses markdown or the one-line `report` text, which only wakes it. A missing or invalid file counts as no report.

| File | Written by |
|---|---|
| `<run>/contract.md` | driver: the rules every task shares |
| `<run>/<task>/task.md` | driver: the worker's packet |
| `<run>/<task>/report.json` | worker |
| `<run>/<task>/review.json` | reviewer |
| `<run>/<task>/findings.json` | driver, for a fix round |
| `<run>/<task>/request.<n>.json`, `<run>/<task>/decision.<n>.json` | driver; Lead, through `decide` |
| `<run>/receipts/` | driver: every evidence run, its receipt and log |
| `<run>/attention.md`, `<run>/deferred.md`, `<run>/gaps.md`, `<run>/metrics.json` | driver (gaps.md: the gaps reviewer), for people |

The schemas and field lists live in the member's `contracts.py` only.

## When the run pauses

The driver pauses a unit when it needs a person: a scope or product question, a failure it could not settle, a worker that went idle. The request names the unit, the reason and a menu. Answer it:

```
<engine> decide <plan> <unit> --json <file|->
<engine> decide <plan> <unit> <action> --reason "<why>" [--answer "<text>"]
```

The request's menu lists each option's `action`, `summary` and `inputs` (each marked `required` or not). Answer with `--json`: one object `{"action", "reason", "answer"?}` from a file or `-` for stdin. The decision comes back as JSON; a refusal is one JSON object `{error, reason, way_out}` on stderr, and the request stays open. The flag form writes the same decision.

- `retry`, `retry one class up`, `fresh worker`: a new attempt of the same unit; escalation counts carry over.
- `answer`: the same worker resumes with `--answer` as its next instruction. The driver refuses an answer that names a ticket ID: say "your Paths", not the ticket.
- `mark blocked`, `skip`: the unit stops; its dependents stay blocked.
- `amend`: the unit parks `awaiting-amendment` and its worker waits untouched. Change the plan (see Gate); the adopted amendment releases the unit.

If the answer changes scope, decide `amend` and change the plan (see Gate).

A person-owned ticket reads `needs you: <what it delivers>` once its blockers merge. Do the work it names, in its `repo` when it has one, then record it:

```
<engine> complete <plan> <T#> --note "<what landed>" [--cover S<n>=<node>]...
```

Give one `--cover` per test node that proves a scenario the ticket satisfies; a node in another repository is `<repo-name>/<path>::<test>`. The archive lists each in its scenario's Coverage row. Verify starts once every agent ticket is COMPLETE, but the archive waits for every ticket, so a run with only person tickets open ends: after `complete`, `launch` again.

## Verify and accept

Once every ticket is COMPLETE, the driver runs every evidence item on one pinned default-branch commit that contains each merge. `<engine> verify <plan>` says whether the outcome holds on those receipts, and exits non-zero when it does not.

An evidence item that did not pass, or a `human` item, waits for a person. Check it yourself, then record it:

```
<engine> accept <plan> <scenario> --note "<what you checked>"
```

The note is kept with your name, the time and the tree, and the plan becomes ACCEPTED_WITH_HUMAN. The archive starts once the plan is accepted.

Two wakes report work the run could not do:

- `stranded <unit>`: the drive cannot tell what became of an open task's agent. Nothing was released or spawned and the run exits non-zero; the work may still be in its terminal — look at it, then restart the drive.
- `not-dispatched <ticket>`: the dispatch failed; `status` shows its reason on the ticket.

When only paused units remain, the run exits. Run `launch` again after answering: the driver re-reads the plan and the ledger, so it picks up where it stopped. A run still alive picks a decision up on its next round.

## Markdown plans

A plan written before the YAML contract (`<name>.plan.md` with a `## Tickets` table) still runs until the legacy reader is removed. Its Status cells are its ledger, and the user answers a pause through them: `TO-DO` retries, `COMPLETE <date>` marks the ticket done by hand.

## References

- [Routing](references/routing.md): size and difficulty to class and effort; escalation; the idle window.
- [State helper](references/state.md): the ledger the driver writes, and the manual commands for diagnosis.
- [Chunked dispatch](references/chunked-dispatch.md), [cross-repository work](references/cross-repository.md): not done by the driver; manual use only.

Plan ticket numbers stay out of product code, commit messages, and PR descriptions; describe the implemented behavior. Scenario and requirement IDs belong only in test names or a Python test's docstring first line.
