import React from "react";
import { AbsoluteFill } from "remotion";
import { theme } from "../../theme/theme";

const SAFE_TOP = 288;
const SAFE_BOTTOM = 192;
const TOTAL_HEIGHT = 1920;

type ShortSlideProps = {
  children: React.ReactNode;
  sceneLabel?: string;
};

const ParticleField = () => {
  const particles = Array.from({ length: 56 }, (_, i) => {
    const x = (i * 97) % 1080;
    const y = (i * 173) % TOTAL_HEIGHT;
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
          opacity: 0.10 + (i % 5) * 0.02,
          boxShadow: `0 0 ${8 + i}px currentColor`,
        }}
      />
    );
  });

  return <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>{particles}</div>;
};

export const ShortSlide = ({ children, sceneLabel }: ShortSlideProps) => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(circle at 18% 8%, rgba(43,238,52,0.12), transparent 30%), radial-gradient(circle at 86% 18%, rgba(0,212,255,0.10), transparent 28%), #0B0F14",
      color: theme.colors.text,
      fontFamily: "Inter, system-ui, sans-serif",
      overflow: "hidden",
    }}
  >
    <ParticleField />
    <div
      style={{
        position: "absolute",
        inset: 16,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: 22,
        background: "linear-gradient(135deg, rgba(255,255,255,0.045), rgba(255,255,255,0.01))",
      }}
    />
    <div
      style={{
        position: "relative",
        zIndex: 2,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        paddingTop: SAFE_TOP,
        paddingBottom: SAFE_BOTTOM,
        paddingLeft: 60,
        paddingRight: 60,
      }}
    >
      {sceneLabel && (
        <div
          style={{
            color: theme.colors.muted,
            fontSize: 20,
            fontFamily: "Fira Code, monospace",
            letterSpacing: 0,
            marginBottom: 20,
          }}
        >
          {sceneLabel}
        </div>
      )}
      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {children}
      </main>
    </div>
  </AbsoluteFill>
);
