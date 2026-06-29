import React from "react";
import { ArrowUpRight } from "lucide-react";
import type { ZipPerformance } from "../data/types";
import { theme } from "../theme/theme";
import { formatCurrency, formatPercent } from "../utils/format";
import { useEntrance } from "./animations";
import { GlassCard } from "./GlassCard";

export const Leaderboard = ({ rows }: { rows: ZipPerformance[] }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
    {rows.map((row, index) => {
      const entrance = useEntrance(8 + index * 5);
      return (
        <GlassCard key={row.zipCode} style={{ padding: "21px 24px", ...entrance }}>
          <div style={{ display: "grid", gridTemplateColumns: "72px 1fr 130px 170px", alignItems: "center", gap: 18 }}>
            <div style={{ color: index === 0 ? theme.colors.primary : theme.colors.muted, fontSize: 35, fontWeight: 900 }}>
              #{index + 1}
            </div>
            <div>
              <div style={{ fontSize: 33, fontWeight: 850 }}>{row.zipCode}</div>
              <div style={{ color: theme.colors.muted, fontSize: 21, marginTop: 3 }}>{row.neighborhood}</div>
            </div>
            <div style={{ color: theme.colors.secondary, fontSize: 27, fontWeight: 800 }}>{formatPercent(row.rentGrowth30d)}</div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 24, fontWeight: 800 }}>{formatCurrency(row.medianRent)}</div>
              <div style={{ color: theme.colors.primary, fontSize: 18, display: "flex", justifyContent: "flex-end", gap: 6, alignItems: "center" }}>
                Demand {row.demandScore}
                <ArrowUpRight size={18} />
              </div>
            </div>
          </div>
        </GlassCard>
      );
    })}
  </div>
);
