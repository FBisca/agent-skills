---
name: start-planning
description: Plan one feature spec-driven, from its sources to WHEN/THEN scenarios and vertical tickets, then stop for approval. Use when the user wants to plan a feature, idea or task, says "let's plan X", or hands over a PRD, Linear issue or vault note to build.
---

# Start planning

**Input:** a feature, idea or task, plus whatever already describes it: a PRD, Linear issues, vault notes, a living spec, or only the request itself.
**Output:** one approved **plan** at `docs/plans/YYYY-MM-DD-<slug>.plan.md`, dated the day it is written and never re-dated.
**Hand-off:** `/orchestrate <plan-path>` builds it.

Three documents, three jobs: the **PRD**, when there is one, says why and for whom; the **plan** turns one piece of the work into testable scenarios and tickets; the **living spec** (`docs/specs/<area>.md`) records what the system does today.

## Delegation

Step 1 needs another context; step 2 needs another skill.

- **Gather**: a fresh-context gatherer — a subagent with no inherited context and no fork of this session.
- **Grill**: the `grilling` skill, which asks the user.

The gather must be bounded and explicit: it runs under a timeout, it returns structured findings (the Sources table, the decisions with their sources, the findings, the counts and the edge cases), and it fails loudly. When it times out, fails or returns anything else, stop: never continue into the plan on evidence it did not produce.

`grilling` is an upstream skill, installed separately. When it is missing, stop and name the install command; never answer its questions yourself and never skip the grill.

A harness with no subagent of its own dispatches the gatherer through the adapter this skill ships, `scripts/fresh_context.py`. [references/delegation.md](references/delegation.md) has the per-harness dispatch, the packet, the result schema and the failure codes.

## 1. Gather

A PRD is not a gate. Plan an idea or task from the request and whatever sources exist; the request itself is a source. Suggest `/to-spec` only when the work hinges on a product decision (who it is for, what users get, whether to build it) that no PRD settles, and keep planning unless the user chooses to write one. A product question that surfaces later goes to the PRD owner, or to the user when there is no PRD, not into the plan.

Dispatch a fresh-context gatherer (see Delegation): where the harness has model classes, a medium-class ([class](../orchestrate/references/routing.md#class-to-model)) one. It lists every source with its link (the request, the PRD if any, the Linear project and issues, the vault project note and its decision notes, RFCs, the living spec for the area), extracts each decision they already settle with its source, and reads the code the feature touches. When a decision depends on real data (backfill, migration, existing records), it runs read-only queries and returns the counts and edge cases: empty sets, conflicts, departed or archived owners.

The gatherer's answer is the only evidence you may use: its Sources table and the decisions it settled with their sources. Do not fill a gap it left with your own recollection of the conversation.

Done when the gatherer has returned the Sources table and every settled decision with its source.

## 2. Grill the gaps

Invoke the `grilling` skill on the decisions the sources leave open or contradict, bringing Gather's counts and edge cases into the questions. Settled decisions enter the plan unasked, with their source.

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
- **Size** (`small | regular`) and **Difficulty** (`simple | complex`): judged by orchestrate's [routing](../orchestrate/references/routing.md), they pick the ticket's worker. A person-owned ticket leaves both empty. `big` is not a size: the driver refuses such a ticket, so split the work into two tickets.
- **Owner**: `agent` for code. Every step a person runs or approves (prod data apply, sign-off, deploy) is its own ticket with that person as Owner; a code PR never closes it.
- **Status**: TO-DO, IN PROGRESS or COMPLETE.

A wide mechanical refactor runs as expand–contract: expand, one ticket per migrate batch, then contract.

When the repo is tracked in Linear, create one sub-issue per ticket under the feature issue. The plan stays the source of truth.

Done when every scenario appears in some ticket's Satisfies.

## 5. Approve

Show the plan path, the decisions, the scenarios and the tickets table with each Size and Difficulty, then stop for one approval. Build nothing at this point. On approval, set `Status: APPROVED <date>` and hand off to `/orchestrate <plan-path>`.
