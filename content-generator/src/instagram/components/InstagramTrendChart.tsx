import React from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import type { TrendPoint } from "../../data/types";
import { theme } from "../../theme/theme";

export const InstagramTrendChart = ({ data }: { data: TrendPoint[] }) => (
  <div
    style={{
      height: 430,
      borderRadius: 18,
      background: "rgba(21,27,36,0.78)",
      border: `1px solid ${theme.colors.border}`,
      padding: 24
    }}
  >
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 20, right: 10, bottom: 8, left: 10 }}>
        <defs>
          <linearGradient id="instagram-rent-fill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={theme.colors.primary} stopOpacity={0.48} />
            <stop offset="100%" stopColor={theme.colors.primary} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="rent"
          stroke={theme.colors.primary}
          strokeWidth={8}
          fill="url(#instagram-rent-fill)"
          dot={false}
          activeDot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  </div>
);
