import React from "react";
import { CalendarClock, DollarSign, Home, PanelsTopLeft } from "lucide-react";
import type { ZillowMarketData } from "../data/types";
import { buildInsights } from "../data/insights";
import { Slide } from "../components/Slide";
import { KpiCard } from "../components/KpiCard";
import { SectionTitle } from "../components/SectionTitle";
import { formatCurrency, formatNumber } from "../utils/format";

export const Slide03Snapshot = ({ market }: { market: ZillowMarketData }) => {
  const insights = buildInsights(market);
  return (
    <Slide index={3} nextHint="Now watch which curve is accelerating.">
      <SectionTitle title={insights.snapshotTitle} kicker={`${market.city}, ${market.state}`} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22, marginTop: 44 }}>
        <KpiCard label="Active Listings" value={formatNumber(market.activeListings)} detail="live market supply" icon={PanelsTopLeft} delay={8} />
        <KpiCard label="Median Rent" value={formatCurrency(market.medianRent)} detail="asking rent benchmark" icon={DollarSign} accent="secondary" delay={13} />
        <KpiCard label="Median Home Price" value={formatCurrency(market.medianHomePrice, true)} detail="ownership pricing" icon={Home} delay={18} />
        <KpiCard label="Days On Market" value={`${market.avgDaysOnMarket}`} detail="speed of absorption" icon={CalendarClock} accent="warning" delay={23} />
      </div>
    </Slide>
  );
};
