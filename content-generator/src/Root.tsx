import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { ZillowCarousel, SLIDE_COUNT, SLIDE_DURATION } from "./ZillowCarousel";
import { InstagramCarousel, INSTAGRAM_SLIDE_COUNT, INSTAGRAM_SLIDE_DURATION } from "./instagram/InstagramCarousel";
import type { InstagramCarouselProps } from "./instagram/InstagramCarousel";
import { getGeneratedMarketSync } from "./data/loadGenerated";
import { getInstagramAnalyticsSync } from "./instagram/api/zillowAnalyticsService";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadFiraCode } from "@remotion/google-fonts/FiraCode";

loadInter("normal", {
  weights: ["400", "600", "800", "900"],
  subsets: ["latin"],
  ignoreTooManyRequestsWarning: true
});
loadFiraCode("normal", {
  weights: ["500", "700"],
  subsets: ["latin"],
  ignoreTooManyRequestsWarning: true
});

const calculateInstagramMetadata: CalculateMetadataFunction<InstagramCarouselProps> = async () => ({
  props: {
    analyticsState: { status: "ready", data: getInstagramAnalyticsSync() }
  }
});

export const RemotionRoot = () => (
  <>
    <Composition
      id="ZillowIntelligenceCarousel"
      component={ZillowCarousel}
      durationInFrames={SLIDE_COUNT * SLIDE_DURATION}
      fps={30}
      width={1080}
      height={1350}
    />
    <Composition
      id="InstagramZillowCarousel"
      component={InstagramCarousel}
      durationInFrames={INSTAGRAM_SLIDE_COUNT * INSTAGRAM_SLIDE_DURATION}
      fps={30}
      width={1080}
      height={1350}
      defaultProps={{ analyticsState: { status: "ready", data: getInstagramAnalyticsSync() } }}
      calculateMetadata={calculateInstagramMetadata}
    />
  </>
);
