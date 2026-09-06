// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import RevenueSparkline from "../components/screener/RevenueSparkline";
import BookChecklists from "../components/screener/BookChecklists";
import StrategyWizard, { STRATEGY_OPTIONS } from "../components/screener/StrategyWizard";
import MorningBrief from "../components/watchlist/MorningBrief";
import ScreenComponent from "./Screen";
import * as clientModule from "../api/client";

describe("Wave 2 Screener & Watchlist Components", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });
  it("renders pure SVG RevenueSparkline without chart npm libraries (US-0039)", () => {
    const values = [1000, 1200, 1150, 1400, 1600];
    const { container } = render(<RevenueSparkline values={values} width={64} height={18} />);

    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
    expect(svg?.getAttribute("width")).toBe("64");
    expect(svg?.getAttribute("height")).toBe("18");

    const polyline = container.querySelector("polyline");
    expect(polyline).toBeTruthy();
    expect(polyline?.getAttribute("points")).toBeTruthy();

    const circle = container.querySelector("circle");
    expect(circle).toBeTruthy();
  });

  it("handles empty or insufficient sparkline values gracefully", () => {
    const { container } = render(<RevenueSparkline values={[100]} />);
    expect(container.textContent).toContain("Not reported in filing");
  });

  it("renders Academic Book Checklists badges with pass/fail states (US-0041)", () => {
    const checklists = {
      graham: true,
      lynch: false,
      greenblatt: true,
      piotroski: true,
    };
    render(<BookChecklists checklists={checklists} />);

    const gBadge = screen.getByText("G");
    const lBadge = screen.getByText("L");
    const gbBadge = screen.getByText("GB");
    const pBadge = screen.getByText("P");

    expect(gBadge).toBeTruthy();
    expect(gBadge.title).toContain("PASS");
    expect(lBadge).toBeTruthy();
    expect(lBadge.title).toContain("FAIL");
    expect(gbBadge).toBeTruthy();
    expect(gbBadge.title).toContain("PASS");
    expect(pBadge).toBeTruthy();
    expect(pBadge.title).toContain("PASS");
  });

  it("renders Strategy Wizard dialog and applies selected strategy (US-0001)", () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();

    const { rerender } = render(
      <StrategyWizard isOpen={false} onClose={onClose} onSelectStrategy={onSelect} />
    );
    expect(screen.queryByText("Strategy Selection Wizard")).toBeNull();

    rerender(<StrategyWizard isOpen={true} onClose={onClose} onSelectStrategy={onSelect} />);
    expect(screen.getByText("Strategy Selection Wizard")).toBeTruthy();

    // Verify all strategy options rendered
    expect(STRATEGY_OPTIONS.length).toBeGreaterThanOrEqual(8);
    expect(screen.getByText("Magic Formula (Joel Greenblatt)")).toBeTruthy();

    // Click on a strategy card
    const card = screen.getByText("Compound Quality (Buffett / Burry)");
    fireEvent.click(card);

    expect(onSelect).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it("renders MorningBrief with 1-page digest stats, alert feed, and regulatory filings (US-0084, US-0351, US-0377)", async () => {
    vi.spyOn(clientModule.api, "watchlistDigest").mockResolvedValue({
      brief_date: "2026-09-05",
      market_session: "Pre-Market Opening Brief",
      stats: {
        total_watched: 4,
        high_severity_count: 1,
        medium_severity_count: 1,
        low_severity_count: 0,
        rerated_count: 1,
        earnings_count: 1,
      },
      alerts: [
        {
          id: "alert-1",
          company_id: "CA:SHOP:TSX",
          ticker: "SHOP",
          name: "Shopify Inc",
          alert_type: "rerated_quality",
          title: "Signal Upgraded to Strong Candidate",
          detail: "Quality pillar rose +1.2 pts due to expanding FCF margins.",
          severity: "high",
          routing: {
            primary_channel: "In-App Notification + Email Digest",
            fallback_channel: "Feed Alert",
            urgency: "HIGH_PRIORITY",
          },
          sedar_url: "https://www.sedarplus.ca/c/SHOP",
          edgar_url: null,
          timestamp: "2026-09-05T08:00:00Z",
        },
      ],
      cad_companies_count: 2,
      usd_companies_count: 2,
      currency_segregation_note: "Strict Currency Isolation: CAD and USD amounts are segregated. Ratios are unitless.",
      disclaimer: "Personal equity-research app. Local Docker. Not investment advice.",
    });

    vi.spyOn(clientModule.api, "watchlistDeltas").mockResolvedValue({
      count: 1,
      deltas: [
        {
          company_id: "CA:SHOP:TSX",
          ticker: "SHOP",
          name: "Shopify Inc",
          currency: "CAD",
          current_composite: 7.8,
          prior_composite: 7.2,
          delta_composite: 0.6,
          current_signal: "strong_candidate",
          prior_signal: "positive_momentum",
          is_rerated: true,
          pillar_deltas: { quality: 1.2, value: 0.2, growth: 0.5, risk: -0.1 },
          earnings_post_actual: {
            fiscal_year: 2024,
            revenue_actual: 7000000000,
            prior_year_revenue: 5600000000,
            revenue_growth_pct: 0.25,
            net_income_actual: 800000000,
            prior_year_net_income: 600000000,
          },
          filing_links: {
            sedar_plus: "https://www.sedarplus.ca/c/SHOP",
            edgar: null,
          },
          as_of: "2026-09-05T08:00:00Z",
        },
      ],
      timestamp: "2026-09-05T08:00:00Z",
    });

    render(
      <MemoryRouter>
        <MorningBrief companyIds={["CA:SHOP:TSX"]} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Morning Brief/ })).toBeTruthy();
      expect(screen.getByText("Signal Upgraded to Strong Candidate")).toBeTruthy();
      expect(screen.getAllByText(/SEDAR\+/).length).toBeGreaterThan(0);
      expect(screen.getByText(/Strict Currency Isolation/)).toBeTruthy();
    });

    // Switch tab to Score Deltas
    const deltasTab = screen.getByText(/Score Deltas/);
    fireEvent.click(deltasTab);

    await waitFor(() => {
      expect(screen.getByText("+0.60")).toBeTruthy();
      expect(screen.getByText("Re-Rated")).toBeTruthy();
      expect(screen.getByText(/FY2024: Rev Growth/)).toBeTruthy();
    });
  });

  it("renders Screener with Why Matched cohort summary and NULL warning diagnostics (US-0038, US-0049)", async () => {
    vi.spyOn(clientModule.api, "screen").mockResolvedValue({
      total: 1,
      count: 1,
      currency_view: "USD",
      method_version: "v1",
      disclaimer: "personal research software",
      why_matched_summary: {
        median_composite: 8.2,
        median_pe: 18.5,
        median_roe: 0.24,
        top_sectors: [{ sector: "Information Technology", count: 1 }],
        count: 1,
      },
      null_warning: null,
      items: [
        {
          company_id: "US:MSFT:US",
          name: "Microsoft Corp",
          ticker: "MSFT",
          currency: "USD",
          gics_sector: "Information Technology",
          custom_industry_sheet: "Software",
          composite: 8.2,
          signal: "strong_candidate",
          pe_calc: 18.5,
          roe_calc: 0.24,
          fcfmargin_calc: 0.32,
          peer_rank: 1,
          peer_n: 25,
          coverage: 4,
          has_growth_history: true,
          is_bank: false,
          halal_status: "halal_candidate",
          revenue_sparkline: [143000, 168000, 198000, 211000, 245000],
          checklists: {
            graham: true,
            lynch: true,
            greenblatt: true,
            piotroski: true,
          },
        },
      ],
    });

    vi.spyOn(clientModule.api, "sectors").mockResolvedValue({
      custom_industries: [],
      gics_sectors: [],
    });

    render(
      <MemoryRouter initialEntries={["/screen"]}>
        <ScreenComponent />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Why These 1 Companies Matched")).toBeTruthy();
      expect(screen.getByText("18.5x")).toBeTruthy();
      expect(screen.getByText("Microsoft Corp")).toBeTruthy();
      expect(screen.getByText("MSFT")).toBeTruthy();
    });
  });
});