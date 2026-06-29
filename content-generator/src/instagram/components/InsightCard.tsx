import React from "react";
import type { LucideIcon } from "lucide-react";
import { theme } from "../../theme/theme";
import { slideIn } from "./CarouselSlide";

export const InsightCard = ({
  icon: Icon,
  title,
  detail,
  tone = "primary",
  delay = 0
}: {
  icon: LucideIcon;
  title: string;
  detail: string;
  tone?: "primary" | "secondary" | "warning";
  delay?: number;
}) => {
  const color = tone === "secondary" ? theme.colors.secondary : tone === "warning" ? theme.colors.warning : theme.colors.primary;
  const entrance = slideIn(delay);
  return (
    <div
      style={{
        ...entrance,
        padding: 30,
        borderRadius: 22,
        background: "linear-gradient(150deg, rgba(21,27,36,0.88), rgba(21,27,36,0.5))",
        border: `1px solid ${color}55`,
        boxShadow: `0 0 48px ${color}18`
      }}
    >
      <Icon size={42} color={color} />
      <div style={{ fontSize: 39, lineHeight: 1.02, fontWeight: 950, marginTop: 24 }}>{title}</div>
      <div style={{ color: theme.colors.muted, fontSize: 26, lineHeight: 1.25, fontWeight: 800, marginTop: 18 }}>{detail}</div>
    </div>
  );
};
