/** Phase 9: compose an "All" view from USD + CAD without ever blending money. */
import type { SectorSnapshotOut } from "../api/types";

export type CurrencyView = "ALL" | "USD" | "CAD";

export interface ComposedAll {
  companies: number;
  scored: number;
  /** Unitless median composite across both currencies (allowed: unitless). */
  median_composite: number | null;
  /** Money medians stay split per currency — never averaged. */
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

export function composeAll(usd: SectorSnapshotOut, cad: SectorSnapshotOut): ComposedAll {
  const hist: Record<string, number> = {};
  for (const [k, n] of Object.entries(usd.signal_histogram ?? {})) hist[k] = (hist[k] ?? 0) + n;
  for (const [k, n] of Object.entries(cad.signal_histogram ?? {})) hist[k] = (hist[k] ?? 0) + n;
  const comps = [usd.median_composite, cad.median_composite].filter((x): x is number => x != null);
  return {
    companies: usd.companies + cad.companies,
    scored: usd.scored + cad.scored,
    median_composite: median(comps),
    money_by_currency: {
      USD: { median_pe: usd.median_pe, median_pb: usd.median_pb, median_roe: usd.median_roe, companies: usd.companies },
      CAD: { median_pe: cad.median_pe, median_pb: cad.median_pb, median_roe: cad.median_roe, companies: cad.companies },
    },
    signal_histogram: hist,
  };
}
