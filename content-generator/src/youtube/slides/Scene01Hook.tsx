import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { ShortNumber } from "../components/ShortNumber";
import { theme } from "../../theme/theme";

export const Scene01Hook = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy, zipA } = comparison;

  const headlineOpacity = interpolate(frame, [10, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subOpacity = interpolate(frame, [40, 55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const questionY = interpolate(frame, [40, 60], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <ShortSlide sceneLabel="01 / 07  -  HOOK">
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "flex-start",
          gap: 40,
        }}
      >
        <div
          style={{
            fontSize: 28,
            fontWeight: 800,
            color: theme.colors.secondary,
            textTransform: "uppercase",
            letterSpacing: 2,
            opacity: headlineOpacity,
          }}
        >
          {comparison.mode === "winner-vs-runner-up"
            ? "Two ZIPs. One winner."
            : "One soaring. One crashing."}
        </div>

        <div style={{ opacity: headlineOpacity }}>
          <ShortNumber
            value={zipA.score}
            format="number"
            fontSize={220}
            color={theme.colors.primary}
            durationInFrames={35}
          />
        </div>

        <h1
          style={{
            fontSize: 76,
            fontWeight: 900,
            lineHeight: 1.0,
            margin: 0,
            opacity: headlineOpacity,
            letterSpacing: -2,
          }}
        >
          {copy.hookHeadline}
        </h1>

        <p
          style={{
            fontSize: 38,
            fontWeight: 600,
            color: theme.colors.muted,
            margin: 0,
            lineHeight: 1.3,
            opacity: subOpacity,
            translate: `0px ${questionY}px`,
            maxWidth: 880,
          }}
        >
          {copy.hookSub}
        </p>
      </div>
    </ShortSlide>
  );
};
