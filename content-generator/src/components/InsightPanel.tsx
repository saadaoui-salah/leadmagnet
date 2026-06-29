import React from "react";
import type { LucideIcon } from "lucide-react";
import { theme } from "../theme/theme";
import { useEntrance } from "./animations";
import { GlassCard } from "./GlassCard";

export const InsightPanel = ({
  icon: Icon,
  title,
  body,
  accent = theme.colors.primary,
  delay = 0
}: {
  icon: LucideIcon;
  title: string;
  body: string;
  accent?: string;
  delay?: number;
}) => {
  const entrance = useEntrance(delay);
  return (
    <GlassCard style={{ padding: 30, ...entrance }}>
      <Icon size={38} color={accent} />
      <div style={{ fontSize: 32, fontWeight: 850, marginTop: 22 }}>{title}</div>
      <div style={{ color: theme.colors.muted, fontSize: 25, lineHeight: 1.35, marginTop: 14 }}>{body}</div>
    </GlassCard>
  );
};
