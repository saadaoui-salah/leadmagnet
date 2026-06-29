import React from "react";
import { AbsoluteFill } from "remotion";
import { theme } from "../../theme/theme";

export const InstagramSlide = ({
  children,
  index,
  label
}: {
  children: React.ReactNode;
  index: number;
  label: string;
}) => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(circle at 10% 5%, rgba(43,238,52,0.16), transparent 30%), radial-gradient(circle at 92% 8%, rgba(0,212,255,0.14), transparent 28%), linear-gradient(180deg, #0B0F14 0%, #10161D 100%)",
      color: theme.colors.text,
      fontFamily: "Inter, system-ui, sans-serif",
      padding: 54,
      overflow: "hidden"
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: 24,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: 22,
        background: "linear-gradient(135deg, rgba(255,255,255,0.055), rgba(255,255,255,0.01))"
      }}
    />
    <div style={{ position: "relative", zIndex: 1, height: "100%", display: "flex", flexDirection: "column" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontSize: 21, fontWeight: 900, color: theme.colors.muted, textTransform: "uppercase" }}>{label}</div>
        <div style={{ fontFamily: "Fira Code, monospace", color: theme.colors.secondary, fontSize: 22, fontWeight: 700 }}>
          {index}/10
        </div>
      </header>
      <main style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>{children}</main>
      <footer style={{ display: "flex", justifyContent: "space-between", color: theme.colors.muted, fontSize: 20, fontWeight: 800 }}>
        <span>Zillow Intelligence</span>
        <span style={{ color: theme.colors.primary }}>Save + Share</span>
      </footer>
    </div>
  </AbsoluteFill>
);
