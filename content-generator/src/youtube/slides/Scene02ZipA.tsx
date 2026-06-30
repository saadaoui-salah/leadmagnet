import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { ZipCard } from "../components/ZipCard";
import { theme } from "../../theme/theme";

export const Scene02ZipA = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy, zipA } = comparison;

  const labelOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShortSlide sceneLabel="02 / 07  -  CONTENDER A">
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
            ? "Contender number one"
            : "The winner"}
        </div>

        <ZipCard
          zip={zipA}
          label={copy.zipALabel}
          detail={copy.zipADetail}
          side="left"
          accentColor={theme.colors.primary}
        />
      </div>
    </ShortSlide>
  );
};
