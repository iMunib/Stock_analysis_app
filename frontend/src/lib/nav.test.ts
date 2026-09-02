import { describe, expect, it } from "vitest";
import { MAX_COMPARE, compareIdsToQuery, toggleCompareId } from "./compare";
import { gicsSheetParam, navItems, sectorCardKey } from "./nav";

describe("compare ids builder (max 8)", () => {
  it("adds and removes", () => {
    expect(toggleCompareId(["A"], "B")).toEqual(["A", "B"]);
    expect(toggleCompareId(["A", "B"], "A")).toEqual(["B"]);
  });
  it("caps at MAX_COMPARE", () => {
    const ids = ["a", "b", "c", "d", "e", "f", "g", "h"];
    expect(toggleCompareId(ids, "i")).toHaveLength(MAX_COMPARE);
    expect(toggleCompareId(ids, "i")).toEqual(ids);
  });
  it("serializes to a query string", () => {
    expect(compareIdsToQuery(["US:AAPL:US", "CA:RY:TSX"])).toBe("US:AAPL:US,CA:RY:TSX");
  });
});

describe("sector card keys are unique", () => {
  it("never collides between custom and gics groups", () => {
    const keys = [
      sectorCardKey("custom", "Banks"),
      sectorCardKey("gics", "Financials"),
      sectorCardKey("custom", "Financials"),
      sectorCardKey("gics", "Banks"),
    ];
    expect(new Set(keys).size).toBe(keys.length);
  });
  it("prefixes GICS sheets", () => {
    expect(gicsSheetParam("Financials")).toBe("GICS_Financials");
  });
});

describe("nav routes", () => {
  it("always includes Jobs (Stage C)", () => {
    const labels = navItems(false).map((i) => i.label);
    expect(labels).toEqual(["Desk", "Sectors", "Compare", "Jobs", "Learn"]);
  });
  it("shows Jobs when available", () => {
    expect(navItems(true).map((i) => i.label)).toContain("Jobs");
  });});
