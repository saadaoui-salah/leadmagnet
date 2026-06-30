import type { ZillowMarketData } from "../data/types";
import type { ZipForComparison, ShortsMode, SceneCopy } from "./data/types";
import { formatCurrency, formatPercent } from "../utils/format";

type RentDrop = {
  zip: string;
  city: string;
  state: string;
  rent_growth: number;
  avg_rent: number;
};

function findBiggestGap(
  a: ZipForComparison,
  b: ZipForComparison
): { label: string; delta: number; advantageA: boolean } {
  const gaps: { label: string; delta: number; advantageA: boolean }[] = [
    {
      label: "rent growth",
      delta: Math.abs(a.rentGrowth - b.rentGrowth),
      advantageA: a.rentGrowth > b.rentGrowth,
    },
    {
      label: "rental yield",
      delta: Math.abs(a.yieldPct - b.yieldPct),
      advantageA: a.yieldPct > b.yieldPct,
    },
    {
      label: "demand score",
      delta: Math.abs(a.demandScore - b.demandScore),
      advantageA: a.demandScore > b.demandScore,
    },
    {
      label: "days on market",
      delta: Math.abs(a.daysOnMarket - b.daysOnMarket),
      advantageA: a.daysOnMarket < b.daysOnMarket,
    },
  ];

  gaps.sort((x, y) => y.delta - x.delta);
  return gaps[0];
}

export function buildShortsCopy(
  market: ZillowMarketData,
  zipA: ZipForComparison,
  zipB: ZipForComparison,
  mode: ShortsMode,
  rentDrops?: RentDrop[]
): SceneCopy {
  const gen = market.generatedCopy;
  const gap = findBiggestGap(zipA, zipB);

  const isRunnerUp = mode === "winner-vs-runner-up";
  const bLabel = isRunnerUp ? "runner-up" : "biggest rent drop";
  const bDirection = isRunnerUp ? "second-hottest" : "fastest-falling";

  return {
    hookHeadline:
      gen?.hook ||
      `${zipA.city}: ${formatPercent(zipA.rentGrowth)} rent growth`,
    hookSub: isRunnerUp
      ? `Which of these two ZIPs should you invest in right now?`
      : `This ZIP is soaring while another one is crashing.`,

    zipALabel: isRunnerUp
      ? `The #1 ZIP code by investor score`
      : `The highest-scoring ZIP code`,
    zipBDetail: `${formatPercent(zipA.rentGrowth)} growth, ${formatCurrency(zipA.medianRent)} median rent, ${zipA.demandScore}/100 demand`,

    zipBLabel: isRunnerUp
      ? `The runner-up`
      : `The ${bDirection} ZIP`,
    zipADetail: `${formatPercent(zipB.rentGrowth)} growth, ${formatCurrency(zipB.medianRent)} median rent, ${zipB.demandScore}/100 demand`,

    headToHeadIntro: isRunnerUp
      ? "Both are hot. But only one is investable right now."
      : "One market is thriving. The other is collapsing.",

    keyDifference:
      gap.advantageA
        ? `${zipA.zipCode} wins on ${gap.label} by ${gap.label === "rent growth" || gap.label === "rental yield" ? formatPercent(gap.delta) : `${Math.round(gap.delta)} points`}. That is the edge.`
        : `${zipB.zipCode} actually leads on ${gap.label}, but ${zipA.zipCode} dominates everywhere else.`,

    investorTakeaway: isRunnerUp
      ? `High demand + compressed inventory = pricing power. ${zipA.city} landlords are in control.`
      : `When one ZIP drops ${formatPercent(Math.abs(zipB.rentGrowth))} while another gains ${formatPercent(zipA.rentGrowth)}, the spread is where the opportunity lives.`,

    ctaHeadline: "Comment REPORT",
    ctaSub: "to get the full ZIP code analysis with investor scores",
  };
}
