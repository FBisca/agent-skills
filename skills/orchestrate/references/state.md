# Deterministic state helper

Use `scripts/orchestrate.py` with Python 3.9+ on macOS or Linux. It uses only the standard library. It does not call models, execute packet check commands, or write native runtime files.

Choose one private, durable, writable ledger path per active plan outside tracked product files. Pass it with `--state`; record that absolute path in the active chat. All workers and orchestrators for this plan must use the same ledger. Separate ledgers cannot detect each other's assignments. Use a temporary directory only for a deliberately disposable run.

`inspect --checkout <root>` reads Git HEAD, branch, status, and installed executable paths. These are observations, not proof of active model selection. The worktree status is a file inventory, not a content hash; re-read affected source after external edits.

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

These are example values, not paths or commands to run unchanged. `owns` accepts literal relative files/directories, including `.` for exclusive ownership of the checkout. It rejects globs and paths that escape the checkout. Add focused context, peers, exclusions, or plan excerpts to the packet when useful. `worker` is a logical worker key; `runtime_id` is bound after native dispatch.

```sh
python3 <skill-dir>/scripts/orchestrate.py claim --state <ledger> --packet <packet.json>
```

The helper checks ownership conflicts, unfinished assignments, and declared predecessor completion. It reserves before spawn. **Only `action: reserved` is a new reservation.** `action: existing` means inspect the recorded task and runtime; do not spawn again. A failed or lost spawn response keeps the reservation until the runtime proves there is no active worker.

After a successful native spawn or approved reuse:

```sh
python3 <skill-dir>/scripts/orchestrate.py bind --state <ledger> --task <task-id> --runtime-id <native-id>
```

Use a unique runtime identifier, qualified by engine and parent session if needed. The same ID can serve sequential tasks, but cannot hold two unfinished tasks. `bind` also marks a resumed blocked/partial assignment active. Record model/configuration evidence in the handoff; a role name alone does not prove the effective model.

The helper's dependency check only sees this ledger. The orchestrator must separately verify code in the consuming checkout. If a prerequisite existed before this run, include its concrete checkout evidence in the packet rather than inventing a completed ledger task.

## Checkpoint or complete

The worker sends a compact result. The orchestrator normalizes it to JSON and records it after reviewing evidence:

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

`COMPLETE` requires a runtime ID, confirmed acceptance, no remaining work, and passing evidence for every required check. This validates the report contract; it does not independently prove the report true. `PARTIAL` keeps ownership. `BLOCKED` also requires `blocker` and a next action in `remaining`. A failed or omitted check needs a `reason`. Store short decisions, not transcripts. Optional `context` and `presentation` objects can preserve observed telemetry and verified runtime IDs.

If replacing a worker for an unfinished task, first stop or confirm it stopped using native tools. Then:

```sh
python3 <skill-dir>/scripts/orchestrate.py release --state <ledger> --task <task-id> --stopped --reason <reason>
```

This releases ledger ownership only; it does not stop an agent or remove a pane/worktree. Keep the old handoff and use a new task ID for the replacement attempt. Never pass `--stopped` based on a timeout or an idle-looking pane alone. There is no automatic stale-reservation expiry.

`show --state <ledger>` returns a short task index. Add `--task <task-id>` for the full packet and latest handoff. Writes are locked and atomic. A lock conflict returns an error; retry after the other update. No full ledger is injected on each task.

## Context measurement

Obtain telemetry from the **child** runtime. When available, normalize it as:

```json
{
  "kind": "current_context",
  "model": "gpt-5.6-terra",
  "context_tokens": 40000,
  "effective_window": 200000,
  "observed_at": "2026-09-07T12:00:00+00:00",
  "source": "child runtime context event"
}
```

The numbers are illustrative, not Terra defaults. Use the effective window exposed by the running child. Never substitute cumulative usage or the model's advertised maximum. Update the timestamp only when collecting a new observation; do not relabel stale data as fresh.

```sh
python3 <skill-dir>/scripts/orchestrate.py context --sample <sample.json> --reserve-tokens <estimate>
```

The reserve estimates the next task's additional reads, tool results, and reasoning. The helper returns `room_available`, `checkpoint`, or `unknown`. A measurement expires after 300 seconds by default (`--max-age-seconds` changes this freshness bound). Missing values, wrong measurement kinds, invalid windows, and stale samples return `unknown`. The freshness bound is not a context-pressure threshold.

`room_available` is only a capacity check. The orchestrator still evaluates relevance, changed code, and errors. `checkpoint` means save state and compact through a supported runtime operation or assign a fresh worker. `unknown` means make a qualitative decision and state the measurement limit. No automatic replacement, compaction, or global threshold changes occur.

Claude subagent compaction events can inform a checkpoint, but pre-compaction token counts are not current occupancy after compaction. Never assume the parent's compaction also reduced child context.

## Usage comparisons

`metrics --samples <samples.json>` accepts an array of normalized **per-request** records with `kind: request`, unique `source` + `id`, `backend`, `model`, `strategy` (`fresh` or `reuse`), and `actor` (`orchestrator` or worker identifier).

Optional numeric fields: `input_tokens`, `cached_input_tokens`, `cache_write_tokens`, `output_tokens`, `cost_usd`, and `duration_seconds`. Convert provider-specific definitions before recording them; keep the source reference. Do not submit cumulative counters as request increments or duplicate streaming usage events.

The helper reports totals and observation counts per strategy/actor/backend/model. Missing measurements remain null. Partial cost coverage cannot establish total workflow cost. Summed request durations are not elapsed wall time for parallel work.

For a benchmark, use equivalent clean starting checkouts, identical tasks, model settings, and acceptance checks. Include parent work, workers, handoffs, failed attempts, and cache conditions. Measure whole-run elapsed time separately and compare correctness before cost. Do not launch a paid benchmark merely to fill missing telemetry.
