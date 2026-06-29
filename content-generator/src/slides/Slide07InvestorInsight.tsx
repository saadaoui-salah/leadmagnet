import React from "react";
import { ChartNoAxesCombined, KeyRound, TrendingUp } from "lucide-react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { SectionTitle } from "../components/SectionTitle";
import { InsightPanel } from "../components/InsightPanel";
import { theme } from "../theme/theme";

export const Slide07InvestorInsight = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  return (
    <Slide index={7} nextHint="Opportunity without risk is just marketing. Here is the other side.">
      <SectionTitle title="Investor Insight" kicker="Opportunity translation" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 18, marginTop: 46 }}>
        <InsightPanel icon={TrendingUp} title="Pricing power is increasing" body={insights.investorInsight1} delay={8} />
        <InsightPanel icon={ChartNoAxesCombined} title="Spread matters" body={insights.investorInsight2} accent={theme.colors.secondary} delay={16} />
        <InsightPanel icon={KeyRound} title="Actionable lens" body={insights.investorInsight3} delay={24} />
      </div>
    </Slide>
  );
};
