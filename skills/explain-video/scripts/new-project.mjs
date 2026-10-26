#!/usr/bin/env node
// Creates the HyperFrames project for an explain-video script, then narrates it:
//   node new-project.mjs <videos-dir>/<slug>.json [--preset code-editorial] [--voice af_heart]
// → <videos-dir>/<slug>/: `hyperframes init` (general-video), frame.md from the design preset with its fonts
//   staged in assets/fonts, the narration (narrate.mjs) and BRIEF.md. On an existing project it only re-narrates.
//   The CLI is pinned to HF_VERSION (lib.mjs); init skips its global skill re-linking.
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fail, hf, HF_VERSION, hfSkill, parseArgs, run, SKILL_DIR } from "./lib.mjs";

const { positional: [scriptArg], opts } = parseArgs(["preset", "voice"]);
if (!scriptArg) fail("usage: new-project.mjs <videos-dir>/<slug>.json [--preset code-editorial] [--voice af_heart]");
const scriptPath = resolve(scriptArg);
const script = JSON.parse(readFileSync(scriptPath, "utf8"));
for (const key of ["title", "message", "scenes"]) {
  if (!script[key]) fail(`${scriptArg} has no "${key}" (format: references/script.md)`);
}
const slug = basename(scriptPath, ".json");
const videosDir = dirname(scriptPath);
const dir = join(videosDir, slug);
const preset = opts.preset ?? script.preset ?? "code-editorial";
const voice = opts.voice ?? script.voice ?? "af_heart";
const fresh = !existsSync(join(dir, "hyperframes.json"));

// build-frame.mjs copies the preset's FRAME.md but (as of 0.8.184) doesn't stage the preset's own fonts,
// so compositions would fall back to system faces. Copy them and append the @font-face block frame.md cites.
const stageFonts = fontsDir => {
  if (!existsSync(fontsDir)) return;
  const target = join(dir, "assets", "fonts");
  mkdirSync(target, { recursive: true });
  const files = readdirSync(fontsDir).filter(f => /\.(woff2|txt)$/.test(f));
  files.forEach(f => copyFileSync(join(fontsDir, f), join(target, f)));
  const frameMd = join(dir, "frame.md");
  const md = readFileSync(frameMd, "utf8");
  if (md.includes("@font-face{")) return;
  const families = [...new Set([...md.matchAll(/fontFamily:\s*"([^"]+)"/g)].map(m => m[1]))];
  const faces = files.flatMap(f => {
    const [, name, weight] = f.match(/^(.+)-(\d{3})\.woff2$/) ?? [];
    if (!name) return [];
    const family = families.find(fam => fam.replace(/\s/g, "").toLowerCase() === name.toLowerCase()) ?? name;
    return [`@font-face{font-family:"${family}";font-weight:${weight};font-style:normal;font-display:block;src:url("assets/fonts/${f}") format("woff2");}`];
  });
  writeFileSync(
    frameMd,
    `${md.trimEnd()}\n\n## Font faces (staged in assets/fonts/; paste inside every composition's <template> <style>)\n\n\`\`\`css\n${faces.join("\n")}\n\`\`\`\n`
  );
};

const writeBrief = () => {
  const timing = JSON.parse(readFileSync(join(dir, ".hyperframes", "vo-durations.json"), "utf8"));
  const total = timing.reduce((sum, t) => sum + t.duration, 0);
  const length = `${Math.floor(total / 60)}m${String(Math.round(total % 60)).padStart(2, "0")}s`;
  const q = value => JSON.stringify(value ?? "");
  const sources = (script.sources ?? []).map(s => `- ${s}: the facts. Every number and claim on screen comes from here or the script.`);
  writeFileSync(
    join(dir, "BRIEF.md"),
    `---
workflow: general-video
flow: automation
storyboard: no
message: ${q(script.message)}
destination: ${script.destination ?? "youtube"}
aspect: ${script.aspect ?? "1920x1080"}
language: ${script.language ?? "en"}
audience: ${q(script.audience)}
length: ${length} (narration-driven)
angle: ${q(script.angle)}
narration: yes (verbatim, locked)
voice: ${voice}
---

## Intent

${script.title}: a narrated tutorial built by /explain-video. The narration teaches; every scene gets its own invented visual idea, timed to the voice, in the ${preset} look.

## Assets

- assets/vo/sNN.wav: locked narration, one file per scene (Kokoro ${voice}, explain-video narrator). Frame N plays sNN.wav.
- .hyperframes/cues.md: each scene's length and sentence start times; .hyperframes/vo-durations.json has the lengths as data.
- ../${slug}.json: the script (narration and visual hints).
${sources.join("\n")}

## Customizations

- Voice: local Kokoro, offline. Music: none. Captions: none; the bottom ~17% stays clear.
- Audio is mastered to −14 LUFS / −1 dBTP after the render (explain-video finish.mjs).

## Notes

- Storyboard and visual direction follow explain-video's references/visuals.md.
`
  );
};

if (fresh) {
  const resolution = { "1920x1080": "landscape", "1080x1920": "portrait", "1080x1080": "square" }[script.aspect ?? "1920x1080"];
  if (!resolution) fail(`aspect must be 1920x1080, 1080x1920 or 1080x1080, not ${script.aspect}`);
  hf(`hyperframes@${HF_VERSION}`, ["init", slug, "--non-interactive", "--example=blank", "--skill=general-video", "--resolution", resolution], { cwd: videosDir });
  const presets = join(hfSkill("hyperframes-creative"), "frame-presets");
  if (!existsSync(join(presets, preset, "FRAME.md"))) fail(`no design preset "${preset}" in ${presets}`);
  run("node", [join(hfSkill("faceless-explainer"), "scripts", "build-frame.mjs"), "--preset", preset, "--hyperframes", dir, "--preset-dir", presets]);
  stageFonts(join(presets, preset, "fonts"));
}
run("node", [join(SKILL_DIR, "scripts", "narrate.mjs"), scriptPath, dir, "--voice", voice]);
if (fresh) writeBrief();
console.log(`\nProject ready: ${dir}\nNext: write STORYBOARD.md (references/visuals.md), timing reveals from .hyperframes/cues.md.`);
