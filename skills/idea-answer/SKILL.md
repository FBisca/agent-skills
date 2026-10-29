---
name: idea-answer
description: Route an idea's open questions to the people who can answer them, record the answers, and run gate 2. Felippe runs `/idea-answer <idea folder>` after `/idea-frame` passed gate 1, or with a decided feature and its sources.
disable-model-invocation: true
---

# Idea answer

**Input:** an idea folder (`V/01-projects/<slug>/`, stage `gate1` or `answering`), or a decided feature with sources and no folder yet.
**Output:** `answers.md` entries, updated assumption results, a `gate2` line in `gates.md`, hours logged, and an `idea_check --gate 2` report shown to Felippe.
**Hand-off:** gate 2 passed means `/to-spec` (writes `PRD.md` in the folder through the vault tracker setup), then `/goldfish <folder>/PRD.md`. Kill or reshape ends here with the reason in `gates.md`.

Agents asked the late questions in the backtest and nobody answered: operators, finance, compliance and leadership did. This skill gets Felippe to those people with the right questions. It never sends anything.

**Owner guidance** (route by what the question is about):
- finance: business and finance rules, e.g. "what fee must this clear?"; ask the ops owner of that rule; record owner finance
- compliance: legal, security, data access, e.g. "may we store these documents outside the EU?"
- engineering: how the system behaves, e.g. "does the API return the sync date?"; never operators; goes to `/start-planning` Gather
- operator/user: how people react to or use it, e.g. "how do ops handle a failed transfer today?"
- decider: scope and priority, e.g. "is mobile in scope for v1?"
- product-behaviour rules (what the product does in a case): the person who owns that behaviour (operator/user if ops runs it, decider if it is a product call); don't default to decider

## Steps

1. **Open the folder.** Read the index note (`<Title>.md`, the one root-level note with `type: project`), `frame.md`, `assumptions.md`, `premortem.md`, `answers.md`, `gates.md` (the contract is the module docstring of `idea-frame/scripts/idea_check.py`). Set `stage: answering`.
   - **Decided feature, no folder:** create `V/01-projects/<slug>/` with the index note built from `~/developer/vault/90-templates/project.md` (`<Title>.md`, titled like the idea; frontmatter `type: project`, `status: idea`, `stage: answering`, `entry: decided`, `decider: <role>`) listing `[[assumptions]] [[answers]] [[gates]]` under `## Notes`, and `assumptions.md` from the sources (each unconfirmed claim: risk, importance, evidence, owner type, test). Open questions without an answer are rows too. Side notes carry frontmatter `type: note`, `area`, `project: "[[<Title>]]"`, `created`, `updated`, `tags: []`. Skip frame and pre-mortem; gate 2 skips their checks for `entry: decided`.
2. **List open items:** every `Source: unknown` frame question, every high-importance assumption with an empty result, every open product question. Rank by importance (high first, then by what would kill the idea).
3. **Pick, then route.** Show the open items ranked by importance and ask Felippe which 3–5 to take to people. Route and prepare only those: one owner type each (operator/user, finance, compliance, decider, engineering), set on the assumption row using the owner guidance above. The rest stay in `assumptions.md` untouched.
   - If gate 2 is run, each unpicked high-importance item gets the result `accepted by <decider role>: low priority, not asked`, confirmed by the decider at gate 2 like engineering items.
   - `idea_check --gate 2` fails `people-cap` above 12 people items; the pick stays well below it.
   - Engineering items are not for people: record them as handed to `/start-planning` Gather. Result: `accepted by <decider role>: engineering, to /start-planning Gather`; the decider confirms it at gate 2. They leave this loop.
4. **Prepare each conversation** for Felippe, one item at a time, from [`prep.md`](prep.md): who (role), 2-4 Mom Test questions, and the answer that kills or changes the idea. Usability items: suggest a `/prototype` session instead of asking.
   - Outreach (mail, Slack, Teams) is drafted only after Felippe's yes for that item, in his voice, and he sends it. This skill never sends and holds no outbound tool.
5. **Record each answer** when Felippe reports it: an `## ` entry in `answers.md` with Felippe's summary and the lines `Owner: <type> (<role>)` (the type first, so the cap counts it), `Date: YYYY-MM-DD`, `Link: <link>`, `Summary:` (one each). Write no message bodies, no client or investor names (vault rules); the link points to where the source lives. When this creates `answers.md` in an existing folder, add `[[answers]]` to the index note's `## Notes`. Then set the assumption's result: `confirmed`, `killed`, or `accepted by <role>`. idea-check only needs a non-empty result.
   - An answer that kills or reshapes the idea stops the loop: take it to step 6.
6. **Gate 2 with the decider** (D9): every high-importance assumption tested or accepted by the decider, every open question answered or moved to PRD Open Questions with an owner, except items not picked (no entry; the decider confirms their result). A question moved to PRD Open Questions gets its own `answers.md` entry (`Owner: <type> (<role>)`, `Date:`, `Link:`, `Summary: open → PRD Open Questions`) so `/to-spec` picks it up. Ask the decider's call; write one line in `gates.md`: `- <date> gate2: pass by <role>: <reason>` (or `kill: <reason>` / `reshape: <reason>`). Log the hours under `## Hours` in the index note as `- <date> answering <n>h`; set `stage: gate2` on pass, `killed` or `reshaped` otherwise.
7. **Run the gate** and show the output verbatim:

   ```
   python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 2
   ```

   Fix every FAIL (usually a missing Link, empty result, or decider mismatch), rerun until none. Never edit the check or the decider to pass.
8. **Hand off** by naming `/to-spec`, then `/goldfish <folder>/PRD.md`. Do not run either.

Done when `idea_check --gate 2` prints no FAIL and the next command is named, or the idea is killed or reshaped with the reason recorded.

## Rules

- Questions in Mom Test form: past behaviour and specifics; never pitch the idea; never hypotheticals.
- Decisions come from the decider or a source. Never fill `answers.md` or a result from your own inference.
- Only Felippe's yes unlocks a draft; only Felippe sends.
