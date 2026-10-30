"""Write one JSON per frame (plus all.json) into a folder, so each frame can be rendered on its own.

Usage: python3 -I split.py <file.excalidraw> <out_dir>
Frames come from customData.frame set by Sketch.frame(n). Prints the frame numbers written.
"""
import json
import os
import sys

src, out = sys.argv[1], sys.argv[2]
els = json.load(open(src))["elements"]
os.makedirs(out, exist_ok=True)
frames = {}
for e in els:
    frames.setdefault((e.get("customData") or {}).get("frame", 0), []).append(e)
for n, group in frames.items():
    json.dump({"elements": group}, open(os.path.join(out, f"f{n}.json"), "w"))
json.dump({"elements": els}, open(os.path.join(out, "all.json"), "w"))
print("frames", sorted(frames))
