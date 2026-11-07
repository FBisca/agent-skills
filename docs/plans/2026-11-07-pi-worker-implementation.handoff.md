# Handoff: Pi-as-worker implementation (runtime + driver)

**Date:** 2026-11-07 · **Repos:** `agent-runtime` (~/developer/agent-runtime) + `agent-skills` (this repo)
**State:** SUPERSEDED for the next session — see `docs/plans/2026-11-07-pi-worker-pr.handoff.md` (the mission is now: open the PRs and merge them). Both sides are implemented and green; the driver side is no longer red-first only.
**Brain:** `codex gpt-6.1-terra`; the implementer was Pi.

## Where the ledger is (do not re-derive)

| Artifact | Path | What it holds |
|---|---|---|
| Runtime plan (approved) | `~/developer/agent-runtime/docs/plans/2026-11-07-pi-worker.plan.md` | The decisions (D1–D10), the scenarios (S1–S9), the tickets (T1–T5) for the runtime side. |
| Driver plan (approved) | `agent-skills/docs/plans/2026-11-07-pi-worker-driver.plan.md` | The decisions (D1–D5), the scenarios (S1–S6), the tickets (T1–T2) for the driver side. |
| Prior research | `agent-skills/docs/plans/2026-11-07-pi-worker-profiles.handoff.md` | The original blockers and verified facts. Superseded by the two plans above; read only for background. |
| Living specs | `~/developer/agent-runtime/docs/specs/harness-adapters.md` (R171–R187, R178 to amend) and `agent-skills/docs/specs/harness-portability.md` | The requirements the plans amend. |

## What the user decided (2026-11-07)

- **Pi is a native family, not a profile.** `BUILTINS` gains `"pi"`; the `minimax` profile stays a Claude profile. A
  profile named `pi` is impossible anyway (`server/profiles.py:44-46` rejects a name that shadows a built-in).
- **The worker's tools come from Pi's MCP registration** (`mcp__agent-runtime__report`), not from a Pi extension.
- **The role travels in the task text**, not in a role file (Pi has none): `Role: implementer` + the report protocol.
- **A Pi worker may** report, message, wait, status, collect, list, task-list — **never** spawn, stop or resume.
- **The review gates (reviewer + gaps reviewer) run on `gpt-6.1-terra`**; the implementer, archive and lookup tiers run
  on the worker backend (Pi/MiniMax). A Claude or Codex run changes nothing.
