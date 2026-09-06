/** Phase 9: compose an "All" view from USD + CAD without ever blending money. */
import type { SectorSnapshotOut } from "../api/types";

export type CurrencyView = "ALL" | "USD" | "CAD";

export interface ComposedAll {
  companies: number;
  scored: number;
  /** Unitless median composite across both currencies (allowed: unitless). */
  median_composite: number | null;
  /** Money medians stay split per currency - never averaged. */
  money_by_currency: {
    USD: { median_pe: number | null; median_pb: number | null; median_roe: number | null; companies: number } | null;
    CAD: { median_pe: number | null; median_pb: number | null; median_roe: number | null; companies: number } | null;
  };
  signal_histogram: Record<string, number>;
}

function median(vals: number[]): number | null {
  const v = vals.filter((x) => x != null && x === x).sort((a, b) => a - b);
  if (!v.length) return null;
  const n = v.length;
  return v[n >> 1] ?? null;
}

export function composeAll(usd: SectorSnapshotOut, cad: SectorSnapshotOut): ComposedAll;
export function composeAll(usd?: SectorSnapshotOut | null, cad?: SectorSnapshotOut | null): ComposedAll | null;
export function composeAll(usd?: SectorSnapshotOut | null, cad?: SectorSnapshotOut | null): ComposedAll | null {
  if (!usd && !cad) return null;
  const u = usd ?? { companies: 0, scored: 0, median_composite: null, median_pe: null, median_pb: null, median_roe: null, signal_histogram: {} };
  const c = cad ?? { companies: 0, scored: 0, median_composite: null, median_pe: null, median_pb: null, median_roe: null, signal_histogram: {} };
  const hist: Record<string, number> = {};
  for (const [k, n] of Object.entries(u.signal_histogram ?? {})) hist[k] = (hist[k] ?? 0) + n;
  for (const [k, n] of Object.entries(c.signal_histogram ?? {})) hist[k] = (hist[k] ?? 0) + n;
  const comps = [u.median_composite, c.median_composite].filter((x): x is number => x != null);
  return {
    companies: u.companies + c.companies,
    scored: u.scored + c.scored,
    median_composite: median(comps),
    money_by_currency: {
      USD: u.companies > 0 ? { median_pe: u.median_pe, median_pb: u.median_pb, median_roe: u.median_roe, companies: u.companies } : null,
      CAD: c.companies > 0 ? { median_pe: c.median_pe, median_pb: c.median_pb, median_roe: c.median_roe, companies: c.companies } : null,
    },
    signal_histogram: hist,
  };
}