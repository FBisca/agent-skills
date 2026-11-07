# Handoff: Pi-as-worker profiles + MiniMax-only orchestration (option B)

**Date:** 2026-11-07 · **Repos:** `agent-runtime` (~/developer/agent-runtime) + `agent-skills` (this repo)
**Decision:** option B — the user chose the full change: Pi becomes a worker backend in the runtime, the `minimax` profile splits into `claude-minimax` + `pi`, and the orchestration run uses Pi/MiniMax workers with `gpt-6.1-terra` as the brain.
**Status:** nothing implemented yet. The plan `orchestration-baselines` was launched and is **parked** (see "Live run state").

## What the user asked for

1. Split the `minimax` profile into two: `claude-minimax` (Claude CLI → MiniMax endpoint) and `pi` (Pi CLI → MiniMax-M3.1-Flash).
2. Run the orchestration with **Pi agents only, on MiniMax**.
3. Use **`gpt-6.1-terra` (Codex medium) as the brain** for hard decisions — nothing bigger. No `opus`, no `gpt-6.1-sol`.

## Why it is not a config-only change

`~/.config/agent-runtime/profiles.json` today has one profile, and it is a **Claude** profile:

```json
{"profiles": {"minimax": {"cli": "claude", "env": {"ANTHROPIC_BASE_URL": "https://api.minimax.io/anthropic",
 "ANTHROPIC_AUTH_TOKEN": "$MINIMAX_API_KEY", "ANTHROPIC_MODEL": "MiniMax-M3.1-Flash", ...}}}}
```

A `pi` profile cannot be used yet because the runtime has no Pi *worker* support. Four concrete blockers, all verified by reading the code:

| # | Blocker | Location | Why it blocks |
|---|---|---|---|
| 1 | Only two CLI families exist | `server/profiles.py:8` `BUILTINS = ("claude", "codex")`; `server/profiles.py:138` rejects any other family | A profile whose `cli` is `pi` fails profile validation |
| 2 | `spawn` builds the argv per family, no Pi branch | `server/hc_tools.py:355` (`cli = arguments.get("cli")`), `:403-413` (`claude` → `["claude", ...]`, else `["codex", ...]`) | Nothing launches the `pi` binary |
| 3 | Pi is **lead-only** by design | `server/host_policy.py:132` `if host == "pi" and role != "lead": raise Refused("pi is supported as a lead only...")`; requirement R178 in `docs/specs/harness-adapters.md:47` | A Pi worker calling `report` is refused |
| 4 | Pi's MCP server is unregistered | `~/.pi/agent/mcp.json` is `{"mcpServers": {}}`; the working config survives at `~/.pi/agent/mcp.json.bak-20261107142405` | A Pi worker has no `report` tool, so it can never report |

Blocker 4 is a config regression, not a code gap: restore the backup file's `agent-runtime` server entry.

## Verified facts (do not re-derive)

| Fact | Evidence |
|---|---|
| Pi headless on MiniMax works | `pi --print --model minimax/MiniMax-M3.1-Flash "..."` → `PI_OK` |
| Pi resolves its model from `--model` alone | Same command with `env -u PI_MODEL -u PI_PROVIDER` → `PI_OK_SCRUBBED` |
| `MINIMAX_API_KEY` resolves in a spawned worker | `~/.zprofile:4` exports it; visible in the live worker's env (`ps eww`) |
| Pi's MCP tool naming matches the runtime's expectation | Pi names tools `mcp__<server>__<tool>` → `mcp__agent-runtime__report`; the runtime's PreToolUse hook already matches that shape (`hooks/pre_tool_use.py:139`) |
| Pi exposes `--print`, `--model`, `--provider`, `--thinking` | `pi --help`; `--thinking` levels are `off/minimal/low/medium/high/xhigh/max` |
| Pi is a **lead** host today | `server/agent_runtime.py:19` `HARNESSES = ("claude", "codex", "pi")`; `server/host_policy.py:25` `RESTRICTED_HOSTS = ("pi",)` |
| The runtime's own README names the integration points | `README.md` "Hosts" table: `CLIS`, `spawn`, `cli_of_args`, `detect_cli`, `dispatch_identity`, hooks |
| The runtime's gate is | `python3 -B -m unittest discover -s tests` (README:235) |

