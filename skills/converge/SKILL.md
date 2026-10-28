---
name: converge
description: Deterministic gate that checks a ticket or a whole plan against its scenarios, tests and Paths. Use when the user says "converge", or asks whether a ticket or plan is really done, or before marking a ticket COMPLETE or archiving a plan.
---

# Converge

**Input:** an approved plan file (`*.plan.md`), a repo with the work done, and one ticket (`T<n>`) or the whole plan.
**Output:** one PASS / FAIL / SKIPPED line per check; exit 0 only if nothing FAILs.
**Hand-off:** all PASS means the caller may mark the ticket COMPLETE (with `--final`: archive the plan). Any FAIL means not COMPLETE: fix, then rerun. This gate is deterministic: for an AI review of gaps (missing, partial, contradicts, unrequested), use `orchestrate`.

## What it reads

- **Plan header:** `Slug: \`<slug>\``, and `Status:` anywhere on a line. "Approved" means the first word after `Status:` is `APPROVED`.
- **Scenario lines:** `- **S<n>** WHEN …, THEN …` (also `S2a`). These are the IDs to cover.
- **`## Tickets` table:** IDs `T<n>`; `Satisfies` (comma lists, or ranges like `S1–S9` expanded over declared IDs in order); `Paths` (comma-separated repo-relative files, globs, or directories ending `/`).
- **Living specs** `docs/specs/<area>.md`: one line `Paths: src/area/, tests/area/**` (backticks allowed around items), and requirement lines `- **R4** WHEN …, THEN … (from <slug>/S3)`.
- **Tests:** a scenario test carries its ID in the name (`test_S3_…`, `it('S3 …')`). A requirement test carries `<area>/R<n>` (`<area>` = spec file name) in the name or, in Python, on the docstring's first text line (the opening-quote line, or the next non-empty line when that one is empty). A bare `R<n>` does not count.

A plan that is not approved, has no scenario lines, or has no `## Tickets` table with rows is refused before any check: `REFUSED <plan>: <what is missing>`, exit 2. Fix the plan; there is no bypass.

## Run

```
python3 <this skill>/scripts/converge.py <plan.md> --ticket T3 [--base <ref>] [--repo <path>]
python3 <this skill>/scripts/converge.py <plan.md> --final    [--base <ref>] [--repo <path>]
```

One of `--ticket` / `--final` is required. `--base` defaults to the ref `origin/HEAD` points to, else `main`. "Changed" means commits since base, plus the working tree, plus untracked files.

- `--ticket`: coverage on that ticket's Satisfies, scope on that ticket's Paths; the spec check prints SKIPPED.
- `--final`: all scenarios, all tickets' Paths, and the spec co-change check. Run it before archive. A scenario renamed at archive still counts as covered when a test carries `<area>/R<m>` and that spec line records `(from <slug>/S<n>)`. A bare `S<n>` test counts only if it was added or changed since base, so old tests from other plans can't cover this one.

## Reading the result

- `FAIL coverage: S4, S7`: no test is named with those IDs. Write the test **red first** (written and seen failing before the code that makes it pass), or fix a wrongly named one.
- `FAIL tagged: test_x`: a changed test has no plan S-ID and no `<area>/R<n>`. Rename it, or put the ID on its docstring's first text line.
- `FAIL scope: path/a.py`: a file changed outside the Paths in scope. Revert it, or, if the work truly needs it, have the plan's owner amend Paths. The plan file and spec files are exempt.
- `FAIL spec: auth`: code under the area's `Paths:` changed but `docs/specs/auth.md` did not. Update the spec, then rerun. `<spec> (no parseable Paths: line)` means the spec lacks the one-line `Paths:` form above.
- `PASS …` lines need no action. `SKIPPED spec` is expected without `--final`.

A FAIL blocks COMPLETE. Never edit the script or the plan's IDs to turn a FAIL green.

Limits: a test whose body changed but whose opening line did not is invisible to `tagged`.
