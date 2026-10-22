// Narrates a batch of texts with Kokoro (local, offline after the first model download).
//   node kokoro.mjs <jobs.json> <voice> [speed]   (speed: 1 = normal, 1.1 = a little faster)
// jobs.json: [{ "text": "...", "out": "/abs/path.wav", "speed"?: 0.95, "seed"?: 3 }, ...]
//
// Kokoro silently truncates anything past 510 phoneme tokens (~26 s), and punctuation barely changes
// its pause lengths. So each text is synthesized in chunks of 1–3 sentences, every chunk is trimmed to
// a short lead/tail, and the chunks are joined with designed pauses:
//   sentence 0.6 s · after a question 0.8 s · blank line (paragraph) 1.0 s · `[pause 800]` = 800 ms.
// Writes <out>.wav (16-bit, 24 kHz mono) and <out>.cues.json ([{ text, start, end }] per chunk, seconds).
// KOKORO_DTYPE=fp32 swaps the q8 model for the full-precision one (one-time ~326 MB download).
import { readFileSync, writeFileSync } from "node:fs";
import { KokoroTTS, TextSplitterStream } from "kokoro-js";

const [jobsFile, voice = "af_heart", speedArg = "1"] = process.argv.slice(2);
const speed = Number(speedArg) || 1;
const jobs = JSON.parse(readFileSync(jobsFile, "utf8"));

const SR = 24000;
const PAUSE = { sentence: 0.6, question: 0.8, paragraph: 1.0 };
const LEAD = 0.04; // seconds kept before the first audible sample of a chunk
const TAIL = 0.12; // and after the last one (Kokoro's own padding is ~0.3 s / ~0.47 s)

// Spoken forms for things Kokoro misreads ("e.g." → "E G", "1M" → "one M", "3x" → "three X", …).
// Scripts should already be written for the ear; this is the safety net.
const LEXICON = [
  [/\be\.g\.,?/gi, "for example,"],
  [/\bi\.e\.,?/gi, "that is,"],
  [/\bvs\.?(?=\s)/gi, "versus"],
  [/\betc\./gi, "and so on"],
  [/\band\/or\b/gi, "and or"],
  [/\bA\/B\b/g, "A B"],
  [/\bI\/O\b/g, "I O"],
  [/\b([A-Z][A-Za-z]*)\.md\b/g, "$1 dot M D"],
  [/\bQwen\b/g, "chwen"],
  [/(\d+(?:\.\d+)?)\s?[x×](?=\s|$|[.,;:!?])/g, "$1 times"],
  [/(\d+(?:\.\d+)?)\s?[kK]\b/g, "$1 thousand"],
  [/(\d+(?:\.\d+)?)\s?M\b/g, "$1 million"],
  [/(\d+)\s?ms\b/g, "$1 milliseconds"],
  [/\s*→\s*/g, " to "],
  [/\s*\(([^)]*)\)/g, ", $1,"], // kokoro-js deletes parentheses; make the aside a comma phrase
  [/,\s*([,.;:!?])/g, "$1"]
];
const speakable = text => LEXICON.reduce((t, [re, to]) => t.replace(re, to), text);

const sentences = text => {
  const splitter = new TextSplitterStream();
  splitter.push(text);
  return [...splitter];
};

/** Splits sentences over ~220 characters at clause marks, then at a space, so no chunk nears the token cap. */
const splitLong = sentence => {
  if (sentence.length <= 220) return [sentence];
  const pieces = [];
  let cur = "";
  for (const clause of sentence.split(/(?<=[;:—,])\s+/)) {
    if (cur && cur.length + clause.length + 1 > 200) {
      pieces.push(cur);
      cur = clause;
    } else cur = cur ? `${cur} ${clause}` : clause;
  }
  if (cur) pieces.push(cur);
  return pieces.flatMap(p => {
    if (p.length <= 260) return [p];
    const mid = p.lastIndexOf(" ", p.length / 2);
    return splitLong(p.slice(0, mid)).concat(splitLong(p.slice(mid + 1)));
  });
};

/**
 * Groups sentences into chunks: a short sentence (< 80 chars) joins its neighbour while the pair stays under 200.
 * A question always ends its chunk, so its answer gets a real pause instead of Kokoro's rushed ~0.25 s.
 */
