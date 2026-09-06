// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { ScoreBar } from "../bars";
import { TensionCallout } from "./TensionCallout";
import { CoveragePenaltyModal } from "./CoveragePenaltyModal";
import { DecisionBullets } from "./DecisionBullets";
import ThesisNotepad from "./ThesisNotepad";
import AltmanZScoreCard from "./AltmanZScoreCard";
import BeneishMatrix from "./BeneishMatrix";
import { PillarDrilldownModal } from "./PillarDrilldownModal";
import { RatioInspectorModal } from "./RatioInspectorModal";
import type {
  CoveragePenaltyDetails,
  PillarTension,
  BearCaseOut,
  BeneishAnalysis,
  PillarDrilldownOut,
  RatioInspectOut,
} from "../../api/types";

describe("Wave 1 Components Verification", () => {
  describe("ScoreBar Sector Peer Median Overlay (US-0067)", () => {
    it("renders sector peer median marker line and accessibility label", () => {
      const { container } = render(
        <ScoreBar value={7.5} label="Quality" median={6.2} />
      );
      const svg = screen.getByRole("img");
      expect(svg.getAttribute("aria-label")).toContain("Quality: 7.5, Sector Peer Median: 6.2");
      const medianLine = container.querySelector("g.median-marker line");
      expect(medianLine).toBeTruthy();
      expect(medianLine?.getAttribute("x1")).toBe("62");
    });
  });

  describe("TensionCallout (US-0064)", () => {
    it("renders tensions radar with badges and interpretations", () => {
      const tensions: PillarTension[] = [
        {
          tension_id: "quality_vs_value",
          title: "Quality vs Value",
          chip: "Quality Premium",
          summary: "High quality but priced at extreme valuation multiples.",
          pillars_involved: ["Quality", "Value"],
          tone: "warn",
        },
      ];
      render(<TensionCallout tensions={tensions} />);
      expect(screen.getByText(/Pillar Disagreement Radar/i)).toBeTruthy();
      expect(screen.getByText("Quality vs Value")).toBeTruthy();
      expect(screen.getByText("Quality Premium")).toBeTruthy();
      expect(screen.getByText(/High quality but priced at extreme valuation multiples/)).toBeTruthy();
    });
  });

  describe("CoveragePenaltyModal (US-0100)", () => {
    it("renders unadjusted score, deduction, and penalty tiers", () => {
      const details: CoveragePenaltyDetails = {
        unadjusted_weighted_score: 8.0,
        coverage_count: 3,
        multiplier: 0.85,
        deduction: 1.2,
        formula_string: "8.00 × 0.85 multiplier (-1.20 pts deduction)",
        published_score: 6.8,
        penalty_table: [
          { pillars: 4, multiplier: 1.0, label: "100% (No penalty)" },
          { pillars: 3, multiplier: 0.85, label: "85% (15% deduction)" },
          { pillars: 2, multiplier: 0.65, label: "65% (35% deduction)" },
          { pillars: 1, multiplier: 0.4, label: "40% (60% deduction)" },
        ],
      };
      render(
        <CoveragePenaltyModal isOpen={true} onClose={vi.fn()} details={details} />
      );
      expect(screen.getByText("Deterministic Coverage Penalty Breakdown")).toBeTruthy();
      expect(screen.getByText("-1.20 pts")).toBeTruthy();
      expect(screen.getByText("8.00")).toBeTruthy();
      expect(screen.getByText("6.80")).toBeTruthy();
      expect(screen.getByText("85% (15% deduction)")).toBeTruthy();
    });
  });

  describe("DecisionBullets Equal-Billing & Bear Synthesis (US-0705, US-0074)", () => {
    it("renders bull and bear case with equal visual billing and bottom percentiles", () => {
      const bearCase: BearCaseOut = {
        company_id: "US:AAPL:US",
        company_name: "Apple Inc.",
        bear_thesis_narrative: "Vulnerable to hardware replacement cycles and EU regulatory friction.",
        core_vulnerabilities: ["Gross margin compression", "Hardware slowdown"],
        lowest_3_percentiles: [
          { metric_id: "pe", label: "P/E Ratio", percentile: 12, rank_descriptor: "Top Decile Expensive" },
          { metric_id: "growth", label: "Revenue CAGR", percentile: 18, rank_descriptor: "Decelerating" },
        ],
        forensic_flags: [
          {
            model: "Beneish M-Score",
            flag: "DSRI Receivables Growth",
            detail: "DSRI exceeded 1.30",
            false_positive_rate: "14%",
            severity: "medium",
          },
        ],
        pre_mortem_challenge: "Assume catastrophic 50% drawdown...",
        equal_billing_mandate: "Layout requires identical card weight.",
      };

      render(
        <DecisionBullets
          strengths={["Unrivaled ecosystem lock-in", "Massive share repurchase program"]}
          keyRisk="Macro consumer slowdown"
          expectedReturn={11.5}
          indexBaseline={8.0}
          bearCase={bearCase}
        />
      );

      // Verify Equal-Billing Panels exist
      expect(screen.getByTestId("bull-case-panel")).toBeTruthy();
      expect(screen.getByTestId("bear-case-panel")).toBeTruthy();

      // Verify Bull Case Content
      expect(screen.getByText(/Why Buy \(Core Strengths\)/)).toBeTruthy();
      expect(screen.getByText("Unrivaled ecosystem lock-in")).toBeTruthy();

      // Verify Bear Case Content (US-0074)
      expect(screen.getByText(/Case Against This Stock \(Key Vulnerabilities\)/)).toBeTruthy();
      expect(screen.getByText("Vulnerable to hardware replacement cycles and EU regulatory friction.")).toBeTruthy();
      expect(screen.getByText("P/E Ratio")).toBeTruthy();
      expect(screen.getByText("Bottom 12%")).toBeTruthy();
      expect(screen.getByText(/DSRI Receivables Growth/)).toBeTruthy();
    });
  });

  describe("ThesisNotepad Pre-Mortem Prompt (US-0725)", () => {
    it("renders pre-mortem challenge prompt and input area", () => {
      render(<ThesisNotepad companyId="US:TEST:US" />);
      expect(screen.getByTestId("pre-mortem-prompt")).toBeTruthy();
      expect(screen.getByText(/Assume you bought this stock today and over the next 24 months it suffered a catastrophic 50% drawdown/)).toBeTruthy();
      expect(screen.getByPlaceholderText(/Document the exact failure mode here/)).toBeTruthy();
    });
  });

  describe("Forensic Model Date Stamps and False-Positive Rates (US-0905, US-0947)", () => {
    it("Altman Z-Score renders sample window and false positive disclosure when in distress", () => {
      render(
        <AltmanZScoreCard zScore={1.45} zone="Distress" x1={0.1} x2={0.2} x3={0.05} x4={0.8} x5={0.5} />
      );
      expect(screen.getByText(/Altman \(1968\): 1946–1965 Manufacturing sample/)).toBeTruthy();
      expect(screen.getByText(/False-Positive Rate \(~18%\)/)).toBeTruthy();
      expect(screen.getByText(/Model Decay: Altman published 1968/)).toBeTruthy();
    });

    it("Beneish M-Score renders sample window and false positive disclosure when flagged", () => {
      const analysis: BeneishAnalysis = {
        company_id: "US:TEST:US",
        m_score: -1.45,
        is_manipulator: true,
        zone: "Manipulator",
        threshold: -1.78,
        status: "complete",
        interpretation: "High empirical probability of earnings manipulation.",
        variables: { dsri: 1.45, gmi: 1.1, aqi: 1.0, sgi: 1.35, depi: 1.0, sgai: 1.1, lvgi: 1.0, tata: 0.09 },
      };
      render(<BeneishMatrix analysis={analysis} />);
      expect(screen.getByText(/Beneish \(1999\): 1982–1992 Compustat sample/)).toBeTruthy();
      expect(screen.getByText(/False-Positive Rate \(~14%\)/)).toBeTruthy();
      expect(screen.getByText(/FLAGGED: HIGH RISK/)).toBeTruthy();
      expect(screen.getByText(/Model Decay: Beneish published 1999/)).toBeTruthy();
    });
  });

  describe("Modal Keyboard Accessibility & Provenance (Escape & SEDAR+)", () => {
    it("CoveragePenaltyModal dismisses on Escape keydown", () => {
      const onClose = vi.fn();
      const details: CoveragePenaltyDetails = {
        unadjusted_weighted_score: 8.0,
        coverage_count: 3,
        multiplier: 0.85,
        deduction: 1.2,
        formula_string: "8.00 × 0.85",
        published_score: 6.8,
        penalty_table: [],
      };
      render(<CoveragePenaltyModal isOpen={true} onClose={onClose} details={details} />);
      fireEvent.keyDown(window, { key: "Escape" });
      expect(onClose).toHaveBeenCalled();
    });

    it("PillarDrilldownModal dismisses on Escape keydown and renders SEDAR+ link for Canadian companies", () => {
      const onClose = vi.fn();
      const drilldown: PillarDrilldownOut = {
        company_id: "CA:RY:TSX",
        name: "Royal Bank of Canada",
        currency: "CAD",
        sector_peer_medians: { quality: 6.5, value: 5.0, growth: 5.5, risk: 7.0 },
        tensions: [],
        coverage_penalty: {
          unadjusted_weighted_score: 8.0,
          coverage_count: 4,
          multiplier: 1.0,
          deduction: 0.0,
          formula_string: "8.00 × 1.00",
          published_score: 8.0,
          penalty_table: [],
        },
        method_version: "v1",
        disclaimer: "Not investment advice",
        pillars: {
          quality: {
            score: 8.0,
            formula: "Quality = 0.4*ROE + 0.3*ROA",
            interpretation: "Strong Canadian bank balance sheet",
            missing_faq: "Bank capital metrics reported under OSFI Basel III guidelines.",
            sector_median: 6.5,
            sub_metrics: [
              {
                metric_id: "roe",
                name: "Return on Equity (ROE)",
                raw_value: 0.15,
                formatted_value: "15.0%",
                weight: 0.5,
                normalized_score: 7.5,
                formula_definition: "Net Income / Total Equity",
                line_items: [
                  {
                    name: "Net Income",
                    raw_value: 15000000000,
                    formatted: "$15.0B",
                    currency: "CAD",
                    period: "FY2024",
                    sec_edgar_url: "https://www.sedarplus.ca/csa-party/records/document.html",
                    provenance: "SEDAR+ Annual Statement",
                  },
                ],
              },
            ],
          },
          value: { score: 6.0, formula: "", interpretation: "", missing_faq: "", sector_median: 5.0, sub_metrics: [] },
          growth: { score: 7.0, formula: "", interpretation: "", missing_faq: "", sector_median: 5.5, sub_metrics: [] },
          risk: { score: 8.0, formula: "", interpretation: "", missing_faq: "", sector_median: 7.0, sub_metrics: [] },
        },
      };

      render(
        <PillarDrilldownModal
          isOpen={true}
          onClose={onClose}
          pillarKey="quality"
          drilldown={drilldown}
          companyName="Royal Bank of Canada"
          currency="CAD"
        />
      );

      expect(screen.getByText(/Quality Pillar Methodology/)).toBeTruthy();

      // Click metric to expand line items
      fireEvent.click(screen.getByText("Return on Equity (ROE)"));

      // Verify SEDAR+ link is present
      const link = screen.getByTitle("Open filing in SEDAR+");
      expect(link).toBeTruthy();
      expect(link.textContent).toContain("SEDAR+ ↗");

      // Verify Escape dismissal
      fireEvent.keyDown(window, { key: "Escape" });
      expect(onClose).toHaveBeenCalled();
    });

    it("RatioInspectorModal dismisses on Escape keydown and shows SEDAR+ for Canadian filings", () => {
      const onClose = vi.fn();
      const initialData: RatioInspectOut = {
        company_id: "CA:RY:TSX",
        ratio_id: "pb",
        label: "Price-to-Book Ratio (P/B)",
        formula_string: "P/B = Market Capitalization / Total Common Equity",
        result: 1.85,
        result_formatted: "1.85x",
        vintage: "CA:RY:TSX · Audited Statement Line Items",
        numerator: {
          label: "Market Capitalization",
          raw_value: 200000000000,
          formatted: "$200.0B",
          units: "CAD",
          currency: "CAD",
          as_of_date: "2024-08-22",
          statement_location: "Market Close Traded Price × Diluted Shares",
          source: "Market Close",
          sec_edgar_url: "https://www.sedarplus.ca/csa-party/records/document.html",
        },
        denominator: {
          label: "Total Common Equity",
          raw_value: 108000000000,
          formatted: "$108.0B",
          units: "CAD",
          currency: "CAD",
          as_of_date: "FY2024",
          statement_location: "Consolidated Balance Sheet",
          source: "SEDAR+",
          sec_edgar_url: "https://www.sedarplus.ca/csa-party/records/document.html",
        },
        arithmetic_resolution: [
          "1. Numerator: CAD $200.0B",
          "2. Denominator: CAD $108.0B",
          "3. Ratio = $200.0B / $108.0B = 1.85x",
        ],
      };

      render(
        <RatioInspectorModal
          isOpen={true}
          onClose={onClose}
          companyId="CA:RY:TSX"
          ratioName="pb"
          initialData={initialData}
        />
      );

      // Verify SEDAR+ filing link text
      expect(screen.getAllByText("View filing on SEDAR+ ↗").length).toBeGreaterThanOrEqual(1);

      // Verify Escape dismissal
      fireEvent.keyDown(window, { key: "Escape" });
      expect(onClose).toHaveBeenCalled();
    });
  });
});
