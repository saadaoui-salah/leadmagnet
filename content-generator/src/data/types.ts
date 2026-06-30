export type ZipPerformance = {
  zipCode: string;
  neighborhood: string;
  medianRent: number;
  rentGrowth30d: number;
  medianHomePrice: number;
  homeGrowth30d: number;
  activeListings: number;
  demandScore: number;
};

export type TrendPoint = {
  label: string;
  rent: number;
  homePrice: number;
  inventory: number;
  daysOnMarket: number;
};

export type InvestorScores = {
  demand: number;
  competition: number;
  yield: number;
  overall: number;
};

export type RentalBreakdownItem = {
  type: string;
  avgRent: number;
  count: number;
};

export type GeneratedCopy = {
  hook: string;
  hookSub: string;
  curiosity: string;
  snapshotTitle: string;
  rentTrendInsight: string;
  priceTrendInsight: string;
  investorInsight1: string;
  investorInsight2: string;
  investorInsight3: string;
  riskSignal: string;
  inventoryRisk?: string;
  executionRisk?: string;
  watchSupply?: string;
  watchNext: string;
  prediction: string;
  ctaHeadline: string;
  ctaSub: string;
};

export type ZillowMarketData = {
  city: string;
  state: string;
  zipCode: string;
  generatedAt: string;
  activeListings: number;
  medianRent: number;
  medianHomePrice: number;
  monthlyGrowth: number;
  yearlyGrowth: number;
  rentGrowth30d: number;
  homeGrowth30d: number;
  avgDaysOnMarket: number;
  newListingsChange: number;
  inventoryChangePct: number;
  investorScores: InvestorScores;
  rentalBreakdown: RentalBreakdownItem[];
  topZipCodes: ZipPerformance[];
  rentDrops?: Array<{ zip: string; city: string; state: string; rent_growth: number; avg_rent: number }>;
  trends: TrendPoint[];
  generatedCopy?: GeneratedCopy;
  winnerInfo?: WinnerInfo;
};

export type WinnerInfo = {
  zipcode: string;
  city: string;
  state: string;
  score: number;
  breakdown: { growth: number; volume: number; demand: number; yield: number };
  metrics: {
    avg_rent: number;
    rent_growth: number;
    active_listings: number;
    inventory_change: number;
    median_home_value: number;
  };
};
