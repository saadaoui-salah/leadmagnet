import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import type { ZipForComparison } from "../data/types";
import { theme } from "../../theme/theme";
import { formatCurrency, formatPercent } from "../../utils/format";

type ZipCardProps = {
  zip: ZipForComparison;
  label: string;
  detail: string;
  side: "left" | "right";
  accentColor?: string;
};

export const ZipCard = ({
  zip,
  label,
  detail,
  side,
  accentColor,
}: ZipCardProps) => {
  const frame = useCurrentFrame();
  const color = accentColor ?? theme.colors.primary;

  const slideX = interpolate(
    frame,
    [0, 25],
    [side === "left" ? -400 : 400, 0],
    {
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }
  );

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const scoreScale = interpolate(frame, [20, 40], [0.5, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <div
      style={{
        opacity,
        translate: `${slideX}px 0px`,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: 20,
        background: "linear-gradient(145deg, rgba(21,27,36,0.86), rgba(21,27,36,0.46))",
        boxShadow: theme.shadow,
        backdropFilter: "blur(18px)",
        padding: "40px 36px",
        display: "flex",
        flexDirection: "column",
        gap: 24,
        width: "100%",
      }}
    >
      {/* Header row: ZIP + score badge */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
        }}
      >
        <div>
          <div
            style={{
              fontSize: 26,
              fontWeight: 800,
              color: theme.colors.muted,
              marginBottom: 8,
            }}
          >
            {label}
          </div>
          <div
            style={{
              fontSize: 64,
              fontWeight: 900,
              lineHeight: 1,
              letterSpacing: -2,
            }}
          >
            {zip.zipCode}
          </div>
          <div
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: theme.colors.muted,
              marginTop: 6,
            }}
          >
            {zip.city}{zip.state ? `, ${zip.state}` : ""}
          </div>
        </div>
        <div
          style={{
            scale: scoreScale,
            background: `${color}18`,
            border: `2px solid ${color}55`,
            borderRadius: 16,
            padding: "12px 18px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              color,
              lineHeight: 1,
            }}
          >
            {Math.round(zip.score)}
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: theme.colors.muted,
            }}
          >
            SCORE
          </div>
        </div>
      </div>

      {/* Metrics grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 18,
        }}
      >
        <MetricBlock label="Median Rent" value={formatCurrency(zip.medianRent)} />
        <MetricBlock label="Rent Growth" value={formatPercent(zip.rentGrowth)} accent={zip.rentGrowth >= 0} />
        <MetricBlock label="Yield" value={`${zip.yieldPct}%`} />
        <MetricBlock label="Demand" value={`${zip.demandScore}/100`} />
      </div>

      {/* Detail text */}
      <div
        style={{
          fontSize: 22,
          color: theme.colors.muted,
          fontWeight: 600,
          lineHeight: 1.4,
        }}
      >
        {detail}
      </div>
    </div>
  );
};

const MetricBlock = ({
  label,
  value,
  accent = true,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) => (
  <div>
    <div
      style={{
        fontSize: 18,
        fontWeight: 700,
        color: theme.colors.muted,
        marginBottom: 4,
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontSize: 32,
        fontWeight: 900,
        fontFamily: "Fira Code, monospace",
        color: accent ? theme.colors.text : theme.colors.warning,
      }}
    >
      {value}
    </div>
  </div>
);
