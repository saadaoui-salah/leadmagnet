import React from "react";
import { theme } from "../theme/theme";

export const GlassCard = ({
  children,
  style
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) => (
  <div
    style={{
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.radius,
      background: "linear-gradient(145deg, rgba(21,27,36,0.86), rgba(21,27,36,0.46))",
      boxShadow: theme.shadow,
      backdropFilter: "blur(18px)",
      ...style
    }}
  >
    {children}
  </div>
);
