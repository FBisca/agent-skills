# Deterministic state helper

`python3 <skill-dir>/scripts/orchestrate.py` requires Python 3.9+, macOS/Linux, and only stdlib. It forwards to [agent-runtime](https://github.com/FBisca/agent-runtime)'s `agent-orchestrator`. The helper does not call models, execute packet checks, or write native runtime files.

The driver (`run`, started by `launch`) owns claims, bindings, checkpoints, and releases for workers/reviewers/deciders. These commands are for diagnosis or manual runs. Only edit a ledger when its driver is stopped. Report/gate schemas: engine `contracts.py`; checkpoint examples below show ledger shape.

For manual runs, choose one private, durable, writable ledger per plan outside product files, e.g. `~/.local/state/orchestrate/<slug>.json`, beside run directory `<slug>/`. Pass `--state` and record the absolute path in chat. Every participant shares it: separate ledgers cannot detect conflicts. Use temporary directories only for disposable runs. Codex workers need the run directory in their profile's `writable_roots`.

`inspect --checkout <root>` observes HEAD, branch, status, and installed executables; it cannot prove active model selection. Status inventories files, not content hashes: re-read source after external edits.

## Reserve, dispatch, bind

Write a compact JSON packet with the available file-edit tool. Example shape:

```json
{
  "task_id": "api-validation",
  "worker": "api-implementer",
  "plan": "/work/plans/validation.md",
  "objective": "Reject invalid requests before storage",
  "checkout": "/work/api",
  "backend": "codex",
  "owns": ["src/validation", "tests/validation"],
  "acceptance": ["Invalid input returns the documented error"],
  "checks": ["npm test -- validation"],
  "depends_on": []
}
```

Example values require adaptation. Routed packets add [routing](routing.md) fields: `size` (`small|regular|big`), `difficulty` (`simple|complex`), `class` (`small|medium|large`), `effort` (`low` through `max`), resolved `model`, and `unit` (shared across build, fixes, chunks). `claim` requires all route fields; model/effort alone remain unrouted metadata.

`owns` accepts literal relative files/directories (`.` = exclusive checkout), rejecting globs/escaping paths. Add focused context, peers, exclusions, or plan excerpts as needed. `worker` is logical; bind native `runtime_id` after dispatch.

```sh
python3 <skill-dir>/scripts/orchestrate.py claim --state <ledger> --packet <packet.json>
```

`claim` checks ownership conflicts, unfinished assignments, and declared predecessors before spawn. Only `action: reserved` permits a new spawn; `existing` requires inspecting the task/runtime. Failed/lost spawn responses retain the reservation until runtime proves no active worker.

After a successful native spawn or approved reuse:

```sh
python3 <skill-dir>/scripts/orchestrate.py bind --state <ledger> --task <task-id> --runtime-id <native-id>
```

Use a unique native runtime ID, qualified by engine/parent session if needed. Sequential reuse is allowed; simultaneous unfinished tasks are not. `bind` reactivates blocked/partial assignments. Record effective model/config evidence; role names prove nothing.

Dependencies cover this ledger only. Verify prerequisite code in the consumer checkout; pre-existing prerequisites need concrete packet evidence, not fabricated completed tasks.

## Checkpoint or complete

The worker writes its result as `<run>/<task>/report.json`; the driver validates it with `contracts.py` and records it in this shape:

```json
{
  "task_id": "api-validation",
  "status": "COMPLETE",
  "summary": "Invalid requests fail before storage",
  "acceptance_met": true,
  "files": ["src/validation/input.ts"],
  "decisions": ["Keep the documented error shape"],
  "interfaces": [],
  "remaining": [],
  "checks": [{"command": "npm test -- validation", "outcome": "passed"}],
  "context": {"status": "unknown"}
}
```

```sh
python3 <skill-dir>/scripts/orchestrate.py checkpoint --state <ledger> --task <task-id> --report <report.json>
```

`COMPLETE` requires runtime ID, confirmed acceptance, no remaining work, and passing evidence for every required check. Routed tasks also require `review_rounds` (failed reviews; 0 for first-pass success; allowed on PARTIAL) and `usage` (runtime metric line or `unknown`) for routing calibration. Validation checks the report contract, not its truth.

`PARTIAL` retains ownership. `BLOCKED` requires `blocker` and a next action in `remaining`. Failed/omitted checks require `reason`. Keep decisions short; optional `context`/`presentation` retain observed telemetry/verified runtime IDs.

If replacing a worker for an unfinished task, first stop or confirm it stopped using native tools. Then:

```sh
python3 <skill-dir>/scripts/orchestrate.py release --state <ledger> --task <task-id> --stopped --reason <reason>
```

Use `--cutoff` for cutoff stops. `show --unit <id>` sums failed reviews/cutoffs across attempts and reports `escalate` at two of either. Release frees ledger ownership only; it leaves agents, panes, and worktrees intact. Preserve the handoff; replacement gets a new task ID. Confirm worker stoppage through native tools before `--stopped`; timeout/idle appearance is insufficient. Reservations never auto-expire.

`show --state <ledger>` gives a short index; `--task <task-id>` adds full packet/latest handoff. Writes are locked/atomic; retry lock conflicts after the other update. Tasks do not receive the full ledger.

## Context measurement

Obtain telemetry from the **child** runtime. When available, normalize it as:

```json
{
  "kind": "current_context",
  "model": "<resolved model>",
  "context_tokens": 40000,
  "effective_window": 200000,
  "observed_at": "2026-09-07T12:00:00+00:00",
  "source": "child runtime context event"
}
```

Use observed child-runtime occupancy and effective window, not cumulative usage or advertised capacity. Refresh timestamps only on new observations. Example numbers are illustrative.

```sh
python3 <skill-dir>/scripts/orchestrate.py context --sample <sample.json> --reserve-tokens <estimate>
```

Reserve estimates the next task's reads, results, and reasoning. Results:

- `room_available`: capacity only; still assess relevance, code changes, and errors.
- `checkpoint`: save state, then compact through supported runtime operations or assign a fresh worker.
- `unknown`: decide qualitatively and state the measurement limit.

Samples expire after 300 seconds (`--max-age-seconds` overrides). Missing/invalid values, wrong kinds/windows, and stale samples return `unknown`. Freshness is not a pressure threshold; the helper never replaces, compacts, or changes global thresholds automatically.

Claude child compaction events can inform checkpoints; pre-compaction counts do not measure post-compaction occupancy. Parent compaction says nothing about child context.

## Usage comparisons

`metrics --samples <samples.json>` accepts an array of normalized **per-request** records with `kind: request`, unique `source` + `id`, `backend`, `model`, `strategy` (`fresh` or `reuse`), and `actor` (`orchestrator` or worker identifier).

Optional numbers: `input_tokens`, `cached_input_tokens`, `cache_write_tokens`, `output_tokens`, `cost_usd`, and `duration_seconds`. Normalize provider definitions and retain sources; record request increments once, excluding cumulative counters and duplicate stream events.

Totals/counts group by strategy/actor/backend/model; missing values stay null. Partial costs cannot establish total cost; summed parallel request durations are not elapsed time.

Benchmarks require equivalent clean checkouts, identical tasks/settings/acceptance, and accounting for parent, workers, handoffs, failures, and caches. Measure elapsed time separately; compare correctness before cost. Missing telemetry alone does not authorize paid benchmarks.
