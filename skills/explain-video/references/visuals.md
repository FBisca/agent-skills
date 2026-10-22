# Visuals: direction and storyboard

Each scene is one invented visual idea that develops with the voice. That, more than the engine, is what separates these films from a slideshow. STORYBOARD.md holds the whole visual plan, and each Frame block is a dispatch unit: a worker builds its frame from that block, the Video direction, the Shared props and frame.md, nothing else. `<hf>` below is `<ev>/hyperframes-0.8.184`.

## Scene ideas

- **One focal idea per scene**, chosen for its beat: a metaphor object (concentric rings for "three places", a dial for effort, a receipt for cost), a real surface (code, terminal, diff, agent transcript, chart), or kinetic type for a stance or a question.
- **On-screen text is keywords**: labels, code, tokens, file names and numbers, at most ~5 words per label. The voice says the sentence.
- **Guardrail from the rejected v2:** no bullet-list slides, plain data tables, lane-and-arrow sequence diagrams, identical card grids, or narration sentences on screen. When a beat seems to need one, show its surface or a metaphor: a list of failures becomes evidence cards pinned to a board, a request flow becomes a transcript that streams, a price table becomes a dial that turns.
- **Callbacks:** the opening's evidence returns in the payoff, and the model diagram returns wherever it's used. Specify each recurring prop once under `## Shared props` and draw it identically every time.
- **Framing variety:** no two consecutive frames share a framing (close-up, wide board, split, full-bleed type, code surface).
- **One accent moment per frame** (`coral:` in code-editorial): the single thing that draws on.
- **Real figures only:** every number comes from the script or its sources.
- **The bottom ~17% stays clear.**

## Casing

Each kind of text has one casing; lowercase belongs only to literal code and units.

| Text | Casing | Example |
|---|---|---|
| Headlines and questions | Sentence case | "Why did it ignore NEVER?" |
| Concept names and diagram labels | Capitalized | Weights · Context · Harness · Attention |
| Descriptors, chips, captions, axis and state labels | Sentence case | "Attention budget" · "Tool result" · "Frozen · cutoff" |
| Kickers (small tracked mono, ≤ 3 words) | ALL CAPS | ✱ MYSTERY 1 |
| Code, file names, commands, tokens, config values | Exactly as in the source | `CLAUDE.md` · `dates.parseStrict()` · `effort: low` |
| Quoted source text | Exactly as written, in mono | NEVER (quoted from CLAUDE.md) |
| Products and proper nouns | Official casing | Claude Code · GPT-6 · Bash, Edit, Read |
| Units after a number | Lowercase | 12.40 / session · 200 ms · 1M tokens |

- A word that continues a sentence (a headline built word by word, a unit phrase after a figure) keeps sentence case: "Steering models through context".
- Emphasis comes from italic or the accent, never from capitals; ALL CAPS is for kickers and verbatim quotes only.
- The table covers every string that reaches the screen, including text a script types, swaps or counts in (status words, typed lines, label arrays).

## Real products and companies

- A real product or company named on screen (Claude Code, Anthropic, GitHub, OpenAI) carries its official mark: before the name in a chip or label, at text height, and before a credit line ("✱ J-SPACE · [mark] ANTHROPIC").
- Marks come only from `node <ev>/scripts/logos.mjs <project> <slug…>` (official traced SVGs, slugs as on simpleicons.org), staged before dispatch. Draw them from `assets/logos/logos.json` as an inline `<svg viewBox="0 0 24 24"><path d="…"/></svg>`.
- Colour: the brand colour from the manifest, or one flat colour of the look (white or ink) when the brand colour fails contrast on its ground. The shape stays as delivered: no outline, stretch, effect or redrawing; it may fade or move as a whole.
- Referential use only: the mark identifies the thing being discussed. It never stands in for the series' own brand, sits beside the series logo, or implies endorsement; follow the `guidelines` link when the manifest has one.
- A product without a mark in Simple Icons keeps its name as a wordmark in official casing. Commands, tool names and files (`npm test`, Bash, CLAUDE.md) stay text.

## Motion

