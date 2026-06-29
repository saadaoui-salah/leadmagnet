import type { InstagramAnalyticsData, RentGrowthItem } from "../api/types";

const numberOrNull = (value: number | null | undefined) => (typeof value === "number" && Number.isFinite(value) ? value : null);

export const getGrowth = (item: RentGrowthItem) => numberOrNull(item.rent_growth ?? item.rent_growth_pct);
export const getZip = (item: RentGrowthItem) => item.zip ?? item.zipcode ?? "N/A";

export const latestDelta = (values: number[]) => {
  if (values.length < 2) return null;
  const first = values[0];
  const last = values[values.length - 1];
  if (!first) return null;
  return ((last - first) / first) * 100;
};

export const deriveInstagramStory = (data: InstagramAnalyticsData) => {
  const report = data.dailyReport ?? {};
  const overview = report.marketOverview ?? {};
  const topRentGrowth = data.topRentGrowth ?? [];
  const biggestDrops = data.biggestDrops ?? [];
  const top = topRentGrowth[0] ?? report.topGrowingZips?.[0];
  const drop = biggestDrops[0];
  const rentTrends = report.rentTrends ?? { labels: [], values: [] };
  const supplyDemand = report.supplyDemand ?? { labels: [], newListings: [], inventoryChangePct: 0 };
  const priceMovement = report.priceMovement ?? { labels: [], values: [] };
  const investorScores = report.investorScores ?? { demand: 0, competition: 0, yield: 0, overall: 0 };

  const rentDelta = numberOrNull(overview.avgRentChange) ?? latestDelta(rentTrends.values);
  const inventoryDelta = numberOrNull(supplyDemand.inventoryChangePct);
  const score = numberOrNull(investorScores.overall);
  const listings = numberOrNull(overview.totalListings);
  const newListings = numberOrNull(overview.newListingsWeek);
  const avgRent = numberOrNull(overview.avgRent);

  return {
    marketLabel: [report.city, report.state, report.zipcode].filter(Boolean).join(" "),
    date: report.date || data.marketPulse?.date,
    rentDelta,
    inventoryDelta,
    listings,
    newListings,
    avgRent,
    medianHomeValue: numberOrNull(overview.medianHomeValue),
    homeValueDelta: numberOrNull(overview.medianHomeValueChange),
    score,
    top,
    drop,
    demandScore: numberOrNull(investorScores.demand),
    competitionScore: numberOrNull(investorScores.competition),
    yieldScore: numberOrNull(investorScores.yield),
    rentTrend: rentTrends,
    inventoryTrend: {
      labels: supplyDemand.labels,
      values: supplyDemand.newListings
    },
    priceTrend: priceMovement,
    winners: topRentGrowth.length > 0 ? topRentGrowth : (report.topGrowingZips ?? []),
    losers: biggestDrops
  };
};
