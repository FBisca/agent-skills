"""Example spec: two frames of a generic order system. Run: python3 -I example.py /tmp/example.excalidraw"""
import os
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from excali import GREEN, RED, RED_INK, YELLOW, Sketch  # noqa: E402

s = Sketch()
t = s.text(0, -220, "Orders · system design", 48, role="headline")
s.underline(t, "#1e1e1e", 6)

with s.frame(1):
    s.headline(0, 0, "1 · Where it runs", "one service, one queue, one database")
    user = s.box(0, 300, "Customer")
    s.zone(260, 150, 760, 420, "Cloud")
    api = s.box(320, 220, "API")
    worker = s.box(320, 420, "Worker", stroke=RED_INK, dashed=True)
    db = s.box(720, 300, "Database")
    pay = s.box(1200, 300, "Payments", fill=GREEN)
    s.arrow(user, api, "r", "l")
    s.arrow(api, db, "r", "l", "writes")
    s.arrow(worker, db, "r", "l")
    s.arrow(db, pay, "r", "l")
    s.note(api, "stateless", "t")
    s.note(worker, "retries 3×", "b")
    s.note(pay, "external · read-only", "b")
    for b, k in ((user, "person"), (api, "service"), (worker, "job"), (db, "postgres"), (pay, "external")):
        s.tag(b, k)

with s.frame(2):
    s.headline(0, 800, "2 · An order's life", "every step can be repeated safely")
    steps = [s.box(40 + i * 330, 1020, n) for i, n in enumerate(["Place", "Charge", "Ship", "Close"])]
    for i, b in enumerate(steps):
        s.num(b, i + 1)
    for a, b in zip(steps, steps[1:]):
        s.arrow(a, b)
    fail = s.box(370, 1230, "Refund", fill=RED, fs=20)
    s.arrow(steps[1], fail, "b", "t", "declined")
    s.circle(fail)
    s.note(steps[3], "only when paid\nand shipped", "t")
    s.note(fail, "idempotent", "r")
    draft = s.box(1100, 1230, "Rules", fill=YELLOW)
    s.note(draft, "drafted once", "r")

s.save(sys.argv[1] if len(sys.argv) > 1 else "example.excalidraw")
