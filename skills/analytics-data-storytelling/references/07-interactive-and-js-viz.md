# 07 — Interactive visualizations and JavaScript

This file is the canonical home for guidance on **when** to make a chart interactive, **how** the typical visualization tool stack escalates from static Python to web JavaScript, and **what** small but complete code patterns the agent should reach for in each layer. There is no separate `tooling-d3-js` or `tooling-plotly` skill in this repo; both static and interactive viz judgments live here, and any future `tooling-python` or `tooling-r` skill defers to this file for visualization decisions.

## When interactivity earns its cost

Most analytical charts should *not* be interactive. A static chart is reproducible, citable, accessible, viewable on any device, and can be embedded as a screenshot. Interactivity adds engineering cost, accessibility burden, and a chance to hide essential information.

Interactivity earns its cost in three specific cases:

1. **A second, denser layer of information** that would clutter the chart if shown by default. A line chart with annual averages, where hovering reveals the constituent monthly values; a map of regions, where hovering reveals the population, GDP and main metric. The static chart already shows the headline; interaction adds depth.
2. **Genuine reader exploration** with a clear path through the data. A drop-down to switch the displayed metric (employment, inflation, GDP), or a slider to change the year. The interaction must be discoverable, the controls obvious, and the chart must work at every state of the controls.
3. **Scrollytelling** for stories with several moves where seeing all of them at once would overwhelm. The reader's scroll triggers transitions between annotated states.

Interactivity does **not** earn its cost when:

- The headline finding is hidden behind a hover.
- The interaction is a tooltip with no extra content.
- The controls are unclear ("scroll to explore" without telling the reader what they will see).
- The piece will be republished as a static screenshot in social, print or video — and the screenshot is unintelligible.

A working test: take a screenshot of the default state. If the screenshot, on its own, does not deliver the headline, the interactive version is not ready to ship.

## The three-tier tool stack

For analytical visualization, escalate from simple to complex only when the simpler tool genuinely cannot do the job. The tier choice does not change the conventions in this skill; the same rules on color, scale, annotation and ethics apply at every layer.

### Tier 1 — Static, publication-quality charts: `plotnine` (Python) or `ggplot2` (R)

The default for reports, slide decks, README figures, blog plots and any printable artifact. Both implement Wilkinson's grammar of graphics; the conventions, mental model and most function names are shared.

**Choose this tier for:** reports, slide charts, papers, README figures, blog plots, anything that will be exported as PNG or PDF. About 80% of analytical charts.

### Tier 2 — Lightweight web interactivity: `plotly` (Python)

Useful when hover labels, zoom, pan or simple cross-filtering add real value, and the deliverable is a notebook, a dashboard, or a webpage that will not need bespoke design. Plotly emits self-contained HTML, integrates with Jupyter, and is a single-line export from a `pandas` or `polars` data frame.

**Choose this tier for:** notebooks read by stakeholders, internal dashboards, exploratory web pages where the audience benefits from inspection but not custom design.

### Tier 3 — Bespoke interactive web pages: JavaScript

Reserved for the cases where Tiers 1 and 2 cannot deliver the experience the audience needs:

- Custom-designed visualizations that match a publication's house style.
- Scrollytelling pieces.
- Maps with choropleth + tooltip + custom basemap.
- Multi-view linked visualizations.
- High-performance animations.
- Embeddable widgets in a content-managed website.

The JavaScript ecosystem is broad. The agent should know the four sub-tiers within JS itself, and reach for the highest-level one that fits.

## The JavaScript visualization stack

In rough order from highest-level to lowest:

