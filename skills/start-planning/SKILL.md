---
name: start-planning
description: Plan one feature spec-driven, from its sources to WHEN/THEN scenarios and vertical tickets, then stop for approval. Use when the user wants to plan a feature, says "let's plan X", or hands over a PRD, Linear issue or vault note to build.
---

# Start planning

**Input:** a feature, plus whatever already describes it: a PRD, Linear issues, vault notes, a living spec.
**Output:** one approved **plan** at `docs/plans/YYYY-MM-DD-<slug>.plan.md`, dated the day it is written and never re-dated.
**Hand-off:** `/orchestrate <plan-path>` builds it.

Three documents, three jobs: the **PRD** says why and for whom; the **plan** turns one piece of it into testable scenarios and tickets; the **living spec** (`docs/specs/<area>.md`) records what the system does today.

## 1. Gather

When no PRD covers the feature, ask the user to run `/to-spec` and stop. Resume once the PRD exists. A product question that surfaces later goes back to the PRD owner, not into the plan.

Dispatch a fresh-context subagent to gather. It lists every source with its link (the PRD, the Linear project and issues, the vault project note and its decision notes, RFCs, the living spec for the area), extracts each decision they already settle with its source, and reads the code the feature touches. When a decision depends on real data (backfill, migration, existing records), it runs read-only queries and returns the counts and edge cases: empty sets, conflicts, departed or archived owners.

Done when the subagent has returned the Sources table and every settled decision with its source.

## 2. Grill the gaps

Call the Skill tool with `grilling` on the decisions the sources leave open or contradict, bringing Gather's counts and edge cases into the questions. Settled decisions enter the plan unasked, with their source.

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
| # | What it delivers | Satisfies | Blocked by | Paths | Owner | Status |
|---|---|---|---|---|---|---|
| T1 | <end-to-end behaviour> | S1, S2 | none | src/feature/, tests/feature.test.ts | agent | TO-DO |
```

Each scenario is one observable behaviour that a test would catch if it broke. IDs are `S<n>`, with an optional letter suffix (`S4a`). Every requirement becomes a scenario; one you can't phrase as WHEN/THEN is an open decision, so take it back to step 2.

Done when every requirement is a scenario, every decision row names its rejected option and source, and Risks has all four lines.

## 4. Slice into tickets

Each ticket is a **tracer bullet**: one narrow path through every layer it needs (schema, API, UI, test), landing as one PR under ~800 hand-written lines.

- **Satisfies**: the S-IDs the ticket makes true, as a comma list or a range (`S1–S4`). Every scenario sits in some ticket's Satisfies.
- **Blocked by**: the ticket IDs that must merge first, comma-separated, or `none`. A blocked ticket branches from main after its blockers merge; stacked branches break under squash merge.
- **Paths**: the repo-relative files, directories (ending `/`) or globs the ticket may change, comma-separated. The build is fenced to them.
- **Owner**: `agent` for code. Every step a person runs or approves (prod data apply, sign-off, deploy) is its own ticket with that person as Owner; a code PR never closes it.
- **Status**: TO-DO, IN PROGRESS or COMPLETE.

A wide mechanical refactor runs as expand–contract: expand, one ticket per migrate batch, then contract.

When the repo is tracked in Linear, create one sub-issue per ticket under the feature issue. The plan stays the source of truth.

Done when every scenario appears in some ticket's Satisfies.

## 5. Approve

Show the plan path, the decisions, the scenarios and the tickets table, then stop for one approval. Build nothing at this point. On approval, set `Status: APPROVED <date>` and hand off to `/orchestrate <plan-path>`.
