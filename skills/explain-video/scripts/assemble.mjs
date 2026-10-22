#!/usr/bin/env node
// Assembles and checks an explain-video project once every frame is built:
//   node assemble.mjs <project-dir>
// 1. preflight: every Frame block's src and .motion.json exist and every font frame.md cites is on disk;
//    ids/classes that start with a digit are reported
// 2. faceless-explainer's assemble-index.mjs → index.html (frames + each scene's voice), then
//    transitions.mjs inject + verify (it extends the outgoing scene only, so the voices stay in sync)
// 3. the project's pinned `hyperframes check` (lint, runtime, layout, motion, contrast)
// 4. one snapshot per frame at its poster time → .hyperframes/contact/contact-sheet*.jpg
// Stops at the first failing stage.
import { existsSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { fail, hf, hfCli, hfSkill, parseArgs, run, storyboardFrames } from "./lib.mjs";

const { positional: [projectArg] } = parseArgs();
if (!projectArg) fail("usage: assemble.mjs <project-dir>");
const dir = resolve(projectArg);
const frames = storyboardFrames(dir);

const problems = [];
const warnings = [];
for (const f of frames) {
  const html = f.src && join(dir, f.src);
  if (!html || !existsSync(html)) {
    problems.push(`frame ${f.n}: missing ${f.src ?? "src"}`);
    continue;
  }
  if (!existsSync(html.replace(/\.html$/, ".motion.json"))) problems.push(`frame ${f.n}: missing its .motion.json sidecar`);
  // The frame's own id (its file name) starts with a digit by HyperFrames convention; names derived from it
  // only cost CSS escapes, but they break selector-based tools (animation-map), so they are reported, not fatal.
  const frameId = f.src.split("/").pop().replace(/\.html$/, "");
  const names = [...readFileSync(html, "utf8").matchAll(/\b(?:class|id)="([^"]*)"/g)].flatMap(m => m[1].split(/\s+/));
  const bad = [...new Set(names.filter(name => /^\d/.test(name) && name !== frameId))];
  if (bad.length) warnings.push(`frame ${f.n}: ${bad.length} ids/classes start with a digit (${bad.slice(0, 3).join(", ")}…); next time prefix them, e.g. f${String(f.n).padStart(2, "0")}-…`);
}
for (const [, url] of readFileSync(join(dir, "frame.md"), "utf8").matchAll(/url\("([^"]+)"\)/g)) {
  if (!existsSync(join(dir, url))) problems.push(`frame.md cites a font that isn't on disk: ${url}`);
}
warnings.forEach(w => console.log(`  warn ${w}`));
if (problems.length) fail(`Preflight failed:\n${problems.map(p => `  ${p}`).join("\n")}`);

const scripts = join(hfSkill("faceless-explainer"), "scripts");
run("node", [join(scripts, "assemble-index.mjs"), "--storyboard", "STORYBOARD.md", "--hyperframes", ".", "--audio-meta", "audio_meta.json"], { cwd: dir });
run("node", [join(scripts, "transitions.mjs"), "inject", "--storyboard", "./STORYBOARD.md", "--hyperframes", "."], { cwd: dir });
run("node", [join(scripts, "transitions.mjs"), "verify", "--storyboard", "./STORYBOARD.md", "--index", "./index.html"], { cwd: dir });

const cli = hfCli(dir);
hf(cli, ["check"], { cwd: dir });

let clock = 0;
const posters = frames.map(f => {
  const at = clock + (f.poster ?? f.duration * 0.85);
  clock += f.duration;
  return at.toFixed(2);
});
const contact = join(dir, ".hyperframes", "contact");
rmSync(contact, { recursive: true, force: true });
hf(cli, ["snapshot", ".", "--at", posters.join(","), "--no-end", "-o", contact], { cwd: dir });
const sheets = readdirSync(contact).filter(f => f.startsWith("contact-sheet")).sort().map(f => join(contact, f));
console.log(`\nAssembled and checked. Inspect the contact sheets (frames in storyboard order, each at its poster time):\n${sheets.join("\n")}`);