1. **Vega-Lite** — declarative JSON specs for charts. Excellent for charts that already exist in its grammar (most standard chart types). The chart is a JSON object; you describe the data and the encodings; Vega-Lite renders. Good for fast custom charts in articles.
2. **Observable Plot** — a JavaScript port-and-extension of `ggplot2`'s grammar. Concise, modern API. Renders SVG. Good middle ground between Vega-Lite's declarative ergonomics and D3's flexibility.
3. **D3.js** — the foundational, low-level library. You position every element. Maximum flexibility, maximum effort. Reach for D3 when the chart requires a custom shape, a non-standard layout, or a complex animation that the higher-level libraries cannot express.
4. **Component frameworks: Svelte, React, or vanilla JS + DOM/SVG.** Whichever wraps the chart in a page. Svelte is popular in editorial data-viz teams (small bundles, scoped CSS, reactive transitions). React is the default in product teams. Vanilla JS works for static articles.

Adjacent libraries that often appear in the stack:

- **Data manipulation in the browser.** `Arquero`, `Tidy.js`, `Lodash`, `D3-array`, `D3-fetch`. Useful when filtering, grouping, joining or reshaping happens in the client (a reader-controlled dropdown that re-aggregates the data, for example).
- **Maps.** `D3-geo` for projections, `topojson-client` for compact map data, `Mapbox GL JS` or `MapLibre GL JS` for tile-based interactive maps with pan and zoom.
- **Scrollytelling.** `Scrollama.js` to detect when scroll-triggered "steps" enter the viewport.
- **Animation.** D3's transition system, or framework-native primitives (Svelte transitions, React Spring).
- **Bundling and deployment.** Vite for development, ESBuild or Rollup for production, deployed as static HTML/JS/CSS with the data as JSON or CSV alongside.

## The Python → JSON → JavaScript handoff

A typical workflow: do the heavy data transformation in Python (`pandas` / `polars` / SQL in a warehouse), then export a small clean JSON or CSV file that the JavaScript chart consumes. This keeps the browser code small and the data pipeline reproducible.

```python
import json
from pathlib import Path

import pandas as pd

raw = pd.read_parquet("data/transactions.parquet")
monthly = (
    raw
    .assign(month=lambda d: d["timestamp"].dt.to_period("M").dt.to_timestamp())
    .groupby(["month", "segment"], as_index=False)["revenue"]
    .sum()
    .sort_values(["month", "segment"])
)

records = monthly.to_dict(orient="records")
for r in records:
    r["month"] = r["month"].strftime("%Y-%m-%d")

Path("public/monthly_revenue.json").write_text(
    json.dumps(records, separators=(",", ":"))
)
```

Conventions for the handoff:

- **Strip to what the chart needs.** Don't ship the full warehouse to the browser. A few hundred KB is usually enough; a few MB is a smell.
- **Use ISO dates as strings.** `"2024-01-01"` is unambiguous; `"01/02/2024"` is a debugging session waiting to happen.
- **Prefer long-format records** (`[{month, segment, revenue}, ...]`) over wide-format objects. Most JS viz libraries expect long format and `Arquero` / `Plot` can pivot if needed.
- **Version the data file** in the URL path or filename when the data updates. Browsers cache aggressively.
- **Document the schema** in a one-line comment at the top of the JS file. Future readers (including the agent) thank you.

## Small but complete code examples

The examples below are deliberately compact. Each is a working sketch that the agent can adapt to the specific dataset, not a production-ready chart. The conventions in the rest of this skill (color, scale, annotation) apply to all of them.

### Tier 1 — Static chart in `plotnine`

```python
from plotnine import (
    ggplot, aes, geom_line, geom_point, labs,
    scale_color_manual, theme, element_text, theme_minimal,
)

p = (
    ggplot(monthly, aes(x="month", y="revenue", color="segment"))
    + geom_line(size=1)
    + geom_point(size=2)
    + scale_color_manual(
        values={"cloud": "#1f77b4", "hardware": "#d62728", "services": "#2ca02c"}
    )
    + labs(
        title="Cloud overtook hardware as Acme's largest segment in FY2022",
        subtitle="Quarterly revenue, $bn, FY2015–FY2024",
        x="", y="",
        caption="Source: Acme 10-K filings, accessed 2026-04-21.",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(weight="bold", size=14),
        plot_subtitle=element_text(color="#555", size=11),
        legend_position="bottom",
    )
)

p.save("revenue_by_segment.png", width=8, height=5, dpi=200)
```

