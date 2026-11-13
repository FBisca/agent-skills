# Rules behind admission

Each rule carries the nuance that keeps it from being applied as a blunt count. Apply both when you admit, delete, merge or move a test.

## Admission

- **One behaviour, one primary test.** Extend or parametrise the existing test instead of adding a near-copy.
  _Nuance:_ independent failure modes (authentication, concurrency, failure recovery, rollback, a race) each earn their own test, even on one feature.
- **Parametrise one contract** (`pytest.mark.parametrize`, `subTest`, `test.each`), with an id per case.
  _Nuance:_ a case that needs different setup, or asserts a different outcome, is a different test.
- **Edge cases are distinct failure modes** that a requirement or a credible risk names: empty, one, many, the limit and one past it, malformed input, a failing dependency.
  _Nuance:_ different input data alone adds nothing; each case must be able to fail on its own.
- **An observed failure earns a regression test,** even when it resembles an existing one: it pins a path that already broke.
- **Tests follow the contract.** When a contract changes, update or delete the tests of the old one in the same change.
  _Nuance:_ update any spec or plan that cites a test by name, and name the test that keeps a deleted duplicate's guarantee.
- **Fault detection is the measure**, not test count or coverage percentage.
  _Nuance:_ required safety, security and contract coverage stays even when slow. Make it cheaper with the cost rules, and keep its strength and its level.
- **Proportionality.** A one-line fix adds or extends one case.
  _Nuance:_ re-running tests in the loop is not proliferation; count cases, not runs.

## Cost

A test that earns its place still costs no more than it must.

- **Build expensive setup once.** A server, a repository, a release build or a full lifecycle is built once per class or session. Tests that only read it share it; tests that change it take a copy. Start only what the test talks to.
- **Seed state directly.** Reach a state the test does not exercise (a full team, a long inbox, a delivered plan) through the store or a fixture, and drive only the step under test through the real boundary.
- **Wait on events.** Use an injected clock or a barrier: a fixed sleep or a waited-out timeout costs its full duration on every run and flakes under load. Keep a real wait only when the assertion is about elapsed time.
  _Nuance:_ "still running after N seconds" passes even when the code under test was never reached; assert on a signal the code produced.
