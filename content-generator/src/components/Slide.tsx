import React from "react";
import { AbsoluteFill } from "remotion";
import { theme } from "../theme/theme";

type SlideProps = {
  children: React.ReactNode;
  eyebrow?: string;
  index: number;
  nextHint?: string;
};

const ParticleField = () => {
  const particles = Array.from({ length: 42 }, (_, i) => {
    const x = (i * 97) % 1080;
    const y = (i * 173) % 1350;
    const size = 1 + (i % 3);
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: size,
          height: size,
          borderRadius: 999,
          background: i % 4 === 0 ? theme.colors.secondary : theme.colors.primary,
          opacity: 0.12 + (i % 5) * 0.025,
          boxShadow: `0 0 ${10 + i}px currentColor`
        }}
      />
    );
  });

  return <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>{particles}</div>;
};

export const Slide = ({ children, eyebrow, index, nextHint }: SlideProps) => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(circle at 18% 8%, rgba(43,238,52,0.15), transparent 30%), radial-gradient(circle at 86% 18%, rgba(0,212,255,0.14), transparent 28%), #0B0F14",
      color: theme.colors.text,
      fontFamily: "Inter, system-ui, sans-serif",
      padding: 58,
      overflow: "hidden"
    }}
  >
    <ParticleField />
    <div
      style={{
        position: "absolute",
        inset: 22,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: 18,
        background: "linear-gradient(135deg, rgba(255,255,255,0.045), rgba(255,255,255,0.01))"
      }}
    />
    <div style={{ position: "relative", zIndex: 2, height: "100%", display: "flex", flexDirection: "column" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 34 }}>
        <div style={{ color: theme.colors.muted, fontSize: 24, fontFamily: "Fira Code, monospace", letterSpacing: 0 }}>
          {eyebrow ?? "ZILLOW REAL ESTATE INTELLIGENCE"}
        </div>
        <div style={{ color: theme.colors.secondary, fontSize: 24, fontFamily: "Fira Code, monospace" }}>
          {String(index).padStart(2, "0")}/10
        </div>
      </header>
      <main style={{ flex: 1 }}>{children}</main>
      {nextHint ? (
        <footer style={{ color: theme.colors.muted, fontSize: 24, fontWeight: 600, display: "flex", justifyContent: "space-between" }}>
          <span>{nextHint}</span>
          <span style={{ color: theme.colors.primary }}>SWIPE</span>
        </footer>
      ) : null}
    </div>
  </AbsoluteFill>
);
