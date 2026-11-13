---
name: start-planning
description: Plan one feature spec-driven, from its sources to WHEN/THEN scenarios, their evidence and vertical tickets, then stop for approval. Use when the user wants to plan a feature, idea or task, says "let's plan X", or hands over a PRD, Linear issue or vault note to build.
---

# Start planning

**Input:** a feature, idea or task, plus whatever already describes it: a PRD, Linear issues, vault notes, a living spec, or only the request itself.
**Output:** one approved **plan**: one folder in the repository's plan directory, `<plans.dir>/YYYY-MM-DD-<slug>/`, named for the day it is written and never re-dated:

- `plan.yaml`, the **contract** (`plan/1`): goal, scenarios, evidence, tickets. `plan approve` digests it.
- `brief.md`, the **brief**: the plan's diff in plain words, and its decisions. Not digested.
- `acceptance/`, the **acceptance tests** the evidence runs, under the names they keep once promoted; `negatives/` beside it when evidence carries a `negative` patch. `plan approve` digests both.

**Hand-off:** `/orchestrate <plan.yaml>` builds it.

Three documents, three jobs: the **PRD**, when there is one, says why and for whom; the **plan** turns one piece of the work into testable scenarios and tickets; the **living spec** (the contract's `spec`) records what the system does today.

`<engine>` below is `python3 <skill-dir>/../orchestrate/scripts/orchestrate.py`, the orchestrate skill's hand-off to the engine. The engine owns the plan format: its `plan check` is the authority on the contract, and [references/plan-yaml.md](references/plan-yaml.md) is the skeleton to write from.

## Delegation

Steps 2 and 7 need another context; step 3 needs another skill.

- **Gather** and **evidence review**: a fresh-context agent — a subagent with no inherited context and no fork of this session.
- **Grill**: the `grilling` skill, which asks the user.

Each delegation must be bounded and explicit: it runs under a timeout, it returns structured findings, and it fails loudly. When it times out, fails or returns anything else, stop: never continue into the plan on evidence it did not produce.

`grilling` is an upstream skill, installed separately. When it is missing, stop and name the install command; never answer its questions yourself and never skip the grill.

A harness with no subagent of its own dispatches through the adapter this skill ships, `scripts/fresh_context.py`. [references/delegation.md](references/delegation.md) has the per-harness dispatch, the packet, the result schema and the failure codes.

## 0. Pick the lane

The **lane** sizes the planning to the work. Judge the request by orchestrate's [routing](../orchestrate/references/routing.md) size and difficulty, from the request and a glance at the code it names (a few files; the gather has not run):

- **Fast**: small · simple, one ticket, every decision settled, no `risk` tag (step 5). Build it in this session instead of planning it: a red test, the fix, the living spec's requirement when there is one, one PR. Steps 1–8 stay unrun.
- **Standard**: regular · simple, or small · complex; one or two tickets; no `risk` tag.
- **Full**: regular · complex, any `risk` tag, or more than two tickets.

| Step | Standard | Full |
|---|---|---|
| 2. Gather | small class | medium class |
| 7. Evidence review | only when the plan adds an acceptance test; medium class | always; large class |

Every other step runs the same in both lanes.

Say the lane and its reason in one line; the user may override it. When a later step finds more work (a decision the gather leaves open, a `risk` tag, a third ticket), move up a lane and say so. A lane only moves up.

Done when the user has seen the lane and its reason; for Fast, when the in-session build has started.

## 1. Read the repo config

The repo config, `<repo>/.orchestrate/config.yaml`, names three things; an absent file or node means its default:

- `plans.dir` (default `docs/plans`): where the plan folder goes. It may sit outside the repository, with the config itself gitignored, so a repository the user keeps untouched still hosts plans.
- `acceptance.dir` (default `acceptance`): the directory inside each package that promoted acceptance tests join.
- `archive.mode` (default `promote`): `promote` moves the acceptance tests into the package and writes the living spec; `discard` deletes the plan folder and writes nothing.

Run `<engine> plans list --json` to see the plans already there; it refuses an unknown config key, naming it. Create `plans.dir` on the first write.

Done when the plans dir, the acceptance dir and the archive mode are known.

## 2. Gather

A PRD is not a gate. Plan an idea or task from the request and whatever sources exist; the request itself is a source. Suggest `/to-spec` only when the work hinges on a product decision (who it is for, what users get, whether to build it) that no PRD settles, and keep planning unless the user chooses to write one. A product question that surfaces later goes to the PRD owner, or to the user when there is no PRD, not into the plan.

Dispatch a fresh-context gatherer (see Delegation): where the harness has model classes, on the lane's [class](../orchestrate/references/routing.md#class-to-model). It lists every source with its link (the request, the PRD if any, the Linear project and issues, the vault project note and its decision notes, RFCs, the living spec for the area), extracts each decision they already settle with its source, and reads the code the feature touches, naming its seams: the CLI, HTTP, tool and public entry points, and the test fixtures, where a test can drive the feature from outside. When a decision depends on real data (backfill, migration, existing records), it runs read-only queries and returns the counts and edge cases: empty sets, conflicts, departed or archived owners.

The gatherer's answer is the only evidence you may use: its Sources table and the decisions it settled with their sources. Do not fill a gap it left with your own recollection of the conversation.

Done when the gatherer has returned the Sources table, every settled decision with its source, and the seams.

## 3. Grill the gaps

Invoke the `grilling` skill on the decisions the sources leave open or contradict, bringing Gather's counts and edge cases into the questions. Settled decisions enter the plan unasked, with their source.

Done when the grilling frontier is empty; with no decision open, it is empty already.

## 4. Write the scenarios and their evidence

In `plan.yaml`, from [the skeleton](references/plan-yaml.md): `goal` in one sentence, `spec` the living spec, `domain` when the plan promotes, then the scenarios.

Each scenario is one observable behaviour that a test would catch if it broke: `id`, `when`, `then`. IDs are `S<n>`, with an optional letter suffix (`S4a`). Every requirement becomes a scenario; one you can't phrase as WHEN/THEN is an open decision, so take it back to step 3.

`outcome` lists the scenarios that prove the goal on the integrated tree; each carries evidence. Evidence is for the outcome and for the scenarios a risk-tagged ticket satisfies. Every other scenario is covered by the tests its ticket writes, the reviewer and CI.

Write evidence by the **evidence ladder**, taking the first rung that holds:

1. **Reuse**: a `check` that runs an existing test.
2. **Command**: a `check` over an observable (a CLI's output, a file, an exit code).
3. **Black-box acceptance test**: a new test at an existing seam.
4. **Contract-first acceptance test**: a new test against an interface a settled decision fixes.
5. **Human**: `human: <what a person confirms>`.

An acceptance test targets only an interface that exists or that a settled decision fixes; when neither holds, the decision is open: back to step 3. It drives the outermost stable seam and imports the system under test lazily, so it collects cleanly at base. `baseline` is what the check does at base today: `fail` for behaviour still to build, `pass` for behaviour it must keep.

An acceptance test lives in the plan folder's `acceptance/`; its evidence names it in `acceptance:` with `package:`, the package directory it belongs to (`.` at the root of a single-package repository). The engine places it at `<package>/<acceptance.dir>/<domain>/<file>` for every check, and a promoting archive moves it there for good. Its basename differs from every test module already in the package: pytest imports modules by basename.

The **`domain`** is the area of behaviour the promoted tests join: a `[a-z0-9-]+` slug naming a folder under `<package>/<acceptance.dir>/`. Reuse an existing one when the plan's tests belong with it; otherwise propose a name for the area (`archive`, `discovery`), never the plan's slug or the package's name, which change or repeat. A plan whose acceptance tests are not worth keeping sets `archive: discard`, and then needs neither `spec` nor `domain`.

After writing or editing each Python acceptance file, run `python3 <skill-dir>/scripts/format_acceptance.py --repo <repo> <file> <package>/<acceptance.dir>/<domain>/`. When the repository configures ruff, it formats the file as ruff formats its destination, so the byte-identical copy promoted at archive passes the format gate; otherwise it leaves the file as written.

Done when every outcome scenario has evidence, a promoting plan has its `domain`, and every Python acceptance file has been through `format_acceptance.py` since its last edit.

## 5. Slice into tickets

Each ticket is a **tracer bullet**: one narrow path through every layer it needs (schema, API, UI, test), landing as one PR under ~800 hand-written lines.

- **`satisfies`**: the scenario IDs the ticket makes true. Every scenario sits in some ticket's `satisfies`.
- **`blocked_by`**: the ticket IDs that must merge first. A blocked ticket branches from main after its blockers merge; stacked branches break under squash merge.
- **`paths`**: the literal repo-relative files and directories (ending `/`) the ticket may change; no globs. The build is fenced to them, and a ticket that changes a test some other ticket's behaviour breaks owns that test too.
- **`size`** (`small | regular`) and **`difficulty`** (`simple | complex`): judged by orchestrate's [routing](../orchestrate/references/routing.md), they pick the ticket's worker. `big` is not a size: split the work into two tickets.
- **`owner`**: `agent` for code. Every step a person runs or approves (prod data apply, sign-off, deploy, work in another repository) is its own ticket with that person as owner, no `size` or `difficulty`, and `repo` when it is elsewhere; a code PR never closes it.
- **`risk`**: tag a ticket `security`, `concurrency`, `retry-idempotency`, `migration`, `external` or `state` when it carries that risk. It then satisfies a scenario with evidence, or carries an `evidence_waiver` naming where the risk *is* verified.

A wide mechanical refactor runs as expand–contract: expand, one ticket per migrate batch, then contract.

When the repo is tracked in Linear, create one sub-issue per ticket under the feature issue. The plan stays the source of truth.

Done when every scenario appears in some ticket's `satisfies`, and every risk-tagged ticket has evidence or a waiver.

## 6. Write the brief

Write `brief.md`: the plan's **diff** in plain words, what a person reads before approving. It cites scenario and ticket IDs; their text lives in the contract.

```markdown
# Brief: <feature>

Slug: `<slug>`. Contract: `plan.yaml`. Lane: <lane>, <its reason>.

## What changes   (one line per behaviour: `<path or area>`: before → after (T<n>))
## Decisions      (one line each: D<n> <choice>, over <rejected>: <why> (<source>))
## Out of scope   (one line; drop the heading when nothing is)
## Risks          (one line per tagged risk: where it is verified; drop the heading when none)
```

Write each line as the change itself, the way a commit message would; the reasoning behind it belongs to its decision line.

Done when every ticket's `delivers` reads as a What changes line, and every decision line names what it rejected and its source.

## 7. Check and review

1. Run `<engine> plan check <plan.yaml>` and fix every line it prints, until it exits 0.
2. When the lane calls for it, dispatch one fresh-context evidence reviewer on the lane's class (see Delegation). Its packet: the contract, the acceptance files, and the brief's Decisions; never this session's reasoning. It returns, for each scenario with evidence, the assertion that checks its `then` (or none), and for each outcome scenario one counterexample: a wrong implementation its evidence would still pass.
3. Fix the findings you agree with, then run `plan check` and `format_acceptance.py` again on what changed.

The review is advisory: what you leave open goes to the approval.

Done when `plan check` exits 0 on the final contract and the review, when the lane runs it, has returned.

## 8. Approve

Show the lane, the plan folder, the decisions, the scenarios with their evidence, the tickets with each size and difficulty, and the evidence review's open findings; then stop for one approval. Build nothing at this point.

On the user's yes, run `<engine> plan approve <plan.yaml>`. It records the approval in the contract, snapshots the contract and its acceptance and negative files, and runs every evidence item at base against its `baseline`. When it refuses, fix what it names; a fix that changes the plan needs the user's yes again. Any later edit to the contract or a file in `acceptance/` or `negatives/` needs a new `plan approve`.

Then hand off to `/orchestrate <plan.yaml>`.
