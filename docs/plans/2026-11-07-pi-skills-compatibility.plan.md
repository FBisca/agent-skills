# Plan: Make Existing Agent Skills Usable from Pi

Slug: `pi-skills-compatibility`. Living spec: `docs/specs/harness-portability.md`. Status: **APPROVED — READY FOR EXECUTION**.

## Why now

After standalone Pi works, it must be able to invoke the existing `start-planning` and related skills before it can build the rest of the migration. Pi discovers the same `SKILL.md` files, but Claude-specific instructions such as calling `Skill` and native `Task`/fresh-context subagents cannot be assumed to work identically. Preserve Claude and Codex behavior.

## Sources

| Source | What it settles |
|---|---|
| https://github.com/FBisca/agent-skills/blob/main/skills/start-planning/SKILL.md | Planning format, fresh-context gather and `grilling` dependency. |
| https://github.com/FBisca/agent-skills/blob/main/skills/orchestrate/SKILL.md | Launcher invokes the Python driver and requires approved plan shape. |
| https://github.com/FBisca/agent-skills/blob/main/AGENTS.md | Offline test runner is the gate; fakes require terminal answers. |
| https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/skills.md | Pi skill discovery and `/skill:name` invocation. |
| https://pi.dev/ | Pi has no default subagent tool or built-in plan mode. |
| https://raw.githubusercontent.com/FBisca/agent-skills/main/skills/orchestrate/references/routing.md | 2026-11-06 routing calibration and class table dependency. |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | Make existing skills harness-neutral where possible, add minimal conditional adapters. | Fork `pi-*` versions of every skill. | One shared source of truth. | User request; Pi skills docs |
| D2 | Support Pi `/skill:grilling` or a genuine fresh-context subprocess for planning instead of pretending Claude `Skill`/Task tools exist. | Silent no-op for these steps. | Preserve the planning contract. | start-planning skill; Pi docs |
| D3 | Keep `/orchestrate` implementation support out of this plan until runtime Pi lead integration exists. | Rewrite Python driver during skill portability. | Avoid PR #39/#45 conflicts and uncontrolled scope. | orchestrate skill; open runtime PRs |
| D4 | Extend offline unit/static checks and retain `scripts/run-tests.sh` as the gate. | Manual verification only. | Avoid regressions across Claude/Codex. | AGENTS.md |

## Binding P1 contract — Q4, Q8–Q10, Q16, Q24–Q25

- One authoritative skill source. Native `/skill:start-planning` syntax is acceptable; equivalent **behaviour** matters, including approval stop, decisions, scenarios, vertical tickets, and failure-on-missing-prerequisites.
- Treat discovery, invocation and behaviour as **three distinct tests**. A slash command rendering successfully does not prove fresh-context gather or grilling works.
- Fresh-context reviewer/gatherer: spawn bounded `pi --print` or supported noninteractive subprocess in a separate session/worktree with explicit task packet, limited actions, strict return schema and timeout; do **not** inherit parent conversation and do not require `agent-runtime` at P1.
- Do not assume `grilling` is vendored. Detect whether independently installed and provide clear instructions / fail early if absent. No silent skip of a required planning step.
- Keep all updated skills functional in Claude Code/Codex; regression-test tool names and independent review/approval semantics.

## Scenarios

- **S1** WHEN `/skill:start-planning` is invoked in Pi, THEN it loads the existing planning contract and produces a plan with exact required headings, scenarios and ticket columns.
- **S2** WHEN a skill requires `grilling` or a fresh-context reader under Pi, THEN an explicitly supported Pi-compatible invocation runs or reports a clear unsupported dependency, never silently skips it.
- **S3** WHEN the same skill executes under Claude Code or Codex, THEN its existing commands and validation behavior remain unchanged.
- **S4** WHEN the test suite runs offline, THEN harness portability and required Markdown plan contracts are enforced.

## Out of scope

- Pi-to-Pi worker spawning, agent-runtime lifecycle hooks, Pi-run `/orchestrate` launches and model-class routing migration.

## Risks

- **Security:** subprocess or extension-based skills must not bypass approval gates or tool limitations.
- **Performance:** fresh-context startup can increase latency; prefer one bounded gather over repeated re-reading.
- **Migration:** changes to shared skills affect every harness; test Claude/Codex paths in CI.
- **Rollback:** revert only portability adaptations; existing `SKILL.md` sources remain usable.

## Seams

- Existing `scripts/run-tests.sh` and skill lint tests.
- End-to-end plan artifact validation; smoke run `/skill:start-planning` inside Pi with no runtime MCP.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | Make `start-planning` and its grilling/fresh-context handoffs genuinely usable on Pi while retaining Claude/Codex paths and treating `grilling` as a separately installed skill if it is not vendored. | S1, S2, S3 | none | `skills/start-planning/`, `tests/`, `docs/` | regular | complex | agent | TO-DO |
| T2 | Add portable invocation checks and regressions across high-priority skills; document unsupported tools explicitly. | S3, S4 | T1 | `tests/`, `README.md`, `docs/` | regular | simple | agent | TO-DO |
| T3 | Manually produce and validate a real plan with MiniMax on Pi, then sign off. | S1, S2 | T2 | `docs/plans/` |  |  | user | TO-DO |

**Dependency:** `dotfiles/2026-11-07-pi-bootstrap.plan.md` has reached manual Pi smoke verification.


## P1 reviewer adversarial cases

- WHEN Pi sees a valid `SKILL.md` but lacks a `Skill`/`Task` tool equivalent, THEN it must take the documented adapter path or stop with a concrete unsupported-tool failure (not claim success).
- WHEN fresh-context gathering fails/times out/returns malformed findings, THEN the parent must not fabricate evidence or silently continue into ticket generation.
- WHEN parent context has sensitive credentials, THEN subprocess packet includes only references/allowed paths and necessary nonsecret task facts.
- Testing order: parser/discovery -> fresh-context process -> generated plan contract -> same skill smoke under Claude/Codex.

**Status: APPROVED — READY FOR EXECUTION. Implementation not yet started.**
