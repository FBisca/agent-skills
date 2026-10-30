"""Lint a drawing made with excali.py: text budget, overlaps, arrows crossing things, style numbers.

Usage: python3 -I check.py <file.excalidraw> [--ref <reference.excalidraw>]
Prints `FAIL <check>: detail` lines, then the style numbers. Exit 0 when nothing FAILs, 1 otherwise.
"""
import json
import os
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill folder
sys.path.insert(0, os.path.dirname(__file__))
from style import line, measure  # noqa: E402

BUDGET = {"box": 4, "arrow": 3, "note": 10, "tag": 4}  # max words per text, by the owner's role
PAD = 4


def role(e):
    return (e.get("customData") or {}).get("role")


def rect(e):
    return e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]


def overlap(a, b, pad=PAD):
    ax0, ay0, ax1, ay1 = rect(a)
    bx0, by0, bx1, by1 = rect(b)
    return ax0 + pad < bx1 and bx0 + pad < ax1 and ay0 + pad < by1 and by0 + pad < ay1


def seg_hits(x0, y0, x1, y1, e, pad=PAD):
    rx0, ry0, rx1, ry1 = rect(e)
    rx0, ry0, rx1, ry1 = rx0 + pad, ry0 + pad, rx1 - pad, ry1 - pad
    if abs(y0 - y1) < .5:  # horizontal segment
        return ry0 < y0 < ry1 and min(x0, x1) < rx1 and max(x0, x1) > rx0
    if abs(x0 - x1) < .5:  # vertical segment
        return rx0 < x0 < rx1 and min(y0, y1) < ry1 and max(y0, y1) > ry0
    return False


def label(e, by_id):
    for b in e.get("boundElements") or []:
        if b["type"] == "text" and b["id"] in by_id:
            return by_id[b["id"]]["text"].replace("\n", " ")
    return e.get("text", e["id"]).replace("\n", " ")[:40]


def main(path, ref=None):
    els = [e for e in json.load(open(path))["elements"] if not e.get("isDeleted")]
    by_id = {e["id"]: e for e in els}
    fails = []

    # 1. text budget: boxes are nouns, arrows verbs, notes short
    for t in (e for e in els if e["type"] == "text"):
        owner = by_id.get(t.get("containerId"))
        r = role(owner) if owner else role(t)
        limit = BUDGET.get(r)
        if limit and len(t["text"].split()) > limit:
            fails.append(f"budget: {r} '{t['text'][:40]}' has {len(t['text'].split())} words (max {limit})")

    # 2. overlaps among boxes, notes and headlines (tags may sit on their box's border)
    solid = [e for e in els if role(e) in ("box", "note", "headline") and e["type"] != "arrow"
             and not (e["type"] == "text" and e.get("containerId"))]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            if overlap(a, b):
                fails.append(f"overlap: '{label(a, by_id)}' and '{label(b, by_id)}'")
    tags = [e for e in els if role(e) == "tag"]
    for i, a in enumerate(tags):
        for b in tags[i + 1:] + [n for n in solid if role(n) == "note"]:
            if overlap(a, b, 1):
                fails.append(f"overlap: tag '{label(a, by_id)}' and '{label(b, by_id)}'")

    # 3. arrows must not run through boxes or notes other than their own ends
    for a in (e for e in els if e["type"] == "arrow"):
        ends = {(a.get("startBinding") or {}).get("elementId"), (a.get("endBinding") or {}).get("elementId")}
        pts = [(a["x"] + p[0], a["y"] + p[1]) for p in a["points"]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for e in solid:
                if e["id"] not in ends and seg_hits(x0, y0, x1, y1, e):
                    fails.append(f"crossing: arrow '{label(by_id[min(ends - {None})], by_id)}' → … runs through '{label(e, by_id)}'")

    for f in dict.fromkeys(fails):
        print("FAIL", f)
    print(line("drawing  ", measure(path)))
    if ref:
        print(line("reference", measure(ref)))
    return 1 if fails else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    ref = args[args.index("--ref") + 1] if "--ref" in args else None
    sys.exit(main(args[0], ref))