Notes:
- Argument-style title carries the takeaway; subtitle carries the descriptive metadata.
- A small, deliberate palette; segments are mapped to fixed colors so the same color means the same segment everywhere in the piece.
- Legend at the bottom; consider `geom_text` direct labels at line ends instead, especially for print.

### Tier 1 — Static chart in `ggplot2` (R)

```r
library(ggplot2)
library(dplyr)

p <- monthly |>
  ggplot(aes(x = month, y = revenue, color = segment)) +
  geom_line(size = 1) +
  geom_point(size = 2) +
  scale_color_manual(values = c(
    cloud    = "#1f77b4",
    hardware = "#d62728",
    services = "#2ca02c"
  )) +
  labs(
    title    = "Cloud overtook hardware as Acme's largest segment in FY2022",
    subtitle = "Quarterly revenue, $bn, FY2015-FY2024",
    x = NULL, y = NULL,
    caption = "Source: Acme 10-K filings, accessed 2026-04-21."
  ) +
  theme_minimal(base_size = 11) +
  theme(
    plot.title    = element_text(face = "bold", size = 14),
    plot.subtitle = element_text(color = "#555"),
    legend.position = "bottom"
  )

ggsave("revenue_by_segment.png", p, width = 8, height = 5, dpi = 200)
```

The grammar is essentially identical to `plotnine`; the agent can usually translate one to the other line for line.

### Tier 2 — Interactive chart in `plotly`

```python
import plotly.express as px

palette = {"cloud": "#1f77b4", "hardware": "#d62728", "services": "#2ca02c"}

fig = px.line(
    monthly,
    x="month",
    y="revenue",
    color="segment",
    color_discrete_map=palette,
    markers=True,
    title="Cloud overtook hardware as Acme's largest segment in FY2022",
    labels={"month": "", "revenue": "Quarterly revenue ($bn)"},
)

fig.update_layout(
    template="plotly_white",
    title_x=0,
    legend_title_text="",
    legend=dict(orientation="h", y=-0.15),
    margin=dict(t=70, l=40, r=20, b=80),
)
fig.update_traces(hovertemplate="%{y:.1f} $bn (%{x|%b %Y})<extra></extra>")
fig.add_annotation(
    x="2022-04-01", y=monthly.query("segment == 'cloud' and month == '2022-04-01'")["revenue"].iloc[0],
    text="Cloud overtakes hardware",
    showarrow=True, arrowhead=2, ax=0, ay=-30,
)

fig.write_html("revenue_by_segment.html", include_plotlyjs="cdn")
```

Notes:
- The hover template is explicitly designed; the default is rarely the right one.
- An on-chart annotation calls out the inflection point so the headline is visible *before* any hover.
- `include_plotlyjs="cdn"` keeps the file small (the Plotly bundle is loaded from a CDN). Use `"directory"` or `True` if offline embedding is required.

### Tier 3 — Vega-Lite, declarative JSON spec

