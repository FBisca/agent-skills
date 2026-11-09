# agent-skills

Agent skills for [Claude Code](https://claude.com/claude-code), [Codex](https://developers.openai.com/codex) and [Pi](https://pi.dev/). They turn a raw idea into a gated, spec-driven build: each stage hands a checkable artifact to the next, and the gates are scripts, not opinions.

- **Deterministic gates.** `idea_check.py` and `converge.py` read files and exit non-zero; an agent cannot talk its way past them.
- **Agents that disagree on purpose.** `cold-read` asks a fresh reader to paraphrase a document; `orchestrate` builds with separate implementer agents and accepts a ticket only when its scenarios pass.
- **Tested.** The gate and orchestration scripts (`idea-frame`, `idea-answer`, `converge`, `cold-read`, `orchestrate`) have test suites that run in CI on Python 3.11 to 3.13, and a repo-level test lints every `SKILL.md`. `excalidraw` and `explain-video` are checked by their own render loops, not by unit tests.

## The pipeline

```mermaid
flowchart LR
    A["idea-frame<br/>grill the idea, map<br/>the open questions"] -->|idea_check gate 1| B["idea-answer<br/>route each question,<br/>write the Brief"]
    B -->|cold-read + gate 2| C["to-spec<br/>PRD"]
    C --> D["start-planning<br/>scenarios + vertical<br/>tickets, stop for approval"]
    D --> E["orchestrate<br/>implementer agents<br/>build ticket by ticket"]
    E -->|converge| F{"scenarios,<br/>tests, paths<br/>all pass?"}
    F -->|no| E
    F -->|yes| G["archive plan into<br/>the living spec"]
```

The full walkthrough, with the method behind each step and the findings from two backtests, is in **[docs/workflow.md](docs/workflow.md)**.

`to-spec` is an upstream skill (see [Upstream skills](#upstream-skills)). `orchestrate` delegates to workers through the [agent-runtime](https://github.com/FBisca/agent-runtime) tools.

The orchestration engine itself lives in `agent-runtime`, in its `agent-orchestrator` member. `orchestrate` keeps the workflow — its frontmatter, its references and a script that hands the command to that member — and no copy of the driver. See [docs/specs/orchestrator-single-engine.md](docs/specs/orchestrator-single-engine.md).

## Skills

Own = written for this repo. Derivative = modified from an upstream, with attribution in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

| Skill | What it does | Origin |
|---|---|---|
| [`idea-frame`](skills/idea-frame) | Grills one raw idea into a frame and a map of the questions that change the build, then gates it | Own |
| [`idea-answer`](skills/idea-answer) | Routes every open question to whoever can answer it, keeps the Brief current, gates the commitment | Own |
| [`cold-read`](skills/cold-read) | A zero-context reader paraphrases a document to show whether it can be followed | Derivative (Google, Apache-2.0) |
| [`start-planning`](skills/start-planning) | Plans one feature from its sources to WHEN/THEN scenarios and vertical tickets, then stops for approval | Own |
| [`orchestrate`](skills/orchestrate) | Builds an approved plan with implementer agents and gates each ticket on its scenarios | Own |
| [`converge`](skills/converge) | Deterministic check of a ticket or plan against its scenarios, tests and paths | Own |
| [`score-agent`](skills/score-agent) | Scores a finished coding session from its trace, diff and test evidence, against the four rubrics it ships | Own |
| [`score-steering`](skills/score-steering) | Scores how the human steered a coding session, advisory only, against the one rubric it ships | Own |
| [`excalidraw`](skills/excalidraw) | Hand-drawn Excalidraw diagrams written as a Python spec, linted and checked by rendering | Own |
| [`explain-video`](skills/explain-video) | Narrated tutorial videos built as HyperFrames films with a local voice | Own |
| [`assemble-crew`](skills/assemble-crew) | Proposes a crew for a task, including an adversary who tries to break the result | Own |
| [`deep-prompt`](skills/deep-prompt) | Deepens a task prompt with what a top professional would add before rewriting it | Own |
| [`gh-pr-create`](skills/gh-pr-create) | Opens pull requests safely with `gh` | Own |
| [`git-commit`](skills/git-commit) | Conventional Commits with project conventions | Own |
| [`handoff`](skills/handoff) | Compacts a conversation into a handoff document for another agent | Derivative (Matt Pocock, MIT) |
| [`zoom-out`](skills/zoom-out) | Asks for broader context on unfamiliar code | Upstream copy (Matt Pocock, MIT) |

## Install

Pick one.

**Claude Code plugin marketplace** (exposes every skill in this repo):

```
/plugin marketplace add FBisca/agent-skills
/plugin install agent-skills@fbisca-skills
```

**`npx skills`** (Claude Code, Codex and others):

```
npx skills add FBisca/agent-skills
```

**Clone and symlink**:

```bash
git clone https://github.com/FBisca/agent-skills.git
cd agent-skills
mkdir -p ~/.claude/skills ~/.agents/skills
for skill in skills/*/; do
  name="$(basename "$skill")"
  ln -sfn "$PWD/skills/$name" ~/.claude/skills/"$name"
  ln -sfn "$PWD/skills/$name" ~/.agents/skills/"$name"
done
```

`~/.claude/skills` is read by Claude Code, `~/.agents/skills` by Codex and by Pi.

### Harnesses

The same `SKILL.md` serves every harness. Each one discovers a skill natively — a directory with a `SKILL.md` whose frontmatter carries `name` and `description` — so no skill has to teach the harness how to invoke it.

`start-planning` needs one upstream skill, `grilling`, which is not vendored here: install it with `scripts/install-upstream.sh grilling` (see [Upstream skills](#upstream-skills)). The plan refuses to continue without it, and never skips the grill.

A harness with no subagent of its own dispatches the fresh-context gather through the adapter the skill ships (`skills/start-planning/scripts/fresh_context.py`), which runs a bounded, isolated session and validates its answer. The per-harness dispatch is in `skills/start-planning/references/delegation.md`; the supported methods and the known limitations are in **[docs/specs/harness-portability.md](docs/specs/harness-portability.md)**.

### Configuration

| Variable | Used by | Meaning |
|---|---|---|
| `VAULT_DIR` | `idea-frame`, `idea-answer`, `excalidraw`, `explain-video` | Root of your notes vault. Ideas live in `$VAULT_DIR/01-projects/<slug>/`. When unset, `idea_check.py` and the `excalidraw` helpers (`vault_dir()`, `style.py vault:`) exit 3 naming the variable; the other skills stop and tell you to set it. A bundled `idea-frame/templates/project.md` is used when the vault has no `90-templates/project.md`. |
| `AGENT_RUNTIME_HOME` | `orchestrate` | Checkout of [agent-runtime](https://github.com/FBisca/agent-runtime). It names the runtime, and the engine too: the `agent-orchestrator` member it holds is what the skill drives. Falls back to `agent-runtime` on `PATH`. |
| `HYPERFRAMES_SKILLS_DIR` | `explain-video` | `skills/` folder of HyperFrames v0.8.184; `skills/explain-video/scripts/fetch-hyperframes.sh` prints the export line. |

## Upstream skills

Some skills this workflow uses are maintained by others and are not copied here. [`skills.lock.json`](skills.lock.json) lists each with its source and exact install command; install them all with:

```bash
scripts/install-upstream.sh            # or: scripts/install-upstream.sh --dry-run grilling to-spec
```

| Source | Skills |
|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) | `diagnosing-bugs`, `domain-modeling`, `grilling`, `prototype`, `retro`, `setup-matt-pocock-skills`, `to-spec`, `writing-for-agents` |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (Apache-2.0) | `hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use` |

## Tests

```bash
uv sync                          # the environment: uv resolves and installs it
uv run pytest                    # the fast suite: the unit tests, under 3 seconds
uv run pytest -m integration     # the integration tests
uv run pytest -m "" -n 4         # the full suite, four workers
scripts/checks.sh                # the whole gate: lint, frontmatter, full suite
```

The tests are `unittest.TestCase` classes, run by pytest. `uv run pytest` takes the unit tests — the ones that stay
in process; `-m ""` overrides that default and takes every test. CI runs the same gate on Python 3.11, 3.12 and 3.13,
plus `shellcheck` on the scripts. The suite is offline: no network, no model, no agent process.

The suite covers the repo contracts (`tests/`: every `SKILL.md` has frontmatter with a `name` matching its folder and a `description` every harness can read as text; every dropped upstream is in the lock with an install command; `VAULT_DIR` is required; the harness portability and plan Markdown contracts hold) and each skill's own `skills/*/tests` suite.

Every test carries exactly one marker, `unit` or `integration`: a unit test is in process, isolated and deterministic;
an integration test drives a real boundary (a subprocess, a pipe, the filesystem). `scripts/run-tests.sh` runs every
test file in its own process, in parallel, and names the file that never finished — set `TEST_TIMEOUT` (seconds per
file) or `JOBS` (workers) to adjust it. For a focused run, use `uv run pytest path/to/tests/test_file.py`.

The frontmatter rules also run on their own, over any skills folder:

```bash
python3 scripts/lint_skills.py                 # this repo's skills
python3 scripts/lint_skills.py path/to/skills  # any other repo's skills
```

It is the same contract the gate enforces, so another repo that keeps its skills here can run it too. See [Frontmatter](docs/specs/harness-portability.md#frontmatter) for why a colon or a `#` in an unquoted description breaks a harness.

## License

MIT for original work, see [`LICENSE`](LICENSE). Derived material keeps its upstream license: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
