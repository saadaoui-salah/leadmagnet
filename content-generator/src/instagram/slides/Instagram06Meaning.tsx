import React from "react";
import { KeyRound } from "lucide-react";
import type { ZillowMarketData } from "../../data/types";
import { theme } from "../../theme/theme";
import { InstagramSlide } from "../components/InstagramSlide";
import { instagramCopy } from "../instagramCopy";

export const Instagram06Meaning = ({ market }: { market: ZillowMarketData }) => {
  const copy = instagramCopy(market);
  return (
    <InstagramSlide index={6} label="Meaning">
      <KeyRound size={78} color={theme.colors.secondary} />
      <h1 style={{ fontSize: 90, lineHeight: 0.95, margin: "42px 0 0", fontWeight: 950 }}>{copy.plainEnglish}</h1>
      <div style={{ color: theme.colors.muted, fontSize: 34, fontWeight: 850, marginTop: 34 }}>That changes every lease conversation.</div>
    </InstagramSlide>
  );
};
