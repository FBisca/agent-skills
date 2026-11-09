# AGENTS.md

Instructions for agents working in this repo.

## Testing

- **Unit:** In-process, isolated, deterministic; mock external dependencies. A unit test may read the repository and
  write only inside its own temporary directory.
- **Integration:** Tests real component boundaries (subprocesses, IPC, databases, network, servers), even when
  dependencies are faked.
- A temporary directory is not a boundary. A test that writes only in its own temporary directory is still `unit`;
  a test that starts a process, or talks to a server or the network, is `integration`.
- Prefer unit tests for fast feedback; use integration tests to verify contracts.
- Classify tests by behaviour, not filename. Never weaken or reclassify tests just to improve speed.

The environment is [uv](https://docs.astral.sh/uv/): `uv sync` sets it up, `uv run pytest` is the runner. The tests
are `unittest.TestCase` classes, so pytest runs them unchanged.

```bash
uv run pytest                    # the fast suite (the unit tests): under 3 seconds
uv run pytest -m integration     # the integration tests
uv run pytest -m "" -n 4         # the full suite, four workers
uv run pytest -m "" -n auto      # the full suite, every core
uv run pytest --durations=20     # where the time goes (add -m "" for the full suite)
```

`uv run pytest` runs the unit tests; `-m ""` is what overrides that default for the full suite. Run the fast suite
while you work; run the full suite before you report a change complete. `scripts/checks.sh` is the whole gate (lint,
frontmatter, full suite) and is what CI runs. If the suite hangs, `scripts/run-tests.sh` runs every file in its own
process (`JOBS` limits the workers, `TEST_TIMEOUT` the seconds per file) and names the file that never finished: a
suite that hangs is a failing suite, and the cause is a fake that never answers, not a slow test.

The run polices itself (`conftest.py`). It ends with a failing status, and names the cause, when the fast suite takes
3 seconds or more, when it leaves a temporary entry behind, or when a `unit` test is skipped. Every skip prints its
reason, so a skip names the dependency it lacks.

## A skill's frontmatter is read by YAML, not by us

Every harness reads a `SKILL.md` frontmatter as YAML. A value that is not quoted and holds a colon is read as a nested
mapping, so the skill vanishes from that harness; a value that holds a `#` is cut at that word, so the harness routes on
half a description. `scripts/lint_skills.py` holds the rules and names the file, the line and the reason; run it on
any skills folder, not only this repo's. The gate runs it over this repo's skills.

Quote a description that holds a colon or a `#`. The lint is stdlib-only on purpose: it must run in CI on a bare Python,
and the YAML dialects the harnesses use disagree about plain scalars, so it accepts a value only when every dialect
reads the same text back.

## Test fakes are contracts

The engine polls whatever the fakes answer. A fake with no terminal answer — a PR that
stays OPEN, a check that never reports, a worker that never finishes — makes the driver poll forever, so the suite
hangs instead of failing.

- Land a fake's contract change together with the driver change that answers it, in one change.
- Give every fake a terminal answer by default; script the exception only in the test that needs it.
- Exception: the `gh` fake keeps a draft PR OPEN until it is made ready so review tests can observe that transition.
  It must raise after 100 draft polls per PR, so a missing transition fails the test instead of hanging the suite.
- Keep the fakes offline. A fake that reaches the network costs seconds per call and turns a suite into minutes.

## The fakes are modules, not programs

The engine — and with it its fakes — lives in [agent-runtime](https://github.com/FBisca/agent-runtime), in the
`agent-orchestrator` member: `fake_runtime.py` (the agent-runtime) and `fake_gh.py` (the GitHub CLI) sit in that
repository's `packages/agent-orchestrator/tests/`. The driver reaches them through seams — `runtime_process` and
`gh_process` — so a test run answers them in process and starts no process per call. The fixture also puts thin
wrappers for the same modules on PATH, for a driver run outside the tests.

This repository keeps the skill's own suite and the skill's script, and the script is a shim: it resolves the member's
CLI and hands it the command. A fake or a seam of the engine changes in that repository, next to the driver that
answers it.

A new seam follows the same shape: the driver calls a function it could have called directly, and the tests answer
that function. A fake that needs a process of its own has to earn it.
