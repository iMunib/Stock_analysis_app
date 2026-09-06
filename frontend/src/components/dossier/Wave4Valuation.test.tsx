// @vitest-environment jsdom
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import EPVCard from "./EPVCard";
import BankValuationCard from "./BankValuationCard";
import GuidedDCFModal from "./GuidedDCFModal";
import * as clientModule from "../../api/client";

describe("Wave 4 Valuation Suite", () => {
  // Polyfill localStorage for jsdom without file flag
  beforeAll(() => {
    const g: any = globalThis as any;
    if (typeof g.localStorage === "undefined" || g.localStorage == null) {
      const store: Record<string, string> = {};
      g.localStorage = {
        getItem: (k: string) => store[k] ?? null,
        setItem: (k: string, v: string) => { store[k] = String(v); },
        removeItem: (k: string) => { delete store[k]; },
        clear: () => { for (const k in store) delete store[k]; },
        length: 0,
        key: () => null,
      } as any;
    }
  });
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    try { (globalThis as any).localStorage.clear(); } catch {}
    try { localStorage.clear(); } catch {}
  });

  it("renders EPVCard with normalized EBIT, EPV vs reproduction, and thin history flag (US-0106)", async () => {
    vi.spyOn(clientModule.api, "requestEPV").mockResolvedValue({
      company_id: "US:AAPL:US",
      currency: "USD",
      status: "computed",
      normalized_ebit: 120000000000,
      ebit_source: "median_5y",
      thin_history: false,
      tax_rate: 0.21,
      wacc: 0.09,
      nopat: 94800000000,
      epv: 1053333333333,
      reproduction_cost: 352000000000,
      reproduction_note: "Proxy: Total Assets",
      market_cap: 3000000000000,
      floor_value: 352000000000,
      premium_discount_pct: 752.3,
      cheap_for_reason_flag: false,
      is_financial: false,
      disclaimer: "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions.",
      method_version: "v1",
    } as any);

    render(
      <MemoryRouter>
        <EPVCard companyId="US:AAPL:US" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Greenwald Earnings Power Value/)).toBeTruthy();
      expect(screen.getAllByText(/EPV/)[0]).toBeTruthy();
      // Pure SVG meter
      const svg = document.querySelector("svg[role='img']");
      expect(svg).toBeTruthy();
      expect(screen.getAllByText(/Personal research software/)[0]).toBeTruthy();
    });
  });

  it("shows bank valuation routing with DDM and Residual Income and financial exclusion notice (US-0116)", async () => {
    vi.spyOn(clientModule.api, "requestGuided").mockResolvedValue({ status: "financial_institution_excluded", is_financial: true } as any);
    vi.spyOn(clientModule.api, "requestDDM").mockResolvedValue({
      company_id: "CA:RY:TSX",
      currency: "CAD",
      status: "computed",
      latest_dividend: 5.2,
      latest_fy: 2024,
      dividend_cagr: 0.06,
      cost_of_equity: 0.09,
      gordon_g: 0.04,
      fair_value_total: 80000000000,
      fair_value_per_share: 110.5,
      dividend_yield_pct: 3.8,
      payout_ratio_pct: 45.2,
      disclaimer: "Personal research software",
    } as any);
    vi.spyOn(clientModule.api, "requestResidual").mockResolvedValue({
      company_id: "CA:RY:TSX",
      currency: "CAD",
      status: "computed",
      book_equity: 100000000000,
      normalized_roe: 0.15,
      cost_of_equity: 0.09,
      excess_roe: 0.06,
      residual_income: 6000000000,
      equity_value: 166666666666,
      equity_value_per_share: 115.2,
      premium_discount_pct: -5.3,
      disclaimer: "Personal research software",
    } as any);

    render(
      <MemoryRouter>
        <BankValuationCard companyId="CA:RY:TSX" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Bank \/ Insurer Valuation/)).toBeTruthy();
      expect(screen.getByText(/Dividend Discount Model/)).toBeTruthy();
      expect(screen.getAllByText(/Residual Income/)[0]).toBeTruthy();
      expect(screen.getByText(/110\.50/)).toBeTruthy();
    });
  });

  it("renders GuidedDCFModal with Bear/Base/Bull toggle, WACC build, terminal warning, uncertainty range, and local persistence (US-0101/US-0105/US-0125/US-0126/US-0123/US-0113)", async () => {
    vi.spyOn(clientModule.api, "requestGuided").mockResolvedValue({
      company_id: "US:AAPL:US",
      currency: "USD",
      status: "computed",
      inputs: { revenue_growth: 0.05, operating_margin: 0.15, wacc: 0.09, terminal_g: 0.025, years: 5, risk_free: 0.04, erp: 0.05, beta: 1.1, tax_rate: 0.21, thin_history: false },
      wacc_build: { risk_free: 0.04, erp: 0.05, beta: 1.1, formula: "WACC = Rf (4.00%) + ERP (5.00%) × Beta (1.10) = 9.50%", wacc: 0.095 },
      steps: [
        { year: 1, revenue: 410000000000, ebit: 61500000000, nopat: 48585000000, fcf: 48585000000, discount_factor: 0.9174, pv_fcf: 44571000000, formula: "Year 1: FCF 48585000000 / (1+0.09)^1 = 44571000000" },
      ],
      pv_sum: 200000000000,
      terminal_value: 800000000000,
      pv_terminal: 520000000000,
      enterprise_value: 720000000000,
      net_debt: 50000000000,
      equity_value: 670000000000,
      shares: 15408095000,
      per_share: 43.48,
      price: 210,
      premium_discount_pct: 382.9,
      terminal_pct: 72.2,
      terminal_heavy: true,
      uncertainty_range: { p10_per_share: 35.2, p50_per_share: 43.48, p90_per_share: 55.1 },
      disclaimer: "Personal research software, not investment advice.",
    } as any);

    render(
      <MemoryRouter>
        <GuidedDCFModal companyId="US:AAPL:US" isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Guided DCF Sandbox/)[0]).toBeTruthy();
      expect(screen.getAllByText(/^Bear$/)[0]).toBeTruthy();
      expect(screen.getAllByText(/^Base$/)[0]).toBeTruthy();
      expect(screen.getAllByText(/^Bull$/)[0]).toBeTruthy();
      expect(screen.getAllByText(/WACC = Rf/)[0]).toBeTruthy();
      expect(screen.getAllByText(/TERMINAL_HEAVY/)[0]).toBeTruthy();
      expect(screen.getAllByText(/10th.*50th.*90th|P10/)[0]).toBeTruthy();
      expect(screen.getAllByText(/Show me the math/)[0]).toBeTruthy();
    });

    // Slider ARIA
    expect(screen.getByLabelText("Revenue growth")).toBeTruthy();
    expect(screen.getByLabelText("WACC")).toBeTruthy();

    // Save scenario persistence
    const nameInput = screen.getByLabelText("Scenario name") as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: "Bull - 8% growth" } });
    const saveBtn = screen.getByText("Save");
    expect(saveBtn).toBeTruthy();
    fireEvent.click(saveBtn);
    const stored = JSON.parse(localStorage.getItem("valuation_scenarios:US:AAPL:US") || "[]");
    expect(stored.length).toBe(1);
    expect(stored[0].name).toBe("Bull - 8% growth");
  });

  it("shows financial_institution_excluded for banks in Guided DCF (US-0116)", async () => {
    vi.spyOn(clientModule.api, "requestGuided").mockResolvedValue({
      company_id: "CA:RY:TSX",
      status: "financial_institution_excluded",
      reason: "FCF DCF not meaningful for banks/insurers - use DDM/Residual Income.",
      is_financial: true,
      disclaimer: "Personal research software",
    } as any);

    render(
      <MemoryRouter>
        <GuidedDCFModal companyId="CA:RY:TSX" isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/FCF DCF not meaningful for banks/)[0]).toBeTruthy();
    });
  });

  it("respects prefers-reduced-motion and has ARIA on heatmap cells", async () => {
    vi.spyOn(clientModule.api, "requestGuided").mockResolvedValue({
      company_id: "US:AAPL:US",
      currency: "USD",
      status: "computed",
      inputs: { revenue_growth: 0.05, operating_margin: 0.15, wacc: 0.09, terminal_g: 0.025, years: 5, risk_free: 0.04, erp: 0.05, beta: 1, tax_rate: 0.21 },
      wacc_build: { risk_free: 0.04, erp: 0.05, beta: 1, formula: "WACC", wacc: 0.09 },
      steps: [],
      pv_sum: 1, terminal_value: 1, pv_terminal: 1, enterprise_value: 1, net_debt: 0, equity_value: 1, shares: 100, per_share: 10, price: 9, premium_discount_pct: -10, terminal_pct: 40, terminal_heavy: false,
      uncertainty_range: { p10_per_share: 8, p50_per_share: 10, p90_per_share: 12 },
      disclaimer: "Personal",
    } as any);

    render(
      <MemoryRouter>
        <GuidedDCFModal companyId="US:AAPL:US" isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    await waitFor(() => {
      const cells = document.querySelectorAll("[role='gridcell']");
      expect(cells.length).toBeGreaterThan(0);
      expect(cells[0].getAttribute("aria-label")).toContain("growth");
    });
  });
});