# One engine: the skill delegates to the member

Paths: skills/orchestrate/, README.md, AGENTS.md

The engine — the plan parser, the dispatcher, the gates, the ledger — lives in `agent-runtime`, in the
`agent-orchestrator` member. This repository used to carry a copy of it under `skills/orchestrate/scripts/`,
and the two drifted. The copy is gone: the skill's script is a shim that resolves the member's CLI and
hands it the command.

This file states what this repository guarantees about that seam. What the engine itself guarantees is
`agent-runtime`'s `docs/specs/orchestrator-engine.md`; the scenarios below are this repository's own.

## Coverage

| Scenario | Requirement | Test |
|---|---|---|
| S1 | The skill drives the member | `skills/orchestrate/tests/test_engine_home.py`: `test_S1_the_skill_tree_carries_no_copy_of_the_engine` |
| S2 | A missing member refuses with the way out | `skills/orchestrate/tests/test_delegation.py`: `test_S2_without_a_member_the_skill_refuses_and_names_the_way_out` |
| S3 | Engine internals are tested where the engine lives | `skills/orchestrate/tests/test_engine_home.py`: `test_S3_the_engine_internals_are_tested_where_the_engine_lives` |
| S4 | The member answers like the copy it replaced | `skills/orchestrate/tests/test_delegation.py`: `test_S4_the_member_answers_with_the_same_commands_and_exit_codes` |
| S5 | The documents name the seam | `skills/orchestrate/tests/test_delegation.py`: `test_S5_the_documents_name_the_seam_the_order_and_the_way_out` |

## The seam

| Question | Answer |
|---|---|
| Where is the engine? | `agent-runtime`, in the `agent-orchestrator` member (`packages/agent-orchestrator/`). |
| What does this repository keep? | The skill: its frontmatter, its workflow, and a script that delegates. |
| How is the member resolved? | `$AGENT_RUNTIME_HOME` first, then `agent-orchestrator` on `PATH`. |
| What if neither answers? | The skill refuses with the way out and exits 2. It never runs a second engine. |

`AGENT_RUNTIME_HOME` keeps the meaning the README gives it: the checkout of `agent-runtime`. It now names
the checkout that holds the engine as well as the one that holds the runtime, and it wins over `PATH`, so a
checkout the user named is never shadowed by an older install.

## The plans that described the engine

`code-driven-orchestrator` and `orchestrate-lean-loop` built the engine this repository used to carry. Their
implemented scenarios are archived in `agent-runtime`'s `docs/specs/orchestrator-engine.md`, next to the tests
that answer them. The tickets they still hold open are the engine's backlog, and they belong to the member's
repository.

## Requirements

### Requirement: The skill drives the member
The orchestrate skill SHALL drive the member, and its tree SHALL carry no copy of the engine.

#### Scenario: the orchestrate skill runs
- WHEN the orchestrate skill runs
- THEN it drives the member, and the skill's tree carries no copy of the engine

### Requirement: A missing member refuses with the way out
When the member is not installed, the skill SHALL refuse with an actionable message naming the install command and the `AGENT_RUNTIME_HOME` escape hatch, and SHALL never fall back to a second engine.

#### Scenario: the member is not installed
- WHEN the member is not installed
- THEN the skill refuses with an actionable message naming the install command and the `AGENT_RUNTIME_HOME` escape hatch, and it never falls back to a second engine

### Requirement: Engine internals are tested where the engine lives
The skill's suite SHALL hold the skill's own behaviour, and the engine's internals SHALL be tested where the engine lives.

#### Scenario: the skill's suite runs
- WHEN the skill's suite runs
- THEN it holds the skill's own behaviour, and the engine's internals are tested where the engine lives

### Requirement: The member answers like the copy it replaced
The member's CLI SHALL answer the delegation with the same commands, exit codes and ledger as the copy it replaces.

#### Scenario: the delegation is exercised
- WHEN the delegation is exercised
- THEN the member's CLI answers with the same commands, exit codes and ledger as the copy it replaces

### Requirement: The documents name the seam
The skill's documents SHALL name the seam, the resolution order and the way out, and `AGENT_RUNTIME_HOME` SHALL keep its documented meaning.

#### Scenario: the skill's documents are read
- WHEN the skill's documents are read
- THEN the seam, the resolution order and the way out are named, and `AGENT_RUNTIME_HOME` keeps its documented meaning
