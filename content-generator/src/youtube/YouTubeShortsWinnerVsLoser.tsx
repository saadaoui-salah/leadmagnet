import React from "react";
import type { ZillowMarketData } from "../data/types";
import { deriveShortsWinnerVsLoser } from "./data/deriveShortsData";
import { getGeneratedMarketSync } from "../data/loadGenerated";
import {
  YouTubeShortsBase,
  TOTAL_DURATION,
  type ShortsNarration,
} from "./YouTubeShortsBase";

export type YouTubeShortsProps = {
  market?: ZillowMarketData;
  narration?: ShortsNarration[];
  audioMode?: "tts" | "silent";
};

export const YouTubeShortsWinnerVsLoser = ({
  market,
  narration,
  audioMode = "silent",
}: YouTubeShortsProps) => {
  const data = market ?? getGeneratedMarketSync();
  if (!data) {
    throw new Error(
      "No generated data found. Run: python scripts/generate_market_copy.py"
    );
  }

  const comparison = deriveShortsWinnerVsLoser(data);
  if (!comparison) {
    throw new Error(
      "Not enough data for WinnerVsLoser short. Need winnerInfo + at least 1 rentDrop."
    );
  }

  return (
    <YouTubeShortsBase
      comparison={comparison}
      narration={narration}
      audioMode={audioMode}
    />
  );
};

export const WINNER_VS_LOSER_DURATION = TOTAL_DURATION;
