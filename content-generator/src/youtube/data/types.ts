export type ShortsMode = "winner-vs-runner-up" | "winner-vs-loser";

export type ZipForComparison = {
  zipCode: string;
  city: string;
  state: string;
  score: number;
  medianRent: number;
  rentGrowth: number;
  medianHomePrice: number;
  demandScore: number;
  yieldPct: number;
  activeListings: number;
  daysOnMarket: number;
  inventoryChangePct: number;
};

export type ComparisonMetric = {
  label: string;
  zipA: number;
  zipB: number;
  unit: string;
  format: "currency" | "percent" | "number";
  higherIsBetter: boolean;
};

export type SceneCopy = {
  hookHeadline: string;
  hookSub: string;
  zipALabel: string;
  zipBDetail: string;
  zipBLabel: string;
  zipADetail: string;
  headToHeadIntro: string;
  keyDifference: string;
  investorTakeaway: string;
  ctaHeadline: string;
  ctaSub: string;
};

export type CaptionWord = {
  word: string;
  startFrame: number;
  endFrame: number;
};

export type SceneAudio = {
  sceneIndex: number;
  audioFile: string;
  durationInFrames: number;
  captions: CaptionWord[];
};

export type ShortsComparison = {
  mode: ShortsMode;
  zipA: ZipForComparison;
  zipB: ZipForComparison;
  metrics: ComparisonMetric[];
  copy: SceneCopy;
  generatedAt: string;
};
