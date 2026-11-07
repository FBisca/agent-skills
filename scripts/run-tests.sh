#!/usr/bin/env bash
# Run the repo contract tests and every skill's unittest suite, each file in its own process.
# The gate for any change here; scripts/run-tests.py is what it runs.
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root" || exit 1

exec python3 -B "$root/scripts/run-tests.py" "$@"
