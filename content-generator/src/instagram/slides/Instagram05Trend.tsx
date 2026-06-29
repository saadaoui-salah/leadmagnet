import React from "react";
import type { ZillowMarketData } from "../../data/types";
import { theme } from "../../theme/theme";
import { InstagramTrendChart } from "../components/InstagramTrendChart";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram05Trend = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={5} label="Trend">
      <h1 style={{ fontSize: 84, lineHeight: 0.95, margin: "0 0 42px", fontWeight: 950 }}>The line is not subtle.</h1>
      <InstagramTrendChart data={market.trends} />
      <div style={{ color: theme.colors.primary, fontSize: 40, fontWeight: 950, marginTop: 34 }}>{copy.trendTakeaway}</div>
    </InstagramSlide>
  );
};
