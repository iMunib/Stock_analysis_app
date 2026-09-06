# Wave 1 Sprint Report: Visibility of What Exists (21 User Stories)

**Date**: 2026-09-05  
**Scope**: 21 User Stories across Epics 1–4 (Phase 1 Implementation)  
**Status**: APPROVED & VERIFIED  

---

## Executive Summary

Wave 1 implementation activates radical transparency, methodology explainability, empirical base-rate humility, data provenance inspection, and pre-mortem counter-weight analysis across the platform's 720-company universe.

A rigorous, skeptical review of the initial attempt revealed critical regressions against frozen contracts (including invented financial figures, incomplete ratio coverage, and broken Canadian regulatory filings). These defects have been thoroughly dismantled, mathematically reconstructed using authentic database statements, verified with a comprehensive automated test battery, and validated through static type-checking.

---

## 1. Audit of Prior Attempt: Root Cause Analysis

The review identified four major deficiencies in the prior implementation:

### Issue 1: Invented Financial Numbers in Pillar Drilldown (Violation of Rule #3)
- **Input**: User clicks Growth pillar drilldown or Risk pillar drilldown on any company (`/api/v1/companies/{id}/pillar-drilldown`).
- **Expected**: Computed CAGR from actual financial snapshots, authentic Piotroski F-Score breakdown from `compute_piotroski_f_score`, and authentic standard deviation of operating earnings.
- **Actual**: Growth sub-metrics returned hardcoded static CAGRs (Revenue 12.4%, Operating Income 14.1%, FCF 11.8%) and hardcoded base FY2020 amounts (0.0) for every company. Piotroski F-score was hardcoded to 8.0/10 with static fake checks, and earnings volatility was hardcoded to 7.5 (CV = 0.18).
- **Root Cause**: `backend/app/services/pillar_drilldown.py` substituted static mock dictionary literals instead of querying the company's multi-year `FinancialSnapshot` time series and invoking the forensic scoring engines.
- **Fix**: Replaced hardcoded values with dynamic calculations:
  - Multi-year geometric compound annual growth rates computed across 3–5 year statement history.
  - Authentic Piotroski F-score decomposition via `compute_piotroski_f_score` mapping test outcomes and statement periods.
  - Authentic standard deviation and coefficient of variation computed over operating income history.
  - Corrected `_format_money` bug where non-percentage revenue amounts evaluated as 0.0 were erroneously rendered as "0.0%".

### Issue 2: Incomplete Ratio Calculation Inspector (US-0460)
- **Input**: User clicks "Inspect Calculation" on ROIC, P/B, EV/EBITDA, Current Ratio, Interest Coverage, Gross Margin, or Net Debt / FCF.
- **Expected**: Exact formula, audited numerator, audited denominator, currency tags, as-of dates, and step-by-step arithmetic resolution.
- **Actual**: Route returned 404 for 7 out of 12 platform ratios. Provider-only annual rows caused price and valuation multiples (`pb_calc`, `pe_calc`, `ev_to_ebitda_calc`) to resolve as NULL because traded prices live in seed snapshots.
- **Root Cause**: `backend/app/services/ratio_inspector.py` only handled 5 ratios (`roe`, `roa`, `pe`, `fcf`, `fcf_margin`) and lacked fallback to the seed snapshot for market-capitalization and price fields.
- **Fix**: Implemented complete arithmetic decomposition handlers for all 12 key financial ratios (`roe`, `roa`, `roic`, `pe`, `pb`, `ev_ebitda`, `fcf`, `fcf_margin`, `gross_margin`, `current_ratio`, `interest_coverage`, `net_debt_fcf`) with fallback to `seed_snap` for market-traded multiples.

