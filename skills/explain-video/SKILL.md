---
name: explain-video
description: Narrated tutorial videos (YouTube-style MP4) that teach code, a PR, an architecture, a lesson note or a concept, built as HyperFrames films with a local Kokoro voice and one invented visual per scene. Use when the user asks for a video, video tutorial, explainer or walkthrough of code or a topic, or to turn a note or lesson into a video.
---

# Explain video

A tutorial film in four layers: the script teaches, the narrator records it, the storyboard gives each scene one invented visual timed to the voice, and frame workers build those scenes in HyperFrames. Scripts handle the rest: setup, assembly, checks, render and mastering.

- `<ev>` is this skill's directory. `hf` means `HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.184`, run in the project folder. The skip flag stops each CLI call from re-linking the global agent skills.
- The HyperFrames pieces this pipeline needs are frozen in `<ev>/hyperframes-0.8.184/`. Release 0.8.185 dropped the frame presets, blueprints, frame packets and assembly scripts. The installed `/hyperframes` skills may be a different version, so read HyperFrames docs from the frozen folder.

**Where videos live:** in the Obsidian vault at `~/developer/vault`, never in a code repo.
- **A video for a project:** `~/developer/vault/01-projects/<project>/videos/`. Read the vault's `AGENTS.md` and the project's index note first.
- **No project yet:** `~/developer/vault/00-inbox/videos/`, and say so in the hand-over.
- **Each video is three items:**
  - `<slug>.json`: the script.
  - `<slug>/`: the HyperFrames project.
  - `<slug>.mp4`: the render.

## Steps

1. **Source.** Read the real material: the code and its files, the PR diff, or the lesson note. When the video belongs to a project whose index note links a video format note, read it too: its rules override this skill's defaults. Then write down three things:
   - The `message`: the one sentence the viewer leaves with.
   - One running example, with concrete actors, ids and figures.
   - The facts allowed on screen.

   Done when all three exist and every figure has a source.
2. **Script.** Write `<videos-dir>/<slug>.json` following [references/script.md](references/script.md) (format, story spines, writing for the ear). Done when `node <ev>/scripts/narrate.mjs <script> --lint` exits 0 and every scene serves `message`.
3. **Project.** Run `node <ev>/scripts/new-project.mjs <videos-dir>/<slug>.json [--preset code-editorial]`. It creates `<slug>/` with:
   - `BRIEF.md`.
   - `frame.md`, the look, with its fonts staged.
   - The narration in `assets/vo/`.
   - `.hyperframes/cues.md`: each scene's length and the start time of every sentence.

   Done when it prints the scene table and the total length.
4. **Storyboard.** Write `<slug>/STORYBOARD.md` following [references/visuals.md](references/visuals.md):
   - The Video direction and the Shared props.
   - One Frame block per scene, with every reveal timed from `cues.md`.
   - Motion cited from `<ev>/hyperframes-0.8.184/hyperframes-animation/{blueprints,rules}-index.md`.

   Search the registry for any named look, and install the picks now, before dispatch. Stage the marks of real products named on screen with `node <ev>/scripts/logos.mjs <project> <slug…>`. Done when:
   - Every scene has a block with a distinct visual idea, a citation, `focal`, `coral`, `transition_in` and timed Scene lines.
   - No block uses a guardrail form.
5. **Build.** Run `hf usage --json` and tell the user the weekly figure. Then:
   - **Up to ~6 scenes:** build them inline, one packet at a time.
   - **More scenes:** run `node <ev>/scripts/dispatch.mjs <project> [--groups "1,2,22|3,23,25|…"]` (group frames that share props). It writes the packets, the dispatch context and one prompt file per worker. Start every worker in one message: Agent tool, `general-purpose`, `model: "sonnet"`, prompt `Read <worker file> and follow it.`

   Done when every Frame `src` and its `.motion.json` exist on disk. Completion notifications don't count; step 6 lists what is missing, and you re-dispatch only those workers.
6. **Assemble and check.** Run `node <ev>/scripts/assemble.mjs <project>`. It checks for missing files and fonts, assembles `index.html` (frames plus each scene's voice), injects and verifies the transitions, runs `hf check`, and writes contact sheets at each frame's poster time. Look at every sheet for text that reads wrong, casing off the table in `references/visuals.md`, overflow, front-loaded frames and broken callbacks. Fix the frame, set it to `status: animated`, and re-run. Done when the script exits 0 and the sheets look right.
7. **Review.** Before the user sees a cut, run the `scene-reviewer` agent (Agent tool) on the project, passing the render path and the user's notes when they exist. Fix its Blocker and Fix findings, re-assemble, and re-run it on the frames you touched (`scenes`). Done when it returns no Blocker or Fix, or the user has heard why one stays.
8. **Final look.** Run `hf preview --background`, open the URL it prints, and tell the user they can edit there. If it printed a "Keep editing by chatting with Framey" line, add that the **Edit with Framey** button opens the HyperFrames desktop app. Ask one question: render, or revise first? Stop the preview with `hf preview --stop` once they answer.
9. **Finish.** Run `node <ev>/scripts/finish.mjs <project>` in the background (~4 min for 8 min of video). It renders, masters the audio to −14 LUFS / −1 dBTP, verifies the master and writes `<videos-dir>/<slug>.mp4`. Done when it prints the duration, loudness and true peak.
10. **Hand over.** Embed `![[<slug>.mp4]]` in the source note (a `## Video` section) and the project index, and mark any version it replaces as superseded. Report the path, duration, scene count and loudness. Pass on the render's Framey line in your own words, and offer `open <file>`.

## Changing a built video

- **Narration:** edit the script and run `node <ev>/scripts/narrate.mjs <script> <project>`. It names the scenes whose timing changed. Update those Frame blocks from `cues.md`, rebuild those frames, then run assemble.
- **A scene:** edit `compositions/frames/NN-<id>.html`, or re-dispatch that frame's worker file. Then run assemble.
- **Before handing a change back:** run step 7 with the user's notes; the render they watched becomes its baseline for regressions.
- **Edits the user made in Studio or the desktop app:** they are already in the files. Run `hf catch-up` first if a command asks for it.

## Cost

W1.1 (25 scenes, 8 min, workers on Opus) took ~14% of a weekly Max window. Nearly all of it went to the nine frame workers, which built their own render harnesses; the worker prompt now limits them to lint, and they run on Sonnet. A 5-hour session limit stopped one worker mid-wave, and the files it had written survived. If Sonnet frames come back weak on the contact sheet, re-dispatch just those workers without the `model` override. To spend less still, use ~15 scenes and give each worker 3 frames. Check `hf usage --json` before steps 5 and 9.
