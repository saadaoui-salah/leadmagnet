import React from "react";
import { ScanSearch } from "lucide-react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { GlassCard } from "../components/GlassCard";
import { SectionTitle } from "../components/SectionTitle";
import { theme } from "../theme/theme";
import { useEntrance } from "../components/animations";

export const Slide02Curiosity = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  const card = useEntrance(16);
  return (
    <Slide index={2} nextHint="Next: the four numbers that explain the move.">
      <SectionTitle title="But That's Not The Most Interesting Part" kicker="Information gap" />
      <GlassCard style={{ ...card, marginTop: 64, padding: 42 }}>
        <ScanSearch size={52} color={theme.colors.secondary} />
        <div style={{ fontSize: 42, lineHeight: 1.14, fontWeight: 850, marginTop: 28 }}>{insights.curiosity}</div>
        <div style={{ marginTop: 32, color: theme.colors.muted, fontSize: 28 }}>
          The next slide shows whether this is a spike, a structural shift, or a trap.
        </div>
      </GlassCard>
    </Slide>
  );
};
