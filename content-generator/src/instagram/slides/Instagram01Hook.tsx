import React from "react";
import type { ZillowMarketData } from "../../data/types";
import { formatPercent } from "../../utils/format";
import { theme } from "../../theme/theme";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram01Hook = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={1} label="Stop scrolling">
      <div style={{ fontSize: 214, lineHeight: 0.82, fontWeight: 950, color: theme.colors.primary }}>{formatPercent(market.monthlyGrowth)}</div>
      <h1 style={{ fontSize: 86, lineHeight: 0.92, margin: "44px 0 0", fontWeight: 950 }}>{copy.hook}</h1>
      <div style={{ color: theme.colors.muted, fontSize: 28, fontWeight: 800, marginTop: 24 }}>{copy.context}</div>
    </InstagramSlide>
  );
};
