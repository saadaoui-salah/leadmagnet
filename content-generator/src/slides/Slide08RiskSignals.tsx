import React from "react";
import { AlertTriangle, Gauge, WalletCards } from "lucide-react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { SectionTitle } from "../components/SectionTitle";
import { InsightPanel } from "../components/InsightPanel";
import { theme } from "../theme/theme";

export const Slide08RiskSignals = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  return (
    <Slide index={8} nextHint="The next move depends on three watchpoints.">
      <SectionTitle title="Risk Signals" kicker="Balanced analysis" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 18, marginTop: 46 }}>
        <InsightPanel icon={WalletCards} title="Affordability ceiling" body={insights.risk} accent={theme.colors.warning} delay={8} />
        <InsightPanel icon={Gauge} title="Inventory rebound risk" body={insights.inventoryRisk} accent={theme.colors.danger} delay={16} />
        <InsightPanel icon={AlertTriangle} title="Execution risk" body={insights.executionRisk} accent={theme.colors.warning} delay={24} />
      </div>
    </Slide>
  );
};
