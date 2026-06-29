import React from "react";
import { MessageCircle, Plus } from "lucide-react";
import { theme } from "../theme/theme";
import { useEntrance } from "./animations";

export const CtaBlock = () => {
  const entrance = useEntrance(18);
  return (
    <div style={{ ...entrance, display: "flex", gap: 18, marginTop: 44 }}>
      <div
        style={{
          width: 230,
          height: 78,
          borderRadius: 8,
          background: theme.colors.primary,
          color: "#061008",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 12,
          fontSize: 30,
          fontWeight: 900
        }}
      >
        <Plus size={33} />
        Follow
      </div>
      <div
        style={{
          height: 78,
          borderRadius: 8,
          border: `1px solid ${theme.colors.border}`,
          display: "flex",
          alignItems: "center",
          padding: "0 28px",
          gap: 12,
          fontSize: 27,
          fontWeight: 800,
          color: theme.colors.text
        }}
      >
        <MessageCircle size={30} color={theme.colors.secondary} />
        DM "REPORT"
      </div>
    </div>
  );
};