```javascript
// chart.js
import vegaEmbed from "vega-embed";

const spec = {
  $schema: "https://vega.github.io/schema/vega-lite/v5.json",
  description: "Quarterly revenue by segment, FY2015-FY2024",
  data: { url: "monthly_revenue.json" },
  width: "container",
  height: 360,
  mark: { type: "line", point: true, strokeWidth: 2 },
  encoding: {
    x: { field: "month", type: "temporal", title: null },
    y: { field: "revenue", type: "quantitative", title: "Quarterly revenue ($bn)" },
    color: {
      field: "segment",
      type: "nominal",
      scale: {
        domain: ["cloud", "hardware", "services"],
        range: ["#1f77b4", "#d62728", "#2ca02c"],
      },
      legend: { orient: "bottom", title: null },
    },
    tooltip: [
      { field: "month",   type: "temporal",     title: "Quarter", format: "%b %Y" },
      { field: "segment", type: "nominal",      title: "Segment" },
      { field: "revenue", type: "quantitative", title: "Revenue ($bn)", format: ".1f" },
    ],
  },
  config: {
    background: "white",
    view: { stroke: null },
    title: { fontSize: 14, fontWeight: "bold", anchor: "start" },
  },
  title: {
    text: "Cloud overtook hardware as Acme's largest segment in FY2022",
    subtitle: "Quarterly revenue, $bn (Acme 10-K filings)",
    subtitleColor: "#555",
  },
};

vegaEmbed("#chart", spec, { actions: false });
```

```html
<!-- index.html -->
<div id="chart" style="max-width: 720px; margin: 0 auto;"></div>
<script type="module" src="./chart.js"></script>
```

Vega-Lite is the fastest path from a JSON data file to a polished, interactive chart. The full chart is described declaratively; tooltips and hover are built in.

### Tier 3 — Observable Plot, JS grammar of graphics

```javascript
// chart.js
import * as Plot from "@observablehq/plot";

const data = await fetch("monthly_revenue.json").then((r) => r.json());

const palette = { cloud: "#1f77b4", hardware: "#d62728", services: "#2ca02c" };

const chart = Plot.plot({
  width: 720,
  height: 360,
  marginLeft: 50,
  marginBottom: 50,
  x: { label: null, type: "time" },
  y: { label: "Quarterly revenue ($bn)", grid: true },
  color: { domain: Object.keys(palette), range: Object.values(palette), legend: true },
  marks: [
    Plot.lineY(data, { x: (d) => new Date(d.month), y: "revenue", stroke: "segment", strokeWidth: 2 }),
    Plot.dot(data,   { x: (d) => new Date(d.month), y: "revenue", fill: "segment", r: 3 }),
    Plot.ruleY([0]),
    Plot.text(
      data.filter((d) => d.month === "2022-04-01" && d.segment === "cloud"),
      { x: (d) => new Date(d.month), y: "revenue", text: () => "Cloud overtakes hardware", dy: -12, fontSize: 11 }
    ),
  ],
});

document.getElementById("chart").append(chart);
```

Observable Plot is concise, ergonomic, and yields SVG that downstream CSS or JS can style further. Good first stop after Vega-Lite when more programmatic control is needed.

### Tier 3 — D3.js, low-level control

```javascript
// chart.js
import * as d3 from "d3";

const data = await d3.json("monthly_revenue.json");
const parseDate = d3.utcParse("%Y-%m-%d");
data.forEach((d) => { d.month = parseDate(d.month); d.revenue = +d.revenue; });

const segments = Array.from(new Set(data.map((d) => d.segment)));
const series = d3.group(data, (d) => d.segment);

const width = 720, height = 360;
const margin = { top: 60, right: 24, bottom: 40, left: 56 };

const x = d3
  .scaleUtc()
  .domain(d3.extent(data, (d) => d.month))
  .range([margin.left, width - margin.right]);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(data, (d) => d.revenue)]).nice()
  .range([height - margin.bottom, margin.top]);
const color = d3.scaleOrdinal()
  .domain(segments)
  .range(["#1f77b4", "#d62728", "#2ca02c"]);

const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]).attr("width", "100%");

svg.append("text")
  .attr("x", margin.left).attr("y", 24)
  .attr("font-weight", "bold").attr("font-size", 14)
  .text("Cloud overtook hardware as Acme's largest segment in FY2022");
svg.append("text")
  .attr("x", margin.left).attr("y", 42).attr("fill", "#555").attr("font-size", 11)
  .text("Quarterly revenue ($bn)");

svg.append("g")
  .attr("transform", `translate(0,${height - margin.bottom})`)
  .call(d3.axisBottom(x).ticks(8).tickSizeOuter(0));
svg.append("g")
  .attr("transform", `translate(${margin.left},0)`)
  .call(d3.axisLeft(y).ticks(6))
  .call((g) => g.select(".domain").remove())
  .call((g) => g.selectAll(".tick line").clone()
    .attr("x2", width - margin.left - margin.right)
    .attr("stroke", "#eee"));

const line = d3.line()
  .x((d) => x(d.month))
  .y((d) => y(d.revenue))
  .curve(d3.curveMonotoneX);

for (const [segment, rows] of series) {
  svg.append("path")
    .datum(rows.sort((a, b) => a.month - b.month))
    .attr("fill", "none")
    .attr("stroke", color(segment))
    .attr("stroke-width", 2)
    .attr("d", line);
  svg.append("text")
    .datum(rows[rows.length - 1])
    .attr("x", (d) => x(d.month) + 4)
    .attr("y", (d) => y(d.revenue))
    .attr("dy", "0.35em")
    .attr("fill", color(segment))
    .attr("font-size", 11)
    .text(segment);
}

document.getElementById("chart").append(svg.node());
```

