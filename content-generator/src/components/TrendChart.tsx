import React from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { TrendPoint } from "../data/types";
import { theme } from "../theme/theme";
import { useEntrance } from "./animations";
import { GlassCard } from "./GlassCard";

type TrendChartProps = {
  data: TrendPoint[];
  dataKey: "rent" | "homePrice";
  title: string;
  color: string;
  formatter: (value: number) => string;
  delay?: number;
};

export const TrendChart = ({ data, dataKey, title, color, formatter, delay = 0 }: TrendChartProps) => {
  const entrance = useEntrance(delay);
  if (!data || data.length === 0) {
    return (
      <GlassCard style={{ padding: 28, height: 520, ...entrance }}>
        <div style={{ fontSize: 28, fontWeight: 800 }}>{title}</div>
        <div style={{ display: "grid", placeItems: "center", height: 390, color: theme.colors.muted, fontSize: 24 }}>
          No trend data available
        </div>
      </GlassCard>
    );
  }
  const last = data[data.length - 1];
  const first = data[0];
  const delta = first[dataKey] !== 0 ? (((last[dataKey] - first[dataKey]) / first[dataKey]) * 100).toFixed(1) : "0.0";

  return (
    <GlassCard style={{ padding: 28, height: 520, ...entrance }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 18 }}>
        <div style={{ fontSize: 28, fontWeight: 800 }}>{title}</div>
        <div style={{ color, fontSize: 34, fontWeight: 850 }}>+{delta}%</div>
      </div>
      <div style={{ width: "100%", height: 390 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 4 }}>
            <defs>
              <linearGradient id={`fill-${dataKey}`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.42} />
                <stop offset="100%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
            <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: theme.colors.muted, fontSize: 18 }} />
            <YAxis hide domain={["dataMin - 1000", "dataMax + 1000"]} />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={5}
              fill={`url(#fill-${dataKey})`}
              dot={false}
              activeDot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 22, color: theme.colors.muted }}>
        <span>{formatter(first[dataKey])} start</span>
        <span style={{ color: theme.colors.text }}>{formatter(last[dataKey])} current</span>
      </div>
    </GlassCard>
  );
};
