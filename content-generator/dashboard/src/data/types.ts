export interface Slide {
  id: number;
  platform: 'linkedin' | 'instagram' | 'youtube' | 'facebook' | 'threads' | 'x';
  file: string;
  title: string;
  desc: string;
  isPdf?: boolean;
}

export interface MarketData {
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
  topZipCodes: {
    zipCode: string;
    neighborhood: string;
    medianRent: number;
    rentGrowth30d: number;
    demandScore: number;
  }[];
  generatedCopy: {
    hook: string;
    hookSub: string;
    curiosity: string;
    investorInsight1: string;
    investorInsight2: string;
    investorInsight3: string;
    riskSignal: string;
    watchNext: string;
    ctaHeadline: string;
  };
}

export type FilterTab = 'all' | 'linkedin' | 'instagram' | 'youtube' | 'facebook' | 'threads' | 'x';
