# Plan: orchestrate lean loop — Lead wakes, reviewer reuse, evidence findings, run telemetry

Slug: `orchestrate-lean-loop`. Living spec: `docs/specs/orchestrate.md`. Status: APPROVED 2026-11-06.

## Why now

The code-driven driver (plan `code-driven-orchestrator`) took the loop out of the LLM lead, but each gate still repeats work. Every review is a fresh reviewer reading the whole diff. Fix rounds pass on converge alone, so fix code reaches CI unreviewed. Findings carry no reasoning or evidence, so the implementer re-runs checks to find out why something failed. A fresh decider re-reads the plan the Lead already holds. Metrics are written only when the run stops, and token usage reads `unknown`. The T1–T6 reviews deferred 40+ items, most of them one of these gaps. Goal: no re-reads, re-tests or re-sent tokens that the run can avoid, every handoff structured and validated, and every run measured with a retro at the end.

This plan is built by the current driver. The Lead logs any driver friction it observes during the build (D15), and T8 compares the new driver's first run against this one.

## Sources

| Source | What it settles |
|---|---|
| Design session with Felippe, 2026-11-06 (decisions file `orchestrator-decisions.md`) | D1–D11 |
| `~/Downloads/test.excalidraw` (Felippe's flow diagram) | Flow: implementer → report.json → converge → reviewer → findings.json → rounds gate → Lead |
| `~/.local/state/orchestrate/code-driven-orchestrator/deferred.md` and T1–T6 review files | Defects absorbed by D2, D3, D6, D9, D11 and S10 (see Out of scope for the rest) |
| `docs/plans/2026-11-06-code-driven-orchestrator.plan.md` | Current driver: gates, ledger, contracts v1, launch, Herdr pane naming |
| `skills/orchestrate/scripts/orchestrate.py`, `contracts.py` | Current gate steps, `MAX_FIX_ROUNDS`, `context_verdict`, review/findings shape |
| agent-runtime plan `2026-11-06-call-ancestry-gate` (sibling) | D10: the `agent-runtime call` gate. Lives in agent-runtime; this plan does not depend on it |
| agent-runtime plan `2026-11-06-worker-token-metrics` | Token usage on wait/status; until it ships, usage stays `unknown` (D5c) |

## Decisions

| # | Choice | Rejected | Why | Source |
|---|---|---|---|---|
| D1 | The Lead (the LLM that launched the driver) settles every escalation; no decider agent | Fresh large decider, then Lead | The Lead already holds the plan's intent; a decider re-reads plan + task + findings | Felippe |
| D2 | The driver wakes the Lead on: decision needed, PR ready to merge, run finished, plan invalid, a unit idle at 2 consecutive idle ticks (`--idle-minutes`, default 10) | Waking on every ticket completion | Each wake adds to the Lead's context; the plan Status column already shows progress | Felippe |
| D2b | A wake is one line `<kind> <unit>: <reason> -> <path>`; `request.json` holds the evidence paths and the action menu | Inline digest in the wake | The Lead reads the file only when it needs to | Felippe |
| D2c | While a decision is pending, other units keep running; wakes queue in order | Pause dispatch | One stuck unit must not stall the run | Felippe |
| D3 | Every fix round (converge, review or CI source) goes back to the unit's same reviewer, resumed, with only `<last_reviewed>..HEAD`; nothing reaches CI unreviewed | Converge-only gate for fix rounds (today) | Fix code was reaching CI unreviewed; the delta avoids re-reading the whole diff | Felippe |
| D3b | A re-review checks each earlier finding (resolved or not, with evidence) and raises new blocking items only inside the delta | Full re-review | Stops new blockers appearing on code already reviewed | Felippe |
| D3c | One reviewer per unit: spawned once, resumed for each re-review, stopped when the unit merges or pauses | Stop between rounds | Warm cache; fixes the never-stopped reviewer pane (T3 D4) | Felippe |
| D4 | Review envelope v2: core `id, kind (blocking/concern/question/nit/deferred), summary, answer_required`. Blocking items also need `file, line, fix, evidence{command, exit, excerpt, log_path}`; `scenario, why, verify` are optional. Every other field is kept verbatim. The reviewer runs with its own instructions; only the envelope is validated | Fixed narrow schema (today's id/file/line/problem/fix) | The implementer fixes without rediscovering the problem; reviewers can bring their own rubric | Felippe |
| D4b | Converge and CI findings use the same evidence shape, filled by the driver from gate output | Text lines (today) | The worker never re-runs a check just to read why it failed | Felippe |
| D4c | The implementer answers, in `responses[] {id, status fixed/disputed, commit, note, changes_code?}`, only the items the reviewer marked `answer_required` | Answer every item; answer none | The reviewer decides what needs a reply | Felippe |
| D4d | The reviewer's `checks_run[] {command, exit, at_commit}` goes into findings; the implementer re-runs only what its fix touches plus the final gate | Full gate re-run every round | Removes duplicate test runs | Felippe |
| D4f | Verdict pass with answer_required items does not gate: the unit goes on to CI while the implementer is resumed for answers only. An answer `disputed` with `changes_code: true` goes back to the reviewer | Gate on the answers; ask the Lead | A question costs no round | Felippe |
| D4g | Nits and concerns without answer_required go only to `deferred.md` and the retro | Send them to the fix round as optional | Keeps fix rounds small | Felippe |
| D5 | Fix-round cap 2 by default; `--max-fix-rounds` and an optional plan line `Max fix rounds: T3=3, T5=1` under the Tickets table. The driver owns the counts and ignores `review_rounds` in the report | A column in the Tickets table; difficulty-based caps | A new column breaks the table parsing that assumes Status is last (T1 deferred); workers inflating counts (T2 D2) | Felippe; line format: Claude |
| D5b | Below the context reserve before a resume, the driver swaps in a fresh agent of the same class. Handoff: task.md, last report.json, findings.json, commit range; no transcript. Metrics only, no wake | Wake the Lead | Mechanical; no judgment needed | Felippe |
| D5c | Context usage unknown: resume and log `context: unknown` | Swap after N resumes as a stand-in | Behaviour corrects itself once worker-token-metrics ships | Felippe |
| D6 | The worker opens a draft PR with its report; CI runs during review; after the final pass the driver runs `gh pr ready` | PR after approval (diagram); the driver opens it | CI runs in parallel with review; no extra agent turn | Felippe |
| D6b | CI and merge are one non-blocking poll in the loop (checks green, then merged); "no checks yet" gets polled again | Blocking `wait-checks` for up to 600s (today) | Fixes T3 D1 (the loop stalls) and D2 (no checks treated as a failure) | Felippe |
| D6c | Approved + green + answers in: stop both panes; a unit waiting for merge holds no `--max-workers` slot | Keep panes warm until merge | Fixes T3 D3 (unmerged PRs stop all dispatch) | Felippe |
| D6d | Base drift: the driver runs `gh pr update-branch`. Clean: no review. Conflict: a fresh worker with a rebase task, then a delta re-review, counted as a round | Wake the Lead on any drift | Most drift is mechanical | Felippe |
| D6e | Felippe merges by hand at any time; a merge is final. Open findings go to `deferred.md` tagged `merged-early` | Wake the Lead on an early merge | A merge expresses the decision already | Felippe |
| D7 | Implementer and reviewer of one unit may use agent-runtime `message` directly. Each one is self-reported as `clarifications[] {finding, asked_by, note}` in report.json / review.json | Files only; the driver reading agent-runtime's store | Peer messages live in agent-runtime's private store; self-reporting keeps the driver off it | Felippe; tracking: Claude |
| D7b | Cross-unit needs: read the other unit's files and the plan Decisions, else `kind=decision` to the Lead; no messages to another unit's agents | Direct peer messages | Traceable; doesn't pull a busy agent off its own work | Felippe |
| D7c | `orchestrate.py show <plan> [--unit T<n>] --json` is the read-only view any agent may call; each call is logged as a `lookup` | Run-dir files only | Visibility on request instead of pushing it into prompts; counted | Felippe |
| D8 | The plan's Tickets table is the only task source. An edit to an in-flight ticket goes out as a "scope changed" diff on the next resume or re-review; an invalid edit is ignored (the driver keeps the last valid plan) and wakes the Lead once | A separate tasks.md; restart the unit | One source, so nothing drifts; keeps the work done | Felippe |
| D9 | Append-only `<run>/events.jsonl` (gate moves, wakes, findings, decisions, clarifications, lookups, contract errors, idle hits, swaps, merged-early). metrics.json is rolled up from it on stop or on demand | Rollup only at stop | Survives a crash (T5 D9); can be replayed | Felippe |
| D9b | Duplicate work is measured as the same `(command, commit)` across a unit's report `checks[]` and reviewer `checks_run[]` | Read hooks; token deltas | Cheap and deterministic | Felippe |
| D9c | At finish the driver writes `retro.md` tables; the Lead adds `## What to change` and proposes edits to Felippe; nothing is applied automatically | Numbers only; a retro agent | Retro without a fresh agent re-reading everything | Felippe |
| D11 | One `ensure_agent(unit, role)`: record the intent, spawn under a stable name, bind; on restart look the name up via status/list and re-attach | Fixing each spawn site separately | Same bug in T1 RESERVED, T2 D3/D6, T4 d5, T5 D10 | Felippe |
| D12 | Wake channel: the Lead runs `orchestrate.py await <plan>` as a background Bash command. It prints the next unprinted wake and exits, which re-invokes the Lead; the Lead starts it again after handling | The Lead polling `show`; agent-runtime messages to the Lead session | The Lead uses no tokens while waiting; the harness re-invokes it when the command exits | Claude |
| D13 | `orchestrate.py decide <plan> <unit> <action> --reason … [--answer …]` writes and validates `decision.json`. The menu is today's minus `ask user` (the Lead asks Felippe itself), plus `answer` (resume the worker with the Lead's text) | The Lead writing JSON by hand | Validation stays deterministic; a typo exits 2 | Claude |
| D14 | Contracts bump to version 2; the driver still reads v1 `review.json` (`major[]` as blocking items, `deferred[]` as deferred) and a run dir without `events.jsonl` | A clean break | This plan is built by the old driver; relaunching after a pause runs new code over an old run dir | Claude |
| D15 | During this build the Lead keeps `<run>/dogfood.md` (time, unit, what the driver did wrong or slowly, cost). At T8 each line becomes a follow-up ticket or a deferred row | Not tracking it | Felippe asked to watch the driver for improvements while it builds its successor | Felippe |
| D16 | The Lead's own context has no swap policy in this plan. Every wake stands alone (a line + path), so a Lead can be restarted and re-attach with `launch`. `events.jsonl` counts wakes per run | A context policy for the Lead | Measure first; decide in the T8 retro | Claude |
| D17 | `launch` nests the driver pane under the Lead's terminal (visible in Herdr under the Lead's agent) and the driver passes `--lead orchestrate:<slug>` on every `call`, so it resolves as a lead. Needs agent-runtime `call-ancestry-gate` T3 | Starting the pane without a parent (today's workaround); a slug truncated to fit the 32-character pane name | The first launch nested the pane and the driver resolved as a worker, so every spawn failed. The workaround makes the pane invisible in Herdr. Truncation hides which plan the pane belongs to | Felippe, 2026-11-06 (dogfood) |
| D18 | Speed mode for this plan's reviews. Block only on MAJOR defects: wrong behaviour, data loss or a crash, or a scenario with no real test. Everything else (style, naming, structure, docs, edge-case hardening, test tightness) goes to `deferred`, short notes only. Read the diff and the scenario tests; don't re-run the suite (the worker's checks and CI cover it). One pass, aim for under 10 minutes | Full review; review rounds on nits | Felippe wants this plan delivered fast; deferred items go to the major review after the new driver ships, as in call-cli D6 | Felippe, 2026-11-06 |
| D19 | For this plan only, the Lead merges a ticket's PR (squash, after `gh pr ready`) once its last review verdict is pass and its checks are green. A ticket whose last gate was a fix round without a passing review waits for Felippe. Reviews run on the `large` class mapped to sonnet (`--models-file <run>/models-fast.md`) | Felippe merges every PR; opus reviewer | Delivery speed for this plan | Felippe, 2026-11-06 |
| D20 | The driver's own audit (2026-11-06, `~/.local/state/orchestrate/orchestrate-lean-loop/driver-audit.md`) adds follow-up tickets T10–T13 for the defects T3–T7 did not scope: exact task ids, durable wakes, review provenance, a stop/resume path and a Lead-to-worker channel | Fixing them inside T3–T7 | Those tickets are already built or in flight; new tickets keep the chain intact and each one stays reviewable on its own | Lead, 2026-11-06 |


## Scenarios

**Lead wake and decisions**
- **S1** WHEN a unit fails more gates than its fix-round cap allows, or its worker reports blocked or decision, or it ends without a valid report, THEN the driver writes `<run>/<unit>/request.json` (event, reason, evidence paths, action menu) and appends one wake `decision <unit>: <reason> -> <request path>` to `<run>/wakes.jsonl`, and spawns no decider.
- **S2** WHEN the Lead runs `orchestrate.py await <plan>` and a wake not yet printed exists or arrives, THEN it prints exactly that one line and exits 0. WHEN the run has ended with nothing left to print, THEN it prints `finished -> <run>/retro.md` and exits 0.
- **S3** WHEN the Lead runs `orchestrate.py decide <plan> <unit> <action> --reason …` with an action on the menu, THEN `decision.json` is written and validated, the request is marked resolved, and the driver applies it on its next round (`answer` resumes the worker with the `--answer` text). WHEN the action is not on the menu or the unit has no open request, THEN it exits 2 and writes nothing.
- **S4** WHEN one unit has an open request, THEN the other units keep dispatching and gating, and later wakes come out of `await` one at a time in the order they were written.
- **S5** WHEN a unit has passed review and its checks are green, THEN exactly one `pr-ready <unit>: <PR url>` wake is written for that unit and head commit.
- **S6** WHEN an idle tick (`--idle-minutes`, default 10) finds a unit whose agent showed no new state or report since the last tick, or whose CI shows no progress, THEN an `idle` event is logged. WHEN the same unit is idle at two consecutive ticks, THEN a decision wake is written for it.
- **S7** WHEN a worker's complete or blocked message arrives while its unit has an open request, THEN the driver keeps it and acts on it after the decision is applied, instead of dropping it.
- **S31** WHEN the plan file stops passing the plan check (bad table, missing scenario, a cycle in Blocked by), THEN the driver keeps running on the last valid plan and writes one `plan-invalid` wake per distinct error.

**Reviewer reuse**
- **S8** WHEN a fix round of any source reports, THEN the unit's existing reviewer `<slug>-t<n>-review` is resumed, not spawned, with the range `<last_reviewed>..HEAD` and the previous findings, and the unit reaches CI only after that re-review passes.
- **S9** WHEN a re-review raises a blocking item whose file is not changed in the delta and which references no earlier finding, THEN the driver records it as deferred, logs a `scope` event, and does not gate on it.
- **S10** WHEN `review.json`'s `commit` is shorter than 7 hex characters or does not equal the checkout's HEAD, THEN the review is not accepted and the unit gets a request (contract error).
- **S11** WHEN a unit merges or pauses, THEN its implementer and reviewer panes are stopped.

**Findings and responses**
- **S12** WHEN a review item lacks id, kind, summary or answer_required, or a blocking item lacks file, line, fix or evidence, THEN validation fails, naming the item and field. WHEN an item has fields outside the core, THEN they appear verbatim in `findings.json`.
- **S13** WHEN the verdict and the items disagree (block without a blocking item, or pass with one), THEN validation fails.
- **S14** WHEN converge or CI fails, THEN each `findings.json` item has `kind: blocking`, `source`, `check`, `command`, `exit`, `excerpt` and `log_path`, filled by the driver (the CI excerpt comes from the failing check's log).
- **S15** WHEN the driver writes a fix round's `findings.json`, THEN it holds only blocking and answer_required items plus the reviewer's `checks_run[]`, and every other item is appended to `deferred.md`.
- **S16** WHEN a fix-round report lacks a response for an answer_required item, THEN a `contract-error` event is logged and the worker is resumed once with the missing ids, at no round cost. WHEN the next report still lacks them, THEN the unit gets a request.
- **S17** WHEN a review passes with answer_required items, THEN the unit goes on to CI and the implementer is resumed for answers only. WHEN a response is `disputed` with `changes_code: true`, THEN its new commits go to a delta re-review.
- **S26** WHEN a report or review lists `clarifications[]`, THEN each one is logged as a `clarification` event with its finding id.

**Worker reuse and limits**
- **S18** WHEN a unit fails a gate, THEN the driver counts the failure itself, ignoring the report's `review_rounds`, and the failure after the cap (`--max-fix-rounds`, default 2) raises S1.
- **S32** WHEN the plan has a line `Max fix rounds: T3=3`, THEN T3's cap is 3 and other tickets keep the default.
- **S19** WHEN the implementer or reviewer is below the context reserve before a resume, THEN the driver stops it and spawns a fresh agent of the same class with task.md, last report.json, findings.json and the commit range, logs `swap`, keeps the unit's counts, and writes no wake. WHEN usage is unknown, THEN it resumes and logs `context: unknown`.

**PR, CI, merge**
- **S20** WHEN a first build reports, THEN the PR it names is a draft and its checks are polled during review. WHEN the unit passes its last review with green checks, THEN the driver runs `gh pr ready`.
- **S21** WHEN `gh` reports no checks yet, or checks still running, THEN the driver polls again on a later round without blocking other units and raises no fix round.
- **S22** WHEN a unit is waiting for merge, THEN it does not count toward `--max-workers`.
- **S23** WHEN the PR is behind base, THEN the driver runs `gh pr update-branch`. On success there is no review. On conflict, a fresh worker gets a rebase task, its result goes to a delta re-review, and the conflict counts as a round.
- **S24** WHEN the PR is merged while the unit is in any gate, THEN the unit is COMPLETE, its agents are stopped, and its open findings are appended to `deferred.md` tagged `merged-early`.

**Visibility, metrics, retro, plan edits**
- **S25** WHEN an agent runs `orchestrate.py show <plan> --unit T2 --json`, THEN it prints that unit's gate, attempts, report/review/findings paths and decisions as JSON, and logs a `lookup` event.
- **S27** WHEN the driver changes any unit's state, writes a wake, takes a finding, applies a decision or hits an idle tick, THEN one JSON line is appended to `<run>/events.jsonl` before the next step. WHEN `orchestrate.py metrics <plan>` runs, including after a crash, THEN metrics.json is rebuilt from `events.jsonl`.
- **S28** WHEN a unit's report `checks[]` and reviewer `checks_run[]` hold the same command at the same commit, THEN metrics counts one `duplicate_check` for that unit.
- **S29** WHEN the run finishes, THEN `<run>/retro.md` holds per-unit tables (rounds, findings by kind and source, wakes by kind, idle hits, swaps, duplicate checks, contract errors, clarifications, lookups, tokens or `unknown`), and the finished wake points to it.
- **S30** WHEN an in-flight ticket's objective, acceptance, Satisfies or Paths change in the plan, THEN the next resume of its implementer or reviewer carries a "scope changed" note with the old→new packet diff, and the work already done is kept.

**Restart and compatibility**
- **S33** WHEN the driver restarts after a crash between recording a spawn intent and binding it, THEN `ensure_agent` finds the agent by its stable name and re-attaches. It spawns only when no such agent exists, and never two with one name.
- **S34** WHEN the driver runs on a run dir written by the previous version (contract 1 `review.json`, no `events.jsonl`), THEN in-flight units continue: v1 `major[]` items count as blocking, v1 `deferred[]` as deferred.
- **S35** WHEN `launch` gets an unknown option or a slug outside `a-z 0-9 - _`, THEN it exits 2 before starting a pane.
- **S36** WHEN `launch` runs from an hc terminal, THEN the driver pane is started as a child of that terminal, and the driver's first spawn succeeds as lead `orchestrate:<slug>`.
- **S37** WHEN the pane name `orchestrate-<slug>` would exceed 32 characters, THEN `launch` exits 2 naming the limit, instead of truncating.

- **S38** WHEN the driver dispatches, reopens, redoes or fixes a task, THEN the brief states the exact `task_id` the report must carry, and a report whose `task_id` differs is a contract error.
- **S39** WHEN `await` prints a wake, THEN the wake stays pending until the Lead acknowledges it, and a wake printed but not acknowledged is delivered again, in write order.
- **S40** WHEN a worker sends a distinct message while a request of the same kind is open, THEN the driver holds it as its own item and, after the decision, raises one request per distinct question in arrival order.
- **S41** WHEN `decide` names an unknown unit, an action off the menu, or a unit with no open request, THEN it exits 2 and writes no file and creates no directory.
- **S42** WHEN a unit's last gate was a review pass and its checks are green, THEN the driver writes a ready record holding the PR, its current head, the reviewed commit and the green-check commit; WHEN the PR head changes after that, THEN the record is invalid and no watcher may merge on it.
- **S43** WHEN `await` runs and the run's driver is not alive (it never started, or it died without a finish event), THEN it prints the queued wakes first and then exits with a distinct `driver-dead` or `not-started` status.
- **S44** WHEN the Lead runs `orchestrate.py stop <plan>`, THEN that run's driver stops gracefully with a recorded reason, and a later `launch` resumes the same run from its ledger; the workers it owns are stopped or re-adopted, never orphaned.
- **S45** WHEN the Lead runs `orchestrate.py tell <plan> <unit> <text>`, THEN the text reaches that unit's current worker through the runtime, the delivery is recorded, and a unit with no live worker is refused.
- **S46** WHEN the driver appends to `events.jsonl`, THEN it repairs an unterminated final line before appending, so no two events ever share a line, and a short write is completed.
- **S47** WHEN a crash left a request file without its wake, THEN the next round restores the wake, and an existing request and wake are never duplicated.
- **S48** WHEN a held complete message is acted on, THEN the driver uses only a report written for that completion (freshness by content, not mtime) and leaves the other held messages queued.

- **S49** WHEN `orchestrate.py launch` runs inside an hc terminal, THEN the driver pane is started as a child of that terminal, so the pane and the workers it spawns appear in the Herdr panel.
- **S50** WHEN `launch` runs outside an hc terminal, THEN the driver pane is started at the top level, as today.

**Restart reconciliation**
- **S51** WHEN the driver cleans up a unit and the runtime refuses to stop an agent it does not own ("not your child"), THEN the cleanup records that agent as kept, logs the refusal, and the run continues instead of failing.
- **S52** WHEN the driver holds a ticket whose worker is gone, THEN it asks the runtime whether that agent is alive before skipping the ticket; a dead agent's ticket is released and re-dispatched, and a live agent's ticket stays held.
- **S53** WHEN a run resumes after a crash, THEN the plan's Status cell and the ledger are reconciled: a ticket the ledger holds as ACTIVE whose agent is gone goes back to TO-DO in the plan and is re-dispatched, and a ticket whose agent is alive stays IN PROGRESS.

**The named profile**
- **S54** WHEN a run starts with `--profile <name>`, THEN the start event and the ledger's task packets record that profile, so the run's log says which profile its workers ran under.
- **S55** WHEN `--profile` names a profile whose CLI family differs from `--cli`, THEN the driver refuses the run with an error naming both families.
- **S56** WHEN `--profile` names a profile that is not configured, THEN the driver exits before it creates a worktree or claims a ticket, naming the unknown profile.
- **S57** WHEN a run names a profile, THEN every spawn it makes carries it: the implementer, the fix-round worker, the reviewer, the archive unit and the gaps review.
- **S58** WHEN `launch` forwards `--profile` to `run`, THEN the driver runs under that profile.

## Out of scope

- The `agent-runtime call` ancestry gate (D10): sibling plan `call-ancestry-gate` in agent-runtime.
- Token usage on wait/status: agent-runtime plan `worker-token-metrics`.
- A context policy for the Lead (D16): decided after T8.
- Re-read detection with hooks, and token-delta analysis (D9b).
- Chunked dispatch and cross-repository units (manual only, unchanged).
- T1 deferred parser nits (tables with ≥9 cells after Tickets, Status as last column, claim compares identical packets, a re-claimed TO-DO not rewritten, branch reuse from origin/main); converge `--final` on the APPROVED copy (converge skill); T5 D2/D3/D4/D6 gaps-reviewer items; T6 D3/D4/D6 test and doc nits. They stay in `deferred.md` for the major review.

## Risks

- **Security:** agents get only the read-only `show`; `await` and `decide` are for the Lead and change state only through the validated `decision.json`. The Bash gate on `agent-runtime call` is the sibling plan; until it ships the hook is a guardrail (call-cli D6).
- **Performance:** CI and merge polling move into the non-blocking loop (S21). `events.jsonl` is append-only, one line per event. `await` polls `wakes.jsonl` every 2 s and costs no tokens while waiting.
- **Migration:** contracts v2 are read alongside v1 (D14, S34). The driver runs from the symlinked main checkout, so a merge changes the code a relaunch picks up. A relaunch mid-build switches the Lead to the new protocol from T2 on (`await`/`decide` instead of the decider).
- **Rollback:** revert the PRs in reverse order. A run dir written by v2 is not readable by v1, so finish or abandon in-flight runs before rolling back.

## Seams

- `orchestrate.py run` against a fake `agent-runtime call` executable, a fake `gh`, and a temp git repo, in `skills/orchestrate/tests/` (existing harness). `converge.py` runs for real.
- `await`, `decide`, `show` and `metrics` run as subprocesses on the same fixture run dir.
- `contracts.py` validators tested directly with v1 and v2 fixtures.

## Tickets

| # | What it delivers | Satisfies | Blocked by | Paths | Size | Difficulty | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| T1 | `events.jsonl` writer + `metrics` rebuild, `ensure_agent` for every spawn, v1 run-dir and contract compatibility | S27, S33, S34 | none | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged https://github.com/FBisca/agent-skills/pull/15 (df522ba) |
| T2 | Lead wake: `request.json`, `wakes.jsonl`, `await`, `decide` (decider removed), wake queue, messages kept during a decision, pr-ready and plan-invalid wakes | S1–S5, S7, S31 | T1 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged https://github.com/FBisca/agent-skills/pull/16 (f395058) |
| T3 | Contracts v2: review envelope kinds with passthrough, evidence findings for converge/CI, responses, `checks_run`, clarifications, strict commit check, fix-round contents, pass with answers | S10, S12–S17, S26 | T2 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged https://github.com/FBisca/agent-skills/pull/17 (68216db) |
| T4 | Reviewer reuse with delta re-review and scope filter, panes stopped on merge/pause, driver-owned counts with per-ticket cap, context swap | S8, S9, S11, S18, S19, S32 | T3 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-06 · merged https://github.com/FBisca/agent-skills/pull/19 (a67859a) |
| T5 | PR and CI: draft + `gh pr ready`, non-blocking checks-then-merge poll, free slots while awaiting merge, update-branch / conflict rebase, merged-early, idle timer | S6, S20–S24 | T4 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | COMPLETE 2026-11-07 · merged https://github.com/FBisca/agent-skills/pull/23 (91d571f) |
| T6 | `show --json` with lookups, duplicate-check metric, `retro.md` + finished wake, scope-changed note on plan edits | S25, S28–S30 | T5 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | simple | agent | TO-DO |
| T7 | `launch` validation; SKILL.md and references rewritten for the Lead loop (launch, background `await`, `decide`, retro notes) and contracts v2; pane nested under the Lead with `--lead`, no slug truncation | S35–S37 | T6, T9 | skills/orchestrate/ | small | simple | agent | TO-DO |
| T8 | First live run of the new driver on a 1–2 ticket plan in Herdr: compare its retro with this build's metrics, turn `dogfood.md` into follow-up tickets or deferred rows, decide D16 | none | T7 | | | | Felippe | TO-DO |
| T9 | agent-runtime `call-ancestry-gate` T3 (`call --lead` forces the lead role) merged and installed on this machine | none | none | | | | Felippe | COMPLETE 2026-11-06 · agent-runtime PR #49 merged (68205cd), installed through the repo symlink |
| T10 | Exact task id in every brief, `decide` writes nothing when it refuses, `events.jsonl` appends are whole lines and repair a torn tail | S38, S41, S46 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T11 | Durable wake delivery with an explicit ack, one request per distinct held question, request and wake recovery after a crash, fresh-report rule for held completions | S39, S40, S47, S48 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | TO-DO |
| T12 | A ready record that proves the PR head passed review with green checks, `await` that reports a dead driver, `stop` and `resume` of a run | S42, S43, S44 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | TO-DO |
| T13 | `orchestrate.py tell`: the Lead steers a driver-owned worker through the runtime | S45 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T14 | `launch` nests the driver pane under the Lead's terminal, so the driver and its workers are visible in the Herdr panel | S49, S50 | none | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | COMPLETE 2026-11-06 · merged https://github.com/FBisca/agent-skills/pull/18 (d9cb946) |
| T15 | A cleanup that cannot stop its worker records it as kept, so a refused stop does not kill the run | S51 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T16 | The driver asks the runtime whether a held ticket's agent is alive; a dead worker's ticket is released and re-dispatched | S52 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T17 | A resumed run reconciles the plan's Status cell with the ledger, so a ticket dispatched before a crash comes back | S53 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | regular | complex | agent | TO-DO |
| T18 | The run records the profile its workers ran under, and every spawn path is pinned by a test | S54, S57, S58 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T19 | A profile whose CLI family differs from `--cli` is refused | S55 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
| T20 | An unknown profile name fails the run before it touches the repo | S56 | T7 | skills/orchestrate/scripts/, skills/orchestrate/tests/ | small | simple | agent | TO-DO |
