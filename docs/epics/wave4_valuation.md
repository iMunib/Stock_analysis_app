# Wave 4 Epic Specification: Valuation Depth — Guided DCF, EPV, Bank Models & Sensitivity

> **Phase 1 Wave 4 Specification**
> **Objective**: Deliver 38 user stories in Epic 10 (Guided DCF, Reverse-DCF & Valuation Sensitivity Matrix) — an assumption-explicit, range-based valuation suite that complements the locked 0.30/0.25/0.25/0.20 composite without altering it. Native-currency only, ranges not points, bank/insurer DCF disabled with DDM/Residual Income routing, pure SVG sensitivity heatmaps, and local scenario persistence.
> **Frozen Contracts Maintained**: Native-currency valuation (multiples/yields/growth unitless); seed immutability; honest NULL + flag (valuations are ranges, never single-point false precision); scoring weights locked (valuation does NOT alter composite); bank/insurer FCF DCF invalid → DDM/Residual Income with explicit notice; pure SVG+CSS (tokens.css) only; local Docker/SQLite WAL; a11y (prefers-reduced-motion, ARIA, keyboard); disclaimer on every valuation surface.

---

## Epic 10: Guided DCF, Reverse-DCF & Valuation Sensitivity Matrix (38 Stories)

### US-0101: Guided DCF Walkthrough in Plain English
- **Given** a learner opening the Valuation & Expectations tab on any company
- **When** launching the Guided DCF modal
- **Then** a step-by-step sandbox renders (Revenue → EBIT → NOPAT → FCF → Discount → Terminal Value → Enterprise Value → Equity Value → per-share) with plain-English explanations and live arithmetic resolution per step.

### US-0102: Every DCF Driver Shows Source & History
- **Given** the Guided DCF with default assumptions
- **When** inspecting any driver (revenue growth, operating margin, WACC, terminal growth)
- **Then** the modal displays source badge (`owner workbook` | `sec_companyfacts` | `yfinance`), historical trajectory (3-yr CAGR / 5-yr median), and derivation note; missing history shows `insufficient_data` rather than a guessed default.

### US-0105: Bear / Base / Bull Scenarios with Sensitivity Table
- **Given** the Guided DCF with three scenario presets
- **When** toggling Bear (pessimistic margins/growth), Base (mid), Bull (optimistic)
- **Then** each scenario recomputes intrinsic value and renders a sensitivity heatmap (WACC × terminal growth) with accessible ARIA labels.

### US-0106: Greenwald Earnings Power Value (EPV) vs Market Cap
- **Given** a non-financial company with EBIT and WACC
- **When** viewing the EPV card
- **Then** EPV = Normalized Operating Earnings × (1 − tax) / WACC is computed, compared to reproduction cost (Total Assets) and market cap, with margin-of-safety floor.

### US-0108: Interactive Sandbox — Instant Value Impact
- **Given** any numeric DCF input (growth, margin, WACC, terminal g)
- **When** dragging the slider or typing a new value
- **Then** intrinsic value, upside %, and sensitivity heatmap update instantly (< 50 ms) with no page reload.

### US-0109: Dividend Discount Model (DDM) for Steady Payers
- **Given** a company with at least 3 years of dividend history
- **When** requesting DDM valuation
- **Then** a multi-stage DDM (Gordon + 5-yr supernormal growth where payout history supports it) returns fair value, dividend yield, payout ratio, and Gordon sanity check; otherwise `insufficient_data`.

### US-0111: Thin-History Warning in Valuation Inputs
- **Given** a company with < 3 FY of history for a driver (e.g., only 1–2 revenue points)
- **When** the DCF renders
- **Then** a warning chip "Thin history — assumption uses 1–2 points" appears next to that driver with `thin_history` flag.

### US-0113: Save Multiple Named Valuation Scenarios (Local Persistence)
- **Given** a user editing Bears/Base/Bull assumptions and clicking "Save scenario"
- **When** providing a name and notes
- **Then** the scenario JSON is persisted to `localStorage` key `valuation_scenarios:{company_id}` (max 10, each ≤ 2 KB) and reappears on reload.

### US-0114: Valuation Historian — Past Implied Expectations vs Actuals
- **Given** a company with 5-year history and current reverse DCF
- **When** opening the Historian strip
- **Then** the UI plots historical implied growth (market-implied g from backfilled EV years where available) against realized 5-yr FCF CAGR, highlighting expectation misses.

### US-0115: Cheap-for-a-Reason Check (EPV vs Forensic Flags)
- **Given** price < EPV or NCAV but Beneish/Altman flags fail
- **When** the EPV card renders
- **Then** a `CHEAP_FOR_A_REASON` warning banner notes "Price below EPV floor but forensic flags triggered — investigate before anchoring."

