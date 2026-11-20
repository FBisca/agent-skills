---
name: start-planning
description: Plan one feature spec-driven, from its sources to the requirement changes. Use when the user wants to plan a feature, idea or task, says "let's plan X".
---

# Start planning

**You own the contract, not the code.** Gather, decide, write the plan, check it, stop for approval.

**Input:** a feature, idea or task, and whatever describes it: a PRD, issues, docs, the spec, or only the request.
**Output:** `<plans.dir>/YYYY-MM-DD-<slug>/`, dated the day it is written:

- `plan.yaml`, the **contract** (`plan/2`, from [the skeleton](references/plan-yaml.md)): the requirement changes with their scenarios, and the tickets. `plan check` is its authority; `plan approve` digests it.
- `brief.md`, the **brief** (from [the template](references/brief.md)): the review document the user reads and comments on, with a Reference for the worker. It cites the contract's IDs, never copies its text, and is not digested.

The **spec** (one capability per file) is what the system does today; the archive applies the plan's changes to it. **The implementation brings the evidence:** the ticket that satisfies a scenario writes its tests, tagged with the requirement's title, and maps them in its report's `covers`. The plan holds no tests.

`<engine>` is `python3 <skill-dir>/../orchestrate/scripts/orchestrate.py`. `<deps> <name>` is `python3 <skill-dir>/scripts/check_deps.py <name>`: it prints `FOUND <name>: <path>`, or exits non-zero naming the install command.

A **fresh agent** is agent-runtime's `spawn` (`kind: worker`, `cli` this session's harness, the class as `model`, the task), then `wait`; its report is the answer. A spawn failure, a timeout or a missing report fails it; `collect` diagnoses a missing report and never stands in for one. Once its report is read, or it has failed, `stop` it: no agent of this skill outlives its step.

To **ask** is to put a decision to the user through the harness's interactive question tool, one option per answer, the recommended one first; without such a tool, as a numbered list.

## 0. Lane

