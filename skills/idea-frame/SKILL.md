---
name: idea-frame
description: Grill one raw idea into a frame and a map of the questions that change the build, then gate it. The user runs `/idea-frame <one-sentence idea>` before any PRD work.
disable-model-invocation: true
---

# Idea Frame

**Input:** one sentence describing the idea.
**Output:** the idea folder `~/developer/vault/01-projects/<slug>/` with the index note `<Title>.md`, `frame.md`, `assumptions.md`, and an `idea_check --gate 1` result shown to the user.
**Hand-off:** on continue, `/idea-answer <folder>` for every open row (not optional); it writes the Brief; `/to-spec` then writes the PRD.

The folder contract (file formats, allowed values, check rules) is the docstring of `~/.claude/skills/idea-frame/scripts/idea_check.py`. Read it before writing any file; the gate fails on anything it does not allow. Vault rules apply: no client or investor names, no message bodies, no secrets.

## Steps

1. **Folder.** Derive a short `<Title>` from the sentence and a kebab `<slug>` from the title. If the folder exists, stop and ask. Create the index note `<Title>.md` (the only root-level note with `type: project`) from `~/developer/vault/90-templates/project.md`, keeping its sections (Outcome, `## Now`, Tasks base embed, `## Notes`, `## Decisions`). Frontmatter: `type: project`, `status: idea`, `stage: framing`, `entry: raw`, `decider: <role>` (ask the user which role decides; a role, never a name), `area`, `created`, `updated`, `tags: []`. Outcome = the sentence. Add `## Hours` and `## Gates`. Under `## Notes` list `[[frame]] [[assumptions]]`. Each side note gets frontmatter `type: note`, `area`, `project: "[[<Title>]]"`, `created`, `updated`, `tags: []`.
2. **Grill.** Call the Skill tool with `grilling`, seeding the design tree with [`seeds.md`](seeds.md) (Heilmeier catechism and the internal FAQ). Extra rules for this grilling:
   - Facts are your job: look them up read-only (fleet brain, code, vault) and record `Source: lookup <link>`. Never ask the user for what you can find.
   - The user may answer `unknown`. An `unknown` is recorded as `Source: unknown` and becomes a row in the map; it is never forced into a decision.
   - Never ask for roadmap end dates or a dated step sequence: they come after the PRD, once the product and outcomes are clear. Record a success horizon the user volunteers as given.
   - Stop when the frontier is empty and the user confirms.
3. **Write the frame.** From the grilling:
   - `frame.md`: grilling notes, one `## Q<n> <question>` per question with its `Source:` line (`me`, `lookup <link>` or `unknown`) and the answer. No check reads it.
   - `assumptions.md`: the map, one row per question whose answer would change the build (every `unknown`, every belief that is not a lookup), header `id | assumption | if wrong | owner | source | test | result`. Ids `A<n>`. `if wrong` is the consequence. owner is a free-text role who can answer (finance, compliance, operator, decider, engineering). `source` is the `Q<n>` or lookup. `test` only for a real experiment, written `<type>: <criterion>` (e.g. `interview: 3 of 5 ops leads describe the manual workaround`); otherwise empty. `result` stays empty. Order the rows by what changes the build most; no fixed count.
4. **Gate 1.** Set `stage: gate1`. Put the kill criteria to the user and wait for their call:
   - kill if there is no named person or role with the problem, no observable success, or the cost is above their appetite;
   - otherwise continue only if every row has an owner.
   Who decides: proposer alone below appetite, the decider above. Append to `## Gates` in the index note (never overwrite) `- YYYY-MM-DD gate1: continue|kill|reshape: <reason>`. Log the framing time under `## Hours` (`- YYYY-MM-DD framing <n>h`, one total is enough; ask if unknown). Run and show the output of `python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 1`; fix every FAIL and rerun.
5. **Outcome.**
   - continue: set `stage: answering`, name `/idea-answer <folder>`; every open row goes through it, none is skipped.
   - kill: set `stage: killed`, `status: dropped`; after the user's yes, move the whole folder to `04-archive/`.
   - reshape: set `stage: reshaped`, then `stage: framing` while reframing in the same folder; keep the history.
   Update `updated:` on every edit.

Done when `idea_check.py <folder> --gate 1` shows no FAIL and `## Gates` has the gate 1 line; on continue, name `/idea-answer <folder>` for every open row.
