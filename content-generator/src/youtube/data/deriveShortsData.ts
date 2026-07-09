import type {
  ZillowMarketData,
  ZipPerformance,
  WinnerInfo,
} from "../../data/types";
import type {
  ShortsComparison,
  ZipForComparison,
  ComparisonMetric,
} from "./types";
import { buildShortsCopy } from "../shortsCopy";

type RentDrop = NonNullable<ZillowMarketData["rentDrops"]>[number];

function zipPerformanceToComparison(
  z: ZipPerformance,
  score: number
): ZipForComparison {
  const medianHome = z.medianHomePrice || z.medianRent * 280;
  const annualRent = z.medianRent * 12;
  const yieldPct =
    medianHome > 0 ? (annualRent / medianHome) * 100 : 0;

  return {
    zipCode: z.zipCode,
    city: z.neighborhood,
    state: "",
    score,
    medianRent: z.medianRent,
    rentGrowth: z.rentGrowth30d,
    medianHomePrice: medianHome,
    demandScore: z.demandScore,
    yieldPct: Math.round(yieldPct * 10) / 10,
    activeListings: z.activeListings,
    daysOnMarket: 18,
    inventoryChangePct: 0,
  };
}

function winnerInfoToComparison(w: WinnerInfo): ZipForComparison {
  const m = w.metrics;
  const medianHome = m.median_home_value || m.avg_rent * 280;
  const yieldPct =
    medianHome > 0
      ? Math.round(((m.avg_rent * 12) / medianHome) * 1000) / 10
      : 0;

  return {
    zipCode: w.zipcode,
    city: w.city,
    state: w.state,
    score: w.score,
    medianRent: m.avg_rent,
    rentGrowth: m.rent_growth,
    medianHomePrice: medianHome,
    demandScore: Math.round(
      Math.min(Math.max(w.breakdown.demand * 5, 0), 100)
    ),
    yieldPct,
    activeListings: m.active_listings,
    daysOnMarket: 18,
    inventoryChangePct: m.inventory_change,
  };
}

function rentDropToComparison(r: RentDrop): ZipForComparison {
  const medianHome = r.avg_rent * 280;
  return {
    zipCode: r.zip,
    city: r.city,
    state: r.state,
    score: 0,
    medianRent: r.avg_rent,
    rentGrowth: r.rent_growth,
    medianHomePrice: medianHome,
    demandScore: 20,
    yieldPct: Math.round(((r.avg_rent * 12) / medianHome) * 1000) / 10,
    activeListings: 0,
    daysOnMarket: 30,
    inventoryChangePct: 0,
  };
}

function buildMetrics(a: ZipForComparison, b: ZipForComparison): ComparisonMetric[] {
  return [
    {
      label: "Median Rent",
      zipA: a.medianRent,
      zipB: b.medianRent,
      unit: "$",
      format: "currency",
      higherIsBetter: false,
    },
    {
      label: "Rent Growth (30d)",
      zipA: a.rentGrowth,
      zipB: b.rentGrowth,
      unit: "%",
      format: "percent",
      higherIsBetter: true,
    },
    {
      label: "Rental Yield",
      zipA: a.yieldPct,
      zipB: b.yieldPct,
      unit: "%",
      format: "percent",
      higherIsBetter: true,
    },
    {
      label: "Demand Score",
      zipA: a.demandScore,
      zipB: b.demandScore,
      unit: "/100",
      format: "number",
      higherIsBetter: true,
    },
    {
      label: "Days on Market",
      zipA: a.daysOnMarket,
      zipB: b.daysOnMarket,
      unit: " days",
      format: "number",
      higherIsBetter: false,
    },
  ];
}

export function deriveShortsWinnerVsRunnerUp(
  market: ZillowMarketData
): ShortsComparison | null {
  const winnerRaw = market.winnerInfo;
  const rentDrops = market.rentDrops ?? [];

  let zipA: ZipForComparison;
  if (winnerRaw && winnerRaw.zipcode) {
    zipA = winnerInfoToComparison(winnerRaw);
  } else {
    const top = market.topZipCodes[0];
    if (!top) return null;
    zipA = zipPerformanceToComparison(top, 80);
  }

  const runnerUp = market.topZipCodes[1];
  if (!runnerUp) return null;

  const zipB = zipPerformanceToComparison(
    runnerUp,
    runnerUp.demandScore
  );

  const metrics = buildMetrics(zipA, zipB);
  const copy = buildShortsCopy(market, zipA, zipB, "winner-vs-runner-up", rentDrops);

  return {
    mode: "winner-vs-runner-up",
    zipA,
    zipB,
    metrics,
    copy,
    generatedAt: market.generatedAt,
  };
}

export function deriveShortsWinnerVsLoser(
  market: ZillowMarketData
): ShortsComparison | null {
  const winnerRaw = market.winnerInfo;
  const rentDrops = market.rentDrops ?? [];

  let zipA: ZipForComparison;
  if (winnerRaw && winnerRaw.zipcode) {
    zipA = winnerInfoToComparison(winnerRaw);
  } else {
    const top = market.topZipCodes[0];
    if (!top) return null;
    zipA = zipPerformanceToComparison(top, 80);
  }

  const loser = rentDrops[0];
  if (!loser) return null;

  const zipB = rentDropToComparison(loser);

  const metrics = buildMetrics(zipA, zipB);
  const copy = buildShortsCopy(market, zipA, zipB, "winner-vs-loser", rentDrops);

  return {
    mode: "winner-vs-loser",
    zipA,
    zipB,
    metrics,
    copy,
    generatedAt: market.generatedAt,
  };
}
