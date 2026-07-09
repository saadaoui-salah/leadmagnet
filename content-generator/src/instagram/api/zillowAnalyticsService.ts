/**
 * Analytics service for the Instagram carousel.
 *
 * Fetches ZIP-level rent growth / drops + market pulse from the
 * Django backend analytics API. Falls back to empty data when the
 * backend is unreachable so the composition still renders.
 */

import type { InstagramAnalyticsData, RentGrowthItem } from "./types";

const BACKEND_API =
  (typeof process !== "undefined" && process.env?.BACKEND_API) ||
  "http://127.0.0.1:8000";

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BACKEND_API}${path}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Async fetch for calculateMetadata / SSR.
 */
export async function getInstagramAnalytics(): Promise<InstagramAnalyticsData> {
  const [topRentGrowth, biggestDrops, marketPulse, dailyReport] =
    await Promise.all([
      fetchJson<RentGrowthItem[]>("/api/analytics/top-rent-growth/?limit=5"),
      fetchJson<RentGrowthItem[]>("/api/analytics/biggest-drops/?limit=5"),
      fetchJson<InstagramAnalyticsData["marketPulse"]>("/api/analytics/market-pulse/"),
      fetchJson<InstagramAnalyticsData["dailyReport"]>(
        "/api/analytics/daily-report/?zipcode=10001"
      ),
    ]);

  return {
    topRentGrowth: topRentGrowth ?? [],
    biggestDrops: biggestDrops ?? [],
    marketPulse: marketPulse ?? undefined,
    dailyReport: dailyReport ?? undefined,
  };
}

/**
 * Sync accessor. Returns empty data when offline; the carousel
 * renders graceful "No API data" placeholders in that case.
 *
 * Note: this cannot perform network I/O synchronously, so it only
 * serves a safe empty shell. Use getInstagramAnalytics() for real data.
 */
export function getInstagramAnalyticsSync(): InstagramAnalyticsData {
  return {
    topRentGrowth: [],
    biggestDrops: [],
    marketPulse: undefined,
    dailyReport: undefined,
  };
}
