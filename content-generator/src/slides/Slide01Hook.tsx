import React from "react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { MetricHero } from "../components/MetricHero";
import { theme } from "../theme/theme";
import { formatDate } from "../utils/format";
import { useEntrance } from "../components/animations";

export const Slide01Hook = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  const text = useEntrance(14);
  return (
    <Slide index={1} nextHint="The headline number is only the entry point.">
      <div style={{ height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <MetricHero value={market.rentGrowth30d} label="30-day median rent growth" />
        <h1 style={{ ...text, fontSize: 88, lineHeight: 0.96, maxWidth: 880, margin: "42px 0 0", fontWeight: 900 }}>{insights.hook}</h1>
        <div style={{ ...text, display: "flex", gap: 18, marginTop: 34, color: theme.colors.muted, fontSize: 28, fontWeight: 700 }}>
          <span>{insights.hookSub || `${market.zipCode} \u2022 ${market.city}, ${market.state} \u2022 ${formatDate(market.generatedAt)}`}</span>
        </div>
      </div>
    </Slide>
  );
};
