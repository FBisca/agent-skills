# Gather packet

The task packet for the fresh-context gatherer. Copy everything below the line, fill the placeholders, and dispatch it as the `task` of an agent-runtime `spawn` (see the skill's fresh agent). The answer is the JSON object in the gatherer's report; a missing report, a missing key or anything other than that object fails the gather, and the plan stops.

---

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
2. Which existing code does the feature touch, and where are its seams: the CLI, HTTP, tool and
   public entry points, and the test fixtures a test can drive it from?
3. Which decisions depend on real data? For each: the count, and the edge cases (empty set,
   conflict, departed or archived owner).

## Rules for the gatherer

- Read only the allowed paths and the sources. Change nothing: no edit, no create, no delete.
  Run only read-only queries.
- Report what the data shows, including empty results. Never guess a count.
- A decision that no source settles is `open`, with the source that would settle it.

## Return format

Report one JSON object and nothing else: no prose before it, no code fences.

{"sources": [{"source": "<link or repo-relative path>", "settles": "<what it settles>"}],
 "decisions": [{"decision": "<what the source settles>", "source": "<source>", "status": "settled|open"}],
 "findings": ["<fact read from the code or a source, seams included>"],
 "counts": {"<population>": <integer>},
 "edge_cases": ["<empty set, conflict, departed or archived owner>"]}

All five keys, no others. `sources` lists every source you read, with what it settles.
`decisions` lists the decisions the sources settle (status `settled`) and the ones they leave
open (status `open`). `counts` and `edge_cases` carry what the data shows: `{}` and `[]` when
there is no data to count.
