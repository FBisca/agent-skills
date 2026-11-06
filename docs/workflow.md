# Feature workflow

From a raw idea to shipped code. Every step is a skill in [`skills/`](../skills); the ones marked *user* need the user in the session. Steps marked *user-invoked* never start on their own: each hand-off names the next command.

Evidence levels: none of the source methods has an RCT; "adoption" means widely used, not proven. The findings below come from two backtests on shipped features: one on PRD-writing methods, one on this pipeline.

## Which door

| You have | Start at |
|---|---|
| A raw idea, nothing written | 1. `/idea-frame` |
| A decided feature with sources (a request, an RFC, a kickoff) | 2. `/idea-answer` (it creates the folder with `entry: decided`) |
| A PRD already | 6. `/start-planning` |
| A small fix with no product question | `/diagnosing-bugs` (an upstream skill, see [`skills.lock.json`](../skills.lock.json)) directly |

## The steps

| # | Step | Skill | Who | What it does | Based on |
|---|---|---|---|---|---|
| 1 | Frame + kill cheaply | `/idea-frame` (user-invoked) | user + agent | Grills the user with seed questions; facts are looked up, never asked; an answer the user can't know becomes `Source: unknown` and a row in the map. Writes the idea folder in the vault (`$VAULT_DIR`): `frame.md` (grilling notes) and `assumptions.md`, the map of questions that change the build (`id | assumption | if wrong | owner | source | test | result`). Gate 1 in the index note: kill, reshape or continue; the proposer decides alone below appetite, the decider above. `idea_check.py --gate 1` must pass. | Heilmeier catechism (DARPA); internal FAQ from Working Backwards PR/FAQ (Bryar & Carr 2021); assumption mapping (Bland & Osterwalder 2019; Torres 2021); Stage-Gate (Cooper); appetite from Shape Up (Singer 2019); the `grilling` skill |
| 2 | Ask what changes the build | `/idea-answer` (user-invoked) | user, with owners | Every open row goes to the owner who can answer it (finance, compliance, operator/user, decider; engineering rows are looked up in code). No pick, no cap. Prepares each conversation; the user or a teammate asks; answers land in `answers.md` with owner, date, link, summary. Each row closes `confirmed`, `killed`, `changed: <what>` or `accepted by <role>: <reason>; revisit: <trigger>`. Outreach is drafted only after the user's yes; the user sends it. | The Mom Test (Fitzpatrick 2013), for user behaviour only; assumption tests (Torres 2021); routing to owners comes from the discovery backtest |
| 3 | Brief | inside `/idea-answer` | user + stakeholders | `Brief.md`, 1-2 pages: problem and who has it, observable success, appetite, solution sketch, no-gos, open questions with owners and answers, `## Terms`. The user publishes it to the shared doc tool; stakeholders comment; it is revised as answers land. | Shape Up pitch (Singer 2019) |
| 4 | Commit | `/cold-read` (user-invoked), then inside `/idea-answer` | decider | Once, on the final Brief: `/cold-read <folder>/Brief.md` has a zero-context reader paraphrase it; the user records `cold-read: pass <sha12>` (or `accepted`) in the index `## Gates`. The decider's `gate2: pass by <role>` rides on their approval of the final Brief, no separate meeting. `idea_check.py --gate 2` must pass. | Stage-Gate (Cooper); Elephant-Goldfish Model's comprehension check (Google 2026, Apache-2.0) |
| 5 | PRD | `/to-spec` (user-invoked) | agent, user fixes | Writes `PRD.md` in the project folder from the final Brief and the answers; open risks listed with owners. The index note moves to `stage: prd`. | Pocock's spec template |
| 6 | Plan | `/start-planning` (calls `grilling`) | user + agent | Gathers sources and settled decisions, grills only what's open, writes WHEN/THEN scenarios, decisions with the rejected option and source, vertical tickets with Paths. One approval. | Spec-driven development (OpenSpec, GitHub Spec Kit, Pocock); EARS-style scenarios; ADRs (Nygard); tracer bullets / vertical slices; ISO/IEC/IEEE 29148 requirement qualities |
| 7 | Build | `/orchestrate` (user-invoked) | agents | One implementer per ticket in its own worktree; each scenario becomes a test that fails first. Each ticket's Tier picks the cheapest model that can finish it: `brief` tickets and large fix rounds go to a cheap model through chunk briefs an Opus planner writes; the ledger records model, effort, review rounds and usage so a tier changes only on evidence. | TDD red-green-refactor; ATDD; Thoughtworks Radar, [blanket frontier model usage](https://www.thoughtworks.com/radar/techniques/blanket-frontier-model-usage) (Caution) |
| 8 | Gate each ticket | `/converge`, fresh-context review | code + agent | `converge` checks every scenario has a test, every changed test carries an ID, the diff stays in Paths. An Opus reviewer that never saw the build checks correctness and conventions. Then PR and merge. | Spec Kit `converge`, OpenSpec `verify`; independent review |
| 9 | Archive | `/orchestrate` + `converge --final` | agent | Scenarios become numbered requirements in the living spec `docs/specs/<area>.md`; tests are renamed to them. | OpenSpec living spec and delta specs |
| 10 | Measure | backtest D extraction | agent + user | After a feature ships, count the product decisions that arrived after its PRD. Baseline 27–32 per feature. | Discovery backtest |

## What the evidence says so far

- **Discovery backtest** (3 shipped production features): no PRD-writing method beat `/to-spec` on its own documents. 72% of the decisions made after the PRD could have been caught before it by asking their owners. The agents' questions already named 56% of them; nobody answered.
- **Idea pipeline backtest v1**: steps 1–3 named 59% of those later decisions (to-spec 40%), mostly by asking more, and routed only 46% to the right owner. FAIL against its 65% / 70% bar.
- **v2**, after adding owner guidance and the 12-item cap: FAIL, and lower. It named 52% (to-spec 40%), but the items that reach people named about 38%, no better than to-spec. Routing fell to 40%, and that metric compares against who *caused* a decision, not who should have been asked, so it can't be read reliably.
- **What stays:** the assumption map, which names 11–19 points more than to-spec in both runs. The simplified flow keeps the map and asks every open row's owner (step 2), cutting the pre-mortem, scoring, top-3, pick and cap: whether owners' answers prevent late decisions needs real conversations, not a backtest.
- **Real trial**: one large feature plus the next raw ideas (at most 5), judged on a fixed date. Keep if median active human time is ≤ 4 h, shipped ideas have ≤ 15 late decisions after the PRD, and at least one owner answer changed a build decision before commitment; no kill quota.

## Where things live

- **Skills:** `skills/<name>/` in this repo, installed as described in the [README](../README.md#install).
- **Ideas, PRDs and plans:** the vault, `$VAULT_DIR/01-projects/<slug>/`: the index note, `frame.md`, `assumptions.md`, `answers.md`, `Brief.md`, `PRD.md`, `plans/`.
- **The folder contract:** the docstring of [`skills/idea-frame/scripts/idea_check.py`](../skills/idea-frame/scripts/idea_check.py).
- **Living specs:** `docs/specs/<area>.md` in the repo that holds the code.
