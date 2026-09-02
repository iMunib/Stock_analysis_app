import { describe, expect, it } from "vitest";
import { enc } from "./client";
import { coveragePenaltyCopy, growthCopy, halalCopy, mixedCurrencyWarning, money, signalCopy, signalLabel, whyBullets } from "./copy";
import type { DossierOut } from "./types";
import { signalTone } from "./visuals";

describe("company_id URL encoding", () => {
  it("encodes colons for URLs", () => {
    expect(enc("US:AAPL:US")).toBe("US%3AAAPL%3AUS");
    expect(enc("CA:IIP.UN:TSX")).toBe("CA%3AIIP.UN%3ATSX");
  });
  it("round-trips through decodeURIComponent", () => {
    const id = "CA:BN:TSX";
    expect(decodeURIComponent(enc(id))).toBe(id);
  });
});

describe("mixed-currency warning", () => {
  it("is true only with 2+ currencies", () => {
    expect(["USD", "CAD"].length > 1).toBe(true);
    expect(["USD"].length > 1).toBe(false);
  });
});

describe("pillar template picker", () => {
  it("uses the locked copy for NULL growth", () => {
    expect(growthCopy(null)).toBe("Growth not scored — fewer than 3 years of history in the database.");
  });
  it("uses the locked copy for coverage penalty", () => {
    expect(coveragePenaltyCopy(3, 0.92)).toContain("Composite reduced");
    expect(coveragePenaltyCopy(4, 1)).toBeNull();
  });
  it("uses the locked copy for mixed signal", () => {
    expect(signalCopy("mixed")).toBe("Neither cheap nor clearly high-quality versus peers in the same currency.");
  });
  it("uses the locked halal copy", () => {
    expect(halalCopy("not_halal")).toContain("Not a religious ruling");
    expect(halalCopy("unknown")).toContain("missing inputs");
  });
  it("labels signals in plain words", () => {
    expect(signalLabel("avoid")).toBe("Avoid");
    expect(signalLabel(null)).toBe("Not scored");
  });
  it("shows money with currency and em-dash for null", () => {
    expect(money(null, "USD")).toBe("—");
    expect(money(24_948_000_000, "USD")).toContain("B");
    expect(money(24_948_000_000, "USD")).toContain("USD");
  });
  it("maps signals to consistent visual tones", () => {
    expect(signalTone("avoid")).toBe("bad");
    expect(signalTone("constructive")).toBe("good");
    expect(signalTone(null)).toBe("info");
  });
});

const baseDossier: DossierOut = {
  identity: { company_id: "US:X:US", name: "X", currency: "USD", country: "US", gics_sector: "Industrials", gics_industry: null, custom_industry_sheet: "Industrials", indexes: [], in_sp500: true, in_tsx_composite: false },
  latest_snapshot: { pe_calc: 15, pb_calc: 2, roe_calc: 0.18, fcfmargin_calc: 0.1 },
  history_annual: [],
  score: { composite: 5, pillars: { quality: 6, value: 5, growth: null, risk: 6 }, coverage: 3, penalty: 0.92, signal: "mixed", peer_set_type: "custom_industry_currency", peer_rank: 3, peer_n: 20, as_of_fy: 2024, computed_at: null, method_version: "v1" },
  halal: { status: "unknown", method: "aaoifi_style_v1", failed_tests: [] },
  data_gaps: ["growth_history"],
  method_version: "v1",
  disclaimer: "d",
};

describe("why bullets", () => {
  it("does not claim growth when growth is null", () => {
    const b = whyBullets(baseDossier);
    expect(b.some((x) => /growth scored/i.test(x))).toBe(false);
    expect(b.some((x) => /Growth not scored/i.test(x))).toBe(true);
  });
  it("mentions valuation and peer rank", () => {
    const b = whyBullets(baseDossier);
    expect(b.some((x) => /15\.0× earnings/.test(x))).toBe(true);
    expect(b.some((x) => /Ranks 3 of 20/.test(x))).toBe(true);
  });
});

describe("mixed-currency warning", () => {
  it("warns only with two currencies", () => {
    expect(mixedCurrencyWarning(["USD", "CAD"])).toContain("never converted");
    expect(mixedCurrencyWarning(["USD"])).toBeNull();
    expect(mixedCurrencyWarning([])).toBeNull();
  });
});
