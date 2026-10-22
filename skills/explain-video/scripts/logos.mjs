#!/usr/bin/env node
// Stages official brand marks for the products and companies a video names on screen:
//   node logos.mjs <project-dir> <slug…>          e.g. claude anthropic github
// Fetches each mark from Simple Icons (CC0 SVGs traced from official brand assets, pinned version) into
// assets/logos/<slug>.svg and records title, brand colour, source and guidelines in assets/logos/logos.json.
// A slug Simple Icons doesn't have is reported: that product stays a wordmark in its official casing.
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { fail, parseArgs } from "./lib.mjs";

const SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.35.0";

const { positional: [projectArg, ...slugs] } = parseArgs();
if (!projectArg || !slugs.length) fail("usage: logos.mjs <project-dir> <slug…>  (slugs as on simpleicons.org)");
const dir = join(resolve(projectArg), "assets", "logos");
mkdirSync(dir, { recursive: true });

const data = await (await fetch(`${SIMPLE_ICONS}/data/simple-icons.json`)).json();
const icons = Array.isArray(data) ? data : data.icons;
const slugOf = icon => icon.slug ?? icon.title.toLowerCase().replace(/\+/g, "plus").replace(/[^a-z0-9]/g, "");
const manifestFile = join(dir, "logos.json");
const manifest = existsSync(manifestFile) ? JSON.parse(readFileSync(manifestFile, "utf8")) : {};

for (const slug of slugs) {
  const icon = icons.find(i => slugOf(i) === slug);
  const res = await fetch(`${SIMPLE_ICONS}/icons/${slug}.svg`);
  if (!icon || !res.ok) {
    console.log(`  ${slug}: no official mark in Simple Icons; use the name as a wordmark`);
    continue;
  }
  const svg = await res.text();
  writeFileSync(join(dir, `${slug}.svg`), svg);
  manifest[slug] = {
    title: icon.title,
    hex: `#${icon.hex}`,
    path: svg.match(/ d="([^"]+)"/)[1],
    source: icon.source,
    guidelines: icon.guidelines ?? null,
    file: `assets/logos/${slug}.svg`
  };
  console.log(`  ${slug}: ${icon.title} #${icon.hex} → assets/logos/${slug}.svg`);
}
writeFileSync(manifestFile, JSON.stringify(manifest, null, 1));
