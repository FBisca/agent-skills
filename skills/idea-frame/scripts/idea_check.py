#!/usr/bin/env python3
r"""Deterministic idea-folder gate (converge-style). This docstring is the idea-folder contract (v2).

Usage: idea_check.py <folder> [--gate 1|2]
Output: one `PASS|FAIL|SKIPPED <check>: detail` line per check. Exit 0 if nothing FAILs, 1 on any FAIL,
2 on `REFUSED <path>: <what>` (not exactly one index note; printed to stdout and stderr, no checks run).

Checks:
  no --gate:  stage-value, gate-reason, hours-logged
  --gate 1:   + question-owners, test-criterion
  --gate 2:   + assumptions-closed, answers-sourced, decider-signoff, brief-read
`entry: decided` skips nothing.
A gate check whose file is absent FAILs (assumptions.md at gate 1 and 2, Brief.md for brief-read).
At a gate, assumptions.md without all seven header columns, or with zero data rows, FAILs every
assumptions-based check (`missing columns: ...` / `no questions recorded`); a row without an id is named `row <n>`.
An absent answers.md has no entries, so answers-sourced PASSes. No other file is checked: frame.md
holds grilling notes only; there is no premortem.md or gates.md.

Folder contract:
- Index note: the ONE root-level `.md` whose frontmatter has `type: project`, titled like the idea
  (`Robo-Doc.md`); assumptions, answers, frame and Brief `.md` are never candidates and their own
  frontmatter is ignored. A BOM is tolerated; directories named `*.md`, non-UTF-8 files and subfolders
  are not candidates. Zero or several candidates is REFUSED. Frontmatter is flat `key: value` lines
  between `---` fences; surrounding quotes on a value are stripped. `stage` is one of framing, gate1,
  answering, gate2, prd, killed, reshaped. `entry` defaults to raw. `decider` is the role who signs gate 2.
- `## Hours` in the index note: lines `- YYYY-MM-DD <label> <n>h`. Past framing (any stage but framing),
  hours-logged needs at least one such line with n > 0; the label is free, no per-stage line is required.
- `## Gates` in the index note (heading case-insensitive, every such section read; gate keywords case-insensitive): lines `- YYYY-MM-DD gate1|gate2: kill|reshape|continue|pass by <role>[: <reason>]`
  and `- YYYY-MM-DD cold-read: pass <sha12>` or `accepted <sha12> by <role>` (bullet `-` or `*`).
  gate-reason: a kill or reshape line needs a non-empty reason, and any line containing `gate1:` or `gate2:`
  that does not fit the grammar above (`killed`, a typo) FAILs.
- assumptions.md: markdown table, header `id | assumption | if wrong | owner | source | test | result`
  (columns matched by name, order free; owner is a free-text role). Cells split on unescaped `|`;
  `\|` stays inside the cell.
  question-owners (gates 1, 2): a row with an empty result needs a non-empty owner; FAIL names the row id.
  test-criterion (gates 1, 2): a non-empty test cell is `<type>: <criterion>`, type (case-insensitive)
  interview, prototype, data, survey or spike, criterion non-empty; an empty test passes.
  assumptions-closed (gate 2): every result is `confirmed`, `killed`, `changed: <what>` or
  `accepted by <role>: <reason>; revisit: <trigger>` (non-blank role; case-insensitive); anything else FAILs naming the row.
- answers.md: entries are `## ` sections. answers-sourced (gate 2): each entry needs a non-empty `Owner:`,
  a `Date:` that is a real YYYY-MM-DD no later than today, a non-empty `Link:` and a non-empty
  `Summary:`; FAIL names the entry (its first heading word).
- decider-signoff (gate 2): the LATEST `gate2` line in `## Gates` is `pass by <role>`, role equal to the
  index `decider` (case-insensitive), and no kill or reshape line (any gate) comes after it.
- brief-read (gate 2): `Brief.md` (exact filename) exists, has a `## Terms` section, and the LATEST `cold-read:` line is
  `pass <sha12>` or `accepted <sha12> by <role>` (non-empty role), sha12 = the first 12 hex of the sha256
  of the Brief's UTF-8 text without frontmatter, stripped of surrounding whitespace. Else FAIL naming
  the current sha12.
"""
import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