## Scope of the change

### A. `agent-runtime` — Pi as a worker backend

Work in `~/developer/agent-runtime` on a fresh branch off `main` (main is at `b0cbef2` "feat(pi): support Pi as a first-class lead harness (#53)").

1. **`server/profiles.py`** — allow the `pi` family.
   - `BUILTINS = ("claude", "codex")` → add `"pi"` (it is the family allow-list; `launch()` at `:138` and `cli_names()` at `:107` both read it).
   - Decide and document: a profile with `"cli": "pi"` needs its own env overlay. Pi reads `PI_PROVIDER` / `PI_MODEL` / `PI_API_KEY` (docs/environment-variables.md) and `MINIMAX_API_KEY` for the MiniMax provider (docs/providers.md:57). **Pi ignores `ANTHROPIC_*`** — those only drive the Claude family. So the `pi` profile must carry Pi's variables, not a copy of the Claude ones.
   - `PROVIDER_VARIABLES` (`:9`) drives what `scrub_prefix()` strips from a built-in spawn. Add the Pi equivalents so a non-Pi worker never inherits `PI_*` credentials.
2. **`server/hc_tools.py` — `spawn`** — add the Pi branch next to `:403-413`.
   - Pi's non-interactive argv: `pi --print --model <model> --provider <provider> --thinking <effort> "<task>"`.
   - `effort` → `--thinking` mapping: the runtime's effort vocabulary is `low/medium/high/xhigh/max` (`EFFORTS`, `server/hc_tools.py:238`); Pi's is `off/minimal/low/medium/high/xhigh/max`. Map directly for the five shared values; decide what `max` and the Pi-only levels do.
   - `agent` role: Claude uses `--agent <name>`, Codex reads `~/.codex/agents/<name>.toml`. Pi has no role file concept — it has extensions/skills/prompt templates. Decide the Pi equivalent for the `implementer` role and how `agent: "none"` behaves.
   - The worker protocol text (`WORKER_PROTOCOL`, `:160`) must reach Pi, since it is what makes the worker call `report`.
3. **`server/host_policy.py:132`** — let a Pi **worker** report.
   - Today any Pi session that is not a lead is refused every call. A Pi worker needs `report` (and `message`/`wait`/`status` for its own team). R178 in `docs/specs/harness-adapters.md:47` encodes "Pi is supported as a lead only" — **R178 must be amended, and the spec updated**, not worked around.
   - Keep the R171-R187 guarantees intact: explicit backend naming, authorized directories, no implicit provider choice.
4. **`server/mcp_server.py:37`** — the `cli` enum for `spawn` is `["claude", "codex"]`; it is overwritten dynamically at `:138` by `profiles.cli_names(env)`, so adding `pi` to `BUILTINS` covers it. Verify.
5. **Identity** — `dispatch_identity` (`server/hc_tools.py:190`) refuses a Pi session with no visible Pi process and an ambiguous host. A Pi **worker** resolves as role `worker` (it has a parent terminal), so check `cli_generation()` (`server/agent_runtime.py:124`) still yields the worker's `pid:lstart` and that `store.actor` (`server/dispatch_store.py:456`) binds the Pi worker to the lead's team via `assignment_id`.
6. **Tests** — the runtime's gate is `python3 -B -m unittest discover -s tests`. Add red-first tests in `tests/test_pi_lead.py` (or a new `tests/test_pi_worker.py`) covering: a Pi profile validates; `spawn` builds the Pi argv; a Pi worker may `report`; a Pi worker still may **not** spawn outside the authorized directories.

**Conflict warning:** PRs **#39** (`server/dispatch_store.py`, `server/dispatch_wait.py`, `server/hc_tools.py`, `tests/test_event_wait.py`) and **#45** (`server/hc_tools.py`, `server/usage.py`, `tests/test_usage.py`) are open and both touch `server/hc_tools.py`. The runtime's own plan `docs/plans/2026-11-07-pi-lead-adapter.plan.md` (D4) says to reconcile #39/#45 **before** editing overlapping runtime paths, and that PR reconciliation is not a prerequisite for P0/P1 work but **is** for touching `hc_tools.py` lifecycle code. Resolve this first — decide merge/rebase order against actual then-current `main`, re-run the affected tests, and state the decision in the plan.

