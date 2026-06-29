import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import type { ZillowMarketData } from "./data/types";
import { getGeneratedMarketSync } from "./data/loadGenerated";
import { Slide01Hook } from "./slides/Slide01Hook";
import { Slide02Curiosity } from "./slides/Slide02Curiosity";
import { Slide03Snapshot } from "./slides/Slide03Snapshot";
import { Slide04RentTrend } from "./slides/Slide04RentTrend";
import { Slide05PriceTrend } from "./slides/Slide05PriceTrend";
import { Slide06TopZipCodes } from "./slides/Slide06TopZipCodes";
import { Slide07InvestorInsight } from "./slides/Slide07InvestorInsight";
import { Slide08RiskSignals } from "./slides/Slide08RiskSignals";
import { Slide09WatchNext } from "./slides/Slide09WatchNext";
import { Slide10Cta } from "./slides/Slide10Cta";

export const SLIDE_COUNT = 10;
export const SLIDE_DURATION = 120;

export type ZillowCarouselProps = {
  market?: ZillowMarketData;
};

const slideComponents = [
  Slide01Hook,
  Slide02Curiosity,
  Slide03Snapshot,
  Slide04RentTrend,
  Slide05PriceTrend,
  Slide06TopZipCodes,
  Slide07InvestorInsight,
  Slide08RiskSignals,
  Slide09WatchNext,
  Slide10Cta
] as const;

export const ZillowCarousel = ({ market }: ZillowCarouselProps) => {
  const data = market ?? getGeneratedMarketSync();
  if (!data) {
    throw new Error("No generated data found. Run: python scripts/generate_market_copy.py");
  }
  return (
    <AbsoluteFill>
      {slideComponents.map((SlideComponent, index) => (
        <Sequence
          key={index}
          from={index * SLIDE_DURATION}
          durationInFrames={SLIDE_DURATION}
          style={{
            translate: "-1.5px -1.2px"
          }}
        >
          <SlideComponent market={data} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
