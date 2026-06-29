import type { ZillowMarketData } from "./types";

const API_BASE =
  (typeof process !== "undefined" && process.env?.VITE_API_URL) ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://realestate-leadmagnet.onrender.com");

async function fetchJSON<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchMarketData(
  zipcode?: string
): Promise<ZillowMarketData | null> {
  const zip = zipcode ? `?zipcode=${zipcode}` : "";

  // Fetch all endpoints in parallel
  const [marketData, investorScores, rentalBreakdown, growthMetrics, trendsData, topZipsRaw] =
    await Promise.all([
      fetchJSON<Record<string, unknown>>(`/api/analytics/generate-market-data/${zip}`),
      fetchJSON<Record<string, unknown>>(`/api/analytics/investor-scores/${zip}`),
      fetchJSON<Record<string, unknown>>(`/api/analytics/rental-breakdown/${zip}`),
      fetchJSON<Record<string, unknown>>(`/api/analytics/growth-metrics/${zip}`),
      fetchJSON<Record<string, unknown>>(`/api/analytics/trends/${zip}`),
      fetchJSON<unknown[]>(`/api/analytics/top-zips/?limit=5`),
    ]);

  const topZips = Array.isArray(topZipsRaw) ? topZipsRaw : [];

  // If the main endpoint works, use it as base and enrich with focused endpoints
  if (marketData && Number(marketData.medianRent ?? 0) > 0) {
    const base = normalizeMarketData(marketData);
    // Override with focused endpoint data if available
    if (investorScores) base.investorScores = normalizeInvestorScores(investorScores);
    if (rentalBreakdown?.breakdown) base.rentalBreakdown = normalizeRentalBreakdown(rentalBreakdown.breakdown);
    if (growthMetrics) {
      base.monthlyGrowth = Number(growthMetrics.monthlyGrowth ?? base.monthlyGrowth);
      base.yearlyGrowth = Number(growthMetrics.yearlyGrowth ?? base.yearlyGrowth);
      base.rentGrowth30d = Number(growthMetrics.rentGrowth30d ?? base.rentGrowth30d);
      base.homeGrowth30d = Number(growthMetrics.homeGrowth30d ?? base.homeGrowth30d);
    }
    if (trendsData?.trends && Array.isArray(trendsData.trends)) base.trends = normalizeTrends(trendsData.trends);
    if (topZips && topZips.length > 0) base.topZipCodes = normalizeTopZips(topZips);
    return base;
  }

  // Main endpoint failed — assemble from focused endpoints
  if (!growthMetrics && !trendsData) return null;

  const z = growthMetrics ?? {};
  const t = Array.isArray(trendsData?.trends) ? trendsData.trends : [];
  const top = topZips ?? [];

  return {
    city: String(marketData?.city ?? "Unknown"),
    state: String(marketData?.state ?? ""),
    zipCode: String(marketData?.zipCode ?? marketData?.zipcode ?? zipcode ?? ""),
    generatedAt: String(marketData?.generatedAt ?? new Date().toISOString()),
    activeListings: Number(marketData?.activeListings ?? 0),
    medianRent: Number(marketData?.medianRent ?? 0),
    medianHomePrice: Number(marketData?.medianHomePrice ?? 0),
    monthlyGrowth: Number(z.monthlyGrowth ?? 0),
    yearlyGrowth: Number(z.yearlyGrowth ?? 0),
    rentGrowth30d: Number(z.rentGrowth30d ?? 0),
    homeGrowth30d: Number(z.homeGrowth30d ?? 0),
    avgDaysOnMarket: Number(marketData?.avgDaysOnMarket ?? 0),
    newListingsChange: Number(marketData?.newListingsChange ?? 0),
    inventoryChangePct: Number(marketData?.inventoryChangePct ?? 0),
    investorScores: investorScores
      ? normalizeInvestorScores(investorScores)
      : { demand: 0, competition: 0, yield: 0, overall: 0 },
    rentalBreakdown: rentalBreakdown?.breakdown
      ? normalizeRentalBreakdown(rentalBreakdown.breakdown)
      : [],
    topZipCodes: normalizeTopZips(top),
    trends: normalizeTrends(t),
  };
}

function normalizeTrends(raw: unknown[]): ZillowMarketData["trends"] {
  return raw.map((t) => {
    const p = t as Record<string, unknown>;
    return {
      label: String(p.label ?? ""),
      rent: Number(p.rent ?? 0),
      homePrice: Number(p.homePrice ?? 0),
      inventory: Number(p.inventory ?? 0),
      daysOnMarket: Number(p.daysOnMarket ?? 0),
    };
  });
}

function normalizeTopZips(raw: unknown[]): ZillowMarketData["topZipCodes"] {
  return raw.map((z) => {
    const p = z as Record<string, unknown>;
    return {
      zipCode: String(p.zipCode ?? p.zipcode ?? ""),
      neighborhood: String(p.neighborhood ?? p.city ?? ""),
      medianRent: Number(p.medianRent ?? 0),
      rentGrowth30d: Number(p.rentGrowth30d ?? 0),
      medianHomePrice: Number(p.medianHomePrice ?? 0),
      homeGrowth30d: Number(p.homeGrowth30d ?? 0),
      activeListings: Number(p.activeListings ?? 0),
      demandScore: Number(p.demandScore ?? 0),
    };
  });
}

function normalizeMarketData(raw: Record<string, unknown>): ZillowMarketData {
  return {
    city: String(raw.city ?? "Unknown"),
    state: String(raw.state ?? ""),
    zipCode: String(raw.zipCode ?? raw.zipcode ?? ""),
    generatedAt: String(raw.generatedAt ?? new Date().toISOString()),
    activeListings: Number(raw.activeListings ?? 0),
    medianRent: Number(raw.medianRent ?? 0),
    medianHomePrice: Number(raw.medianHomePrice ?? 0),
    monthlyGrowth: Number(raw.monthlyGrowth ?? 0),
    yearlyGrowth: Number(raw.yearlyGrowth ?? 0),
    rentGrowth30d: Number(raw.rentGrowth30d ?? 0),
    homeGrowth30d: Number(raw.homeGrowth30d ?? 0),
    avgDaysOnMarket: Number(raw.avgDaysOnMarket ?? 0),
    newListingsChange: Number(raw.newListingsChange ?? 0),
    inventoryChangePct: Number(raw.inventoryChangePct ?? 0),
    investorScores: normalizeInvestorScores(raw.investorScores),
    rentalBreakdown: normalizeRentalBreakdown(raw.rentalBreakdown),
    topZipCodes: normalizeTopZips(raw.topZipCodes as unknown[] ?? []),
    trends: normalizeTrends(raw.trends as unknown[] ?? []),
    generatedCopy: raw.generatedCopy as ZillowMarketData["generatedCopy"],
  };
}

function normalizeInvestorScores(raw: unknown): ZillowMarketData["investorScores"] {
  if (raw && typeof raw === "object") {
    const s = raw as Record<string, unknown>;
    return {
      demand: Number(s.demand ?? 0),
      competition: Number(s.competition ?? 0),
      yield: Number(s.yield ?? 0),
      overall: Number(s.overall ?? 0),
    };
  }
  return { demand: 0, competition: 0, yield: 0, overall: 0 };
}

function normalizeRentalBreakdown(raw: unknown): ZillowMarketData["rentalBreakdown"] {
  if (Array.isArray(raw)) {
    return raw.map((item) => {
      const p = item as Record<string, unknown>;
      return {
        type: String(p.type ?? ""),
        avgRent: Number(p.avgRent ?? 0),
        count: Number(p.count ?? 0),
      };
    });
  }
  return [];
}
