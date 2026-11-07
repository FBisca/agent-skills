# Delegating the gather and the grill

`start-planning` needs two things from its harness: a fresh-context gatherer and the `grilling` skill. The skill states the requirement; this file is the per-harness detail, read only when the step is about to run.

## What a delegation must guarantee

- **No inherited context.** The gatherer starts with no conversation from this session and no fork of it.
- **Bounded.** It runs under a timeout and stops when it exceeds it.
- **Limited actions.** It reads; it does not change the repository.
- **Structured result.** It returns the Sources table, the decisions with their sources, the findings, the counts and the edge cases.
- **Loud failure.** A timeout, a crash or a malformed answer fails the step: the plan stops instead of continuing on evidence the gatherer did not produce.

## Which mechanism to use

| Harness | Gather | Grill |
|---|---|---|
| Claude Code | a Task subagent, no fork of this session | the Skill tool with `grilling` |
| Codex | its subagent run, no inherited context | the `grilling` skill |
| A harness with no subagent tool | the adapter below | the `grilling` skill |

## The adapter for a harness with no subagent

Pi has no subagent tool of its own, so this skill ships one: `scripts/fresh_context.py`. It runs the packet in a separate `pi` session — a new session directory, no parent conversation, read-only tools, a timeout, a scrubbed environment — and validates the answer against a strict schema.

Pi does ship a subagent extension, but as an example: it must be installed by hand (the extension plus its agent definitions) before any skill can call it, and it spawns the same kind of separate `pi` process. A skill has to work for someone who installed Pi and nothing else, so the adapter travels with the skill. When the harness offers its own delegation, use it — the guarantees above are what matter, not the mechanism.

### Running it

```
python3 <this skill>/scripts/fresh_context.py --packet <packet.md> [--timeout 600] [--output <result.json>] [--model <id>]
```

The packet template is [`gather-packet.md`](gather-packet.md). The script appends the return format to the packet and validates the answer against it: `sources`, `decisions`, `findings`, `counts` and `edge_cases`, and nothing else. The five keys are required and no others are; a source or a decision may carry extra annotations, and a count written in digits is read as the number it is.

The gatherer reads by default. When a plan needs live counts, run the read-only query yourself or re-run the gatherer with `--allow-bash` and say in the packet that only read-only queries are allowed.

### When it fails

| Exit | Meaning |
|---|---|
| 2 | the packet is missing or unusable |
| 3 | `pi` is not installed |
| 4 | the `pi` session failed |
| 5 | the session timed out |
| 6 | the answer was not a valid result |
| 7 | the packet carried a credential |

Every one of them stops the plan. Report the reason; do not gather in this session instead.

## The `grilling` dependency

`grilling` is an upstream skill (see `skills.lock.json`), not vendored here. Check it before the grill:

```
python3 <this skill>/scripts/check_deps.py grilling
```

It prints `FOUND grilling: <path>` when the skill is installed and exits non-zero with the install command when it is not:

```
scripts/install-upstream.sh grilling
```

A missing `grilling` stops the plan. Never skip the grill and never answer its questions yourself.
