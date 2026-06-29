import React from "react";
import { theme } from "../../theme/theme";
import { formatCurrency, formatNumber } from "../../utils/format";

type Point = { x: number; y: number };

const plotPadding = { top: 42, right: 20, bottom: 26, left: 20 };

const getSeries = (values: number[], width: number, height: number) => {
  if (values.length === 0) return { points: [] as Point[], min: 0, max: 0, range: 1 };

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const plotWidth = width - plotPadding.left - plotPadding.right;
  const plotHeight = height - plotPadding.top - plotPadding.bottom;

  const points = values.map((value, index) => ({
    x: plotPadding.left + (index / Math.max(1, values.length - 1)) * plotWidth,
    y: plotPadding.top + plotHeight - ((value - min) / range) * plotHeight
  }));

  return { points, min, max, range };
};

const linePath = (points: Point[]) =>
  points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");

const smoothPath = (points: Point[]) => {
  if (points.length < 2) return linePath(points);

  return points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
    const previous = points[index - 1];
    const controlX = previous.x + (point.x - previous.x) * 0.5;
    return `${path} C ${controlX.toFixed(1)} ${previous.y.toFixed(1)}, ${controlX.toFixed(1)} ${point.y.toFixed(1)}, ${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
  }, "");
};

const formatChartValue = (value: number, label: string) => {
  const normalizedLabel = label.toLowerCase();
  if (normalizedLabel.includes("rent") || normalizedLabel.includes("price")) {
    return formatCurrency(value, value >= 100000);
  }
  return formatNumber(Math.round(value));
};

export const Sparkline = ({ values, color = theme.colors.primary, height = 150 }: { values: number[]; color?: string; height?: number }) => {
  const width = 520;
  const { points } = getSeries(values, width, height);
  const path = smoothPath(points);
  const first = values[0] ?? null;
  const latest = values[values.length - 1] ?? null;

  return (
    <div style={{ height, width: "100%", display: "grid", gridTemplateRows: "38px 1fr", gap: 4 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 18 }}>
        <div style={{ color: theme.colors.muted, fontSize: 25, fontWeight: 950 }}>
          {first !== null ? formatNumber(Math.round(first)) : ""}
        </div>
        <div style={{ color, fontSize: 31, fontWeight: 950 }}>
          {latest !== null ? formatNumber(Math.round(latest)) : ""}
        </div>
      </div>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="sparkline-glow" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={1} />
          </linearGradient>
        </defs>
        <path d={path} fill="none" stroke="rgba(226,232,240,0.14)" strokeWidth={18} strokeLinecap="round" />
        <path d={path} fill="none" stroke="url(#sparkline-glow)" strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" />
        {points.length > 0 ? <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r={8} fill={color} /> : null}
      </svg>
    </div>
  );
};

export const AreaTrendChart = ({
  values,
  label,
  color = theme.colors.primary
}: {
  values: number[];
  label: string;
  color?: string;
}) => {
  const width = 820;
  const height = 320;
  const { points, min, max } = getSeries(values, width, height);
  const path = smoothPath(points);
  const lastPoint = points[points.length - 1];
  const latest = values[values.length - 1] ?? null;
  const gradientId = `premium-area-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  const areaPath = path && lastPoint ? `${path} L ${lastPoint.x.toFixed(1)} ${height - plotPadding.bottom} L ${points[0].x.toFixed(1)} ${height - plotPadding.bottom} Z` : "";

  return (
    <div
      style={{
        height: "100%",
        minHeight: 250,
        borderRadius: 24,
        border: `1px solid ${theme.colors.border}`,
        background: "linear-gradient(145deg, rgba(21,27,36,0.74), rgba(21,27,36,0.36))",
        overflow: "hidden",
        position: "relative"
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at 85% 20%, ${color}24, transparent 36%)`,
          pointerEvents: "none"
        }}
      />
      <div style={{ position: "relative", height: "100%", padding: "24px 26px", display: "grid", gridTemplateRows: "auto 1fr", gap: 6 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 20 }}>
          <div>
            <div style={{ fontSize: 24, fontWeight: 950, color: theme.colors.muted, textTransform: "uppercase" }}>{label}</div>
            {values.length > 1 ? (
              <div style={{ display: "flex", gap: 14, marginTop: 10, color: theme.colors.muted, fontSize: 20, fontWeight: 900 }}>
                <span>Low {formatChartValue(min, label)}</span>
                <span style={{ color: "rgba(226,232,240,0.32)" }}>/</span>
                <span>High {formatChartValue(max, label)}</span>
              </div>
            ) : null}
          </div>
          {latest !== null ? <div style={{ color, fontSize: 42, lineHeight: 1, fontWeight: 950 }}>{formatChartValue(latest, label)}</div> : null}
        </div>
        {values.length > 1 ? (
          <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ minHeight: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                <stop offset="55%" stopColor={color} stopOpacity={0.12} />
                <stop offset="100%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            {[0.25, 0.5, 0.75].map((ratio) => (
              <line key={ratio} x1={plotPadding.left} x2={width - plotPadding.right} y1={height * ratio} y2={height * ratio} stroke="rgba(226,232,240,0.08)" strokeWidth={2} />
            ))}
            <path d={areaPath} fill={`url(#${gradientId})`} />
            <path d={path} fill="none" stroke="rgba(226,232,240,0.14)" strokeWidth={14} strokeLinecap="round" />
            <path d={path} fill="none" stroke={color} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" />
            {lastPoint ? (
              <>
                <circle cx={lastPoint.x} cy={lastPoint.y} r={13} fill="rgba(11,15,20,0.92)" stroke={color} strokeWidth={5} />
                <line x1={lastPoint.x} x2={lastPoint.x} y1={lastPoint.y + 18} y2={height - plotPadding.bottom} stroke={color} strokeOpacity={0.3} strokeWidth={3} />
              </>
            ) : null}
          </svg>
        ) : (
          <div style={{ display: "grid", placeItems: "center", color: theme.colors.muted, fontSize: 34, fontWeight: 900 }}>Trend unavailable</div>
        )}
      </div>
    </div>
  );
};

