/**
 * Institutional Equity Desk Design System Tokens
 * Source of truth for styling, visualization primitives, and component themes.
 */

export const TOKENS = {
  surfaces: {
    bg0: "#0a0e14",
    bg1: "#131922",
    bg2: "#1a222f",
    bg3: "#212c3b",
  },
  typography: {
    ink0: "#f0ede6",
    ink1: "#94a3b8",
    ink2: "#5c6b7d",
    display: '"Spectral", Georgia, serif',
    heading: '"IBM Plex Sans", -apple-system, BlinkMacSystemFont, sans-serif',
    body: '"IBM Plex Sans", -apple-system, BlinkMacSystemFont, sans-serif',
    mono: '"IBM Plex Mono", ui-monospace, monospace',
  },
  accent: {
    gold: "#e0a84f",
    goldWeak: "rgba(224, 168, 79, 0.10)",
    goldStrong: "#f5ba5d",
  },
  functional: {
    pos: "#4ade80",
    posWeak: "rgba(74, 222, 128, 0.12)",
    neg: "#f87171",
    negWeak: "rgba(248, 113, 113, 0.12)",
    warn: "#fbbf24",
    warnWeak: "rgba(251, 191, 36, 0.12)",
    info: "#60a5fa",
    infoWeak: "rgba(96, 165, 250, 0.12)",
  },
  borders: {
    normal: "#232d3a",
    strong: "#364556",
  },
  spacing: {
    space1: 4,
    space2: 8,
    space3: 12,
    space4: 16,
    space6: 24,
    space8: 32,
    space12: 48,
  },
  radii: {
    card: 8,
    chip: 4,
    sm: 2,
  },
  elevation: {
    card: "0 2px 8px -2px rgba(0, 0, 0, 0.4), 0 1px 3px -1px rgba(0, 0, 0, 0.25)",
    hover: "0 4px 12px -2px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.35)",
    modal: "0 8px 30px -4px rgba(0, 0, 0, 0.6), 0 4px 10px -2px rgba(0, 0, 0, 0.4)",
  },
  maxWidth: "1280px",
} as const;

export const TOKENS_LIGHT = {
  surfaces: {
    bg0: "#f8fafc",
    bg1: "#ffffff",
    bg2: "#f1f5f9",
    bg3: "#e2e8f0",
  },
  typography: {
    ink0: "#0f172a",
    ink1: "#475569",
    ink2: "#64748b",
    display: '"Spectral", Georgia, serif',
    heading: '"IBM Plex Sans", -apple-system, BlinkMacSystemFont, sans-serif',
    body: '"IBM Plex Sans", -apple-system, BlinkMacSystemFont, sans-serif',
    mono: '"IBM Plex Mono", ui-monospace, monospace',
  },
  accent: {
    gold: "#b47818",
    goldWeak: "rgba(180, 120, 24, 0.10)",
    goldStrong: "#925f0e",
  },
  functional: {
    pos: "#16a34a",
    posWeak: "rgba(22, 163, 74, 0.10)",
    neg: "#dc2626",
    negWeak: "rgba(220, 38, 38, 0.10)",
    warn: "#d97706",
    warnWeak: "rgba(217, 119, 6, 0.10)",
    info: "#2563eb",
    infoWeak: "rgba(37, 99, 235, 0.10)",
  },
  borders: {
    normal: "#e2e8f0",
    strong: "#cbd5e1",
  },
  spacing: TOKENS.spacing,
  radii: TOKENS.radii,
  elevation: {
    card: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.03)",
    hover: "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.04)",
    modal: "0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04)",
  },
  maxWidth: "1280px",
} as const;

export type ThemeMode = "dark" | "light";

export function getThemeTokens(theme: ThemeMode = "dark") {
  return theme === "light" ? TOKENS_LIGHT : TOKENS;
}

export default TOKENS;