### US-0116: Bank/Insurer Valuation Routing — Residual Income / Excess Returns
- **Given** a company where `gics_sector == Financials` or `custom_industry_sheet` in `{Banks, Insurance, Credit Services}`
- **When** opening Valuation tab
- **Then** standard FCF DCF shows disabled state "FCF DCF not meaningful for banks/insurers" and auto-routes to DDM + Residual Income (Equity + PV(Excess ROE over Cost of Equity)).

### US-0117: Mid-Cycle Normalized Earnings for Cyclicals (Energy/Materials/Industrials)
- **Given** a cyclical-sector company with ≥ 5 FY earnings
- **When** toggling "Mid-cycle normalized" view
- **Then** normalized earnings = 5-yr median EBIT (or median ROE × book equity) replaces peak-year EBIT; the card shows both peak and normalized values with Δ.

### US-0118: Fair Multiple View — Current PE vs Justified PE (Growth + ROE)
- **Given** any company with PE, EPS growth, and ROE
- **When** viewing the Quick Multiple card
- **Then** justified PE = (1 − payout) / (cost_of_equity − growth) simplified to `ROE/median * (1+g)/(k−g)` proxy is shown alongside current PE with Δ and interpretation.

### US-0119: Portfolio Valuation Export — Price vs Intrinsic Value Gaps
- **Given** a watchlist of 2–8 companies with saved intrinsic values (or on-the-fly DCF fair values)
- **When** clicking "Export valuation gaps"
- **Then** a CSV with columns `Company, Currency, Price, Intrinsic Value, Premium/Discount %, As-of Date` is downloaded (currency-tagged, never blended).

### US-0120: Educator Live Valuation Projection (Deterministic)
- **Given** any company in a classroom setting
- **When** projecting the Guided DCF
- **Then** all inputs/outputs are deterministic, reproducible, and labeled with provenance — no LLM or random component.

### US-0121: Alert When Watched Name Crosses Below Intrinsic Value
- **Given** a saved scenario with intrinsic value V and current price P from `GET /companies/{id}/valuation`
- **When** price crosses below V (`P < V`) on next ingest
- **Then** the watchlist digest logic can surface a local `valuation_opportunity` alert (evaluated client-side via `watchlist.ts` re-check; no server push).

### US-0122: Reverse DCF Decomposition (Price vs Volume vs Margin Recovery)
- **Given** revenue, price, and margin history
- **When** requesting reverse DCF decomposition
- **Then** the API decomposes implied growth into `volume_component`, `price_component`, and `margin_recovery_component` where data allows; missing components return `insufficient_data` rather than invented splits.

### US-0123: Uncertainty Ranges (10th–90th Percentile), Not Single Points
- **Given** the Guided DCF with base assumptions
- **When** the uncertainty band toggle is enabled
- **Then** the DCF renders a 10th–50th–90th percentile fair-value range (via ±1.5 pp growth and ±1 pp WACC shocks) rather than a single-point fair value.

### US-0125: Discount Rate (WACC) Build Component
- **Given** the DCF WACC row
- **When** expanding WACC details
- **Then** the build shows Risk-Free Rate (default 4.0% ± user override) + Equity Risk Premium (default 5.0%) × Beta (derived from `beta` key stat or 1.0 fallback) with arithmetic `WACC = Rf + ERP × Beta`.

### US-0126: Terminal Value Percentage Warning (>70% EV)
- **Given** a DCF where terminal value PV > 70% of total EV
- **When** the sensitivity card renders
- **Then** a `TERMINAL_HEAVY` warning chip appears: "Terminal value represents >70% of EV — valuation is fragile to terminal assumptions."

### US-0128: 3-Minute Valuation in One Screen Walkthrough
- **Given** a first-time valuer
- **When** clicking "3-minute walkthrough" in Learn or Valuation tab
- **Then** a guided overlay steps through base DCF → sensitivity → EPV floor → bank routing with a real example (AAPL).

### US-0129: Value-Trap Flag Next to 'Undervalued' Verdict
- **Given** an undervalued verdict (price < intrinsic) but `forensic_health_score` < 50 or Altman Distress
- **When** the valuation header renders
- **Then** a `VALUE_TRAP_RISK` chip notes "Cheap but forensic flags failing — do not anchor on price alone."

### US-0130: Dividend-Adjusted Total Return Scenarios to Horizon
- **Given** current price, dividend yield, and horizon (5/10 yr) with base growth
- **When** viewing the dividend total-return strip
- **Then** the card shows total-return CAGR (price appreciation + dividend yield) for Bear/Base/Bull with native-currency labels.

### US-0131: Attach Valuation Thesis to Company Record (Local)
- **Given** a valuation scenario
- **When** saving with thesis notes
- **Then** the thesis text is persisted alongside the scenario in `localStorage` `valuation_scenarios:{company_id}` and surfaced in the scenario manager.

