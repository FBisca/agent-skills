# The contract: `plan/1`

The skeleton to write `<name>.plan.yaml` from. The engine's loader is strict: an unknown or duplicate key, a missing field or a wrong type is refused, and `plan check` names the field and the fix. Never write `approval`: `plan approve` writes it.

```yaml
schema: plan/1
slug: <slug>
goal: <one sentence: what is true for whom once the plan is built>
spec: docs/specs/<area>.md          # the living spec the scenarios archive into
outcome: [S7]                       # the scenarios that prove the goal; each has evidence

scenarios:
  - id: S1
    when: <condition>
    then: <observable outcome>
  - id: S7
    when: <condition>
    then: <observable outcome>
    evidence:                       # one of check (+ baseline) or human
      check: uv run pytest tests/test_feature.py -q --junitxml="$EEC_JUNIT"
      baseline: fail                # pass | fail: what the check does at base today
      oracle: [test_feature.py.oracle]   # files in <name>.oracle/, optional
      place: tests/                 # repo directory each oracle is copied to, `.oracle` dropped
      timeout: 600                  # seconds, optional
      env: [API_TOKEN]              # names passed through to the check, optional
      negative: break.patch         # a patch in <name>.oracle/ that breaks the behaviour: the check must then fail on an assertion, optional
      promote: true                 # copy the oracle into the repo at archive (default true)
  - id: S8
    when: <condition>
    then: <what only a person can observe>
    evidence:
      human: <what a person confirms>   # human alone, no check options

tickets:
  - id: T1
    delivers: <the end-to-end behaviour>
    satisfies: [S1, S7]
    paths: [src/feature/, tests/test_feature.py]
    size: regular                   # small | regular
    difficulty: simple              # simple | complex
    blocked_by: []                  # optional
    risk: [state]                   # optional: security, concurrency, retry-idempotency, migration, external, state
    evidence_waiver: <where the risk is verified instead>   # optional
  - id: T2
    delivers: <what a person runs or approves>
    satisfies: [S7]
    paths: [docs/runbook.md]
    owner: <person>                 # default agent; a person's ticket has no size or difficulty
    repo: ../other-repo             # only for a ticket outside this repository
```

## Rules the loader enforces

- IDs: scenarios `S<n>` with an optional letter (`S4a`), tickets `T<n>`, each unique; every reference names a declared ID; `blocked_by` has no cycle.
- Paths (`paths`, `place`, `oracle`, `negative`): literal and repo-relative, no globs, no `..`, not absolute. A directory ends `/`.
- Evidence is exactly one kind: `check` with `baseline`, or `human` alone.
- An oracle `place` stays inside the repository, and the promoted file must not exist yet.
- An agent ticket carries `size` and `difficulty`; `repo` is only for a person's ticket.
- A risk-tagged ticket satisfies a scenario with evidence or carries `evidence_waiver`.

## The check's environment

The engine runs `check` in a scratch checkout of the phase's commit, each oracle already copied to its `place`, and `EEC_JUNIT` set to the path for a JUnit XML report. A check that writes `--junitxml="$EEC_JUNIT"` lets the receipt name the tests that ran.
