#!/usr/bin/env node
// Prepares the parallel scene build once STORYBOARD.md is final:
//   node dispatch.mjs <project-dir> [--per 3 | --groups "01,02,22|03,23,25|…"]
// 1. general-video's frame-packets.mjs → .hyperframes/frame-packets/ (_role.md + one packet per Frame block)
// 2. .hyperframes/dispatch-context.md: canvas, design truth, fonts, naming, installed components, and
//    STORYBOARD.md's "Video direction" and "Shared props" sections verbatim
// 3. .hyperframes/workers/wN.md: one prompt per worker, 2–3 consecutive frames each (--per caps it), or the
//    explicit --groups of frame numbers (group frames that share props so one worker draws them alike)
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { fail, hfCli, hfSkill, parseArgs, run, SKILL_DIR, storyboardFrames } from "./lib.mjs";

const { positional: [projectArg], opts } = parseArgs(["per", "groups"]);
if (!projectArg) fail('usage: dispatch.mjs <project-dir> [--per 3 | --groups "01,02,22|03,23,25|…"]');
const dir = resolve(projectArg);
const per = Number(opts.per ?? 3);
const hf = join(dir, ".hyperframes");

const md = readFileSync(join(dir, "STORYBOARD.md"), "utf8");
const section = name => md.match(new RegExp(`^## ${name}[^\\n]*\\n([\\s\\S]*?)(?=^## |(?![\\s\\S]))`, "m"))?.[1].trim();
const direction = section("Video direction");
// Casing and brand marks are film-independent, so they come from the skill's own reference, not each storyboard.
const visuals = readFileSync(join(SKILL_DIR, "references", "visuals.md"), "utf8");
const rule = name => visuals.match(new RegExp(`^## ${name}\\n([\\s\\S]*?)(?=^## )`, "m"))?.[1].trim();
const casing = rule("Casing");
const brands = rule("Real products and companies");
const logosFile = join(dir, "assets", "logos", "logos.json");
const logos = existsSync(logosFile) ? Object.entries(JSON.parse(readFileSync(logosFile, "utf8"))) : [];
if (!direction) fail("STORYBOARD.md has no `## Video direction` section (references/visuals.md)");
const props = section("Shared props");
const frames = storyboardFrames(dir);
const missing = frames.filter(f => !f.src || !f.duration);
if (missing.length) fail(`Frame blocks without src or duration: ${missing.map(f => f.n).join(", ")}`);

run("node", [join(hfSkill("general-video"), "scripts", "frame-packets.mjs"), "--project", dir, "--storyboard", join(dir, "STORYBOARD.md")]);

const [width, height] = (md.match(/^format:\s*(\d+)x(\d+)/m) ?? [, 1920, 1080]).slice(1).map(Number);
const components = (JSON.parse(readFileSync(join(dir, "hyperframes.json"), "utf8")).registryItems ?? []).map(r => `PROJECT_DIR/${r.target}`);
writeFileSync(
  join(hf, "dispatch-context.md"),
  `## Dispatch context

- PROJECT_DIR: ${dir}
- Canvas: ${width}×${height}. No captions, but keep content above y ≈ ${Math.round(height * 0.83)} (the bottom ~17% stays clear).
- Design truth: PROJECT_DIR/frame.md. Paste its "Font faces" @font-face block inside every composition's <template><style>; the fonts are in PROJECT_DIR/assets/fonts/.
- Timing: every reveal lands on the time in your block's Scene lines; they are measured from the narration. At t=0 only what the voice is saying is on screen.
- Glyphs the staged fonts lack (✱, arrows, check marks, ≈) are drawn as inline SVG.
- Naming: start every id and class with your frame's number, e.g. \`f04-slip\` (the animation map can't parse names that start with a digit).
${logos.length ? `- Staged brand marks (inline the \`path\` from PROJECT_DIR/assets/logos/logos.json): ${logos.map(([slug, l]) => `${l.title} (${slug}, ${l.hex})`).join(", ")}\n` : ""}${components.length ? `- Installed registry components you may adapt when your block names them (read each file's WIRING comment; recolor to frame.md tokens): ${components.join(", ")}\n` : ""}
### Video direction (applies to every frame)

${direction}
${casing ? `\n### Casing (every visible word)\n\n${casing}\n` : ""}${brands ? `\n### Real products and companies\n\n${brands}\n` : ""}${props ? `\n### Shared props (draw them exactly like this so frames match across workers)\n\n${props}\n` : ""}`
);

const workers = Math.ceil(frames.length / per);
const groups = opts.groups
  ? opts.groups.split("|").map(g => g.split(",").map(n => frames.find(f => f.n === Number(n)) ?? fail(`--groups: no frame ${n}`)))
  : Array.from({ length: workers }, (_, k) =>
      frames.slice(Math.round((k * frames.length) / workers), Math.round(((k + 1) * frames.length) / workers))
    );
const grouped = groups.flat().map(f => f.n);
const ungrouped = frames.filter(f => !grouped.includes(f.n));
if (ungrouped.length) fail(`--groups leaves out frames ${ungrouped.map(f => f.n).join(", ")}`);
const workersDir = join(hf, "workers");
rmSync(workersDir, { recursive: true, force: true });
mkdirSync(workersDir, { recursive: true });
console.log(`\n${frames.length} frames → ${groups.length} workers. Dispatch them all in one wave; each prompt is "Read <file> and follow it.":`);
groups.forEach((group, k) => {
  const ids = group.map(f => basename(f.src, ".html"));
  const file = join(workersDir, `w${k + 1}.md`);
  writeFileSync(
    file,
    `You build ${ids.length} scenes of a HyperFrames video. Everything you need is on disk; read these files in order before writing anything:

1. ${join(hf, "frame-packets", "_role.md")} (your role: the composition contract and output rules)
2. ${join(hf, "dispatch-context.md")} (project facts and the film-level direction)
3. Your packets, one per scene:
${ids.map(id => `   - ${join(hf, "frame-packets", `${id}.md`)}`).join("\n")}

For each scene, write its exact \`src\` and the \`<frame_id>.motion.json\` sidecar beside it, then run \`HYPERFRAMES_SKIP_SKILLS=1 npx --yes ${hfCli(dir)} lint\` in ${dir} and fix every error in your files. Lint is your whole check: the orchestrator snapshots the assembled film afterwards, so write no render, screenshot or audio tooling of your own. Keep any scratch files in ${join(hf, "work", `w${k + 1}`)}.

Done when both files exist for every scene above and lint reports no errors in them. Reply with one line per scene: the file, its duration, and anything in its block you could not realize.
`
  );
  console.log(`  w${k + 1}: ${ids.join(", ")} → ${file}`);
});
if (!existsSync(join(hf, "frame-packets", "_role.md"))) fail("frame-packets.mjs wrote no _role.md");
