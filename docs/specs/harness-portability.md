# Harness portability

Paths: skills/start-planning/, tests/, docs/, README.md

What the shared skills do in each harness, and where a harness still lacks a tool the skill needs. This is the living spec of the portability work; the plan that started it is `docs/plans/2026-11-07-pi-skills-compatibility.plan.md`.

## How a harness reaches the skill

Discovery is the same everywhere: a skill is a directory with a `SKILL.md` whose frontmatter carries `name` and `description`. Each harness invokes it its own way, so no skill body teaches the invocation — the skill states the workflow, the reference states the mechanism.

The two delegated steps are dispatched the same way in every harness:

| Step | Every harness |
|---|---|
| gather (fresh context) | agent-runtime's `spawn` (`cli: claude`, `codex` or `pi`), the gather packet as its task; `wait` returns its report |
| grill | the `grilling` skill |

agent-runtime gives every harness a fresh agent with no inherited context, so the skill ships no adapter of its own. The gather is bounded (the `wait` timeout), read-only (its packet's rules), structured (one JSON object with exactly `sources`, `decisions`, `findings`, `counts`, `edge_cases`) and loud: a spawn failure, a timeout, a missing report or a malformed answer stops the plan, which never carries evidence the gatherer did not produce.

`/orchestrate` stays out of Pi at P1 (see Limitations).

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
- **Pi has no plan mode and no review subagent.** Steps that rely on a second opinion go through agent-runtime's `spawn`, like every other harness.
- **`grilling` must be installed separately.** The plan refuses to continue without it; it does not install it.
- **Frontmatter must be quoted when it holds a colon.** Pi's YAML parser rejects an unquoted `description:` with a colon inside it ("Nested mappings are not allowed in compact mappings") and skips the skill without failing loudly. `assemble-crew` and `deep-prompt` hit this; both descriptions are quoted now, and `tests/test_pi_discovery.py` fails if any skill in this repo stops loading in Pi.
- **A `#` in an unquoted description is worse than a colon.** YAML starts a comment there, so the description is silently cut at that word. Every harness does it: Pi, Claude Code and Codex all read `Friday, his #heritage-updates reply` as `Friday, his`. The skill still loads, so nothing reports the loss. Quote the value.
- **T3 is manual.** Nothing here proves a real plan was produced with MiniMax M3.1 inside Pi; that is the acceptance test in the plan.

## Verification

```bash
scripts/run-tests.sh
```

The portability contracts live in `tests/test_portability.py` (discovery, the shared skills' harness contracts, the plan Markdown contract), `tests/test_pi_discovery.py` (Pi's own loader finds the skills: offline, no model) and in `skills/start-planning/tests/` (the plan contract and the dependency check). They run offline: no network, no model, no Pi process.

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

The portability contracts are enforced by `tests/test_portability.py` (the engine's plan contract: test-suite's "Plan ticket table contract" and "Unit and integration markers"), `tests/test_pi_discovery.py` ("Pi discovers every skill") and `skills/start-planning/tests/test_portability.py` ("Plan ticket table contract"). Their living spec is `docs/specs/test-suite.md`.

## Requirements

### Requirement: Pi runs the planning skill
`start-planning`, invoked in Pi as `/skill:start-planning`, SHALL load the same planning contract and write a plan with the required headings, scenarios and ticket columns.

#### Scenario: invoked in Pi
- WHEN `start-planning` is invoked in Pi as `/skill:start-planning`
- THEN it loads the same planning contract and writes a plan with the required headings, scenarios and ticket columns

### Requirement: Pi dependencies fail loudly
A skill that needs `grilling` or a fresh-context gatherer under Pi SHALL run a supported Pi invocation, or fail with a concrete missing-dependency message, and never skip the step.

#### Scenario: a dependency under Pi
- WHEN a skill needs `grilling` or a fresh-context gatherer under Pi
- THEN a supported Pi invocation runs, or the skill fails with a concrete missing-dependency message, and never skips the step

### Requirement: Claude Code and Codex unchanged
A skill that runs under Claude Code or Codex SHALL keep its commands, gates and validation behaviour unchanged.

#### Scenario: the same skill in Claude Code or Codex
- WHEN the same skill runs under Claude Code or Codex
- THEN its commands, gates and validation behaviour are unchanged

### Requirement: Portability enforced offline
The offline test suite SHALL enforce skill discovery, the plan Markdown contract and the portability contracts.

#### Scenario: the suite runs offline
- WHEN the test suite runs offline
- THEN skill discovery, the plan Markdown contract and the portability contracts are enforced
