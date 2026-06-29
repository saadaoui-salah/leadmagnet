import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B0F14",
        surface: "#151B24",
        green: "#2BEE34",
        cyan: "#00D4FF",
        text: "#F5F7FA",
        muted: "#94A3B8"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Fira Code", "monospace"]
      }
    }
  },
  plugins: []
} satisfies Config;
