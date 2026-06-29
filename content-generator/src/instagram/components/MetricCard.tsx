import React from "react";
import type { LucideIcon } from "lucide-react";
import { theme } from "../../theme/theme";
import { formatCurrency, formatNumber, formatPercent } from "../../utils/format";
import { slideIn, useCountUp } from "./CarouselSlide";

export const formatMetric = (value: number | null | undefined, kind: "currency" | "number" | "percent" | "score") => {
  if (typeof value !== "number" || !Number.isFinite(value)) return "No data";
  if (kind === "currency") return formatCurrency(value, value >= 100000);
  if (kind === "percent") return formatPercent(value);
  if (kind === "score") return `${Math.round(value)}/100`;
  return formatNumber(Math.round(value));
};

export const KpiChip = ({ label, value, tone = "primary" }: { label: string; value: string; tone?: "primary" | "secondary" | "warning" }) => {
  const color = tone === "secondary" ? theme.colors.secondary : tone === "warning" ? theme.colors.warning : theme.colors.primary;
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        padding: "13px 16px",
        borderRadius: 999,
        background: `${color}18`,
        border: `1px solid ${color}66`,
        boxShadow: `0 0 34px ${color}22`,
        color: theme.colors.text,
        fontSize: 20,
        fontWeight: 900
      }}
    >
      <span style={{ color }}>{label}</span>
      {value}
    </div>
  );
};

export const MetricCard = ({
  label,
  value,
  kind,
  icon: Icon,
  delay = 0,
  tone = "primary"
}: {
  label: string;
  value: number | null | undefined;
  kind: "currency" | "number" | "percent" | "score";
  icon: LucideIcon;
  delay?: number;
  tone?: "primary" | "secondary" | "warning";
}) => {
  const entrance = slideIn(delay);
  const animated = useCountUp(value, delay);
  const color = tone === "secondary" ? theme.colors.secondary : tone === "warning" ? theme.colors.warning : theme.colors.primary;

  return (
    <div
      style={{
        ...entrance,
        padding: 24,
        borderRadius: 18,
        background: "linear-gradient(150deg, rgba(21,27,36,0.92), rgba(21,27,36,0.54))",
        border: `1px solid ${theme.colors.border}`,
        minHeight: 178
      }}
    >
      <Icon size={31} color={color} />
      <div style={{ color: theme.colors.muted, fontSize: 19, fontWeight: 900, marginTop: 18, textTransform: "uppercase" }}>
        {label}
      </div>
      <div style={{ fontSize: 44, fontWeight: 950, marginTop: 8 }}>{formatMetric(animated, kind)}</div>
    </div>
  );
};
