import React from "react";
import { theme } from "../theme/theme";
import { revealValue, useEntrance } from "./animations";
import { formatPercent } from "../utils/format";

export const MetricHero = ({ value, label }: { value: number; label: string }) => {
  const animated = revealValue(value, 8);
  const entrance = useEntrance(4);
  return (
    <div style={{ ...entrance }}>
      <div
        style={{
          fontSize: 210,
          lineHeight: 0.84,
          fontWeight: 900,
          color: theme.colors.primary,
          textShadow: "0 0 46px rgba(43,238,52,0.36)",
          letterSpacing: 0
        }}
      >
        {formatPercent(animated)}
      </div>
      <div style={{ color: theme.colors.muted, fontSize: 31, fontWeight: 700, marginTop: 24 }}>{label}</div>
    </div>
  );
};
