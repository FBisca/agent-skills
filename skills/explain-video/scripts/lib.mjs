// Shared helpers for the explain-video scripts.
import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const SKILL_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const NARRATOR = join(SKILL_DIR, "narrator");

export const fail = message => {
  console.error(message);
  process.exit(1);
};

/** Runs a command with its output streamed; a failure ends this script with the command named. */
export const run = (cmd, args, opts = {}) => {
  try {
    return execFileSync(cmd, args, { stdio: "inherit", ...opts });
  } catch (e) {
    fail(`\n✗ failed (exit ${e.status ?? "?"}): ${cmd} ${args.join(" ")}`);
  }
};

/** `node x.mjs <positional…> [--flag] [--name value]`; `valued` names the options that take a value. */
export const parseArgs = (valued = []) => {
  const argv = process.argv.slice(2);
  const positional = [];
  const opts = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) positional.push(a);
    else if (valued.includes(a.slice(2))) opts[a.slice(2)] = argv[++i];
    else opts[a.slice(2)] = true;
  }
  return { positional, opts };
};

// The HyperFrames toolchain v3 was built with, frozen: the CLI version every project pins, and the workflow
// pieces 0.8.185 dropped (presets, blueprints, frame packets, assembly) vendored beside this file's folder.
// Upgrading means re-vendoring from a newer release and re-running a project end to end.
export const HF_VERSION = "0.8.184";
export const HF_DIR = join(SKILL_DIR, `hyperframes-${HF_VERSION}`);
export const hfSkill = name => join(HF_DIR, name);

/** The project's pinned `hyperframes@x.y.z` (from its package.json scripts), so every command matches its renders. */
export const hfCli = projectDir => {
  const pkg = JSON.parse(readFileSync(join(projectDir, "package.json"), "utf8"));
  return Object.values(pkg.scripts ?? {}).join(" ").match(/hyperframes@[\w.-]+/)?.[0] ?? `hyperframes@${HF_VERSION}`;
};

/** Runs the HyperFrames CLI without its side effect of re-linking global agent skills. */
export const hf = (cli, args, opts = {}) =>
  run("npx", ["--yes", cli, ...args], { ...opts, env: { ...process.env, HYPERFRAMES_SKIP_SKILLS: "1" } });

/** The `## Frame N` blocks of a project's STORYBOARD.md, in document order. */
export const storyboardFrames = projectDir => {
  const md = readFileSync(join(projectDir, "STORYBOARD.md"), "utf8");
  return md
    .split(/^## Frame /m)
    .slice(1)
    .map(block => {
      const field = name => block.match(new RegExp(`^- ${name}:\\s*(.+)$`, "m"))?.[1].trim();
      const seconds = name => (field(name) === undefined ? undefined : Number.parseFloat(field(name)));
      return { n: Number.parseInt(block, 10), src: field("src"), duration: seconds("duration"), poster: seconds("poster") };
    });
};

/** Seconds of audio in a PCM WAV file. */
export const wavSeconds = path => {
  const b = readFileSync(path);
  const rate = b.readUInt32LE(24);
  const blockAlign = b.readUInt16LE(32);
  for (let o = 12; o + 8 <= b.length; ) {
    const size = b.readUInt32LE(o + 4);
    if (b.toString("ascii", o, o + 4) === "data") return size / (rate * blockAlign);
    o += 8 + size + (size % 2);
  }
  throw new Error(`no data chunk in ${path}`);
};

// Broadcast-style voice chain, then a two-pass linear loudnorm to YouTube's reference (-14 LUFS, -1 dBTP).
// A pink-noise room tone at about -65 dBFS fills the digital silence between scenes.
export const master = (input, output) => {
  const chain =
    "highpass=f=70,equalizer=f=300:t=q:w=1.2:g=-2,equalizer=f=4500:t=q:w=1.5:g=1.5," +
    "deesser=i=0.3:m=0.5:f=0.5,acompressor=threshold=-24dB:ratio=2:attack=10:release=200:knee=4:makeup=2dB," +
    "volume=10dB,alimiter=limit=-2dB:attack=3:release=80:level=false";
  const bed = "anoisesrc=color=pink:amplitude=0.003:sample_rate=48000,aformat=channel_layouts=stereo";
  const graph = loudnorm => `[0:a]${chain}[v];${bed}[n];[v][n]amix=inputs=2:duration=first:normalize=0,${loudnorm}[o]`;
  // loudnorm's linear gain can lift the pre-limiter's -2 dB ceiling past the target; a 4x-oversampled
  // limiter after it catches those true peaks without moving the loudness.
  const truePeakGuard = "aresample=192000,alimiter=limit=-2dB:attack=1:release=50:level=false,aresample=48000";
  const target = "I=-14:TP=-1.5:LRA=9"; // -1.5 leaves room for the AAC encode overshoot (lands near -1.1 to -1.7 dBTP)
  const probe = spawnSync(
    "ffmpeg",
    ["-hide_banner", "-nostats", "-i", input, "-filter_complex", graph(`loudnorm=${target}:print_format=json`), "-map", "[o]", "-f", "null", "-"],
    { encoding: "utf8" }
  );
  // ffmpeg prints more stderr after the JSON report, so pick the object out instead of parsing the tail.
  const report = probe.stderr.match(/\{[^{}]*"input_i"[^{}]*\}/);
  if (!report) throw new Error(`loudnorm measurement failed:\n${probe.stderr.slice(-2000)}`);
  const m = JSON.parse(report[0]);
  const measured = `measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}`;
  execFileSync("ffmpeg", [
    "-hide_banner", "-loglevel", "error", "-y", "-i", input,
    "-filter_complex", graph(`loudnorm=${target}:${measured}:linear=true,${truePeakGuard}`),
    "-map", "0:v", "-map", "[o]", "-c:v", "copy", "-c:a", "aac", "-b:a", "384k", "-movflags", "+faststart", output
  ]);
};

/** Integrated loudness (LUFS), true peak (dBTP) and duration (s) of a media file. */
export const measure = file => {
  const { stderr } = spawnSync("ffmpeg", ["-hide_banner", "-nostats", "-i", file, "-af", "ebur128=peak=true", "-f", "null", "-"], {
    encoding: "utf8"
  });
  const summary = stderr.slice(stderr.lastIndexOf("Summary:"));
  const [, h, min, s] = stderr.match(/Duration:\s*(\d+):(\d+):([\d.]+)/) ?? [];
  return {
    lufs: Number(summary.match(/I:\s+(-?[\d.]+) LUFS/)?.[1]),
    peak: Number(summary.match(/Peak:\s+(-?[\d.]+) dBFS/)?.[1]),
    seconds: Number(h) * 3600 + Number(min) * 60 + Number(s)
  };
};
