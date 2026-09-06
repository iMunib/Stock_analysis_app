// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Dossier from "./Dossier";
import * as clientModule from "../api/client";
import type { DossierOut } from "../api/types";

describe("Dossier Status Ribbon, CIK link, and Dual Currency", () => {
  it("renders status ribbon with dual currency and CIK edgar link for foreign issuer (BABA)", async () => {
    const mockDossier: DossierOut = {
      identity: {
        company_id: "US:BABA:US",
        name: "Alibaba Group Holding Ltd",
        currency: "USD",
        country: "US",
        gics_sector: "Consumer Discretionary",
        gics_industry: "Broadline Retail",
        custom_industry_sheet: "retail",
        indexes: ["ADR"],
        in_sp500: false,
        in_tsx_composite: false,
        cik: 1577552,
        reporting_currency: "CNY",
        filing_type: "20-F",
      },
      latest_snapshot: {
        company_id: "US:BABA:US",
        fiscal_year: 2024,
        source: "sec_companyfacts",
        currency: "CNY",
        revenue: 996_000_000_000,
        net_income: 72_000_000_000,
        price: 85.0,
        price_currency: "USD",
        as_of_date: "2024-03-31",
      },
      history_annual: [],
      score: {
        composite: 6.8,
        pillars: { quality: 7.2, value: 6.5, growth: null, risk: 6.8 },
        coverage: 3,
        penalty: 0.1,
        signal: "favorable",
        peer_set_type: "broad_peer_set",
        peer_rank: 12,
        peer_n: 250,
        as_of_fy: 2024,
        computed_at: "2026-09-02T12:00:00",
        method_version: "v1",
      },
      halal: null,
      data_gaps: ["shares", "history_short"],
      method_version: "v1",
      disclaimer: "Not investment advice.",
    };

    vi.spyOn(clientModule.api, "dossier").mockResolvedValue(mockDossier);
    vi.spyOn(clientModule.api, "similar").mockResolvedValue({ items: [] } as any);

    render(
      <MemoryRouter initialEntries={["/c/US%3ABABA%3AUS"]}>
        <Routes>
          <Route path="/c/:companyId" element={<Dossier />} />
        </Routes>
      </MemoryRouter>
    );

    // Verify status ribbon
    const titles = await screen.findAllByText("Alibaba Group Holding Ltd");
    expect(titles.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByLabelText("Coverage status ribbon")).toBeTruthy();
    expect(screen.getByText(/Revenue CNY 996.00B · trading USD/i)).toBeTruthy();
    expect(screen.getByText(/broad peer set \(n=250\)/i)).toBeTruthy();

    // Verify EDGAR CIK link includes CIK 1577552 and 20-F
    const edgarLink = screen.getByRole("link", { name: /20-F filings on EDGAR/i });
    expect(edgarLink).toBeTruthy();
    expect(edgarLink.getAttribute("href")).toBe("https://www.sec.gov/edgar/browse/?CIK=1577552");

    // Verify actionable gap buttons
    expect(screen.getByRole("button", { name: /Fetch shares from Yahoo/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Retry EDGAR filings/i })).toBeTruthy();

    // Verify Hero split grid with live interactive chart and fundamentals bar
    expect(screen.getByText(/Live Technical Chart/i)).toBeTruthy();
    expect(screen.getAllByText("Price").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Market Cap").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Trailing P/E").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("ROIC").length).toBeGreaterThanOrEqual(1);

    // Verify tab navigation renders workspace tabs without horizontal overflow
    const tablists = screen.getAllByRole("tablist");
    expect(tablists.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("tablist", { name: /Research terminal workspace navigation/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Overview/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Financials/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Technicals & Chart/i })).toBeTruthy();
  });
});

