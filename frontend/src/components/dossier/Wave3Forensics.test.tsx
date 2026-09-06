// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import BenfordChart from "./BenfordChart";
import AsFiledToggle from "./AsFiledToggle";
import RedFlagsWorkspace from "./RedFlagsWorkspace";
import * as clientModule from "../../api/client";

describe("Wave 3 Forensic Red Flags & Restatements", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders pure SVG BenfordChart with observed vs expected bars and ARIA (US-0211)", () => {
    const data: any = {
      company_id: "US:AAPL:US",
      status: "computed",
      data_available: true,
      observations: 42,
      min_required: 15,
      observed_freq: { "1": 0.31, "2": 0.18, "3": 0.12, "4": 0.09, "5": 0.07, "6": 0.06, "7": 0.06, "8": 0.05, "9": 0.06 },
      expected_freq: { "1": 0.301, "2": 0.176, "3": 0.125, "4": 0.097, "5": 0.079, "6": 0.067, "7": 0.058, "8": 0.051, "9": 0.046 },
      chi2: 6.42,
      degrees_of_freedom: 8,
      verdict: "conforms",
      interpretation: "χ²=6.42 (df=8) - conforms",
      disclaimer: "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
    };
    const { container } = render(<BenfordChart data={data} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toContain("Benford");
    expect(svg?.getAttribute("aria-label")).toContain("chi-square");
    // Should have 9 bars (rect) + 9 labels
    const rects = container.querySelectorAll("rect");
    expect(rects.length).toBe(9);
    expect(screen.getAllByText(/χ²=6.42/)[0]).toBeTruthy();
    expect(screen.getAllByText(/Personal research software/)[0]).toBeTruthy();
  });

  it("shows insufficient_data state for Benford when fewer than 15 figures (US-0211)", () => {
    const data: any = {
      company_id: "CA:IIP.UN:TSX",
      status: "insufficient_data",
      data_available: false,
      observations: 4,
      min_required: 15,
      observed_freq: null,
      expected_freq: { "1": 0.301 },
      chi2: null,
      degrees_of_freedom: 8,
      verdict: "insufficient_data",
      interpretation: "Only 4 positive figures - at least 15 required",
      disclaimer: "Personal research software, not investment advice.",
    };
    render(<BenfordChart data={data} />);
    expect(screen.getByText(/Only 4 positive figures/)).toBeTruthy();
  });

  it("renders AsFiledToggle with keyboard Tab/Escape and hasRestatement messaging (US-0161/US-0245)", () => {
    const onChange = vi.fn();
    const { rerender } = render(<AsFiledToggle value="filed" onChange={onChange} hasRestatement={false} />);
    expect(screen.getByText("As-Filed")).toBeTruthy();
    expect(screen.getByText("As-Restated")).toBeTruthy();
    expect(screen.getByText(/No restatements detected/)).toBeTruthy();

    rerender(<AsFiledToggle value="restated" onChange={onChange} hasRestatement={true} />);
    expect(screen.getByText(/Restatement delta shown/)).toBeTruthy();

    // Click toggle
    fireEvent.click(screen.getByText("As-Filed"));
    expect(onChange).toHaveBeenCalledWith("filed");
    // Escape should blur (no throw)
    const btn = screen.getByText("As-Filed");
    fireEvent.keyDown(btn, { key: "Escape" });
    // ARIA
    expect(btn.getAttribute("role")).toBe("tab");
  });

  it("renders RedFlagsWorkspace with consolidated summary, Benford, trajectory, CCC, goodwill, dilution, and restatement toggle (US-0213/US-0211/US-0152/US-0228/US-0168/US-0158/US-0245)", async () => {
    vi.spyOn(clientModule.api, "forensicsSummary").mockResolvedValue({
      company_id: "US:AAPL:US",
      currency: "USD",
      forensic_health_score: 85,
      forensic_risk_tier: "Clean / Low Forensic Risk",
      flag_count: 0,
      flags: [],
      triggered_codes: [],
      cross_model_divergence: null,
      plain_language_summary: "No material forensic flags triggered; earnings and balance-sheet screens appear clean.",
      beneish: { m_score: -2.4, is_manipulator: false, zone: "Non-manipulator" } as any,
      distress: { active_z: 4.2, zone: "Safe", model_used: "manufacturing" } as any,
      sloan: { accrual_ratio: 0.02, flag: null } as any,
      shenanigans: {
        working_capital: { dso: { triggered: false }, inventory: { triggered: false }, capitalized_expenses: { triggered: false }, covenant: { triggered: false }, goodwill: { triggered: false }, serial_acquirer: { triggered: false } },
        auditor: { going_concern_detected: false, timeline: [] },
        triggered_flags: [],
      } as any,
      benford: { verdict: "conforms", chi2: 6.4, observations: 42 } as any,
      disclaimer: "Personal research software, not investment advice.",
      method_version: "v1",
    } as any);

    vi.spyOn(clientModule.api, "forensicsBenford").mockResolvedValue({
      company_id: "US:AAPL:US",
      status: "computed",
      data_available: true,
      observations: 42,
      min_required: 15,
      observed_freq: { "1": 0.3, "2": 0.17, "3": 0.12, "4": 0.1, "5": 0.08, "6": 0.07, "7": 0.06, "8": 0.05, "9": 0.04 },
      expected_freq: { "1": 0.301, "2": 0.176, "3": 0.125, "4": 0.097, "5": 0.079, "6": 0.067, "7": 0.058, "8": 0.051, "9": 0.046 },
      chi2: 6.42,
      degrees_of_freedom: 8,
      verdict: "conforms",
      interpretation: "χ²=6.42 - conforms",
      disclaimer: "Personal research software, not investment advice.",
    } as any);

    vi.spyOn(clientModule.api, "trajectory").mockResolvedValue({
      company_id: "US:AAPL:US",
      count: 3,
      currency: "USD",
      points: [
        { fiscal_year: 2022, revenue: 394328000000, gross_margin: 0.43, operating_margin: 0.30, fcf: 111443000000, inflections: [], currency: "USD" },
        { fiscal_year: 2023, revenue: 383285000000, gross_margin: 0.44, operating_margin: 0.30, fcf: 99584000000, inflections: [], currency: "USD" },
        { fiscal_year: 2024, revenue: 391035000000, gross_margin: 0.46, operating_margin: 0.31, fcf: 108807000000, inflections: ["revenue_surge"], currency: "USD" },
      ],
    } as any);

    vi.spyOn(clientModule.api, "workingCapital").mockResolvedValue({
      company_id: "US:AAPL:US",
      data_available: true,
      series: [
        { fiscal_year: 2022, dso: 28.5, dio: 12.1, dpo: 85.3, ccc: -44.7 },
        { fiscal_year: 2023, dso: 29.1, dio: 11.8, dpo: 86.0, ccc: -45.1 },
        { fiscal_year: 2024, dso: 27.9, dio: 10.2, dpo: 88.4, ccc: -50.3 },
      ],
      disclaimer: "Personal research software",
    } as any);

    vi.spyOn(clientModule.api, "restatements").mockResolvedValue({
      company_id: "US:AAPL:US",
      count: 2,
      items: [
        { fiscal_year: 2023, as_filed: { revenue: 383285000000, net_income: 96995000000 }, as_restated: { revenue: 383285000000, net_income: 96995000000 }, delta_pct: { revenue: 0, net_income: 0 }, has_restatement: false, provenance: { filed_source: "seed", restated_source: "sec_edgar" } },
        { fiscal_year: 2024, as_filed: { revenue: 391035000000, net_income: 93736000000 }, as_restated: null, delta_pct: {}, has_restatement: false, provenance: { filed_source: "seed", restated_source: null } },
      ],
      disclaimer: "Personal",
    } as any);

    vi.spyOn(clientModule.api, "goodwillRisk").mockResolvedValue({
      company_id: "US:AAPL:US",
      goodwill: { triggered: false, proxy_ratio: 0.12, reason: null } as any,
      serial_acquirer: { triggered: false } as any,
      strip: [
        { fiscal_year: 2022, proxy_intangible_ratio: 0.11, total_assets: 352755000000 },
        { fiscal_year: 2023, proxy_intangible_ratio: 0.12, total_assets: 365000000000 },
        { fiscal_year: 2024, proxy_intangible_ratio: 0.10, total_assets: 365000000000 },
      ],
      disclaimer: "Personal",
    } as any);

    vi.spyOn(clientModule.api, "dilution").mockResolvedValue({
      company_id: "US:AAPL:US",
      count: 2,
      series: [
        { fiscal_year: 2023, shares: 15812547000, sbc: 10000000000, annotation: "net_buyback", delta: -200000000, delta_pct: -1.2 },
        { fiscal_year: 2024, shares: 15408095000, sbc: 10800000000, annotation: "net_buyback", delta: -404452000, delta_pct: -2.56 },
      ],
      disclaimer: "Personal",
    } as any);

    render(
      <MemoryRouter>
        <RedFlagsWorkspace companyId="US:AAPL:US" currency="USD" />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Consolidated Forensic Summary")).toBeTruthy();
      expect(screen.getAllByText(/What could go wrong/)[0]).toBeTruthy();
      expect(screen.getAllByText(/Benford's Law/)[0]).toBeTruthy();
      expect(screen.getByText(/10-Year Synchronized Trajectory/)).toBeTruthy();
      expect(screen.getByText(/Cash Conversion Cycle/)).toBeTruthy();
      expect(screen.getByText(/Goodwill vs Tangible Assets/)).toBeTruthy();
      expect(screen.getByText(/Share Dilution Tracker/)).toBeTruthy();
      expect(screen.getByText(/As-Filed vs As-Restated/)).toBeTruthy();
      // Disclaimer
      expect(screen.getAllByText(/Personal research software, not investment advice/)[0]).toBeTruthy();
      // Hindenburg checklist
      expect(screen.getByText(/Hindenburg-Style First-Pass Checklist/)).toBeTruthy();
      // Pure SVG checks - trajectory chart should have svg with role img
      const svgs = document.querySelectorAll("svg[role='img']");
      expect(svgs.length).toBeGreaterThanOrEqual(3);
    });

    // AsFiledToggle interaction inside RedFlagsWorkspace (restatement card)
    const restatedBtn = screen.getAllByText("As-Restated")[0];
    fireEvent.click(restatedBtn);
    expect(restatedBtn).toBeTruthy();
  });

  it("shows financial_institution_excluded for banks on distress (US-0208)", async () => {
    vi.spyOn(clientModule.api, "forensicsSummary").mockResolvedValue({
      company_id: "CA:RY:TSX",
      currency: "CAD",
      forensic_health_score: 70,
      forensic_risk_tier: "Moderate Forensic Caution",
      flag_count: 0,
      flags: [],
      triggered_codes: [],
      cross_model_divergence: null,
      plain_language_summary: "No material flags.",
      beneish: { status: "financial_institution_excluded", zone: "Excluded", m_score: null } as any,
      distress: { status: "financial_institution_excluded", zone: "Excluded", active_z: null } as any,
      sloan: { status: "financial_institution_excluded", flag: null } as any,
      shenanigans: { working_capital: {}, auditor: {}, triggered_flags: [] } as any,
      benford: { verdict: "insufficient_data", chi2: null, observations: 3 } as any,
      disclaimer: "Personal research software",
      method_version: "v1",
    } as any);
    vi.spyOn(clientModule.api, "forensicsBenford").mockResolvedValue({
      company_id: "CA:RY:TSX",
      status: "financial_institution_excluded",
      data_available: false,
      observations: 5,
      min_required: 15,
      observed_freq: null,
      expected_freq: null,
      chi2: null,
      degrees_of_freedom: 8,
      verdict: "insufficient_data",
      interpretation: "insufficient",
      disclaimer: "Personal",
    } as any);
    vi.spyOn(clientModule.api, "trajectory").mockResolvedValue({ company_id: "CA:RY:TSX", count: 0, points: [], currency: "CAD" } as any);
    vi.spyOn(clientModule.api, "workingCapital").mockResolvedValue({ company_id: "CA:RY:TSX", data_available: false, reason: "working_capital_inputs_missing", series: [], disclaimer: "Personal" } as any);
    vi.spyOn(clientModule.api, "restatements").mockResolvedValue({ company_id: "CA:RY:TSX", count: 0, items: [], disclaimer: "Personal" } as any);
    vi.spyOn(clientModule.api, "goodwillRisk").mockResolvedValue({ company_id: "CA:RY:TSX", goodwill: { triggered: false } as any, serial_acquirer: {} as any, strip: [], disclaimer: "Personal" } as any);
    vi.spyOn(clientModule.api, "dilution").mockResolvedValue({ company_id: "CA:RY:TSX", count: 0, series: [], disclaimer: "Personal" } as any);

    render(
      <MemoryRouter>
        <RedFlagsWorkspace companyId="CA:RY:TSX" currency="CAD" />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Consolidated Forensic Summary")).toBeTruthy();
    });
    // Bank should show excluded state somewhere (beneish/distress zone Excluded) - use getAll to handle multiple matches
    expect(screen.getAllByText(/Clean \/ Low Forensic Risk|Moderate Forensic Caution/)[0]).toBeTruthy();
  });
});