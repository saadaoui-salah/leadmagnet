import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { theme } from "../../theme/theme";
import { formatPercent, formatCurrency } from "../../utils/format";

type ShortNumberProps = {
  value: number;
  format?: "percent" | "currency" | "number";
  fontSize?: number;
  color?: string;
  durationInFrames?: number;
};

export const ShortNumber = ({
  value,
  format = "number",
  fontSize = 160,
  color,
  durationInFrames = 45,
}: ShortNumberProps) => {
  const frame = useCurrentFrame();

  const animated = interpolate(frame, [0, durationInFrames], [0, value], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const scaleIn = interpolate(frame, [0, 15], [0.8, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  let display: string;
  if (format === "percent") {
    display = formatPercent(animated);
  } else if (format === "currency") {
    display = formatCurrency(Math.round(animated));
  } else {
    display = Math.round(animated).toLocaleString();
  }

  return (
    <div
      style={{
        fontSize,
        lineHeight: 0.9,
        fontWeight: 900,
        color: color ?? theme.colors.primary,
        textShadow: `0 0 40px ${color ?? theme.colors.primary}55`,
        letterSpacing: -2,
        opacity,
        scale: scaleIn,
      }}
    >
      {display}
    </div>
  );
};
