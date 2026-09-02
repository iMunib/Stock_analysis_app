// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import Compare from "./Compare";

describe("Compare headers accessibility and InfoTip", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, "compare").mockResolvedValue({
      currencies: ["USD"],
      rows: [
        {
          company_id: "US:AAPL:US",
          name: "Apple Inc.",
          currency: "USD",
          found: true,
          composite: 8.5,
          quality: 9.0,
          value: 6.0,
          growth: 8.0,
          risk: 8.5,
          signal: "strong_candidate",
          pe_calc: 28.5,
          pb_calc: 45.0,
          ev_to_ebitda_calc: 22.0,
          roe_calc: 1.45,
          roa_calc: 0.28,
          fcfmargin_calc: 0.26,
          peer_rank: 1,
        } as any,
        {
          company_id: "US:MSFT:US",
          name: "Microsoft Corp.",
          currency: "USD",
          found: true,
          composite: 8.2,
          quality: 8.8,
          value: 5.5,
          growth: 8.2,
          risk: 8.0,
          signal: "strong_candidate",
          pe_calc: 32.0,
          pb_calc: 12.0,
          ev_to_ebitda_calc: 24.0,
          roe_calc: 0.38,
          roa_calc: 0.18,
          fcfmargin_calc: 0.31,
          peer_rank: 2,
        } as any,
      ],
    } as any);
  });

  afterEach(() => {
    cleanup();
  });

  it("compare header PE has accessible description containing 'earnings'", async () => {
    const { unmount } = render(
      <MemoryRouter initialEntries={["/compare?ids=US%3AAAPL%3AUS%2CUS%3AMSFT%3AUS"]}>
        <Routes>
          <Route path="/compare" element={<Compare />} />
        </Routes>
      </MemoryRouter>
    );

    const headers = await screen.findAllByRole("columnheader");
    const peHeader = headers.find((h) => h.textContent?.startsWith("PE"));
    expect(peHeader).toBeTruthy();
    if (!peHeader) return;
    expect(peHeader.textContent).toContain("PE");
    // Verify accessible description/label on the header or its InfoTip button contains 'earnings'
    const peBtn = peHeader.querySelector("button");
    expect(peBtn).toBeTruthy();
    const label = peBtn?.getAttribute("aria-label")?.toLowerCase() ?? "";
    const title = peBtn?.getAttribute("title")?.toLowerCase() ?? "";
    expect(label.includes("earnings") || title.includes("earnings")).toBe(true);
    unmount();
  });
});
