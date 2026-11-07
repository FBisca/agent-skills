# AGENTS.md

Instructions for agents working in this repo.

## The suite is the gate

`scripts/run-tests.sh` is the gate for any change here; it runs every test file in its own process, in parallel
(`JOBS` limits the workers). Run the gate before reporting a change complete. A suite that hangs is a failing suite:
the cause is a fake that never answers, not a slow test.

## A skill's frontmatter is read by YAML, not by us

Every harness reads a `SKILL.md` frontmatter as YAML. A value that is not quoted and holds a colon is read as a nested
mapping, so the skill vanishes from that harness; a value that holds a `#` is cut at that word, so the harness routes on
half a description. `scripts/lint_skills.py` holds the rules and names the file, the line and the reason; run it on
any skills folder, not only this repo's. The gate runs it over this repo's skills.

Quote a description that holds a colon or a `#`. The lint is stdlib-only on purpose: it must run in CI on a bare Python,
and the YAML dialects the harnesses use disagree about plain scalars, so it accepts a value only when every dialect
reads the same text back.

## Test fakes are contracts

`skills/orchestrate/scripts/orchestrate.py` polls whatever the fakes answer. A fake with no terminal answer — a PR that
stays OPEN, a check that never reports, a worker that never finishes — makes the driver poll forever, so the suite
hangs instead of failing.

- Land a fake's contract change together with the driver change that answers it, in one change.
- Give every fake a terminal answer by default; script the exception only in the test that needs it.
- Exception: the `gh` fake keeps a draft PR OPEN until it is made ready so review tests can observe that transition.
  It must raise after 100 draft polls per PR, so a missing transition fails the test instead of hanging the suite.
- Keep the fakes offline. A fake that reaches the network costs seconds per call and turns a suite into minutes.

## The fakes are modules, not programs

The fakes live in `skills/orchestrate/tests/`: `fake_runtime.py` (the agent-runtime)
and `fake_gh.py` (the GitHub CLI). The driver reaches them through seams — `runtime_process` and `gh_process` —
so a test run answers them in process and starts no process per call. The fixture also puts thin wrappers for the
same modules on PATH, for a driver run outside the tests.

A new seam follows the same shape: the driver calls a function it could have called directly, and the tests answer
that function. A fake that needs a process of its own has to earn it.
