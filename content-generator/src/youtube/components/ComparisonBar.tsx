import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ComparisonMetric } from "../data/types";
import { theme } from "../../theme/theme";
import { formatCurrency, formatPercent } from "../../utils/format";

type ComparisonBarProps = {
  metric: ComparisonMetric;
  index: number;
  maxFrames: number;
};

const formatValue = (value: number, format: ComparisonMetric["format"]): string => {
  switch (format) {
    case "currency":
      return formatCurrency(value);
    case "percent":
      return formatPercent(value);
    default:
      return Math.round(value).toLocaleString();
  }
};

export const ComparisonBar = ({ metric, index, maxFrames }: ComparisonBarProps) => {
  const frame = useCurrentFrame();
  const staggerDelay = index * 20;
  const barFrames = Math.max(maxFrames - staggerDelay, 20);

  const barOpacity = interpolate(frame, [staggerDelay, staggerDelay + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const aWidth = interpolate(
    frame,
    [staggerDelay, staggerDelay + barFrames],
    [0, 100],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }
  );

  const bWidth = interpolate(
    frame,
    [staggerDelay + 5, staggerDelay + 5 + barFrames],
    [0, 100],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }
  );

  const maxVal = Math.max(Math.abs(metric.zipA), Math.abs(metric.zipB), 1);
  const aPct = Math.max((Math.abs(metric.zipA) / maxVal) * 100, 8);
  const bPct = Math.max((Math.abs(metric.zipB) / maxVal) * 100, 8);

  const aWinner =
    (metric.higherIsBetter && metric.zipA >= metric.zipB) ||
    (!metric.higherIsBetter && metric.zipA <= metric.zipB);

  return (
    <div style={{ opacity: barOpacity }}>
      {/* Metric label */}
      <div
        style={{
          fontSize: 26,
          fontWeight: 800,
          color: theme.colors.text,
          marginBottom: 12,
        }}
      >
        {metric.label}
      </div>

      {/* ZIP A bar */}
      <BarRow
        width={`${interpolate(aWidth, [0, 100], [0, aPct])}%`}
        color={aWinner ? theme.colors.primary : theme.colors.muted}
        value={formatValue(metric.zipA, metric.format)}
        isWinner={aWinner}
        delay={staggerDelay + 15}
      />

      {/* ZIP B bar */}
      <BarRow
        width={`${interpolate(bWidth, [0, 100], [0, bPct])}%`}
        color={!aWinner ? theme.colors.secondary : theme.colors.muted}
        value={formatValue(metric.zipB, metric.format)}
        isWinner={!aWinner}
        delay={staggerDelay + 20}
        margin
      />
    </div>
  );
};

const BarRow = ({
  width,
  color,
  value,
  isWinner,
  delay,
  margin = false,
}: {
  width: string;
  color: string;
  value: string;
  isWinner: boolean;
  delay: number;
  margin?: boolean;
}) => {
  const frame = useCurrentFrame();

  const valueOpacity = interpolate(frame, [delay, delay + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        marginTop: margin ? 8 : 0,
        marginBottom: 6,
      }}
    >
      <div
        style={{
          flex: 1,
          height: 36,
          borderRadius: 8,
          background: `${color}18`,
          overflow: "hidden",
          position: "relative",
        }}
      >
        <div
          style={{
            height: "100%",
            width,
            borderRadius: 8,
            background: `linear-gradient(90deg, ${color}55, ${color}88)`,
            boxShadow: isWinner ? `0 0 20px ${color}33` : undefined,
          }}
        />
      </div>
      <div
        style={{
          fontSize: 26,
          fontWeight: 900,
          fontFamily: "Fira Code, monospace",
          color: isWinner ? color : theme.colors.text,
          opacity: valueOpacity,
          minWidth: 140,
          textAlign: "right",
        }}
      >
        {value}
      </div>
    </div>
  );
};
