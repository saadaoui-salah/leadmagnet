import React from "react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { SectionTitle } from "../components/SectionTitle";
import { TrendChart } from "../components/TrendChart";
import { InsightPanel } from "../components/InsightPanel";
import { Flame } from "lucide-react";
import { theme } from "../theme/theme";
import { formatCurrency } from "../utils/format";

export const Slide04RentTrend = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  return (
    <Slide index={4} nextHint="Rent is moving. Price is the confirmation signal.">
      <SectionTitle title="Rent Trend Is Breaking Higher" kicker="Demand pressure" />
      <div style={{ display: "grid", gridTemplateColumns: "1.35fr 0.75fr", gap: 22, marginTop: 40 }}>
        <TrendChart data={market.trends} dataKey="rent" title="Median Rent" color={theme.colors.primary} formatter={formatCurrency} delay={8} />
        <InsightPanel icon={Flame} title="Why it matters" body={insights.rentTrendInsight} delay={16} />
      </div>
    </Slide>
  );
};
