// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ForensicCard } from "./ForensicCard";
import { ReverseDCFCard } from "./ReverseDCFCard";

afterEach(() => {
  cleanup();
});

vi.mock("../api/client", () => ({
  api: {
    forensics: vi.fn().mockResolvedValue({
      company_id: "US:AAPL:US",
      currency: "USD",
      sloan_accrual_ratio: 0.04,
      sloan_signal: "neutral",
      cash_conversion_ratio: 0.85,
      cash_conversion_signal: "healthy",
      roic: 0.28,
      fcf_yield: 0.05,
      nopat: 110000000000,
      invested_capital: 390000000000,
      fcf_vs_ni_history: [
        { fiscal_year: 2021, net_income: 94680000000, fcf: 92953000000 },
        { fiscal_year: 2022, net_income: 99803000000, fcf: 111443000000 },
        { fiscal_year: 2023, net_income: 96995000000, fcf: 99584000000 },
        { fiscal_year: 2024, net_income: 93736000000, fcf: 108807000000 },
        { fiscal_year: 2025, net_income: 100000000000, fcf: 98767000000 },
      ],
    }),
    valuation: vi.fn().mockResolvedValue({
      company_id: "US:AAPL:US",
      status: "converged",
      current_share_price: 230.0,
      diluted_shares: 14594180000,
      net_debt: 54744000000,
      baseline_fcf: 98767000000,
      wacc: 0.09,
      terminal_growth_rate: 0.025,
      market_implied_growth_10y: 0.108,
      historical_5y_cagr: 0.085,
      expectations_gap: 0.023,
      sensitivity_matrix: {
        wacc_headers: [0.08, 0.09, 0.10],
        terminal_g_headers: [0.02, 0.025, 0.03],
        grid: [
          [
            { wacc: 0.08, terminal_g: 0.02, implied_growth: 0.095 },
            { wacc: 0.08, terminal_g: 0.025, implied_growth: 0.088 },
            { wacc: 0.08, terminal_g: 0.03, implied_growth: 0.081 },
          ],
          [
            { wacc: 0.09, terminal_g: 0.02, implied_growth: 0.115 },
            { wacc: 0.09, terminal_g: 0.025, implied_growth: 0.108 },
            { wacc: 0.09, terminal_g: 0.03, implied_growth: 0.101 },
          ],
          [
            { wacc: 0.10, terminal_g: 0.02, implied_growth: 0.135 },
            { wacc: 0.10, terminal_g: 0.025, implied_growth: 0.128 },
            { wacc: 0.10, terminal_g: 0.03, implied_growth: 0.121 },
          ],
        ],
      },
    }),
  },
}));

describe("ForensicCard Component", () => {
  it("renders accrual metrics, cash conversion, and SVG trajectory", async () => {
    render(<ForensicCard companyId="US:AAPL:US" />);
    await waitFor(() => {
      expect(screen.getByText("Forensic Quality Suite")).toBeDefined();
      expect(screen.getByText("Sloan Accruals")).toBeDefined();
      expect(screen.getByText("4.0%")).toBeDefined();
      expect(screen.getByText("Cash Conversion (CCER)")).toBeDefined();
      expect(screen.getByText("85%")).toBeDefined();
      expect(screen.getByText("5-Year Free Cash Flow vs. Net Income Trajectory")).toBeDefined();
    });
  });
});

describe("ReverseDCFCard Component", () => {
  it("renders market implied growth, expectations spread, and sensitivity matrix", async () => {
    render(<ReverseDCFCard companyId="US:AAPL:US" />);
    await waitFor(() => {
      expect(screen.getByText("Deterministic Reverse DCF")).toBeDefined();
      expect(screen.getByText("Market-Implied 10Y FCF CAGR")).toBeDefined();
      expect(screen.getAllByText("10.8%").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Historical FCF CAGR (5Y)")).toBeDefined();
      expect(screen.getByText("8.5%")).toBeDefined();
      expect(screen.getByText("+2.3%")).toBeDefined();
      expect(screen.getByText("Sensitivity Matrix: Implied Growth Rate (WACC vs. Terminal g)")).toBeDefined();
    });
  });
});
