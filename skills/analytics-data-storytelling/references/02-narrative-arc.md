# 02 — Narrative arc

A dataset has many hidden stories; an analytical piece tells one of them. The conventions in this file aim at three goals: a **single, defensible message**; a **structure that earns it**; and a presentation form (static, interactive, or scrollytelling) that fits the audience.

## A chart is a visual argument

Every analytical chart makes an argument: about a level, a direction, a comparison, a relationship, a turning point, an anomaly. A chart with no argument is exploratory by nature, and exploratory charts are debugging plots — useful to the analyst, rarely useful to the reader.

Two implications:

- **The argument should be statable in one sentence,** before you choose a chart type.
- **The chart's title should usually be that sentence,** not a generic label.

Compare:

- Generic title: "Quarterly revenue by segment, FY2015–FY2024."
- Argument title: "Cloud overtook hardware as Acme's largest segment in FY2022."

The first is a label; the second is a sentence the reader can agree or disagree with after looking at the chart. Argument-style titles are the dominant convention at *The Economist*, *The Financial Times*, *The New York Times* and *Bloomberg* — for a reason.

When the chart is genuinely exploratory or the takeaway is uncertain, fall back to the descriptive label. Avoid pretending to a takeaway you do not have.

## The single-sentence message

The first work after orientation is to compress the analysis into one sentence:

> *"In the last decade, [thing] [direction-and-magnitude] [where/for whom], driven by [cause]."*

Then audit the sentence:

- **Is it falsifiable?** "Engagement is up" is too vague. "Daily active users in cohort A rose 18% between 2022 and 2024, while cohort B was flat" is a sentence the data can support or refute.
- **Is the magnitude calibrated?** Words like "soared," "plunged," "doubled," "halved" are not synonyms for "grew" and "fell." If you reach for them, the data must back the strength.
- **Does it acknowledge whom it does not apply to?** A finding that holds for the median and breaks for the tails should say so.

If the sentence cannot be written, the analysis is not done.

## Structure: hook, context, evidence, close

For an analytical write-up of any length, a workable default structure:

1. **Hook.** The headline finding in one or two sentences. The lede; the chart everyone needs to see if they read nothing else. This is a lift from journalism, and it works because most readers do not finish.
2. **Context.** Why this question, why now, what the reader needs to know to evaluate the rest. Keep it short. Long context is procrastination.
3. **Evidence.** The body. Each section answers one sub-question with one chart and a paragraph or two of prose. Strong-to-weak when persuading; weakest-to-strongest only when building a case the reader will resist.
4. **Caveats.** What the analysis cannot tell you, and what would change the answer. Name them; do not hide them in a footnote.
5. **Close.** The recommendation, the next step, or the open question. Forward-looking, not a recap.

This is the same arc as the [process-business-writing](../../process-business-writing/SKILL.md) memo template, applied to analysis. The structure is in service of the message; deviate when the piece needs it.

## Exploratory vs. explanatory work

Two distinct genres of visualization, with different conventions:

- **Exploratory.** The analyst is looking for the story. Charts are fast, ugly, plentiful, and live in the analyst's notebook. Default styles are fine. Honesty matters; polish does not.
- **Explanatory.** The analyst has the story and is presenting it. One or a few charts; each carefully designed; argument-style titles; deliberate annotations; consistent palette across the piece.

Conflating them is a common failure. An explanatory deliverable that looks like exploratory output (default colors, no annotations, generic titles, ten charts where one would do) signals to the reader that the analyst has not yet decided what the story is. An exploratory plot that has been over-polished risks freezing the analyst on a story before the data has spoken.

The agent should know which mode it is in and design accordingly.

## When the data has multiple stories

Real datasets often carry several defensible stories: a long-run trend, a recent inflection, a within-group reversal, a tail behavior. The piece does not have to choose one and bury the others; it has to **lead with one** and let the others appear as supporting structure.

Useful patterns:

