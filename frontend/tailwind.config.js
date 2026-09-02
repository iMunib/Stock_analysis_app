/** Tailwind config — "night research desk" theme. */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0e1319",
        panel: "#141a21",
        panel2: "#1a222b",
        line: "#27313c",
        line2: "#33404d",
        paper: "#e8e4da",
        fog: "#8fa0b0",
        dim: "#5c6b7a",
        gold: "#e0a84f",
        goldsoft: "#8a6a35",
        good: "#5fb57a",
        mid: "#d9a441",
        warn: "#cf7a4e",
        bad: "#c45a4e",
        info: "#7ba3c9",
      },
      fontFamily: {
        display: ["Spectral", "Georgia", "serif"],
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      maxWidth: {
        desk: "72rem",
      },
    },
  },
  plugins: [],
};
