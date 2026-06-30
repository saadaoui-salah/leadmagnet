import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { ZipCard } from "../components/ZipCard";
import { theme } from "../../theme/theme";

export const Scene03ZipB = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy, zipB } = comparison;

  const labelOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShortSlide sceneLabel="03 / 07  -  CONTENDER B">
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
            opacity: labelOpacity,
            fontSize: 30,
            fontWeight: 800,
            color: theme.colors.muted,
          }}
        >
          {comparison.mode === "winner-vs-runner-up"
            ? "Contender number two"
            : "And the loser"}
        </div>

        <ZipCard
          zip={zipB}
          label={copy.zipBLabel}
          detail={copy.zipADetail}
          side="right"
          accentColor={
            comparison.mode === "winner-vs-loser"
              ? theme.colors.danger
              : theme.colors.secondary
          }
        />
      </div>
    </ShortSlide>
  );
};
