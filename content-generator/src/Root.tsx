import React from "react";
import { Composition } from "remotion";
import { ZillowCarousel, SLIDE_COUNT, SLIDE_DURATION } from "./ZillowCarousel";
import { InstagramCarousel, INSTAGRAM_SLIDE_COUNT, INSTAGRAM_SLIDE_DURATION } from "./instagram/InstagramCarousel";
import { getInstagramAnalyticsSync } from "./instagram/api/zillowAnalyticsService";
import { YouTubeShortsWinnerVsRunnerUp, WINNER_VS_RUNNER_UP_DURATION } from "./youtube/YouTubeShortsWinnerVsRunnerUp";
import { YouTubeShortsWinnerVsLoser, WINNER_VS_LOSER_DURATION } from "./youtube/YouTubeShortsWinnerVsLoser";
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
    />
    <Composition
      id="YouTubeShortsWinnerVsRunnerUp"
      component={YouTubeShortsWinnerVsRunnerUp}
      durationInFrames={WINNER_VS_RUNNER_UP_DURATION}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ audioMode: "silent" as const }}
    />
    <Composition
      id="YouTubeShortsWinnerVsLoser"
      component={YouTubeShortsWinnerVsLoser}
      durationInFrames={WINNER_VS_LOSER_DURATION}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ audioMode: "silent" as const }}
    />
  </>
);
