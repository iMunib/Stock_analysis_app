/** SVG bar helpers (pure). No chart library — just width/height math. */

export function barWidth(value: number | null | undefined, max = 10): number {
  if (value == null || Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, (value / max) * 100));
}

/** Normalize a series to 0..height for column bars; null/negative -> 0 (no fake slope). */
export function columnHeights(values: (number | null | undefined)[], height = 100): number[] {
  const nums = values.map((v) => (v == null || Number.isNaN(v) || v < 0 ? 0 : v));
  const max = Math.max(...nums, 0);
  if (max === 0) return nums.map(() => 0);
  return nums.map((n) => (n / max) * height);
}

export function pillarWidths(p: {
  quality: number | null;
  value: number | null;
  growth: number | null;
  risk: number | null;
}): { quality: number; value: number; growth: number; risk: number } {
  return {
    quality: barWidth(p.quality),
    value: barWidth(p.value),
    growth: barWidth(p.growth),
    risk: barWidth(p.risk),
  };
}
