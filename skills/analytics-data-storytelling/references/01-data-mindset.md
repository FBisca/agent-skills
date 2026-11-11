# 01 — Data mindset

Before any chart, before any model, the agent needs a working stance toward data itself. The mistakes most likely to embarrass an analyst — overclaiming, missing what isn't there, mistaking a metric for the underlying thing — are mindset mistakes, not technical ones. The conventions in this file aim to install that mindset.

## Data is empirical evidence, not truth

A dataset is the result of someone deciding what to measure, how to measure it, who to count, and what to ignore. The number that lands in your `data.csv` carries those choices forward silently.

Treat data as **one input** to a decision, alongside reasoning, intuition, qualitative evidence and other sources. Use it to ground arguments, not to settle them. When the data and a stakeholder's intuition disagree, both are evidence; the question is why.

A short test: if a piece of analysis would only be improved by *more data of the same kind*, you are probably treating data as truth. The piece is more often improved by **different** evidence — qualitative interviews, an adversarial dataset, a deliberate effort to disprove the finding.

## Data without thought is decoration

Numbers strung through a deck without an argument are decorative, not analytical. The presence of a chart or a metric does not make a piece data-driven. The defining trait of analytical work is whether the data shifts the conclusion when it changes — not whether a chart is on the page.

Before generating a chart, the agent should be able to finish two sentences:

- "If the data showed X, I would conclude A; if it showed Y, I would conclude B."
- "Without this chart, the reader could still draw conclusion ___, but would miss ___."

If neither sentence has a clear ending, the chart is decorative.

## Easy data, hard data, no data

Not every question can be answered with a spreadsheet. A useful taxonomy:

- **Easy data.** The numbers exist, are accessible, and roughly mean what their column names say. Most operational metrics, financials, and standard public datasets live here.
- **Hard data.** Either the numbers exist but are messy (multiple sources disagree, definitions shift over time, coverage is uneven), or the question requires assembling several imperfect signals.
- **No data.** The thing you want to measure has not been measured, cannot be measured, or has been measured only in proxy form. Recognize this case explicitly. Either change the question, change the method (qualitative interviews, expert elicitation, market signal, modeled estimate with stated assumptions), or commission new data collection.

A common failure is to spend a week fitting models to "easy" data on the wrong question rather than spending a day collecting the right rough data.

## Inferential vs. existential data

Two different jobs:

- **Existential data** answers *what is happening*. Reported counts, prices, totals.
- **Inferential data** answers *why or what's coming next*. Estimates, models, forecasts, A/B-test results, polls.

Both are legitimate; the agent should not present them with the same certainty. Existential data deserves caveats about coverage and measurement. Inferential data deserves caveats about models, assumptions, intervals and the universe being estimated. Mark inferential outputs visually (dashed lines for forecasts, shaded bands for intervals, "modeled" or "estimate" in the chart subtitle).

## Reported vs. revealed data

Asking a population what it does is rarely the same as observing what it does:

- **Reported.** Survey responses, self-reported behaviors, intent statements, NPS, employee surveys.
- **Revealed.** Logs of what people actually did — clicks, purchases, time on page, returns, bounces.

Use both, and treat each with skepticism for the right reasons. Reported data picks up *intent* and is vulnerable to social desirability and recall. Revealed data picks up *behavior* and is vulnerable to instrumentation gaps and proxies. A piece that depends on one of them alone, on a question that needs both, is incomplete.

## There is no such thing as raw data

Every dataset has been shaped before you see it: schemas defined, units decided, missing values coded, outliers pruned (or not), categories collapsed, time zones normalized (or not). "Raw" usually means "the form I received it in," not "the truth."

Make the choices visible. Either:

- In a notebook, work cell by cell and keep the transformations alongside the analysis.
- In a pipeline, name the layers (raw → cleaned → modeled → reported) and write down what changes between them.

If a stakeholder challenges a number, you should be able to walk back from the chart to the source row in seconds. If you cannot, the analysis is not reproducible, no matter how persuasive the chart.

## There is no such thing as clean data

The companion to the previous principle: cleaning is never "done." Real datasets always carry residual noise — encoding glitches, joining mismatches, missing-data masquerades (a `0` that means "missing", a `2099-12-31` that means "unbounded"), schema drift, late-arriving facts.

