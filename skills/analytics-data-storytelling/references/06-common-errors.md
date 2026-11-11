# 06 — Common errors and anti-patterns

A short field guide to the visualization and data-storytelling errors most likely to show up in AI-assisted analytical work. The agent should be able to spot each on sight and either fix or call it out.

The errors fall into three loose buckets: **scale and axis errors** (how the chart encodes magnitude), **comparison and inference errors** (what the chart claims about the world), and **rhetorical errors** (how the chart frames its argument).

## Scale and axis errors

### Bar charts with truncated axes

A bar chart's bar length encodes the value. Starting the axis at any value other than zero shrinks (or stretches) the visual differences and lies about the underlying ratios. A 5% increase looks like a tripling.

**Rule:** never truncate a bar chart's value axis. If an outlier dominates so heavily that small bars vanish, switch to a different chart (a log-scale dot plot, a slope chart, a small-multiples version). Don't break the axis to "fix" it.

### Line charts with badly chosen axes

Line charts can start above zero — small movements often need a tighter range to read — but this freedom is abused.

- **Tightening to exaggerate.** A 1% wiggle blown up to fill a chart's height misleads about the change's importance.
- **Wide ranges that hide changes.** A meaningful 10% move on a 0-to-100,000 scale becomes invisible.
- **Axis breaks without marks.** A break in the y-axis (the "two parallel slashes" convention) must be visually obvious; otherwise it is dishonest.

**Rule:** match the axis range to the importance of the variation you are claiming. If the variation is the story, use a tight range and label it. If the variation is small relative to the level, show that smallness.

### Inappropriate log scales

Log scales are right when values span orders of magnitude (population, asset values, virus loads, GDP). They are wrong when the data is roughly within the same order of magnitude — the log transform then compresses the visual differences misleadingly.

**Rule:** use log scales when the data demands them, label the scale clearly ("log scale, base 10"), and place tick marks at recognizable values (1, 10, 100, 1000) so readers without log fluency can still read the chart.

### Misaligned dual y-axes

Two series on a shared x-axis with different y-axes implies a relationship between them. The implication is often spurious: any two unrelated series can be made to look correlated by choosing the right scales.

**Rule:** prefer a single normalized axis (both series indexed to 100 at a baseline date) over a dual axis. When dual axes are unavoidable (a bar/line combo for volume + price, for example), align the zero of both axes if zero is meaningful, and label both axes clearly.

### 3D distortion

3D bars, 3D pies, 3D scatter and any chart with a perspective angle distort the visual length, area or position of marks. A bar at the back appears smaller than a bar of the same height at the front.

**Rule:** no 3D charts for analytical purposes. The only legitimate 3D analytical visualization is a small set of cases in physical sciences and immersive data exploration, and in those cases the reader interactively rotates the view.

## Comparison and inference errors

### Spurious correlations

