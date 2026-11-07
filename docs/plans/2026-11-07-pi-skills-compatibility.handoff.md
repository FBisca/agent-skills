# Handoff: Pi skills compatibility (P1)

**Date:** 2026-11-07
**Repo:** `agent-skills` · **State:** PR https://github.com/FBisca/agent-skills/pull/25 **merged** as `8948b80`; `main` is at that commit and the feature branch (local and remote) is deleted.
**Next session focus:** run the manual acceptance test **T3** — produce and validate a real `start-planning` plan inside Pi with MiniMax M3.1 — then plan P2.

## What is done

P1 **T1 and T2** are implemented, reviewed and merged into `main` (`8948b80`). The plan's ledger marks them `COMPLETE 2026-11-07`; **T3 is still `TO-DO`** and is the only thing left in P1.

Read these instead of this file when you need detail:

- Plan: `docs/plans/2026-11-07-pi-skills-compatibility.plan.md` (decisions, S1–S4, ticket boundaries, adversarial cases)
- Living spec (what landed, known limits): `docs/specs/harness-portability.md`
- The diff: PR #25 (squash-merged into `main` as `8948b80`; the branch is gone, so read the commit and `git show 8948b80` instead of a branch diff)

## The shape of the change

- One authoritative `SKILL.md` per skill, harness-neutral. `skills/start-planning/SKILL.md` states the **Delegation** requirement (no inherited context, bounded, structured result, loud failure) and nothing about how a harness spells its invocation; the per-harness dispatch lives in `skills/start-planning/references/delegation.md`, loaded on demand. The review comment on the skill's invocation line is addressed: no skill body names a harness's invocation syntax any more (enforced by `tests/test_portability.py`).
- A harness with no subagent tool dispatches the fresh-context gather through the adapter the skill ships, `skills/start-planning/scripts/fresh_context.py`: an isolated `pi --print` session (own session dir, no inherited conversation, read-only tools, timeout, scrubbed env) with a strict answer schema. Every failure path exits non-zero, so a plan never continues on evidence the gatherer did not produce. Pi's own subagent extension was evaluated and not used: it is an example that must be installed by hand, and it spawns the same kind of separate process.
- `skills/start-planning/scripts/check_deps.py` finds the separately installed `grilling` or prints the install command and exits non-zero.
- Tests: `tests/test_portability.py` (discovery rules, the shared skills' Claude/Codex contracts, the Markdown plan contract of every tracked plan), `tests/test_pi_discovery.py` (Pi's own loader, offline), `skills/start-planning/tests/` (isolation, timeout, subprocess failure, malformed answer, missing dependency, frozen pre-portability contract).
- `assemble-crew` and `deep-prompt` were invisible in Pi (unquoted `description` with a colon); both descriptions are quoted, and the discovery test now fails if any skill of this repo stops loading in Pi.

## State of the gate

`scripts/run-tests.sh` → 31 test files, 0 failed, ~29s, fully offline (no network, no model, no Pi process in the suite).

One pre-existing failure was fixed in this branch: `tests/test_repo.py` scanned git-ignored local files, so a local `.claude/settings.local.json` made the suite red on `main` before this work.

## T3: the manual acceptance test (not done, needs a person)

T3 is deliberately left manual and is **not** claimed anywhere. To run it:

```bash
cd <the agent-skills checkout>
ls -l ~/.agents/skills/start-planning ~/.agents/skills/grilling     # both linked
python3 skills/start-planning/scripts/check_deps.py grilling        # must print FOUND

cd /path/to/a/scratch/repo
pi --model minimax/MiniMax-M3.1-Flash
#   inside Pi:  /skill:start-planning <the feature to plan>
#   expect: the gather step runs (the Sources table and decisions come from the gatherer,
#           not from the parent session), the grill runs via /skill:grilling, and the plan
#           lands in docs/plans/YYYY-MM-DD-<slug>.plan.md with Status: AWAITING APPROVAL

cd <the agent-skills checkout>
cp <scratch-repo>/docs/plans/<slug>.plan.md docs/plans/
python3 -m unittest discover -s tests -t tests -p "test_portability.py"   # the contract holds
scripts/run-tests.sh
```

MiniMax's M3.1 model id in Pi's catalogue is `MiniMax-M3.1-Flash` (provider `minimax`). The gatherer was already proven against a real MiniMax M3.1 session (schema-valid answer in 12s); what is unproven is the whole `/skill:start-planning` flow end to end.

## What the next agent should know

- **Do not start P2 on your own.** P2 is not planned yet; the next step after T3 is to plan it (`/start-planning`), not to implement it.
- **Known limits, all documented in `docs/specs/harness-portability.md`:** `/orchestrate` still does not run under Pi (plan decision D3 — the driver needs the agent-runtime tools, and `orchestrate.py` must not be touched here); the Pi gatherer has no `bash` by default (live counts need the parent or an explicit `--allow-bash`); `grilling` must be installed separately and the plan refuses to continue without it.
- **Untouched by this branch:** `skills/orchestrate/scripts/orchestrate.py` and the orchestration graph, `agent-runtime`, `dotfiles`.
- **Untracked files in the working tree that are not mine and must stay untracked:** `docs/plans/2026-11-06-code-driven-orchestrator.plan.md`, `docs/plans/2026-11-06-judge-tier.handoff.md`, `docs/plans/2026-11-06-orchestrate-lean-loop.plan.md`, `docs/plans/2026-11-06-orchestrate-smoke.plan.md`, and this handoff file.
- **Review state:** PR #25 was reviewed and merged (`8948b80`). Nothing is pending on the PR; the review thread is closed.

## Suggested skills for the next session

- `/cold-read` on the produced plan, or `converge` (`python3 skills/converge/scripts/converge.py <plan> --final`) once the plan is approved and the work exists — to check the plan against the scenarios.
- `handoff` again when the T3 result is in, so the next hop carries the evidence rather than the description.
- `/start-planning` when P2 is ready to be planned.
