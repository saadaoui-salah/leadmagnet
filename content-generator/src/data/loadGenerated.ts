import type { ZillowMarketData } from "./types";

/**
 * Load generated market data from JSON file.
 * Always reads fresh so Remotion picks up regenerations.
 */

export const loadGeneratedMarket = async (): Promise<ZillowMarketData | null> => {
  try {
    const data = await import("./generatedMarket.json");
    return (data.default ?? data) as ZillowMarketData;
  } catch {
    return null;
  }
};

export const getGeneratedMarketSync = (): ZillowMarketData | null => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const data = require("./generatedMarket.json") as ZillowMarketData;
    return data;
  } catch {
    return null;
  }
};
