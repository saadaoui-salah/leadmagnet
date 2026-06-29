import React from "react";
import { InstagramCta } from "../components/InstagramCta";
import { InstagramSlide } from "../components/InstagramSlide";

export const Instagram10Cta = () => (
  <InstagramSlide index={10} label="Follow">
    <h1 style={{ fontSize: 86, lineHeight: 0.95, margin: 0, fontWeight: 950 }}>Want Daily Market Insights?</h1>
    <div style={{ fontSize: 36, lineHeight: 1.2, fontWeight: 850, marginTop: 32, color: "#94A3B8" }}>
      Follow for daily Zillow intelligence.
    </div>
    <InstagramCta />
  </InstagramSlide>
);