### Issue 3: Inappropriate EDGAR Links for Canadian Equities (SEDAR+ Routing)
- **Input**: Canadian stock (`CA:RY:TSX`, `CA:SHOP:TSX`, `CAD` currency) inspected in `PillarDrilldownModal` or `RatioInspectorModal`.
- **Expected**: Canadian regulatory filings route to SEDAR+ (`https://www.sedarplus.ca/csa-party/records/document.html`).
- **Actual**: Generated SEC EDGAR search URLs pointing to 0 results on `sec.gov` for domestic Canadian issuers.
- **Root Cause**: `_sec_url` functions in backend services defaulted to `https://www.sec.gov/edgar/searchedgar/companysearch` regardless of issuer country, and frontend modal templates hardcoded `"EDGAR ↗"`.
- **Fix**: Updated backend URL generators to detect Canadian equities (`cur == 'CAD'`, `company_id.startswith('CA:')`, `':TSX'`, or `.TO` tickers) and route to SEDAR+. Frontend modals dynamically render `SEDAR+ ↗` with appropriate accessibility titles.

### Issue 4: Modal Keyboard Accessibility (WCAG 2.1 & Prefers-Reduced-Motion)
- **Input**: User presses `Escape` while inspecting any Wave 1 modal (`PillarDrilldownModal`, `CoveragePenaltyModal`, `RatioInspectorModal`).
- **Expected**: Modal dismisses immediately regardless of where focus resides in the DOM.
- **Actual**: `onKeyDown` was bound only to the outer backdrop element, failing to dismiss if focus was inside modal content or buttons.
- **Root Cause**: Missing global `keydown` event listener attached to `window`.
- **Fix**: Added `useEffect` window keydown listener to all 3 modals, ensuring standard keyboard dismissal.

---

## 2. Requirements Coverage (21 User Stories)

| Story ID | Epic | Feature Description | Implementation Location | Status |
|---|:---:|---|---|:---:|
| **US-0051** | Epic 1 | Exact Formulas, Weights & Sub-Metric Breakdown | `PillarDrilldownModal.tsx`, `pillar_drilldown.py` | VERIFIED |
| **US-0052** | Epic 1 | Dynamic 1-Line Pillar Interpretation | `Dossier.tsx`, `pillar_drilldown.py` | VERIFIED |
| **US-0056** | Epic 1 | Line Items & SEC/SEDAR+ Provenance Links | `PillarDrilldownModal.tsx`, `pillar_drilldown.py` | VERIFIED |
| **US-0064** | Epic 1 | Pillar Disagreement Radar (Tensions) | `TensionCallout.tsx`, `Dossier.tsx` | VERIFIED |
| **US-0067** | Epic 1 | Sector Peer Median Marker Overlays | `ScoreBar` in `bars.tsx`, ARIA labels | VERIFIED |
| **US-0080** | Epic 1 | Risk Pillar Decomposed Into 3 Sub-Bars | `PillarDrilldownModal.tsx`, `pillar_drilldown.py` | VERIFIED |
| **US-0083** | Epic 1 | Per-Pillar Missing Data Explainer FAQ | `PillarDrilldownModal.tsx` (Bank & General FAQ) | VERIFIED |
| **US-0100** | Epic 1 | Interactive Coverage Penalty Visualizer | `CoveragePenaltyModal.tsx`, `Dossier.tsx` | VERIFIED |
| **US-0060** | Epic 2 | Macro Regime Sensitivity Notes on Factors | `/api/v1/factors/evidence`, `factor_evidence.py` | VERIFIED |
| **US-0063** | Epic 2 | Model Alpha Decay Dates Out-of-Sample | `AltmanZScoreCard.tsx`, `BeneishMatrix.tsx` | VERIFIED |
| **US-0676** | Epic 2 | Bessembinder Empirical Base-Rate Panel | `ExecutiveCockpit.tsx`, `factor_evidence.py` | VERIFIED |
| **US-0905** | Epic 2 | Immutable Academic Study Date-Stamps | Altman (1968), Beneish (1999), Piotroski (2000) cards | VERIFIED |
| **US-0919** | Epic 2 | Canonical Factor Sharpe Ratios & Premiums | `/api/v1/factors/evidence`, `FactorEvidenceOut` | VERIFIED |
| **US-0947** | Epic 2 | Model False-Positive Rate Disclosures | `AltmanZScoreCard.tsx`, `BeneishMatrix.tsx` | VERIFIED |
| **US-0453** | Epic 3 | Direct Metric Links to SEC/SEDAR+ Filings | `pillar_drilldown.py`, `ratio_inspector.py` | VERIFIED |
| **US-0460** | Epic 3 | 12-Ratio Arithmetic Inspector Modal | `RatioInspectorModal.tsx`, `ratio_inspector.py` | VERIFIED |
| **US-0466** | Epic 3 | Universe Data Coverage & Health Matrix | `/api/v1/coverage/health`, `CoverageHealth.tsx` | VERIFIED |
| **US-0481** | Epic 3 | Prominent As-Of Vintage Timestamps | `Dossier.tsx`, `Screener.tsx` header/footer | VERIFIED |
| **US-0074** | Epic 4 | Auto-Generated Bear Case Narrative | `/api/v1/companies/{id}/bear-case`, `bear_case_engine.py` | VERIFIED |
| **US-0705** | Epic 4 | Structural Equal-Billing for Bear Signals | `DecisionBullets.tsx` (identical layout & card weight) | VERIFIED |
| **US-0725** | Epic 4 | Pre-Mortem Thesis Challenge Prompt | `ThesisNotepad.tsx` (50% catastrophic drawdown prompt) | VERIFIED |

