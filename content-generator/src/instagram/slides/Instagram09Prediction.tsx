import React from "react";
import { Eye } from "lucide-react";
import type { ZillowMarketData } from "../../data/types";
import { theme } from "../../theme/theme";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram09Prediction = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={9} label="Prediction">
      <Eye size={82} color={theme.colors.secondary} />
      <h1 style={{ fontSize: 88, lineHeight: 0.95, margin: "42px 0 0", fontWeight: 950 }}>What happens next?</h1>
      <div style={{ color: theme.colors.primary, fontSize: 42, lineHeight: 1.12, fontWeight: 900, marginTop: 34 }}>{copy.prediction}</div>
    </InstagramSlide>
  );
};
