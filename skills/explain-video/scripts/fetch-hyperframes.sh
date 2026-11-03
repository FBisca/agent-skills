#!/usr/bin/env bash
# Fetch the HyperFrames v0.8.184 workflow pieces explain-video is built on (Apache-2.0, heygen-com/hyperframes).
# Usage: fetch-hyperframes.sh [target-dir]   (default: ${XDG_CACHE_HOME:-$HOME/.cache}/hyperframes-0.8.184)
set -euo pipefail
version="0.8.184"
target="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/hyperframes-$version}"
if [ ! -d "$target/.git" ]; then
  git clone --quiet --depth 1 --branch "v$version" https://github.com/heygen-com/hyperframes "$target"
fi
echo "export HYPERFRAMES_SKILLS_DIR=\"$target/skills\""
