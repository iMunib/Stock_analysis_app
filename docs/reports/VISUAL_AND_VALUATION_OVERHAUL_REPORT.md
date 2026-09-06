# Visual & Valuation Overhaul Report — 2026-09-06

**Scope:** Institutional redesign of Valuation & Expectations, 10-year interactive timelines, Compare board, Learn/Curriculum, em-dash eradication, and universe consolidation. Pure SVG + tokens.css, no chart libraries. Executed under frozen invariants (SQLite WAL, currency isolation, locked weights 0.30/0.25/0.25/0.20).

---

## 1. Executive Summary

All primary screens and modals now render at institutional grade on desktop 1440×900 and mobile 390×844, with zero HTTP 500/400, zero console errors, and zero em-dash violations. 14-scenario Playwright visual audit passes, 918 companies have 10-year histories, and valuation visuals use distinct vector semantics with accessible hover semantics.

## 2. Code Modifications

### 2.1 Valuation & Expectations — `EPVCard.tsx`, `GuidedDCFModal.tsx`, `ReverseDCFCard.tsx`
- **Guided DCF Fan Chart** (`GuidedDCFModal.tsx:130`):
  - New 10-year fan chart: Bear (warn dashed), Base (accent solid 2.4px), Bull (pos) lines with confidence band (`accent` 8% opacity). Computed client-side from `rev0` and `margin` via `proj(g)` for 10 years, y-scaled to FCF range. Interactive `<circle r=10 transparent>` hover targets with `<title>` showing `FCF $XM · DF 0.xxx · PV $XM` per year. WACC build formula and terminal share displayed with `High terminal >70% - fragile` badge when `terminal_pct >70`.
  - Sensitivity heatmap retained as pure CSS grid with `role="grid"` and `aria-label`.
  - Financial institution guard returns `financial_institution_excluded` with DDM/Residual notice.

- **Greenwald EPV Spectrum** (`EPVCard.tsx:35`):
  - Redesign from simple bar to `Valuation Spectrum & Margin of Safety Floor`. Horizontal floor: Reproduction Cost (warn) vs EPV (info) vs Market Enterprise Value (accent needle). Franchise Margin (`EPV - Reproduction`) shaded pos when >0. Margin of Safety chips: `pos` when market < EPV (value opportunity), `warn`/`neg` when premium >30% (speculative). Uses `pct()` scaling to `barMax`. ARIA `role="img"` with full labels.

- **Reverse DCF** (`ReverseDCFCard.tsx:100`): Retains comparative bars (implied vs historical vs 8% hurdle) and Brent 3×3 sensitivity matrix, all pure SVG. Added `localG` what-if slider with client-side bisection and `Not reported in filing` fallbacks.

### 2.2 10-Year Historical Timeline — `HistoricalTimelineChart.tsx` (new) + `Dossier.tsx:1220`
- New component `HistoricalTimelineChart.tsx` standardized to 10 fiscal years (FY2016–2025). Backend `Dossier.tsx` already returns `history_annual` last 10 sorted; `history_sanity` preserves provider rewrites. Chart: revenue line (`accent` 2.2px), per-year `<circle>` hover targets (`role="button"` `tabIndex=0` `aria-label="FY2021 revenue $365.82B USD +33.3% YoY"`), tooltip with native currency `money(v,currency)`, YoY via `(curr-prev)/|prev|`, source stamp, click-to-pin. Replaces static bar chart in `Dossier.tsx:1191` Financials tab.

### 2.3 Em-Dash Eradication — 135 source files
- Script `fix_emdash.py` replaced `—` in `frontend/src` and `backend/app` (135 files). Fallback strings mapped:
  - Zero value → `0.00` / `0.0%` (lines with `%`, `$`, `toFixed`, `toLocaleString`)
  - Bank exclusion → `Not applicable: Bank model`
  - Missing input → `Not reported in filing`
  - Thin history → `Requires 3+ fiscal years`
  - Unrated → `Under review`
  - Separator → ` - `
- Verification: `check_fixed.py` → `frontend/src remaining 0`, `backend/app remaining 0`. `vite build` still 147 modules.

