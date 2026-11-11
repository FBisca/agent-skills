# 04 — Chart selection and adaptation

The first design choice is the chart type, and most of the time the right answer is unfashionable: a bar chart, a line chart, a scatter plot. The conventions in this file aim at three goals: matching the **chart to the question**, escalating to richer forms only when needed, and **adapting** the chosen chart for the medium it will live in.

## Match the chart to the question

A chart answers a question. Picking the chart starts with naming the question:

| Question | First chart to try | Notes |
|---|---|---|
| "How does X compare across categories?" | Bar chart (horizontal if labels are long) | Sort by value unless ordering carries meaning (months, ranks). |
| "How has X moved over time?" | Line chart with time on the x-axis | One series per category; few categories. |
| "How is X distributed?" | Histogram, density plot, or box plot | Choose by audience: histograms for general; box plots for analytic. |
| "How do X and Y move together?" | Scatter plot | Add a fitted line only with explicit labeling. |
| "How does a whole break into parts?" | Stacked bar (categories) or stacked area (time) | Only when parts sum to a meaningful whole. |
| "Where is X concentrated geographically?" | Choropleth (rates) or symbol map (counts) | Maps are heavy; check whether a bar or table would do. |
| "How do ranks change?" | Bump chart or slope chart | Slope chart for two periods; bump chart for many. |
| "How is a single value evolving toward a target?" | Bullet chart or gauge | Use sparingly; numbers in a sentence often suffice. |

Most analytical questions reduce to one of the first four rows. Default there.

## The simpler chart is usually right

A useful test before reaching for an advanced chart type: what would the same data look like as a bar chart? If the bar chart answers the question, the bar chart wins. The candidate complications — dual axes, 3D, stacked variants, niche chart types — should each justify themselves against the bar chart they would replace.

A handful of chart types tend to be over-used; a handful tend to be under-used.

**Over-used:**
- Pie charts (use bars; the eye compares lengths far better than angles).
- Stacked bars where the parts do not sum to a meaningful whole (use grouped bars).
- Donut charts, 3D bars, 3D pies.
- Word clouds (a sorted bar chart of word frequencies is more informative).
- Dual-axis charts where the two scales are unrelated.

**Under-used:**
- Slope charts for two-point comparisons across many categories.
- Small multiples for "the same chart, repeated by group."
- Dot plots with thin lines for category-level distributions.
- Direct labels on lines and bars in place of a separate legend.

## A short tour of richer chart types

When the simple chart genuinely fails, escalate deliberately. A few that earn their keep:

- **Bubble chart.** Three variables: x, y and area. Use sqrt-area scaling so the *area* is proportional to the value (not the radius). Prefer when the third variable is decisive; otherwise color or size separately.
- **Treemap.** Nested part-to-whole with many leaves. Better than a stacked bar when there are too many slices for bar-comparison; worse for precise comparison.
- **Ridgeline (joyplot).** A stack of small density plots. Good for "the distribution shifted over time."
- **Connected scatter.** Two variables over time, with year labels along the path. Good for showing the trajectory in (x, y) space rather than each variable separately.
- **Ternary plot.** Three components that sum to 100%. Good for compositions (votes across three parties; alloys across three metals); requires reader familiarity.
- **Beeswarm / strip plot.** All individual points with horizontal jitter to avoid overplotting. Better than a box plot when the audience benefits from seeing the distribution itself.
- **Sankey / alluvial.** Flow between categories. Read flows visually but precise comparison is hard; pair with a table for the numeric backing.
- **Slope chart.** Two-period comparison across categories, lines connecting the two endpoints. Cleaner than a paired bar chart when there are many categories.
- **Bump chart.** Rank changes over many periods. Visually busy; reserve for cases where rank is the story (sports tables, brand rankings, country leaderboards).
- **Heatmap / matrix.** Two categorical axes, one numeric variable encoded by color. Good for high-cardinality cross-tabs; bad when precise reading is needed.
- **Cartogram.** A map distorted by a variable (population, GDP). Conveys magnitude where a choropleth would over-emphasize land area; less familiar to readers.

For each, ask: does the audience know how to read it? If not, either use a more familiar chart or invest in onboarding (a small annotated example, an "how to read this chart" callout).

## Maps deserve their own care

Maps are persuasive and easy to mislead with. Conventions:

- **Choose the projection deliberately.** Mercator is familiar but distorts polar regions; equal-area projections (Mollweide, Eckert, Equal Earth) preserve area at the cost of shape. Pick to match the variable: equal-area for population or anything per-area; Mercator only when navigation is the point.
- **Watch out for area dominance.** A choropleth shaded by a per-capita rate gives huge visual weight to large but sparsely populated regions. Consider a cartogram, a hex-tile map (each region a same-size hexagon), or a small-multiple of bars instead.
- **Disputed borders.** Internationally disputed territories (Kashmir, Crimea, the West Bank, Western Sahara, Taiwan, etc.) require an editorial choice. Many newsrooms render them with dashed outlines, neutral coloring, or labels noting the dispute. Make the choice consciously and document it; do not let a default basemap make it for you.
- **Labels in many languages.** Place names that locals expect to see may differ from the audience's language. Pick a convention; be consistent.
- **Color matters more on maps.** Sequential color ramps for ordinal data (low to high), diverging palettes for data with a meaningful midpoint (above/below average, gain/loss), categorical palettes for unordered groups. See [05-visual-elements.md](05-visual-elements.md).
- **Symbol maps for counts.** When the variable is a count or absolute total, place sized markers on a map rather than coloring regions.
- **Globe vs. flat map for global stories.** If the story is genuinely planetary (climate, ocean currents, polar ice), an orthographic projection or rotating globe avoids the distortion of any flat map.

