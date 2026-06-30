import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { theme } from "../../theme/theme";

export const Scene06InvestorTakeaway = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy } = comparison;

  const opacity = interpolate(frame, [5, 25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const yShift = interpolate(frame, [5, 25], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <ShortSlide sceneLabel="06 / 07  -  TAKEAWAY">
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 36,
        }}
      >
        <div
          style={{
            opacity,
            fontSize: 30,
            fontWeight: 800,
            color: theme.colors.primary,
            textTransform: "uppercase",
            letterSpacing: 2,
          }}
        >
          Investor takeaway
        </div>

        <div
          style={{
            opacity,
            translate: `0px ${yShift}px`,
            border: `1px solid ${theme.colors.primary}33`,
            borderRadius: 20,
            background: `linear-gradient(145deg, ${theme.colors.primary}0d, ${theme.colors.primary}05)`,
            padding: "44px 40px",
            fontSize: 52,
            fontWeight: 800,
            lineHeight: 1.25,
            letterSpacing: -1,
          }}
        >
          {copy.investorTakeaway}
        </div>
      </div>
    </ShortSlide>
  );
};
