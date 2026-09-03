// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import CommonSizeTable from "./CommonSizeTable";
import CapitalReturnCard from "./CapitalReturnCard";
import type { CommonSizeOut, ShareholderYield } from "../../api/types";

describe("Financial Statement Analytical Components", () => {
  afterEach(cleanup);

  describe("CommonSizeTable", () => {
    const mockCommonSize: CommonSizeOut = {
      company_id: "US:AAPL:US",
      currency: "USD",
      years_delivered: 3,
      income_statement_common_size: [
        {
          fiscal_year: 2024,
          revenue: { raw: 391035000000, pct: 100.0 },
          cost_of_goods_sold: { raw: 210352000000, pct: 53.8 },
          gross_profit: { raw: 180683000000, pct: 46.2 },
          operating_expenses: { raw: 57468000000, pct: 14.7 },
          operating_income: { raw: 123215000000, pct: 31.5 },
          net_income: { raw: 93736000000, pct: 24.0 },
        },
      ],
      balance_sheet_common_size: [
        {
          fiscal_year: 2024,
          total_assets: { raw: 364980000000, pct: 100.0 },
          cash_and_equivalents: { raw: 29943000000, pct: 8.2 },
          current_assets: { raw: 152763000000, pct: 41.9 },
          total_debt: { raw: 106629000000, pct: 29.2 },
          total_liabilities: { raw: 308030000000, pct: 84.4 },
          stockholders_equity: { raw: 56950000000, pct: 15.6 },
        },
      ],
      margin_drift_flags: [
        {
          code: "COST_CREEP",
          severity: "warning",
          metric: "opex",
          from_year: 2022,
          to_year: 2024,
          change_bps: 120,
          message: "SG&A / Operating expense ratio expanded by 1.2% over 3 years.",
        },
      ],
    };

    it("renders normalized income statement and balance sheet with toggle", () => {
      render(<CommonSizeTable data={mockCommonSize} currency="USD" />);
      expect(screen.getByRole("heading", { name: /Common-Size Statements/i })).toBeDefined();
      expect(screen.getByText(/% of Total Revenue/i)).toBeDefined();
      expect(screen.getByText("Gross Profit")).toBeDefined();
      expect(screen.getByText("46.2%")).toBeDefined();
      expect(screen.getByText(/SG&A \/ Operating expense ratio expanded/i)).toBeDefined();
    });

    it("handles null or empty data gracefully", () => {
      render(<CommonSizeTable data={null} currency="USD" />);
      expect(screen.getByText(/Multi-year common-size financial statements not available/i)).toBeDefined();
    });
  });

  describe("CapitalReturnCard", () => {
    const mockYield: ShareholderYield = {
      company_id: "US:AAPL:US",
      currency: "USD",
      share_count_history: [
        { fiscal_year: 2022, diluted_shares: 16100000000 },
        { fiscal_year: 2023, diluted_shares: 15700000000 },
        { fiscal_year: 2024, diluted_shares: 15300000000 },
      ],
      share_count_cagr_3y_pct: -2.51,
      share_count_delta_1y_pct: -2.55,
      dividend_yield_pct: 0.52,
      net_buyback_yield_pct: 3.25,
      total_shareholder_yield_pct: 3.77,
      flags: ["ACCELERATED_BUYBACKS"],
    };

    it("renders diluted share chart, CAGR, and total shareholder yield", () => {
      render(<CapitalReturnCard data={mockYield} />);
      expect(screen.getByText(/Capital Return & Share Dilution/i)).toBeDefined();
      expect(screen.getByText("3.77%")).toBeDefined();
      expect(screen.getByText("-2.51%")).toBeDefined();
      expect(screen.getByText(/ACCELERATED BUYBACKS/i)).toBeDefined();
      expect(screen.getByRole("img", { name: /Diluted shares outstanding trend/i })).toBeDefined();
    });

    it("handles null shareholder yield data gracefully", () => {
      render(<CapitalReturnCard data={null} />);
      expect(screen.getByText(/Capital return and share count history unavailable/i)).toBeDefined();
    });
  });
});
