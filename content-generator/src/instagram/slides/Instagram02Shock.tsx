import React from "react";
import type { ZillowMarketData } from "../../data/types";
import { theme } from "../../theme/theme";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram02Shock = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={2} label="Shock fact">
      <h1 style={{ fontSize: 94, lineHeight: 0.95, margin: 0, fontWeight: 950 }}>Most People Miss This.</h1>
      <div style={{ fontSize: 68, lineHeight: 1, color: theme.colors.secondary, fontWeight: 950, marginTop: 58 }}>{copy.shock}</div>
      <div style={{ fontSize: 44, color: theme.colors.primary, fontWeight: 950, marginTop: 26 }}>{copy.shockDetail}</div>
      <div style={{ color: theme.colors.muted, fontSize: 28, fontWeight: 800, marginTop: 38 }}>Why is it happening?</div>
    </InstagramSlide>
  );
};
