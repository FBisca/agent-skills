# Gather packet

The task packet for the fresh-context gatherer. Copy it, fill the placeholders, then run:

```
python3 <this skill>/scripts/fresh_context.py --packet <your copy> [--output <result.json>]
```

The gatherer runs the packet in its own Pi session: no parent conversation, no parent
session, a timeout, and a restricted tool set (`read`, `ls`, `grep`, `find`). It answers with
one JSON object; the script validates it and exits non-zero when the answer is missing,
malformed or timed out. Planning stops on that exit code — never continue on evidence the
gatherer did not produce.

## Request

<one paragraph: what the user asked for, in facts only. No credentials, no tokens, no
private content that is not needed for the decision.>

## Sources

Every source the gatherer may read, one per line: the request itself, the PRD, the Linear
project and issues, the vault project note and its decision notes, RFCs, the living spec of
the area.

- <link or repo-relative path> — <what it settles>

## Allowed paths

The repo-relative paths and directories the gatherer may read. Nothing else.

- <path or directory/>

## Questions

1. Which decisions do the sources settle, and which do they leave open or contradict?
2. Which existing code does the feature touch?
3. Which decisions depend on real data? For each: the count, and the edge cases (empty set,
   conflict, departed or archived owner).

## Rules for the gatherer

- Read only the allowed paths and the sources. Do not edit, create or delete anything.
- Report what the data shows, including empty results. Never guess a count.
- A decision that no source settles is `open`, with the source that would settle it.
- Answer with the JSON object only. No prose, no code fences.

## Return format

The gatherer appends this instruction to the packet; the shape it must answer with is:

```json
{"sources": [{"source": "<link or repo-relative path>", "settles": "<what it settles>"}],
 "decisions": [{"decision": "<what the source settles>", "source": "<source>", "status": "settled|open"}],
 "findings": ["<fact read from the code or a source>"],
 "counts": {"<population>": <integer>},
 "edge_cases": ["<empty set, conflict, departed or archived owner>"]}
```

`sources` must not be empty. `decisions`, `findings`, `counts` and `edge_cases` may be empty
when nothing was found; say so rather than inventing an entry.

## When the gatherer needs a live query

The default tool set cannot run commands. If the plan needs counts from a live database or
a script, either run the read-only query yourself in the parent, or re-run the gatherer with
`--allow-bash` and state in the packet that only read-only queries are allowed.
