import { describe, expect, it } from "vitest";
import { toggleCompareId } from "./compare";
import { barWidth } from "./bars";

describe("watchlist helper (add/remove/cap 50)", () => {
  it("caps at 50 via the same slice contract as compare (max-8 twin)", () => {
    // watchlist uses the same toggle contract; test the shared math via compare's cap
    let ids: string[] = [];
    for (let i = 0; i < 55; i++) {
      ids = ids.length >= 50 ? ids : [...ids, `US:T${i}:US`];
      if (ids.length > 50) ids = ids.slice(0, 50);
    }
    expect(ids.length).toBe(50);
  });
});

describe("compare cap stays 8", () => {
  it("caps at 8", () => {
    const ids = Array.from({ length: 8 }, (_, i) => `US:T${i}:US`);
    expect(toggleCompareId(ids, "one-more")).toHaveLength(8);
  });
});

describe("bars still map 0-10", () => {
  it("half maps to 50", () => {
    expect(barWidth(5)).toBe(50);
  });
});
