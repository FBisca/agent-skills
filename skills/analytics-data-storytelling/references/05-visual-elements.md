# 05 — Visual elements

Once the chart type is chosen, the design choices that matter are surprisingly few: **color, space, hierarchy, annotations, typography**. The conventions in this file aim at a chart that reads cleanly, encodes meaning consistently, and survives the conditions it will be read in.

## Color is the most easily misused element

Color carries semantic weight whether you mean it to or not. Conventions:

### Use as few colors as possible

Six is a soft ceiling; many strong charts use one or two. Each additional hue raises the cognitive cost.

- **One color** when the chart shows a single variable. Encode the data with position and length; let color carry the brand or aesthetic only.
- **Two colors** when the chart contrasts two things — categorical (men/women, control/treatment), directional (gain/loss), or temporal (before/after).
- **Three to six colors** when several distinct categories must be shown. Beyond six, consider grouping, faceting (small multiples), or highlighting a few series with a "background-and-figure" pattern.

When in doubt, the chart with fewer colors usually beats the chart with more.

### Pick the palette type to match the data

- **Categorical (qualitative).** Unordered groups (countries, segments, products). Use a palette where colors are perceptually distinct and not visually ordered. Avoid palettes that imply a ranking when there isn't one.
- **Sequential (single-hue).** Ordered data, low to high (rates, intensities, percentages). Use a single-hue ramp from light to dark, or a perceptually uniform multi-hue ramp such as **viridis**, **magma** or **cividis**.
- **Diverging.** Data with a meaningful midpoint (gain/loss, above/below average, hot/cold). Use two contrasting hues meeting at a neutral middle. Common pairings: red–blue, orange–blue, purple–green. Center the neutral at the meaningful zero (zero, average, baseline year), not at the data's midpoint.
- **Highlighting.** Most data in grey, the few series of interest in a single saturated color. Excellent default for showing a cohort against a population.

Avoid the **rainbow palette** (red→yellow→green→blue→purple) for ordinal data. It is perceptually non-uniform — the human eye sees more difference in some bands than others — and it confuses readers who don't know the encoding direction. Viridis-family palettes were designed to fix this; use them.

### Accessibility

About 8% of men and 0.5% of women have some form of color-vision deficiency. Defenses:

- **Never rely on color alone.** Combine color with a second cue: line style, marker shape, direct labels.
- **Avoid red+green pairings.** They are the most common confusion. Substitute red+blue, orange+blue, or magenta+teal.
- **Vary lightness, not only hue.** Two colors that differ only in hue (a green and a red of equal lightness) collapse to indistinguishable greys for some readers. Differ in lightness as well.
- **Test with a tool.** Color Oracle, Sim Daltonism, or the Chrome DevTools color-vision emulator simulate deficiencies on the live chart.
- **Test in grayscale.** Print previews and shared screenshots strip color; if the chart still reads, color is doing the right job.

### Cultural meaning

Color is not neutral across audiences:

- Red commonly reads as "loss," "danger," or "stop" in Western financial and public-health contexts; as "auspicious," "prosperous," or even "rising" in much of East Asia and parts of South Asia.
- Green commonly reads as "good," "growth," "go" in Western contexts; as "rising" in some East Asian financial contexts (the opposite of the Western convention).
- Up/down direction commonly reads as good/bad in many cultures; reversing it (zero at the top of the y-axis) almost always confuses readers regardless of locale.

When the audience is global, prefer palettes that carry meaning through *direction* and *intensity* (lightness) rather than through culturally loaded hues. Make conventions explicit in the legend or annotation: "darker = higher rate."

### Reuse colors with discipline

Across a piece, pick one color per concept and keep it. If "Europe" is teal in chart 1, it must be teal in chart 2. Mixing the same color across different concepts is one of the easiest ways to mislead a reader who is comparing charts.

## Typography

Type choices in charts carry less weight than color, but inconsistent type chips away at readability.

- **One typeface family per piece.** Sans-serif works at small sizes and on screens; serif works in long-form print. Pick one and use it everywhere.
- **Two or three sizes.** Title, body/labels, footnote. Avoid three different label sizes inside the chart.
- **Numbers in tabular figures.** Most fonts have a "tabular" or "monospaced number" variant where digits share equal width. Use it for axis ticks, table cells, and aligned numeric labels. Otherwise the columns shimmer.
- **Avoid all-caps labels.** They read more slowly than mixed case. Reserve all-caps for short titles or category headers where size is constrained.
- **Avoid italic, bold and color stacking.** A single emphasis cue is enough.

## Hierarchy

Every chart has elements competing for attention; the design imposes an order. A working hierarchy from most to least prominent:

1. **The data.** Bars, lines, dots — the primary marks.
2. **Annotations on the data.** Highlights, callouts, era markers — the takeaway-shaped narrative.
3. **The takeaway title.** The argument, in a sentence.
4. **Axis labels and ticks.** The frame.
5. **Source, notes, units.** The chrome.
6. **Gridlines.** Subordinate; never compete with the marks.
7. **Background.** Almost invisible.

