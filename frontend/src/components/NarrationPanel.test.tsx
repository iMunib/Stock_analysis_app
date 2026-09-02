// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import NarrationPanel from "./NarrationPanel";

describe("NarrationPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("handles HTML 504 gateway timeout gracefully without SyntaxError: Unexpected token '<'", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 504,
        text: async () => "<html><head><title>504 Gateway Time-out</title></head><body><center><h1>504 Gateway Time-out</h1></center></body></html>",
      }))
    );

    render(<NarrationPanel endpoint="/api/v1/companies/US:AAPL:US/narrate" label="Plain-English explanation" />);

    const btn = screen.getByRole("button", { name: /generate explanation/i });
    expect(btn).toBeTruthy();

    fireEvent.click(btn);

    // Wait for the friendly error banner to appear
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });

    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("Narration unavailable");
    expect(alert.textContent).toContain("504");
    expect(alert.textContent).not.toContain("Unexpected token");
  });

  it("disables button and shows spinner while generating", async () => {
    let resolvePromise: (val: any) => void = () => {};
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    vi.stubGlobal(
      "fetch",
      vi.fn(() => pendingPromise)
    );

    render(<NarrationPanel endpoint="/api/v1/companies/US:AAPL:US/narrate" label="Plain-English explanation" />);

    const btn = screen.getByRole("button", { name: /generate explanation/i });
    fireEvent.click(btn);

    // Button should now be disabled and show loading state
    expect((btn as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/30–90s on free models/i)).toBeTruthy();

    // Resolve successfully
    resolvePromise({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ narration: "AAPL is strong.", model: "test-model:free", cached: true }),
    });

    await waitFor(() => {
      expect(screen.getByText("AAPL is strong.")).toBeTruthy();
    });
  });
});