const buildHeatmapValues = (values: Array<number | null>) => {
  if (values.length >= 21) return values.slice(0, 21);
  if (values.length === 0) return Array.from({ length: 21 }, () => null);

  return Array.from({ length: 21 }, (_, index) => {
    const source = values[index % values.length];
    if (source === null) return null;
    const fade = 1 - Math.floor(index / values.length) * 0.16;
    return source * Math.max(0.42, fade);
  });
};

export const Heatmap = ({ values }: { values: Array<number | null> }) => {
  const heatmapValues = buildHeatmapValues(values);
  const numericValues = heatmapValues.filter((value): value is number => typeof value === "number");
  const deepestDrop = numericValues.length > 0 ? Math.min(...numericValues) : null;

  return (
    <div style={{ display: "grid", gridTemplateRows: "auto auto 1fr", gap: 22, height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 16 }}>
        <div style={{ color: theme.colors.muted, fontSize: 20, fontWeight: 900 }}>{numericValues.length} markets scanned</div>
        <div style={{ color: theme.colors.warning, fontSize: 34, fontWeight: 950 }}>
          {deepestDrop !== null ? `${deepestDrop.toFixed(1)}%` : "No data"}
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 12 }}>
        <div style={{ height: 8, borderRadius: 999, background: "rgba(255,200,87,0.18)" }} />
        <div style={{ color: theme.colors.muted, fontSize: 17, fontWeight: 900 }}>lighter to deeper drops</div>
        <div style={{ height: 8, borderRadius: 999, background: `linear-gradient(90deg, rgba(255,200,87,0.25), ${theme.colors.warning})` }} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gridAutoRows: 58, gap: 10, alignContent: "start" }}>
        {heatmapValues.map((value, index) => {
          const intensity = typeof value === "number" ? Math.max(0.2, Math.min(1, Math.abs(value) / 4)) : 0.1;
          const background =
            typeof value === "number"
              ? `linear-gradient(145deg, rgba(255,200,87,${0.24 + intensity * 0.5}), rgba(255,200,87,${0.09 + intensity * 0.18}))`
              : "rgba(226,232,240,0.08)";
          return (
            <div
              key={index}
              style={{
                borderRadius: 13,
                background,
                border: `1px solid rgba(255,200,87,${0.16 + intensity * 0.28})`,
                boxShadow: typeof value === "number" ? `inset 0 1px 0 rgba(255,255,255,0.12)` : "none"
              }}
            />
          );
        })}
      </div>
    </div>
  );
};
