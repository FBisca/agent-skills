# Unslop packet

The task packet for the fresh-context prose review of the brief. Copy everything below the line, fill the placeholders, and dispatch it as the `task` of an agent-runtime `spawn` (see the skill's Delegation). The answer is the JSON object in the reviewer's report; a missing report, a missing key or anything other than that object fails the review, and the step skips the review.

---

## Task

Audit one plan's brief for AI writing patterns, report-only. Read these, in order:

1. `<unslop-dir>/SKILL.md`
2. `<unslop-dir>/references/core-contract.md`
3. the report-only part of `<unslop-dir>/references/commands/cleanup.md`

Use the `crisp` preset.

## Scope

- Audit `<plan-dir>/brief.md` only.
- Change nothing: no edit, no create, no delete. Do not touch `plan.yaml`.
- Leave every ID (S<n>, T<n>, D<n>), every path, every source link and the format of every D-line as written. Flag a span only for its prose.

## Return format

Report one JSON object and nothing else: no prose before it, no code fences.

{"findings": [{"section", "span", "category", "severity", "reason", "suggestion"}]}

- `section`: the brief heading the span sits under.
- `span`: the exact text of the span, quoted.
- `category`: the unslop category the span matches.
- `severity`: `low`, `medium` or `high`.
- `reason`: one line on why the span reads as slop.
- `suggestion`: the replacement text, which keeps the meaning and every ID, path and link.

An empty list is a valid answer: `{"findings": []}`.
