#!/usr/bin/env bash
# Install the upstream skills this repo does not carry, as listed in skills.lock.json.
# Usage: scripts/install-upstream.sh [--dry-run] [skill-name ...]   (no names = all)
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
lock="$root/skills.lock.json"
dry_run=0
names=()
for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=1 ;;
    -h | --help) sed -n '2,3p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) names+=("$arg") ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

commands="$(python3 - "$lock" "${names[@]+"${names[@]}"}" <<'PY'
import json
import sys

lock = json.load(open(sys.argv[1], encoding="utf-8"))
wanted = set(sys.argv[2:])
known = {entry["name"] for entry in lock["skills"]}
if wanted - known:
    sys.exit("unknown skill(s): " + ", ".join(sorted(wanted - known)))
for entry in lock["skills"]:
    if not wanted or entry["name"] in wanted:
        print(entry["install"])
PY
)"

while IFS= read -r cmd; do
  [ -n "$cmd" ] || continue
  echo "+ $cmd"
  if [ "$dry_run" -eq 0 ]; then
    bash -c "$cmd"
  fi
done <<< "$commands"
