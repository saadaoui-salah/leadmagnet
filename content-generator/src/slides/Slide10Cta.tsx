import React from "react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { CtaBlock } from "../components/CtaBlock";
import { GlassCard } from "../components/GlassCard";
import { theme } from "../theme/theme";
import { useEntrance } from "../components/animations";

export const Slide10Cta = ({ market }: { market: ZillowMarketData }) => {
  const entrance = useEntrance(6);
  const insights = buildInsights(market);
  return (
    <Slide index={10} eyebrow="DAILY MARKET INTELLIGENCE">
      <div style={{ height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <h1 style={{ ...entrance, fontSize: 88, lineHeight: 0.96, margin: 0, maxWidth: 900, fontWeight: 900 }}>
          {insights.ctaHeadline}
        </h1>
        <p style={{ ...entrance, fontSize: 34, lineHeight: 1.28, color: theme.colors.muted, maxWidth: 830, marginTop: 34 }}>
          {insights.ctaSub}
        </p>
        <CtaBlock />
        <GlassCard style={{ ...entrance, marginTop: 48, padding: 28, maxWidth: 720 }}>
          <div style={{ color: theme.colors.secondary, fontSize: 24, fontWeight: 800 }}>Today's tracked market</div>
          <div style={{ fontSize: 36, fontWeight: 900, marginTop: 10 }}>
            {market.city}, {market.state} / {market.zipCode}
          </div>
        </GlassCard>
      </div>
    </Slide>
  );
};
