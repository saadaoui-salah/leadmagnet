import type { ZillowMarketData } from "./types";
import { formatCurrency, formatPercent } from "../utils/format";

export const buildInsights = (market: ZillowMarketData) => {
  const top = market.topZipCodes[0] ?? { zipCode: market.zipCode, neighborhood: market.city, rentGrowth30d: 0, demandScore: 0, medianRent: 0, medianHomePrice: 0, homeGrowth30d: 0, activeListings: 0 };
  const trends = market.trends;
  const inventoryChange = trends.length >= 2 && trends[0].inventory > 0
    ? ((trends[trends.length - 1].inventory - trends[0].inventory) / trends[0].inventory) * 100
    : 0;

  const gen = market.generatedCopy;

  const inventoryDirection = inventoryChange > 0 ? "rising" : "falling";
  const inventoryAbs = Math.abs(inventoryChange).toFixed(1);
  const dom = market.avgDaysOnMarket;

  return {
    hook: gen?.hook || `${market.city} Rents Just Jumped ${formatPercent(market.rentGrowth30d)}`,
    hookSub: gen?.hookSub || `${market.activeListings.toLocaleString()} active listings \u2022 ZIP ${market.zipCode} \u2022 ${market.generatedAt}`,
    curiosity: gen?.curiosity || `${top.zipCode} is moving faster than the citywide signal, but the real story is pricing power versus shrinking supply.`,
    snapshotTitle: gen?.snapshotTitle || "Market Snapshot",
    opportunity: gen?.investorInsight1 || `Rental demand is growing faster than inventory. ${top.neighborhood} leads with ${formatPercent(
      top.rentGrowth30d
    )} rent growth and a ${top.demandScore}/100 demand score.`,
    investorInsight1: gen?.investorInsight1 || `Rental demand is growing faster than inventory. ${top.neighborhood} leads with ${formatPercent(
      top.rentGrowth30d
    )} rent growth and a ${top.demandScore}/100 demand score.`,
    investorInsight2: gen?.investorInsight2 || `The strongest ZIPs are pulling away from the average. That is where sourcing, renovation, and leasing speed become alpha.`,
    investorInsight3: gen?.investorInsight3 || `Prioritize submarkets where rent growth, low days on market, and inventory compression appear together.`,
    rentTrendInsight: gen?.rentTrendInsight || `Rent acceleration often shows up before sale prices. For investors, it can signal stronger cash-flow underwriting before comps fully reset.`,
    priceTrendInsight: gen?.priceTrendInsight || `Home price growth is lagging rent growth, suggesting rental demand is the leading indicator in this market.`,
    risk: gen?.riskSignal || `Affordability pressure is rising: median rent is ${formatCurrency(
      market.medianRent
    )}, while inventory is ${inventoryAbs}% lower than January.`,
    inventoryRisk: gen?.inventoryRisk || `If new listings rise faster than lease velocity, rent growth can cool. Inventory is currently ${inventoryDirection} at ${inventoryAbs}% over the period.`,
    executionRisk: gen?.executionRisk || `Fast markets punish slow underwriting. At ${dom} days on market, the best ZIPs may already price in part of the demand shock.`,
    watch: gen?.watchNext || `Watch days on market first. If it stays near ${dom} days while rents hold above ${formatCurrency(
      market.medianRent
    )}, landlords keep leverage.`,
    watchSupply: gen?.watchSupply || `A second month of inventory compression would make the rent trend harder to fade. Current inventory change: ${inventoryAbs}% ${inventoryDirection}.`,
    prediction: gen?.prediction || `Base case: premium ZIPs keep outperforming. Upside case: inventory tightens again and rent growth re-accelerates into late summer.`,
    ctaHeadline: gen?.ctaHeadline || "Want Daily Zillow Market Intelligence?",
    ctaSub: gen?.ctaSub || "Follow for daily ZIP-code-level market insights across rent growth, inventory pressure, pricing power, and investor risk signals.",
  };
};
