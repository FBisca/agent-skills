#!/usr/bin/env bash
# Run every test file of the repo in its own process, in parallel. scripts/run-tests.py is what it runs.
# The gate for any change here; scripts/checks.sh runs the whole gate.
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root" || exit 1

if command -v uv >/dev/null 2>&1; then
  exec uv run python -B "$root/scripts/run-tests.py" "$@"
fi

exec python3 -B "$root/scripts/run-tests.py" "$@"
