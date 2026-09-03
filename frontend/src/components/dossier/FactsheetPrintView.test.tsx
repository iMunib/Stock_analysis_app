// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { FactsheetPrintView } from "./FactsheetPrintView";
import type { DossierOut, PractitionerOut } from "../../api/types";

describe("FactsheetPrintView", () => {
  it("renders 2-page institutional memo with executive summary and pillars", () => {
    const mockDossier: DossierOut = {
      identity: {
        company_id: "US:MSFT:US",
        ticker: "MSFT",
        name: "Microsoft Corporation",
        currency: "USD",
        country: "US",
        gics_sector: "Information Technology",
        gics_industry: "Software",
        custom_industry_sheet: "Tech",
        indexes: ["SP500", "QQQ", "SPUS"],
        in_sp500: true,
        in_tsx_composite: false,
      },
      latest_snapshot: {
        company_id: "US:MSFT:US",
        fiscal_year: 2024,
        period_type: "FY",
        currency: "USD",
        revenue: 245122000000,
        net_income: 88136000000,
        fcf_calc: 74071000000,
        price: 420.0,
        market_cap: 3100000000000,
        pe_calc: 35.2,
      },
      history_annual: [],
      score: {
        composite: 7.8,
        pillars: {
          quality: 8.5,
          value: 5.2,
          growth: 8.0,
          risk: 9.0,
        },
        coverage: 4,
        penalty: 0,
        signal: "strong_candidate",
        peer_set_type: "sector",
        peer_rank: 5,
        peer_n: 75,
        as_of_fy: 2024,
        computed_at: "2026-09-02",
        method_version: "v1",
      },
      halal: null,
      data_gaps: [],
      method_version: "v1",
      disclaimer: "Research memo only",
    };

    const mockPractitioner: PractitionerOut = {
      company_id: "US:MSFT:US",
      beneish_analysis: {
        company_id: "US:MSFT:US",
        fiscal_year: 2024,
        status: "computed",
        m_score: -2.45,
        is_manipulator: false,
        zone: "Non-manipulator",
        threshold: -1.78,
        interpretation: "Low probability of earnings manipulation",
      },
      distress_analysis: {
        company_id: "US:MSFT:US",
        status: "computed",
        model_used: "manufacturing",
        z_score: 4.82,
        zone: "Safe",
        active_z: 4.82,
        z_double_prime: null,
        factors: {
          x1_working_capital_to_ta: 0.15,
          x2_retained_earnings_to_ta: 0.45,
          x3_ebit_to_ta: 0.22,
          x4_market_equity_to_tl: 2.5,
          x5_sales_to_ta: 0.5,
        },
      },
    };

    render(<FactsheetPrintView dossier={mockDossier} practitioner={mockPractitioner} />);
    expect(screen.getByText("MSFT")).toBeDefined();
    expect(screen.getByText("Microsoft Corporation")).toBeDefined();
    expect(screen.getByText("Institutional Equity Research Factsheet")).toBeDefined();
    expect(screen.getByText("4-Pillar Fundamental Framework (MATH v1)")).toBeDefined();
    expect(screen.getByText("Altman Z-Score")).toBeDefined();
    expect(screen.getByText("4.82")).toBeDefined();
    expect(screen.getByText("Beneish M-Score")).toBeDefined();
    expect(screen.getByText("-2.45")).toBeDefined();
  });
});
