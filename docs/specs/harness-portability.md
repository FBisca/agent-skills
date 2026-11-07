# Harness portability

Paths: skills/start-planning/, tests/, docs/, README.md

What the shared skills do in each harness, and where a harness still lacks a tool the skill needs. This is the living spec of the portability work; the plan that started it is `docs/plans/2026-11-07-pi-skills-compatibility.plan.md`.

- **R1** WHEN `start-planning` is invoked in Pi as `/skill:start-planning`, THEN it loads the same planning contract and writes a plan with the required headings, scenarios and ticket columns (from pi-skills-compatibility/S1).
- **R2** WHEN a skill needs `grilling` or a fresh-context gatherer under Pi, THEN a supported Pi invocation runs, or the skill fails with a concrete missing-dependency message, and never skips the step (from pi-skills-compatibility/S2).
- **R3** WHEN the same skill runs under Claude Code or Codex, THEN its commands, gates and validation behaviour are unchanged (from pi-skills-compatibility/S3).
- **R4** WHEN the test suite runs offline, THEN skill discovery, the plan Markdown contract and the portability contracts are enforced (from pi-skills-compatibility/S4).

## Supported invocation methods

| Skill | Claude Code | Codex | Pi |
|---|---|---|---|
| `start-planning` | `/start-planning` | the `start-planning` skill | `/skill:start-planning` |
| gather (fresh context) | a Task subagent, no fork of the session | its subagent run | `python3 skills/start-planning/scripts/fresh_context.py --packet <packet>` |
| grill | the Skill tool with `grilling` | the `grilling` skill | `/skill:grilling` |
| `orchestrate` | `/orchestrate <plan>` | `/orchestrate <plan>` | not supported at P1 (see Limitations) |

Discovery is the same everywhere: a skill is a directory with a `SKILL.md` whose frontmatter carries `name` and `description`. `name` matches the folder name, so the command is `/skill:<folder>` in Pi.

## The Pi gatherer

Pi has no subagent tool, so the fresh-context gather is a script: `skills/start-planning/scripts/fresh_context.py`.

- **Isolation.** A separate `pi --print` session: `--no-session`, its own `--session-dir`, no `--continue`, no `--resume`, no extensions, no MCP. The parent conversation is never part of the prompt; the packet is.
- **Bounded.** A timeout (`--timeout`, default 600s) and a restricted tool set (`read,ls,grep,find`). `--allow-bash` adds `bash` for read-only queries; `--inherit-env` passes the whole parent environment.
- **Structured.** The answer must be one JSON object with exactly `sources`, `decisions`, `findings`, `counts`, `edge_cases`. Anything else is malformed.
- **Loud on failure.** Exit codes: `0` ok, `2` usage, `3` pi not found, `4` pi failed, `5` timeout, `6` malformed answer, `7` packet refused. Planning stops on any non-zero exit; the plan never carries evidence the gatherer did not produce.
- **No credentials in the packet.** A packet carrying a secret-looking string is refused before the subprocess starts.

## The `grilling` dependency

`grilling` is an upstream skill and is not vendored in this repo. Before the grill, the plan runs:

```
python3 skills/start-planning/scripts/check_deps.py grilling
```

It prints `FOUND grilling: <path>` when the skill is installed (it searches `~/.agents/skills`, `~/.claude/skills`, the project `.agents/skills` and `.claude/skills`, Pi's own `skills` setting and this repo's `skills/`) and exits non-zero with the install command when it is not:

```
scripts/install-upstream.sh grilling
```

## Known limitations

- **`/orchestrate` does not run under Pi yet.** The driver needs the agent-runtime tools, which Pi does not expose. P1 keeps the driver untouched; the Pi path for orchestration is later work (out of scope in this plan).
- **The Pi gatherer cannot run commands by default.** Counts that need a live database or script are either run by the parent or opted into with `--allow-bash`, which widens the subprocess's powers.
- **Pi has no plan mode and no review subagent.** Steps that rely on a second opinion must go through the gatherer script or an explicit `/skill:` command.
- **`grilling` must be installed separately.** The plan refuses to continue without it; it does not install it.
- **Frontmatter must be quoted when it holds a colon.** Pi's YAML parser rejects an unquoted `description:` with a colon inside it ("Nested mappings are not allowed in compact mappings") and skips the skill without failing loudly. `assemble-crew` and `deep-prompt` hit this; both descriptions are quoted now, and `tests/test_pi_discovery.py` fails if any skill in this repo stops loading in Pi.
- **T3 is manual.** Nothing here proves a real plan was produced with MiniMax M3.1 inside Pi; that is the acceptance test in the plan.

## Verification

```bash
scripts/run-tests.sh
```

The portability contracts live in `tests/test_portability.py` (discovery, the shared skills' harness contracts, the plan Markdown contract), `tests/test_pi_discovery.py` (Pi's own loader finds the skills: offline, no model) and in `skills/start-planning/tests/` (the gatherer's isolation, timeouts, malformed answers and the dependency check). They run offline: no network, no model, no Pi process.

## The manual acceptance test (T3)

T3 is a person running Pi, not a test in the suite:

```bash
# 1. the skills are linked where Pi looks for them
ls -l ~/.agents/skills/start-planning ~/.agents/skills/grilling

# 2. the dependency the plan needs is installed
python3 skills/start-planning/scripts/check_deps.py grilling

# 3. in a scratch repo, invoke the skill with MiniMax M3.1
cd /path/to/scratch-repo
pi --model minimax/MiniMax-M3.1-Flash
#   then, inside Pi:  /skill:start-planning <the feature to plan>

# 4. the plan lands in docs/plans/YYYY-MM-DD-<slug>.plan.md with Status: AWAITING APPROVAL
# 5. the contract holds
python3 -m unittest discover -s tests -t tests -p "test_portability.py"
```

Step 3 also has to show the gather step running: the plan's Sources table and decisions come from the gatherer, not from the parent session.
