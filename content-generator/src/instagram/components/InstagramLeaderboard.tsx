import React from "react";
import type { ZipPerformance } from "../../data/types";
import { theme } from "../../theme/theme";
import { formatPercent } from "../../utils/format";

const medalColors = ["#FFD166", "#D8DEE9", "#C58C5C"];

export const InstagramLeaderboard = ({ rows }: { rows: ZipPerformance[] }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
    {rows.slice(0, 3).map((row, index) => (
      <div
        key={row.zipCode}
        style={{
          display: "grid",
          gridTemplateColumns: "92px 1fr 130px",
          gap: 18,
          alignItems: "center",
          padding: 28,
          borderRadius: 18,
          background: index === 0 ? "rgba(255,209,102,0.12)" : "rgba(21,27,36,0.78)",
          border: `1px solid ${index === 0 ? "rgba(255,209,102,0.52)" : theme.colors.border}`
        }}
      >
        <div style={{ color: medalColors[index], fontSize: 52, fontWeight: 950 }}>#{index + 1}</div>
        <div>
          <div style={{ fontSize: 42, fontWeight: 950 }}>{row.zipCode}</div>
          <div style={{ color: theme.colors.muted, fontSize: 22, fontWeight: 700, marginTop: 4 }}>{row.neighborhood}</div>
        </div>
        <div style={{ color: theme.colors.primary, fontSize: 32, fontWeight: 950, textAlign: "right" }}>
          {formatPercent(row.rentGrowth30d)}
        </div>
      </div>
    ))}
  </div>
);
