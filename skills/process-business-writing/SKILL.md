---
name: process-business-writing
description: "Conventions for clear, persuasive business writing and storytelling in English — planning by purpose, audience, message and structure; paragraph-as-point composition; concrete word choice over jargon; short active sentences; ethical data storytelling; and disciplined editing. Apply this skill whenever generating or editing English prose for human readers — emails, memos, reports, slide decks, README sections, PR descriptions, dashboard copy, executive summaries, stakeholder analyses, release notes, commit-message bodies — even when the user does not explicitly ask for 'good writing,' because the same conventions raise the quality of every English text the agent produces."
disable-model-invocation: true
license: Apache-2.0
---

# Business Writing and Storytelling

Conventions the agent should apply by default whenever it writes English prose intended for a human reader. The goal is writing that is **clear, accurate, audience-aware, and confidently edited** — usable in any business context from a one-line Slack update to a multi-section report.

These conventions are vendor-agnostic and IDE-agnostic. They are based on the working practices of professional editors and on widely cited references in the writing-craft canon (Strunk and White, Orwell's *Politics and the English Language*, Pinker's *The Sense of Style*, Tufte's data-visualization work, Knaflic's *Storytelling with Data*).

## When this skill applies

Apply by default when the agent produces or edits prose for human consumption. Common situations:

- Drafting commit messages, PR titles and PR descriptions (combine with [git-commit](../git-commit/SKILL.md) and [gh-pr-create](../gh-pr-create/SKILL.md))
- Writing or editing README sections, AGENTS.md, ADRs, runbooks, design docs
- Producing executive summaries, stakeholder updates, analytical write-ups
- Writing dashboard text, chart titles, alert copy, release notes
- Drafting emails, memos, slides, and other business documents on the user's behalf
- Reviewing and editing prose the user has written, when asked for feedback

When in doubt, treat any English text destined for a human reader as in scope.

## The six pillars

The skill covers six pillars; each has a dedicated reference file. Read the relevant reference when the user's task touches that pillar, or when the agent is producing more than a few paragraphs of prose.

