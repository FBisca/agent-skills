#!/usr/bin/env bash
# One quality gate for local work and CI. Install requirements-dev.txt first.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
printf '%s\n' '== Python lint'
python3 -m ruff check .
printf '%s\n' '== Skill frontmatter'
python3 scripts/lint_skills.py
printf '%s\n' '== Tests'
scripts/run-tests.sh
