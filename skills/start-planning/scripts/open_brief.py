#!/usr/bin/env python3
"""Open a plan's brief in Obsidian, when the brief sits inside a vault.

Obsidian opens only files of a vault: a folder holding `.obsidian/`. This script answers
whether the brief is in one, and opens it there through the `obsidian://open` URI.

Usage:
    python3 open_brief.py <brief.md> --check    # is it in a vault?
    python3 open_brief.py <brief.md>            # open it

Exit codes: 0 in a vault (and opened, without --check), 2 not in a vault or no such file.
"""

import argparse
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

OK = 0
NO_VAULT = 2

OPENERS = {"darwin": ["open"], "win32": ["cmd", "/c", "start", ""]}


def vault_of(path):
    """The vault holding the file: its nearest ancestor with `.obsidian/`, or None."""
    for parent in path.parents:
        if (parent / ".obsidian").is_dir():
            return parent
    return None


def uri_for(path):
    return "obsidian://open?path=" + quote(str(path), safe="")


def launch(uri):
    """Hand the URI to the system's opener. The tests answer this function."""
    subprocess.run(OPENERS.get(sys.platform, ["xdg-open"]) + [uri], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Open a brief in Obsidian.")
    parser.add_argument("brief", help="the path to brief.md")
    parser.add_argument("--check", action="store_true", help="only say whether it is in a vault")
    args = parser.parse_args(argv)

    brief = Path(args.brief).expanduser().resolve()
    vault = vault_of(brief) if brief.is_file() else None
    if vault is None:
        print("NO VAULT %s: no ancestor folder holds .obsidian/" % brief, file=sys.stderr)
        return NO_VAULT
    if args.check:
        print("VAULT %s" % vault)
        return OK
    uri = uri_for(brief)
    launch(uri)
    print("OPENED %s" % uri)
    return OK


if __name__ == "__main__":
    sys.exit(main())
