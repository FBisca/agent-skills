#!/usr/bin/env python3
"""Deterministic idea-folder gate (converge-style): structural checks, plus gate 1 / gate 2 checks.

Usage: idea_check.py <folder> [--gate 1|2]
Output: one `PASS|FAIL|SKIPPED <check>: detail` line per check. Exit 0 if nothing FAILs, 1 on any FAIL,
2 on `REFUSED <path>: <what>` (no `idea.md`; printed to stdout and stderr, no checks run).

Checks (no --gate = structural only):
  structural: stage-value, assumption-values, premortem-links, gate-reason, hours-logged
  --gate 1:   structural + frame-sources, unknown-to-assumption, top3-ready
  --gate 2:   gate 1 + assumptions-closed, answers-sourced, decider-signoff
A structural check whose file is absent prints SKIPPED. A gate check whose file is absent FAILs
(gate 1 needs frame.md, assumptions.md, premortem.md; gate 2 also needs answers.md, gates.md).
`entry: decided` + --gate 2: frame-sources, unknown-to-assumption, top3-ready, premortem-links print
SKIPPED; the other checks run.

Contract decisions (files as in the plan's idea-folder table):
- idea.md frontmatter is flat `key: value` lines between `---` fences; surrounding quotes on a value are
  stripped (`stage: "gate1"`). `stage` must be one of
  framing, gate1, answering, gate2, prd, killed, reshaped. `entry` defaults to raw.
- Stage order is framing, gate1, answering, gate2, prd. The completed stages are those strictly before
  the current stage; killed and reshaped complete only framing. `entry: decided` needs no
  framing/gate1 hours. Each completed stage needs a
  `- YYYY-MM-DD <stage> <n>h` line under `## Hours`.
- frame.md: sections `## Q<n> <question>`; each needs `Source: me`, `Source: lookup <link>` or
  `Source: unknown`. The keyword is case-insensitive (`Source: Unknown`); a lookup link is any
  text after `lookup`, spaces allowed (`Source: lookup [[Idea to PRD - PRD]]`).
- assumptions.md: markdown table with header `id | risk | assumption | importance | evidence | owner |
  test | result` (column order free, matched by name). Ids are `A<n>`. risk: value, usability,
  feasibility, viability. owner: operator/user, finance, compliance, decider, engineering.
  importance and evidence: each MUST be exactly high, med or low (an empty or other value FAILs
  assumption-values). Matching is case-insensitive. Empty owner/test/result cells are allowed by
  assumption-values (other checks need them). Cells split on unescaped `|` only; `\|` (Obsidian
  alias `[[note\|alias]]`) stays inside the cell.
- An assumption cites frame question Q<n> when the token `Q<n>` appears in its assumption cell.
- top3-ready: at least 3 assumptions with importance high have a non-empty owner and test.
- assumptions-closed: each high-importance assumption has a non-empty result (`accepted by <role>`
  is a result).
- premortem.md: items are lines starting `-`, `*` or `1.`; each must end `→ PRD: <text>` or `→ A<n>`
  (`->` accepted); trailing punctuation after `A<n>` (`→ A3.`) is allowed. When
  assumptions.md exists, the cited `A<n>` must be an id in it, else FAIL.
- answers.md: entries are `## ` sections; each needs `Owner:`, `Date:`, `Link:` with a value
  (`Summary:` is not checked). At gate 2 a missing answers.md PASSes answers-sourced only when
  nothing was open: no frame question has `Source: unknown` and no high-importance assumption has an
  empty result; otherwise it FAILs.
- gates.md: `- YYYY-MM-DD gate1|gate2: kill|reshape|continue|pass by <role>[: <reason>]`; kill and
  reshape need a non-empty reason. decider-signoff needs a `gate2: pass by <role>` line whose role
  equals idea.md's `decider` (case-insensitive).
"""
import argparse
import re
import sys
from pathlib import Path

STAGES = ["framing", "gate1", "answering", "gate2", "prd"]
VALID_STAGES = STAGES + ["killed", "reshaped"]
RISKS = {"value", "usability", "feasibility", "viability"}
OWNERS = {"operator/user", "finance", "compliance", "decider", "engineering"}
LEVELS = {"high", "med", "low"}
GATE_LINE = re.compile(
    r"^\s*[-*]\s+\d{4}-\d\d-\d\d\s+gate([12]):\s*(kill|reshape|continue|pass by [^:]+?)\s*(?::\s*(.*?))?\s*$")


