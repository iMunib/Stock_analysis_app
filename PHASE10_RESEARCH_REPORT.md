# Phase 10 / Research-Desk Upgrade Sprint Report

**Date:** 2026-09-02  
**Status:** All Exit Checks Passed (100% Green)

---

## 1. Executive Summary

This upgrade converts the filing-first research application from a passive score viewer into an active, repeatable 7-step equity-research workstation:
`Find/add name → Business in one sentence → Financials + YoY → Valuation vs peers → Risks/flags → Write a 5-line thesis → Watch + next earnings`.

All four mandatory live preconditions were verified prior to deployment:
1. AMD Ingest verified working through the 202 asynchronous state machine.
2. Foreign private issuer currency mismatch verified (BABA preserves native `CNY` while suppressing USD-denominated price multiples).
3. LLM gateway narration errors safely caught without JSON parsing crashes (`proxy_read_timeout 180s`, HTML fallback).
4. Interactive `InfoTip` accessibility verified on Compare headers and Dossier snapshot tiles.

---

## 2. Implemented Capabilities

### A. Screener Engine (`GET /api/v1/screen` & `/screen`)
- **Filters:** Full AND logic across:
  - Currency (`ALL`, `USD`, `CAD`)
  - GICS Sector & Custom Industry Sheet
  - Signal (`undervalued`, `fair_value`, `overvalued`, `speculative`, `insufficient_data`)
  - Minimum Composite Score (0–10)
  - Maximum PE (with automatic exclusion of companies with blank/missing PE)
  - Minimum ROE % and Minimum FCF Margin %
  - Minimum Coverage Pillars (1–4)
  - 3-Year Growth History required toggle
  - Exclude Banks / Financials toggle
- **Multi-Currency Protection:** When viewing in `ALL` currency mode, absolute money columns are hidden to prevent cross-border currency confusion, showing only unitless valuation ratios and composite scores.
- **Table Controls:** Sortable headers, multi-row selection, and **"Compare Selected (N) →"** button navigating directly to `/compare?ids=...`.
- **Empty State Copy:** Exact contracted copy displayed when 0 names match: `"No names match — loosen PE or coverage."`

### B. Company Research Pack on Dossier (`/c/:companyId`)
- **Business in One Line:** 280-character snapshot extracted from Yahoo Finance (`longBusinessSummary`).
- **Dividend Pack & Next Earnings:**
  - Dividend yield (%) and dividend per share ($) or "—" if not reported.
  - Next upcoming earnings date or "—".
- **Quarterly Financial History:** 4-quarter compact table (Revenue, Net Income, Diluted EPS) directly beneath the annual history table.
- **Moat & SWOT Draft (`POST /api/v1/companies/{company_id}/research`):**
  - Triggered via button: `"Draft SWOT from numbers (not AI score)"`.
  - Sends deterministic facts JSON (ratios, growth, margins, coverage) to OpenRouter free models only (models containing `:free`).
  - Cached in SQLite `llm_cache` under `kind="swot"`.
  - Strict label: `"LLM draft from our facts. Not a 10-K."`.
  - Structured into Strengths, Weaknesses, Opportunities, Threats, and Competitive Advantage (1 line). Never overwrites deterministic fundamentals.
- **Thesis Notepad:**
  - Local scratchpad saved in browser `localStorage` under `thesis:{company_id}`.
  - Capped at 1,000 characters with live character counter and auto-saved timestamp.
  - Label: `"Your notes stay on this browser."`
- **Toy DCF Calculator:**
  - Interactive scratchpad card accepting Base FCF, Growth rate %, Discount rate (WACC) %, and Projection years.
  - Output is purely client-side exploratory math and is never stored as truth.
  - Disabled for financial institutions (banks/insurers) without auto-filling fake FCF.
- **Print / Save PDF:**
  - Dedicated `@media print` CSS stylesheet hiding navigation bars, action buttons, and dark styling for a clean, 1-page research report.

### C. Watchlist & Local Alerts
- **Watchlist Key Contract:** Standardized to `watchIds` via `getWatchlist()`.
- **Desk Watchlist Display:** Shows company name, ticker/ID, latest composite score, signal badge, and last-opened timestamp (`opened:{company_id}`).
- **Local Alerts:**
  - Configurable on Dossier and evaluated locally on page load (`localStorage` key `stockAlerts`).
  - Triggers a banner if PE exceeds threshold or Composite score falls below target.

### D. UX & Navigation Enhancements
- **Keyboard Shortcut:** Pressing `/` anywhere in the app instantly focuses the global search bar in the header.
- **Sector Screen Link:** Sector header contains direct link to `"Screen this sector →"`.
- **404 Ticker Recovery:** Missing company view includes 1-click chip: `"Fetch {ticker} from SEC / Yahoo"`.

### E. Documentation
- Created `docs/RESEARCH_LOOP.md` detailing how each of the 7 research steps maps to screens and tools.
- Updated `README.md` with complete documentation of the Screener, SWOT card, Thesis notepad, Toy DCF, and local alerts.

---

## 3. Test & Verification Results

| Test Suite | Result | Details |
|---|---|---|
| **Backend Pytest** | **124 / 124 Passed (100%)** | Full backend test suite passing in 8.87s, including `test_screen.py` (8 tests) and `test_research.py` (4 tests). |
| **Frontend Vitest** | **60 / 60 Passed (100%)** | 14 test files passing in 1.48s, including `Screen.test.tsx`, `alerts.test.ts`, `thesis.test.ts`, and `Dossier.test.tsx`. |
| **Frontend Build** | **Clean Build (Exit Code 0)** | `tsc && vite build` completed in 778ms without warnings or errors. |
| **Playwright E2E** | **All Passed** | `e2e/sprint.spec.ts` (6 passed); `e2e/app.spec.ts` (8 passed, including filter Software USD → click row to dossier in 565ms). |

---

## 4. Contract Conformance

- **Conservative Defaults:** Missing values remain `NULL` with quality flags.
- **No Money Cross-Contamination:** CAD and USD are never combined or averaged. Ratios only across borders.
- **No Paid APIs:** All data sourced from local seed workbook, SEC EDGAR, and Yahoo Finance free feeds.
- **OpenRouter Free Tier:** LLM calls strictly restricted to `:free` models with ground-truth facts JSON payloads only.
