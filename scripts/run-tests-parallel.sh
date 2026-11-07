#!/usr/bin/env bash
# Run every skill's unittest suite in parallel, one process per test file.
# The CI gate is scripts/run-tests.sh; this is the fast local gate (same tests, same assertions).
set -uo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root" || exit 1
jobs="${JOBS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)}"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
list="$work/list"
: > "$list"

for dir in tests skills/*/tests; do
  [ -d "$dir" ] || continue
  for file in "$dir"/test_*.py; do
    [ -e "$file" ] || continue
    printf '%s %s\n' "$dir" "$(basename "$file")" >> "$list"
  done
done

echo "== $(( $(wc -l < "$list") )) test files on $jobs workers"

run_file() {
  dir="$1"; file="$2"
  python3 -B -m unittest discover -s "$dir" -t "$dir" -p "$file"
}
export -f run_file

xargs -P "$jobs" -n 2 sh -c 'run_file "$0" "$1"' < "$list"
status=$?

if [ "$status" -ne 0 ]; then
  echo "== some test files failed (xargs status $status)"
fi
exit "$status"
