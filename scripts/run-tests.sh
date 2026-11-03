#!/usr/bin/env bash
# Run the repo contract tests and every skill's unittest suite, each in its own process.
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root" || exit 1
failed=0

run_suite() {
  echo "== $1"
  python3 -B -m unittest discover -s "$1" -t "$1" || failed=1
}

run_suite tests
for dir in skills/*/tests; do
  [ -d "$dir" ] && run_suite "$dir"
done

exit "$failed"