const chunk = sents => {
  const out = [];
  let cur = "";
  for (const s of sents.flatMap(splitLong)) {
    if (!cur) cur = s;
    else if (!cur.endsWith("?") && (cur.length < 80 || s.length < 80) && cur.length + s.length < 200) cur += ` ${s}`;
    else {
      out.push(cur);
      cur = s;
    }
  }
  return cur ? [...out, cur] : out;
};

/** Chunks of a narration, each with the pause that follows it. */
const plan = text => {
  const units = [];
  for (const paragraph of speakable(text).split(/\n\s*\n/)) {
    const parts = paragraph.split(/\[pause\s+(\d+)\]/i);
    for (let p = 0; p < parts.length; p += 2) {
      const chunks = chunk(sentences(parts[p].trim()));
      chunks.forEach(c => units.push({ text: c, pause: c.endsWith("?") ? PAUSE.question : PAUSE.sentence }));
      if (units.length && parts[p + 1] !== undefined) units.at(-1).pause = Number(parts[p + 1]) / 1000;
    }
    if (units.length) units.at(-1).pause = Math.max(units.at(-1).pause, PAUSE.paragraph);
  }
  return units;
};

/** Trims a chunk to LEAD/TAIL around its audible part (-45 dBFS), with 10 ms fades. */
const trim = audio => {
  const threshold = 10 ** (-45 / 20);
  let start = 0;
  let end = audio.length - 1;
  while (start < end && Math.abs(audio[start]) < threshold) start++;
  while (end > start && Math.abs(audio[end]) < threshold) end--;
  const seg = audio.slice(Math.max(0, start - Math.round(LEAD * SR)), Math.min(audio.length, end + Math.round(TAIL * SR)));
  const fade = Math.round(0.01 * SR);
  for (let i = 0; i < fade && i < seg.length / 2; i++) {
    seg[i] *= i / fade;
    seg[seg.length - 1 - i] *= i / fade;
  }
  return seg;
};

const writeWav = (path, samples) => {
  const b = Buffer.alloc(44 + samples.length * 2);
  b.write("RIFF", 0);
  b.writeUInt32LE(36 + samples.length * 2, 4);
  b.write("WAVEfmt ", 8);
  b.writeUInt32LE(16, 16);
  b.writeUInt16LE(1, 20); // PCM
  b.writeUInt16LE(1, 22); // mono
  b.writeUInt32LE(SR, 24);
  b.writeUInt32LE(SR * 2, 28);
  b.writeUInt16LE(2, 32);
  b.writeUInt16LE(16, 34);
  b.write("data", 36);
  b.writeUInt32LE(samples.length * 2, 40);
  samples.forEach((v, i) => b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, v)) * 32767), 44 + 2 * i));
  writeFileSync(path, b);
};

const tts = await KokoroTTS.from_pretrained("onnx-community/Kokoro-82M-v1.0-ONNX", {
  dtype: process.env.KOKORO_DTYPE ?? "q8",
  device: "cpu"
});

for (const [i, job] of jobs.entries()) {
  const seed = job.seed ?? i; // seeds the pause jitter per scene, so an unchanged scene re-narrates identically
  const jobSpeed = job.speed ?? speed;
  const parts = [];
  const cues = [];
  let t = 0;
  const units = plan(job.text);
  for (const [u, unit] of units.entries()) {
    const raw = (await tts.generate(unit.text, { voice, speed: jobSpeed })).audio;
    if (raw.length / SR > 24 / jobSpeed) {
      throw new Error(`chunk too long, Kokoro may have truncated it: "${unit.text.slice(0, 80)}…"`);
    }
    const seg = trim(raw);
    parts.push(seg);
    cues.push({ text: unit.text, start: +t.toFixed(3), end: +(t + seg.length / SR).toFixed(3) });
    t += seg.length / SR;
    if (u < units.length - 1) {
      const gap = unit.pause + ((((seed * 31) + u * 37) % 7) - 3) * 0.02; // ±60 ms, so the rhythm isn't metronomic
      parts.push(new Float32Array(Math.round(gap * SR)));
      t += gap;
    }
  }
  const all = new Float32Array(parts.reduce((n, p) => n + p.length, 0));
  let offset = 0;
  for (const p of parts) {
    all.set(p, offset);
    offset += p.length;
  }
  writeWav(job.out, all);
  writeFileSync(job.out.replace(/\.wav$/, ".cues.json"), JSON.stringify(cues));
  process.stdout.write(`  kokoro ${i + 1}/${jobs.length}: ${units.length} chunks, ${t.toFixed(1)}s\n`);
}