### US-0132: Company Own 10-Year Multiple Range Context
- **Given** a company's 10-year PE history
- **When** viewing the multiple context strip
- **Then** a pure SVG range meter shows min/median/max PE and current PE marker with percentile rank.

### US-0134: Edit and Fork Built-In Valuation Templates
- **Given** a built-in template (Base/Bear/Bull)
- **When** clicking "Fork template"
- **Then** a new local scenario clones the template with editable name/notes; built-ins remain immutable.

### US-0135: Delta Between User Scenario and Market-Implied Scenario
- **Given** a saved user scenario (growth g_user) and market-implied growth g_mkt from reverse DCF
- **When** viewing the delta strip
- **Then** Δ = g_user − g_mkt is shown with interpretation ("You assume X pp more growth than market prices").

### US-0138: FCF Conversion Trend Before Valuation Trust
- **Given** FCF/Net Income history
- **When** conversion < 0.7 for 2 consecutive FY
- **Then** a `WEAK_CONVERSION` warning appears in the DCF header with link to forensic CCC card.

### US-0141: Required Return Scenarios (10%/12%/15%) vs Single Discount Rate
- **Given** base FCF forecast
- **When** toggling "Required return" view
- **Then** the DCF recomputes present value at 10%, 12%, 15% required returns alongside the base WACC, showing return humility.

### US-0142: Cycle-Aware Margin Context Before Normalizing
- **Given** gross/operating margins across 5-yr history
- **When** opening the mid-cycle panel
- **Then** the panel shows margins vs 10-yr range (min/median/max) before the user chooses normalized vs peak.

### US-0143: Inventory & Receivables Trends Flagged Inside Valuation Notes
- **Given** shenanigans DSO/inventory flags
- **When** valuation notes render
- **Then** any `RED_FLAG_DSO_SURGE` or `RED_FLAG_INVENTORY_BUILDUP` appears as an inline valuation note.

### US-0144: Portfolio Builder — Rank Watchlist by Discount to Intrinsic Value
- **Given** a watchlist with saved intrinsic values
- **When** requesting portfolio ranking
- **Then** `GET /api/v1/valuation/rank?ids=a,b` returns companies sorted by discount/premium % to intrinsic value.

### US-0145: Step-by-Step Arithmetic Rendering (Show Me the Math)
- **Given** any DCF output (PV of flows, terminal value, EV, equity value, per-share)
- **When** expanding "Show math"
- **Then** each arithmetic step is rendered with formula, inputs, and result (e.g., `PV year 1: 100 × 1.05 / 1.09 = 96.33`).

### US-0146: Clone Last Year's Assumptions into This Year's Update
- **Given** a saved scenario from a prior FY
- **When** clicking "Clone to current year"
- **Then** the scenario is duplicated with updated baseline FCF and as-of date, preserving growth/margin assumptions.

### US-0147: Ways This Valuation Fails (Assumption Breaks) per Model
- **Given** any valuation model (DCF, EPV, DDM, Residual Income)
- **When** expanding "Ways this fails"
- **Then** a checklist of failure modes (e.g., "Growth never materializes", "WACC underestimated", "Regulatory capital breach for banks") is displayed.

### US-0148: Total-Yield (Dividend + Buyback) Alongside DCF Outputs
- **Given** DCF outputs
- **When** total-yield is available from `shareholder_yield`
- **Then** the DCF footer shows total shareholder yield vs FCF yield for capital-return context.

### US-0149: Side-by-Side Valuation for Two Companies (Teaching Aid)
- **Given** two company IDs
- **When** requesting comparison
- **Then** `GET /api/v1/valuation/compare?ids=a,b` returns both companies' valuation suites side-by-side.

### US-0150: Uncertainty Reminder — Valuation Is a Range with Confidence
- **Given** any valuation view
- **When** the view renders
- **Then** a persistent disclaimer banner states "Intrinsic value is a hypothetical range based on user assumptions, not a prediction. Confidence is limited by input uncertainty." alongside the standard not-investment-advice disclaimer.

---

## Cross-Cutting Acceptance Notes

- All valuations operate in native currency; growth/margin/yield multiples are unitless. Cross-currency watchlist ranking uses discount % (unitless), never blended money.
- Missing inputs → `NULL` + flag (`insufficient_data`, `thin_history`, `bank_excluded`). No single-point false precision: ranges and percentiles are shown.
- Bank/insurer routing: `is_financial` → DCF `status: financial_institution_excluded` with notice and DDM/Residual Income displayed instead.
- Pure SVG heatmaps/range meters use `<svg>`, `<rect>`, `<line>`, `<text>` with `tokens.css`; no chart npm libraries.
- a11y: sliders, scenario tables, heatmap cells have `role="slider"`/`role="gridcell"`, `aria-valuenow`, `aria-label`, keyboard arrow support, and `prefers-reduced-motion` disables count-up.
- Disclaimer on every valuation surface: "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions."
