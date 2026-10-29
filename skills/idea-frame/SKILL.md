---
name: idea-frame
description: Grill one raw idea into a frame, an assumption map and a pre-mortem, then gate it. Felippe runs `/idea-frame <one-sentence idea>` before any PRD work.
disable-model-invocation: true
---

# Idea Frame

**Input:** one sentence describing the idea.
**Output:** the idea folder `~/developer/vault/01-projects/<slug>/` with the index note `<Title>.md`, `frame.md`, `assumptions.md`, `premortem.md`, `gates.md`, and an `idea-check --gate 1` result shown to Felippe.
**Hand-off:** on continue, `/to-spec` with the idea folder loaded, then optionally `/idea-answer <folder>` for the 3–5 items Felippe picks.

The folder contract (file formats, allowed values, check rules) is the docstring of `~/.claude/skills/idea-frame/scripts/idea_check.py`. Read it before writing any file; the gate fails on anything it does not allow. Vault rules apply: no client or investor names, no message bodies, no secrets.

**Owner guidance** (route by what the question is about):
- finance: business and finance rules, e.g. "what fee must this clear?"; ask the ops owner of that rule; record owner finance
- compliance: legal, security, data access, e.g. "may we store these documents outside the EU?"
- engineering: how the system behaves, e.g. "does the API return the sync date?"; never operators; goes to `/start-planning` Gather
- operator/user: how people react to or use it, e.g. "how do ops handle a failed transfer today?"
- decider: scope and priority, e.g. "is mobile in scope for v1?"
- product-behaviour rules (what the product does in a case): the person who owns that behaviour (operator/user if ops runs it, decider if it is a product call); don't default to decider

## Steps

1. **Folder.** Derive a short `<Title>` from the sentence and a kebab `<slug>` from the title. If the folder exists, stop and ask. Create the index note `<Title>.md` (the only root-level note with `type: project`) from `~/developer/vault/90-templates/project.md`, keeping its sections (Outcome, `## Now`, Tasks base embed, `## Notes`, `## Decisions`). Frontmatter: `type: project`, `status: idea`, `stage: framing`, `entry: raw`, `decider: <role>` (ask Felippe which role decides; a role, never a name), `area`, `created`, `updated`, `tags: []`. Outcome = the sentence. Add `## Hours`. Under `## Notes` list `[[frame]] [[assumptions]] [[premortem]] [[gates]]`. Every side note gets frontmatter `type: note`, `area`, `project: "[[<Title>]]"`, `created`, `updated`, `tags: []`.
2. **Grill.** Call the Skill tool with `grilling`, seeding the design tree with [`seeds.md`](seeds.md) (Heilmeier catechism and the internal FAQ on value, usability, feasibility, viability). Extra rules for this grilling:
   - Facts are your job: look them up read-only (fleet brain, code, vault) and record `Source: lookup <link>`. Never ask Felippe for what you can find.
   - Felippe may answer `unknown`. An `unknown` is recorded as `Source: unknown` and becomes an assumption to test; it is never forced into a decision.
   - Stop when the frontier is empty and Felippe confirms.
3. **Write the frame.** From the grilling:
   - `frame.md`: one `## Q<n> <question>` per question with its `Source:` line and the answer. `Q<n>` keeps counting across rounds; ids are unique. Every `Source: unknown` question gets an `Owner: <type>` line (a D10 type, chosen with the owner guidance above); `idea_check --gate 1` fails without it.
   - `assumptions.md`: the table `id | risk | assumption | importance | evidence | owner | test | result`. Every `Source: unknown` question is cited as `Q<n>` in the assumption cell of at least one row. importance and evidence are `high|med|low`; owner is one of `operator/user, finance, compliance, decider, engineering`; every high-importance assumption gets an owner and a test. Engineering questions are left for `/start-planning` Gather.
   - `premortem.md`: about 8 reasons the idea failed, each a bullet ending `→ PRD: <what the PRD must say>` or `→ A<n>`.
4. **Gate 1.** Set `stage: gate1` while the gate is decided. Log the framing time in the index note's `## Hours` (`- YYYY-MM-DD framing <n>h`, ask if unknown). Put the kill criteria to Felippe and wait for his call:
   - kill if there is no named person or role with the problem, no measurable success, or the cost is above his appetite;
   - otherwise continue only if the top 3 assumptions each have an owner type and a test.
   Append to `gates.md` (never overwrite) the line `- YYYY-MM-DD gate1: continue|kill|reshape: <reason>` and log the gate time as `- YYYY-MM-DD gate1 <n>h`. Then run and show the output of `python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 1`. Fix every FAIL (ask Felippe where the fix is a judgment) and rerun until none remain.
5. **Outcome.**
   - continue: set `stage: answering`; read `frame.md` and `assumptions.md` into the conversation, and tell Felippe to run `/to-spec`: its Further Notes must list every open assumption (`A<n>`, risk, owner type) as an open question. Then offer `/idea-answer <folder>` for the 3–5 items he picks.
   - kill: set `stage: killed`, `status: dropped`; after his yes, move the whole folder to `04-archive/`.
   - reshape: set `stage: reshaped`, then `stage: framing` while reframing in the same folder; keep the history and append to `gates.md`, never overwrite.
   Update `updated:` on every edit.

Done when `idea_check.py <folder> --gate 1` shows no FAIL and `gates.md` has the gate 1 line; on continue, name `/to-spec` with the idea folder loaded (Further Notes list each open assumption with its owner), then `/idea-answer <folder>` only for the 3–5 items he picks.
