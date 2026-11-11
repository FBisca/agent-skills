# 03 — Data quality and uncertainty

Most analytical errors are quality errors: the data was joined badly, the field meant something else, the survey missed half the population, the model's confidence interval was hidden. The conventions in this file aim to install the habits that catch those errors *before* a chart goes out, and to communicate the uncertainty that remains.

## Look at the raw data first

Before any aggregation, the agent should:

1. **Open the file.** Read the first ten rows. Read the last ten. Read ten random rows. (Numbers feel different at the head and the tail.)
2. **Read the documentation, if any.** If a column called `revenue` does not have a unit in the docs, the unit is unknown.
3. **Run a profile.** A `describe()` / `summary()` / `glimpse()` call, plus per-column null counts, unique-value counts, and value distributions for categoricals. In Python, `pandas.DataFrame.describe(include='all')`, `pandas.DataFrame.isna().sum()`, `df.nunique()`, and a one-line histogram per numeric column. In R, `skimr::skim()` or `summary()` plus `dplyr::glimpse()`.
4. **Sanity-check the totals.** Does the sum of `country` rows match the published global total? Does `month` cover every month or are there gaps? Does the time range match the source's stated range?

Skipping this step in favor of "I'll trust the schema" produces silent errors that survive into charts. The cheapest way to find a wrong column is at the start.

## Audit the schema

For every column the agent will use:

- **What is the unit?** Currency, count, percentage, percentage points, ratio, bytes, seconds, milliseconds. If the column is "monthly active users," is that "users active this month" or "average daily active users this month"? Names lie.
- **What is the time zone?** Especially for event timestamps. UTC, local, "the application's default" are all distinct.
- **What is the null encoding?** `NULL`, empty string, `0`, `-1`, `9999`, `2099-12-31`, `"NA"`, `"unknown"`, a sentinel from a legacy system. All have to be normalized before aggregation.
- **What does each enum value mean?** Especially for categoricals with shifting taxonomies over time (`status` codes, account types, plan tiers, country codes after political changes).
- **What is the grain of one row?** A user-day, a session, a transaction line, a daily snapshot? Aggregations across the wrong grain are an extremely common silent error.

The agent should be able to answer all of these for any column it cites. If it cannot, the analysis is fragile.

## Premature enumeration and the meaning of words

Tim Harford, in *The Data Detective*, names "premature enumeration" — counting a thing before being sure what the thing is. Examples:

- "How many tech jobs were lost?" depends entirely on what counts as a tech job. Definitions vary by source.
- "Crime rate" can mean reported crimes, charged crimes, or convicted crimes — three trends that often diverge.
- "Inflation" can be CPI, core CPI, PCE, or GDP deflator. Choice of measure changes the magnitude and sometimes the sign.
- "Carbon emissions" can be territorial, consumption-based, or per capita. All are legitimate; they answer different questions.

Before reaching for a number, write down:

1. **What is the thing being counted?**
2. **By whom, and over what unit of time and space?**
3. **What does the chosen measure exclude?**

Skip this step and the analysis is built on sand.

## Coverage and survivorship

Two common failures of who is in the data:

- **Coverage.** What populations or events are systematically missing? "Active users" excludes churned ones; "sales" excludes refunds; "successful logins" excludes the locked-out; "patients in the system" excludes those who never sought care. The chart's title should specify the population.
- **Survivorship bias.** When the data only includes the ones that survived a filter, conclusions about "what worked" are unreliable. Studying successful startups tells you what successful startups have in common, not what causes startups to succeed. Abraham Wald's WWII bullet-hole study — armoring planes where the surviving ones were *not* hit — is the canonical example.

Make a habit of asking, before each finding: *what is missing from this dataset, and would it change the answer?*

## "There is no raw data" — re-stated for cleaning

Cleaning is editorial. Each transformation is a choice with a defensible reason. Common choices and the questions they raise:

- **Imputation.** Filling missing values is sometimes safer than dropping rows, and sometimes the opposite. Which one depends on whether missingness is plausibly random or correlated with the outcome. Document the choice.
- **Outlier handling.** "Outliers" are sometimes data entry errors and sometimes the most informative observations. Removing them silently is a choice; clipping or winsorizing is a choice; reporting separately is a choice. Pick one and name it.
- **Joining.** Inner joins drop unmatched rows on either side. Left joins introduce nulls that have to be handled later. Many-to-many joins multiply rows. The agent should be able to predict the row count of every join before running it, and verify after.
- **Type coercion.** Numbers stored as strings, dates parsed by the wrong locale, booleans encoded as `"Y"`/`"N"`/`"True"`/`1`/`-1`. A coercion that fails silently produces nulls; a coercion that succeeds wrongly produces nonsense.
- **Deduplication.** Defining a "duplicate" requires defining identity. Two rows with the same `id` and different `updated_at` may be revisions, not duplicates.

Each of these is a place where the analysis can quietly diverge from what the user thinks they have. The agent should narrate the decisions briefly in the analysis: "Of the 12 million events, we excluded 240,000 with missing user IDs (0.02%, primarily in the first week of data collection)."

## Sanity-check before publishing