- **Scope: deliver the Pi worker.** Relaunching the parked `orchestration-baselines` run is out of scope (the user's Q6).
- Working style for this session: **all tests red first, then all tickets implemented, then one fix pass** (the user
  asked for this explicitly). Use `ruff` (already installed at
  `~/.local/share/mise/installs/python/3.11.14/bin/ruff`) for fast syntax feedback — a stray quote in a test file cost
  several minutes of pointless debugging before ruff was used.

## What is already done — `agent-runtime` (uncommitted, on `main` @ `b0cbef2`)

`git status` in `~/developer/agent-runtime`: modified `server/profiles.py`, `server/hc_tools.py`, `server/host_policy.py`;
new `tests/test_pi_worker.py`, `docs/plans/2026-11-07-pi-worker.plan.md`.

| Ticket | State | What changed |
|---|---|---|
| T1 (S1, S6) | **done** | `profiles.BUILTINS = ("claude", "codex", "pi")`; `hc_tools.spawn` builds `["pi", "--print"] + model + [message]`; `spawn_effort` maps the five efforts to `--thinking`; the pi family gets `Role: <agent>` + `PI_WORKER_PROTOCOL` (the exact MCP tool name) in the task. |
| T2 (S2) | **done** | `profiles.scrub_prefix(env, cli)` is family-aware: `PROVIDER_VARIABLES` now includes `MINIMAX_API_KEY`, `PI_API_KEY`, `PI_PROVIDER`, `PI_MODEL`; a `pi` spawn keeps them (`PI_PROVIDER_VARIABLES`), every other family loses them. |
| T3 (S3, S4, S5) | **done** | `host_policy.check_worker`: a Pi worker may `report`, `message`, `wait`, `status`, `collect`, `list` and `task list`; everything else is refused with "a pi worker may only …". The blanket "pi is a lead only" refusal is gone. |
| T4 (S7, S8) | **done** | The end-to-end path is covered by `tests/test_pi_worker.py` (a Pi worker registers, reports once, the lead's team receives exactly one result; the authorised-directory and authorised-backend guarantees hold). |
| T5 (S9) | **not done** | The local configuration (below). |

`tests/test_pi_worker.py`: **20 tests, all passing** (`python3 -B -m unittest discover -s tests -p "test_pi_worker.py"`).
It is red-first: it was written and seen failing before the implementation.

### Still missing on the runtime side

- **The spec amendment (plan D6, ticket T3):** `docs/specs/harness-adapters.md` still says "Pi is a **lead only** in this
  plan" in the intro and encodes **R178** ("a Pi session that resolves as a worker is refused"). R178 must be amended and
  **R188–R191** added (a Pi worker may report inside its team; may not spawn/stop/resume; the team scope holds; the
  authorised-directory guarantee holds), plus the Coverage table rows. `README.md` (the "Hosts" table) must name the pi
  family and record the local configuration.
- **`server/host_policy.py`'s module docstring** still says the server decides what "the lead may mutate" — update it for
  the worker set.
- **`server/mcp_server.py`'s spawn description** ("cli: built-in or profile; default claude") should mention pi.

### Known gate breakage (the "one fix pass")

The full runtime gate (`python3 -B -m unittest discover -s tests`) has not been run green since the change. Two things are
expected to need updating, because they hard-code the old family list:

- `tests/test_tools.py`: `PROVIDERS` (the expected scrub list) must gain `MINIMAX_API_KEY`, `PI_API_KEY`, `PI_PROVIDER`,
  `PI_MODEL`; the `cli` enum assertions (`["claude", "codex"]`, `["claude", "codex", "selected"]`) must gain `"pi"`.
- Any other file that asserts the family list or the scrub prefix.

Run the gate per file when in doubt (`-p "test_x.py"`); a file that "hangs" is usually a leftover process from a killed
run — `timeout 180` without `-k` waits forever on a process that ignores SIGTERM, so use `timeout -k 5 180`.

## What is not started — `agent-skills` (the driver)

`agent-skills/skills/orchestrate/tests/test_pi_backend.py` is **written and red** (8 tests; 6 error out because
`--cli pi` is not accepted yet). The implementation is untouched.

Driver plan, condensed (the full text is in the plan):

- **T1 (S1, S2):** `--cli` accepts `pi`; `class_models(path, backend)` must resolve a column **by header name**
  (`Claude`, `Codex`, `Pi`) with the positional rule (`claude`→1, `codex`→2) as the fallback; when the models file has no
  Pi column, the classes resolve from a **new skill-local table** `skills/orchestrate/references/models.md` (one "Model
  classes" section, a Pi column, `minimax/MiniMax-M3.1-Flash` for small/medium/large). A Pi column in `--models-file`
  wins when it is there.
- **T2 (S3–S6):** a new `--brain-cli` flag. When it is given, the **reviewer and the gaps reviewer** spawn on that
  backend with its **medium** model (`gpt-6.1-terra` on the Codex column) and the reviewer's effort stays `high`; the
  implementer, archive and lookup tiers stay on the worker backend. When it is not given, every tier keeps today's
  backend and model (a Claude run's reviewer is still `claude`/`opus`). A named brain backend wins over `--profile` for
  the gate spawns (`spawn_args` must not overwrite the gate's `cli` with the profile).
- Update the plan's D3/D5 wording when the flag lands (the plan currently describes the brain tier without naming the
  flag).

The driver gate is `scripts/run-tests.sh` (every file in its own process, in parallel; `JOBS` limits the workers).

## Local configuration (plan ticket T5, not done)

- `~/.pi/agent/mcp.json` is `{"mcpServers": {}}` — restore the `agent-runtime` entry from
  `~/.pi/agent/mcp.json.bak-20261107142405` (`python3 server/mcp_server.py`, `AGENT_RUNTIME_DISPATCH=1`,
  `"exposure": "direct"`). Without it a Pi worker has no `report` tool.
- `~/.config/agent-runtime/hosts.json`: the `pi` host's `backends` list must gain `"pi"` (it is `["minimax", "codex",
  "claude"]` now); `paths` already covers `~/developer`.
- `~/.claude/CLAUDE.md` (symlink → `~/developer/dotfiles/agents/.claude/CLAUDE.md`): a Pi column is optional — the
  driver falls back to its own table until the dotfiles commit lands.

## Verify the delivery end to end

One live check is still missing: a real Pi worker on MiniMax reporting through the restored MCP registration. The
previous research verified `pi --print --model minimax/MiniMax-M3.1-Flash "…"` → `PI_OK`, so the remaining risk is the
MCP registration, not Pi itself.

## Open PRs to reconcile before merging (runtime)

PRs **#39** (`feat/resume-attention`) and **#45** (`feat/worker-session-binding`) are open and both touch
`server/hc_tools.py`. The Pi lead plan (D4) requires reconciling them before overlapping lifecycle edits. They are the
user's to merge; keep the Pi branch's `spawn` hunks disjoint and rebase onto `main` afterwards.

## Skills for the next session

- `/orchestrate <plan-path>` to build either plan with agents (the runtime plan is ready; the driver plan needs its
  implementation first, or implement it directly as the "hands").
- `converge` (`python3 skills/converge/scripts/converge.py <plan> --final`) to check a plan against its scenarios.
- `tdd` for the remaining red-first work (the driver side is already red).
- `/handoff` again if the run must pass to a third agent.