Notes on D3:
- D3 is a *toolbox*, not a chart library. Every chart is built from scales, axes and shape generators.
- Direct labels at the line's end replace a separate legend.
- Cloned tick lines turn axis ticks into faint background gridlines; this is a common D3 pattern for non-intrusive grids.

### Tier 3 — Scrollytelling with Scrollama.js

A scrollytelling page uses regular DOM scroll plus a small library to detect when each "step" enters the viewport, then triggers a transition on a sticky chart pinned in the layout.

```html
<!-- index.html -->
<article class="scrolly">
  <figure class="scrolly-graphic">
    <div id="chart"></div>
  </figure>
  <div class="scrolly-steps">
    <section class="step" data-step="1">
      <h2>Step 1: Cloud is small but growing</h2>
      <p>...</p>
    </section>
    <section class="step" data-step="2">
      <h2>Step 2: Hardware peaks in 2018</h2>
      <p>...</p>
    </section>
    <section class="step" data-step="3">
      <h2>Step 3: Cloud overtakes in 2022</h2>
      <p>...</p>
    </section>
  </div>
</article>
<script type="module" src="./scroller.js"></script>
```

```css
/* scrolly.css */
.scrolly { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.scrolly-graphic { position: sticky; top: 10vh; height: 80vh; margin: 0; }
.scrolly-steps .step { min-height: 80vh; padding: 4rem 0; }
@media (max-width: 720px) {
  .scrolly { grid-template-columns: 1fr; }
  .scrolly-graphic { height: 60vh; top: 20vh; }
}
```

```javascript
// scroller.js
import scrollama from "scrollama";
import { renderChartForStep } from "./chart.js";

renderChartForStep(0);

scrollama()
  .setup({
    step: ".scrolly-steps .step",
    offset: 0.5,
    debug: false,
  })
  .onStepEnter(({ element }) => {
    const step = +element.dataset.step;
    renderChartForStep(step);
  });
```

Conventions, distilled from current editorial practice:

- **One idea per step.** Each `<section class="step">` says one thing; the chart updates to one new state.
- **Story works on the y-axis.** Down the page is the dominant reading direction; left-right interactive controls are secondary.
- **Sticky figure.** The chart stays pinned while text scrolls past, so the reader can compare consecutive states.
- **Static fallback.** Every step should have a printable, screenshot-able fallback. If the story collapses without the interaction, redesign.
- **Performance budget.** Mobile readers on cellular networks are the binding constraint. Lazy-load assets, prefer SVG over canvas where feasible, prefer CSS transitions over per-frame redraws.
- **Accessibility.** Each step's text should be readable as a normal article without scrolling-triggered animation.

### A note on Svelte and React

For a single article-style scrollytelling piece, the vanilla JS pattern above is enough. For larger projects (multiple charts, shared state, reusable components, design-system integration), wrap the chart code in components.

