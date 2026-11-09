# Harness portability

Paths: skills/start-planning/, tests/, docs/, README.md

What the shared skills do in each harness, and where a harness still lacks a tool the skill needs. This is the living spec of the portability work; the plan that started it is `docs/plans/2026-11-07-pi-skills-compatibility.plan.md`.

- **R1** WHEN `start-planning` is invoked in Pi as `/skill:start-planning`, THEN it loads the same planning contract and writes a plan with the required headings, scenarios and ticket columns (from pi-skills-compatibility/S1).
- **R2** WHEN a skill needs `grilling` or a fresh-context gatherer under Pi, THEN a supported Pi invocation runs, or the skill fails with a concrete missing-dependency message, and never skips the step (from pi-skills-compatibility/S2).
- **R3** WHEN the same skill runs under Claude Code or Codex, THEN its commands, gates and validation behaviour are unchanged (from pi-skills-compatibility/S3).
- **R4** WHEN the test suite runs offline, THEN skill discovery, the plan Markdown contract and the portability contracts are enforced (from pi-skills-compatibility/S4).

## How a harness reaches the skill

Discovery is the same everywhere: a skill is a directory with a `SKILL.md` whose frontmatter carries `name` and `description`. Each harness invokes it its own way, so no skill body teaches the invocation — the skill states the workflow, the reference states the mechanism.

What differs is how the two delegated steps are dispatched. That table lives with the skill, loaded on demand: `skills/start-planning/references/delegation.md`.

| Step | Claude Code | Codex | A harness with no subagent |
|---|---|---|---|
| gather (fresh context) | a Task subagent, no fork of the session | its subagent run | the adapter `skills/start-planning/scripts/fresh_context.py` |
| grill | the Skill tool with `grilling` | the `grilling` skill | the `grilling` skill |

`/orchestrate` stays out of Pi at P1 (see Limitations).

## The gatherer adapter

A harness with no subagent of its own dispatches the fresh-context gather through the adapter the skill ships: `skills/start-planning/scripts/fresh_context.py`.

- **Isolation.** A separate `pi --print` session: `--no-session`, its own `--session-dir`, no `--continue`, no `--resume`, no extensions, no MCP. The parent conversation is never part of the prompt; the packet is.
- **Bounded.** A timeout (`--timeout`, default 600s) and a restricted tool set (`read,ls,grep,find`). `--allow-bash` adds `bash` for read-only queries; `--inherit-env` passes the whole parent environment.
- **Structured.** The answer must be one JSON object with exactly `sources`, `decisions`, `findings`, `counts`, `edge_cases`. Anything else is malformed.
- **Loud on failure.** Exit codes: `0` ok, `2` usage, `3` pi not found, `4` pi failed, `5` timeout, `6` malformed answer, `7` packet refused. Planning stops on any non-zero exit; the plan never carries evidence the gatherer did not produce.
- **Why it ships with the skill.** Pi has a subagent extension, but as an example: it must be installed by hand before any skill can call it, and it spawns the same kind of separate `pi` process. A skill has to work for someone who installed Pi and nothing else.
- **No credentials in the packet.** A packet carrying a secret-looking string is refused before the subprocess starts.

## Frontmatter

Every harness reads a skill's frontmatter as YAML, and each one is a little different about what
it accepts. A frontmatter that YAML cannot parse makes the skill disappear from that harness; a
frontmatter that YAML reads as something other than the text the author wrote makes the harness
route on a description nobody wrote. Neither is loud.

The rules, and the script that enforces them:

```bash
python3 scripts/lint_skills.py                 # this repo's skills
python3 scripts/lint_skills.py path/to/skills  # any other repo's skills
```

The rule the lint holds is the one every harness agrees on: **the value a harness reads is the
text the author wrote.** A description that holds a colon or a `#` is quoted, because an unquoted
value is a YAML plain scalar and plain scalars do not survive those two characters:

| Unquoted | YAML reads | The harness gets |
| --- | --- | --- |
| `description: into the vault: tasks` | a nested mapping | the whole frontmatter fails to parse; the skill vanishes |
| `description: Friday, his #reply` | a comment starts at the `#` | `Friday, his` |

Both dialects are covered. YAML 1.1 (PyYAML) and YAML 1.2 (the `yaml` npm package Pi uses)
disagree about plain scalars such as `yes`, `12:30` and `2026-11-07` - one reads a boolean or a
number where the other reads text - so a value is only accepted when both read the same thing
back. A description that is not text is refused for the same reason.

The lint is stdlib-only, so it runs in CI on a bare Python, and it names the file, the line and
the reason. `tests/test_skill_frontmatter.py` runs it over this repo's skills and over the
frontmatter that must be refused.

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

- **`/orchestrate` does not run under Pi yet.** The driver needs the agent-runtime tools, which Pi does not expose. The driver itself now lives in [agent-runtime](https://github.com/FBisca/agent-runtime), in the `agent-orchestrator` member, and this skill's script hands the command to it; the Pi path for orchestration is later work (out of scope in this plan).
- **The Pi gatherer cannot run commands by default.** Counts that need a live database or script are either run by the parent or opted into with `--allow-bash`, which widens the subprocess's powers.
- **Pi has no plan mode and no review subagent.** Steps that rely on a second opinion must go through a delegation: the harness's own, or the adapter the skill ships.
- **`grilling` must be installed separately.** The plan refuses to continue without it; it does not install it.
- **Frontmatter must be quoted when it holds a colon.** Pi's YAML parser rejects an unquoted `description:` with a colon inside it ("Nested mappings are not allowed in compact mappings") and skips the skill without failing loudly. `assemble-crew` and `deep-prompt` hit this; both descriptions are quoted now, and `tests/test_pi_discovery.py` fails if any skill in this repo stops loading in Pi.
- **A `#` in an unquoted description is worse than a colon.** YAML starts a comment there, so the description is silently cut at that word. Every harness does it: Pi, Claude Code and Codex all read `Friday, his #heritage-updates reply` as `Friday, his`. The skill still loads, so nothing reports the loss. Quote the value.
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
uv run pytest tests/test_portability.py
```

Step 3 also has to show the gather step running: the plan's Sources table and decisions come from the gatherer, not from the parent session.

## Tests

The portability contracts are enforced by `tests/test_portability.py` (the plan reader and the engine's plan contract, `test-suite/R1`, `test-suite/R2`, `test-suite/R12`), `tests/test_pi_discovery.py` (`test-suite/R16`) and `skills/start-planning/tests/test_portability.py` (`test-suite/R2`). Their living spec is `docs/specs/test-suite.md`.
