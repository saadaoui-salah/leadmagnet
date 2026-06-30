import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";
import type { CaptionWord } from "../data/types";

type CaptionsOverlayProps = {
  captions: CaptionWord[];
  totalDurationInFrames: number;
  fps: number;
};

export const CaptionsOverlay = ({
  captions,
  totalDurationInFrames,
  fps,
}: CaptionsOverlayProps) => {
  const frame = useCurrentFrame();

  const allVisibleWords = captions.filter(
    (w) => frame >= w.startFrame && frame <= w.endFrame
  );

  if (allVisibleWords.length === 0) return null;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          paddingBottom: 280,
          paddingLeft: 80,
          paddingRight: 80,
          maxWidth: 960,
          textAlign: "center",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "8px 12px",
        }}
      >
        {captions.map((w, i) => {
          const wordFrame = frame - w.startFrame;
          const opacity = interpolate(wordFrame, [-3, 3], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          const isActive =
            frame >= w.startFrame && frame <= w.endFrame;

          if (opacity <= 0) return null;

          return (
            <span
              key={`${i}-${w.word}`}
              style={{
                fontSize: 48,
                fontWeight: 800,
                lineHeight: 1.3,
                color: isActive ? "#FFFFFF" : "rgba(255,255,255,0.5)",
                textShadow:
                  isActive
                    ? "0 2px 8px rgba(0,0,0,0.8), 0 0 2px rgba(0,0,0,0.5)"
                    : "0 1px 4px rgba(0,0,0,0.4)",
                opacity,
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/**
 * Utility: convert plain text to CaptionWord[] with even timing
 * Used when TTS word-level timestamps are not available (fallback)
 */
export function textToEvenCaptions(
  text: string,
  startFrame: number,
  wordsPerSecond = 2.5,
  fps = 30
): CaptionWord[] {
  const words = text.split(/\s+/).filter(Boolean);
  const framePerWord = Math.round(fps / wordsPerSecond);
  return words.map((word, i) => ({
    word,
    startFrame: startFrame + i * framePerWord,
    endFrame: startFrame + i * framePerWord + framePerWord - 2,
  }));
}
