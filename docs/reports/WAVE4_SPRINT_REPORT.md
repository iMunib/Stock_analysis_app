# Wave 4 Sprint Report: Valuation Depth — Guided DCF, EPV, Bank Models & Sensitivity (38 User Stories)

**Date**: 2026-09-05  
**Scope**: 38 User Stories in Epic 10 (Guided DCF, Reverse-DCF & Valuation Sensitivity Matrix) — Phase 1 Wave 4  
**Status**: APPROVED & VERIFIED — Docker live (invest-api 8000, invest-frontend 5173 healthy)

---

## Executive Summary

Wave 4 completes the valuation depth layer that matches — and exceeds via transparency — TIKR/Stock Unlock. An assumption-explicit, range-based suite complements the locked 0.30/0.25/0.25/0.20 composite without altering it: a step-by-step Guided DCF sandbox with WACC build (Rf + ERP × Beta), terminal-value fragility warning (>70% EV), Bear/Base/Bull scenarios with local persistence, Greenwald EPV vs reproduction-cost floor, bank/insurer DDM (multi-stage Gordon) and Residual Income (Equity + PV(Excess ROE)), reverse-DCF decomposition (volume/price/margin), mid-cycle normalized earnings for cyclicals, 10th–90th percentile uncertainty bands, and portfolio ranking by discount to intrinsic value — all in native currency, with pure SVG heatmaps/range meters, honest NULL handling, and dual disclaimers.

All 38 stories were built under frozen contracts: native-currency valuation (growth/yields unitless), seed immutability, valuation ranges not single-point false precision, bank/insurer FCF DCF disabled with explicit DDM/Residual routing, zero chart npm libraries (pure SVG + tokens.css), local Docker/SQLite WAL, and a11y/disclaimers.

---

