import { describe, expect, it } from "vitest";
import { money, multiple, percentish, score1, yoyPct } from "./format";

describe("percentish formatting (compare 30.2% not 0.3)", () => {
  it("treats fractions as percents, including high-ROE compounders like AAPL (1.519 -> 151.9%)", () => {
    expect(percentish(0.302)).toBe("30.2%");
    expect(percentish(0.3)).toBe("30.0%");
    expect(percentish(1.519)).toBe("151.9%");
    expect(percentish(-0.05)).toBe("-5.0%");
  });
  it("treats |x| > 5.0 as already-percent", () => {
    expect(percentish(30.2)).toBe("30.2%");
    expect(percentish(45)).toBe("45.0%");
  });
  it("null is a dash", () => {
    expect(percentish(null)).toBe("—");
    expect(percentish(undefined)).toBe("—");
  });
});

describe("multiples and scores", () => {
  it("keeps one decimal without %", () => {
    expect(multiple(26.9)).toBe("26.9");
    expect(multiple(8.05)).toBe("8.1");
    expect(multiple(null)).toBe("—");
  });
  it("scores one decimal", () => {
    expect(score1(6.06)).toBe("6.1");
    expect(score1(null)).toBe("—");
  });
  it("money keeps currency and dash", () => {
    expect(money(24_948_000_000, "USD")).toContain("24.95B USD");
    expect(money(null, "USD")).toBe("—");
  });
});

describe("yoy", () => {
  it("computes growth and refuses nulls", () => {
    expect(yoyPct(245, 212)).toBeCloseTo(15.566);
    expect(yoyPct(245, null)).toBeNull();
    expect(yoyPct(null, 212)).toBeNull();
  });
});
