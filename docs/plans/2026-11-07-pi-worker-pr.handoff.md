# Handoff: open the PRs and merge them (Pi worker + uv/pytest)

**Date:** 2026-11-07 · **Repos:** `agent-runtime` (`~/developer/agent-runtime`) and `agent-skills`
(`~/developer/agent-skills`) · **State:** all the code is written and green; **nothing is committed, no branch,
no PR**.

## The mission

Turn the two dirty working trees into **two merged PRs**, in this order:

| # | Repo | PR | Content |
|---|---|---|---|
| 1 | `agent-runtime` | `feat/pi-worker` | The Pi worker runtime: the `pi` family spawns, the family-aware scrub, the Pi worker tool set, the spec amendment. |
| 2 | `agent-runtime` | `chore/uv-pytest` | The testing workflow: uv + pytest, the markers, the fast suite, CI on uv. |
| 3 | `agent-skills` | `chore/uv-pytest` | The testing workflow (already in the working tree, uncommitted). |
| 4 | `agent-skills` | `feat/pi-worker-driver` | The driver: `--cli pi`, `--brain-cli`, the Pi model column. |

Do them in that order and merge each as it goes; PR 1 is the one the user actually wants (it unlocks the
Pi worker), PRs 2–4 are the workflow that makes the rest fast.

## What is already done (do not redo it)

**`agent-runtime`** (branch `main`, everything uncommitted in the working tree):

- The Pi worker runtime: `server/profiles.py` (`BUILTINS` gains `pi`, family-aware scrub), `server/hc_tools.py`
  (`pi --print --model … --thinking …`, the role line and `PI_WORKER_PROTOCOL` in the task), `server/host_policy.py`
  (the Pi worker allowlist), `server/mcp_server.py` (the `cli` enum follows `BUILTINS`), the new
  `tests/test_pi_worker.py` (20 tests) and the plan `docs/plans/2026-11-07-pi-worker.plan.md`.
- The spec amendment: `docs/specs/harness-adapters.md` (R178 amended, R188–R191 added, the Coverage rows).
- The README: the pi family, the worker tool set, the local configuration.
- The local configuration (outside the repo): `~/.pi/agent/mcp.json` restored from
  `mcp.json.bak-20261107142405`, and `~/.config/agent-runtime/hosts.json` now lists `"pi"` in the pi host's
  `backends`.
- The testing workflow: `pyproject.toml`, `uv.lock`, `AGENTS.md` (new), `tests/conftest.py` (new), the markers on
  every test file, the new in-process unit suites `tests/test_profiles.py` and `tests/test_host_policy.py`, the
  thread-cleanup fixes in `tests/test_event_wait.py` and `tests/test_mcp_server.py`, `.github/workflows/ci.yml` on
  uv, `.gitignore`.

**`agent-skills`** (branch `main`, everything uncommitted in the working tree):

- The uv + pytest workflow (44 files: `pyproject.toml`, `uv.lock`, `conftest.py`, `AGENTS.md`, `ci.yml`,
  `scripts/checks.sh`, the markers on every test file). It was already in the working tree; it is **not** on
  `origin/main` (`git fetch` confirms `origin/main` is still `dd083da`).
