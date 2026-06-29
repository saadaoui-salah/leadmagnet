import React from "react";
import { theme } from "../theme/theme";
import { useEntrance } from "./animations";

export const SectionTitle = ({ title, kicker, delay = 0 }: { title: string; kicker?: string; delay?: number }) => {
  const entrance = useEntrance(delay);
  return (
    <div style={{ ...entrance }}>
      {kicker ? <div style={{ color: theme.colors.primary, fontSize: 25, fontWeight: 800, marginBottom: 16 }}>{kicker}</div> : null}
      <h1 style={{ fontSize: 76, lineHeight: 0.96, margin: 0, fontWeight: 850, letterSpacing: 0 }}>{title}</h1>
    </div>
  );
};
