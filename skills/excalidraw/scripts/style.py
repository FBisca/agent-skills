"""Measure the drawing style of any .excalidraw file (yours or a reference someone drew by hand).

Usage: python3 -I style.py <file.excalidraw> [<reference.excalidraw>]
Prints one line per file; with a reference, also the gap on each measure.
"""
import json
import statistics as st
import sys

SHAPES = ("rectangle", "ellipse", "diamond")
PILL_MAX_H = 30  # tag pills are small; they are not boxes


def measure(path):
    els = [e for e in json.load(open(path))["elements"] if not e.get("isDeleted")]
    by_id = {e["id"]: e for e in els}
    texts = [e for e in els if e["type"] == "text"]
    shapes = [e for e in els if e["type"] in SHAPES and e["height"] > PILL_MAX_H
              and (e.get("customData") or {}).get("role") != "zone"]
    in_box = [len(t["text"].split()) for t in texts
              if t.get("containerId") in by_id and by_id[t["containerId"]]["type"] in SHAPES
              and by_id[t["containerId"]]["height"] > PILL_MAX_H]
    roles = lambda t: (t.get("customData") or {}).get("role")
    free = [len(t["text"].split()) for t in texts if not t.get("containerId") and roles(t) not in ("headline", "zone", "mark")]
    arrows = [e for e in els if e["type"] == "arrow"]
    labelled = sum(any(b["type"] == "text" for b in (a.get("boundElements") or [])) for a in arrows)
    white = sum(s["backgroundColor"] in ("transparent", "#ffffff") for s in shapes)
    return {
        "box_words_median": st.median(in_box) if in_box else 0,
        "box_words_max": max(in_box) if in_box else 0,
        "white_boxes_pct": round(100 * white / len(shapes)) if shapes else 0,
        "elbow_arrows_pct": round(100 * sum(bool(a.get("elbowed")) for a in arrows) / len(arrows)) if arrows else 0,
        "labelled_arrows_pct": round(100 * labelled / len(arrows)) if arrows else 0,
        "notes": len(free),
        "note_words_median": st.median(free) if free else 0,
        "hand_marks": sum(e["type"] == "freedraw" for e in els),
        "boxes": len(shapes),
    }


def line(name, m):
    return name + " | " + " · ".join(f"{k} {v}" for k, v in m.items())


if __name__ == "__main__":
    mine = measure(sys.argv[1])
    print(line("drawing  ", mine))
    if len(sys.argv) > 2:
        ref = measure(sys.argv[2])
        print(line("reference", ref))
