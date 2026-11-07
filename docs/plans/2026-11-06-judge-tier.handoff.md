# Handoff — judge tier + one-shot review

**For:** the agent implementing `docs/plans/2026-11-06-code-driven-orchestrator.plan.md`.
**Date:** 2026-11-06. **Written by:** a design session that wrote no code and changed no plan.

Read the plan first; this document does not repeat it.

## Where things stand

- Merged: T1 (#9, `d94c780`), T2 (#10, `e498a1b`). T3 is in flight, uncommitted, in `~/developer/agent-skills.worktrees/cdo-t3` (`orchestrate.py`, `tests/fixtures.py`, `tests/test_gates.py`). `cdo-t4` exists but is empty.
- Live run dir + ledger: `~/.local/state/orchestrate/code-driven-orchestrator/`.
- The plan now carries **D13** (versioned JSON handoffs validated in `skills/orchestrate/scripts/contracts.py`).

## Already built — do not rebuild

T2 already ships the one-shot reviewer: one review per ticket, paths-only packet (`Driver.review_text`), `review.json` with `verdict`/`major[]`/`deferred[]`, non-blocking findings to `<run>/deferred.md`, fix rounds gated by converge alone. See `step_reviewed`, `review_text`, `fail_gate` in `skills/orchestrate/scripts/orchestrate.py`.

## Proposed in that session — NOT approved, NOT implemented

The user was asked and did not approve. Options, not instructions.

### 1. Judge tier (lands in T4) — replace the S11 fixed menu

- **Problem:** the menu `{retry, retry one class up, fresh worker, mark blocked, skip, ask user}` has no action for *"the work was fine, the plan was wrong."* S4 (the plan edited mid-run) and a downstream brief invalidated by an upstream interface change both collapse into `ask user`, spending the user's attention on something a judge could settle in one turn.
- **Shape:** code-owned durable wake-queue (zero tokens) → wake-scoped judge (fresh, small packet) → `decision.json` validated by code on **effects, not vocabulary**. A menu only for irreversible/authority-bearing actions and retry budgets.
- **Continuity without context growth:** a script-written `digest.md` (plan status table, ledger slice, unresolved decisions, last N events, the ticket's scenarios), regenerated each wake. Identity and contract persist; the window does not.
- **Invariant:** one active judgment per unit, serialized like the ledger lock.
- **Plan edits if adopted:** D16 (three tiers: code / wake-scoped judge / human), D17 (effects not vocabularies), new scenarios for the wake-queue and digest, T4 rewritten.
- **Reference implementation for the watcher semantics:** `github.com/kunchenguid/firstmate` — `docs/architecture.md`, `bin/fm-watch.sh`. Absorb benign events, suppression markers, bounded rechecks, relaunch attempt budget, and never auto-interrupt or restart. Cost model that decides it: persistent lead = turns × context (grows, this repo's 220M problem); wake-scoped judge = events × small (flat).

### 2. Reviewer packet, three cheap gaps

- **Decision graph:** add active vault decisions to the packet via fleet-brain `brain_decisions` (area filter, `include_superseded=false`, capped, cited by note title). A code-side lookup, not a model step. A diff contradicting an active Decision is the finding a generic reviewer never makes.
- **Rules file:** see §3.
- **Overlap:** the reviewer and `wait-checks` could run concurrently — wall clock becomes max(review, CI), not the sum. Currently S6 → S8 is sequential.

### 3. A reviewer that learns the user's taste (new artifact, no ticket yet)

- `docs/review/rules.md`: rule · why · applies-to · example PR · severity. Loaded into the packet by code, never pasted wholesale.
- `findings.jsonl` records the user's verdict on each finding (accepted / rejected-as-yours / wrong).
- Periodic distillation turns rejected findings into rules; the user approves the rules diff.
- Precedent in this repo: `~/.claude/agents/scene-reviewer.md` — lenses as classes of past notes, the rule pointer wins over the gloss, stop test, "taste without a rule behind it stays out".

## Open issues spotted in the plan — no owner yet

- **D8 vs D12:** D8 says the user merges; D12 says the lead merges. Needs one rule. Precedent (firstmate `AGENTS.md`): green and in-scope may merge autonomously; red, destructive, irreversible, security-sensitive never.
- **D11 cannot fail for the right reason:** it measures the lead tokens the plan deletes. Add total tokens *and* wall-clock per shipped ticket, with a baseline from a run on the same plan.
- **D12 vs S5–S7 and routing.md:** one review per ticket means `review_rounds ≤ 1`, so routing.md's "escalate at two failed review rounds" never fires. Decide the counting rule and rewrite both sides.
- **`big` is a hole:** `check_plan` refuses `Size: big` ("needs chunked dispatch, which `run` does not do"), routing.md promises big → chunked, and no ticket covers chunked dispatch. Either add one or state v1's scope.
- **wait hot-spin:** T1's deferred findings flagged `wait` returning at once with reason `attention` while `unfinished` stays non-empty. Check the current `loop()` for backoff and suppression.
- **Status truth:** the plan's Status column (S3, `set_status` assumes the last column) versus the ledger. Consider ledger as truth with a generated column; deferred findings already flag the column assumption and the ≥9-cell table parsing.
- **Notification gap:** D9 has no push. The driver can sit in `attention.md` unobserved.

## Constraints for any implementing agent

- `~/.claude/CLAUDE.md`: report concisely; delegate Codex via agent-runtime `spawn` with `cli: "codex"`; **no** `Co-Authored-By` or "Generated with" trailer on commits or PRs; model classes — small = haiku, medium = sonnet, large = opus.
- Run directory `~/.local/state/orchestrate/<slug>/` is 0700; files are write-once (later attempts write `.2`, `.3`); handoffs are JSON per D13.
- Red-first: one test per scenario, named with its S-ID.
- Tests: fake `agent-runtime`, `gh`, `wait-checks` executables plus a temp git repo in `skills/orchestrate/tests/`; `converge.py` runs for real.

## Skills for the next session

- `/orchestrate` — dispatch and gate the plan's own tickets.
- `converge` — gate each ticket (`--ticket T<n>`, `--final`).
- `grilling` — sharpen the judge-tier decision before it enters the plan.
- `start-planning` — if the judge tier becomes its own plan.
- `writing-for-agents` — for the digest, packet and rules text.
- `git-commit`, `gh-pr-create` — commits and PRs.
- built-in `code-review` — optional ad hoc PR review (effort levels, `--max-findings`); it is not the driver's reviewer.

## Status in one line

The plan is healthy and executing; the open decision is the judge tier (fixed menu vs wake-scoped judge), and the reviewer's remaining gaps are the decision graph, the rules file, and reviewer‖CI overlap.
