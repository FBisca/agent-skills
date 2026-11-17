# The contract: `plan/2`

The skeleton to write `<plans.dir>/YYYY-MM-DD-<slug>/plan.yaml` from. The engine's loader is strict: an unknown or duplicate key, a missing field or a wrong type is refused, and `plan check` names the field and the fix. Never write `approval`: `plan approve` writes it.

```yaml
schema: plan/2
slug: <slug>
goal: <one sentence, what is true for whom once the plan is built>
spec: docs/specs/<capability>.md    # the spec the archive applies the changes to; optional when the plan discards
archive: promote                    # promote | discard, optional: the repo config's archive.mode when absent

requirements:
  added:                            # titles the spec does not hold yet
    - title: <Requirement title>
      shall: <One sentence with SHALL.>
      scenarios:                    # 1 to 3
        - id: S1
          name: <spec heading>      # optional: the WHEN when absent
          when: <condition>
          then: <observable outcome>
  modified:                         # titles the spec holds, restated whole
    - title: <Existing requirement title>
      shall: <One sentence with SHALL.>
      scenarios:
        - id: S2
          when: <condition>
          then: <observable outcome>
  removed:                          # titles the spec holds
    - title: <Existing requirement title>
      why: <why it goes>

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

- `plan check` refuses an `added` title the spec already holds, and a `modified` or `removed` title it lacks. Titles match exactly.
- A requirement's `shall` holds the word SHALL; it has 1 to 3 scenarios. `added`, `modified` and `removed` each default to empty.
- IDs: scenarios `S<n>` with an optional letter (`S4a`), plan-local; tickets `T<n>`; each unique; every reference names a declared ID; `blocked_by` has no cycle.
- `paths`: literal, repo-relative, no globs, no `..`, not absolute; a directory ends `/`. An agent ticket's `paths` hold a test file or directory. They are a starting map and the conflict map between tickets, not a fence: a worker may edit any other file the change needs.
- A discarding plan needs no `spec`.
- An agent ticket carries `size` and `difficulty`; `repo` is only for a person's ticket.
- A scenario is `id`, `when`, `then` and an optional `name`: the tests the implementing ticket writes are its evidence. `then` states observable behaviour; a timing, size or count threshold appears only when that number is the product requirement.

On archive the engine applies the changes to the spec: it appends each added requirement, replaces each modified one whole and deletes each removed one.