---

## 3. Verification Battery

### Automated Backend Tests (Pytest)
```
C:\Python313\python.exe -m pytest tests/ -q
245 passed, 10 warnings in 40.80s
```
- Includes 11 targeted Wave 1 verification scenarios covering:
  - Canadian company SEDAR+ routing and authentic CAGR calculations (`CA:RY:TSX`).
  - Bank stock regulatory disclosures and missing data FAQ (`US:JPM:US`).
  - Arithmetic decomposition of all 12 platform ratios.
  - Universe coverage and health audit endpoints.
  - Bear case synthesis and factor evidence catalog.

### Automated Frontend Tests (Vitest)
```
npm test -- --run
Test Files  26 passed (26)
Tests       133 passed (133)
Duration    3.72s
```
- Includes modal keyboard accessibility tests (Escape key dismissal).
- Includes SEDAR+ Canadian filing link verification.
- Includes pure SVG ScoreBar median marker line and ARIA label tests.
- Includes equal-billing Bull/Bear panel render tests.

### Production Build Verification (Vite + TypeScript)
```
npm run build
✓ 123 modules transformed.
dist/index.html                   1.50 kB │ gzip:   0.77 kB
dist/assets/index-D0q91j5p.css   40.36 kB │ gzip:   8.49 kB
dist/assets/index-_Ih_2toE.js   573.05 kB │ gzip: 155.88 kB
✓ built in 1.34s
```
Zero TypeScript errors, zero compilation warnings.

---

## 4. Frozen Contracts Compliance Audit

1. **Zero chart npm libraries**: All visualizers (`ScoreBar`, `PillarRadar`, `CompositeGauge`, `Sparkline`, `CashFlowWaterfall`) use pure SVG primitives and CSS tokens (`tokens.css`).
2. **Strict Currency Segregation**: CAD and USD are segregated in database and UI representations. Cross-border comparisons operate exclusively on unitless ratios.
3. **Locked Composite Weights**: 0.30 Quality / 0.25 Value / 0.25 Growth / 0.20 Risk frozen in code without user-editable sliders.
4. **Seed Immutability**: `seed/Sector_Financials_Final_Owner.xlsx` was verified untouched via Git audit.
5. **Honest Missing Data**: Zero invented numbers; missing inputs emit NULL + explicit explanatory FAQ flags.
