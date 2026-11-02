---
name: idea-answer
description: Route every open question of an idea to the people who can answer it, record the answers, keep the Brief current and commit. The user runs `/idea-answer <idea folder>` after `/idea-frame` passed gate 1, or with a decided feature and its sources.
disable-model-invocation: true
---

# Idea answer

**Input:** an idea folder (`~/developer/vault/01-projects/<slug>/`, stage `gate1` or `answering`), or a decided feature with sources and no folder yet.
**Output:** `answers.md` entries, closed rows in `assumptions.md`, `Brief.md`, the cold-read and `gate2` lines in the index note's `## Gates`, hours logged, and an `idea_check --gate 2` report shown to the user.
**Hand-off:** gate 2 passed means `/to-spec`, writing the PRD from the final Brief and the answers. Kill or reshape ends here with the reason in `## Gates`.

The folder contract is the docstring of `~/.claude/skills/idea-frame/scripts/idea_check.py`; read it before writing any file. This skill never sends anything.

**Owner guidance** (who can answer, by what the row is about): finance and compliance for money, legal, security and data rules (ask the owner of that rule); operator/user for how people work or react; decider for scope and priority, and for product-behaviour rules that are a product call; engineering for how the system behaves (read-only lookup in code, no one is asked).

## Steps

1. **Open the folder.** Read the index note (`<Title>.md`, the one root-level note with `type: project`), `frame.md`, `assumptions.md`, `answers.md` and `Brief.md` if present. Set `stage: answering`.
   - **Decided feature, no folder:** create `~/developer/vault/01-projects/<slug>/` with the index note built from `~/developer/vault/90-templates/project.md` (`<Title>.md`; frontmatter `type: project`, `status: idea`, `stage: answering`, `entry: decided`, `decider: <role>`; sections `## Hours` and `## Gates`) and `assumptions.md` from the sources, at least one row, one per claim or open question (header per the docstring); claims the sources already confirm get result `confirmed`. There is no `frame.md`: generate the Brief from the sources. Side notes carry frontmatter `type: note`, `area`, `project: "[[<Title>]]"`, `created`, `updated`, `tags: []`; list them under `## Notes`.
2. **List the open rows:** every row with an empty result. Route every open row: no pick, no cap. Ask the user who owns each if the owner cell is vague.
3. **Prepare each conversation** from [`prep.md`](prep.md), one row at a time: Mom Test only for how users behave; a policy or rule owner is asked for the current rule. The user holds the conversation, or teammates may ask the owner; the user collects what they report. Usability rows: suggest `/prototype` instead of asking. Engineering rows: look up in code, read-only.
   - Outreach (mail, Slack, Teams) is drafted only after the user's yes for that row, in their voice, and the user sends it. This skill never sends and holds no outbound tool.
4. **Record each answer** when the user reports it: an `## ` entry in `answers.md` with the lines `Owner:`, `Date: YYYY-MM-DD`, `Link:`, `Summary:` (plain lines, no bullet or bold, one each, no message bodies, no client or investor names; the link points to where the source lives). Then close the row's result: `confirmed`, `killed`, `changed: <what>` or `accepted by <role>: <reason>; revisit: <trigger>` (the decider accepts a risk, with a reason and when to look again). An answer that kills or reshapes the idea stops the loop: take it to step 7.
5. **Keep `Brief.md` current.** 1-2 pages generated from the frame and the map: problem and who has it, observable success, appetite, solution sketch, no-gos, open questions with owners and answers, and a `## Terms` list (words an owner may name differently). It is the only document stakeholders read, published by the user to their shared doc tool (the vault stays private) and revised as answers land.
6. **Before commitment** every row is closed. Name `/cold-read <folder>/Brief.md` once, on the final Brief; do not run it. Run `idea_check --gate 2` and read the sha12 from its `brief-read` line; the user appends to `## Gates` `- YYYY-MM-DD cold-read: pass <sha12>` or `accepted <sha12> by <role>`. A later Brief edit needs a new line.
7. **Commit.** The decider's commitment rides on their approval of the final Brief (no separate meeting): append `- YYYY-MM-DD gate2: pass by <decider role>` (or `gate2: kill: <reason>` / `gate2: reshape: <reason>`) to `## Gates`. Log hours under `## Hours` as `- YYYY-MM-DD answering <n>h`; set `stage: gate2` on pass, `killed` or `reshaped` otherwise.
8. **Run the gate** (on kill or reshape, stop after recording the line with its reason and setting `stage: killed` or `reshaped`) and show the output verbatim:

   ```
   python3 ~/.claude/skills/idea-frame/scripts/idea_check.py <folder> --gate 2
   ```

   Fix every FAIL (usually an open row, a missing Link, or a stale cold-read sha12), rerun until none (on pass). Never edit the check or the decider to pass.
9. **Hand off** by naming `/to-spec`; after it writes the PRD, set `stage: prd`. Do not run it.

Done when `idea_check --gate 2` prints no FAIL and `/to-spec` is named from the final Brief, or the idea is killed or reshaped with the reason recorded.

## Rules

- Decisions come from the decider or a source. Never fill `answers.md` or a result from your own inference.
- Only the user's yes unlocks a draft; only the user sends.
- A material answer change after commitment reopens it: new Brief revision, new cold-read line, new `gate2` line.