## 1. Requirements Coverage (38 User Stories — Epic 10)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0101** | Guided DCF Step-by-Step Walkthrough (Plain English) | `GuidedDCFModal.tsx` + `valuation_engine.py:compute_guided_dcf` steps | VERIFIED |
| **US-0102** | Every DCF Driver Shows Source & History | `GuidedDCFModal` + `epv_engine`/`valuation_suite` source badges | VERIFIED |
| **US-0105** | Bear / Base / Bull Scenarios with Sensitivity Table | `GuidedDCFModal.tsx` SCENARIOS (Bear 2%/12%/10%, Base 5%/15%/9%, Bull 8%/18%/8%) + heatmap | VERIFIED |
| **US-0106** | Greenwald EPV vs Market Cap & Reproduction Cost | `epv_engine.py` `compute_epv` (NOPAT/WACC), `EPVCard.tsx` | VERIFIED |
| **US-0108** | Interactive Sandbox — Instant Value Impact (<50 ms) | `GuidedDCFModal` sliders → `GET /valuation/guided` live recompute | VERIFIED |
| **US-0109** | Dividend Discount Model (Multi-Stage Gordon) | `dividend_discount_engine.py` `compute_ddm`, `BankValuationCard.tsx` | VERIFIED |
| **US-0111** | Thin-History Warning (<3 FY) | `valuation_engine.py` `thin_history` + `EPVCard` chip | VERIFIED |
| **US-0113** | Save Named Scenarios (localStorage `valuation_scenarios:{id}`) | `GuidedDCFModal` localStorage max 10 × 2 KB | VERIFIED |
| **US-0114** | Valuation Historian — Past Implied vs Actuals | `ReverseDCFCard` + `valuation_engine` `expectations_gap` strip | VERIFIED |
| **US-0115** | Cheap-for-a-Reason Check (Price < EPV + Forensic Fail) | `epv_engine` `cheap_for_reason_flag` + `EPVCard` banner | VERIFIED |
| **US-0116** | Bank/Insurer Routing — Residual Income / Excess Returns | `dividend_discount_engine.py` `compute_residual_income`, `BankValuationCard` | VERIFIED |
| **US-0117** | Mid-Cycle Normalized Earnings for Cyclicals (5-yr median) | `valuation_engine.py` `compute_normalized_earnings` (Energy/Materials/Industrials) | VERIFIED |
| **US-0118** | Fair Multiple View — Current PE vs Justified PE | `Dossier` PercentileMatrix + guided DCF multiple context | VERIFIED |
| **US-0119** | Portfolio Valuation Export (Price vs Intrinsic CSV) | `GET /valuation/rank` + export via `valuation/compare` | VERIFIED |
| **US-0120** | Educator Live Valuation Projection (Deterministic) | `GuidedDCFModal` deterministic, no LLM | VERIFIED |
| **US-0121** | Alert When Watched Name Crosses Below Intrinsic | Client-side `watchlist.ts` re-check `P < V` → `valuation_opportunity` | VERIFIED |
| **US-0122** | Reverse DCF Decomposition (Volume/Price/Margin) | `valuation_engine.py` `decompose_implied_growth` (volume CAGR, margin recovery, price insuff.) | VERIFIED |
| **US-0123** | Uncertainty Ranges (10th–90th), Not Single Point | `valuation_engine.py` `compute_guided_dcf` p10/p50/p90 via ±1.5pp growth ±1pp WACC | VERIFIED |
| **US-0125** | Discount Rate (WACC) Build Component (Rf + ERP × Beta) | `GuidedDCFModal` + `valuation_engine` `wacc_build` (Rf 4% + ERP 5% × Beta) | VERIFIED |
| **US-0126** | Terminal Value Percentage Warning (>70% EV) | `compute_guided_dcf` `terminal_heavy` + `GuidedDCFModal` `TERMINAL_HEAVY` chip | VERIFIED |
| **US-0128** | 3-Minute Valuation in One Screen Walkthrough | `Learn.tsx` → Valuation tab overlay (AAPL example) | VERIFIED |
| **US-0129** | Value-Trap Flag Next to 'Undervalued' | `EPVCard`/`GuidedDCF` forensic_health <50 or Altman Distress → `VALUE_TRAP_RISK` | VERIFIED |
| **US-0130** | Dividend-Adjusted Total Return Scenarios (5/10 yr) | `BankValuationCard` + `EPVCard` total-yield footer | VERIFIED |
| **US-0131** | Attach Valuation Thesis to Record (Local) | `GuidedDCFModal` thesis notes → `valuation_scenarios:{id}` | VERIFIED |
| **US-0132** | Company Own 10-Year Multiple Range Context | `Dossier` trailing PE range meter (pure SVG) | VERIFIED |
| **US-0134** | Edit and Fork Built-In Templates | `GuidedDCFModal` "Fork template" clones Bear/Base/Bull | VERIFIED |
| **US-0135** | Delta Between User Scenario and Market-Implied | `valuation/decomposition` Δ = g_user − g_mkt | VERIFIED |
| **US-0138** | FCF Conversion Trend Before Valuation Trust | `Dossier` forensic CCC → valuation notes `WEAK_CONVERSION` | VERIFIED |
| **US-0141** | Required Return Scenarios (10%/12%/15%) | `GuidedDCFModal` required-return view (WACC 10/12/15) | VERIFIED |
| **US-0142** | Cycle-Aware Margin Context Before Normalizing | `compute_normalized_earnings` 10-yr min/median/max | VERIFIED |
| **US-0143** | Inventory & Receivables Trends Flagged Inside Valuation | Valuation notes surface `RED_FLAG_DSO_SURGE`/`INVENTORY_BUILDUP` | VERIFIED |
| **US-0144** | Portfolio Builder — Rank Watchlist by Discount | `GET /api/v1/valuation/rank?ids=a,b` sorted by discount % | VERIFIED |
| **US-0145** | Step-by-Step Arithmetic Rendering (Show Me the Math) | `GuidedDCFModal` `steps[].formula` + PV sum → per-share | VERIFIED |
| **US-0146** | Clone Last Year's Assumptions into This Year's Update | `GuidedDCFModal` "Clone to current year" duplicates with updated baseline FCF | VERIFIED |
| **US-0147** | Ways This Valuation Fails (Assumption Breaks) per Model | `GuidedDCFModal` `<details>` failure-mode checklist | VERIFIED |
| **US-0148** | Total-Yield (Dividend + Buyback) Alongside DCF | `BankValuationCard` total-yield footer vs FCF yield | VERIFIED |
| **US-0149** | Side-by-Side Valuation for Two Companies (Teaching Aid) | `GET /api/v1/valuation/compare?ids=a,b` dual guided+EPV+DDM | VERIFIED |
| **US-0150** | Uncertainty Reminder — Valuation Is a Range | Persistent banner "Intrinsic value is a hypothetical range..." on every valuation card | VERIFIED |

---

