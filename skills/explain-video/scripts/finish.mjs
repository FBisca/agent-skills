#!/usr/bin/env node
// Renders an explain-video project and masters its audio to YouTube's reference (-14 LUFS, -1 dBTP):
//   node finish.mjs <project-dir> [--out <file.mp4>] [--quality draft|looks|delivery]
// → <videos-dir>/<slug>.mp4 next to the project by default. The raw render is deleted once the master
//   is verified.
import { existsSync, mkdirSync, rmSync, statSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fail, hf, hfCli, master, measure, parseArgs } from "./lib.mjs";

const { positional: [projectArg], opts } = parseArgs(["out", "quality"]);
if (!projectArg) fail("usage: finish.mjs <project-dir> [--out <file.mp4>] [--quality draft|looks|delivery]");
const dir = resolve(projectArg);
if (!existsSync(join(dir, "index.html"))) fail(`${dir} has no index.html: run assemble.mjs first`);
const slug = basename(dir);
const out = resolve(opts.out ?? join(dirname(dir), `${slug}.mp4`));
const raw = join(dir, "renders", `${slug}.raw.mp4`);
mkdirSync(dirname(raw), { recursive: true });

const started = Date.now();
hf(hfCli(dir), ["render", ".", "-o", raw, "--skill", "general-video", ...(opts.quality ? ["-q", opts.quality] : [])], { cwd: dir });
console.log("Mastering the audio…");
master(raw, out);
const m = measure(out);
if (!(Math.abs(m.lufs + 14) <= 0.5 && m.peak <= -1)) {
  fail(`Master is off target (I ${m.lufs} LUFS, true peak ${m.peak} dBTP); raw render kept at ${raw}`);
}
rmSync(raw);
const mins = `${Math.floor(m.seconds / 60)}m${String(Math.round(m.seconds % 60)).padStart(2, "0")}s`;
console.log(
  `\nVideo: ${out}\n  ${mins} · ${m.lufs} LUFS · ${m.peak} dBTP · ${(statSync(out).size / 1e6).toFixed(0)} MB · built in ${Math.round((Date.now() - started) / 60000)} min`
);
