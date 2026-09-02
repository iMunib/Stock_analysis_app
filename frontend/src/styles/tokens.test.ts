import { describe, expect, it } from "vitest";
import { TOKENS } from "./tokens";

describe("Design Tokens System", () => {
  it("defines core background surface tokens", () => {
    expect(TOKENS.surfaces.bg0).toBe("#0a0e14");
    expect(TOKENS.surfaces.bg1).toBe("#131922");
    expect(TOKENS.surfaces.bg2).toBe("#1a222f");
    expect(TOKENS.surfaces.bg3).toBe("#212c3b");
  });

  it("defines typography ink hierarchy tokens", () => {
    expect(TOKENS.typography.ink0).toBe("#f0ede6");
    expect(TOKENS.typography.ink1).toBe("#94a3b8");
    expect(TOKENS.typography.ink2).toBe("#5c6b7d");
  });

  it("defines accent and semantic color tokens", () => {
    expect(TOKENS.accent.gold).toBe("#e0a84f");
    expect(TOKENS.accent.goldWeak).toBe("rgba(224, 168, 79, 0.10)");
    expect(TOKENS.functional.pos).toBe("#4ade80");
    expect(TOKENS.functional.neg).toBe("#f87171");
    expect(TOKENS.functional.warn).toBe("#fbbf24");
    expect(TOKENS.functional.info).toBe("#60a5fa");
  });

  it("defines border and shadow tokens", () => {
    expect(TOKENS.borders.normal).toBe("#232d3a");
    expect(TOKENS.borders.strong).toBe("#364556");
    expect(TOKENS.elevation.card).toBeTruthy();
    expect(TOKENS.elevation.modal).toBeTruthy();
  });

  it("defines 8pt spacing scale variables", () => {
    expect(TOKENS.spacing.space1).toBe(4);
    expect(TOKENS.spacing.space2).toBe(8);
    expect(TOKENS.spacing.space3).toBe(12);
    expect(TOKENS.spacing.space4).toBe(16);
    expect(TOKENS.spacing.space6).toBe(24);
    expect(TOKENS.spacing.space8).toBe(32);
    expect(TOKENS.spacing.space12).toBe(48);
  });

  it("defines font family stacks", () => {
    expect(TOKENS.typography.display).toContain("Spectral");
    expect(TOKENS.typography.heading).toContain("IBM Plex Sans");
    expect(TOKENS.typography.body).toContain("IBM Plex Sans");
    expect(TOKENS.typography.mono).toContain("IBM Plex Mono");
  });
});
