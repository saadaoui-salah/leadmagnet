import React from "react";
import { theme } from "../../theme/theme";

export const InstagramKpi = ({ label, value }: { label: string; value: string }) => (
  <div
    style={{
      padding: 28,
      borderRadius: 16,
      background: "rgba(21,27,36,0.78)",
      border: `1px solid ${theme.colors.border}`,
      boxShadow: "0 22px 70px rgba(0,0,0,0.34)"
    }}
  >
    <div style={{ fontSize: 22, fontWeight: 900, color: theme.colors.muted, textTransform: "uppercase" }}>{label}</div>
    <div style={{ fontSize: 54, fontWeight: 950, marginTop: 16, letterSpacing: 0 }}>{value}</div>
  </div>
);
