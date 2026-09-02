/** Shared tone mapping for signal colors (single source for badges/histograms). */
export function signalTone(signal: string | null | undefined): "good" | "mid" | "bad" | "info" {
  switch (signal) {
    case "strong_candidate":
    case "constructive":
      return "good";
    case "mixed":
      return "mid";
    case "weak":
    case "avoid":
      return "bad";
    default:
      return "info";
  }
}

export const SIGNAL_ORDER = [
  "strong_candidate",
  "constructive",
  "mixed",
  "weak",
  "avoid",
  "insufficient_data",
  "score_missing",
] as const;
