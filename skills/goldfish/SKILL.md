---
name: goldfish
description: Zero-context comprehension check of one document. The user runs `/goldfish <doc>` after `/to-spec`, or on any plan or doc, to see whether a cold reader can follow it.
disable-model-invocation: true
---

# Goldfish

**Input:** a path to one document (`<doc>`).
**Output:** a comprehension report shown to the user: per-section paraphrases, undefined terms, ambiguous statements, Blockers.
**Hand-off:** the user fixes the doc, then reruns `/goldfish <doc>` until no Blocker remains. This skill never edits the doc.

A review in your own context is not a Goldfish review: you know too much. The reader must be a fresh subagent.

## Steps

1. Resolve `<doc>` to an absolute path. Stop and ask if it is missing or not a single file.
2. Spawn one fresh subagent (no fork, no inherited context) whose prompt is [`reader.md`](reader.md) plus the absolute path, with tools limited to file reading where the runtime allows (Claude: a subagent type without write/web tools if one exists, else general-purpose with the only-this-file rule as a prompt rule; Codex: the equivalent).
3. Show its report to the user verbatim, then a one-line count: sections, undefined terms, ambiguities, Blockers.
4. Stop. Do not fix the doc, answer the reader's questions from your own context, or rerun unprompted. Every `CANNOT PARAPHRASE` is a Blocker: the doc is not ready until the user clears it.

Done when the report is shown and the count line printed.

Method adapted from Google's Elephant-Goldfish Model; see [`NOTICE.md`](NOTICE.md).
