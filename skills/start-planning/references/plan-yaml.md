# The contract: `plan/1`

The skeleton to write `<plans.dir>/YYYY-MM-DD-<slug>/plan.yaml` from. The engine's loader is strict: an unknown or duplicate key, a missing field or a wrong type is refused, and `plan check` names the field and the fix. Never write `approval`: `plan approve` writes it.

```yaml
schema: plan/1
slug: <slug>
goal: <one sentence: what is true for whom once the plan is built>
spec: docs/specs/<area>.md          # the living spec the scenarios archive into; optional when the plan discards
domain: <area>                      # the folder under <package>/<acceptance.dir>/ promoted tests join; required to promote
archive: promote                    # promote | discard, optional: the repo config's archive.mode when absent
outcome: [S7]                       # the scenarios that prove the goal; each has evidence

scenarios:
  - id: S1
    when: <condition>
    then: <observable outcome>
  - id: S7
    when: <condition>
    then: <observable outcome>
    evidence:                       # one of check (+ baseline) or human
      check: uv run pytest pkg/acceptance/<area>/test_feature.py -q --junitxml="$EEC_JUNIT"
      baseline: fail                # pass | fail: what the check does at base today
      acceptance: [test_feature.py] # files in the plan folder's acceptance/, optional
      package: pkg                  # the package each acceptance file belongs to; `.` for the repository root
      timeout: 600                  # seconds, optional
      env: [API_TOKEN]              # names passed through to the check, optional
      negative: negatives/break.patch   # relative to the plan folder: a patch that breaks the behaviour; the check must then fail on an assertion, optional
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
- Paths (`paths`, `package`, `acceptance`, `negative`): literal and relative, no globs, no `..`, not absolute. A directory ends `/`. `paths` and `package` are repo-relative and stay inside the repository; `acceptance` names files in the plan folder's `acceptance/`, `negative` a file relative to the plan folder.
- Evidence is exactly one kind: `check` with `baseline`, or `human` alone.
- A promoting plan has a `domain`. Each acceptance file's destination, `<package>/<acceptance.dir>/<domain>/<file>`, does not exist yet, and its basename matches no test module already in the package.
- A discarding plan needs neither `spec` nor `domain`.
- An agent ticket carries `size` and `difficulty`; `repo` is only for a person's ticket.
- A risk-tagged ticket satisfies a scenario with evidence or carries `evidence_waiver`.

## The check's environment

The engine runs `check` in a scratch checkout of the phase's commit, each acceptance file already placed at its destination, and `EEC_JUNIT` set to the path for a JUnit XML report. A check that writes `--junitxml="$EEC_JUNIT"` lets the receipt name the tests that ran.
