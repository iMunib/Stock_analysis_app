// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BeneishCard } from "./BeneishCard";
import type { BeneishAnalysis } from "../../api/types";

describe("BeneishCard", () => {
  it("renders non-manipulator clean profile correctly", () => {
    const analysis: BeneishAnalysis = {
      company_id: "US:MSFT:US",
      fiscal_year: 2024,
      status: "computed",
      m_score: -2.45,
      is_manipulator: false,
      zone: "Non-manipulator",
      threshold: -1.78,
      variables: {
        dsri: 1.02,
        gmi: 0.98,
        aqi: 1.01,
        sgi: 1.15,
        depi: 1.0,
        sgai: 0.95,
        lvgi: 0.92,
        tata: 0.04,
      },
      interpretation: "Low probability of earnings manipulation (M <= -1.78).",
    };

    render(<BeneishCard analysis={analysis} />);
    expect(screen.getByText("Beneish M-Score Forensic Screen")).toBeDefined();
    expect(screen.getByText("-2.45")).toBeDefined();
    expect(screen.getByText("Clean Profile (Non-manipulator)")).toBeDefined();
    expect(screen.getByText("DSRI")).toBeDefined();
    expect(screen.getByText("1.02")).toBeDefined();
  });

  it("renders excluded financial institution correctly", () => {
    const analysis: BeneishAnalysis = {
      company_id: "CA:RY:TSX",
      status: "financial_institution_excluded",
      m_score: null,
      is_manipulator: false,
      zone: "Excluded",
      threshold: -1.78,
      interpretation: "Financial institution excluded",
      message: "Financial institutions excluded from Beneish M-Score analysis.",
    };

    render(<BeneishCard analysis={analysis} />);
    expect(screen.getByText("Excluded (Financial Institution)")).toBeDefined();
    expect(
      screen.getByText("Financial institutions excluded from Beneish M-Score analysis.")
    ).toBeDefined();
  });
});
