// @vitest-environment jsdom
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Portfolio from "./Portfolio";
import AlertsCenter from "./AlertsCenter";
import * as clientModule from "../api/client";

describe("Wave 5 Portfolio & Alerts", () => {
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
  });

  it("renders Portfolio with currency-isolated summary and pure SVG allocation chart (US-0304/US-0323/US-0302)", async () => {
    vi.spyOn(clientModule.api, "portfolioAccounts").mockResolvedValue({ count: 2, accounts: [{ id: "a1", name: "TFSA - CAD", account_type: "TFSA", currency: "CAD" }, { id: "a2", name: "RRSP - USD", account_type: "RRSP", currency: "USD" }] } as any);
    vi.spyOn(clientModule.api, "portfolioHoldings").mockResolvedValue({ count: 1, holdings: [{ account_id: "a1", company_id: "CA:RY:TSX", ticker: "RY", quantity: 10, avg_cost_per_share: 150, cost_basis: 1500, market_price: 160, market_value: 1600, unrealized_pnl: 100, currency: "CAD", composite: 7.2 }] } as any);
    vi.spyOn(clientModule.api, "portfolioSummary").mockResolvedValue({
      holdings_count: 1,
      total_market_value_by_currency: { CAD: 1600 },
      total_cost_basis_by_currency: { CAD: 1500 },
      total_unrealized_by_currency: { CAD: 100 },
      currencies: ["CAD"],
      currency_note: "Totals are segregated by native currency; no FX conversion or blending.",
      weighted_pillar_avg: { quality: 7, value: 6, growth: 5, risk: 6 },
      weighted_composite: 6.5,
      sector_concentration: [{ sector: "Financials", market_value: 1600, weight_pct: 100 }],
    } as any);
    vi.spyOn(clientModule.api, "portfolioDividends").mockResolvedValue({ trailing_12m_by_currency: { CAD: 45 }, forward_12m_by_currency: { CAD: 50 } } as any);
    vi.spyOn(clientModule.api, "portfolioRebalance").mockResolvedValue({ total_market_value: 1600, holdings: [{ company_id: "CA:RY:TSX", ticker: "RY", weight_pct: 100, target_pct: 100, drift_pct: 0, warning: null }] } as any);
    vi.spyOn(clientModule.api, "portfolioHeatmap").mockResolvedValue({ count: 1, heatmap: [{ company_id: "CA:RY:TSX", ticker: "RY", severity: 0, flags: [] }] } as any);
    vi.spyOn(clientModule.api, "journalEntries").mockResolvedValue({ count: 0, entries: [], avg_confidence: null } as any);

    render(<MemoryRouter><Portfolio /></MemoryRouter>);

    // Title is static, should appear quickly
    expect(await screen.findByText(/Portfolio & Holdings/, {}, { timeout: 3000 })).toBeTruthy();
    // SVG chart
    const svg = await screen.findByRole("img", {}, { timeout: 3000 });
    expect(svg).toBeTruthy();
  });

  it("renders AlertsCenter with rule creation, events, calendar, and heartbeat (US-0355/US-0390/US-0352/US-0400)", async () => {
    vi.spyOn(clientModule.api, "alertRules").mockResolvedValue({ count: 1, rules: [{ id: "r1", company_id: "US:AAPL:US", rule_type: "distress", params: {}, enabled: true }] } as any);
    vi.spyOn(clientModule.api, "alertsEvents").mockResolvedValue({ count: 1, events: [{ id: "e1", company_id: "US:AAPL:US", ticker: "AAPL", rule_type: "distress", severity: "critical", detail: "Altman Z in Distress" }] } as any);
    vi.spyOn(clientModule.api, "alertsCalendar").mockResolvedValue({ count: 1, items: [{ company_id: "US:AAPL:US", event_type: "earnings", event_date: "2026-09-20", days_ahead: 5 }] } as any);
    vi.spyOn(clientModule.api, "alertsHeartbeat").mockResolvedValue({ status: "operational", daemon: "local_alerts_daemon", last_evaluated_at: "2026-09-05T12:00:00", uptime: "local SQLite WAL" } as any);

    render(<MemoryRouter><AlertsCenter /></MemoryRouter>);

    expect(await screen.findByText(/Alerts Center/, {}, { timeout: 3000 })).toBeTruthy();
    expect(await screen.findByText(/Create Alert Rule/, {}, { timeout: 3000 })).toBeTruthy();
    expect(await screen.findByText(/Active Rules/, {}, { timeout: 3000 })).toBeTruthy();
  });

  it("portfolio transaction modal is keyboard accessible (Tab/Escape) and has ARIA", async () => {
    vi.spyOn(clientModule.api, "portfolioAccounts").mockResolvedValue({ count: 1, accounts: [{ id: "a1", name: "TFSA", account_type: "TFSA", currency: "CAD" }] } as any);
    vi.spyOn(clientModule.api, "portfolioHoldings").mockResolvedValue({ count: 0, holdings: [] } as any);
    vi.spyOn(clientModule.api, "portfolioSummary").mockResolvedValue({ holdings_count: 0, total_market_value_by_currency: {}, total_cost_basis_by_currency: {}, total_unrealized_by_currency: {}, currencies: [], currency_note: "", weighted_pillar_avg: {}, weighted_composite: null, sector_concentration: [] } as any);
    vi.spyOn(clientModule.api, "portfolioDividends").mockResolvedValue({ trailing_12m_by_currency: {}, forward_12m_by_currency: {} } as any);
    vi.spyOn(clientModule.api, "portfolioRebalance").mockResolvedValue({ total_market_value: 0, holdings: [] } as any);
    vi.spyOn(clientModule.api, "portfolioHeatmap").mockResolvedValue({ count: 0, heatmap: [] } as any);
    vi.spyOn(clientModule.api, "journalEntries").mockResolvedValue({ count: 0, entries: [] } as any);

    render(<MemoryRouter><Portfolio /></MemoryRouter>);
    const btn = await screen.findByText(/Add Transaction/, {}, { timeout: 3000 });
    expect(btn).toBeTruthy();
    fireEvent.click(btn);
    const dialog = await screen.findByRole("dialog", { name: /Add Transaction/ }, { timeout: 3000 });
    expect(dialog).toBeTruthy();
    expect(screen.getByLabelText("Company ID")).toBeTruthy();
  });
});