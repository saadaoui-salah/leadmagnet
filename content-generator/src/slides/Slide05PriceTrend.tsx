import React from "react";
import { Landmark } from "lucide-react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { SectionTitle } from "../components/SectionTitle";
import { TrendChart } from "../components/TrendChart";
import { InsightPanel } from "../components/InsightPanel";
import { theme } from "../theme/theme";
import { formatCurrency } from "../utils/format";

export const Slide05PriceTrend = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  return (
    <Slide index={5} nextHint="The ZIP-level ranking shows where the move is concentrated.">
      <SectionTitle title="Home Values Are Confirming The Signal" kicker="Capital movement" />
      <div style={{ display: "grid", gridTemplateColumns: "1.35fr 0.75fr", gap: 22, marginTop: 40 }}>
        <TrendChart data={market.trends} dataKey="homePrice" title="Median Home Price" color={theme.colors.secondary} formatter={(v) => formatCurrency(v, true)} delay={8} />
        <InsightPanel icon={Landmark} title="Key takeaway" body={insights.priceTrendInsight} accent={theme.colors.secondary} delay={16} />
      </div>
    </Slide>
  );
};
