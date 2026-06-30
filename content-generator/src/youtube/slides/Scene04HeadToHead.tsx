import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { ComparisonBar } from "../components/ComparisonBar";
import { theme } from "../../theme/theme";

export const Scene04HeadToHead = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy, zipA, zipB, metrics } = comparison;

  const introOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const legendOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShortSlide sceneLabel="04 / 07  -  HEAD TO HEAD">
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 30,
        }}
      >
        <h2
          style={{
            fontSize: 48,
            fontWeight: 900,
            margin: 0,
            lineHeight: 1.1,
            opacity: introOpacity,
            letterSpacing: -1,
          }}
        >
          {copy.headToHeadIntro}
        </h2>

        {/* Legend */}
        <div
          style={{
            opacity: legendOpacity,
            display: "flex",
            gap: 32,
            fontSize: 22,
            fontWeight: 800,
          }}
        >
          <span style={{ color: theme.colors.primary }}>
            {zipA.zipCode}
          </span>
          <span style={{ color: theme.colors.muted }}>vs</span>
          <span style={{ color: theme.colors.secondary }}>
            {zipB.zipCode}
          </span>
        </div>

        {/* Bars */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 28,
            flex: 1,
          }}
        >
          {metrics.map((metric, i) => (
            <ComparisonBar
              key={metric.label}
              metric={metric}
              index={i}
              maxFrames={60}
            />
          ))}
        </div>
      </div>
    </ShortSlide>
  );
};
