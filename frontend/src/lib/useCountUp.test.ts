// @vitest-environment jsdom
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { useCountUp } from "./useCountUp";

describe("useCountUp Hook", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns null when target value is null", () => {
    const { result } = renderHook(() => useCountUp(null));
    expect(result.current).toBeNull();
  });

  it("returns target immediately when prefers-reduced-motion is true", () => {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const { result } = renderHook(() => useCountUp(10.5));
    expect(result.current).toBe(10.5);
  });
});
