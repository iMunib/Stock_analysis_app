import { describe, expect, it } from "vitest";
import { barWidth, columnHeights } from "./bars";

describe("SVG bar helper maps 0-10 to width", () => {
  it("maps mid, low, high", () => {
    expect(barWidth(5)).toBe(50);
    expect(barWidth(0)).toBe(0);
    expect(barWidth(10)).toBe(100);
    expect(barWidth(8.5)).toBe(85);
  });
  it("treats null as empty (hollow), not zero-fill", () => {
    expect(barWidth(null)).toBe(0);
    expect(barWidth(undefined)).toBe(0);
  });
  it("clamps out-of-range", () => {
    expect(barWidth(15)).toBe(100);
    expect(barWidth(-2)).toBe(0);
  });
});

describe("history column bars never fake a slope", () => {
  it("normalizes to the max (single point = one full bar; the UI hides <3-point trends)", () => {
    expect(columnHeights([42], 100)).toEqual([100]);
  });
  it("normalizes to the max", () => {
    const h = columnHeights([10, 20, 30], 100);
    expect(h[2]).toBe(100);
    expect(h[0]).toBeCloseTo((10 / 30) * 100);
  });
  it("null becomes zero height", () => {
    const h = columnHeights([null, 50], 100);
    expect(h[0]).toBe(0);
    expect(h[1]).toBe(100);
  });
});
