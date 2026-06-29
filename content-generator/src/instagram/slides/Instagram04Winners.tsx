import React from "react";
import type { ZillowMarketData } from "../../data/types";
import { InstagramLeaderboard } from "../components/InstagramLeaderboard";
import { InstagramSlide } from "../components/InstagramSlide";

export const Instagram04Winners = ({ market }: { market: ZillowMarketData }) => (
  <InstagramSlide index={4} label="Winners">
    <h1 style={{ fontSize: 86, lineHeight: 0.94, margin: "0 0 46px", fontWeight: 950 }}>Top ZIPs right now.</h1>
    <InstagramLeaderboard rows={market.topZipCodes} />
  </InstagramSlide>
);
