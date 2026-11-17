---
name: orchestrate
description: Implement an approved plan or its next ticket through agents, scenario gates, and archive.
---

# Orchestrate

**Input:** `<plan-path>`: an approved `plan/2` folder (`plan.yaml`, `brief.md`), approved with `plan approve`. Legacy layouts also run: `<name>.plan.yaml`, `<name>.brief.md` (or `<name>.plan.md`); Markdown plans are described below.
**Output:** tickets merged and COMPLETE, each with CI green; archive by mode: `promote` applies the plan's requirement changes to its spec and deletes the plan folder; `discard` deletes the plan folder without writing a spec.
**Scope:** new scope returns to start-planning.

`<engine>` means `python3 <skill-dir>/scripts/orchestrate.py`; this shim forwards commands and arguments unchanged.

## Launch

1. Require an approved plan. For missing/unapproved plans, name the deficiency and direct the user to start-planning; sources (PRDs, issues, vault notes) need planning first. `<engine> plan check <plan>` diagnoses deficiencies.
2. Run `<engine> launch <plan>`.
3. Exit 2: relay the deficiency and stop; nothing started. Otherwise report the printed pane name, `orchestrate-<slug>`, and end the turn. Re-launching a live driver returns its name without duplicating it.

The Python driver handles dispatch, the ticket gate, review/fix rounds, CI, unblocking after user merges, and archive through agent-runtime. It never merges PRs. Answer its requests and complete person-owned tickets. Options: `<engine> run --help`.

## The ticket gate

An implementation provides its evidence. Each scenario the ticket satisfies needs a covering test the ticket changed, tagged with its requirement's title and mapped in its report's `covers` (`S<n>` → `path::test_name`), and seen red first: the report's `red` (`S<n>` → the failing output from before the fix, naming the node) proves it. CI green on the same head proves the tests pass. The gate, `verify`, checks scope (the diff stays in the ticket's `paths`), integrity (the ticket leaves its plan folder untouched), covers (every satisfied scenario maps to test nodes that exist and changed in the ticket) and red (every satisfied scenario has an excerpt naming one of its nodes); the reviewer judges whether each excerpt is a genuine assertion failure. Say the same when you answer a worker: the tests it writes, seen red, are the ticket's only evidence.

## Change the plan: re-approve

The plan records scope and decisions; approval covers its bytes. Record user decisions in the brief and scope changes in the contract's requirements, tickets or `paths`. A contract edit needs the user's yes, then:

```
<engine> plan approve <plan> --reason "<why>"
```

Keep the driver running: the edit drains dispatch until the re-approval; the next round adopts the new digest, dispatches new tickets, and resumes changed in-flight tickets with new packets. COMPLETE tickets and their scenarios are frozen; merged work needs a new ticket. The brief is not digested; a decision-only edit needs no re-approval.

The covers gate says a ticket's `paths` can hold no test → add the test location to its `paths`, re-approve, then decide `retry`.

## Engine and panes