VALID_STAGES = ["framing", "gate1", "answering", "gate2", "prd", "killed", "reshaped"]
COLUMNS = ("id", "assumption", "if wrong", "owner", "source", "test", "result")
TEST_TYPES = ("interview", "prototype", "data", "survey", "spike")
SIDE_FILES = {"assumptions.md", "answers.md", "frame.md", "brief.md"}  # compared lowercased
GATE_LINE = re.compile(
    r"^\s*[-*]\s+\d{4}-\d\d-\d\d\s+gate([12]):\s*(kill|reshape|continue|pass by [^:]+?)\s*(?::\s*(.*?))?\s*$", re.I)
COLD_LINE = re.compile(r"^\s*[-*]\s+\d{4}-\d\d-\d\d\s+cold-read:(.*)$")
HOURS_LINE = re.compile(r"^\s*[-*]\s+\d{4}-\d\d-\d\d\s+\S+\s+(\d+(?:\.\d+)?)h\b", re.M)
CLOSED = re.compile(r"confirmed|killed|changed:\s*\S.*|accepted by\s+[^:;\s][^:;]*:\s*[^;\s][^;]*;\s*revisit:\s*\S.*", re.I)


def load(path):
    """Text of a file (BOM dropped), or None if it is not a readable UTF-8 file."""
    try:
        return path.read_text(encoding="utf-8-sig") if path.is_file() else None
    except (UnicodeDecodeError, OSError):
        return None


def read(folder, name):
    """A side file's body: its own frontmatter is never read by any check."""
    text = load(Path(folder) / name)
    return text if text is None else re.sub(r"\A---\s*\n(?:.*?\n)?---[ \t]*\n?", "", text, count=1, flags=re.S)


def frontmatter(text):
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, sep, v = line.partition(":")
        if sep:
            out[k.strip()] = v.strip().strip("\"'")
    return out


def sections(text):
    """[(heading, body)] for each `## ` section."""
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = [line[3:].strip(), []]
            out.append(cur)
        elif cur:
            cur[1].append(line)
    return [(h, "\n".join(b)) for h, b in out]


def section(text, name):
    """Body of every `## <name>` section (heading case-insensitive), joined; None when there is none."""
    bodies = [b for h, b in sections(text) if h.lower() == name.lower()]
    return "\n".join(bodies) if bodies else None


def table_rows(text):
    """(header columns, data rows as dicts); columns is None when there is no table."""
    rows, cols = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if cols is None:
            cols = [c.lower() for c in cells]
        elif not all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            rows.append(dict(zip(cols, cells + [""] * (len(cols) - len(cells)))))
    return cols, rows


def result(ok, name, detail=""):
    return (("PASS" if ok else "FAIL"), name, detail)


def check_stage(idea):
    stage = idea.get("stage", "")
    return result(stage in VALID_STAGES, "stage-value", stage or "stage missing")


def check_gate_reason(gates):
    bad = []
    for l in gates.splitlines():
        if re.search(r"gate[12]:", l, re.I):
            m = GATE_LINE.match(l)
            if not m or (m.group(2).lower() in ("kill", "reshape") and not m.group(3)):
                bad.append(l.strip())
    return result(not bad, "gate-reason", "no reason or malformed: " + "; ".join(bad) if bad else "")


def check_hours(idea, hours):
    stage = idea.get("stage", "")
    if stage not in VALID_STAGES:
        return ("SKIPPED", "hours-logged", "invalid stage")
    total = sum(float(h) for h in HOURS_LINE.findall(hours))
    return result(stage == "framing" or total > 0, "hours-logged", f"{total:g}h logged")


def row_names(rows, keep):
    """Ids of the rows keep() selects; a row without an id is named `row <n>` (1-based)."""
    return [r.get("id") or f"row {i}" for i, r in enumerate(rows, 1) if keep(r)]


def check_owners(rows):
    bad = row_names(rows, lambda r: not r.get("result") and not r.get("owner"))
    return result(not bad, "question-owners", "no owner: " + ", ".join(bad) if bad else "")


def check_test_criterion(rows):
    pat = re.compile(r"(?:%s):\s*\S" % "|".join(TEST_TYPES), re.I)
    bad = row_names(rows, lambda r: r.get("test") and not pat.match(r["test"]))
    return result(not bad, "test-criterion", "need `<type>: <criterion>`: " + ", ".join(bad) if bad else "")


def check_closed(rows):
    bad = row_names(rows, lambda r: not CLOSED.fullmatch(r.get("result", "")))
    return result(not bad, "assumptions-closed", "not closed: " + ", ".join(bad) if bad else "")