- **Lead chart, then breakdowns.** The first chart shows the overall finding; subsequent charts show how it varies by region, cohort, or category.
- **Small multiples.** When the same chart shape applies to many groups, repeat it as a grid rather than overplotting. The reader compares panels at a glance.
- **Big-picture chart with annotated era markers.** Long time series almost always carry several inflection points; mark them on the chart instead of in the text.
- **Scrollytelling.** When the story has several moves and the reader benefits from seeing them in sequence rather than all at once, consider a scrolly piece (see [07-interactive-and-js-viz.md](07-interactive-and-js-viz.md)). It is expensive; reserve it for stories that earn it.

## The chart-text contract

Charts and prose are partners. A working contract:

- **The chart carries the data.** Numbers, levels, comparisons, trends.
- **The prose carries the reasoning.** Why this metric, why this window, what the chart implies, what comes next.
- **Annotations bridge the two.** A label on the chart at the moment a policy changed; a small arrow at the inflection point; a callout at the highest bar with the value.

Three bad patterns to avoid:

- **The chart that repeats the prose.** "As you can see in the chart, sales rose from 100 to 200 in 2023" — and the chart's only content is "sales rose from 100 to 200 in 2023." Either trust the chart and cut the prose, or replace the chart with a sentence.
- **The prose that ignores the chart.** A figure dropped in with no reference, no callout, no quoted value. The reader has to do the agent's job.
- **The chart with no prose at all.** Sometimes appropriate (a dashboard, a poster), often not. In a written analysis, a chart without surrounding sentences is a chart without an argument.

## Scrollytelling — when the form fits

Scrollytelling pieces step the reader through a sequence of states (charts, maps, frames) as they scroll. They suit data stories with several moves where seeing all of them at once would overwhelm: a model that builds up layer by layer, a map that zooms from global to local, a long time series that deserves multiple annotated stops.

Conventions for scrollytelling, distilled from current practice:

- **One idea per scroll step.** Each frame says one thing.
- **The story should work on the y-axis.** Down the page is the dominant reading direction; left-right interactive controls are secondary.
- **Static image backup.** Every frame should have a printable, screenshot-able fallback for readers, social previews, and accessibility. If the story collapses without the interaction, redesign.
- **Performance budget.** Mobile readers on cellular networks are the binding constraint. Lazy-load assets, prefer SVG over canvas where feasible, prefer CSS transitions over per-frame redraws.
- **Don't bury the lede.** The first frame should already make the headline finding visible. Use the rest of the scroll to deepen, not to delay.

The mechanics of building scrollytelling pieces (Scrollama.js, Svelte transitions, Observable Plot frames, the Python → JSON → JS data handoff) are in [07-interactive-and-js-viz.md](07-interactive-and-js-viz.md). The judgment of *whether* to scrollytell at all is here.

## Don't bury the lede

A common analytical failure is to lead with the method ("we collected data on N firms across K years using model M…") rather than the finding. Most readers do not finish a piece; the ones who do will return for the method if the finding is interesting.

Default order:

1. **What we found.**
2. **Why it matters.**
3. **How we found it.**
4. **What the analysis cannot tell you.**

The exception is when the method is the news (a novel measurement, a new dataset, a methodological correction to an earlier finding). Even then, the headline is the finding; the method shows up immediately after, not in paragraph nine.

## End forward, not backward

The closing paragraph or final chart should point the reader somewhere — a recommendation, a decision deadline, an open question, a next experiment. A summary recap of what the piece just said is wasted real estate.

Useful closings:

- "We recommend X by date Y, on the strength of evidence A and B; we will revisit if Z."
- "The data favor hypothesis A, but cannot rule out B; experiment Q would distinguish them."
- "If the trend persists, we expect Z by end-of-quarter; the next checkpoint is on D."

A piece that ends with "in conclusion, this analysis showed that…" has wasted its strongest position.

## A narrative-arc checklist

Before delivering an analytical piece, verify:

- [ ] One-sentence message exists, is falsifiable, and is calibrated to the strength of the evidence.
- [ ] Hook → context → evidence → caveats → close structure (or a deliberate alternative).
- [ ] Each chart has a takeaway-style title that matches the surrounding prose.
- [ ] Caveats are visible, not hidden.
- [ ] The piece ends on a forward-looking note.
- [ ] If the format is interactive or scrollytelling, the form earns its cost.
