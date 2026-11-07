#!/usr/bin/env bash
# One quality gate for local work and CI. It needs uv (https://docs.astral.sh/uv/): `uv sync` sets the
# environment up, and every command below runs inside it.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

run() {  # run a command in the project environment, with uv when it is there
  if command -v uv >/dev/null 2>&1; then
    uv run "$@"
  else
    "$@"
  fi
}

printf '%s\n' '== Python lint'
run python -m ruff check .
printf '%s\n' '== Skill frontmatter'
run python scripts/lint_skills.py
printf '%s\n' '== Tests'
run python -m pytest -m "" -n auto
