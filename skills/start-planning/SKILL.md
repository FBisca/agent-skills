---
name: start-planning
description: Plan one feature spec-driven, from its sources to the requirement changes. Use when the user wants to plan a feature, idea or task, says "let's plan X".
---

# Start planning

**You own the contract, not the code.** Gather, decide, write the plan, check it, stop for approval.

**Input:** a feature, idea or task, plus whatever describes it: a PRD, issues, documentation, the spec, or only the request.
**Output:** one plan folder, `<plans.dir>/YYYY-MM-DD-<slug>/`, dated the day it is written:

- `plan.yaml`, the **contract** (`plan/2`): the requirements the plan adds to, modifies in or removes from its spec, each with its scenarios, and the tickets. `plan approve` digests it.
- `brief.md`, the **brief**: the design doc the user reviews and comments on in place. Its shape is in [references/brief.md](references/brief.md). Not digested.

The **spec** (`spec`, one capability per file) states what the system does today; the archive applies the plan's changes to it.

**An implementation provides its evidence.** The ticket that satisfies a scenario writes the tests that prove it, each tagged with its requirement's title, and maps the scenario to them in its report's `covers`. The plan holds no tests.

`<engine>` is `python3 <skill-dir>/../orchestrate/scripts/orchestrate.py`. Its `plan check` is the authority on the contract; [references/plan-yaml.md](references/plan-yaml.md) is the skeleton to write from.

## Delegation

The gather (step 2) runs in a fresh agent: agent-runtime's `spawn` (`kind: worker`, `cli` this session's harness, the medium class as `model`) with the packet as its `task`, then `wait`; its report is the answer. The agent works with no inherited context (its packet alone), under the `wait`'s timeout, read-only, answers with the structured JSON its packet names, and fails loudly: a spawn failure, a timeout, a missing report or a malformed answer fails the step. `collect` diagnoses a missing report; it never stands in for one.

`grilling` (step 3) is an upstream skill (`skills.lock.json`), installed separately. Before the grill run `python3 <skill-dir>/scripts/check_deps.py grilling`: it prints `FOUND grilling: <path>`, or exits non-zero naming the install command (`scripts/install-upstream.sh grilling`). When it is missing, stop and name that command; the grill runs through the skill or not at all.

## 0. Pick the lane

