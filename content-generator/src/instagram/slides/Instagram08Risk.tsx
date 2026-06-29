import React from "react";
import { AlertTriangle } from "lucide-react";
import type { ZillowMarketData } from "../../data/types";
import { theme } from "../../theme/theme";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram08Risk = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={8} label="Risk alert">
      <AlertTriangle size={82} color={theme.colors.warning} />
      <h1 style={{ fontSize: 92, lineHeight: 0.95, margin: "42px 0 0", fontWeight: 950 }}>Risk alert.</h1>
      <div style={{ color: theme.colors.muted, fontSize: 40, lineHeight: 1.12, fontWeight: 850, marginTop: 34 }}>{copy.risk}</div>
    </InstagramSlide>
  );
};