The engine and its tests live in [agent-runtime](https://github.com/FBisca/agent-runtime)'s `agent-orchestrator` member; behavior/contracts: `docs/specs/orchestrator-engine.md`, `docs/specs/plan-contract.md`.

Shim resolution:

1. `$AGENT_RUNTIME_HOME` checkout: `.venv/bin/agent-orchestrator` if synced, otherwise `uv run` there.
2. `agent-orchestrator` on `PATH`.

The named checkout wins over PATH. If neither resolves, exit 2 explains recovery: `uv sync --frozen --all-packages` in an agent-runtime checkout and `export AGENT_RUNTIME_HOME=<that checkout>`, or install the member on PATH. There is no second engine fallback.

In Herdr, `orchestrate-<slug>` nests under the Lead's terminal, falling back to top-level. Names allow `a-z 0-9 - _` (hyphen replaces colon). Workers `<slug>-t<n>` nest under it and appear on Plans ticket rows.

## Observe

`<engine> status <plan>` shows state/history and each ticket's state, reason, and PR; `--json` returns data including `run_dir`.

- `IN PROGRESS · awaiting merge (<PR>)`: user merges; driver then marks COMPLETE and unblocks dependents.
- `needs you: <reason>`: person required.
- `orphaned` event: restarted drive found an open task whose agent runtime no longer lists. An implementer missing its report is redispatched alone as `t<N>o<k>`, retaining worktree, branch, and worker name.

`<run>` = `~/.local/state/orchestrate/<repo-key>/<slug>/`:

| Artifact | Purpose |
|---|---|
| `attention.md` | Pending user questions/actions |
| `metrics.json` | Written at stop: per-ticket route, review rounds, escalations, decider calls, usage; lead model turns = 0 |

## Handoff contracts

Agent-to-driver handoffs are versioned JSON, code-validated. Missing/invalid files count as no report; Markdown and one-line `report` text (wake only) are not parsed. Schemas/fields live solely in the engine's `contracts.py`.

| File | Writer |
|---|---|
| `<run>/contract.md` | Driver: shared rules |
| `<run>/<task>/task.md` | Driver: worker packet |
| `<run>/<task>/report.json` | Worker |
| `<run>/<task>/review.json` | Reviewer |
| `<run>/<task>/findings.json` | Driver: fix round |
| `<run>/<task>/request.<n>.json` | Driver |
| `<run>/<task>/decision.<n>.json` | Lead through `decide` |
| `<run>/attention.md`, `<run>/deferred.md`, `<run>/metrics.json` | Driver: human-facing artifacts |

## Resolve pauses

Scope/product questions, unresolved failures, and idle workers pause a unit. Its request names the unit, reason, and menu (`action`, `summary`, `inputs`, each input marked required or optional).

```
<engine> decide <plan> <unit> --json <file|->
<engine> decide <plan> <unit> <action> --reason "<why>" [--answer "<text>"]
```

Prefer JSON: `{"action": "…", "reason": "…", "answer": "…"}` (`answer` optional), from file or stdin (`-`). Both forms return the decision as JSON. Refusal writes `{error, reason, way_out}` to stderr and leaves the request open.

| Action | Effect |
|---|---|
| `retry`, `retry one class up`, `fresh worker` | New attempt of same unit; escalation counts persist |
| `answer` | Same worker resumes with `--answer`; ticket IDs are refused—say "your Paths" |
| `mark blocked`, `skip` | Stops unit; dependents remain blocked |

A scope-changing answer is a plan change: re-approve (above), then `retry` the unit.

Person-owned tickets show `needs you: <deliverable>` after blockers merge. Complete the work in its `repo`, when specified, then:

```
<engine> complete <plan> <T#> --note "<what landed>"
```

The plan is ACCEPTED when every agent ticket is COMPLETE; archive requires every ticket. A run with only person tickets remaining exits: after `complete`, `launch` again.

## Accept, resume

Once every agent ticket is COMPLETE (merged, CI green), the plan is ACCEPTED and archive starts; nothing is re-run, since CI runs on every merge.

- `stranded <unit>`: agent fate unknown; no release/spawn; non-zero exit. Inspect its terminal, then restart the drive.
- `not-dispatched <ticket>`: dispatch failed; `status` gives the reason.

A run exits when only paused units remain. Answer, then `launch` again to resume from plan/ledger; a live run picks up decisions next round.

## Legacy Markdown plans

`<name>.plan.md` with a `## Tickets` table runs until legacy-reader removal. Status cells are its ledger: `TO-DO` retries; `COMPLETE <date>` records manual completion.

## References

- [Routing](references/routing.md): size/difficulty, class/effort, escalation, idle window.
- [State helper](references/state.md): ledger and manual diagnosis commands.
- [Chunked dispatch](references/chunked-dispatch.md), [cross-repository work](references/cross-repository.md): manual-only workflows, outside the driver.

Keep plan ticket and scenario IDs out of product code, test names, commits, and PR descriptions; describe behavior. A test names its requirement by title in its tag (the `tdd` skill).