### B. `agent-skills` — the orchestrate driver

Work in this repo (`skills/orchestrate/scripts/orchestrate.py`).

7. **Model classes for Pi.** `class_models()` (`orchestrate.py:514`) reads the "Model classes" table from `~/.claude/CLAUDE.md` and picks the Claude or Codex column by `backend`. A Pi backend needs its own column or its own table. The table currently is:

    ```
    | Class | Claude | Codex |
    | small | model: "haiku" | gpt-6.1-luna |
    | medium | model: "sonnet" | gpt-6.1-terra |
    | large | model: "opus" | gpt-6.1-sol |
    ```

    Pi has one model here (`MiniMax-M3.1-Flash`), so small/medium/large all map to it — but **effort must still vary by class** (`ROUTE`, `orchestrate.py:115`; `MATRIX`). Confirm Pi's `--thinking` accepts the runtime's effort values before wiring this.
8. **The brain tier.** The user allows `gpt-6.1-terra` only, nothing bigger. These tiers ask for `self.models["large"]` → `opus` / `gpt-6.1-sol` today:
   - reviewer: `orchestrate.py:1271` (`"model": self.models["large"], "effort": "high"`)
   - gaps reviewer: `orchestrate.py:2298` (`self.models["medium"]`, already terra on the Codex column)
   - archive worker: `orchestrate.py:2221` (`self.models[klass]`, class from size/difficulty)

   The reviewer (and any decider-like tier) must route to `gpt-6.1-terra` (Codex medium). Decide whether that is a new table column, a plan-level rule, or a driver flag — and note the gaps reviewer at medium is already within budget.

   **Note on "the brain":** in this driver the *decider* is **not a spawned worker**. `step_decided` (`orchestrate.py:2044`) applies a decision that the Lead answers through `orchestrate.py decide <plan> <unit> <action> --reason R` (`:2568`) — the Lead is the deciding agent. So "codex terra as the brain" applies to the **spawned** tiers (reviewer, gaps, archive) and to whatever the Lead session itself runs; the driver's escalation menu (`retry`, `retry one class up`, `fresh worker`, `mark blocked`, `skip`, `answer`) is answered by a human or Lead session, not by a spawned terra agent.
9. **Backend selection.** The driver has `--cli {claude,codex}` and `--profile` (`:2694`, "replaces the CLI family in the spawn"). Once `pi` is a real family, `--profile pi` must be able to reach it, and the driver's `spawn_args` (`:1845`) already forwards a profile name as `cli`. Confirm the profile name reaches `hc_tools.spawn` unchanged.
10. **Tests.** This repo's gate is `scripts/run-tests.sh` (every test file in its own process, in parallel; `JOBS` limits workers). A suite that hangs is a failing suite.

### C. Configuration

11. **Split the profile** in `~/.config/agent-runtime/profiles.json` (mode 0600, local file, not in a repo):
    - `claude-minimax` — the current `minimax` profile, unchanged in substance (Claude CLI → MiniMax Anthropic endpoint).
    - `pi` — the Pi family, with Pi's provider variables pointing at MiniMax and `MINIMAX_API_KEY` as a `$MINIMAX_API_KEY` reference (never a literal).
    - **The name `minimax` is referenced elsewhere**: `tests/test_tools.py:595,620,624` in the runtime use it as a fixture profile name, and `docs/specs/harness-adapters.md:68` shows it as an authorized backend in a `hosts.json` example. Renaming the profile means updating the runtime tests and that spec example; keeping `minimax` as an alias avoids both.
12. **Restore Pi's MCP registration**: `~/.pi/agent/mcp.json` → copy the `agent-runtime` server entry from `~/.pi/agent/mcp.json.bak-20261107142405`. Required for a Pi worker to have `report` at all.
13. **`~/.config/agent-runtime/hosts.json`** — the Pi host policy authorizes backends `["minimax", "codex", "claude"]`. It must authorize the new Pi backend name, and `paths` must cover the worktrees (`~/developer`). Read `server/host_policy.py:10` for the format.
14. **`~/.claude/CLAUDE.md`** — the Model classes table (symlinked from `~/developer/dotfiles/agents/.claude/CLAUDE.md`, dotfiles repo `0cc10d6`). Adding a Pi column means a dotfiles commit too.

