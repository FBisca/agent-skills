"""Hand-drawn Excalidraw sketches from Python: short boxes, notes beside them, elbow arrows, hand marks.

A spec script imports this module, draws with a Sketch, and saves a .excalidraw file:

    import sys; sys.dont_write_bytecode = True; sys.path.insert(0, "<skill>/scripts")
    from excali import Sketch, GREEN, RED, YELLOW
    s = Sketch()
    with s.frame(1):
        s.headline(0, 0, "1 · Where it runs", "one line that says the point")
        a = s.box(0, 200, "Operator")
        b = s.box(400, 200, "Tool", fill=GREEN)
        s.arrow(a, b)
        s.note(b, "runs locally", "b")
    s.save("out.excalidraw")

Every element carries customData {"frame": n, "role": ...}; check.py and split.py read it.
"""
import json
import math
import random
from contextlib import contextmanager

INK, GREY, MUTED = "#1e1e1e", "#868e96", "#495057"
RED, GREEN, YELLOW, WHITE = "#ffc9c9", "#b2f2bb", "#ffec99", "#ffffff"
RED_INK, BLUE_INK, ORANGE_INK, PURPLE = "#e03131", "#1971c2", "#f08c00", "#9c36b5"
CW = 0.64  # Excalifont character width as a fraction of font size (measured by rendering)

_SIDE = {"r": (1, .5), "l": (0, .5), "t": (.5, 0), "b": (.5, 1)}
_FIXED = {"r": [1.03, .5], "l": [-.03, .5], "t": [.5, -.06], "b": [.5, 1.06]}


def tsize(s, fs):
    lines = s.split("\n")
    return max(len(l) for l in lines) * fs * CW, len(lines) * fs * 1.25