Pick the lane from [routing](../orchestrate/references/routing.md#lane). Direct builds it in this session and stops here.

Done when the user has seen the lane and its reason.

## 1. Config

`<engine> plans list --json` gives `plans.dir` (default `docs/plans`), `archive.mode` (default `promote`; `discard` when the repo keeps no living spec) and the plans already there. Create `plans.dir` on the first write.

Done when the plans dir and the archive mode are known.

## 2. Gather

A PRD is not a gate. A product call no source settles (who it is for, whether to build it) → suggest `/to-spec`, and keep planning unless the user writes one.

Spawn a fresh agent (medium class) with [the gather packet](references/gather-packet.md) as its task. It returns the sources with their links, the decisions they settle, the code the feature touches with its seams (CLI, HTTP, tool and public entry points; the test fixtures that drive them), and read-only counts and edge cases when a decision depends on real data.

Its answer is the only evidence: fill no gap from your memory of the conversation. When the gather fails, stop.

Done when the gatherer has returned its sources, its settled decisions and the seams, and is stopped.

## 3. Decide

At the first decision, create `brief.md` from the template; add each decision to its Decision log as a D-line as it settles.

- A fork a run can settle (prototype, query) → run it; the D-line cites the result.
- A decision the gather settled → put to the user in the grill for a yes, with its source.
- A product or preference call → the `grilling` skill, with the gather's counts and edge cases in the questions. Run `<deps> grilling` first; when it is missing, stop and name its install command: the grill runs through the skill or not at all.

When `<deps> i-have-adhd` finds it, read its `SKILL.md` and apply it to every grill round and to the step 8 reply.

A call the user defers in the grill keeps the plan's default and goes to the brief's Your calls.

Done when the user has answered or deferred every decision, and every D-line names what it rejected and its source.

## 4. Write the requirement changes

Read the spec first: a requirement's exact title decides added or modified. Fill `goal` (one sentence), `spec`, then `requirements`:

- **`added`**: a behaviour the spec lacks, under a title it does not hold.
- **`modified`**: a title the spec holds, restated whole; the archive replaces it.
- **`removed`**: a title the spec holds, with `why`.

An added or modified requirement is one SHALL sentence and 1–3 scenarios. Scenarios are what gets built and tested; write each with care:

- **One behaviour.** One WHEN, one THEN. An "and", an "until" or a second clause is two scenarios: a compound one gets half-tested.
- **Observable.** `then` is what a test asserts, at a seam the gather named or an interface a decision fixes.
- **Model behaviour.** A `then` only the model produces (Claude replies, lists, hands over) has no seam to test: a person's run is its evidence, in the ticket that runs it. No test of the skill's prose stands in.
- **Measured numbers.** A threshold, limit or timeout cites a measurement in the brief, or the ticket's first job measures it and the scenario says so: guessed numbers get disproved by the code. A number that is the requirement itself (`daily at 09:00`) needs neither.
- **No WHEN/THEN, no scenario.** A behaviour you cannot phrase that way is an open decision: back to step 3.

Done when every behaviour the plan changes sits under a requirement and every `then` names an outcome a test can observe.

## 5. Slice into tickets

Each ticket is a **tracer bullet**: one narrow path through every layer it needs, one PR under ~800 hand-written lines, writing the tests for the scenarios it satisfies.

- **`satisfies`**: the scenario IDs it makes true. Every scenario sits in some ticket.
- **`blocked_by`**: the tickets that merge first. A blocked ticket branches from main after they merge; stacked branches break under squash merge.
- **`paths`**: literal repo-relative files and directories (ending `/`), no globs. They are the starting map and the conflict map: the worker edits any file the change needs, and the gate refuses only a file another unfinished ticket lists. An agent ticket lists its tests' location; a ticket that breaks another ticket's test lists that test.
- **`size`** (`small | regular`) and **`difficulty`** (`simple | complex`): by [routing](../orchestrate/references/routing.md); they pick the worker. Work past `regular` is two tickets.
- **`owner`**: `agent` for code. A step a person runs or approves (prod data apply, sign-off, deploy, work in another repository) is its own ticket with that person as owner, no `size` or `difficulty`, and `repo` when it is elsewhere.
- **`risk`**: a ticket touching [sensitive](../orchestrate/references/routing.md#difficulty) code gets its tag (`security`, `concurrency`, `retry-idempotency`, `migration`, `external`, `state`) and a scenario that pins it.

A wide mechanical refactor runs expand–contract: expand, one ticket per migrate batch, contract. In a repository tracked in Linear, one sub-issue per ticket under the feature issue; the plan stays the source of truth.

Done when every scenario is in some `satisfies` and every agent ticket's `paths` hold a test location.

## 6. Check

Run `<engine> plan check <plan.yaml>` and fix every line it prints.

Done when it exits 0.

## 7. Write the brief

Fill every section of `brief.md`, by [its rules for the reviewer](references/brief.md#writing-for-the-reviewer). Above the rule its reader is the user, who approves; the Reference serves the worker, who builds. A decision that must be enforced becomes a scenario or a rule in the repository's rulebook, and review checks only those; any other decision is guidance. Keep implementation instructions ("inject it as a callable") out, or review polices coding choices instead of behaviour.

Done when every section is filled, every scenario ID appears in What changes and every ticket ID in Build order.

## 8. Approve

Build nothing yet. Reply with the plan path, the number of open calls and the number of tickets; the brief holds the rest. Then ask "Approve this plan?":

- **Approve**: with [the review's](references/brief.md#review) grep empty, run `<engine> plan approve <plan.yaml>` and fix whatever it refuses. With marks left, resolve them first and ask again.
- **I left comments**: resolve the marks per the review, reply with its line per mark, and ask again.
- Free text is a comment on the plan: resolve it the same way.

A later contract change needs the user's yes and `plan approve <plan.yaml> --reason "<why>"`. After approval, end the reply with the next command on its own line, the plan path filled in: `/orchestrate <plan.yaml>`.

Done when the review's grep prints nothing, `plan approve` exits 0 and the reply ends with the orchestrate command.
