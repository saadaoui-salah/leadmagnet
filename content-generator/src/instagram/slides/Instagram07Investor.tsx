import React from "react";
import { TrendingUp } from "lucide-react";
import type { ZillowMarketData } from "../../data/types";
import { theme } from "../../theme/theme";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram07Investor = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={7} label="Investor alert">
      <TrendingUp size={82} color={theme.colors.primary} />
      <h1 style={{ fontSize: 92, lineHeight: 0.95, margin: "42px 0 0", fontWeight: 950 }}>Investor alert.</h1>
      <div style={{ color: theme.colors.muted, fontSize: 42, lineHeight: 1.12, fontWeight: 850, marginTop: 34 }}>{copy.investor}</div>
    </InstagramSlide>
  );
};
