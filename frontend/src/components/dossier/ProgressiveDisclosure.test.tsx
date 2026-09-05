// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { VerdictBadge, computeVerdict } from "./VerdictBadge";
import { TrafficLightTile } from "./TrafficLightTile";
import { ReverseDcfRuleBox } from "./ReverseDcfRuleBox";
import { DecisionBullets } from "./DecisionBullets";
import { LynchArchetypeCard } from "./LynchArchetypeCard";
import { ShareholderYieldBar } from "./ShareholderYieldBar";
import { CashFlowWaterfall } from "./CashFlowWaterfall";
import { BeneishMatrix } from "./BeneishMatrix";
import { PenmanDecompositionTable } from "./PenmanDecompositionTable";
import { AltmanZScoreCard } from "./AltmanZScoreCard";
import { FridsonRealitySpread } from "./FridsonRealitySpread";
import { CurrencyBadge } from "../ui/CurrencyBadge";

describe("Progressive Disclosure & Telemetry Components", () => {
  describe("VerdictBadge", () => {
    it("computes COMPOUNDER AT FAIR VALUE for wide moat with safe Altman", () => {
      const v = computeVerdict({
        moatPass: true,
        altmanSafe: true,
        reverseDcfGap: 1.5,
        coverage: 4,
      });
      expect(v.label).toBe("COMPOUNDER AT FAIR VALUE");
      expect(v.tone).toBe("positive");
    });

    it("computes AVOID: VALUE TRAP / DISTRESS for distressed company", () => {
      const v = computeVerdict({
        altmanDistress: true,
        coverage: 4,
      });
      expect(v.label).toBe("AVOID: VALUE TRAP / DISTRESS");
      expect(v.tone).toBe("negative");
    });

    it("renders verdict text and confidence", () => {
      render(<VerdictBadge verdict="COMPOUNDER AT FAIR VALUE" confidence="HIGH (4/4 Pillars Complete)" />);
      expect(screen.getByText("COMPOUNDER AT FAIR VALUE")).toBeTruthy();
      expect(screen.getByText(/4\/4 Pillars Complete/)).toBeTruthy();
    });
  });

  describe("TrafficLightTile", () => {
    it("renders title, status text, and metrics", () => {
      render(
        <TrafficLightTile
          number={1}
          title="Business Moat & Quality"
          statusText="WIDE MOAT"
          status="green"
          description="High pricing power"
          metrics={[{ label: "ROIC", value: "58.0%" }]}
        />
      );
      expect(screen.getByText(/1\. Business Moat & Quality/)).toBeTruthy();
      expect(screen.getByText("WIDE MOAT")).toBeTruthy();
      expect(screen.getByText("58.0%")).toBeTruthy();
    });
  });

  describe("ReverseDcfRuleBox", () => {
    it("renders quotation with required growth rate", () => {
      render(
        <ReverseDcfRuleBox
          currentPrice={228.5}
          currency="USD"
          companyName="Apple Inc."
          impliedCagr={11.2}
          historicalCagr={13.8}
        />
      );
      expect(screen.getByText(/To justify today's price of/)).toBeTruthy();
      expect(screen.getByText(/\$228\.50 USD/)).toBeTruthy();
      expect(screen.getByText(/\+11\.2%/)).toBeTruthy();
      expect(screen.getByText(/compounded cash flow at/)).toBeTruthy();
    });
  });

  describe("DecisionBullets", () => {
    it("renders core strengths, key risk, and index opportunity cost", () => {
      render(
        <DecisionBullets
          strengths={["Pristine balance sheet", "High-margin services"]}
          keyRisk="Supply chain concentration"
          expectedReturn={10.8}
          indexBaseline={8.0}
        />
      );
      expect(screen.getByText(/Why Buy \(Core Strengths\)/)).toBeTruthy();
      expect(screen.getByText("Pristine balance sheet")).toBeTruthy();
      expect(screen.getByText("Supply chain concentration")).toBeTruthy();
      expect(screen.getByText(/10\.8%/)).toBeTruthy();
    });
  });

  describe("LynchArchetypeCard & Buffett Owner Earnings", () => {
    it("renders Peter Lynch archetype and Buffett owner earnings", () => {
      render(
        <LynchArchetypeCard
          archetype="STALWART COMPOUNDER"
          epsGrowth5y={14.2}
          peRatio={32.4}
          pegRatio={2.28}
          netIncome={100_000_000_000}
          ownerEarnings={98_000_000_000}
          ownerEarningsYield={2.82}
        />
      );
      expect(screen.getByText("STALWART COMPOUNDER")).toBeTruthy();
      expect(screen.getByText("32.4x")).toBeTruthy();
      expect(screen.getByText(/Buffett Owner Earnings/)).toBeTruthy();
      expect(screen.getByText(/Yield: 2.82%/)).toBeTruthy();
    });
  });

  describe("ShareholderYieldBar", () => {
    it("renders dividends, buybacks, SBC deduction and true yield", () => {
      render(
        <ShareholderYieldBar
          dividendYield={0.44}
          buybackYield={3.12}
          buybackDollars={108_000_000_000}
          sbcDilutionYield={0.32}
          sbcDollars={11_000_000_000}
          netFloatShrinkPct={-2.8}
        />
      );
      expect(screen.getByText(/\+0\.44%/)).toBeTruthy();
      expect(screen.getByText(/\+3\.12%/)).toBeTruthy();
      expect(screen.getByText(/-0\.32%/)).toBeTruthy();
      expect(screen.getByText("3.24%")).toBeTruthy(); // 0.44 + 3.12 - 0.32
    });
  });

  describe("CashFlowWaterfall", () => {
    it("renders revenue to FCF cascading conversion", () => {
      render(
        <CashFlowWaterfall
          revenue={383_000_000_000}
          grossProfit={170_000_000_000}
          netIncome={100_000_000_000}
          cfo={110_000_000_000}
          fcf={99_000_000_000}
        />
      );
      expect(screen.getByText("Ittelson Cash Flow Waterfall")).toBeTruthy();
      expect(screen.getByText("Gross Profit")).toBeTruthy();
      expect(screen.getByText("Cash from Operations (CFO)")).toBeTruthy();
      expect(screen.getByText("Free Cash Flow (FCF)")).toBeTruthy();
    });
  });

  describe("BeneishMatrix", () => {
    it("renders 8 forensic variables with PASS/FLAG status", () => {
      render(
        <BeneishMatrix
          analysis={{
            company_id: "US:AAPL:US",
            m_score: -2.94,
            is_manipulator: false,
            zone: "Non-manipulator",
            threshold: -1.78,
            variables: {
              dsri: 1.02,
              gmi: 0.96,
              aqi: 0.91,
              sgi: 1.06,
              depi: 0.98,
              sgai: 0.97,
              lvgi: 0.94,
              tata: 0.02,
            },
            interpretation: "Clean accounting profile.",
            status: "normal",
            message: undefined,
          }}
        />
      );
      expect(screen.getByText("Beneish 8-Variable Forensic Matrix")).toBeTruthy();
      expect(screen.getByText("-2.94")).toBeTruthy();
      expect(screen.getByText("CLEAN PROFILE")).toBeTruthy();
      expect(screen.getByText("DSRI")).toBeTruthy();
      expect(screen.getByText("TATA")).toBeTruthy();
    });
  });

  describe("PenmanDecompositionTable", () => {
    it("renders FLEV leverage multiplier and operating spread", () => {
      render(
        <PenmanDecompositionTable
          rnoa={0.482}
          flev={1.14}
          nbc={0.032}
          spread={0.45}
          roe={0.995}
        />
      );
      expect(screen.getByText(/Stephen Penman Reformulation/)).toBeTruthy();
      expect(screen.getByText("1.14x")).toBeTruthy();
      expect(screen.getByText("45.0%")).toBeTruthy();
    });
  });

  describe("AltmanZScoreCard", () => {
    it("renders safe zone and 5-factor breakdown", () => {
      render(
        <AltmanZScoreCard
          zScore={4.82}
          zone="Safe"
          x1={0.08}
          x2={0.22}
          x3={0.34}
          x4={3.82}
          x5={1.1}
        />
      );
      expect(screen.getByText(/Edward Altman Distress & Solvency Suite/)).toBeTruthy();
      expect(screen.getByText("4.82")).toBeTruthy();
      expect(screen.getByText("SAFE ZONE (Z > 2.99)")).toBeTruthy();
      expect(screen.getByText("X1")).toBeTruthy();
    });
  });

  describe("FridsonRealitySpread", () => {
    it("renders EBITDA vs CFO reality spread", () => {
      render(
        <FridsonRealitySpread
          ebitda={125_000_000_000}
          cfo={110_000_000_000}
        />
      );
      expect(screen.getByText(/Martin Fridson Reality Spread/)).toBeTruthy();
      expect(screen.getByText(/Spread \(EBITDA - CFO\):/)).toBeTruthy();
    });
  });

  describe("CurrencyBadge", () => {
    it("renders USD with strict isolation styling", () => {
      render(<CurrencyBadge currency="USD" showQuarantineNote />);
      expect(screen.getByText("USD")).toBeTruthy();
      expect(screen.getByText(/\(Strict ledger isolation\)/)).toBeTruthy();
    });
  });
});