- **Every reveal lands on its cue.** Scene lines carry times from `.hyperframes/cues.md`; at t=0 only what the voice is saying is on screen. A frame that front-loads and then holds is the slideshow failure. `~` times are estimates inside a spoken chunk: give those reveals a little slack, or split the sentence in the script.
- **The look's register** (code-editorial: long-tail eases, `power3.out` by default, `power2.inOut` for camera moves, no bounce or overshoot). Code types on line by line, numbers count up, and the accent draws on.
- **Between reveals**, at most a slow camera drift or a 1–2 px breathe on background decoratives; nothing floats on its own.
- **Held breathers:** 2–4 per film, right after a big idea. Name them in the Video direction.
- **Cite each frame's motion** from `<hf>/hyperframes-animation/blueprints-index.md` (`blueprint: <id> (Adapt)`: keep the signature and restate it in the block) or, when no blueprint fits, the rules from `rules-index.md` it composes (`blueprint: compose`). Ids come from those indexes; the packet builder inlines their bodies for the worker. W1.1 adapted 13 blueprints across 16 frames and composed 9.
- **Named looks** (a terminal run, a chart, a marker highlight): run `hf catalog --query "<look>" --json` before planning to build one, install the picks with `hf add <name> --no-clipboard --json` before dispatch, and name the component in the block.

## Transitions

Each incoming frame sets `transition_in`; mix them across the film. Use `push-slide LEFT` between ordinary beats (W1.1: 14 of 25), `zoom-through` to go deeper into a mystery (5), and `blur-crossfade` for a shift in time or mood (3). Use `crossfade` or `squeeze` once or twice, and `cut` for the opener and hard reveals. `<type> <N>s` sets the length.

## STORYBOARD.md

```markdown
---
format: 1920x1080
duration: 474s
message: "<BRIEF.md message>"
arc: Incident → Promise → Model → Mystery 1 → Mystery 2 → Mystery 3 → Twist → Payoff → Habits → Next
audience: <BRIEF.md audience>
mode: autonomous
music: none
---

## Video direction

- Palette by role (from frame.md) · type, with video-scale minimums (display ≥ 64px, labels ≥ 22px) · motion grammar ·
  recurring props and the frames they appear in · rhythm and held breathers · framing variety · the guardrail above

## Shared props

- **Evidence card** (frames 1, 2, 22): tile card, 12px radius, 1px ink hairline, ~440×190px; mono kicker "✱ FAILURE 1";
  content in JetBrains Mono 36px …

## Frame 1 — One rename, three surprises

- status: outline
- src: compositions/frames/01-incident.html
- duration: 20.0s
- poster: 18s
- transition_in: cut
- scene: An agent transcript says "done"; the camera pulls back to an evidence board of three failures
- voiceover: "<the scene's narration, verbatim>"
- blueprint: transcript-scroll-artifact-reveal (Adapt)
- rules: discrete-text-sequence, counting-dynamic-scale
- focal: the agent transcript, then the three evidence cards
- roles: navy transcript panel = foreground (Scenes 1–2) · evidence cards = foreground (Scenes 3–5) · cream ground with a faint hairline grid = background · kicker "✱ THE INCIDENT" = supporting
- coral: the "$12.40" figure
- sfx: none

Adapt: keep the signature (the transcript reads as evidence of work, then one pivot opens the artifact view).
Scene 1 (0.0–4.1s): Tight on a navy transcript panel; the prompt `> rename formatDate(), fix the failing test` types on from 1.2s as the voice says the task.
Scene 2 (4.1–5.7s): The reply streams in: `✓ renamed …`, `✓ all tests passing`, then `Done.` in green.
Scene 3 (5.7–9.9s): On "Then you look", a decelerating pull-back opens the evidence board; at 6.6s card 1 lands …
```

- One Frame block per script scene, in script order: frame N plays `assets/vo/sNN.wav`, and its `src` is `compositions/frames/NN-<id>.html`.
- `duration` is the scene's length from `cues.md` (voice + pause), never an estimate. `poster` is the moment that best shows the finished frame; the contact sheet uses it.
- Scene lines split the frame into 2–6 beats, each with its time range and the cue it lands on.
- `status: outline` until the frame is built, then `animated`.

The full W1.1 storyboard is the worked example: `~/developer/vault/01-projects/mega-dev/videos/w1-1-rename-that-cost-twelve-dollars/STORYBOARD.md`.
