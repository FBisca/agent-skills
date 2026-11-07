# AGENTS.md

Instructions for agents working in this repo.

## The suite is the gate

`scripts/run-tests.sh` is the gate for any change here; it runs every test file in its own process, in parallel
(`JOBS` limits the workers). Run the gate before reporting a change complete. A suite that hangs is a failing suite:
the cause is a fake that never answers, not a slow test.

## Test fakes are contracts

`skills/orchestrate/scripts/orchestrate.py` polls whatever the fakes answer. A fake with no terminal answer — a PR that
stays OPEN, a check that never reports, a worker that never finishes — makes the driver poll forever, so the suite
hangs instead of failing.

- Land a fake's contract change together with the driver change that answers it, in one change.
- Give every fake a terminal answer by default; script the exception only in the test that needs it.
- Keep the fakes offline. A fake that reaches the network costs seconds per call and turns a suite into minutes.

## The fakes are modules, not programs

The fakes live in `skills/orchestrate/tests/`: `fake_runtime.py` (the agent-runtime), `fake_gh.py` (the GitHub CLI)
and `fake_wait_checks.py` (the CI gate's wait). The driver reaches them through seams — `runtime_process`,
`gh_process` and the `wait_checks` module — so a test run answers them in process and starts no process per call. The
fixture also puts thin wrappers for the same modules on PATH, for a driver run outside the tests.

A new seam follows the same shape: the driver calls a function it could have called directly, and the tests answer
that function. A fake that needs a process of its own has to earn it.