Budget time for cleaning. Expect 50–90% of an analysis's time to live there. The agent should not be shocked when a "five-minute chart" takes an afternoon; it should be shocked when one doesn't.

## Have an adversarial relationship with your hypothesis

The most common analytical failure is to find the answer you set out to find. Defenses:

- **Pre-register the takeaway.** Write the headline before plotting. If the data don't support it, change the headline, not the data.
- **Look for the chart that would falsify your story.** If you believe sales rose because of a campaign, the falsifying chart is "sales rose just as fast in the segments the campaign didn't reach." Plot that chart first.
- **Welcome the boring answer.** "No effect" and "we can't tell" are valid findings. They are uncomfortable but they are honest.
- **Triangulate.** If a single dataset gives a strong answer, look for an unrelated dataset that would corroborate it. Two weak signals pointing the same way are usually stronger than one strong signal.

## Ask, "for whom does this fail?"

Every metric, model and chart has populations it serves badly. A summary statistic averages over groups; a model trained on one population may underperform on another; a chart designed for a desktop reader may be illegible on a phone for the half of users who read on one.

Routinely ask, before publishing:

- Which subgroup is least well represented in this data?
- Which subgroup is the metric most likely to mismeasure?
- Which audience is the chart hardest to read for?
- What action does this chart imply, and who would be hurt if it were taken on weaker evidence than it suggests?

This question is the operational form of the warnings in Cathy O'Neil's *Weapons of Math Destruction* and Caroline Criado Perez's *Invisible Women*. It belongs in every analytical workflow, not only in fairness audits.

## Observer effects

Measuring a thing changes it.

- **Hawthorne-style effects.** People behave differently when they know they are being observed. Surveys, time-and-motion studies, opt-in panels and announced experiments all carry this risk.
- **Goodhart's Law.** When a metric becomes a target, it ceases to be a good metric. Once a team is rewarded for a number, the number tends to rise without the underlying thing improving. Write down what the metric is *trying to be a proxy for* and audit the proxy regularly.
- **Selection effects.** Who shows up in the dataset is rarely a random sample of the population the dataset is "about." Voluntary surveys, self-selected reviewers, customers who churn before the cohort window, devices that drop offline — all bend the data.

The agent should be able to articulate, for any analysis, the most likely observer effect at work and how it bends the result.

## Distinguish data, information and insight

Three different things:

- **Data.** Rows, columns, cells. The raw input.
- **Information.** Data put in context — definitions, baselines, time windows, comparisons.
- **Insight.** A decision-relevant takeaway that did not exist before the analysis.

A dashboard full of metrics is data. A weekly report with comparisons is information. A finding that changes a stakeholder's plan is insight. The agent's analytical output should aim for the third whenever a decision is in scope; otherwise, name the artifact for what it is.

## Where to find data

When the user asks the agent to "find data" on something, work in this order:

1. **Internal sources first.** The system being analyzed usually has logs, telemetry, application data or CRM exports that beat any external proxy.
2. **Primary public sources.** Statistical offices (BLS, Eurostat, ONS, OECD, World Bank, IMF), government data portals, regulators' filings, central-bank releases. These have known methodology and revision histories.
3. **Aggregators that link back to primaries.** Our World in Data, Kaggle's curated datasets, FRED. Useful as discovery tools; cite the underlying primary source.
4. **Subject-matter publications.** Industry research, academic papers, NGO reports. Treat with the methodology lens — read the methods section before the conclusions.
5. **Your own collection.** A short survey, a small scrape, an internal tally. Often the highest-leverage option for an under-served question, with the methodology you choose.

For each source, write down: who collected it, when, with what method, who paid for it, and what its known biases are. If any of those answers is unknown, the source is weaker than it looks.

## A data mindset, summarized

A short list to internalize:

- Data is evidence, not truth.
- "Raw" and "clean" are aspirations, not states.
- Easy data, hard data, no data — pick the right method for which.
- Existential vs. inferential, reported vs. revealed — name which you have.
- Try to disprove the finding.
- Ask who the metric and the chart fail.
- Watch for the observer effect on your own measurement.
- Move from data to information to insight; do not stop at the first.
