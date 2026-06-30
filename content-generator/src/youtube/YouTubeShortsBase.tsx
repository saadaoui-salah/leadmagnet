import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ShortsComparison, SceneAudio, CaptionWord } from "./data/types";
import { Scene01Hook } from "./slides/Scene01Hook";
import { Scene02ZipA } from "./slides/Scene02ZipA";
import { Scene03ZipB } from "./slides/Scene03ZipB";
import { Scene04HeadToHead } from "./slides/Scene04HeadToHead";
import { Scene05KeyDifference } from "./slides/Scene05KeyDifference";
import { Scene06InvestorTakeaway } from "./slides/Scene06InvestorTakeaway";
import { Scene07Cta } from "./slides/Scene07Cta";
import { CaptionsOverlay, textToEvenCaptions } from "./components/CaptionsOverlay";

export const SCENE_DURATIONS = {
  scene1Hook: 90,          // 3s
  scene2ZipA: 180,         // 6s
  scene3ZipB: 180,         // 6s
  scene4HeadToHead: 300,   // 10s
  scene5KeyDifference: 180,// 6s
  scene6Takeaway: 180,     // 6s
  scene7Cta: 240,          // 8s
} as const;

export const SCENE_COUNT = 7;
export const TOTAL_DURATION = Object.values(SCENE_DURATIONS).reduce((a, b) => a + b, 0);

const sceneComponents = [
  Scene01Hook,
  Scene02ZipA,
  Scene03ZipB,
  Scene04HeadToHead,
  Scene05KeyDifference,
  Scene06InvestorTakeaway,
  Scene07Cta,
] as const;

const sceneKeys = [
  "scene1Hook",
  "scene2ZipA",
  "scene3ZipB",
  "scene4HeadToHead",
  "scene5KeyDifference",
  "scene6Takeaway",
  "scene7Cta",
] as const;

export type ShortsNarration = {
  text: string;
  audioFile?: string;
};

export type YouTubeShortsBaseProps = {
  comparison: ShortsComparison;
  narration?: ShortsNarration[];
  audioMode: "tts" | "silent";
};

/**
 * Builds caption word arrays for each scene using TTS timestamps if provided,
 * otherwise falling back to even timing derived from the narration text.
 */
const buildSceneCaptions = (
  sceneStartFrame: number,
  sceneDuration: number,
  narration?: ShortsNarration
): CaptionWord[] => {
  if (!narration || !narration.text) return [];
  return textToEvenCaptions(
    narration.text,
    sceneStartFrame,
    2.8,
    30
  ).map((w) => ({
    ...w,
    endFrame: Math.min(w.endFrame, sceneStartFrame + sceneDuration - 2),
  }));
};

export const YouTubeShortsBase = ({
  comparison,
  narration,
  audioMode,
}: YouTubeShortsBaseProps) => {
  const { fps } = useVideoConfig();

  const sceneStartFrames: number[] = [];
  let cum = 0;
  sceneKeys.forEach((key) => {
    sceneStartFrames.push(cum);
    cum += SCENE_DURATIONS[key];
  });

  // Flatten all captions across scenes into one timeline for the overlay
  const allCaptions: CaptionWord[] = [];
  sceneKeys.forEach((key, idx) => {
    const caps = buildSceneCaptions(
      sceneStartFrames[idx],
      SCENE_DURATIONS[key],
      narration?.[idx]
    );
    allCaptions.push(...caps);
  });

  return (
    <AbsoluteFill>
      {/* Background music bed (ducked) */}
      {audioMode === "tts" && (
        <Audio
          src={staticFile("audio/music/shorts-bed.mp3")}
          volume={0.12}
          loop
        />
      )}

      {/* Scene sequence */}
      {sceneComponents.map((SceneComponent, index) => {
        const key = sceneKeys[index];
        const start = sceneStartFrames[index];
        const duration = SCENE_DURATIONS[key];
        return (
          <Sequence
            key={index}
            from={start}
            durationInFrames={duration}
            name={`Scene ${index + 1}`}
          >
            <SceneComponent comparison={comparison} />
            {/* TTS narration per scene */}
            {audioMode === "tts" && narration?.[index]?.audioFile && (
              <Audio src={staticFile(`audio/shorts/${narration[index].audioFile}`)} />
            )}
          </Sequence>
        );
      })}

      {/* Captions overlay spanning the whole timeline */}
      <CaptionsOverlay
        captions={allCaptions}
        totalDurationInFrames={TOTAL_DURATION}
        fps={fps}
      />
    </AbsoluteFill>
  );
};
