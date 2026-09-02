import { describe, expect, it } from "vitest";
import { composeAll } from "./allCurrency";
import type { SectorSnapshotOut } from "../api/types";

const snap = (over: Partial<SectorSnapshotOut>): SectorSnapshotOut => ({
  sheet: "Banks",
  currency: "USD",
  companies: 2,
  scored: 2,
  signal_histogram: { mixed: 2 },
  median_composite: 5,
  median_pe: 10,
  median_pb: 1,
  median_roe: 0.1,
  top: [],
  bottom: [],
  method_version: "v1",
  disclaimer: "d",
  ...over,
});

describe("All composer never averages Revenue/money across USD+CAD", () => {
  it("keeps money medians split per currency", () => {
    const usd = snap({ currency: "USD", median_pe: 10, median_pb: 1, median_roe: 0.1, companies: 2 });
    const cad = snap({ currency: "CAD", median_pe: 30, median_pb: 2, median_roe: 0.2, companies: 3 });
    const all = composeAll(usd, cad);
    // The single blended median would be (10+30)/2 = 20 — it must NOT appear anywhere.
    expect(JSON.stringify(all)).not.toContain("20");
    expect(all.money_by_currency.USD?.median_pe).toBe(10);
    expect(all.money_by_currency.CAD?.median_pe).toBe(30);
    expect(all.median_composite).toBe(5); // unitless composite median is fine
    expect(all.companies).toBe(5);
  });
  it("sums the signal histogram", () => {
    const usd = snap({ signal_histogram: { mixed: 2, avoid: 1 } });
    const cad = snap({ signal_histogram: { mixed: 3 } });
    const all = composeAll(usd, cad);
    expect(all.signal_histogram).toEqual({ mixed: 5, avoid: 1 });
  });
});
