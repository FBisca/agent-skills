# The brief: `brief.md`

The human-readable design doc the user reads, comments on and updates before approval. The contract is `plan.yaml`; the brief cites its IDs and never copies its text.

## Outline

Every heading appears in every brief, in this order. A section with nothing to say holds `None.`

```markdown
# Brief: <feature>
Slug: `<slug>`. Contract: `plan.yaml`. Lane: Plan, <its cell and why>.
## Why
## What Changes
## Capabilities
## Impact
## Context
## Goals / Non-Goals
## Decisions
## Risks / Trade-offs
## Open Questions
```

Who writes each section:

- **Decisions**: step 3, one D-line per decision as it settles.
- **Everything else**, the header included: step 7.

Section rules:

- **Why**: 1–2 sentences, the problem and why now.
- **What Changes**: one line per behaviour, `<path or area>`: before → after (S<n>, T<n>). Cite the scenario it makes observable and the ticket that delivers it. Write each line as the change itself, the way a commit message would. Prefix **BREAKING** when a caller breaks.
- **Capabilities**: one line, the plan's `spec` file, new or modified.
- **Impact**: the code areas and seams the gather named.
- **Context**: what the reader needs to judge the rest.
- **Goals / Non-Goals**: what the plan delivers; what it deliberately leaves out.
- **Decisions**: the D-lines.
- **Risks / Trade-offs**: each risk with its mitigation. Cover security, privacy, observability, rollout and rollback.
- **Open Questions**: what the plan assumed without asking.

## Review round

The user marks brief.md with CriticMarkup:

- `{>> comment <<}` a comment
- `{== span ==}` a highlighted span
- `{~~old~>new~~}` a suggested replacement
- `{++ text ++}` an insertion
- `{-- text --}` a deletion

A comment on the contract cites the ID it concerns, for example `{>> S3: should also cover the empty set <<}`.

For each mark, do one of:

- edit brief.md
- edit `plan.yaml`, then run `plan check` until it exits 0
- record a D-line in Decisions
- answer the question in the reply

Then delete the mark. `plan.yaml` never holds a mark: CriticMarkup's `{` breaks its YAML. After an approval, a contract edit also needs a new `plan approve --reason`.

The round is done when this prints nothing:

```bash
grep -nE '\{(>>|==|~~|\+\+|--)' brief.md
```

Run it before `plan approve`.
