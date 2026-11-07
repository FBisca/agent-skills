#!/usr/bin/env python3
"""Check that a skill this plan depends on is installed, and say how to install it.

`grilling` is an upstream skill, not vendored here: the plan must never skip the grill
because the dependency was missing. This script answers one question — is the skill
installed, and where — and fails with the install command when it is not.

Usage:
    python3 check_deps.py <skill-name> [--skills-dir DIR ...]

Exit codes: 0 found, 2 missing.
"""

import argparse
import json
import os
from pathlib import Path
import sys

FOUND = 0
MISSING = 2

REPO_ROOT = Path(__file__).resolve().parents[3]
LOCK = REPO_ROOT / "skills.lock.json"


def pi_settings_dirs():
    """The skill directories Pi's own settings add, user level and project level."""
    dirs = []
    agent_dir = Path(os.environ.get("PI_CODING_AGENT_DIR") or (Path.home() / ".pi" / "agent"))
    settings = [agent_dir / "settings.json", Path.cwd() / ".pi" / "settings.json"]
    for path in settings:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for entry in data.get("skills") or []:
            if not isinstance(entry, str) or entry.startswith("!"):
                continue
            base = agent_dir if path.parent == agent_dir else path.parent
            dirs.append(Path(entry).expanduser() if Path(entry).expanduser().is_absolute()
                        else base / entry)
    return dirs


def candidate_dirs(extra=(), only=False):
    """Every directory a skill may be installed in, in the order they are searched."""
    home = Path.home()
    dirs = [Path(item).expanduser() for item in extra]
    if only:
        return dirs
    dirs += [home / ".agents" / "skills", home / ".claude" / "skills",
             Path.cwd() / ".agents" / "skills", Path.cwd() / ".claude" / "skills"]
    dirs += pi_settings_dirs()
    dirs.append(Path(__file__).resolve().parents[2])  # this repo's own skills/
    seen = []
    for directory in dirs:
        if directory not in seen:
            seen.append(directory)
    return seen


def find_skill(name, dirs):
    """The installed skill's path, or None."""
    for directory in dirs:
        candidate = directory / name / "SKILL.md"
        if candidate.is_file():
            return candidate
    return None


def install_command(name):
    """The documented install command for the skill, from the repo's upstream lock."""
    try:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for entry in lock.get("skills", []):
        if entry.get("name") == name:
            return entry.get("install")
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check that a dependency skill is installed.")
    parser.add_argument("name", help="the skill name, e.g. grilling")
    parser.add_argument("--skills-dir", action="append", default=[],
                        help="an extra directory to search (repeatable)")
    parser.add_argument("--only-dirs", action="store_true",
                        help="search only the given directories, not the default ones")
    args = parser.parse_args(argv)

    dirs = candidate_dirs(args.skills_dir, only=args.only_dirs)
    found = find_skill(args.name, dirs)
    if found is not None:
        print("FOUND %s: %s" % (args.name, found))
        return FOUND

    print("MISSING %s" % args.name, file=sys.stderr)
    print("searched:", file=sys.stderr)
    for directory in dirs:
        print("  %s" % directory, file=sys.stderr)
    command = install_command(args.name)
    if command:
        print("install it with:", file=sys.stderr)
        print("  %s" % command, file=sys.stderr)
        print("or: scripts/install-upstream.sh %s" % args.name, file=sys.stderr)
    else:
        print("install it with: npx skills add <source> --skill %s" % args.name, file=sys.stderr)
    return MISSING


if __name__ == "__main__":
    sys.exit(main())
