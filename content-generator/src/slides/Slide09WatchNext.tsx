import React from "react";
import { Activity, Eye, Route } from "lucide-react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { SectionTitle } from "../components/SectionTitle";
import { InsightPanel } from "../components/InsightPanel";
import { theme } from "../theme/theme";

export const Slide09WatchNext = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  return (
    <Slide index={9} nextHint="Final slide: get the daily ZIP-code intelligence.">
      <SectionTitle title="What To Watch Next" kicker="Forward signal" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 18, marginTop: 46 }}>
        <InsightPanel icon={Eye} title="Watch absorption" body={insights.watch} delay={8} />
        <InsightPanel icon={Activity} title="Watch supply" body={insights.watchSupply} accent={theme.colors.secondary} delay={16} />
        <InsightPanel icon={Route} title="Scenario" body={insights.prediction} delay={24} />
      </div>
    </Slide>
  );
};
