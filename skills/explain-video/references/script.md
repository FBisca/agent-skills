# Script: format, story and narration

The script is the teacher. It is a JSON file the narrator records scene by scene; every later step (timing, storyboard, frames) is built on the recording, so the script is final before step 3.

## Format

```json
{
  "title": "The rename that cost twelve dollars",
  "message": "When your coding agent fails, ask which of three places failed (weights, context or harness): each has a different fix.",
  "audience": "senior engineers who build with coding agents",
  "angle": "narrative incident: one rename, three failures, a twist, a payoff",
  "sources": ["../../lessons/W1.1 Mechanics Behind Generative AI.md"],
  "speed": 1.05,
  "scenes": [
    {
      "id": "incident",
      "narration": "Here's a small task. Rename one helper, and fix the test that breaks. Your agent says it's done. Then you look. …",
      "visual": "an agent transcript says done; the camera pulls back to an evidence board of three failures",
      "pauseAfter": 0.8
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `title`, `message` | Required. `message` is the one sentence the viewer leaves with; it becomes BRIEF.md's message and decides which scenes exist. |
| `audience`, `angle` | Who it's for; the story shape in one phrase. |
| `sources` | Files every number and claim comes from, relative to the project folder (`<videos-dir>/<slug>/`). |
| `aspect`, `voice`, `preset`, `speed` | Defaults `1920x1080`, `af_heart`, `code-editorial`, `1`. Speed 1.05 suits most tutorials. |
| scene `id` | kebab-case; the frame becomes `compositions/frames/NN-<id>.html`. |
| scene `narration` | What the voice says. Empty makes a silent beat of `seconds` (default 3). A blank line inside is a 1 s paragraph pause; `[pause 800]` is an explicit pause in ms. |
| scene `visual` | The visual idea in one line, carried into the storyboard. |
| scene `speed` | 0.95 on a key idea, 1.1 on a recap; otherwise the script's. |
| scene `pauseAfter`, `chapter` | Silence after the voice in seconds: default 0.7, or 1.0 with `chapter: true`. |

Old explain-video scripts (Remotion scene `type`s) still narrate: their visual fields are ignored and `type: "title"` counts as a chapter.

## Story

Pick the spine that fits, then cut every scene that doesn't serve `message`. 10–25 scenes, 5–9 minutes.

- **Lesson or concept:** incident → promise ("by the end you'll name all three") → the model → one mystery per mechanic → twist → payoff (replay the incident through the model) → habits → next.
- **Code, PR or architecture:** a concrete moment that needs the code (a bug, a request, a user question) → the map, with one running example's real actors and ids → 2–4 flows, each followed by the code that does it → the gotcha → payoff (replay the opening moment) → where to read next. Every excerpt matches the real file.

Rules for both:

- Open on a concrete incident, never a definition. An invented composite incident is fine for a concept; code videos use the real code.
- Carry one running example through every scene, and bring the opening's evidence back in the payoff.
- Promise early what the viewer will be able to do, and close every loop you open.
- Chapter beats are questions ("Why did it ignore the rule?").
- Link scenes with *but*, *so*, *which means*.
- Use only figures from `sources` or the code.
- One idea per scene: 3–8 sentences, about 70 words (lint flags over 110).

## Narration: write for the ear

- Second person, contractions, mostly short sentences with a few longer ones.
- Spell out symbols and numbers: "twelve dollars and forty cents", "one million tokens", "three times", `!==` → "is not". Say identifiers by role or as words ("the check-mutation helper", "your CLAUDE file").
- Emphasis comes from position (the end of a short sentence) and isolation (a 1–3 word sentence). Kokoro ignores CAPS and italics, deletes parentheses, and pauses the same on every punctuation mark.
- A question gets its own pause, so ending a scene on a question lands it.
- The voice explains; the screen shows keywords. Write sentences that say more than the labels on screen.
- Order the narration in the order things should appear; the storyboard times each reveal to its sentence.

`node <ev>/scripts/narrate.mjs <script.json> --lint` lists what Kokoro would misread (currency and abbreviated numbers, slashes and arrows, capitals for emphasis, long scenes).

## What the narrator does

`narrator/kokoro.mjs` (Kokoro-82M, local and free) synthesizes each scene in chunks of 1–3 sentences, because Kokoro silently drops everything past 510 phoneme tokens (~26 s) in one call; it throws if a chunk comes back near that cap. It trims each chunk and joins them with designed pauses (sentence 0.6 s, question 0.8 s, paragraph 1.0 s, ±60 ms seeded jitter so the rhythm isn't metronomic), rewrites common misreads (`e.g.`, `1M`, `3x`, `CLAUDE.md`, parentheses, arrows), and records each chunk's start and end. Voices: `af_heart` (default, US female), `af_bella`, `am_michael` (US male), `bf_emma`, `bm_george` (UK). `KOKORO_DTYPE=fp32` swaps the q8 model for full precision (one-time ~326 MB download).
