#!/usr/bin/env node
// Narrates an explain-video script into its HyperFrames project with Kokoro (local, offline):
//   node narrate.mjs <script.json> <project-dir> [--voice af_heart]
//   node narrate.mjs <script.json> --lint        # check the narration only; exits 1 on findings
// Writes assets/vo/sNN.wav (+ sNN.cues.json), audio_meta.json (voices; existing bgm/sfx kept),
// .hyperframes/vo-durations.json and .hyperframes/cues.md: each scene's length and the start time of every
// sentence, which the storyboard times its reveals to. Frame N plays sNN.wav.
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fail, NARRATOR, parseArgs, wavSeconds } from "./lib.mjs";

// Kokoro clips come back trimmed to ~40 ms lead / ~120 ms tail, so the silence after a scene is set here:
// scene.pauseAfter, else these defaults (a chapter card gets a longer beat).
const PAUSE_AFTER = { chapter: 1.0, default: 0.7 };
const SILENT_SECONDS = 3; // a scene without narration, unless it sets `seconds`

// Things Kokoro reads badly or ignores. kokoro.mjs rewrites the common ones; the rest is on the script.
const LINT = [
  [/\$\d/, "currency in digits (write \"twelve dollars\")"],
  [/\b\d+(?:\.\d+)?\s?[kKM]\b|\b\d+x\b/, "abbreviated number (write \"one million\", \"three times\")"],
  [/\b\d{5,}\b/, "long number"],
  [/[\/→]/, "slash or arrow"],
  [/\b(?:NEVER|ALWAYS|MUST|NOT|DON'T|IMPORTANT)\b/, "capitals for emphasis (Kokoro ignores them; use a short sentence)"]
];

const { positional: [scriptArg, projectArg], opts } = parseArgs(["voice"]);
if (!scriptArg || (!projectArg && !opts.lint)) {
  fail("usage: narrate.mjs <script.json> <project-dir> [--voice af_heart]\n       narrate.mjs <script.json> --lint");
}
const script = JSON.parse(readFileSync(resolve(scriptArg), "utf8"));
const scenes = script.scenes;
const spoken = i => Boolean(scenes[i].narration?.trim());

const findings = scenes.flatMap((scene, i) => {
  const text = scene.narration ?? "";
  const words = text.split(/\s+/).filter(Boolean).length;
  return [
    ...LINT.flatMap(([re, why]) => text.match(re)?.slice(0, 1).map(m => `scene ${i + 1}: ${why}: "${m}"`) ?? []),
    ...(words > 110 ? [`scene ${i + 1}: ${words} words, consider splitting the scene`] : [])
  ];
});
findings.forEach(f => console.log(`  lint ${f}`));
if (opts.lint) process.exit(findings.length ? 1 : 0);

const dir = resolve(projectArg);
const voDir = join(dir, "assets", "vo");
const hfDir = join(dir, ".hyperframes");
mkdirSync(voDir, { recursive: true });
mkdirSync(hfDir, { recursive: true });
const pad = i => String(i + 1).padStart(2, "0");
const wavOf = i => join(voDir, `s${pad(i)}.wav`);

// Voice files of scenes that were removed or went silent would otherwise still play.
for (const file of readdirSync(voDir)) {
  const n = Number(file.match(/^s(\d+)\.(?:wav|cues\.json)$/)?.[1]);
  if (n && (n > scenes.length || !spoken(n - 1))) rmSync(join(voDir, file));
}

if (!existsSync(join(NARRATOR, "node_modules", "kokoro-js"))) {
  console.log("Installing the narrator (first run only)…");
  execFileSync("pnpm", ["install"], { cwd: NARRATOR, stdio: "inherit" });
}
const voice = opts.voice ?? script.voice ?? "af_heart";
// One process for every scene: the model loads once.
const jobs = scenes.flatMap((scene, i) => (spoken(i) ? [{ text: scene.narration, out: wavOf(i), speed: scene.speed, seed: i + 1 }] : []));
console.log(`Narrating ${jobs.length} scenes (Kokoro ${voice})…`);
const jobsFile = join(hfDir, "narration-jobs.json");
writeFileSync(jobsFile, JSON.stringify(jobs));
execFileSync("node", ["kokoro.mjs", jobsFile, voice, String(script.speed ?? 1)], { cwd: NARRATOR, stdio: "inherit" });
rmSync(jobsFile);

const round = x => Math.round(x * 100) / 100;
let clock = 0;
const timing = scenes.map((scene, i) => {
  const vo = spoken(i) ? round(wavSeconds(wavOf(i))) : 0;
  const chapter = scene.chapter || scene.type === "title";
  const pause = spoken(i) ? (scene.pauseAfter ?? (chapter ? PAUSE_AFTER.chapter : PAUSE_AFTER.default)) : 0;
  const duration = spoken(i) ? round(vo + pause) : (scene.seconds ?? SILENT_SECONDS);
  const cues = spoken(i) ? JSON.parse(readFileSync(wavOf(i).replace(/\.wav$/, ".cues.json"), "utf8")) : [];
  const at = round(clock);
  clock += duration;
  return { n: pad(i), id: scene.id ?? null, vo, pause, duration, at, cues };
});

const durationsFile = join(hfDir, "vo-durations.json");
const before = existsSync(durationsFile) ? JSON.parse(readFileSync(durationsFile, "utf8")) : [];
writeFileSync(durationsFile, JSON.stringify(timing.map(({ cues, ...t }) => t), null, 1));

const metaFile = join(dir, "audio_meta.json");
const meta = existsSync(metaFile) ? JSON.parse(readFileSync(metaFile, "utf8")) : { bgm: null, sfx: [] };
meta.voices = timing.flatMap((t, i) => (spoken(i) ? [{ frame: i + 1, path: `assets/vo/s${t.n}.wav` }] : []));
writeFileSync(metaFile, JSON.stringify(meta, null, 1));

// A chunk's start is exact; later sentences inside the chunk are placed by their share of its characters.
const sentenceLines = cue => {
  const parts = cue.text.split(/(?<=[.?!])\s+/);
  const total = parts.reduce((sum, p) => sum + p.length, 0);
  let offset = 0;
  return parts.map((text, k) => {
    const start = cue.start + ((cue.end - cue.start) * offset) / total;
    offset += text.length;
    return `- ${k ? "~" : ""}${start.toFixed(2)}  ${text}`;
  });
};
writeFileSync(
  join(hfDir, "cues.md"),
  [
    `# Cue sheet: ${script.title ?? ""}`,
    "",
    "Seconds from each scene's start (`~` = estimated inside a spoken chunk). Time every reveal to the line it illustrates.",
    ...timing.flatMap(t => [
      "",
      `## ${t.n}${t.id ? ` ${t.id}` : ""}: ${t.duration.toFixed(2)} s (voice ${t.vo.toFixed(2)} + pause ${t.pause.toFixed(2)}), starts at ${t.at.toFixed(2)} s`,
      ...t.cues.flatMap(sentenceLines)
    ])
  ].join("\n") + "\n"
);

timing.forEach(t => console.log(`  ${t.n} ${(t.id ?? "").padEnd(22)} ${t.duration.toFixed(2).padStart(6)} s`));
console.log(`Total ${Math.floor(clock / 60)}m${String(Math.round(clock % 60)).padStart(2, "0")}s → ${join(hfDir, "cues.md")}`);
const changed = timing.filter((t, i) => before[i] && Math.abs(before[i].duration - t.duration) > 0.05);
if (changed.length) {
  console.log(
    `Timing changed: ${changed.map(t => `${t.n} (${before[Number(t.n) - 1].duration} → ${t.duration} s)`).join(", ")}.` +
      " Update those Frame blocks' duration and Scene times from cues.md, then rebuild them."
  );
}