Svelte is popular in editorial data-viz teams: small bundles, scoped CSS, and a reactive store model that fits the "data changes → chart re-renders" pattern. React is the default in product teams; a chart component takes its data as props and re-renders on prop change. The choice rarely affects the chart's *content*; it affects the surrounding application code.

## Maps in JavaScript

Two main paths:

1. **Vector + D3** for editorial maps. Use `topojson-client` to load compact map files; `d3-geo` to project; SVG paths with click and hover. Best when the map is part of a custom-designed editorial chart.
2. **Tile-based with Mapbox GL JS / MapLibre GL JS** for pan-and-zoom maps. Best when the reader needs to navigate the map (zooming into a city, panning across a region) rather than read it as a single composed chart.

Conventions for editorial maps in JS:

- **Pre-process geo data** in Python (with `geopandas`) to a small `topojson` file. The browser should not parse a full shapefile.
- **Disputed borders** rendered with a deliberate convention (dashed outlines, neutral fill, explicit labels). Set the convention once for the whole project.
- **Choropleth + tooltip + cartogram alternative.** When the message is per-capita rates, consider a hex-tile or population-cartogram alternative — JS makes both easy.
- **Mobile.** Test the map at 360px wide; many newsroom maps live or die on phone screens.

## Performance budget

Interactive web visualization runs in the reader's browser, often on a phone, often on a slow connection. A working budget:

- **Bundle size.** Aim for the chart's JS + CSS to fit in a few hundred KB compressed. Vega-Lite's full bundle is large; ship the embed-only build, or pre-render to SVG server-side. D3's modular structure (only import what you use) is your friend.
- **Data file size.** A few hundred KB is usually fine; a few MB is a smell. Pre-aggregate in Python; ship only the resolution the chart needs.
- **First paint.** The static "hero" frame should be visible within ~1 second on a typical mobile connection. Lazy-load anything more.
- **Animation cost.** Animating SVG with hundreds of elements is fine; thousands often is not. Switch to canvas, or pre-render frames, when SVG runs out.

## Build, embed, deploy

For a small editorial piece, a build is barely required: a single `index.html`, a JS file, a CSS file, and a JSON data file dropped into a static host (S3/CloudFront, Netlify, Vercel, GitHub Pages) is enough. Use a bundler (Vite for development; ESBuild or Rollup for production) when:

- Multiple JS modules and dependencies are involved.
- TypeScript or JSX needs compiling.
- The piece is part of a larger publication with a shared design system.

Embed in a CMS via an `<iframe>` or via the publication's chart-embed mechanism. Either way:

- **Set explicit dimensions** on the iframe; charts that resize awkwardly inside iframes are a familiar source of bugs.
- **Provide a static fallback image** for syndication, social previews and AMP variants.
- **Strip analytics from the embed** unless you need them, to keep the bundle small and the privacy footprint clean.

## An interactive-and-JS checklist

Before shipping an interactive or JS-based visualization, verify:

- [ ] The interactivity earns its cost: detail, exploration, or scrollytelling — not "because we could."
- [ ] The static screenshot of the default state delivers the headline finding.
- [ ] The Python → JSON → JS handoff is reproducible and the JSON file is small.
- [ ] The chart works on a 360px-wide phone, on a slow connection, and in grayscale screenshot.
- [ ] Color, scale, annotation and ethics conventions from this skill are applied — the JS code is the *vehicle*, not a license to deviate.
- [ ] Disputed borders, projection choices, and any politically sensitive map decisions are deliberate.
- [ ] Bundle and data sizes fit a reasonable mobile-first budget.
- [ ] Tooltips contain *additional* information; they do not hide *essential* information.
- [ ] Accessibility: keyboard navigation works, color is never the sole encoding, alt text is provided.
- [ ] A static fallback image exists for social previews, syndication, and accessibility.
