import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import type { ApiLoadState, InstagramAnalyticsData } from "./api/types";
import {
  ErrorStateSlide,
  LoadingStateSlide,
  Slide10Cta,
  Slide1Curiosity,
  Slide2Gap,
  Slide3Evidence,
  Slide4Winners,
  Slide5Losers,
  Slide6Why,
  Slide7Meaning,
  Slide8Risk,
  Slide9Prediction
} from "./slides/PremiumInstagramSlides";

export const INSTAGRAM_SLIDE_COUNT = 10;
export const INSTAGRAM_SLIDE_DURATION = 90;

export type InstagramCarouselProps = {
  analyticsState?: ApiLoadState<InstagramAnalyticsData>;
};

const slides = [
  Slide1Curiosity,
  Slide2Gap,
  Slide3Evidence,
  Slide4Winners,
  Slide5Losers,
  Slide6Why,
  Slide7Meaning,
  Slide8Risk,
  Slide9Prediction,
  Slide10Cta
] as const;

export const InstagramCarousel = ({ analyticsState = { status: "loading" } }: InstagramCarouselProps) => {
  if (analyticsState.status === "loading") {
    return <LoadingStateSlide />;
  }

  if (analyticsState.status === "error") {
    return <ErrorStateSlide error={analyticsState.error} />;
  }

  return (
    <AbsoluteFill>
      {slides.map((SlideComponent, index) => (
        <Sequence key={index} from={index * INSTAGRAM_SLIDE_DURATION} durationInFrames={INSTAGRAM_SLIDE_DURATION}>
          <SlideComponent data={analyticsState.data} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