- The Pi driver: `skills/orchestrate/scripts/orchestrate.py` (`--cli pi`, `--brain-cli`, the header-name model
  columns, the skill's own table fallback, the brain tier for the review gates),
  `skills/orchestrate/references/models.md` (new) and `skills/orchestrate/tests/test_pi_backend.py` (new, 8 tests).

## The two landmines

1. **Both trees mix two concerns.** In each repo, split the diff into the feature commit and the workflow commit
   (`git add <paths>`, never `git add -A` for the feature). The file lists are in the tables above.
2. **`agent-skills` has four untracked plan/handoff docs** from the research (`docs/plans/2026-11-06-*.plan.md`,
   `docs/plans/2026-11-07-pi-*.handoff.md`). They are notes, not product: commit them with the driver PR or
   leave them out — but never let `tests/test_repo.py` fail on them (it rejects a literal absolute home path; two of
   them had it and it is now `~/developer`).

## The commands (in order)

```bash
# --- agent-runtime -------------------------------------------------------
cd ~/developer/agent-runtime
git checkout -b feat/pi-worker
git add server/ docs/specs/harness-adapters.md docs/plans/2026-11-07-pi-worker.plan.md \
        tests/test_pi_worker.py tests/test_tools.py tests/test_mcp_server.py tests/test_spawn_cleanup.py README.md
git commit -m "feat(pi): run a worker on the pi family"
git push -u origin feat/pi-worker
gh pr create --title "feat(pi): run a worker on the pi family" --body-file <(cat <<'EOF'
The `pi` family is a built-in worker backend: `pi --print --model … --thinking …` with the task last, the role
line and the report protocol in the task. The provider scrub is family-aware (a pi worker keeps
`MINIMAX_API_KEY` and `PI_*`; a claude or codex worker loses them), and a Pi worker may report and read its
own team but never spawn, stop or resume. R178 is amended and R188–R191 are added.

Tests: `uv run pytest -n 4` (554 passed).
EOF
)

git checkout main && git checkout -b chore/uv-pytest
git add -A   # the rest is the workflow only
git commit -m "chore(testing): run the suite with uv and pytest"
git push -u origin chore/uv-pytest
gh pr create --title "chore(testing): run the suite with uv and pytest" --body "…"

# --- agent-skills --------------------------------------------------------
cd ~/developer/agent-skills
git checkout -b chore/uv-pytest
git add -A   # the workflow: pyproject.toml, uv.lock, conftest.py, AGENTS.md, ci.yml, scripts/, the markers
git commit -m "chore(testing): run the suite with uv and pytest"
git push -u origin chore/uv-pytest && gh pr create --title "chore(testing): run the suite with uv and pytest" --body "…"

git checkout main && git checkout -b feat/pi-worker-driver
git add skills/orchestrate/scripts/orchestrate.py skills/orchestrate/references/models.md \
        skills/orchestrate/tests/test_pi_backend.py
git commit -m "feat(orchestrate): run the workers on pi and the gates on the brain backend"
git push -u origin feat/pi-worker-driver
gh pr create --title "feat(orchestrate): run the workers on pi and the gates on the brain backend" --body "…"
```

Merge each PR when its checks are green (`gh pr merge --squash` unless the repo prefers a merge commit — check
the last merged PRs).

## The gates (run before you push)

```bash
cd ~/developer/agent-runtime && uv run pytest          # the fast suite: 67 passed in ~0.2s
cd ~/developer/agent-runtime && uv run pytest -n 4     # the whole suite
cd ~/developer/agent-skills && bash scripts/checks.sh   # lint + frontmatter + the whole suite (455 passed)
```

## What is still open (not part of the PRs)

- **The live check.** A real Pi worker on MiniMax reporting through the restored MCP registration was never
  run: the previous research verified `pi --print --model minimax/MiniMax-M3.1-Flash "…"` → `PI_OK`, so the
  risk is the registration, not Pi. After PR 1 is merged, try one real spawn.
- **The open PRs #39 (`feat/resume-attention`) and #45 (`feat/worker-session-binding`) in `agent-runtime`** touch
  `server/hc_tools.py`, the same file as PR 1. They are the user's to merge; if either lands first, rebase PR 1
  (`git rebase origin/main`) and check that the `spawn` hunks still apply.
- **The dotfiles commit** that adds a Pi column to `~/.claude/CLAUDE.md` is not needed: the driver falls back to
  `skills/orchestrate/references/models.md`.

## The skills for the next session

- `gh-pr-create` (the skill in `~/.agents/skills/gh-pr-create`) for the PR bodies.
- `git-commit` for the Conventional Commits format.
- `converge` (`python3 skills/converge/scripts/converge.py <plan> --final`) to check a plan against its scenarios
  before the PR: `agent-runtime/docs/plans/2026-11-07-pi-worker.plan.md` and
  `agent-skills/docs/plans/2026-11-07-pi-worker-driver.plan.md`.
