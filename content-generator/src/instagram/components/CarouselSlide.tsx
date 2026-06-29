import React from "react";
import { AbsoluteFill } from "remotion";
import { theme } from "../../theme/theme";

export const slideIn = (_delay = 0) => {
  return {
    opacity: 1,
    transform: "none"
  };
};

export const useCountUp = (value: number | null | undefined, _delay = 0) => {
  if (typeof value !== "number") return null;
  return value;
};

const GridTexture = () => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity: 0.18,
      transform: "none",
      backgroundImage:
        "linear-gradient(rgba(148,163,184,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.10) 1px, transparent 1px)",
      backgroundSize: "54px 54px"
    }}
  />
);

export const CarouselSlide = ({
  children,
  index,
  section,
  accent = "primary"
}: {
  children: React.ReactNode;
  index: number;
  section: string;
  accent?: "primary" | "secondary" | "warning";
}) => {
  const accentColor =
    accent === "secondary" ? theme.colors.secondary : accent === "warning" ? theme.colors.warning : theme.colors.primary;

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 18% 10%, rgba(43,238,52,0.15), transparent 30%), radial-gradient(circle at 84% 18%, rgba(0,212,255,0.12), transparent 28%), #0B0F14",
        color: theme.colors.text,
        fontFamily: "Inter, system-ui, sans-serif",
        overflow: "hidden",
        padding: 48
      }}
    >
      <GridTexture />
      <div
        style={{
          position: "absolute",
          inset: 24,
          borderRadius: 24,
          border: `1px solid ${theme.colors.border}`,
          background: "linear-gradient(135deg, rgba(255,255,255,0.055), rgba(255,255,255,0.008))"
        }}
      />
      <div
        style={{
          position: "relative",
          zIndex: 2,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          transform: "none"
        }}
      >
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ width: 10, height: 10, borderRadius: 999, background: accentColor, boxShadow: `0 0 22px ${accentColor}` }} />
            <span style={{ color: theme.colors.muted, fontSize: 19, fontWeight: 900, textTransform: "uppercase" }}>
              {section}
            </span>
          </div>
          <div style={{ color: accentColor, fontFamily: "Fira Code, monospace", fontSize: 22, fontWeight: 800 }}>
            {index}/10
          </div>
        </header>
        <main style={{ flex: 1 }}>{children}</main>
      </div>
    </AbsoluteFill>
  );
};
