import React from "react";
import type { ZillowMarketData } from "../data/types";
import { Slide } from "../components/Slide";
import { SectionTitle } from "../components/SectionTitle";
import { Leaderboard } from "../components/Leaderboard";

export const Slide06TopZipCodes = ({ market }: { market: ZillowMarketData }) => (
  <Slide index={6} nextHint="Ranking is useful. The opportunity is in the spread.">
    <SectionTitle title="Top ZIP Codes By Momentum" kicker="Leaderboard" />
    <div style={{ marginTop: 38 }}>
      <Leaderboard rows={market.topZipCodes} />
    </div>
  </Slide>
);
