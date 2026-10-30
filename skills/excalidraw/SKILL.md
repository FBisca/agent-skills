---
name: excalidraw
description: Hand-drawn Excalidraw diagrams (system design, flows, states, risks) written as a Python spec, linted by script and checked by rendering each frame. Use when the user asks for an Excalidraw drawing or diagram, or to redraw one so it looks hand-made.
---

# Excalidraw

**Input:** what to draw (a design note, a flow, a decision) and, when there is one, a drawing the user made by hand as the style reference.
**Output:** `<slug>.excalidraw` and its spec `<slug>.sketch.py`, side by side; the check passing; every frame rendered and read; the style numbers next to the reference's.
**Hand-off:** the path, the style numbers, and anything not checked.

`<sk>` is this skill's directory. Scripts run with `python3 -I`. Drawings live in the Obsidian vault at `~/developer/vault`, next to the project's index note (`01-projects/<project>/`), or in `00-inbox/excalidraws/` when there is no project. Link the drawing from the index note.

## The style

The drawing should look like a person sketched it in five minutes and explained it out loud:

- **Noun boxes, verb arrows.** A box label is a noun of 1–3 words. An arrow is mostly unlabelled; a label is 1–2 words.
- **Notes beside.** Every explanation is a small `note()` next to its box (≤ 8 words, a thin leader line). The box stays short; the note carries the why.
- **One question per frame.** Each frame has a headline that answers its question, a one-line subtitle, and a reading path (`num()` or left-to-right).
- **White by default.** Colour means one of three things: red for risk or STOP, green for steps only a person may do, yellow for what is drafted or highlighted. Everything else stays white.
- **Hand marks on what matters.** `circle()` or `underline()` the one to three things the reader must not miss.
- **Tags when asked.** `tag()` puts a small pill on a box saying what it is in the build (skill, command, file).

## Steps

1. **Frames.** Split the material into questions, one per frame (where it runs, how data flows, the states, the risks...). For each frame, write the headline, the boxes (nouns) and the arrows between them. Leave out anything that doesn't change the reader's decision; the source note keeps the detail. Done when every frame has a headline, at most about 12 boxes, and every box label is ≤ 3 words.
2. **Reference.** Look for a drawing the user made by hand: the one they name, else `*.excalidraw` files in the vault. Run `python3 -I <sk>/scripts/style.py <reference>`. With no reference, the targets are the ones measured on the user's own drawing: box words median 2, white boxes ≥ 75%, elbow arrows ≥ 90%, labelled arrows ≤ 25%, note words median 4–6, and some hand marks. Done when the target numbers are written down.
3. **Spec.** Write `<slug>.sketch.py` with `excali.Sketch` (read its docstring; `<sk>/examples/example.py` shows every helper). Draw each frame inside `with s.frame(n):`, and stack frames vertically with room between them. Done when the spec runs and writes `<slug>.excalidraw`.
4. **Check.** Run `python3 -I <sk>/scripts/check.py <slug>.excalidraw --ref <reference>`. It FAILs on text over budget, overlapping boxes or notes, and arrows running through a box or note. Fix the spec and rerun. Done when it exits 0 and every style number is within the target from step 2.
5. **Look.** Render every frame and read each screenshot, following the render loop in [REFERENCE.md](REFERENCE.md). Fix what the lint can't see: crowding, a label sitting on a dashed border, a frame whose picture doesn't say its headline. Rerun step 4 after each fix. Done when every frame's screenshot has been read after the last change, and each frame passes the five-second test: someone who wasn't in the room can say what it shows from the headline and the boxes.
6. **Hand over.** Save the drawing and spec in the vault, link the drawing from the index note, stop the server, and delete the screenshots and browser logs the render loop wrote. Report the path, your style numbers beside the reference's, and anything you could not check.