class Sketch:
    def __init__(self, seed=11, jitter=True):
        self.rng = random.Random(seed)
        self.els = []
        self._frame = 0
        self.jit = jitter
        self._n = 0

    # ------------------------------------------------------------ plumbing
    def _j(self, v):
        return self.rng.uniform(-v, v) if self.jit else 0

    def _el(self, t, x, y, w, h, role, **kw):
        self._n += 1
        e = {"id": f"sk{self._n:05d}", "type": t, "x": x, "y": y, "width": w, "height": h, "angle": 0,
             "strokeColor": kw.pop("stroke", INK), "backgroundColor": kw.pop("bg", "transparent"),
             "fillStyle": "solid", "strokeWidth": kw.pop("sw", 2), "strokeStyle": kw.pop("ss", "solid"),
             "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
             "roundness": kw.pop("roundness", {"type": 3}), "seed": self.rng.randint(1, 2**31), "version": 1,
             "versionNonce": self.rng.randint(1, 2**31), "isDeleted": False, "boundElements": [],
             "updated": 1790000000000, "link": None, "locked": False,
             "customData": {"frame": self._frame, "role": role}}
        e.update(kw)
        self.els.append(e)
        return e

    def _bind_text(self, owner, s, fs, color=INK):
        tw, th = tsize(s, fs)
        if owner["type"] == "arrow":
            cx, cy = self._arrow_mid(owner)
        else:
            cx, cy = owner["x"] + owner["width"] / 2, owner["y"] + owner["height"] / 2
        t = self.text(cx - tw / 2, cy - th / 2, s, fs, color, role="label", container=owner["id"], align="center")
        owner["boundElements"].append({"id": t["id"], "type": "text"})
        return t

    @staticmethod
    def _arrow_mid(a):
        p = a["points"]
        k = len(p) // 2
        return a["x"] + (p[k - 1][0] + p[k][0]) / 2, a["y"] + (p[k - 1][1] + p[k][1]) / 2

    @contextmanager
    def frame(self, n):
        """Tag everything drawn inside with frame n (used to render and check one frame at a time)."""
        old, self._frame = self._frame, n
        yield
        self._frame = old

    # ------------------------------------------------------------ text
    def text(self, x, y, s, fs=18, color=INK, role="note", container=None, align="left"):
        w, h = tsize(s, fs)
        return self._el("text", x, y, w, h, role, stroke=color, roundness=None, text=s, fontSize=fs,
                        fontFamily=5, textAlign=align, verticalAlign="middle" if container else "top",
                        containerId=container, originalText=s, autoResize=True, lineHeight=1.25)

    def headline(self, x, y, title, sub=None):
        t = self.text(x, y, title, 36, role="headline")
        if sub:
            self.text(x, y + 56, sub, 20, MUTED, role="headline")
        return t

    # ------------------------------------------------------------ shapes
    def box(self, x, y, label, fill="transparent", stroke=INK, dashed=False, fs=24, minw=0, shape="rectangle"):
        tw, th = tsize(label, fs)
        w, h = max(minw, tw + 68) + self._j(8), th + 44 + self._j(4)
        b = self._el(shape, x + self._j(5), y + self._j(5), w, h, "box", bg=fill, stroke=stroke,
                     ss="dashed" if dashed else "solid")
        self._bind_text(b, label, fs)
        return b

    def zone(self, x, y, w, h, label):
        z = self._el("rectangle", x, y, w, h, "zone", ss="dashed", stroke=GREY)
        self.text(x + 16, y + 10, label, 20, GREY, role="zone")
        return z

    def tag(self, b, s, color=PURPLE):
        """Small pill on a box's top-left corner: what the box is in the build."""
        tw, th = tsize(s, 14)
        w, h = tw + 18, th + 8
        p = self._el("rectangle", b["x"] - 14, b["y"] - h / 2, w, h, "tag", bg=WHITE, stroke=color, sw=1)
        self._bind_text(p, s, 14, color)
        return p

    def num(self, b, n, color=BLUE_INK):
        return self.text(b["x"] - 30, b["y"] - 30, str(n), 22, color, role="mark")

    # ------------------------------------------------------------ notes
    def note(self, b, s, side="r", gap=None, fs=18, color="#343a40"):
        """A short handwritten note beside a box, joined by a thin leader line."""
        gap = gap if gap is not None else (46 if side in "lr" else 30)
        if side == "t":
            gap += 16  # leave room for a tag pill
        tw, th = tsize(s, fs)
        cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        if side == "r":
            x, y = b["x"] + b["width"] + gap, cy - th / 2
            p, q = (b["x"] + b["width"] + 6, cy), (x - 6, y + th / 2)
        elif side == "l":
            x, y = b["x"] - gap - tw, cy - th / 2
            p, q = (b["x"] - 6, cy), (x + tw + 6, y + th / 2)
        elif side == "b":
            x, y = cx - tw / 2, b["y"] + b["height"] + gap
            p, q = (cx, b["y"] + b["height"] + 6), (cx, y - 6)
        else:
            x, y = cx - tw / 2, b["y"] - gap - th
            p, q = (cx, b["y"] - 6), (cx, y + th + 6)
        t = self.text(x, y, s, fs, color, role="note")
        pts = [[0, 0], [q[0] - p[0], q[1] - p[1]]]
        self._el("line", p[0], p[1], abs(pts[1][0]), abs(pts[1][1]), "leader", sw=1, stroke=GREY,
                 roundness={"type": 2}, points=pts, lastCommittedPoint=None, startBinding=None,
                 endBinding=None, startArrowhead=None, endArrowhead=None, polygon=False)
        return t

    # ------------------------------------------------------------ arrows
    def _anchor(self, e, s, gap=7):
        fx, fy = _SIDE[s]
        dx, dy = {"r": (gap, 0), "l": (-gap, 0), "t": (0, -gap), "b": (0, gap)}[s]
        return e["x"] + e["width"] * fx + dx, e["y"] + e["height"] * fy + dy

    def arrow(self, a, b, sa="r", sb="l", label=None, dashed=False, d=60, mx=None, my=None):
        """Elbow arrow from side sa of a to side sb of b. Same-side pairs loop out by d; mx/my force the bend."""
        x1, y1 = self._anchor(a, sa)
        x2, y2 = self._anchor(b, sb)
        horiz = lambda s: s in "rl"
        if horiz(sa) and horiz(sb):
            if mx is None:
                mx = (max(x1, x2) + d if sa == "r" else min(x1, x2) - d) if sa == sb else (x1 + x2) / 2
            P = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
        elif not horiz(sa) and not horiz(sb):
            if my is None:
                my = (max(y1, y2) + d if sa == "b" else min(y1, y2) - d) if sa == sb else (y1 + y2) / 2
            P = [(x1, y1), (x1, my), (x2, my), (x2, y2)]
        elif horiz(sa):
            P = [(x1, y1), (x2, y1), (x2, y2)]
        else:
            P = [(x1, y1), (x1, y2), (x2, y2)]
        Q = [P[0]]
        for p in P[1:]:
            if abs(p[0] - Q[-1][0]) > .5 or abs(p[1] - Q[-1][1]) > .5:
                Q.append(p)
        pts = [[px - x1, py - y1] for px, py in Q]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        ar = self._el("arrow", x1, y1, max(xs) - min(xs), max(ys) - min(ys), "arrow", roundness=None,
                      ss="dashed" if dashed else "solid", points=pts, lastCommittedPoint=None,
                      startBinding={"elementId": a["id"], "mode": "orbit", "fixedPoint": _FIXED[sa]},
                      endBinding={"elementId": b["id"], "mode": "orbit", "fixedPoint": _FIXED[sb]},
                      startArrowhead=None, endArrowhead="arrow", elbowed=True, fixedSegments=None,
                      startIsSpecial=None, endIsSpecial=None)
        a["boundElements"].append({"id": ar["id"], "type": "arrow"})
        b["boundElements"].append({"id": ar["id"], "type": "arrow"})
        if label:
            self._bind_text(ar, label, 16)
        return ar

    # ------------------------------------------------------------ hand marks
    def _stroke(self, pts, color, sw=2):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        self._el("freedraw", pts[0][0], pts[0][1], max(xs) - min(xs), max(ys) - min(ys), "mark", stroke=color,
                 sw=sw, roundness=None, points=[[px - pts[0][0], py - pts[0][1]] for px, py in pts],
                 pressures=[], simulatePressure=True, strokeOptions={"variability": "variable", "streamline": .5})

    def circle(self, e, color=RED, pad=(22, 18)):
        cx, cy = e["x"] + e["width"] / 2, e["y"] + e["height"] / 2
        rx, ry = e["width"] / 2 + pad[0], e["height"] / 2 + pad[1]
        a0 = self.rng.uniform(0, 6.28)
        pts = []
        for i in range(60):
            a = a0 + i / 59 * (2 * math.pi + .45)
            k = 1 + self.rng.uniform(-.02, .02) + .04 * i / 59
            pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
        self._stroke(pts, color)

    def underline(self, e, color=RED, below=10):
        x0, x1, y = e["x"], e["x"] + e["width"], e["y"] + e["height"] + below
        self._stroke([(x0 + (x1 - x0) * i / 30, y + 3 * math.sin(i / 3) + self.rng.uniform(-1, 1))
                      for i in range(31)], color)

    # ------------------------------------------------------------ output
    def save(self, path):
        doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": self.els,
               "appState": {"gridSize": 20, "gridStep": 5, "gridModeEnabled": False,
                            "viewBackgroundColor": "#ffffff"}, "files": {}}
        with open(path, "w") as f:
            json.dump(doc, f, indent=1)
        print(path, len(self.els), "elements")