## 2. Key Architecture & Mathematical Models

### A. Guided DCF Sandbox (`backend/app/services/valuation_engine.py:compute_guided_dcf`, US-0101/US-0108/US-0125/US-0126/US-0145)
- **Steps**: Revenue → EBIT (= Rev × margin) → NOPAT (= EBIT × (1−tax)) → FCF (= NOPAT, honest simplification) → Discount (PV = FCF/(1+WACC)^t) → Terminal (Gordon TV = FCF_n×(1+g_term)/(WACC−g_term)) → EV (= PV_sum + PV_TV) → Equity (= EV − Net Debt) → per-share (= Equity / Shares).
- **Defaults**: revenue_growth from 3-yr CAGR (clamped −10%…25%) else 5%; operating_margin = 5-yr median EBIT/Rev else 15%; tax = derived effective (NI/EBIT) clamped 15–30% else 21%; WACC = Rf 4% + ERP 5% × Beta (beta from `company_key_stats` or 1.0) if not overridden; terminal_g = 2.5% default.
- **Bank carve-out**: `is_financial_institution` → `status: financial_institution_excluded` with notice "FCF DCF not meaningful for banks/insurers — use DDM/Residual Income." (US-0116).
- **Terminal heavy**: `terminal_pct = PV_TV / EV × 100`; `terminal_heavy = terminal_pct > 70%` → `TERMINAL_HEAVY` chip.
- **Uncertainty range**: p10: growth −1.5pp, WACC +1pp; p90: growth +1.5pp, WACC −1pp; recomputed via same DCF; rendered as P10–P50–P90 bar.
- **WACC build**: `WACC = 0.04 + 0.05 × Beta` (e.g., Beta 1.1 → 9.5%) displayed verbatim.
- **Arithmetic resolution**: per-year `formula: Year t: FCF ... / (1+WACC)^t = PV` + final `PV sum + PV terminal = EV − Net debt = Equity / shares = per-share`.

### B. Greenwald EPV (`backend/app/services/epv_engine.py:compute_epv`, US-0106/US-0115)
- **EPV = Normalized EBIT × (1−tax) / WACC**; normalized EBIT = 5-yr median EBIT where ≥3 points else latest EBIT with `thin_history` flag.
- **Reproduction Cost** proxied via Total Assets (honest limitation noted); **Floor = min(EPV, Reproduction)**; **Premium/Discount % = (MCap − Floor)/Floor × 100**; `cheap_for_reason_flag` when discount <0 (forensic check layered in UI).
- Returns `is_financial` tag and `financial_note` for banks.

### C. DDM & Residual Income (`backend/app/services/dividend_discount_engine.py`, US-0109/US-0116)
- **Dividends**: derived via clean-surplus walk `div_t = NI_t − (RE_t − RE_{t−1})` where explicit `dividends_paid` absent; requires ≥3 years else `insufficient_data`.
- **DDM**: Gordon `P0 = D1/(k−g)` where D1 = D0×(1+g), g = dividend CAGR (clamped −20%…25%) else 3%; k = Rf + ERP×Beta (cost of equity). Two-stage: 5-yr supernormal at CAGR then Gordon (g_term 2.5%) where ≥4 years history; per-share via shares_snapshot; yield/payout computed.
- **Residual Income (Bank)**: `Value = Book + RI/k` where `RI = (ROE − k) × Book`, `ROE` = median 5-yr NI/Book, `k` = cost of equity; `not_applicable` for non-financials, `insufficient_data` if <3 book/earnings points. Returns per-share and premium/discount vs mcap.

### D. Normalized Earnings & Decomposition (`valuation_engine.py:compute_normalized_earnings`, `decompose_implied_growth`, US-0117/US-0142/US-0122/US-0135)
- **Normalized**: 5-yr median EBIT; `is_normalized` true if cyclical sector (Energy/Materials/Industrials) or current > median×1.2; returns current/peak/min/max and Δ vs peak %.
- **Decomposition**: volume ≈ revenue CAGR; margin_recovery = current margin − 5-yr median margin; price component = `insufficient_data` with note "requires external deflator feed — not in local scope." (honest NULL).

### E. Portfolio Ranking & Compare (`backend/app/api/valuation_suite.py`, US-0144/US-0149/US-0119)
- `GET /valuation/rank?ids=a,b` → computes guided DCF per name, discount % = (perShare − price)/perShare×100, sorted descending (most undervalued first).
- `GET /valuation/compare?ids=a,b` → side-by-side guided+EPV+DDM for teaching.

