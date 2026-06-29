import React from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { RentGrowthItem } from "../api/types";
import { theme } from "../../theme/theme";
import { formatCurrency, formatPercent } from "../../utils/format";
import { getGrowth, getZip } from "../data/deriveInstagramStory";
import { slideIn } from "./CarouselSlide";

export const RankingCard = ({ item, rank, mode }: { item: RentGrowthItem; rank: number; mode: "winner" | "loser" }) => {
  const growth = getGrowth(item);
  const entrance = slideIn(rank * 5);
  const positive = mode === "winner";
  const color = positive ? theme.colors.primary : theme.colors.warning;
  const Icon = positive ? ArrowUpRight : ArrowDownRight;

  return (
    <div
      style={{
        ...entrance,
        display: "grid",
        gridTemplateColumns: "82px 1fr 130px",
        gap: 18,
        alignItems: "center",
        padding: 24,
        borderRadius: 18,
        background: rank === 1 ? `${color}16` : "rgba(21,27,36,0.78)",
        border: `1px solid ${rank === 1 ? `${color}88` : theme.colors.border}`
      }}
    >
      <div style={{ color, fontSize: 48, fontWeight: 950 }}>#{rank}</div>
      <div>
        <div style={{ fontSize: 40, fontWeight: 950 }}>{getZip(item)}</div>
        <div style={{ color: theme.colors.muted, fontSize: 20, fontWeight: 800 }}>{item.city}, {item.state}</div>
      </div>
      <div style={{ textAlign: "right" }}>
        <Icon size={30} color={color} />
        <div style={{ color, fontSize: 30, fontWeight: 950 }}>{growth === null ? "No data" : formatPercent(growth)}</div>
        <div style={{ color: theme.colors.muted, fontSize: 17, fontWeight: 800 }}>
          {typeof item.avg_rent === "number" ? formatCurrency(item.avg_rent) : ""}
        </div>
      </div>
    </div>
  );
};