Two series moving together over a chosen time window do not imply causation, common cause, or even genuine correlation. The website [Spurious Correlations](https://www.tylervigen.com/spurious-correlations) has thousands of examples (US per-capita cheese consumption tracking deaths by bedsheet entanglement, etc.).

**Rule:** when a correlation is the chart's argument, pre-register the relationship before plotting, ground it in a stated mechanism, and check whether it holds out of sample (a different time window, a different population). Mention the relevant base rates and any obvious confounders in the caption.

### Simpson's paradox

A trend within each subgroup can vanish or reverse when subgroups are combined. The classic example is the UC Berkeley admissions case: each department admitted men and women at similar rates, but the aggregate showed a gender bias because women applied to more selective departments.

**Rule:** when a chart aggregates across subgroups, also plot at the disaggregated level and compare. Lead with the level of aggregation that best matches the decision the analysis informs; show the other for honesty.

### Percentage vs. percentage points

A change from 10% to 12% is a 2 *percentage-point* increase and a 20 *percent* increase. They are not synonyms.

**Rule:** be explicit. "Approval rose from 40% to 48%" is unambiguous; "approval rose 8%" is not. In chart titles and prose, prefer the explicit construction.

### Base-rate fallacy

The absolute count of an outcome in a subgroup tells you almost nothing without the underlying population. "X% of crimes are committed by Y" is meaningless without knowing the share of Y in the population, the rates per capita, and the structural factors involved. The same trap appears in disease incidence, traffic safety, customer churn and educational outcomes.

**Rule:** report rates, not just counts, when populations differ. Pair counts with denominators. Be explicit about what is being normalized.

### Sample size and noise

A small sample with a striking effect should not be presented like a large sample with the same effect. A 10-percentage-point gap in a 50-person survey is consistent with no real difference; the same gap in a 5,000-person survey is decisive.

**Rule:** quote the sample size. For ordered comparisons (rankings, league tables) where some categories have small samples, either suppress the small-sample categories or present their values with explicit margins of error.

### Survivorship bias

Studying only the survivors of a filter (successful funds, successful startups, successful campaigns, surviving WWII bombers) tells you what the survivors had in common, not what causes survival.

**Rule:** name the population the data covers in the chart's subtitle or footnote. If survivors are over-represented, either expand the population or label the analysis "of those that survived."

### Premature enumeration

Counting a thing before being sure what it is. "Tech jobs," "crime," "inflation," "user," "active," "engagement" — every one of these names a contested category. (See [03-data-quality.md](03-data-quality.md).)

**Rule:** every chart that cites a count or a rate should define the unit clearly in the subtitle or footnote.

### Cherry-picked windows

A start date chosen because it makes the trend look steeper. A "since 2020" chart that begins at the trough of a pandemic shock shows growth that would look like a partial recovery in a longer window.

**Rule:** state the window deliberately. If the natural window is "since the most recent comparable point" (a previous downturn, a methodology change, a corporate event), use that. Avoid round-number defaults ("since 2020") that hide a chosen baseline.

## Rhetorical and design errors

### The neutrality fallacy

Believing a chart "just shows the data." Every chart is the result of editorial choices: which data, which window, which units, which chart type, which scale, which colors, which annotations, which omissions. Pretending otherwise is dishonest, and downstream readers will mistake the chart's framing for objectivity.

**Rule:** own the editorial choices. The chart's caption can be specific about the choice ("indexed to January 2020 for comparison") without hand-wringing. The agent should never use neutrality as a shield against a difficult finding; if the framing matters, name it.

### Default-style charts as deliverables

Shipping the matplotlib / Excel / Tableau default look — the gray background, the rainbow palette, the generic title, the side legend — to a stakeholder.

**Rule:** treat default styling as debugging. Anything that leaves a notebook for a human reader gets a deliberate title, palette, hierarchy and chrome. The cost is small; the credibility difference is large.

### Chart soup

Producing five or ten charts when one would do. Each chart adds cognitive load; readers stop reading.

**Rule:** every chart should answer one question that needs answering. If a chart is on the page because it was easy to make, cut it. The piece is stronger.

### Decoration that does not encode

Stock illustrations, gradient backgrounds, drop shadows, glow effects, embellished icons, repeated decorative elements that do not encode a variable. Tufte's "data-ink" framing: ink that does not represent data is a candidate for cutting.

**Rule:** every visual element should justify itself by encoding something. If an element exists for "look and feel" alone, it should be subtle (background brand color) rather than competing with the data.

### Pie charts (and friends)

Pie charts force the eye to compare angles or arc lengths, both of which the eye does badly. Two pie charts side by side is worse: the eye has to compare angles across two centers. Donut charts inherit the same problem with worse data-ink. 3D pies compound the problems with perspective distortion.

**Rule:** use horizontal bar charts. The eye compares lengths against a common baseline very well. The pie chart is the canonical example of "the chart that always has a better alternative."

### Word clouds

Font size encodes word frequency; layout encodes nothing meaningful (it follows space-filling, not data). The eye cannot reliably compare the size of "innovation" against "scale" when the words have different lengths and shapes.

**Rule:** use a sorted bar chart of word frequencies. Or, if the analysis is qualitative, quote a few representative phrases and report the frequencies in the surrounding prose.

### Chartjunk and data-driven illustrations done wrong

Illustrative charts where bars are stacked tomato slices, lines are pipelines, axes are ladders. They can work in editorial graphics where the metaphor is well-chosen and the underlying data still reads. They fail when the metaphor distorts the encoding (slices that don't have linear length, pipes whose width doesn't represent flow correctly).

**Rule:** if the metaphor reads at a glance, encodes data accurately, and the audience expects this register, use it. Otherwise, prefer an unambiguous chart.

### Interactivity for its own sake

Tooltips that hide essential information. Sliders that no one will move. "Explore the data" buttons with no path through the data. Hover effects that obscure the chart underneath.

**Rule:** the static version of the chart must carry the headline. Interactivity adds detail or supports exploration; it does not deliver the message. (See [07-interactive-and-js-viz.md](07-interactive-and-js-viz.md).)

### Premature precision

A chart that reports modeled estimates to four decimal places when the model's confidence band is wider than the value implies. (See [03-data-quality.md](03-data-quality.md) on premature precision.)

**Rule:** match output precision to the precision of the underlying measurement.

### Inconsistent palette across a piece

Using teal for "Europe" in chart 1 and teal for "tech sector" in chart 2 in the same article. The reader's eye learns the convention and is then misled.

**Rule:** one color per concept across the entire piece. Pick palettes once at the start; reuse rigorously.

## Mistakes the agent itself is prone to

In AI-assisted analytical workflows, a recognizable cluster of failure modes shows up:

- **Confident interpretation of unverified data.** The agent should never claim a finding it has not verified by inspecting the data and re-running the calculation. State both the method and the result.
- **Plot-first, think-later.** Reaching for a chart before answering the four planning questions. A chart that exists before the question does is decoration.
- **Defaults treated as choices.** Allowing the tool's default chart, default palette, default title to ship as the deliverable.
- **Over-confident language on noisy data.** "Sales soared" on a dataset with a wide confidence interval. Calibrate language to the strength of the evidence.
- **Forgetting the audience.** Producing a chart at the analyst's desk that does not survive the audience's medium, screen size or familiarity with the chart type.
- **Plagiarism risk in the prose.** Borrowing distinctive phrasings from the source materials when distilling. The output should be the agent's own paraphrase, original prose, with citations to primary sources where credibility matters.

The agent should treat each as a checklist item to interrogate before presenting analytical work.

## Post-mortems are part of the practice

Every newsroom and analytical team will at some point publish a chart they later regret. *The Economist* publishes "Mistakes, we've drawn a few" and similar reviews; The New York Times has retroactive corrections; data-viz teams keep internal post-mortem logs.

A post-mortem is short and concrete:

- **What was the chart trying to show?**
- **What did it actually show?**
- **What design choice caused the gap?**
- **What would we do differently?**

When the agent or the user notices a chart that misled, even mildly, write the four-line post-mortem. The practice is the single most reliable way to stop repeating the same error.

## A common-errors checklist

Before delivering a chart, verify:

- [ ] No bar chart has a non-zero baseline; line-chart axis breaks are clearly marked.
- [ ] Log scales are used only when justified, and labeled.
- [ ] Dual y-axes have been replaced with normalized axes whenever feasible.
- [ ] No 3D anything.
- [ ] Sample sizes are visible when comparison is the point.
- [ ] Comparisons control for population (rates, not raw counts) where appropriate.
- [ ] Subgroup-vs-aggregate views have been checked for Simpson's paradox.
- [ ] Percent vs. percentage-point distinctions are explicit.
- [ ] Cherry-picked windows are deliberate and named.
- [ ] No decoration that does not encode data.
- [ ] Pie charts and word clouds replaced with sorted bar charts.
- [ ] Interactivity earns its cost; static fallback carries the headline.
- [ ] Output precision matches data precision.
- [ ] Palette is consistent across the piece.
