/** Tailwind config — "night research desk" theme wired to CSS tokens. */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Design System Surface Tokens
        "bg-0": "var(--bg-0)",
        "bg-1": "var(--bg-1)",
        "bg-2": "var(--bg-2)",
        "bg-3": "var(--bg-3)",

        // Design System Typography Tokens
        "ink-0": "var(--ink-0)",
        "ink-1": "var(--ink-1)",
        "ink-2": "var(--ink-2)",

        // Accent Tokens
        accent: "var(--accent)",
        "accent-weak": "var(--accent-weak)",
        "accent-strong": "var(--accent-strong)",

        // Status & Flag Tokens (strictly directional/status, never decorative)
        pos: "var(--pos)",
        "pos-weak": "var(--pos-weak)",
        neg: "var(--neg)",
        "neg-weak": "var(--neg-weak)",
        warn: "var(--warn)",
        "warn-weak": "var(--warn-weak)",
        info: "var(--info)",
        "info-weak": "var(--info-weak)",

        // Hairlines & Borders
        border: "var(--border)",
        "border-strong": "var(--border-strong)",

        // Legacy Aliases for Seamless Backward Compatibility
        ink: "var(--bg-0)",
        panel: "var(--bg-1)",
        panel2: "var(--bg-2)",
        line: "var(--border)",
        line2: "var(--border-strong)",
        paper: "var(--ink-0)",
        fog: "var(--ink-1)",
        dim: "var(--ink-2)",
        gold: "var(--accent)",
        goldsoft: "#8a6a35",
        good: "var(--pos)",
        mid: "var(--warn)",
        bad: "var(--neg)",
      },
      fontFamily: {
        display: ["Spectral", "Georgia", "serif"],
        heading: ['"IBM Plex Sans"', "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        sans: ['"IBM Plex Sans"', "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "var(--radius-card)",
        chip: "var(--radius-chip)",
        sm: "var(--radius-sm)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        hover: "var(--shadow-hover)",
      },
      maxWidth: {
        desk: "var(--max-page-width)",
        "7xl": "80rem",
      },
      spacing: {
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "6": "24px",
        "8": "32px",
        "12": "48px",
      },
    },
  },
  plugins: [],
};