Pick the lane from [routing](../orchestrate/references/routing.md#lane); Direct builds it directly in this session and stops here.

Done when the user has seen the lane and its reason.

## 1. Read the repo config

`<engine> plans list --json` reads `.orchestrate/config.yaml`'s `plans.dir` (default `docs/plans`) and `archive.mode` (default `promote`; `discard` is for a repository with no living spec) and lists the plans already there. Create `plans.dir` on the first write.

Done when the plans dir and the archive mode are known.

## 2. Gather

Plan from the request and whatever sources exist; a PRD is not a gate. A product decision no source settles (who it is for, whether to build it) → suggest `/to-spec`, and keep planning unless the user chooses to write one.

Dispatch the gatherer (see Delegation) with [the gather packet](references/gather-packet.md). It returns every source with its link, each decision the sources settle with its source, the code the feature touches with its seams (the CLI, HTTP, tool and public entry points, and the test fixtures a test drives it from), and, when a decision depends on real data, read-only counts and edge cases.

Its answer is the only evidence: fill no gap from your recollection of the conversation. When the gather fails, stop: never continue into the plan on evidence it did not produce.

Done when the gatherer has returned its sources, its settled decisions and the seams.

## 3. Decide

Create `brief.md` with the first decision and write each into its `## Decisions` as it settles, one line: `D<n> <choice>, over <rejected>: <why> (<source>)`. Decisions the gather settled enter unasked, with their source.

- A fork a run can settle (prototype, query) → run it and record the D-line with its evidence.
- A product or preference call → the `grilling` skill, with the gather's counts and edge cases in the questions.

Each grill round:

- **At most 5 questions.** The rest of the frontier waits for the next round.
- **Opens with one state line:** decisions settled so far, the round number, and the estimated rounds left.
- **Mid-round questions** go into the next round.

Done when no decision is open and every decision has its D-line naming what it rejected and its source.

## 4. Write the requirement changes

Read the spec first: a requirement's exact title decides whether the plan adds or modifies it. In `plan.yaml`, from [the skeleton](references/plan-yaml.md): `goal` in one sentence, `spec` the capability's file, then `requirements`:

- **`added`**: a behaviour the spec lacks, under a title the spec does not hold.
- **`modified`**: a requirement the spec holds, by its exact title, restated whole: the archive replaces it.
- **`removed`**: a requirement the spec holds, by its exact title, with `why`.

An added or modified requirement is one `shall` sentence with SHALL and 1–3 scenarios. A scenario is one observable behaviour a test would catch if it broke: `id` (`S<n>`, plan-local), `when`, `then`, and an optional `name` for its spec heading. Write `then` as what that test asserts, at a seam the gather named or an interface a decision fixes: an observable behaviour. A scenario holds one behaviour: one WHEN, one THEN; a `when` or `then` that joins two behaviours (an "and", an "until", a second clause) is two scenarios, because a compound scenario gets half-tested. A threshold, limit or timeout cites a measurement in the brief, or the ticket's first job is to measure it and the scenario says so, because guessed numbers get disproved by the code and force plan amendments; a number that is itself the product requirement (`daily at 09:00`) needs neither. A behaviour you can't phrase as a WHEN/THEN is an open decision: take it back to step 3.

Done when every behaviour the plan changes sits under a requirement and each `then` names an outcome a test can observe.

## 5. Slice into tickets

Each ticket is a **tracer bullet**: one narrow path through every layer it needs, landing as one PR under ~800 hand-written lines. It writes the tests that prove the scenarios it satisfies.

- **`satisfies`**: the scenario IDs the ticket makes true. Every scenario sits in some ticket's `satisfies`.
- **`blocked_by`**: the tickets that must merge first. A blocked ticket branches from main after they merge; stacked branches break under squash merge.
- **`paths`**: the literal repo-relative files and directories (ending `/`) the ticket starts from; no globs. They are a starting map and the conflict map between tickets, so the worker edits any file the change needs and the gate refuses only one another unfinished ticket lists. An agent ticket's `paths` hold its tests' file or directory, and a ticket that breaks another ticket's test lists that test too.
- **`size`** (`small | regular`) and **`difficulty`** (`simple | complex`): by orchestrate's [routing](../orchestrate/references/routing.md); they pick the worker. Work past `regular` is two tickets.
- **`owner`**: `agent` for code. Each step a person runs or approves (prod data apply, sign-off, deploy, work in another repository) is its own ticket with that person as owner, no `size` or `difficulty`, and `repo` when it is elsewhere.
- **`risk`**: a ticket touching [sensitive](../orchestrate/references/routing.md#difficulty) code gets its tag (`security`, `concurrency`, `retry-idempotency`, `migration`, `external` or `state`) and a scenario that pins it.

A wide mechanical refactor runs as expand–contract: expand, one ticket per migrate batch, then contract. In a repository tracked in Linear, create one sub-issue per ticket under the feature issue; the plan stays the source of truth.

Done when every scenario appears in some ticket's `satisfies` and every agent ticket's `paths` hold a test location.

## 6. Check

Run `<engine> plan check <plan.yaml>` and fix every line it prints until it exits 0.

Done when `plan check` exits 0 on the final contract.

## 7. Write the brief

Finish `brief.md` per [references/brief.md](references/brief.md): every section, the copied Requirements and Tickets, and the header. Its Decisions were written at step 3.

The brief has two readers: the user, who approves the plan, and the worker, who builds it. A decision that must be enforced becomes a scenario (testable behaviour) or a rule in the repository's rulebook; any other decision is guidance for the worker, and review does not check it. The reviewer judges code against the scenarios and the rulebook only, so an implementation instruction in the brief ("inject it as a callable") would make it police coding choices instead of behaviour.

Done when every heading of [references/brief.md](references/brief.md) is present, Requirements and Tickets match `plan.yaml`, and every ticket's `delivers` reads as a What changes line.

## 8. Approve

Reply, then stop for one approval; build nothing yet. On a mark in brief.md, run the review round from [references/brief.md](references/brief.md) on it, reply again, and stop again. On the user's yes, run the round's grep: if it prints a mark, handle each one and reply again; approve only once it prints nothing. Then run `<engine> plan approve <plan.yaml>`: it records the approval and digests `plan.yaml`. When it refuses, fix what it names. A fix or any later edit that changes the contract needs the user's yes and a new `plan approve <plan.yaml> --reason "<why>"`.

Then hand off to `/orchestrate <plan.yaml>`.

**Reply:** the first line is the action: "Comment in brief.md, or say yes to approve (`plan approve <plan.yaml>`)." Then the lane and its cell, the plan path, the decisions, the requirement changes (added, modified, removed, by title), the tickets with size and difficulty, and what stays open. Show at most 5 items per group and name the count of the rest, which are in brief.md. The last line is the single next action.

Done when the grep prints nothing on brief.md and `plan approve` exits 0.
