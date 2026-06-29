import React from "react";
import type { LucideIcon } from "lucide-react";
import { theme } from "../theme/theme";
import { useEntrance } from "./animations";
import { GlassCard } from "./GlassCard";

type KpiCardProps = {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  accent?: "primary" | "secondary" | "warning";
  delay?: number;
};

export const KpiCard = ({ label, value, detail, icon: Icon, accent = "primary", delay = 0 }: KpiCardProps) => {
  const entrance = useEntrance(delay);
  const color = accent === "secondary" ? theme.colors.secondary : accent === "warning" ? theme.colors.warning : theme.colors.primary;

  return (
    <GlassCard style={{ padding: 30, minHeight: 210, ...entrance }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ color: theme.colors.muted, fontSize: 23, fontWeight: 700, textTransform: "uppercase" }}>{label}</div>
        <Icon size={34} color={color} strokeWidth={2.2} />
      </div>
      <div style={{ fontSize: 58, fontWeight: 800, marginTop: 30, letterSpacing: 0 }}>{value}</div>
      <div style={{ color: theme.colors.muted, fontSize: 24, marginTop: 10 }}>{detail}</div>
    </GlassCard>
  );
};