| Pillar | Reference | Use when |
|---|---|---|
| 1. Planning | [references/01-planning.md](references/01-planning.md) | Starting a new piece, fighting a blank page, scoping a deliverable |
| 2. Structure | [references/02-structure.md](references/02-structure.md) | Outlining, ordering paragraphs, building an argument, ending a piece |
| 3. Word choice | [references/03-words.md](references/03-words.md) | Editing for jargon, vagueness, hype, euphemism; choosing precise verbs |
| 4. Sentences | [references/04-sentences.md](references/04-sentences.md) | Tightening sentences, picking voice and weighting, using metaphor responsibly |
| 5. Data storytelling | [references/05-data-storytelling.md](references/05-data-storytelling.md) | Citing numbers, choosing charts, writing ethical data prose |
| 6. Editing | [references/06-editing.md](references/06-editing.md) | Revising drafts (own or others'), cutting, polishing, finalizing |

## Workflow the agent applies

When producing a substantive piece of writing (more than ~150 words, or any document with a clear deliverable), follow this loop:

1. **Plan.** State the four answers explicitly to yourself (or out loud to the user if scope is unclear): purpose, audience, message, structure. See [01-planning.md](references/01-planning.md).
2. **Outline.** Write a short list of the points you intend to make in the order you will make them. One paragraph per point. The list itself becomes the candidate executive summary or introduction.
3. **Draft.** Write quickly. Allow rough phrasing; the goal of the first pass is completeness, not polish.
4. **Edit pass 1 — structure.** Does each paragraph make a single point? Does the order create momentum (small to bigger, or hook → context → argument → close)? Cut detours.
5. **Edit pass 2 — language.** Replace jargon with everyday words. Prefer concrete verbs and short sentences. Cut at least 10% of the words. See [03-words.md](references/03-words.md), [04-sentences.md](references/04-sentences.md), [06-editing.md](references/06-editing.md).
6. **Edit pass 3 — accuracy.** Check facts, figures, names, links. A single wrong fact undermines an otherwise strong piece.
7. **Read aloud (or simulate it).** Anything that trips your tongue trips the reader's eye.

For very short outputs (a one-line PR title, a Slack reply), collapse the loop into a single conscious pass: ask "purpose, audience, message" silently before writing.

## The four planning questions

Every substantive piece answers four questions, ideally before drafting begins:

- **Purpose.** What change should this writing produce in the reader — a decision, an action, an understanding, an alignment?
- **Audience.** Who is the reader, what do they already know, and what will they push back on?
- **Message.** If the reader takes away one sentence, what should it be?
- **Structure.** What is the minimum sequence of points that gets the reader from where they are to that one-sentence takeaway?

If the agent cannot answer any of these in one short sentence, planning is not done. Ask the user, or make a defensible assumption and flag it.

## Defaults the agent applies to all English prose

These are the cross-cutting defaults. They override local stylistic instincts unless the user explicitly asks for a different register.

### Voice and clarity

- Prefer the **active voice**. Use the passive only when the actor is unknown, irrelevant, or deliberately backgrounded.
- Prefer **short, declarative sentences**. Break long sentences with full stops rather than commas or semicolons. Two crisp sentences usually beat one elegant compound sentence.
- Prefer **everyday English over Latinate or bureaucratic registers**. "Use" beats "utilize." "Help" beats "facilitate." "Show" beats "demonstrate." Choose the shorter, plainer word unless the longer one carries a meaning the shorter one cannot.
- Prefer **concrete nouns and vivid verbs** over abstractions. "The team shipped the migration" beats "The team facilitated implementation of the migration initiative."
- Avoid **jargon, clichés and pre-assembled phrases** ("at the end of the day," "leverage synergies," "move the needle," "low-hanging fruit"). When a technical term is unavoidable, define it on first use.
- Avoid **vague hedges** ("various," "several," "some," "many") when a number, a name, or an example would carry more weight.
- Avoid **euphemism that obscures meaning** and **hype that exaggerates it**. Both erode reader trust.

### Structure

- A paragraph is a single point. If a paragraph carries two points, split it. If a sentence wanders into a second idea, split it.
- State the **conclusion early** when persuading. Readers cannot evaluate evidence whose direction they cannot see.
- End sentences and paragraphs on the **strong word**. Rhythm matters; weight falls naturally on the last beat.
- Close with a **forward-looking note**, not a recap of what was just said.

### Numbers and evidence

- A number in isolation rarely informs. Pair it with a comparison, a baseline, or a vivid analogy.
- Distinguish **relative from absolute change** explicitly. "Risk doubled" without context can mean a tiny absolute change or a large one.
- Cite **primary sources** when feasible; name them inline when credibility matters.
- When data is patchy, **caveat** rather than overclaim, and pull together multiple sources to triangulate.

### Inclusivity and fairness

- Use **gender-neutral language** by default (singular *they*, plurals, role-based references) unless gender is the topic.
- Steelman the opposing view before disagreeing with it. The persuasive piece is the one that takes the counter-argument seriously and answers it.

### Cross-cultural awareness

- Avoid idioms, sports metaphors, or references that assume a single national context when the audience is global. If the piece is internal and English-second-language readers are likely, lean further toward plain syntax.

### Spelling and locale

- **Default to American English** (color, organize, behavior, analyze, -ize verb endings, single quotes around quoted speech inside double quotes per US convention). This is the user's working default; it is **not a hard rule**.
- Honor an explicit override. If the user, the project, or the audience signals British English (a UK-based company, a publication style guide, an existing document in British spelling), match it consistently throughout the piece.
- Whatever the locale, **do not mix**. A single document in mixed US/UK spelling looks careless. Pick one, lock it in, and run a final pass to catch drift.

## Output templates

The agent should adopt these compact templates when the task fits.

### Memo or short report

```
# [Title — what changed or what to decide]

## TL;DR
[One to three sentences. The decision, the recommendation, or the headline finding.]

## Context
[What prompted this; what the reader needs to know to evaluate the rest.]

## [Body sections, one point per heading]

## Recommendation / Next step
[A specific action, owner, and date when applicable.]
```

### PR description (combine with [gh-pr-create](../gh-pr-create/SKILL.md))

```
## Summary
[1–3 sentences: what this PR does and why it matters.]

## Context
[What prompted this change.]

## Changes
[Optional, only when the diff is large enough to need a guide.]

## References
[Issues, docs, prior art.]
```

### Executive summary at the top of an analysis

```
**Question.** [The decision the analysis informs.]
**Finding.** [The single-sentence answer.]
**Confidence.** [How sure, and what would change the answer.]
**Recommendation.** [What to do next.]
```

## Anti-patterns

These show up frequently in AI-assisted drafts. Reject them on sight.

- **Throat-clearing openings**: "In today's fast-paced world…", "It is important to note that…". Cut and start with the point.
- **Stacked qualifiers**: "It could potentially be argued that there might be a possibility that…". Choose one hedge or none.
- **Filler phrases**: "in order to" → "to"; "due to the fact that" → "because"; "at this point in time" → "now."
- **Empty intensifiers**: "very," "really," "truly," "clearly," "literally." Either find a stronger word or delete.
- **Unanchored numbers**: "Engagement increased by 23%" without a baseline, time window, or definition.
- **Sourceless assertions**: "Studies show…", "It is widely known that…". Either cite or recast as the writer's view.
- **Recap endings**: A closing paragraph that re-lists what was just said. End forward-looking instead.

## Interaction with other skills

- **[git-commit](../git-commit/SKILL.md)** and **[gh-pr-create](../gh-pr-create/SKILL.md)**: this skill governs the *prose* in commit messages and PR descriptions; those skills govern their *format* and the surrounding workflow. Both apply.
- **`analytics-descriptive`** (planned): when present, that skill carries the analytical-methodology layer (what to measure, how to frame uncertainty); this skill carries the *writing* layer that sits on top.

## Quality checklist for the agent

Before delivering a piece of substantive prose, the agent should verify:

- [ ] Purpose, audience, message and structure are answerable in one sentence each.
- [ ] Each paragraph makes a single point; the order builds momentum.
- [ ] Active voice predominates; passives are deliberate.
- [ ] No jargon, clichés or filler phrases that survive a fresh read.
- [ ] Numbers carry context (baseline, time window, comparison).
- [ ] Claims are sourced or framed as the writer's view.
- [ ] The piece has been cut by at least 10% from the first complete draft.
- [ ] The final sentence points forward, not backward.

## References

The conventions in this skill draw on widely available, primary-source writing-craft references. Consult them when deeper grounding is needed:

- William Strunk and E. B. White, *The Elements of Style*.
- George Orwell, [*Politics and the English Language*](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-works/politics-and-the-english-language/).
- Steven Pinker, *The Sense of Style*.
- Bryan Garner, *Garner's Modern English Usage*.
- Edward Tufte, *The Visual Display of Quantitative Information*.
- Cole Nussbaumer Knaflic, *Storytelling with Data*.
- Alberto Cairo, *The Truthful Art* and *How Charts Lie*.
- *The Economist Style Guide* (publicly available editions) — for newsroom-grade conventions on concision and clarity.
- [Anthropic Agent Skills](https://github.com/anthropics/skills) — the skill format this document follows.
