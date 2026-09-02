/** Single source of truth for number formatting (Phase 10 B). */

/** Ratios that are conceptually percents: 0.302 → "30.2%", 30.2 → "30.2%" (never 0.3). */
export function percentish(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const abs = Math.abs(v);
  const frac = abs <= 1.5 ? v * 100 : v;
  return `${frac.toFixed(digits)}%`;
}

/** Multiples: one decimal, no % (26.9, 8.1, 20.4). */
export function multiple(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(digits);
}

/** Money with currency suffix; null → "—". Does not prefix non-dollar currencies (e.g. CNY) with $. */
export function money(v: number | null | undefined, currency: string | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const sign = v < 0 ? "-" : "";
  const abs = Math.abs(v);
  const cur = (currency ?? "").trim().toUpperCase();
  const isDollar = !cur || cur === "USD" || cur === "CAD";
  const sym = isDollar ? "$" : `${cur} `;
  const suffix = isDollar && cur ? ` ${cur}` : "";
  if (abs >= 1e12) return `${sign}${sym}${(abs / 1e12).toFixed(2)}T${suffix}`;
  if (abs >= 1e9) return `${sign}${sym}${(abs / 1e9).toFixed(2)}B${suffix}`;
  if (abs >= 1e6) return `${sign}${sym}${(abs / 1e6).toFixed(1)}M${suffix}`;
  return `${sign}${sym}${abs.toLocaleString()}${suffix}`;
}

/** Composite/pillars: one decimal. */
export function score1(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(1);
}

/** YoY change between two raw values, returns null when not computable. */
export function yoyPct(cur: number | null | undefined, prev: number | null | undefined): number | null {
  if (cur == null || prev == null || prev === 0) return null;
  return ((cur - prev) / Math.abs(prev)) * 100;
}
