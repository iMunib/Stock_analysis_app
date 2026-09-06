// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CompositeGauge } from "./CompositeGauge";
import { MiniPillarBars } from "./MiniPillarBars";
import { PillarRadar } from "./PillarRadar";
import { Sparkline } from "./Sparkline";
import { PercentileMatrix } from "./PercentileMatrix";
import { AltmanZGauge } from "./AltmanZGauge";

describe("SVG Visualization Primitives", () => {
  afterEach(cleanup);

  describe("CompositeGauge", () => {
    it("renders gauge with value and accessible label", () => {
      render(<CompositeGauge value={7.8} signal="strong_candidate" size="md" />);
      expect(screen.getByText("7.8")).toBeDefined();
      expect(screen.getByRole("img", { name: /Composite score gauge/i })).toBeDefined();
    });

    it("handles null value gracefully", () => {
      render(<CompositeGauge value={null} size="sm" />);
      expect(screen.getByText("0.00")).toBeDefined();
    });
  });

  describe("PillarRadar", () => {
    it("renders polygon with 4 scored axes and accessible label", () => {
      const { container } = render(
        <PillarRadar quality={8.5} value={6.2} growth={7.1} risk={5.0} size={200} />
      );
      expect(screen.getByRole("img", { name: /Pillar radar chart/i })).toBeDefined();
      const polygon = container.querySelector("polygon");
      expect(polygon).not.toBeNull();
      expect(polygon?.getAttribute("points")).toBeTruthy();
    });

    it("renders hollow dot for null pillar", () => {
      const { container } = render(
        <PillarRadar quality={8.5} value={6.2} growth={null} risk={5.0} size={200} />
      );
      const circles = container.querySelectorAll("circle");
      expect(circles.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe("Sparkline", () => {
    it("renders pure SVG sparkline path and last-point dot", () => {
      const { container } = render(
        <Sparkline data={[10, 20, 15, 30, 25]} width={60} height={20} />
      );
      expect(screen.getByRole("img", { name: /Historical trend sparkline/i })).toBeDefined();
      const path = container.querySelector("path");
      expect(path).not.toBeNull();
      const circle = container.querySelector("circle");
      expect(circle).not.toBeNull();
    });

    it("handles empty or insufficient data without crashing", () => {
      render(<Sparkline data={[]} />);
      expect(screen.getByText("Requires 3+ fiscal years")).toBeDefined();
    });
  });

  describe("MiniPillarBars", () => {
    it("renders 4 pillar bars (Q, V, G, R)", () => {
      render(<MiniPillarBars quality={7} value={8} growth={null} risk={6} />);
      expect(screen.getByText("Q")).toBeDefined();
      expect(screen.getByText("V")).toBeDefined();
      expect(screen.getByText("G")).toBeDefined();
      expect(screen.getByText("R")).toBeDefined();
      expect(screen.getByRole("img", { name: /Pillars: Q 7\.0, V 8\.0, G 0\.00, R 6\.0/i })).toBeDefined();
    });
  });

  describe("PercentileMatrix", () => {
    it("renders percentile bars and accessible table", () => {
      const mockPercentiles = {
        pe_ratio: 85.0,
        ev_to_ebitda: 72.5,
        pb_ratio: 60.0,
        roe: 92.0,
        roic_or_rnoa: 88.0,
        fcf_margin: 78.0,
        net_debt_to_ebitda: 35.0,
        total_shareholder_yield: 65.0,
      };
      render(<PercentileMatrix percentiles={mockPercentiles} sectorName="Technology" currency="USD" />);
      expect(screen.getByText(/Sector Percentile Matrix/i)).toBeDefined();
      expect(screen.getAllByText(/P\/E Multiple/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/85\.0th pct/i)).toBeDefined();
    });

    it("handles null percentiles gracefully", () => {
      render(<PercentileMatrix percentiles={null} />);
      expect(screen.getByText(/Sector percentile ranks not materialized/i)).toBeDefined();
    });
  });

  describe("AltmanZGauge", () => {
    it("renders distress gauge with needle and zones", () => {
      const mockDistress = {
        model: "service_z_double_prime" as const,
        active_z: 4.82,
        zone: "Safe" as const,
        is_bank: false,
        bank_warning: null,
        factors: { x1_wc_ta: 0.2, x2_re_ta: 0.4, x3_ebit_ta: 0.15, x4_bve_tl: 1.8 },
        thresholds: { distress_cutoff: 1.1, safe_cutoff: 2.6 },
        interpretation: "Negligible probability of financial distress over a 2-year horizon.",
      };
      render(<AltmanZGauge distress={mockDistress as any} />);
      expect(screen.getByText(/Altman Solvency & Distress/i)).toBeDefined();
      expect(screen.getAllByText("4.82").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/Safe/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByRole("img", { name: /Altman Z-Score Meter/i })).toBeDefined();
    });

    it("displays bank exclusion badge when company is a bank", () => {
      const mockBank = {
        model: "service_z_double_prime" as const,
        active_z: null,
        zone: "Excluded" as const,
        status: "financial_institution_excluded",
        is_bank: true,
        bank_warning: "Financial institution excluded.",
        factors: {},
        thresholds: { distress_cutoff: 1.1, safe_cutoff: 2.6 },
        interpretation: "Banks and insurers are excluded from Altman Z modeling.",
      };
      render(<AltmanZGauge distress={mockBank as any} />);
      expect(screen.getByText(/Bank \/ Insurer Excluded/i)).toBeDefined();
    });
  });

  describe("CashFlowBridge", () => {
    it("renders waterfall bridge with positive and negative steps", async () => {
      const { CashFlowBridge } = await import("./CashFlowBridge");
      render(
        <CashFlowBridge
          inputs={{
            net_income: -5846000000,
            cfo: 4462000000,
            capex: 801000000,
            fcf: 3661000000,
            currency: "USD",
          }}
        />
      );
      expect(screen.getByText(/Ittelson Bridge/i)).toBeDefined();
      expect(screen.getByText(/Currency: USD/i)).toBeDefined();
      expect(screen.getByText(/Free Cash Flow/i)).toBeDefined();
      expect(screen.getByText(/Show Waterfall Statement Table/i)).toBeDefined();
    });

    it("displays missing data message when net income or CFO is missing", async () => {
      const { CashFlowBridge } = await import("./CashFlowBridge");
      render(
        <CashFlowBridge
          inputs={{
            net_income: null,
            cfo: null,
            capex: null,
            fcf: null,
          }}
        />
      );
      expect(screen.getByText(/needs net income and operating cash flow/i)).toBeDefined();
    });
  });

  describe("TerminalMarketTape", () => {
    it("renders market tape with benchmarks and pulse status", async () => {
      const { TerminalMarketTape } = await import("./TerminalMarketTape");
      render(<TerminalMarketTape />);
      expect(screen.getByLabelText(/Global market benchmarks ticker tape/i)).toBeDefined();
      expect(screen.getAllByText("SPX").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("TX60").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("DESK FEED")).toBeDefined();
    });
  });

  describe("IsometricFinanceGraphic", () => {
    it("renders 3D decision architecture SVG graphic", async () => {
      const { IsometricFinanceGraphic } = await import("./IsometricFinanceGraphic");
      render(
        <IsometricFinanceGraphic
          ticker="AAPL"
          moat="Wide Moat · 58% ROIC"
          solvency="Pristine · Altman Z 4.8"
          hurdle="FCF Hurdle 11.2% CAGR"
        />
      );
      expect(screen.getByRole("img", { name: /3D Isometric Decision Architecture/i })).toBeDefined();
      expect(screen.getByText("SOLVENCY FLOOR")).toBeDefined();
      expect(screen.getByText("OPERATING MOAT")).toBeDefined();
      expect(screen.getByText(/AAPL/)).toBeDefined();
    });
  });

  describe("HalalComplianceCard", () => {
    it("renders failed tests with object ratio without [object Object]", async () => {
      const { HalalComplianceCard } = await import("../dossier/HalalComplianceCard");
      const mockHalal = {
        status: "not_halal",
        method: "AAOIFI-21",
        failed_tests: [
          {
            test: "debt_to_mcap",
            ratio: { ratio: 0.385, limit: 0.3, result: "fail" },
          },
          {
            test: "activity_screen",
            basis: { keyword_hit: "brewery", gics_sector: "Consumer Staples" },
          },
        ],
      };
      const { container } = render(<HalalComplianceCard halal={mockHalal as any} />);
      expect(screen.getByText(/Failed Compliance Criteria \(2\)/i)).toBeDefined();
      expect(screen.getByText(/Ratio: 38.5% \(limit 30%\)/i)).toBeDefined();
      expect(screen.getByText(/Hit: "brewery"/i)).toBeDefined();
      expect(container.textContent).not.toContain("[object Object]");
    });
  });
});
