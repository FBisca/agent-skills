# 05 — Data storytelling

> **For deeper analytical work,** see the dedicated [`analytics-data-storytelling`](../../analytics-data-storytelling/SKILL.md) skill. It is the terminal judgment layer for any data analysis, chart selection, visual design, common-error audit, and interactive or JavaScript-based visualization. The page you are reading is the lighter-weight section that lives inside `process-business-writing` for the case where data appears as part of general business prose.

Numbers and charts are the parts of business writing where misleading the reader is easiest, often by accident. The conventions in this file aim at three goals: numbers that **inform**, charts that **work**, and prose around the data that is **honest**.

## Numbers as part of prose

A number is an evidence point, not a decoration. Every number you cite in prose should pass three tests:

- **Comparable.** Is the number paired with a baseline, a comparison group, or a familiar reference? "Revenue grew $42M" is information; "Revenue grew $42M, up from $30M last quarter" is meaning.
- **Framed.** Is it relative or absolute? Over what time window? Real or nominal? Per user, per cohort, or in total? Spell out whatever the reader cannot see.
- **Vivid.** Where useful, anchor the number to something the reader can picture. "Each user reads 12,000 words per week — about a Harry Potter chapter every Tuesday" is more memorable than "12,000 words per week."

## Where to place numbers

A common failure mode is to dump numbers in the introduction. The reader cannot yet see why they matter and disengages.

Better placement:

- **Lead** with the headline number when the data *is* the news.
- **Cluster** supporting numbers in the second or third paragraph, after you have set up why they matter.
- **Avoid the number swamp.** If you find yourself writing six numbers in two sentences, move them to a small table or chart.
- **Acknowledge the work.** When the calculation is non-trivial, tell the reader: "These figures rest on three assumptions, set out in the appendix." That treatment increases trust rather than reducing it.

## Numbers that mislead — even when accurate

A number can be technically correct and still mislead. Watch for:

- **Relative without absolute.** "Risk doubled" — from what to what? A doubling from 0.001% to 0.002% is not a public-health emergency.
- **Cherry-picked windows.** Choosing a flattering start date is the easiest way to mislead without lying. State why you chose the window you did.
- **Misaligned comparisons.** Comparing 2019 GDP to 1990 GDP without noting the gap; comparing one country measured in nominal terms to another in real terms; mixing PPP-adjusted and nominal figures.
- **Single-fact arguments.** A single month, a single survey, a single anecdote — none is enough to support a strong claim. Look for trends; triangulate when sources disagree.
- **Inform vs. persuade confusion.** Be honest with yourself. If you are writing to persuade, that is fine — but do not pretend you are writing to inform. Your numbers will be picked accordingly, and the reader deserves to know.

## Choosing the right chart

Most business charts are over-engineered. About 80% of useful charts are **bar charts** or **line charts**, used in the right place. Start there; deviate only when the data resists.

Match chart type to the **question** the chart answers:

| Question | First chart to try |
|---|---|
| "How does X compare across categories?" | Bar chart (horizontal if labels are long) |
| "How has X moved over time?" | Line chart with time on the x-axis |
| "How is X distributed?" | Histogram or density plot |
| "How do X and Y move together?" | Scatter plot |
| "How does X break into parts?" | Stacked bar (only when the parts sum to a meaningful whole) |
| "Where is X concentrated geographically?" | Choropleth or symbol map |
| "How does X rank, and how do ranks change?" | Bump chart or slope chart |

Reach for fancier chart types — sankeys, treemaps, parallel coordinates, 3D — only when the simpler chart genuinely fails. The bar chart is rarely the wrong answer; the 3D pie chart almost always is.

## Effective beats beautiful

Aesthetic polish helps engagement, but it cannot rescue a chart that does not communicate. Reverse the priority: build the chart that answers the question, then make it pleasant.

A working test: show the chart to someone who has not seen the underlying data and ask, *"What does this say?"* If they describe what you intended, the chart works. If they ask "what am I looking at?", the chart has too much going on. Take things off; rarely add them.

## Honest axes

The single most common way charts mislead is the choice of axis range.

- **Bar charts** must start the value axis at zero. The bar's *length* encodes the value, and shortening a bar by truncating the axis exaggerates differences. Never break a bar-chart axis.
- **Line charts** can start the axis above zero — small movements often need a tighter range to be visible — but **mark the break clearly** and leave a visible gap below the line so the reader cannot miss it. A small change framed as enormous is dishonest; a small change shown as small while still readable is the goal.
- **Log scales** are appropriate when values span orders of magnitude. Label the scale clearly; readers who do not know it is log will misinterpret it.

## Honest comparisons

When a chart shows two or more series:

- **Same units, same definition.** Mixing real and nominal, gross and net, or different currencies on one axis hides as much as it reveals.
- **Same time window** unless the difference is the point.
- **Be careful with dual y-axes.** Two series on a shared x-axis with different y-axes implies a relationship between them. Two unrelated series can look correlated by accident. If the relationship is real, prefer a single normalized axis (e.g. indexed to 100 at a baseline date).
- **Smoothing.** When daily data is noisy, a moving average can show the trend more clearly. Label it as smoothed and disclose the window.

## Color, ordering, and accessibility

Charts encode meaning visually as well as numerically. Conventions:

- **Up tends to read as good, down as bad.** Plotting an axis upside-down (zero at the top, increasing downward) reverses this and confuses almost every reader.
- **Color carries meaning.** Red commonly reads as bad or negative; green as good; blue as neutral or positive in many contexts. These conventions are not universal across cultures but are worth respecting unless you have reason to break them. If you do break them, make the meaning explicit in the legend.
- **Reuse colors carefully.** Using the same color for two different things across charts in one piece will mislead. Pick one color per concept and keep it.
- **Design for accessibility.** Do not rely on color alone to distinguish series — combine color with line style, shape, or direct labels. Choose palettes that survive color-vision deficiencies and grayscale printing.
- **Label directly when possible.** Labeling lines and bars on the chart itself is faster to read than a separate legend.

## Highlighting in busy charts

When you must show many series at once (every country, every cohort, every product), do not give every series equal visual weight. Push the bulk into the background as faint lines, and **highlight** the few that the piece actually discusses. The reader sees the cohort-of-interest in context, not lost in the crowd.

## Three principles to keep in mind

A useful summary of the data-visualization conventions above:

- **Trustworthy.** The chart does not distort the data; assumptions and sources are visible.
- **Accessible.** Anyone in the intended audience can read it without specialized knowledge.
- **Elegant.** The chart looks pleasant, but never at the cost of the first two.

When the three conflict, drop elegance first.

## Quality checks for data prose and charts

- [ ] Every cited number has a baseline, a window, and a source.
- [ ] Relative and absolute changes are distinguished.
- [ ] No bar chart has a non-zero baseline; line-chart axis breaks are clearly marked.
- [ ] Comparisons use comparable units, time windows, and definitions.
- [ ] Color and direction follow standard conventions, or the deviation is explicit.
- [ ] A non-expert reader can describe the chart in one sentence.

## References

- Edward Tufte, *The Visual Display of Quantitative Information* — foundational reference on chart honesty.
- Cole Nussbaumer Knaflic, *Storytelling with Data* — practical conventions for business charts.
- Alberto Cairo, *The Truthful Art* and *How Charts Lie* — on chart ethics.
- Andy Kirk, *Data Visualisation: A Handbook for Data Driven Design*.
- David Spiegelhalter, *The Art of Statistics* — on framing risk and uncertainty.
- *The Economist's* publicly available articles on chart design (see "Mistakes, we've drawn a few" and similar pieces).
