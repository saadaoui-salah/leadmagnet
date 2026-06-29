import React from "react";
import { Bookmark, Send, UserPlus } from "lucide-react";
import { theme } from "../../theme/theme";

const actions = [
  { icon: Bookmark, label: "Save this post" },
  { icon: Send, label: "Share with a friend" },
  { icon: UserPlus, label: "Follow for tomorrow" }
];

export const InstagramCta = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 42 }}>
    {actions.map(({ icon: Icon, label }) => (
      <div
        key={label}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "24px 28px",
          borderRadius: 16,
          background: "rgba(21,27,36,0.82)",
          border: `1px solid ${theme.colors.border}`,
          fontSize: 30,
          fontWeight: 900
        }}
      >
        <Icon size={34} color={theme.colors.primary} />
        {label}
      </div>
    ))}
  </div>
);