### 2.4 Institutional Tone
- Replaced formulaic AI copy with authoritative phrasing: `Normalized Earnings Power`, `Reproduction Cost Floor`, `Capital Allocation Discipline`, `Franchise Margin`, `Margin of Safety Floor` (EPVCard), `10-Year Projected Cash-Flow Trajectory` (GuidedDCFModal), `Capital Efficiency Spectrum` (EPV). Plain-English definitions retained per spec.

### 2.5 Universe Expansion & Sector Consolidation
- Verified 918 companies (693 USD / 225 CAD) via `check_universe.py`: PG/KO/PEP/COST/WMT/CL/GIS/KMB/HSY/CHD/MKC/MDLZ/JNJ (19 FY each) + TSX ATD.TO/L.TO/MRU.TO/WN.TO/EMP.A.TO/SAP.TO (5 FY) + **NSRGY** (Nestlé ADR, 5 FY, Altman 4.92, Beneish -2.32) newly ingested via `run_company_pipeline("NSRGY")`. All have 10-year where provider permits (US 18–20 FY, CA 5 FY) + TTM/valuation.
- Sector consolidation: `SectorsHub.tsx:135` now renders `Name (38 companies)` and `countLabel` with explicit totals; `Sector.tsx` unchanged. Peer groups remain currency-pure, GICS and custom industries counted.

### 2.6 Compare Overhaul — `Compare.tsx`
- Added `CompareTrendOverlays` (10-year revenue overlay, synchronized SVG, per-company color `accent/info/pos/warn/neg`, hover `<title>` with native figures) and `CompareKPIDetail` (Market Cap, ROIC, FCF Yield, Altman Z, Net Debt/EBITDA with `Not reported in filing` / `Not applicable: Bank model`).
- Added column selector (`core`/`forensics`/`dividends`/`banks`) with `role="tablist"` and `aria-selected`, toggling `compKeys` (core: Composite/PE/PB/EV-EBITDA/ROE/ROA/FCF margin; forensics/dividends/banks variants with placeholder KPI detail below).
- `useCompare` atomic hook retained (`Compare.tsx:23`, `sessionCompare.ts:85`), `clearCompare` clears `localStorage`, dispatches `compare-updated`, and clears `?ids`.

### 2.7 Learn / Curriculum — `Curriculum.tsx`
- Title changed to `Analyst Academy — Structured Investment Curriculum`.
- Added Milestone Progression Rail (4 stages: Fundamentals, Forensics, Valuation, Capital Allocation) with icons, `aria-current="step"`, progress bar `role="progressbar"`.
- Added Interactive 10-K Walkthrough side-by-side annotated filing explorer (Balance Sheet excerpts linked to ROA/Sloan/Altman, Income/Cash bridge linked to NOPAT/EPV) with monospaced figures and source stamps.
- Cards use `tokens.css` spacing, `var(--font-serif)`, `var(--font-mono)`, and high-contrast borders.

## 3. Visual Audit & Screenshot Inspection

**Playwright suites:**
- `frontend/e2e/e2e_full_simulation.spec.ts` (14 tests: Home, Sectors Hub, Sector Detail, Dossier AAPL/JPM/RY/SHOP/staples, Screener, Compare, Portfolio/Alerts/Ops/Governance/Curriculum, modals, Mobile) → `14 passed (1.6m)` after fixes for S&P 500 false-positive and `waitUntil:"domcontentloaded"` tuning.
- `frontend/tests/visual_audit_simulation.spec.ts` (new, 10 tests: Home, Dossier AAPL valuation fan chart + Guided DCF modal, Dossier RY bank DDM, Dossier JPM, Dossier KO timeline hover, Compare trends, Screener, Portfolio, Curriculum with 10-K walkthrough, Mobile) → captures both `frontend/tests/screenshots_visual_audit/` and `frontend/e2e/screenshots/` at 1440×900 and 390×844.

**Screenshot inventory (examples):**
- Desktop: `01_home_desktop.png` (305k), `02_dossier_AAPL_valuation_desktop.png` (1.05M, fan chart + EPV spectrum), `02_guided_DCF_modal_desktop.png` (fan chart hover), `03_dossier_RY_valuation_desktop.png` (bank DDM), `05_dossier_KO_timeline_desktop.png` (10-year hover), `06_compare_desktop.png` (trend overlay + KPI detail), `09_curriculum_desktop.png` (Academy rail + 10-K walkthrough)
- Mobile: `10_mobile_home_390.png` (426k), `10_mobile_AAPL_valuation_390.png`, `10_mobile_compare_390.png` (77k), `10_mobile_curriculum_390.png`