Tools to enforce hierarchy:

- **Contrast.** The data should have the highest visual weight; gridlines the lowest.
- **Position.** Title and takeaway above the chart; source and notes below; legend either inside or right.
- **Size and weight.** Title larger, source smaller. Highlight the few series of interest in saturated color; push the rest to a faint grey.
- **Negative space.** Generous margins around the chart; do not crowd the edges.

A useful test: squint at the chart. The first thing your eye lands on should be the data and its highlight. If your eye lands on a heavy gridline, a brand logo, or a colorful legend, the hierarchy is wrong.

## Space and proportion

- **Aspect ratio matters.** A line chart squeezed into a square exaggerates short-run wiggles; a line chart stretched wide hides them. Pick the aspect ratio that lets the variation read at the right intensity for the message. The classic guidance ("banking to 45 degrees") is a useful starting point.
- **Margins.** Tight margins crowd; over-generous margins waste attention. Match to medium: web charts breathe; print charts pack tighter.
- **Bar widths.** Bars touching feel like a histogram (continuous). Bars with gaps feel like categories (discrete). Use the convention that matches the data.
- **Stacking order.** In a stacked bar or area, put the largest, most stable series at the bottom and the most volatile at the top. Volatile series at the bottom make every series above them appear to wiggle.
- **Sort order.** For bar charts of categories, sort by value unless the order carries meaning (months, ranks, official categories).
- **Reference lines.** Zero lines, target lines, average lines, era boundaries should be styled as auxiliary geometry — thinner, lighter, dashed — not competing with the data.

## Annotations

A chart with no annotations is a chart with no opinions. Annotations are where the chart's argument shows up.

- **Highlight inflection points.** A small arrow and a short label at the moment a trend changed.
- **Mark eras.** Vertical shading or labeled date bands for relevant periods (a recession, a campaign, a regulatory change).
- **Label key values.** The highest bar, the latest data point, the series of interest. Direct on-chart labels often beat a separate legend.
- **Replace the legend when possible.** Direct labels at the end of lines, or color-coded labels in the title, read faster than a separate legend block.
- **Keep annotations brief.** A label is not a paragraph. If the explanation needs more than ~10 words, split into a "small text on the chart" + "longer prose in the body."
- **Annotation typography matches body type.** Same family, often a slightly smaller size.

## Chart chrome — the bare-minimum elements

Every analytical chart that leaves the analyst's screen carries a few elements alongside the data:

- **Title.** A sentence or a label.
- **Subtitle.** The metric, units, geography, time window. Often serves as the descriptive complement to a takeaway-style title.
- **Y-axis label or unit hint.** "Quarterly revenue, $bn" — placed next to the y-axis, or in the subtitle when the axis is self-explanatory.
- **X-axis label or time markers.** Years for time series, category names for bars.
- **Legend or direct labels.** Direct labels preferred when feasible.
- **Source.** Below the chart, with a date accessed.
- **Notes.** Definitions, scope, calculations the chart hides.
- **Forecast / model / preliminary markers** when applicable.

These are the chart's chrome: necessary, but never the visual lead.

## Background and decoration

The default chart in most tools comes with a grey background, prominent gridlines, a default palette and a default font. None of these are wrong; few of them are best.

- **Prefer a white or transparent background** for analytical charts.
- **Make gridlines faint.** Grey on white at low contrast. Major gridlines slightly stronger than minor.
- **Cut decoration.** Decorative drop shadows, gradient fills, illustrative borders, "data ink" that doesn't encode data — Tufte's *data-ink ratio* — should be cut by default.
- **Brand sparingly.** A logo and a brand color in the corner are enough. Avoid coloring data series in the brand palette unless the palette also serves the data.

## Interactivity is a hierarchy decision

Interactivity (hover, click, tooltip, zoom, filter) sits in this section because it is largely a hierarchy choice: what is shown by default, and what is layered behind interaction.

The deeper conventions on when to be interactive at all live in [07-interactive-and-js-viz.md](07-interactive-and-js-viz.md). The quick rule for visual elements: **the chart must work without interaction.** A reader who never hovers should still get the headline finding. Interaction adds detail; it does not deliver the message.

## A visual-elements checklist

Before delivering a chart, verify:

- [ ] Color count is at most ~6 hues; a palette is chosen and used consistently.
- [ ] Palette type matches data type (categorical, sequential, diverging, or highlight).
- [ ] No red/green-only pairings; color has a second cue (line, shape, label).
- [ ] Hierarchy is correct: the data is loudest, gridlines and chrome quietest.
- [ ] Aspect ratio shows variation at the right intensity for the message.
- [ ] Annotations call out the takeaway; nothing else competes for attention.
- [ ] Title, subtitle, source and notes are present and proportionate.
- [ ] The chart works in grayscale and at thumbnail size.
- [ ] Numbers in axes and labels use tabular figures.
- [ ] Default styling has been overridden where it does not serve the message.