Quick checks to run on any aggregated table before turning it into a chart:

- **Row count.** Is it what you expected? An order-of-magnitude surprise is the cheapest signal that something is wrong.
- **Top of the distribution.** Sort descending; is the top row plausible? Common-sense limits beat statistical tests for catching data-entry errors.
- **Bottom of the distribution.** Sort ascending; are negative values legitimate? Are zeros really zeros, or are they nulls?
- **Group totals.** Does the country breakdown sum to the global total? Does the segment breakdown sum to the firm total?
- **Time-series continuity.** Are there gaps where there shouldn't be? Daylight savings, late-arriving data, system outages all create realistic gaps; treat them.
- **Recompute one row by hand.** If the calculation is non-trivial, pick one row and recompute it manually or with an independent query. A single mismatch beats any test suite.

## Premature precision

A number with five significant figures implies five-figure precision. If the underlying measurement is good to two, the extra digits lie. Round outputs to the precision the data supports:

- Survey numbers based on N = 800: round percentages to whole numbers or 0.5.
- Financial estimates from analyst aggregates: round to one decimal at most.
- Modeled forecasts: state the interval; do not report the central estimate to a precision the interval refutes.

In charts, axis labels, callouts and footnotes should match. "$1,234,567" from a model whose error bar is ±$200,000 should be "$1.2m (±$0.2m)."

## Communicating uncertainty

Forecasts, model outputs, polling averages, A/B-test estimates, and survey aggregates all carry uncertainty. A single line on a chart implies false precision. Conventions:

- **Show intervals.** A 50% and 90% credible (or confidence) interval as nested shaded bands around the central estimate is the standard pattern in election and macroeconomic forecasting (e.g., FiveThirtyEight, *The Economist*'s election models, the Bank of England fan charts). Two bands are usually clearer than one.
- **Show constituent observations.** For a polling average, plot the individual polls in the background as faint dots, with the smoothed average and its band on top. The reader sees why the band has the width it does.
- **Mark forecasts visually.** Switch to dashed lines, or split the chart with a vertical "today" rule, beyond which the line becomes a forecast and the shaded band appears.
- **State the level.** "50/90% prediction interval" or "95% confidence interval" should appear in the chart subtitle or footnote. Do not assume the reader knows the convention.
- **Resist over-precision in prose.** Pair point estimates with intervals or with calibrated language ("likely," "more likely than not," "very unlikely") and define those terms once if used.

When uncertainty is large enough to undermine the headline, that is the headline. Don't bury it.

## Models and proxies

When the underlying thing cannot be observed directly, an estimate stands in. Examples:

- Excess deaths during an epidemic (a model on baseline mortality vs. observed).
- Customer lifetime value (a model on retention curves and discounting).
- Political-unrest risk (a model on event databases and structural variables).
- Revealed preference for a product (a proxy via clicks, time-on-page, or repurchase).

Treat every model output as inherently uncertain, and treat every proxy as inherently biased. State both:

- The model's structure in one sentence ("a state-space model on weekly mortality from 2010–2019 baseline").
- The proxy's gap to the underlying thing in one sentence ("clicks measure interest, not satisfaction; the two diverge for unfamiliar UI elements").

## Polls and surveys

Surveys deserve their own caution:

- **Sample size and margin of error** drive the precision; report them.
- **Mode effect.** Phone, web, in-person, panel surveys yield systematically different responses to the same questions. Aggregating across modes without weighting is an error.
- **Question wording.** Two reasonable wordings of the same question can yield 10-percentage-point differences. Quote the wording when it matters.
- **House effects.** Pollsters have systematic leans visible only in pollster-vs-pollster comparison. Average across houses or weight for known biases.
- **Polling averages** smooth noise but lag turning points. Show both the smoothed average and the constituent polls.

These cautions are not about whether to use polls — they are about how to communicate what a poll can and cannot say.

## Speak softly when the evidence is weak

Calibrated language is itself a quality mechanism. A chart with a small effect, a noisy series, or a borderline statistical signal should be accompanied by language that matches the strength.

A practical scale (compatible with the IPCC's likelihood vocabulary, used by climate, intelligence and policy communities):

- "Virtually certain": ≥99%
- "Very likely": ≥90%
- "Likely": ≥66%
- "About as likely as not": 33–66%
- "Unlikely": ≤33%
- "Very unlikely": ≤10%
- "Exceptionally unlikely": ≤1%

The agent does not have to use this scale verbatim, but should not dress a 60% finding in the language of certainty.

## A data-quality checklist

Before publishing an analytical artifact, verify:

- [ ] The schema is understood: units, time zones, null encodings, enum semantics, grain.
- [ ] Cleaning choices (imputation, outliers, joins, deduplication, type coercion) are explicit and defensible.
- [ ] Coverage and survivorship are interrogated; populations missing from the data are named.
- [ ] Sanity checks pass: row counts, group totals, top-and-bottom rows, time continuity, hand-recomputed example.
- [ ] Output precision matches data precision.
- [ ] Forecasts, models, proxies and polls are labeled as such, with intervals or constituent observations shown.
- [ ] Calibrated language matches the strength of the evidence.