## Live run state (parked — decide what to do with it)

The plan `docs/plans/2026-11-07-orchestration-baselines.plan.md` was launched and its pane is alive but **not progressing**:

- Pane: `orchestrate-orchestration-baseli` (hc address `t19v`, parent `t19r`), run dir `~/.local/state/orchestrate/orchestration-baselines/`.
- T1's worker (`claude --agent implementer --model sonnet --effort high`, pane `t19w`) **exited idle without a report** → T1 is `IN PROGRESS · decision pending: orchestration-baselines-t1 ended without a report: runtime state idle`.
- The open request is `~/.local/state/orchestrate/orchestration-baselines/t1/request.json` (`status: "open"`, `decision: null`).
- The driver is idle-looping (30 s ticks in `events.jsonl`) waiting on that decision.

Note the worker ran `--model sonnet`, i.e. **the real Claude, not MiniMax** — the driver defaults to `--cli claude` with no profile. That is consistent with "Pi/MiniMax only" being unconfigured so far.

**Recommended:** let the current run die rather than resume it under the new backend (its ledger and worktree are bound to the Claude backend). Stop the pane (`hc kill orchestrate-orchestration-baseli`), reset T1's Status in the plan to `TO-DO` so the driver re-dispatches it, and relaunch once the Pi backend exists. The skill's rule: `TO-DO` retries the unit as a fresh attempt; `COMPLETE <date>` marks it done by hand; any other edit leaves it paused.

**The plan also needs its schema fixed** (already partly done — the Status line was normalized to `Status: APPROVED` and the ticket cells were made machine-readable; a `D4` Decisions row records that). The plan's scenarios and `T1`-`T4` tickets are at `docs/plans/2026-11-07-orchestration-baselines.plan.md`; the driver validates them via `check_plan()` (`orchestrate.py:420`).

## Repo conventions (both repos)

- **agent-skills**: `AGENTS.md` — the gate is `scripts/run-tests.sh`; every test file runs in its own process, in parallel. A hang is a failure. Skills' frontmatter is read by YAML: quote any description holding `:` or `#`; `scripts/lint_skills.py` names file, line and reason.
- **agent-runtime**: `python3 -B -m unittest discover -s tests`. Plans live in `docs/plans/`, living specs in `docs/specs/`; every behaviour change updates the spec.
- Plans are the ledger of scope and decisions. When a decision is made mid-task, write it into the plan as a Decisions row.
- Plan ticket numbers stay out of product code, commit messages and PR descriptions. Scenario IDs belong only in test names or a Python test's docstring first line.

## Suggested order

1. Reconcile #39/#45 on `server/hc_tools.py` (or pick branches that avoid the overlap) and re-run the runtime's tests.
2. Restore `~/.pi/agent/mcp.json` from its backup — cheap, unblocks a Pi worker, and lets you verify Pi's `report` path early.
3. Runtime: `profiles.py` (pi family + Pi provider vars) → `hc_tools.spawn` (Pi argv) → `host_policy` (Pi worker may report) → identity check → tests. Amend R178 and `docs/specs/harness-adapters.md`.
4. Split the profile into `claude-minimax` + `pi`; update `hosts.json` to authorize the Pi backend.
5. Driver: Pi model column / effort mapping, brain tier pinned to `gpt-6.1-terra`, `--profile pi` plumbing → `scripts/run-tests.sh`.
6. Kill the parked pane, reset T1 to `TO-DO`, relaunch the plan with the Pi profile, and watch that a Pi worker starts, reports, and reaches `IN PROGRESS · awaiting merge (<PR>)`.

## Skills for the next session

- `/orchestrate` to relaunch the plan once the Pi backend works.
- `converge` (`python3 skills/converge/scripts/converge.py <plan> --final`) to check the plan against its scenarios before archiving.
- `tdd` for the runtime's red-first test work.
- `/cold-read` on `docs/plans/2026-11-07-orchestration-baselines.plan.md` to re-read the scope before touching it.
- `handoff` again if the run must pass to a third agent.