def field(body, name):
    m = re.search(rf"^\s*{name}:[ \t]*(\S.*?)\s*$", body, re.M | re.I)
    return m.group(1) if m else ""


def real_past_date(value):
    try:
        return datetime.date.fromisoformat(value) <= datetime.date.today() and bool(re.fullmatch(r"\d{4}-\d\d-\d\d", value))
    except ValueError:
        return False


def check_answers(text):
    bad = []
    for head, body in sections(text or ""):
        miss = [f for f in ("Owner", "Date", "Link", "Summary")
                if not (real_past_date(field(body, f)) if f == "Date" else field(body, f))]
        if miss:
            bad.append(f"{head.split()[0] if head else '?'} lacks " + "/".join(miss))
    return result(not bad, "answers-sourced", "; ".join(bad))


def check_signoff(gates, decider):
    lines = [m for m in map(GATE_LINE.match, gates.splitlines()) if m]
    last = max((i for i, m in enumerate(lines) if m.group(1) == "2"), default=None)
    head = lines[last].group(2) if last is not None else ""
    role = head[len("pass by "):].strip() if head.lower().startswith("pass by ") else ""
    ok = bool(decider) and role.lower() == decider.lower() and not any(
        m.group(2).lower() in ("kill", "reshape") for m in lines[last + 1:])
    return result(ok, "decider-signoff", f"need latest gate2 `pass by {decider or '<decider>'}`" if not ok else "")


def check_brief(brief, gates):
    if brief is None:
        return result(False, "brief-read", "Brief.md missing")
    sha = hashlib.sha256(brief.strip().encode("utf-8")).hexdigest()[:12]
    if section(brief, "Terms") is None:
        return result(False, "brief-read", f"Brief.md has no ## Terms; brief {sha}")
    lines = [m.group(1).strip() for m in map(COLD_LINE.match, gates.splitlines()) if m]
    ok = bool(lines) and re.fullmatch(rf"pass\s+{sha}|accepted\s+{sha}\s+by\s+\S.*", lines[-1], re.I) is not None
    return result(ok, "brief-read", f"brief {sha}" if ok else f"no cold-read pass for brief {sha}")


def find_index(folder):
    """(text, None) of the one root-level .md with `type: project`, else (None, why)."""
    found = []
    for p in sorted(Path(folder).glob("*.md")):
        text = None if p.name.lower() in SIDE_FILES else load(p)
        if text is not None and frontmatter(text).get("type") == "project":
            found.append(text)
    if len(found) != 1:
        return None, (f"{len(found)} index notes" if found else "no index note")
    return found[0], None


def run(folder, gate):
    """Result lines, or a refusal string."""
    text, why = find_index(folder)
    if text is None:
        return why
    idea = frontmatter(text)
    gates = section(text, "Gates") or ""
    out = [check_stage(idea), check_gate_reason(gates), check_hours(idea, section(text, "Hours") or "")]
    if gate >= 1:
        raw = read(folder, "assumptions.md")
        cols, rows = table_rows(raw or "")
        absent = [c for c in COLUMNS if c not in (cols or [])]
        why = ("assumptions.md missing" if raw is None else
               "missing columns: " + ", ".join(absent) if absent else "no questions recorded" if not rows else "")

        def need(name, fn):
            return result(False, name, why) if why else fn()

        out.append(need("question-owners", lambda: check_owners(rows)))
        out.append(need("test-criterion", lambda: check_test_criterion(rows)))
        if gate >= 2:
            out.append(need("assumptions-closed", lambda: check_closed(rows)))
            out.append(check_answers(read(folder, "answers.md")))
            out.append(check_signoff(gates, idea.get("decider", "")))
            has_brief = "Brief.md" in {p.name for p in Path(folder).iterdir()}  # exact name, even on case-insensitive disks
            out.append(check_brief(read(folder, "Brief.md") if has_brief else None, gates))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate an idea folder.")
    ap.add_argument("folder")
    ap.add_argument("--gate", type=int, choices=[1, 2], default=0)
    a = ap.parse_args(argv)
    results = run(a.folder, a.gate)
    if isinstance(results, str):
        msg = f"REFUSED {a.folder}: {results} (need exactly one root-level .md with `type: project`)"
        print(msg)
        print(msg, file=sys.stderr)
        return 2
    for status, name, detail in results:
        print(f"{status} {name}: {detail}".rstrip(": ").rstrip())
    return 1 if any(r[0] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
