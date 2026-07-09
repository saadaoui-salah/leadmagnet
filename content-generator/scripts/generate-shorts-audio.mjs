#!/usr/bin/env node

/**
 * generate-shorts-audio.mjs
 *
 * Generates TTS audio for YouTube Shorts scenes using Piper-TTS.
 *
 * Prerequisites:
 *   1. Install Piper: https://github.com/rhasspy/piper/releases
 *      Download piper binary and a voice model (e.g. en_US-lessac-medium.onnx)
 *   2. Set PIPER_PATH and PIPER_VOICE env vars, or edit defaults below
 *
 * Usage:
 *   node scripts/generate-shorts-audio.mjs [--mode winner-vs-runner-up|winner-vs-loser|all]
 *
 * Output:
 *   public/audio/shorts/scene-01.wav .. scene-07.wav
 *   src/data/generatedShortsNarration.json (for Remotion to consume)
 */

import { execSync } from "child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join, resolve } from "path";

const ROOT = resolve(import.meta.dirname, "..");
const SCRIPT_DIR = join(ROOT, "scripts");
const SRC_DIR = join(ROOT, "src", "data");
const AUDIO_DIR = join(ROOT, "public", "audio", "shorts");

const PIPER_PATH = process.env.PIPER_PATH || "piper";
const PIPER_VOICE = process.env.PIPER_VOICE || "en_US-lessac-medium.onnx";
const PIPER_VOICE_PATH = process.env.PIPER_VOICE_PATH || join(ROOT, "voices", PIPER_VOICE);

const SCENE_COUNT = 7;
const SCENE_LABELS = [
  "hook",
  "zip-a",
  "zip-b",
  "head-to-head",
  "key-difference",
  "takeaway",
  "cta",
];

function ensureDir(dir) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

function loadNarrationText(mode) {
  const path = join(SRC_DIR, "generatedShortsCopy.json");
  if (!existsSync(path)) {
    console.error(`[ERROR] Narration file not found: ${path}`);
    console.error("        Run: python scripts/generate_market_copy.py first");
    process.exit(1);
  }

  const data = JSON.parse(readFileSync(path, "utf-8"));
  const key = mode === "winner-vs-runner-up" ? "runnerUp" : "winnerVsLoser";
  const scenes = data?.shortsCopy?.[key]?.scenes;
  if (!scenes || scenes.length === 0) {
    console.error(`[ERROR] No narration scenes found for mode: ${mode}`);
    process.exit(1);
  }
  return scenes;
}

function generateWav(text, outputPath) {
  const escapedText = text.replace(/"/g, '\\"');
  // Piper with --output-raw writes raw WAV to stdout
  const cmd = `"${PIPER_PATH}" --model "${PIPER_VOICE_PATH}" --output-raw -q <<< "${escapedText}" > "${outputPath}"`;
  try {
    execSync(cmd, { stdio: "pipe", timeout: 30000 });
    return true;
  } catch (err) {
    console.error(`  [FAIL] Piper failed for: ${text.substring(0, 60)}...`);
    console.error(`         Error: ${err.message?.substring(0, 200)}`);
    return false;
  }
}

function generateSilentWav(outputPath, durationMs = 3000) {
  // Generate a minimal silent WAV as fallback when Piper is not available
  const sampleRate = 22050;
  const numSamples = (sampleRate * durationMs) / 1000;
  const dataSize = numSamples * 2; // 16-bit mono
  const buffer = Buffer.alloc(44 + dataSize, 0);

  // WAV header
  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write("WAVE", 8);
  buffer.write("fmt ", 12);
  buffer.writeUInt32LE(16, 16);        // fmt chunk size
  buffer.writeUInt16LE(1, 20);          // PCM
  buffer.writeUInt16LE(1, 22);          // mono
  buffer.writeUInt32LE(sampleRate, 24); // sample rate
  buffer.writeUInt32LE(sampleRate * 2, 28); // byte rate
  buffer.writeUInt16LE(2, 32);          // block align
  buffer.writeUInt16LE(16, 34);         // bits per sample
  buffer.write("data", 36);
  buffer.writeUInt32LE(dataSize, 40);

  writeFileSync(outputPath, buffer);
}

function processMode(mode) {
  console.log(`\n=== Generating audio for: ${mode} ===`);
  const scenes = loadNarrationText(mode);
  const narration = [];

  ensureDir(AUDIO_DIR);

  let piperAvailable = true;

  for (let i = 0; i < SCENE_COUNT; i++) {
    const scene = scenes[i] || { text: "" };
    const outputPath = join(AUDIO_DIR, `scene-${String(i + 1).padStart(2, "0")}.wav`);
    const label = SCENE_LABELS[i] || `scene-${i + 1}`;

    console.log(`  [${i + 1}/${SCENE_COUNT}] ${label}`);

    if (scene.text && piperAvailable) {
      const ok = generateWav(scene.text, outputPath);
      if (!ok) {
        piperAvailable = false;
        console.log("  [FALLBACK] Piper unavailable. Generating silent WAVs.");
        generateSilentWav(outputPath);
      }
    } else {
      generateSilentWav(outputPath);
    }

    narration.push({
      text: scene.text || "",
      audioFile: `scene-${String(i + 1).padStart(2, "0")}.wav`,
    });
  }

  // Write narration JSON for Remotion
  const outputPath = join(SRC_DIR, "generatedShortsNarration.json");
  const existing = existsSync(outputPath)
    ? JSON.parse(readFileSync(outputPath, "utf-8"))
    : {};
  const key = mode === "winner-vs-runner-up" ? "runnerUp" : "winnerVsLoser";
  existing[key] = narration;
  writeFileSync(outputPath, JSON.stringify(existing, null, 2));
  console.log(`  [SAVED] Narration JSON: ${outputPath}`);
}

// Main
const modeArg = process.argv[2] || "all";

if (modeArg === "all") {
  processMode("winner-vs-runner-up");
  processMode("winner-vs-loser");
} else if (modeArg === "winner-vs-runner-up" || modeArg === "winner-vs-loser") {
  processMode(modeArg);
} else {
  console.error("Usage: node scripts/generate-shorts-audio.mjs [--mode winner-vs-runner-up|winner-vs-loser|all]");
  process.exit(1);
}

console.log("\n[Done] Audio generation complete.");