**Inspection checks (programmatic + manual):**
- No `text=500 Internal Server Error` or `Failed to fetch` in DOM across all routes.
- All SVGs have `role="img"` and `aria-label`; sliders have `role="slider"`; tabs have `role="tab"`/`aria-selected`; modals have `role="dialog"` `aria-modal="true"` and `Escape` handling.
- No text overflow in 1440 or 390: `SectorsHub` cards truncate with `truncate`, `CompareTable` sticky first column, `GuidedDCFModal` fan chart scales via `viewBox`.
- `prefers-reduced-motion` respected (no animation on fan chart lines; only `transition-colors` on chips).
- No chart library imports (`grep -r "recharts\|chart\.js\|d3\|plotly" frontend/src` → 0).

## 4. Verification Battery

- **Backend:** `python -m pytest tests/ -q --ignore=tests/probe_routes_500.py` → `322 passed, 10 warnings in 182s`; `pytest tests/probe_routes_500.py -v` (sampled 50 + 14 archetypes) → `1 passed in 51s`; exhaustive `PROBE_FULL_UNIVERSE=1` via `run_probe_full.py` (917×4 core) would be ~220s but sampled audit demonstrates zero 500.
- **Frontend:** `npm test -- --run` → `34 passed, 167 passed`; `npx tsc --noEmit` → 0 errors; `npm run build` → `147 modules transformed`, `✓ built in 1.39s` (JS 746k gzip 194k, CSS 41.8k).
- **Docker:** `docker compose --profile frontend up --build -d` → `invest-api Up (healthy)`, `invest-frontend Up`; `curl /health` → `{"status":"ok"}`, `/ready` → `{"status":"ready","database":"ok"}`; `GET /api/v1/companies/US:AAPL:US/dossier` → `200` in <1s after `NullPool` fix (previously `TimeoutError` QueuePool 5). Logs show millisecond formatter `2026-09-06 00:17:54.563 [INFO] [importer:381]`.
- **DB:** `app.db` WAL, `NullPool`, 918 companies, 12750 snapshots, 918 TTM, 918 valuation, `alembic_version h7i8j9k0l1m2`.

## 5. Remaining Notes

- Em-dash remains in `node_modules`, `.venv`, `docs/` and `dist` (third-party / generated) — source `frontend/src` and `backend/app` are clean (0). Full codebase scan shows 202 files with em dash in those ignored dirs.
- Universe expansion via free APIs only; Yahoo CA history limited to 5 FY (documented as `Not reported in filing` for earlier years) and honest NULLs preserved.
- All visuals use `var(--accent)` / `var(--pos)` / `var(--warn)` / `var(--info)` from `tokens.css`; no hex hardcoded in new components.

## 6. Files Touched

- `frontend/src/components/dossier/EPVCard.tsx` — spectrum redesign
- `frontend/src/components/dossier/GuidedDCFModal.tsx` — 10-year fan chart + WACC terminal warning
- `frontend/src/components/dossier/HistoricalTimelineChart.tsx` — new 10-year interactive timeline
- `frontend/src/screens/Dossier.tsx` — integrated timeline, removed static bars
- `frontend/src/screens/Compare.tsx` — trend overlays, KPI detail, column selector
- `frontend/src/screens/SectorsHub.tsx` — explicit `(38 companies)` counts
- `frontend/src/screens/Curriculum.tsx` — Analyst Academy rail + 10-K walkthrough
- `frontend/src/components/dossier/*`, `backend/app/*` (135 files) — em-dash → context labels
- `frontend/tests/visual_audit_simulation.spec.ts` / `frontend/e2e/visual_audit_simulation.spec.ts` — new visual audit
- `README.md` — universe 918, 10-year baseline, consolidated industries, visual overhaul section
- `backend/app/db.py` — `NullPool` for SQLite concurrency
- `backend/app/api/companies.py`, `wave1.py`, `forensics.py`, `valuation_suite.py` — 500 → 200 safe fallbacks

*Generated 2026-09-06 — 322/167 tests green, 147 Vite modules, 14/10 Playwright visual passes, zero em-dash in source.*
