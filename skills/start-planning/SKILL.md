---
name: start-planning
description: Create an implementation plan for a feature or initiative. Use when the user wants to plan a feature, start an implementation plan, or says "let's plan X".
---

# Start Planning

## Step 1 — Intake

If the user has not yet provided a clear feature idea or spec, ask:

> What feature or initiative do you want to plan? Give me a brief description — one or two sentences is enough to start.

Wait for the answer before continuing.

---

## Step 2 — Understand the domain context

Before interviewing the user, orient yourself by reading relevant documentation and code. This will help you ask better questions and write a more informed plan.

Do not dump file contents to the user. Use them to ask better questions.

---

## Step 3 — Interview with grill-me

Invoke the `/grill-me` skill now.

Do not move to Step 4 until the interview is over.

---

## Step 4 — Write the plan

Write a plan file to `docs/plans/<feature-slug>.plan.md`.


### What every plan must answer

These are **questions, not section headings**. Choose headings that fit the work. Every plan must make the following five things unambiguous to a reader who has never seen it before:

1. **Why now** — what triggered this work, what breaks without it, what scenario or constraint motivates it.
2. **What changes in the system** — which records, services, agents, files, or contracts shift. Name them.
3. **Locked vs. open** — which design decisions are settled (and the reasoning), which are still being explored. If everything is open, say so explicitly.
4. **How it will be delivered** — the work split into Phases, each independently mergeable with clear goal, deliverables, and definition of done.
5. **How we'll know it worked** — observable behaviour, tests, metrics, or quality gates that distinguish "done" from "not done".

If a plan does not answer all five, it is not finished.

### Rules for Phases

- Each Phase must contain at minimum: **goal**, **deliverables**, **definition of done**. This is what `/plan-worktree-executor` needs to execute it.
- Each Phase must be independently reviewable and mergeable.
- Each Phase must be demonstrable — there is something concrete to show when it lands.
- No Phase may depend on a later Phase in the same plan.
- Prefer 3–6 Phases per plan. If the scope is smaller, 1–2 Phases is fine.
- If the planning requires more than 6 Phases, it is probably too big. Suggest splitting the work into multiple plans.

---

## Step 5 — Confirm and close

After writing the file, tell the user:

1. The full path of the plan file.
2. A one-line summary of each Phase.