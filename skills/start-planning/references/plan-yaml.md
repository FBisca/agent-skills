# The contract: `plan/1`

The skeleton to write `<plans.dir>/YYYY-MM-DD-<slug>/plan.yaml` from. The engine's loader is strict: an unknown or duplicate key, a missing field or a wrong type is refused, and `plan check` names the field and the fix. Never write `approval`: `plan approve` writes it.

```yaml
schema: plan/1
slug: <slug>
goal: <one sentence: what is true for whom once the plan is built>
spec: docs/specs/<area>.md          # the living spec the scenarios archive into; optional when the plan discards
archive: promote                    # promote | discard, optional: the repo config's archive.mode when absent

scenarios:
  - id: S1
    when: <condition>
    then: <observable outcome>
  - id: S2
    when: <condition>
    then: <observable outcome>

tickets:
  - id: T1
    delivers: <the end-to-end behaviour>
    satisfies: [S1]
    paths: [src/feature/, tests/test_feature.py]   # an agent ticket's paths hold its test file or directory
    size: regular                   # small | regular
    difficulty: simple              # simple | complex
    blocked_by: []                  # optional
    risk: [state]                   # optional: security, concurrency, retry-idempotency, migration, external, state
  - id: T2
    delivers: <what a person runs or approves>
    satisfies: [S2]
    paths: [docs/runbook.md]
    owner: <person>                 # default agent; a person's ticket has no size or difficulty
    repo: ../other-repo             # only for a ticket outside this repository
```

## Rules the loader enforces

- IDs: scenarios `S<n>` with an optional letter (`S4a`), tickets `T<n>`, each unique; every reference names a declared ID; `blocked_by` has no cycle.
- `paths`: literal, repo-relative, no globs, no `..`, not absolute; a directory ends `/`. An agent ticket's `paths` hold a test file or directory.
- A discarding plan needs no `spec`.
- An agent ticket carries `size` and `difficulty`; `repo` is only for a person's ticket.
- A scenario is `id`, `when` and `then`, nothing else: the tests the implementing ticket writes are its evidence.