NEVER = 9  # `need` level for structural checks: an absent file is SKIPPED at every gate


def read(folder, name):
    p = Path(folder) / name
    return p.read_text() if p.is_file() else None


def frontmatter(text):
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, sep, v = line.partition(":")
        if sep:
            out[k.strip()] = v.strip().strip("\"'")
    return out


def sections(text, prefix="## "):
    """[(heading, body)] for each `## ` section."""
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith(prefix):
            cur = [line[len(prefix):].strip(), []]
            out.append(cur)
        elif cur:
            cur[1].append(line)
    return [(h, "\n".join(b)) for h, b in out]


def assumptions(text):
    rows, cols = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if cols is None:
            cols = [c.lower() for c in cells]
        elif not all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            rows.append(dict(zip(cols, cells + [""] * (len(cols) - len(cells)))))
    return rows


def completed(stage, entry):
    done = [] if stage not in STAGES else STAGES[:STAGES.index(stage)]
    if stage in ("killed", "reshaped"):
        done = ["framing"]
    return [s for s in done if not (entry == "decided" and s in ("framing", "gate1"))]


def result(ok, name, detail=""):
    return (("PASS" if ok else "FAIL"), name, detail)


def missing(name, file):
    return result(False, name, f"{file} missing")


def high(rows):
    return [r for r in rows if r.get("importance", "").lower() == "high"]


def check_stage(idea):
    stage = idea.get("stage", "")
    ok = stage in VALID_STAGES
    return result(ok, "stage-value", stage or "stage missing")


def check_values(rows):
    bad = []
    for r in rows:
        for col, allowed in (("risk", RISKS), ("owner", OWNERS), ("importance", LEVELS), ("evidence", LEVELS)):
            v = r.get(col, "").lower()
            if (v or col != "owner") and v not in allowed:  # an empty owner is top3-ready's concern
                bad.append(f"{r.get('id', '?')} {col}={r.get(col, '')!r}")
    return result(not bad, "assumption-values", "; ".join(bad))


def check_premortem(text, ids):
    """ids: assumption ids to validate `→ A<n>` against, or None when assumptions.md is absent."""
    bad = []
    for line in text.splitlines():
        if re.match(r"\s*(?:[-*]|\d+[.)])\s+\S", line):
            m = re.search(r"(?:→|->)\s*(?:PRD:\s*\S.*|(A\d+)[.,;!]*)\s*$", line)
            if not m:
                bad.append("no link: " + line.strip()[:60])
            elif m.group(1) and ids is not None and m.group(1) not in ids:
                bad.append(f"{m.group(1)} is not in assumptions.md")
    return result(not bad, "premortem-links", "; ".join(bad))


def parse_gates(text):
    return [m for m in (GATE_LINE.match(l) for l in text.splitlines()) if m]


def check_gate_reason(text):
    bad = [l.strip() for l in text.splitlines()
           if re.search(r"gate[12]:\s*(?:kill|reshape)\b", l)
           and not ((m := GATE_LINE.match(l)) and m.group(3))]
    return result(not bad, "gate-reason", "no reason: " + "; ".join(bad) if bad else "")


def check_hours(idea):
    stage = idea.get("stage", "")
    if stage not in VALID_STAGES:
        return ("SKIPPED", "hours-logged", "invalid stage")
    hours = set(re.findall(r"^\s*[-*]\s+\d{4}-\d\d-\d\d\s+(\w+)\s+[\d.]+h\b", idea["_hours"], re.M))
    need = [s for s in completed(stage, idea.get("entry", "raw")) if s not in hours]
    return result(not need, "hours-logged", "no hours for " + ", ".join(need) if need else "")


def frame_questions(text):
    out = []
    for head, body in sections(text):
        m = re.match(r"(Q\d+)\b", head)
        if m:
            src = re.search(r"^\s*Source:\s*(me|unknown|lookup\s+\S.*?)\s*$", body, re.M | re.I)
            out.append((m.group(1), src.group(1).split()[0].lower() if src else None))
    return out


def check_frame_sources(text):
    bad = [q for q, s in frame_questions(text) if s is None]
    return result(not bad, "frame-sources", "no Source: " + ", ".join(bad) if bad else "")


