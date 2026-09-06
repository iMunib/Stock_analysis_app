// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import PiotroskiCard from "./PiotroskiCard";
import DuPontCard from "./DuPontCard";
import PeerMatrixCard from "./PeerMatrixCard";
import CommandPalette from "../common/CommandPalette";

// Mock api methods
vi.mock("../../api/client", () => ({
  api: {
    piotroski: vi.fn().mockResolvedValue({
      company_id: "US:AAPL:US",
      fiscal_year: 2024,
      prior_fiscal_year: 2023,
      f_score: 7,
      f_possible: 9,
      signal: "Strong",
      interpretation: "Exceptional fundamental health and operational turnaround momentum.",
      is_bank: false,
      tests: {
        roa_positive: {
          name: "Positive Return on Assets",
          category: "Profitability",
          passed: true,
          current_value: 0.28,
          prior_value: null,
          description: "Net income is positive relative to total assets.",
        },
      },
      categories: {
        profitability: [
          {
            name: "Positive Return on Assets",
            category: "Profitability",
            passed: true,
            current_value: 0.28,
            prior_value: null,
            description: "Net income is positive relative to total assets.",
          },
        ],
        leverage_liquidity: [],
        efficiency: [],
      },
    }),
    dupont: vi.fn().mockResolvedValue({
      company_id: "US:AAPL:US",
      is_bank: false,
      primary_driver: "Operational Margin Expansion",
      driver_explanation: "ROE expansion is driven by pricing power and expanding net profit margins.",
      latest: {
        fiscal_year: 2024,
        roe_direct: 1.52,
        net_profit_margin: 0.24,
        asset_turnover: 1.05,
        equity_multiplier: 6.03,
        roe_3stage: 1.52,
        tax_burden: 0.85,
        interest_burden: 0.98,
        operating_margin: 0.31,
        roe_5stage: 1.52,
        revenue: 391000000000,
        net_income: 93700000000,
        ebit: 123000000000,
        total_assets: 364000000000,
        book_equity: 60000000000,
      },
      history: [
        {
          fiscal_year: 2024,
          roe_direct: 1.52,
          net_profit_margin: 0.24,
          asset_turnover: 1.05,
          equity_multiplier: 6.03,
          roe_3stage: 1.52,
          tax_burden: 0.85,
          interest_burden: 0.98,
          operating_margin: 0.31,
          roe_5stage: 1.52,
          revenue: 391000000000,
          net_income: 93700000000,
          ebit: 123000000000,
          total_assets: 364000000000,
          book_equity: 60000000000,
        },
      ],
    }),
    peerMatrix: vi.fn().mockResolvedValue({
      company_id: "US:AAPL:US",
      peer_group: "Information Technology (USD)",
      peer_count: 73,
      pillars: {
        valuation: {
          pe_ratio: { value: 31.5, percentile: 45.0 },
        },
        quality: {
          roic: { value: 0.42, percentile: 92.0 },
        },
        financial_health: {
          altman_z: { value: 8.5, percentile: 85.0 },
        },
        capital_allocation: {
          true_shareholder_yield: { value: 0.04, percentile: 72.0 },
        },
      },
    }),
    suggestions: vi.fn().mockResolvedValue({ items: [] }),
  },
  enc: (s: string) => encodeURIComponent(s),
}));

describe("Institutional Analysis Cards", () => {
  it("renders PiotroskiCard with score, signal, and factors", async () => {
    render(<PiotroskiCard companyId="US:AAPL:US" />);
    expect(await screen.findByText("Piotroski F-Score (9-Factor Accounting Test)")).toBeDefined();
    expect(await screen.findByText("Strong")).toBeDefined();
    expect(await screen.findByText("Positive Return on Assets")).toBeDefined();
  });

  it("renders DuPontCard with 3-stage factors and primary driver", async () => {
    render(<DuPontCard companyId="US:AAPL:US" />);
    expect(await screen.findByText("DuPont ROE Decomposition")).toBeDefined();
    expect(await screen.findByText("Operational Margin Expansion")).toBeDefined();
    expect((await screen.findAllByText("Net Profit Margin")).length).toBeGreaterThanOrEqual(1);
    expect((await screen.findAllByText("Asset Turnover")).length).toBeGreaterThanOrEqual(1);
  });


  it("renders PeerMatrixCard with same-currency cohort and percentiles", async () => {
    render(<PeerMatrixCard companyId="US:AAPL:US" />);
    expect(await screen.findByText("Sector Peer Percentile Matrix")).toBeDefined();
    expect(await screen.findByText("Same-Currency Cohort")).toBeDefined();
    expect(await screen.findByText("P/E Ratio")).toBeDefined();
    expect(await screen.findByText("ROIC")).toBeDefined();
  });

  it("renders CommandPalette without crashing", () => {
    render(
      <BrowserRouter>
        <CommandPalette />
      </BrowserRouter>
    );
    expect(document.body).toBeDefined();
  });
});
