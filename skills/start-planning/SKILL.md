---
name: start-planning
description: Plan one feature spec-driven, from its sources to WHEN/THEN scenarios and the vertical tickets whose tests prove them, then stop for approval. Use when the user wants to plan a feature, idea or task, says "let's plan X", or hands over a PRD, Linear issue or vault note to build.
---

# Start planning

**Input:** a feature, idea or task, plus whatever already describes it: a PRD, Linear issues, vault notes, a living spec, or only the request itself.
**Output:** one approved **plan**: one folder in the repository's plan directory, `<plans.dir>/YYYY-MM-DD-<slug>/`, named for the day it is written and never re-dated:

- `plan.yaml`, the **contract** (`plan/1`): goal, scenarios, tickets. `plan approve` digests it.
- `brief.md`, the **brief**: the plan's diff in plain words, and its decisions. Not digested.

**Hand-off:** `/orchestrate <plan.yaml>` builds it.

Three documents, three jobs: the **PRD**, when there is one, says why and for whom; the **plan** turns one piece of the work into testable scenarios and tickets; the **living spec** (the contract's `spec`) records what the system does today.

The plan's one invariant: **an implementation provides its evidence.** The plan declares what must become true; the ticket that makes a scenario true writes the tests that prove it, and its report's `covers` maps the scenario to those test nodes. The plan holds no tests and runs nothing.

`<engine>` below is `python3 <skill-dir>/../orchestrate/scripts/orchestrate.py`, the orchestrate skill's hand-off to the engine. The engine owns the plan format: its `plan check` is the authority on the contract, and [references/plan-yaml.md](references/plan-yaml.md) is the skeleton to write from.

## Delegation

Steps 2 and 6 need a fresh-context agent; step 3 needs another skill.

- **Gather** and **scenario review**: dispatch through agent-runtime's `spawn` (`kind: worker`, `cli` this session's harness, the lane's class as `model`), with the packet as its `task`. `wait` on it; its report is the answer.
- **Grill**: the `grilling` skill, which asks the user.

Each delegation must be bounded and explicit:

- **No inherited context**: the agent starts from its packet alone, never from this conversation.
- **Bounded**: it runs under a timeout, the `wait` you give it.
- **Read-only**: it reads; it changes nothing in the repository.
- **Structured findings**: it answers with the JSON object its packet's return format names.
- **Fails loudly**: a spawn failure, a timeout, a missing report or a malformed answer fails the step. `collect` diagnoses a missing report; it never stands in for one.

When the gather fails, stop: never continue into the plan on evidence it did not produce. A failed review is the exception (step 6).

`grilling` is an upstream skill (`skills.lock.json`), installed separately. Before the grill run `python3 <skill-dir>/scripts/check_deps.py grilling`: it prints `FOUND grilling: <path>`, or exits non-zero naming the install command (`scripts/install-upstream.sh grilling`). When it is missing, stop and name that command; never answer its questions yourself and never skip the grill.

## 0. Pick the lane

The **lane** sizes the planning to the work. Judge the request by orchestrate's [routing](../orchestrate/references/routing.md) size and difficulty, from the request and a glance at the code it names (a few files; the gather has not run):

- **Fast**: small · simple, one ticket, every decision settled, no `risk` tag (step 5). Build it in this session instead of planning it: a red test, the fix, the living spec's requirement when there is one, one PR. Steps 1–8 stay unrun.
- **Standard**: regular · simple, or small · complex; one or two tickets; no `risk` tag.
- **Full**: regular · complex, any `risk` tag, or more than two tickets.

| Step | Standard | Full |
|---|---|---|
| 2. Gather | small class | medium class |
| 6. Scenario review | skipped | large class |

Every other step runs the same in both lanes.

Say the lane and its reason in one line; the user may override it. When a later step finds more work (a decision the gather leaves open, a `risk` tag, a third ticket), move up a lane and say so. A lane only moves up.

Done when the user has seen the lane and its reason; for Fast, when the in-session build has started.

## 1. Read the repo config

The repo config, `<repo>/.orchestrate/config.yaml`, names two things; an absent file or node means its default:

- `plans.dir` (default `docs/plans`): where the plan folder goes. It may sit outside the repository, with the config itself gitignored, so a repository the user keeps untouched still hosts plans.
- `archive.mode` (default `promote`): `promote` writes the scenarios into the living spec and deletes the plan folder; `discard` deletes the plan folder and writes nothing.

Run `<engine> plans list --json` to see the plans already there; it refuses an unknown config key, naming it. Create `plans.dir` on the first write.

Done when the plans dir and the archive mode are known.

## 2. Gather

A PRD is not a gate. Plan an idea or task from the request and whatever sources exist; the request itself is a source. Suggest `/to-spec` only when the work hinges on a product decision (who it is for, what users get, whether to build it) that no PRD settles, and keep planning unless the user chooses to write one. A product question that surfaces later goes to the PRD owner, or to the user when there is no PRD, not into the plan.

Dispatch a fresh-context gatherer (see Delegation) with [the gather packet](references/gather-packet.md). It lists every source with its link (the request, the PRD if any, the Linear project and issues, the vault project note and its decision notes, RFCs, the living spec for the area), extracts each decision they already settle with its source, and reads the code the feature touches, naming its seams: the CLI, HTTP, tool and public entry points, and the test fixtures, where a test can drive the feature from outside. When a decision depends on real data (backfill, migration, existing records), it runs read-only queries and returns the counts and edge cases: empty sets, conflicts, departed or archived owners.

The gatherer's answer is the only evidence you may use: its Sources table and the decisions it settled with their sources. Do not fill a gap it left with your own recollection of the conversation.

Done when the gatherer has returned the Sources table, every settled decision with its source, and the seams.

## 3. Grill the gaps

Invoke the `grilling` skill on the decisions the sources leave open or contradict, bringing Gather's counts and edge cases into the questions. Settled decisions enter the plan unasked, with their source.

Create `brief.md` when the first decision settles and write each decision into its `## Decisions` as it settles, one line: `D<n> <choice>, over <rejected>: <why> (<source>)`.

Done when the grilling frontier is empty (with no decision open, it is empty already) and every decision, settled or grilled, has its line naming what it rejected and its source.

## 4. Write the scenarios

In `plan.yaml`, from [the skeleton](references/plan-yaml.md): `goal` in one sentence, `spec` the living spec, then the scenarios.

Each scenario is one observable behaviour that a test would catch if it broke: `id`, `when`, `then`. IDs are `S<n>`, with an optional letter suffix (`S4a`). Write `then` as what that test asserts, at a seam the gather named or an interface a settled decision fixes. Every requirement becomes a scenario; one you can't phrase as a WHEN/THEN a test proves is an open decision, so take it back to step 3.

Done when every requirement is a scenario and each `then` names an outcome a test can observe.

## 5. Slice into tickets

Each ticket is a **tracer bullet**: one narrow path through every layer it needs (schema, API, UI, test), landing as one PR under ~800 hand-written lines. It writes the tests that prove the scenarios it satisfies.

- **`satisfies`**: the scenario IDs the ticket makes true. Every scenario sits in some ticket's `satisfies`.
- **`blocked_by`**: the ticket IDs that must merge first. A blocked ticket branches from main after its blockers merge; stacked branches break under squash merge.
- **`paths`**: the literal repo-relative files and directories (ending `/`) the ticket may change; no globs. The build is fenced to them, so an agent ticket's `paths` hold the test file or directory its covering tests go in, and a ticket that changes a test some other ticket's behaviour breaks owns that test too.
- **`size`** (`small | regular`) and **`difficulty`** (`simple | complex`): judged by orchestrate's [routing](../orchestrate/references/routing.md), they pick the ticket's worker. `big` is not a size: split the work into two tickets.
- **`owner`**: `agent` for code. Every step a person runs or approves (prod data apply, sign-off, deploy, work in another repository) is its own ticket with that person as owner, no `size` or `difficulty`, and `repo` when it is elsewhere; a code PR never closes it.
- **`risk`**: tag a ticket `security`, `concurrency`, `retry-idempotency`, `migration`, `external` or `state` when it carries that risk, and give the risk a scenario its tests prove.

A wide mechanical refactor runs as expand–contract: expand, one ticket per migrate batch, then contract.

When the repo is tracked in Linear, create one sub-issue per ticket under the feature issue. The plan stays the source of truth.

Done when every scenario appears in some ticket's `satisfies` and every agent ticket's `paths` hold a test location.

## 6. Check and review

1. Run `<engine> plan check <plan.yaml>` and fix every line it prints, until it exits 0.
2. In the Full lane, dispatch one fresh-context scenario reviewer on the large class (see Delegation). Its packet: the contract, the brief's Decisions and the gather's seams; never this session's reasoning. It returns, for each scenario, the test that would prove it (the seam it drives, the assertion on `then`) or `untestable` with the reason, and for each risk-tagged ticket, the scenario that pins its risk or none.
3. Fix the findings you agree with, run `plan check` on what changed, and stop: one round.

The review is advisory: what you leave open goes to the approval. A review that fails or times out is retried once, narrowed to one scenario or one ticket; when that also fails, the review is unperformed and the approval says the scenarios are unreviewed.

Done when `plan check` exits 0 on the final contract and the review, when the lane runs it, has returned or been declared unperformed.

## 7. Write the brief

Finish `brief.md` around the Decisions step 3 wrote: the plan's **diff** in plain words, what a person reads before approving. It cites scenario and ticket IDs; their text lives in the contract.

```markdown
# Brief: <feature>

Slug: `<slug>`. Contract: `plan.yaml`. Lane: <lane>, <its reason>.

## What changes   (one line per behaviour: `<path or area>`: before → after (T<n>))
## Decisions      (written at step 3)
## Out of scope   (one line; drop the heading when nothing is)
## Risks          (one line per tagged risk: the scenario that proves it; drop the heading when none)
```

Write each line as the change itself, the way a commit message would; the reasoning behind it belongs to its decision line.

Done when every ticket's `delivers` reads as a What changes line.

## 8. Approve

Show the lane, the plan folder, the decisions, the scenarios, the tickets with each size and difficulty, and the scenario review's open findings (or that it went unperformed); then stop for one approval. Build nothing at this point.

On the user's yes, run `<engine> plan approve <plan.yaml>`. It records the approval in the contract and digests `plan.yaml`; it runs nothing. When it refuses, fix what it names; a fix that changes the plan needs the user's yes again. Any later edit to the contract needs a new `plan approve`.

Then hand off to `/orchestrate <plan.yaml>`.
