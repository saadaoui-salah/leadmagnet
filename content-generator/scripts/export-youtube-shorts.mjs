#!/usr/bin/env node

/**
 * export-youtube-shorts.mjs
 *
 * Renders both YouTube Shorts compositions to MP4.
 *
 * Usage:
 *   node scripts/export-youtube-shorts.mjs
 *
 * Output:
 *   out/youtube-shorts/short-winner-vs-runner-up.mp4
 *   out/youtube-shorts/short-winner-vs-loser.mp4
 */

import { execSync } from "child_process";
import { existsSync, mkdirSync } from "fs";
import { join, resolve } from "path";

const ROOT = resolve(import.meta.dirname, "..");
const OUTPUT_DIR = join(ROOT, "out", "youtube-shorts");

if (!existsSync(OUTPUT_DIR)) {
  mkdirSync(OUTPUT_DIR, { recursive: true });
}

const compositions = [
  {
    id: "YouTubeShortsWinnerVsRunnerUp",
    output: join(OUTPUT_DIR, "short-winner-vs-runner-up.mp4"),
  },
  {
    id: "YouTubeShortsWinnerVsLoser",
    output: join(OUTPUT_DIR, "short-winner-vs-loser.mp4"),
  },
];

for (const comp of compositions) {
  console.log(`\n=== Rendering: ${comp.id} ===`);
  console.log(`  Output: ${comp.output}`);

  const cmd = `npx remotion render "${comp.id}" --output="${comp.output}" --codec=h264 --crf=18 --preset=medium`;

  try {
    execSync(cmd, {
      stdio: "inherit",
      cwd: ROOT,
      timeout: 300000,
    });
    console.log(`  [DONE] ${comp.id}`);
  } catch (err) {
    console.error(`  [FAIL] ${comp.id}: ${err.message?.substring(0, 300)}`);
    process.exitCode = 1;
  }
}

console.log("\n[Done] All Shorts rendered.");
