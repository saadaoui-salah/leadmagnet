/**
 * Types for the Instagram analytics API surface.
 *
 * Mirrors the backend Django analytics endpoints
 * (top-rent-growth, biggest-drops, market-pulse, daily-report).
 */

export type RentGrowthItem = {
  zip?: string;
  zipcode?: string;
  city?: string;
  state?: string;
  rent_growth?: number;
  rent_growth_pct?: number;
  avg_rent?: number;
  avgRent?: number;
  active_listings?: number;
  activeListings?: number;
  rentGrowth?: number;
};

export type MarketPulse = {
  date?: string;
  avg_rent?: number | null;
  rent_change_pct?: number | null;
  total_listings?: number | null;
  market_events?: number;
};

export type DailyReport = {
  zipcode?: string;
  city?: string;
  state?: string;
  date?: string;
  marketOverview?: {
    totalListings?: number;
    totalListingsChange?: number;
    avgRent?: number;
    avgRentChange?: number | null;
    medianHomeValue?: number;
    medianHomeValueChange?: number | null;
    newListingsWeek?: number;
    newListingsChange?: number | null;
  };
  rentTrends?: { labels: string[]; values: number[] };
  supplyDemand?: {
    labels: string[];
    newListings: number[];
    propertiesSold: number[];
    inventoryChangePct: number;
  };
  priceMovement?: { labels: string[]; values: number[] };
  topGrowingZips?: RentGrowthItem[];
  rentalBreakdown?: Array<{ type: string; avgRent: number; count: number }>;
  topProperties?: Array<{ name: string; address: string; avgRent: number; beds: number; sqft: number; daysListed: number }>;
  investorScores?: { demand: number; competition: number; yield: number; overall: number };
  marketEvents?: Array<{ type: string; title: string; description: string; severity: string }>;
};

export type InstagramAnalyticsData = {
  topRentGrowth?: RentGrowthItem[];
  biggestDrops?: RentGrowthItem[];
  marketPulse?: MarketPulse;
  dailyReport?: DailyReport;
};

export type ApiLoadState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "error"; error: string };
