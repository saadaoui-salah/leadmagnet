import type { ZillowMarketData } from "./types";
import { fetchMarketData as fetchFromAPI } from "./fetchMarketData";

/**
 * Tries live API first, falls back to generatedMarket.json (static).
 * Run `python scripts/generate_market_copy.py <zipcode>` to refresh the static file.
 */

export const fetchMarketData = async (
  zipcode?: string
): Promise<ZillowMarketData | null> => {
  // 1. Try live API
  const liveData = await fetchFromAPI(zipcode);
  if (liveData && liveData.medianRent > 0) return liveData;

  // 2. Fallback to generated static file
  try {
    const data = require("./generatedMarket.json");
    return data as ZillowMarketData;
  } catch {
    return null;
  }
};
