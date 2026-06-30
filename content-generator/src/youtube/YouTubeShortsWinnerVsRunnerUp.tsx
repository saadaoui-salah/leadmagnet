import React from "react";
import type { ZillowMarketData } from "../data/types";
import { deriveShortsWinnerVsRunnerUp } from "./data/deriveShortsData";
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

export const YouTubeShortsWinnerVsRunnerUp = ({
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

  const comparison = deriveShortsWinnerVsRunnerUp(data);
  if (!comparison) {
    throw new Error(
      "Not enough data for WinnerVsRunnerUp short. Need winnerInfo + at least 2 topZipCodes."
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

export const WINNER_VS_RUNNER_UP_DURATION = TOTAL_DURATION;