## Print, web, mobile, social, video, presentation

The same chart for different media is rarely the same chart. The agent should know which medium the chart will land in and adapt before exporting.

### Print

Constraints: fixed size, often single-page, no interaction, sometimes grayscale.

- Aspect ratio fits the column or page.
- High-resolution exports (PDF/SVG, or 300dpi raster).
- Color choices that survive grayscale printing (vary lightness, not just hue, and combine with line styles or markers).
- Captions and notes printed below the chart, not in tooltips.
- Bigger fonts than on screen; people read print at arm's length.

### Web (desktop)

Constraints: variable width, possible interaction, many readers will see static social-media previews instead of the page.

- Responsive layout; use SVG when possible for scaling.
- Tooltips can layer detail, but the chart must work without them (see [07-interactive-and-js-viz.md](07-interactive-and-js-viz.md)).
- Open Graph image and a Twitter/X card image — usually a static, square or 16:9 version of the chart with title and source baked in.

### Mobile

Constraints: ~360px–430px wide, vertical scrolling, often the dominant audience.

- Redesign for portrait orientation. A wide landscape chart with right-margin annotations does not survive a 360px screen.
- Drop or relocate annotations; consider sequencing them across multiple stacked charts instead of crowding one.
- Larger touch targets on any interactive elements (44×44px minimum).
- Sometimes the mobile chart is genuinely a different chart — e.g., a horizontal bar chart instead of a wide grouped bar chart.

### Social

Constraints: one image, often square or 4:5 portrait, seen at thumbnail size first.

- Title, takeaway and source legible at thumbnail size.
- Strong visual hook: a striking shape or a single highlighted series.
- Branded styling consistent across the publication.
- Avoid fine multi-series detail; one or two series reads at thumbnail size, six does not.

### Video

Constraints: motion, narration, time-based reveal, often 1080p or 4K.

- Reveal the chart in stages — axes first, then series, then annotations — to give the narrator something to point to at each moment.
- Big fonts; the viewer is several feet from the screen.
- Avoid relying on hover or click; the viewer cannot interact.

### Presentation (slides)

Constraints: a few seconds of attention per slide, a speaker present, projection often poor.

- One chart, one message per slide.
- Title is the takeaway sentence; the speaker can elaborate.
- Strong visual hierarchy with one or two highlighted series.
- Strip extraneous gridlines, legends, and decoration; the speaker is providing context, not the chart.

When a piece will appear in multiple media (a publication often hits print, web, mobile, newsletter, social and video for the same story), expect to redesign the chart per medium, not to rescale it.

## Tiny charts and sparklines

Sometimes the right chart is very small: a sparkline embedded in a sentence, a thumb-sized chart in a table cell, a row of indicators on a dashboard. Conventions:

- **Strip everything non-essential.** No axes, no gridlines, sometimes no labels. The reader is reading a shape, not a value.
- **One value, one trend.** A sparkline answers "is this going up, down, or flat" and approximately "how steeply."
- **Pair with the latest number** in the surrounding text or table. The shape gives trend; the number gives level.
- **Consistent scaling across a row of sparklines** when they will be compared, or normalize to share a baseline.

## Infographics — composition, not novelty

An infographic is not a chart type; it is a composition of charts, illustration, callouts and short text laid out as a single visual narrative. Effective infographics:

- **Lead with one big idea.** A single hero chart or image carries the headline; the rest supports it.
- **Compose for a reading order.** Eye flow top-to-bottom for portrait formats; left-to-right for landscape; mark the path with size, alignment and white space.
- **One color story, not many.** Pick a small palette and use it across the panels.
- **Earn each element.** Every panel, illustration and callout should answer a question. Decoration that does not — stock illustrations, decorative backgrounds, repeated icons — should be cut.
- **Separate "the chart" from "the chart's chrome."** Title, units, source, footnote belong on the infographic, but should not dominate it visually.

A sound test: does the infographic still work if you remove all decoration and leave the charts and the text? If yes, the decoration was earning its space; if no, the composition was decoration-led, not data-led.

## Static or animated?

Animation is sometimes the right answer (showing a process unfold, a model converge, a population age), and is more often a distraction. Defaults:

- **Static is the default** for analytical work. It is reproducible, citable, accessible, and the same across media.
- **Animation earns its place** when the *change* is the message — a process, a flow, a build-up.
- **Step-through, not autoplay.** When animation is present in interactive contexts, prefer reader-controlled stepping (scroll or click) over auto-running loops.
- **Static fallback.** Every animated chart should have a single static frame that carries the headline, for print, social and accessibility.

## A chart-selection checklist

Before settling on a chart type, verify:

- [ ] The question the chart answers is statable in one sentence.
- [ ] A bar / line / scatter would not also answer it (or, if it would, you have a deliberate reason to escalate).
- [ ] The chart type is familiar to the audience, or the chart includes a how-to-read it cue.
- [ ] The medium has been chosen and the chart is designed for that medium, not retrofitted.
- [ ] The chart, the title, and the surrounding text agree on the message.
