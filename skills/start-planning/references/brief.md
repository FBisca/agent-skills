# The brief

A review document in two parts. **Above the rule** is what the user reads to approve: one screen or two, plain words, every line open to a comment. **Below the rule** is the Reference, for the worker who builds and for a reviewer who wants the proof.

Copy this template to `brief.md`. Replace each comment; a section with nothing to say holds `None.`

````markdown
---
status: in review
plan: plan.yaml
lane: <cell>
---
# <The feature, as the user would name it>

<!-- 3–4 sentences, no IDs: the problem, what changes and for whom, what it costs (tickets, repositories, people).
     A reader who stops here knows what a yes buys. -->

## Your calls
<!-- What needs the user's answer, before anything else. One checkbox per call:
     - a question the plan left open;
     - a decision the user has not seen: settled by a source or a run, or assumed without asking.
     Each: the question in bold, then "Default:" what the plan does, and its D<n>. The user ticks the box to accept
     the default or comments to change it; a box left empty keeps the default.
     A decision the user made in the grill is theirs already: it goes to the Decision log only. -->
- [ ] **<question>** Default: <what the plan does>. (D<n>)

## What changes
<!-- Grouped under ### headings by who notices: each user role, the model, the system's rules, rollout.
     One line per behaviour, what that reader now sees: **New:**, **Changed:** or **Removed:**, one fact,
     then its scenarios (S<n>, S<n>). **BREAKING** when a caller breaks. Paths and code names stay in Reference.
     Every scenario in plan.yaml appears, each ID written out, never a range. -->

## Walkthrough
<!-- One request traced start to finish through the change, on synthetic data, as numbered steps, each citing its S<n>.
     Then "What can go wrong": one line per refusal and edge case, with its S<n>. -->

## Out of scope
<!-- What a reader might expect and this plan leaves out, one line each, with the reason when it is not obvious. -->

## Risks
<!-- **<Risk in three words>:** what could go wrong, then what limits it.
     Security, privacy, observability, rollout, rollback: only the ones that apply. -->

---

# Reference

## Build order
<!-- One line per ticket, in merge order: T<n> what it delivers in plain words (size · difficulty, or its owner; after T<n>).
     Every ticket in plan.yaml appears. -->

## Decision log
<!-- Step 3, as each settles. Grouped under ### topic headings once there are more than eight.
     **D<n> <the choice, in a few words>.** Rejected: <the alternative>. Why: <one sentence>. Source: <who or where>. -->

## Code touched
<!-- The code areas and seams the gather named, and the plan's `spec` file: new or modified. -->

## Interfaces
<!-- Shapes the worker needs and a reviewer rarely does: file formats, tool inputs and outputs, flags. Tables fit here. -->
````

## Writing for the reviewer

- **Above the rule, prose and lists only.** A table or a callout cannot hold an inline comment; they belong in Reference.
- **One fact per line**, in the reader's words: "the bank's file", not `bank_import.py`. A code name appears above the rule only when the user would type it.
- **IDs trail the sentence**, in parentheses: the line reads whole without them.
- **Length:** above the rule fits 60 lines. Past that, move detail to Reference.

## Review

The user marks `brief.md` with CriticMarkup, in Obsidian or any editor: `{>> comment <<}`, `{== highlight ==}`, `{~~old~>new~~}`, `{++ insert ++}`, `{-- delete --}`, or ticks a box in Your calls. A comment on the contract cites its ID (`{>> S3: also the empty set <<}`); `plan.yaml` holds no marks, since `{` breaks its YAML.

List the marks with their lines:

```bash
grep -nE '\{(>>|==|~~|\+\+|--)' brief.md
```

Resolve each one (edit the brief; edit `plan.yaml` and rerun `plan check`; add a D-line; or answer it in the reply), then delete it. A call left empty keeps its default; a ticked or commented one moves to the Decision log as a D-line with source `user`. The round's reply holds one line per mark: the mark quoted, then what changed and where.

The review is done when the grep prints nothing. On approval, set `status: approved`.
