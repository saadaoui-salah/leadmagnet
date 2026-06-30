import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ShortsComparison } from "../data/types";
import { ShortSlide } from "../components/ShortSlide";
import { theme } from "../../theme/theme";

export const Scene07Cta = ({ comparison }: { comparison: ShortsComparison }) => {
  const frame = useCurrentFrame();
  const { copy } = comparison;

  const headlineOpacity = interpolate(frame, [5, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const keywordOpacity = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const keywordScale = interpolate(
    frame,
    [20, 35, 50, 65, 80],
    [0.7, 1.05, 1, 1.05, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }
  );

  const subOpacity = interpolate(frame, [35, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const brandOpacity = interpolate(frame, [50, 65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShortSlide sceneLabel="07 / 07  -  CALL TO ACTION">
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 32,
          textAlign: "center",
        }}
      >
        <div
          style={{
            opacity: headlineOpacity,
            fontSize: 44,
            fontWeight: 800,
            color: theme.colors.muted,
            textTransform: "uppercase",
            letterSpacing: 2,
          }}
        >
          Want the full analysis?
        </div>

        {/* Keyword pill */}
        <div
          style={{
            opacity: keywordOpacity,
            scale: keywordScale,
            background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.secondary})`,
            borderRadius: 999,
            padding: "32px 64px",
            boxShadow: `0 0 60px ${theme.colors.primary}44`,
          }}
        >
          <span
            style={{
              fontSize: 96,
              fontWeight: 900,
              color: theme.colors.background,
              letterSpacing: 2,
            }}
          >
            {copy.ctaHeadline}
          </span>
        </div>

        <p
          style={{
            opacity: subOpacity,
            fontSize: 36,
            fontWeight: 700,
            color: theme.colors.text,
            margin: 0,
            maxWidth: 800,
            lineHeight: 1.3,
          }}
        >
          {copy.ctaSub}
        </p>

        {/* Brand watermark */}
        <div
          style={{
            opacity: brandOpacity,
            marginTop: 40,
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: 999,
              background: theme.colors.primary,
              boxShadow: `0 0 12px ${theme.colors.primary}`,
            }}
          />
          <span
            style={{
              fontSize: 26,
              fontWeight: 900,
              color: theme.colors.muted,
              fontFamily: "Fira Code, monospace",
              letterSpacing: 1,
            }}
          >
            REAL ESTATE INTELLIGENCE
          </span>
        </div>
      </div>
    </ShortSlide>
  );
};
