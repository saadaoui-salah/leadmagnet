import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { theme } from "../../theme/theme";

export const Scene05KeyDifference = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy } = comparison;

  const opacity = interpolate(frame, [5, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const pulse = interpolate(
    frame,
    [20, 40, 60, 80],
    [1, 1.04, 1, 1.04],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }
  );

  const numberOpacity = interpolate(frame, [25, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShortSlide sceneLabel="05 / 07  -  THE KEY DIFFERENCE">
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 40,
        }}
      >
        <div
          style={{
            opacity,
            fontSize: 30,
            fontWeight: 800,
            color: theme.colors.secondary,
            textTransform: "uppercase",
            letterSpacing: 2,
          }}
        >
          The edge
        </div>

        <div
          style={{
            scale: pulse,
            opacity,
            fontSize: 72,
            fontWeight: 900,
            lineHeight: 1.15,
            letterSpacing: -2,
            textShadow: `0 0 30px ${theme.colors.primary}22`,
          }}
        >
          {copy.keyDifference}
        </div>
      </div>
    </ShortSlide>
  );
};