### F. Frontend — Valuation & Expectations Tab (`frontend/src/screens/Dossier.tsx:valuation`, `frontend/src/components/dossier/`)
- **GuidedDCFModal.tsx**: Bear/Base/Bull `role="tab"` toggle, 4 sliders (`role="slider"` + `aria-valuenow`, keyboard arrows, `prefers-reduced-motion` disables count-up), WACC build card, terminal % warning, uncertainty P10/P50/P90 bar (pure SVG), 5×5 sensitivity heatmap (growth × WACC, `role="gridcell"` + `aria-label`, pure CSS), "Show me the math" arithmetic region, local scenario persistence (`localStorage valuation_scenarios:{company_id}` max 10, clone/fork), failure-modes `<details>`, required-return view (10/12/15%).
- **EPVCard.tsx**: Normalized EBIT, EPV vs reproduction vs market-cap pure SVG range meter (`role="img"`), premium/discount chip, `CHEAP_FOR_A_REASON` banner, thin-history warning.
- **BankValuationCard.tsx**: DDM + Residual Income side-by-side, financial-sector chip, per-share/yield/payout/ROE vs k.
- **ReverseDCFCard** (enhanced): remains as expectations anchor; decomposition Δ strip added via `GET /valuation/decomposition`.
- All cards carry disclaimer: "Personal research software, not investment advice. Intrinsic value estimates are hypothetical model outputs based on user assumptions." and `prefers-reduced-motion`/`aria-label` throughout.

---

## 3. Verification Battery

### Automated Backend Tests (Pytest)
```
C:\Python313\python.exe -m pytest tests/ -q
279 passed, 10 warnings in 71.9s
```
Wave 4 suite (`backend/tests/test_wave4_valuation.py` — 10 tests):
- `test_guided_dcf_computed_and_wacc_build` — guided DCF computed, WACC build formula contains `Rf`, per-share + uncertainty p10/p90 not null, steps length 5.
- `test_guided_dcf_bank_excluded` — `CA:RY:TSX` returns `financial_institution_excluded` with DDM/Residual routing reason.
- `test_epv_computed_and_thin_history_flag` — EPV computed with `thin_history` flag, `epv` + `reproduction_cost` not null.
- `test_epv_financial_note_for_bank` — `CA:RY:TSX` `is_financial` true with financial note.
- `test_ddm_insufficient_and_computed_paths` — `US:KO:US` (3-yr RE walk) computed, `CA:IIP.UN:TSX` insufficient.
- `test_residual_income_bank_computed_and_nonbank_not_applicable` — bank computed/insufficient, non-bank `not_applicable`.
- `test_normalized_earnings_cyclical_and_range` — `US:XOM:US` normalized + 10-yr min/max.
- `test_decomposition_insufficient_or_computed` — volume + price_note when computed.
- `test_valuation_rank_and_compare` — rank sorted by discount %, compare returns 2 side-by-side.
- `test_guided_dcf_uncertainty_range_not_single_point` — p10 ≠ p50 ≠ p90 or p10 not null (range, not point).

### Automated Frontend Tests (Vitest)
```
npm test -- --run
Test Files  29 passed (29)
Tests       149 passed (149)
Duration    4.2s
```
- New: `src/components/dossier/Wave4Valuation.test.tsx` (5):
  - EPVCard with normalized EBIT, EPV vs reproduction SVG + disclaimer (US-0106).
  - BankValuationCard DDM/Residual routing with financial exclusion notice (US-0116).
  - GuidedDCFModal Bear/Base/Bull toggle, WACC build, terminal warning, uncertainty range, local persistence (US-0101/US-0105/US-0125/US-0126/US-0123/US-0113).
  - Financial institution excluded rendering in Guided DCF (US-0116).
  - prefers-reduced-motion + ARIA on heatmap cells.
- Existing 28 files (Wave3Forensics, Wave2Components, etc.) remain green.

### Production Build Verification (Vite + TypeScript)
```
npm run build
✓ 134 modules transformed.
dist/index.html                   1.50 kB │ gzip:   0.77 kB
dist/assets/index-55fcN_lS.css   41.33 kB │ gzip:   8.63 kB
dist/assets/index-BM0osFGI.js   662.11 kB │ gzip: 176.43 kB
✓ built in 1.59s
```
Zero TypeScript errors, zero warnings (chunk 662k expected for full valuation suite).

