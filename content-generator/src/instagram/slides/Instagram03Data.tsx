import React from "react";
import type { ZillowMarketData } from "../../data/types";
import { formatCurrency, formatNumber } from "../../utils/format";
import { InstagramKpi } from "../components/InstagramKpi";
import { InstagramSlide } from "../components/InstagramSlide";

export const Instagram03Data = ({ market }: { market: ZillowMarketData }) => (
  <InstagramSlide index={3} label="The data">
    <h1 style={{ fontSize: 82, lineHeight: 0.95, margin: "0 0 44px", fontWeight: 950 }}>Three numbers explain it.</h1>
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <InstagramKpi label="Median rent" value={formatCurrency(market.medianRent)} />
      <InstagramKpi label="Median price" value={formatCurrency(market.medianHomePrice, true)} />
      <InstagramKpi label="Listings" value={formatNumber(market.activeListings)} />
    </div>
  </InstagramSlide>
);