def check_unknown(text, rows):
    cited = " ".join(r.get("assumption", "") for r in rows)
    bad = [q for q, s in frame_questions(text) if s == "unknown" and not re.search(rf"\b{q}\b", cited)]
    return result(not bad, "unknown-to-assumption", "uncited: " + ", ".join(bad) if bad else "")


def check_top3(rows):
    n = sum(1 for r in high(rows) if r.get("owner") and r.get("test"))
    return result(n >= 3, "top3-ready", f"{n} high-importance assumptions with owner and test (need 3)")


def check_closed(rows):
    bad = [r.get("id", "?") for r in high(rows) if not r.get("result")]
    return result(not bad, "assumptions-closed", "open: " + ", ".join(bad) if bad else "")


def check_answers(text):
    bad = []
    for head, body in sections(text):
        miss = [f for f in ("Owner", "Date", "Link") if not re.search(rf"^\s*{f}:\s*\S", body, re.M)]
        if miss:
            bad.append(f"{head.split()[0] if head else '?'} lacks " + "/".join(miss))
    return result(not bad, "answers-sourced", "; ".join(bad))


def nothing_open(frame, rows):
    unknown = any(s == "unknown" for _, s in frame_questions(frame or ""))
    return not unknown and not [r for r in high(rows) if not r.get("result")]


def check_signoff(text, decider):
    roles = [m.group(2)[len("pass by "):].strip().lower() for m in parse_gates(text)
             if m.group(1) == "2" and m.group(2).startswith("pass by ")]
    return result(decider.lower() in roles and bool(decider), "decider-signoff",
                  f"need `gate2: pass by {decider or '<decider>'}`")


def run(folder, gate):
    text = read(folder, "idea.md")
    if text is None:
        return None
    idea = frontmatter(text)
    idea["_hours"] = (re.split(r"^## Hours\s*$", text, flags=re.M) + [""])[1].split("\n## ")[0]
    skip_gate1 = gate == 2 and idea.get("entry") == "decided"
    docs = {n: read(folder, n) for n in ("frame.md", "assumptions.md", "premortem.md", "answers.md", "gates.md")}
    rows = assumptions(docs["assumptions.md"] or "")
    ids = {r.get("id", "") for r in rows} if docs["assumptions.md"] is not None else None
    out = [check_stage(idea)]

    def need(name, file, gate_needs, fn):
        if skip_gate1 and name in ("frame-sources", "unknown-to-assumption", "top3-ready", "premortem-links"):
            return ("SKIPPED", name, "entry: decided")
        if docs[file] is None:
            return missing(name, file) if gate >= gate_needs else ("SKIPPED", name, f"{file} absent")
        return fn()

    out.append(need("assumption-values", "assumptions.md", NEVER, lambda: check_values(rows)))
    out.append(need("premortem-links", "premortem.md", 1, lambda: check_premortem(docs["premortem.md"], ids)))
    out.append(need("gate-reason", "gates.md", NEVER, lambda: check_gate_reason(docs["gates.md"])))
    out.append(check_hours(idea))
    if gate >= 1:
        out.append(need("frame-sources", "frame.md", 1, lambda: check_frame_sources(docs["frame.md"])))
        out.append(need("unknown-to-assumption", "frame.md", 1,
                        lambda: check_unknown(docs["frame.md"], rows)))
        out.append(need("top3-ready", "assumptions.md", 1, lambda: check_top3(rows)))
    if gate >= 2:
        out.append(need("assumptions-closed", "assumptions.md", 2, lambda: check_closed(rows)))
        if docs["answers.md"] is None and nothing_open(docs["frame.md"], rows):
            out.append(result(True, "answers-sourced", "no answers.md; nothing was open"))
        else:
            out.append(need("answers-sourced", "answers.md", 2, lambda: check_answers(docs["answers.md"])))
        out.append(need("decider-signoff", "gates.md", 2,
                        lambda: check_signoff(docs["gates.md"], idea.get("decider", ""))))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate an idea folder.")
    ap.add_argument("folder")
    ap.add_argument("--gate", type=int, choices=[1, 2], default=0)
    a = ap.parse_args(argv)
    results = run(a.folder, a.gate)
    if results is None:
        msg = f"REFUSED {Path(a.folder) / 'idea.md'}: no idea.md"
        print(msg)
        print(msg, file=sys.stderr)
        return 2
    for status, name, detail in results:
        print(f"{status} {name}: {detail}".rstrip(": ").rstrip())
    return 1 if any(r[0] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