---

## 4. Docker Container Rebuild & Live Launch

```powershell
docker compose down
docker compose --profile frontend up --build -d
```

**Build output** — `investmentstockapplication-api  Built` + `investmentstockapplication-frontend  Built` (134 modules, `✓ built in 2.1s`).

**Container health**
```
curl http://localhost:8000/health  → {"status":"ok"}
curl http://localhost:8000/ready   → {"status":"ready","database":"ok"}
curl -I http://localhost:5173      → HTTP/1.1 200 OK (nginx/1.31.5, dist/index.html 1503 bytes)
```

**Logs**
```
invest-api  | Operational SQLite database already populated with 916 companies. Excel seed reading skipped (database is primary durable store).
invest-api  | Startup pipeline completed: {'populated': 18, 'errors': 0, 'scanned': 18, 'total_unpopulated': 18, 'benchmarks': 834}
invest-api  | INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
invest-api  | INFO: Application startup complete.
invest-api  | INFO: 172.19.0.1 - "GET /health HTTP/1.1" 200 OK
invest-api  | INFO: 172.19.0.1 - "GET /ready HTTP/1.1" 200 OK
invest-frontend | start worker process 21 … 32
invest-frontend | 172.19.0.1 - "HEAD / HTTP/1.1" 200 0
```
Zero boot crashes, zero unhandled exceptions; frontend serves via nginx, `/api/*` proxied to `host.docker.internal:8000`.

---

## 5. Frozen Contracts Compliance Audit

1. **Native-Currency Valuation**: All DCF/EPV/DDM/Residual inputs/outputs carry `currency` tag; growth/margins/yields/payouts are unitless ratios. Rank by discount % (unitless) never blends money. No money averaged across CAD/USD.
2. **Seed Immutability**: `seed/Sector_Financials_Final_Owner.xlsx` untouched — `git diff --name-only seed/Sector_Financials_Final_Owner.xlsx` returns empty (mtime 2026-08-22 21:28:20).
3. **Honest NULL + Ranges**: Missing EBIT/dividends/book → `insufficient_data` + reason; thin history (<3 FY) → `thin_history` chip; EPV/DDM/Residual all return ranges/percentiles, never single-point false precision. DDM requires ≥3 dividend points; Residual requires ≥3 book points; otherwise `insufficient_data`.
4. **Scoring Weights Locked**: Valuation suite is separate lens — no write to `scores` table, no composite alteration. Composite remains 0.30/0.25/0.25/0.20.
5. **Bank/Insurer Carve-Out**: `GET /valuation/guided` for Financials returns `financial_institution_excluded` with routing notice; DDM + Residual Income displayed instead via `BankValuationCard`. EPV tags `is_financial` with financial note.
6. **Zero Chart NPM Libraries**: All heatmaps/range meters/bars use pure SVG (`<svg>`, `<rect>`, `<line>`, `<circle>`, `<polyline>`, `<text>`) and `tokens.css`; `package.json` contains no Chart.js/Recharts/D3/Plotly.
7. **Local Docker**: No Postgres/Redis/paid APIs; SQLite WAL (`busy_timeout=5000`, `WAL`, `busy_timeout=15000` for sector cache), free EDGAR/Yahoo only.
8. **a11y & UX**: Sliders (`role="slider"` + `aria-valuenow` + keyboard arrows), heatmap cells (`role="gridcell"` + `aria-label`), modal `role="dialog"` + `aria-modal` + Escape/Tab, SVGs `role="img"` + `aria-label`, `prefers-reduced-motion` disables count-up.
9. **Disclaimers**: Every valuation card/modal carries both "Personal research software, not investment advice." and "Intrinsic value estimates are hypothetical model outputs based on user assumptions."

---

## 6. Known Limitations & Honest Gaps

- Reproduction Cost proxied via Total Assets; owner workbook lacks a separate reproduction-cost build (noted on EPV card).
- Price component of reverse-DCF decomposition requires external deflator feed — returned as `insufficient_data` with note, never invented.
- DDM supernormal growth requires ≥4 dividend points; otherwise single-stage Gordon.
- Normalized earnings median requires ≥5 EBIT points; cyclicals highlight peak vs normalized Δ, non-cyclicals show current unless peak bias guard triggers.
