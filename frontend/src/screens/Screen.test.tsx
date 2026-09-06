// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import ScreenComponent from "./Screen";
import * as clientModule from "../api/client";
import type { ScreenOut } from "../api/types";

describe("Screener component", () => {
  it("renders filters and table rows from api", async () => {
    const mockScreenOut: ScreenOut = {
      total: 2,
      count: 2,
      currency_view: "ALL",
      method_version: "v1",
      disclaimer: "personal research software",
      items: [
        {
          company_id: "US:AAPL:US",
          name: "Apple Inc.",
          ticker: "AAPL",
          currency: "USD",
          gics_sector: "Information Technology",
          custom_industry_sheet: "Tech",
          composite: 5.1,
          signal: "mixed",
          pe_calc: 30.5,
          roe_calc: 1.5,
          fcfmargin_calc: 0.24,
          peer_rank: 12,
          peer_n: 26,
          coverage: 4,
          has_growth_history: true,
          is_bank: false,
          halal_status: "unknown",
        },
        {
          company_id: "CA:RY:TSX",
          name: "Royal Bank of Canada",
          ticker: "RY",
          currency: "CAD",
          gics_sector: "Financials",
          custom_industry_sheet: "Banks",
          composite: 4.8,
          signal: "balanced_opportunity",
          pe_calc: 13.2,
          roe_calc: 0.14,
          fcfmargin_calc: null,
          peer_rank: 2,
          peer_n: 8,
          coverage: 3,
          has_growth_history: true,
          is_bank: true,
          halal_status: "not_halal",
        },
      ],
    };

    vi.spyOn(clientModule.api, "screen").mockResolvedValue(mockScreenOut);
    vi.spyOn(clientModule.api, "sectors").mockResolvedValue({
      custom_industries: [{ name: "Tech", count: 26, usd: 20, cad: 6 }],
      gics_sectors: [{ name: "Information Technology", count: 80, usd: 70, cad: 10 }],
    });

    render(
      <MemoryRouter initialEntries={["/screen"]}>
        <ScreenComponent />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Screener" })).toBeTruthy();
    expect(screen.getByText("Currency")).toBeTruthy();
    expect(screen.getByLabelText(/Sector/i)).toBeTruthy();

    expect(await screen.findByText("Apple Inc.")).toBeTruthy();
    expect(screen.getByText("Royal Bank of Canada")).toBeTruthy();
    expect(screen.getByText("30.5")).toBeTruthy();
  });

  it("shows empty state message when no items match", async () => {
    vi.spyOn(clientModule.api, "screen").mockResolvedValue({
      total: 0,
      count: 0,
      currency_view: "ALL",
      method_version: "v1",
      disclaimer: "personal research software",
      items: [],
    });
    vi.spyOn(clientModule.api, "sectors").mockResolvedValue({
      custom_industries: [],
      gics_sectors: [],
    });

    render(
      <MemoryRouter initialEntries={["/screen"]}>
        <ScreenComponent />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("No names match - loosen PE or coverage.")).toBeTruthy();
    });
  });
});