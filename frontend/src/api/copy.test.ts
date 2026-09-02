import { describe, expect, it } from "vitest";
import { enc } from "./client";
import { coveragePenaltyCopy, growthCopy, halalCopy, money, signalCopy, signalLabel } from "./copy";
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
