---
name: idea-frame
description: Grill one raw idea into a frame, an assumption map and a pre-mortem, then gate it. The user runs `/idea-frame <one-sentence idea>` before any PRD work.
disable-model-invocation: true
---

# Idea Frame

**Input:** one sentence describing the idea.
**Output:** the idea folder `~/developer/vault/01-projects/<slug>/` with the index note `<Title>.md`, `frame.md`, `assumptions.md`, `premortem.md`, `gates.md`, and an `idea-check --gate 1` result shown to the user.
**Hand-off:** on continue, `/to-spec` with the idea folder loaded, then optionally `/idea-answer <folder>` for the 3–5 items the user picks; after `/to-spec` writes `PRD.md`, set `stage: prd`.

The folder contract (file formats, allowed values, check rules) is the docstring of `~/.claude/skills/idea-frame/scripts/idea_check.py`. Read it before writing any file; the gate fails on anything it does not allow. Vault rules apply: no client or investor names, no message bodies, no secrets.

**Owner guidance** (route by what the question is about):
- finance: business and finance rules, e.g. "what fee must this clear?"; ask the ops owner of that rule; record owner finance
- compliance: legal, security, data access, e.g. "may we store these documents outside the EU?"
- engineering: how the system behaves, e.g. "does the API return the sync date?"; never operators; goes to `/start-planning` Gather
- operator/user: how people react to or use it, e.g. "how do ops handle a failed transfer today?"
- decider: scope and priority, e.g. "is mobile in scope for v1?"
- ethical risk (could it harm someone, would users object if they knew): compliance, or the decider when it is a product call
- product-behaviour rules (what the product does in a case): the person who owns that behaviour (operator/user if ops runs it, decider if it is a product call); don't default to decider

## Steps

1. **Folder.** Derive a short `<Title>` from the sentence and a kebab `<slug>` from the title. If the folder exists, stop and ask. Create the index note `<Title>.md` (the only root-level note with `type: project`) from `~/developer/vault/90-templates/project.md`, keeping its sections (Outcome, `## Now`, Tasks base embed, `## Notes`, `## Decisions`). Frontmatter: `type: project`, `status: idea`, `stage: framing`, `entry: raw`, `decider: <role>` (ask the user which role decides; a role, never a name), `area`, `created`, `updated`, `tags: []`. Outcome = the sentence. Add `## Hours`. Under `## Notes` list `[[frame]] [[assumptions]] [[premortem]] [[gates]]`. Every side note gets frontmatter `type: note`, `area`, `project: "[[<Title>]]"`, `created`, `updated`, `tags: []`.
2. **Grill.** Call the Skill tool with `grilling`, seeding the design tree with [`seeds.md`](seeds.md) (Heilmeier catechism and the internal FAQ on value, usability, feasibility, viability, ethical), then run its story-map pass (actors × steps, "what must be true here?"). Extra rules for this grilling:
   - Facts are your job: look them up read-only (fleet brain, code, vault) and record `Source: lookup <link>`. Never ask the user for what you can find.
   - The user may answer `unknown`. An `unknown` is recorded as `Source: unknown` and becomes an assumption to test; it is never forced into a decision.
   - An answer the user gives from belief (not a lookup) gets evidence low.
   - Stop when the frontier is empty and the user confirms.
3. **Write the frame.** From the grilling:
   - `frame.md` opens with `## Terms`: a table `term | meaning | link`, one row per project-specific term, a one-line meaning, and an optional link (`[[note]]`, `~/path[:line]` or `https://`), per the `idea_check.py` docstring.
   - `frame.md`: one `## Q<n> <question>` per question with its `Source:` line and the answer. `Q<n>` keeps counting across rounds; ids are unique. Every `Source: unknown` question gets an `Owner: <type>` line (a D10 type, chosen with the owner guidance above); `idea_check --gate 1` fails without it.
   - `assumptions.md`: the table `id | risk | assumption | importance | evidence | owner | test | result`. Every `Source: unknown` question is cited as `Q<n>` in the assumption cell of at least one row. importance and evidence are `high|med|low` (level definitions in the `idea_check.py` docstring); every non-lookup story-map answer is a row; owner is one of `operator/user, finance, compliance, decider, engineering`; every high-importance assumption gets an owner and a test written as `<type>: <success criterion>`, type one of interview, prototype, data, survey, spike, criterion set before the test runs (e.g. `interview: 3 of 5 ops leads describe the manual workaround`). Engineering questions are left for `/start-planning` Gather.
   - `premortem.md`: about 8 reasons the idea failed, each a bullet ending `→ PRD: <what the PRD must say>` or `→ A<n>`.
4. **Gate 1.** Show the map sorted by importance high→low, then evidence low→high (leap-of-faith first); the user reorders the rows; the agreed order is the row order in `assumptions.md`. Set `stage: gate1` while the gate is decided. Log the framing time in the index note's `## Hours` (`- YYYY-MM-DD framing <n>h`, ask if unknown). Put the kill criteria to the user and wait for their call:
   - kill if there is no named person or role with the problem, no measurable success, or the cost is above their appetite;
   - otherwise continue only if the top 3 assumptions are the first 3 rows and each have an owner type and a test.
   Append to `gates.md` (never overwrite) the line `- YYYY-MM-DD gate1: continue|kill|reshape: <reason>` and log the gate time as `- YYYY-MM-DD gate1 <n>h`. Run and show the output of `python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 1`; fix every FAIL except `frame-language` (ask the user where the fix is a judgment) and rerun. The reader runs last: spawn a fresh subagent (no fork, no inherited context, read-only tools) with [`reader.md`](reader.md) and the absolute `frame.md` path; on `blocked`, fix each item (look up meanings yourself, ask the user only for judgment) and rerun the reader, after the 2nd blocked round show the items to the user, who answers each one or turns it into a new `## Q<n>` with `Source: unknown`, an `Owner:` line and an assumption row citing it (the assumption row follows step 3: evidence low; a high-importance row needs a `<type>: <criterion>` test); a converted item's quoted text gets a pointer `(… open, Q<n>)`, and a `term` item also gets a Terms row `<term> | unknown, see Q<n> |`; then rerun the reader; the 3rd blocked round is the last: turn all its items into such open questions (owner chosen with the owner guidance), show the added rows to the user, and the user appends `- YYYY-MM-DD language: accepted <sha12> by <role>` (no reader rerun); on `pass`, append `- YYYY-MM-DD language: pass <sha12>` to `gates.md` with the sha12 that idea_check prints for `frame-language`, then rerun idea_check until no FAIL remains. Any later edit to the `frame.md` body needs a fresh reader pass before a new language line; never copy a sha without one (the user's `accepted` line aside).
5. **Outcome.**
   - continue: set `stage: answering`; read `frame.md` and `assumptions.md` into the conversation, and tell the user to run `/to-spec`: its Further Notes must list every open assumption (`A<n>`, risk, owner type) as an open question. Then offer `/idea-answer <folder>` for the 3–5 items they pick.
   - kill: set `stage: killed`, `status: dropped`; after the user's yes, move the whole folder to `04-archive/`.
   - reshape: set `stage: reshaped`, then `stage: framing` while reframing in the same folder; keep the history and append to `gates.md`, never overwrite.
   Update `updated:` on every edit.

Done when `idea_check.py <folder> --gate 1` shows no FAIL and `gates.md` has the gate 1 line; on continue, name `/to-spec` with the idea folder loaded (Further Notes list each open assumption with its owner), then `/idea-answer <folder>` only for the 3–5 items they pick.
