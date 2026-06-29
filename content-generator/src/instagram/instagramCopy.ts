import type { ZillowMarketData } from "../data/types";
import { formatCurrency, formatPercent } from "../utils/format";

export const instagramCopy = (market: ZillowMarketData) => {
  const top = market.topZipCodes[0] ?? { zipCode: market.zipCode, rentGrowth30d: 0 };
  const trends = market.trends;
  const inventoryDrop = trends.length >= 2 && trends[0].inventory > 0
    ? Math.abs(((trends.at(-1)!.inventory - trends[0].inventory) / trends[0].inventory) * 100)
    : 0;

  return {
    hook: `${market.city} rents just moved`,
    shock: `Most people missed ${top.zipCode}.`,
    shockDetail: `${formatPercent(top.rentGrowth30d)} in 30 days.`,
    trendTakeaway: "Renters have less leverage.",
    plainEnglish: "Renters now have less negotiating power.",
    investor: `High demand. Inventory down ${inventoryDrop.toFixed(1)}%.`,
    risk: `${formatCurrency(market.medianRent)} rent can hit an affordability wall.`,
    prediction: "If listings stay tight, rents keep climbing.",
    context: `${market.zipCode} / ${market.city}, ${market.state}`
  };
};
