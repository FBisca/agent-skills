# The brief

Copy this template to `brief.md`. Replace each comment; a section with nothing to say holds `None.`

````markdown
# Brief: <feature>
Slug: `<slug>`. Contract: `plan.yaml`. Lane: Plan, <cell>: <why>.

## Why
<!-- 1–2 sentences: the problem, and why now. -->

## What Changes
<!-- Grouped under ### headings by who notices the change: each user role, the model, the system's rules, rollout.
     One line per behaviour, plain words first: **New:**, **Changed:** or **Removed:**, what that reader now sees,
     then (S<n>, S<n> · T<n> · <path or area>). **BREAKING** when a caller breaks.
     Every scenario and ticket in plan.yaml appears, each ID written out, never a range. -->

## Capabilities
<!-- The plan's `spec` file: new or modified. -->

## Impact
<!-- The code areas and seams the gather named. -->

## Context
<!-- What the reader needs to judge the rest. -->

## Example
<!-- One request traced start to finish through the change, on synthetic data, each step citing its S<n>.
     Then one line per variant: each refusal and edge case, with its S<n>. -->

## Goals / Non-Goals
<!-- What this delivers; what it deliberately leaves out. -->

## Decisions
<!-- Step 3, as each settles: D<n> <choice>, over <rejected>: <why> (<source>). -->

## Risks / Trade-offs
<!-- Each risk and its mitigation: security, privacy, observability, rollout, rollback. -->

## Open Questions
<!-- What the plan assumed without asking. -->
````

## Review

The user marks `brief.md` with CriticMarkup: `{>> comment <<}`, `{== highlight ==}`, `{~~old~>new~~}`, `{++ insert ++}`, `{-- delete --}`. A comment on the contract cites its ID (`{>> S3: also the empty set <<}`); `plan.yaml` holds no marks, since `{` breaks its YAML.

Resolve each mark (edit the brief; edit `plan.yaml` and rerun `plan check`; add a D-line; or answer it in the reply), then delete it. The review is done when this prints nothing:

```bash
grep -nE '\{(>>|==|~~|\+\+|--)' brief.md
```
