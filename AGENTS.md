# AGENTS.md

Instructions for agents working in this repo.

## The suite is the gate

`scripts/run-tests.sh` is the gate for any change here; `scripts/run-tests-parallel.sh` runs the same tests in parallel
for a fast local check. Run the gate before reporting a change complete. A suite that hangs is a failing suite: the
cause is a fake that never answers, not a slow test.

## Test fakes are contracts

`skills/orchestrate/scripts/orchestrate.py` polls whatever the fakes in `skills/orchestrate/tests/fixtures.py` answer.
A fake with no terminal answer — a PR that stays OPEN, a check that never reports, a worker that never finishes — makes
the driver poll forever, so the suite hangs instead of failing.

- Land a fake's contract change together with the driver change that answers it, in one change.
- Give every fake a terminal answer by default; script the exception only in the test that needs it.
- Keep the fakes offline. A fake that reaches the network costs seconds per call and turns a suite into minutes.
