# Gather packet

The task packet for the fresh-context gatherer. Copy it, fill the placeholders, then run it through the adapter (see [`delegation.md`](delegation.md) for the command and the failure codes).

The gatherer runs the packet in its own session: no parent conversation, no parent session, a timeout and a restricted tool set. It answers with one JSON object, which the adapter validates; the planning step stops when the adapter exits non-zero, so never continue on evidence the gatherer did not produce.

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

The adapter appends the return format to the packet and checks the answer against it; the
format is described in [`delegation.md`](delegation.md).
