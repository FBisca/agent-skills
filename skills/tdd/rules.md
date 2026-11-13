# Rules: the most protection for the least test cost

The goal is the most meaningful regression protection for the least test code, maintenance and run time. Each rule below has a nuance that keeps it from being applied as a blunt count. Read the nuance before you act on the rule, whether you are admitting a new test or pruning an old one.

## The ten rules

1. **Behaviour over implementation.** Assert observable outcomes through the public interface, as in [tests.md](tests.md).
   _Nuance:_ an internal sequence is fair to assert when the sequence itself is the requirement, for example "refuse before anything is launched" or "the lock is released on failure".

2. **Reuse before creating.** Search the existing tests for the behaviour before you add one: by the function, the error text, the requirement id and the scenario name.
   _Nuance:_ "covered" means the same guarantee at the same boundary. A test that touches the same code but asserts something else does not cover it.

3. **One behaviour, one primary test.** Extend or parametrise the existing test rather than adding a near-copy.
   _Nuance:_ this rule targets duplication. It does not cap independent scenarios. Authentication, concurrency, failure recovery, rollback and a race each fail differently and each earn their own test, even on the same feature.

4. **Test meaningful boundaries.** An edge case earns a test when it is a distinct failure mode or a stated requirement: empty, one, many, the limit, the limit plus one, a malformed input, a dependency that fails.
   _Nuance:_ different input data alone is not independent value. Several parametrised cases can all be valuable, but only when each one could fail on its own.

5. **One level per scenario.** Prove a scenario at the lowest level that shows it reliably. Use higher levels to prove the boundary, not to repeat the lower level's cases.
   _Nuance:_ deliberate overlap at **different real boundaries** is fine: a unit contract, one integration test that shows the contract crosses the process or the store, and one end-to-end journey for a critical flow. What is not fine is ten integration tests that each re-prove one validation rule.

6. **Parametrise variations of one contract.** Use `pytest.mark.parametrize` (or `subTest` in `unittest` suites, `test.each` in JS).
   _Nuance:_ parametrise only cases with the same setup and the same kind of assertion. When a case needs different setup, or asserts a different outcome, it is a different test. Give each case an id, so a failure names the case.

7. **Tests come from requirements and credible risks.** A hypothetical edge case that no requirement names and no plausible change would break does not earn a test.
   _Nuance:_ a **regression test for a failure that was actually observed** always earns its place, even when it looks like an existing test. It pins a path that already broke once.

8. **Tests follow the contract.** When a contract changes, update or delete the tests that asserted the old one in the same change, so the suite holds no historical assertions.
   _Nuance:_ before you delete or rename a test, check whether a spec, plan or requirement table cites it by name, and update the citation in the same change. Before you delete a test as a duplicate, name the test that keeps its guarantee.

9. **Fault detection is the measure.** Test count and coverage percentage are not. High coverage alone does not show the tests are good.
   _Nuance:_ required safety, security and contract coverage stays even when it is slow. Deleting useful coverage to make the suite faster is not an improvement. Make the test cheaper instead (rule 11), and never weaken or reclassify a test only to speed up the run.

10. **Proportionality.** Size the test change to the code change: a one-line fix adds or extends one case, not a new suite.
    _Nuance:_ running the same test many times while you work is the loop, not proliferation. Count test **cases**, not runs.

## Cost rules

These keep a test that has earned its place from costing more than it must.

11. **Build expensive setup once.** A server, a repository, a release build or a full lifecycle is built once per class or session and shared by the tests that only read its result. A test that changes the state works on its own copy. Start only what the test uses: a worker, server or session the test never talks to is pure cost.

12. **Wait on events, not on the clock.** A fixed sleep, or an assertion that waits out a real timeout, costs its full duration on every run and flakes under load. Inject a clock or a barrier, and keep a real wait only where the assertion is about elapsed time.
    _Nuance:_ an assertion that only checks "the process was still running after N seconds" passes even when the process never reached the code under test. Assert on a signal the code produced.

13. **Seed state directly.** Reaching a state that the test does not exercise (a full team, a long inbox, a delivered plan) through the slow public path is setup, not evidence. Seed it through the store or a fixture, and drive only the step under test through the real boundary.

## The pyramid, for an orchestrator

As an example of the levels in [SKILL.md](SKILL.md), in an agent orchestration runtime:

- **Unit:** scheduling decisions, retry and round caps, state transitions, plan and config parsing, routing precedence, refusal rules, classification of results.
- **Integration:** driver-to-worker execution, persistence and the store, subprocess and signal handling, IPC between sessions, evidence contracts run against a real tree.
- **End to end:** a few representative workflows that prove one whole orchestration completes, from an approved plan to an archived result.
