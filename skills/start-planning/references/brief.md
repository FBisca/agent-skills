# The brief: `brief.md`

The design doc the user reads, comments on and updates before approval.

## Outline

Every heading appears in every brief, in this order. A section with nothing to say holds `None.`

```markdown
# Brief: <feature>
Slug: `<slug>`. Contract: `plan.yaml`. Lane: Plan, <its cell and why>.
## Why
## What Changes
## Capabilities
## Impact
## Requirements
## Context
## Goals / Non-Goals
## Decisions
## Risks / Trade-offs
## Open Questions
## Tickets
```

Who writes each section:

- **Decisions**: step 3, one D-line per decision as it settles.
- **Everything else**, the header included: step 7.

Section rules:

- **Why**: 1–2 sentences, the problem and why now.
- **What Changes**: one line per behaviour, `<path or area>`: before → after (T<n>). Write each line as the change itself, the way a commit message would. Prefix **BREAKING** when a caller breaks.
- **Capabilities**: one line, the plan's `spec` file, new or modified.
- **Impact**: the code areas and seams the gather named.
- **Requirements**: copied from `plan.yaml`, see Copied sections.
- **Context**: what the reader needs to judge the rest.
- **Goals / Non-Goals**: what the plan delivers; what it deliberately leaves out.
- **Decisions**: the D-lines.
- **Risks / Trade-offs**: each risk with its mitigation. Cover security, privacy, observability, rollout and rollback.
- **Open Questions**: what the plan assumed without asking.
- **Tickets**: copied from `plan.yaml`, see Copied sections.

## Copied sections

Copy both sections after `plan check` exits 0, in this form.

- **Requirements**: each requirement as `### <title> (added)`, `(modified)` or `(removed)`, then its SHALL sentence and each scenario as `S<n>` WHEN … THEN …. A removed requirement has no SHALL sentence: give its `why` instead.
- **Tickets**: one line each: `T<n> · delivers · satisfies · size/difficulty (or owner) · blocked_by · risk`. Write `none` for an empty field.

Every edit to `plan.yaml` re-copies both sections in the same edit. The brief then always matches the contract, which `plan approve` does not check.

## Review round

The user marks brief.md with CriticMarkup:

- `{>> comment <<}` a comment
- `{== span ==}` a highlighted span
- `{~~old~>new~~}` a suggested replacement
- `{++ text ++}` an insertion
- `{-- text --}` a deletion

For each mark, do one of:

- edit brief.md or `plan.yaml`
- record a D-line in Decisions
- answer the question in the reply

Then delete the mark. A `plan.yaml` edit runs `plan check` and re-copies Copied sections. After an approval, it also needs a new `plan approve --reason`.

The round is done when this prints nothing:

```bash
grep -nE '\{(>>|==|~~|\+\+|--)' brief.md
```

Run it before `plan approve`.
