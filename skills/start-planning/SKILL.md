---
name: start-planning
description: Plan one feature spec-driven, from its sources to WHEN/THEN scenarios and vertical tickets, then stop for approval. Use when the user wants to plan a feature, idea or task, says "let's plan X", or hands over a PRD, Linear issue or vault note to build.
---

# Start planning

**Input:** a feature, idea or task, plus whatever already describes it: a PRD, Linear issues, vault notes, a living spec, or only the request itself.
**Output:** one approved **plan** at `docs/plans/YYYY-MM-DD-<slug>.plan.md`, dated the day it is written and never re-dated.
**Hand-off:** `/orchestrate <plan-path>` builds it.

Invoke it as `/start-planning` in Claude Code, as `/skill:start-planning` in Pi, or as the `start-planning` skill in Codex. The plan it produces is the same everywhere.

Three documents, three jobs: the **PRD**, when there is one, says why and for whom; the **plan** turns one piece of the work into testable scenarios and tickets; the **living spec** (`docs/specs/<area>.md`) records what the system does today.

## Harness adapters

Two steps need another context: the gatherer in step 1 and the grill in step 2. Each harness gives them differently; the contract of each step is the same everywhere.

| Step | Claude Code | Codex | Pi |
|---|---|---|---|
| 1. Gather (fresh context, no inherited conversation) | a Task subagent, no fork of this session | its subagent run, no inherited context | the bundled gatherer: `python3 <this skill>/scripts/fresh_context.py --packet <packet>` |
| 2. Grill | the Skill tool with `grilling` | the `grilling` skill | `/skill:grilling` |

Pi has no subagent tool, so the gatherer is a script: it runs the packet in a separate `pi --print` session with a fresh session directory, no parent conversation, a timeout and a restricted tool set, and it validates the answer against a strict schema. When it times out, the subprocess fails or the answer is malformed, it exits non-zero and the plan stops: never continue into the plan on evidence the gatherer never produced. The packet template is [`references/gather-packet.md`](references/gather-packet.md).

Paths in this skill are relative to the skill directory (the harness tells you where it lives).

`grilling` is an upstream skill and is not vendored here. Check it before step 2:

```
python3 <this skill>/scripts/check_deps.py grilling
```

It prints `FOUND grilling: <path>` when the skill is installed, and exits non-zero with the install command when it is not. A missing `grilling` stops the plan: never skip the grill, never answer the questions the grill would have asked yourself.

## 1. Gather

A PRD is not a gate. Plan an idea or task from the request and whatever sources exist; the request itself is a source. Suggest `/to-spec` only when the work hinges on a product decision (who it is for, what users get, whether to build it) that no PRD settles, and keep planning unless the user chooses to write one. A product question that surfaces later goes to the PRD owner, or to the user when there is no PRD, not into the plan.

Dispatch a fresh-context gatherer: an agent that inherits no conversation from this session and forks nothing. Under Claude Code and Codex it is a medium-class ([class](../orchestrate/references/routing.md#class-to-model)) subagent; under Pi it is the bundled gatherer above. It lists every source with its link (the request, the PRD if any, the Linear project and issues, the vault project note and its decision notes, RFCs, the living spec for the area), extracts each decision they already settle with its source, and reads the code the feature touches. When a decision depends on real data (backfill, migration, existing records), it runs read-only queries and returns the counts and edge cases: empty sets, conflicts, departed or archived owners.

The gatherer's answer is the only evidence you may use: its Sources table and the decisions it settled with their sources. Do not fill a gap it left with your own recollection of the conversation.

Done when the gatherer has returned the Sources table and every settled decision with its source.

## 2. Grill the gaps

Invoke the `grilling` skill on the decisions the sources leave open or contradict, bringing Gather's counts and edge cases into the questions (see Harness adapters: Claude Code calls the Skill tool, Pi runs `/skill:grilling`). Settled decisions enter the plan unasked, with their source.

Done when the grilling frontier is empty.

## 3. Write the plan

Keep these headings and columns: other skills parse them.

```markdown
# Plan: <feature>

Slug: `<slug>`. Living spec: `docs/specs/<area>.md`. Status: AWAITING APPROVAL.

## Why now
## Sources        (table: Source | What it settles)
## Decisions      (table: # | Choice | Rejected | Why | Source)
## Scenarios
- **S1** WHEN <condition>, THEN <observable outcome>.
## Out of scope
## Risks          (security, performance, migration, rollback: each covered or n/a)
## Seams          (where tests attach: the highest existing seam, as few as possible)
## Tickets
| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | <end-to-end behaviour> | S1, S2 | none | src/feature/, tests/feature.test.ts | regular | simple | agent | TO-DO |
```

Each scenario is one observable behaviour that a test would catch if it broke. IDs are `S<n>`, with an optional letter suffix (`S4a`). Every requirement becomes a scenario; one you can't phrase as WHEN/THEN is an open decision, so take it back to step 2.

Done when every requirement is a scenario, every decision row names its rejected option and source, and Risks has all four lines.

## 4. Slice into tickets

Each ticket is a **tracer bullet**: one narrow path through every layer it needs (schema, API, UI, test), landing as one PR under ~800 hand-written lines.

- **Satisfies**: the S-IDs the ticket makes true, as a comma list or a range (`S1–S4`). Every scenario sits in some ticket's Satisfies.
- **Blocked by**: the ticket IDs that must merge first, comma-separated, or `none`. A blocked ticket branches from main after its blockers merge; stacked branches break under squash merge.
- **Paths**: the repo-relative files, directories (ending `/`) or globs the ticket may change, comma-separated. The build is fenced to them.
- **Size** (`small | regular | big`) and **Difficulty** (`simple | complex`): judged by orchestrate's [routing](../orchestrate/references/routing.md), they pick the ticket's worker. A person-owned ticket leaves both empty.
- **Owner**: `agent` for code. Every step a person runs or approves (prod data apply, sign-off, deploy) is its own ticket with that person as Owner; a code PR never closes it.
- **Status**: TO-DO, IN PROGRESS or COMPLETE.

A wide mechanical refactor runs as expand–contract: expand, one ticket per migrate batch, then contract.

When the repo is tracked in Linear, create one sub-issue per ticket under the feature issue. The plan stays the source of truth.

Done when every scenario appears in some ticket's Satisfies.

## 5. Approve

Show the plan path, the decisions, the scenarios and the tickets table with each Size and Difficulty, then stop for one approval. Build nothing at this point. On approval, set `Status: APPROVED <date>` and hand off to `/orchestrate <plan-path>`.
