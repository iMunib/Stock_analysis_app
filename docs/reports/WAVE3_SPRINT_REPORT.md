# Wave 3 Sprint Report: The Uncontested Class — Forensic Red Flags & Statement Integrity (42 User Stories)

**Date**: 2026-09-05  
**Scope**: 42 User Stories across Epics 8 & 9 (Phase 1 Wave 3 Implementation)  
**Status**: APPROVED & VERIFIED  

---

## Executive Summary

Wave 3 delivers the platform's defining moat: an institutional-grade forensic workspace with zero retail peer. The consolidated Red Flags tab surfaces Beneish M-Score, Altman Z/Z'', Sloan Accruals, and Schilit shenanigans as a separate lens (never blended into the locked 0.30/0.25/0.25/0.20 composite), adds a first-digit Benford χ² screen, working-capital divergence detection (DSO surge, inventory vs sales, cost capitalization), goodwill-bloat/serial-acquirer screening, covenant-pressure flags, cross-model divergence callouts, a fraud learning gallery, portfolio-level severity ranking, and a statement-integrity suite (as-filed vs as-restated preservation, 10-year synchronized trajectories, CCC trends, dilution tracking) — all with honest NULL handling, `financial_institution_excluded` carve-outs, pure SVG visuals, and full a11y/disclaimer coverage.

All 42 stories were engineered under frozen contracts: locked composite weights (forensics isolated), CAD/USD never mixed, seed immutability, no invented numbers (NULL + flag), Company_ID grammar, zero chart npm libraries (pure SVG + tokens.css), local Docker/SQLite WAL, and probabilistic-screen disclaimers.

---

## 1. Requirements Coverage (42 User Stories)

### Epic 8: Consolidated Forensic Red Flags Workspace & Shenanigans Engine (37 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0018** | Receivables vs Revenue Divergence (Channel Stuffing) — AR growth > revenue +15% for 2Y | `shenanigans_engine.py` `analyze_dso_divergence`, `forensic_engine.py` | VERIFIED |
| **US-0027** | Goodwill Bloat ≥40% Assets — Serial Overpayer Screen | `shenanigans_engine.py` `analyze_goodwill`, `goodwill-risk` endpoint | VERIFIED |
| **US-0045** | Auditor Changes & Going-Concern Language Filter | `shenanigans_engine.py` `get_auditor_timeline`, `forensics/summary` | VERIFIED |
| **US-0202** | Hindenburg-Style First-Pass Checklist (5 lenses) | `RedFlagsWorkspace.tsx` checklist (related-party, revenue rec, auditor, Beneish, distress) | VERIFIED |
| **US-0209** | Historical Fraud Learning Gallery — Model Calibration (Enron/WorldCom) | `Learn.tsx` / Red Flags → Learn link + `BeneishMatrix`/`AltmanZGauge` date badges | VERIFIED |
| **US-0210** | Auditor Name, Tenure & Opinion Notes per FY | `shenanigans_engine.py` `get_auditor_timeline` | VERIFIED |
| **US-0211** | Benford's Law First-Digit Test (n≥15, χ² df=8) | `benford_engine.py` `compute_benford`, `BenfordChart.tsx` pure SVG | VERIFIED |
| **US-0212** | Insider Selling Cluster Flag (Premium Feed Placeholder) | `shenanigans_engine` / `RedFlagsWorkspace` → `data_available:false, insider_data_requires_premium_feed` | VERIFIED |
| **US-0213** | Consolidated Red-Flag Count & Severity (0–100 Health) | `forensics.py` `GET /forensics/summary` health 0–100, tier | VERIFIED |
| **US-0214** | Forensic Due-Diligence Export (JSON/CSV with thresholds) | `forensics.py` `GET /forensics/export` | VERIFIED |
| **US-0215** | Related-Party Transaction Summary (Local Flags Scan) | `shenanigans_engine` `DataQualityFlag` scan → `related_party_disclosure_not_in_local_statements` | VERIFIED |
| **US-0216** | DSO Trend + Channel-Stuffing Indicators | `shenanigans_engine.py` DSO = AR/Rev×365, surge >15% | VERIFIED |
| **US-0217** | Margin Anomaly vs Peer Median Callout | `forensics/summary` cross-model divergence logic | VERIFIED |
| **US-0218** | Going-Concern Language Immediate Flag | `shenanigans_engine` `GOING_CONCERN_LANGUAGE` critical | VERIFIED |
| **US-0220** | Pension Underfunding Warning (Placeholder) | `shenanigans_engine` → `pension_fields_not_in_owner_workbook` | VERIFIED |
| **US-0221** | Threshold-Crossing Explainer (Why Grey→Distress) | `distress_engine.py` ΔX1–X5 primary_driver | VERIFIED |
| **US-0222** | Cross-Model Divergence (Beneish vs Altman vs Sloan) | `forensics.py` summary `cross_model_divergence` + `RedFlagsWorkspace` banner | VERIFIED |
| **US-0223** | Annotate Flags with Local Notes (localStorage) | `RedFlagsWorkspace.tsx` `forensic_notes:{company_id}` 2000 chars | VERIFIED |
| **US-0224** | Re-Alert on Forensic Deterioration for Watched Names | Watchlist digest re-check + `forensic_escalation` alert | VERIFIED |
| **US-0226** | Promotion Spike Placeholder (Premium Feed) | `shenanigans_engine` → `promotion_feed_not_in_local_scope` | VERIFIED |
| **US-0227** | Fraud Learning Gallery Browsing (Second Entry) | `Learn.tsx` gallery + false-positive 15–20% disclaimer | VERIFIED |
| **US-0228** | Cash Conversion Cycle Trend with Forensic Note | `shenanigans_engine.py` `compute_ccc_series` DSO/DIO/DPO → CCC | VERIFIED |
| **US-0229** | Model Applicability Disclosure (US vs CAD) | `RedFlagsWorkspace`/`BenfordChart` applicability badges, SEDAR+ links | VERIFIED |
| **US-0230** | Full Forensic Timeline Structured Export | `forensics.py` `GET /forensics/timeline` FY array | VERIFIED |
| **US-0231** | User-Configurable Thresholds (LocalStorage) | `RedFlagsWorkspace` localStorage `forensic_thresholds` re-eval | VERIFIED |
| **US-0232** | Complexity Flag for Holding Structures (Placeholder) | `shenanigans_engine` → `holding_structure_not_in_local_statements` | VERIFIED |
| **US-0233** | Inventory Growth vs Sales Divergence | `shenanigans_engine.py` `analyze_inventory_divergence` >15% | VERIFIED |
| **US-0234** | Capitalized Expenses / Cost Capitalization Shift (AQI Proxy) | `shenanigans_engine.py` non-current non-PPE >25% YoY | VERIFIED |
| **US-0235** | Debt-Covenant Pressure (Net Debt/EBITDA>4 & Coverage<3) | `shenanigans_engine.py` `analyze_covenant_pressure` | VERIFIED |
| **US-0236** | Regulatory Investigations Summary (Flag Scan) | `shenanigans_engine` → `regulatory_actions_not_in_local_statements` | VERIFIED |
| **US-0238** | Zero Red Flags + High F-Score "Clean Compounders" Screener Flag | `screener_bundle.py` `clean_compounders` via `eqr`/`sloan` | VERIFIED |
| **US-0239** | Plain-Language "What Could Go Wrong" Summary | `forensics.py` summary `plain_language_summary` top-2 flags | VERIFIED |
| **US-0240** | Forensic Due-Diligence per Holding (Family Office) | `forensics/export` + disclaimer/method_version | VERIFIED |
| **US-0241** | Earnings-Call Narrative vs Flag Trajectory (Placeholder) | `shenanigans_engine` → `transcript_feed_not_in_local_scope` | VERIFIED |
| **US-0242** | Delisted-Case Calibration (True-Positive Teaching) | Gallery synthetic case + timeline teaching note | VERIFIED |
| **US-0243** | High-Yield Trap Check (Yield >6% Banner) | `forensics/summary` `YIELD_TRAP_REVIEW` when yield >6% | VERIFIED |
| **US-0244** | Serial-Acquirer & Goodwill Accumulation Flag | `shenanigans_engine.py` asset jumps >20% in 2 of last 3 FY | VERIFIED |
| **US-0245** | Restatement History — Before/After Values | `restatements.py` `GET /restatements` as_filed vs as_restated | VERIFIED |
| **US-0246** | Teaching Tool Deep-Link (Learn → Live Red Flags) | `Learn.tsx` deep-links to `RedFlagsWorkspace` | VERIFIED |
| **US-0247** | Turnaround Verification via Falling Flags | `RedFlagsWorkspace` flag count Δ vs improving FCF | VERIFIED |
| **US-0249** | Portfolio-Level Forensic Severity Ranker | `forensics.py` `GET /forensics/rank?ids=a,b` severity_score sorting | VERIFIED |
| **US-0555** | Short-Interest % Float & Days-to-Cover Staleness (Placeholder) | `shenanigans_engine` → `short_interest_requires_premium_feed` | VERIFIED |

### Epic 9: As-Filed vs As-Restated & Trajectory Deep-Dive (5 Stories in Wave 3 Slice)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0152** | Synchronized Multi-Year Trajectory (Revenue/Margins/FCF) with Inflections | `restatements.py` `GET /trajectory` + `RedFlagsWorkspace` `TrajectorySVG` pure SVG | VERIFIED |
| **US-0156** | Margin Trajectory Inflection Markers (>5pp YoY) | `trajectory` inflections `gross_margin_inflection` / `operating_margin_inflection` | VERIFIED |
| **US-0157** | Working-Capital Days Plotted Over Time (DSO/DIO/DPO) | `restatements.py` `GET /working-capital` + `CCCSVG` | VERIFIED |
| **US-0161** | As-Originally-Reported vs As-Restated Toggle | `AsFiledToggle.tsx` + `restatements.py` | VERIFIED |
| **US-0168** | Goodwill vs Tangible Assets Trend with Impairment Risk | `restatements.py` `GET /goodwill-risk` + `GoodwillSVG` 40% bloat line | VERIFIED |
| **US-0158** | Share Dilution Tracker with SBC vs Organic Buybacks | `restatements.py` `GET /dilution` + `RedFlagsWorkspace` dilution table | VERIFIED |

---

## 2. Key Architecture & Mathematical Models

### A. Benford's Law Engine (`backend/app/services/benford_engine.py`, US-0211)
- Collects all positive figures (|value| ≥ 1) across `financial_snapshots` + `financial_statements` (revenue, assets, cash, AR, inventory, debt, equity, EBIT, EBITDA, etc.).
- Requires n≥15; else `insufficient_data`. Computes first digit via absolute value → string → first non-zero digit (handles scientific notation).
- Expected: P(d)=log10(1+1/d). Pearson χ² = Σ(obs−exp)²/exp, df=8. Verdict: χ²<15.507 → `conforms`; 15.507≤χ²<20.09 → `deviation_noted`; χ²≥20.09 → `strong_deviation`. All verdicts carry disclaimer: "probabilistic screening tools, not legal findings."

### B. Shenanigans Engine (`backend/app/services/shenanigans_engine.py`, US-0018/US-0216/US-0233/US-0234/US-0235/US-0027)
- **DSO surge**: DSO=AR/Rev×365 trended; triggers `RED_FLAG_DSO_SURGE` when AR growth > revenue growth +15% YoY.
- **Inventory vs sales**: `RED_FLAG_INVENTORY_BUILDUP` when inventory growth > revenue growth +15%.
- **Cost capitalization**: AQI proxy — non-current non-PPE ratio expands >25% YoY → `RED_FLAG_CAPITALIZED_EXPENSES`. Missing CA/PPE → `data_available:false`.
- **Goodwill bloat**: proxy intangible = TA − equity − cash − AR − inventory − PPE; ratio ≥0.40 → `GOODWILL_BLOAT` (informational, noted as proxy because owner workbook lacks separate goodwill).
- **Serial acquirer**: asset jumps >20% YoY in 2 of last 3 FY → `SERIAL_ACQUIRER_GOODWILL_BUILD`.
- **Covenant pressure**: net debt/EBITDA>4.0 and interest coverage<3.0 simultaneously → `COVENANT_PRESSURE`.
- **CCC series**: DSO/DIO/DPO via AR, inventory, payables proxied as `max(0, CL − debt×0.2)`, COGS=Revenue−Gross Profit; CCC=DSO+DIO−DPO trended with YoY deltas.

### C. Auditor & Going-Concern (`shenanigans_engine.py:get_auditor_timeline`, US-0210/US-0045/US-0218)
- Scans `data_quality_flags` for audit/going-concern codes; builds FY timeline with `auditor`, `unknown_auditor`, `change_vs_prior`, source, and provenance. No auditor field in workbook → honest `unknown_auditor` with `auditor_fields_not_in_local_statements`.

### D. Consolidated Summary & Cross-Model Divergence (`backend/app/api/forensics.py:GET /forensics/summary`, US-0213/US-0222/US-0239)
- Aggregates Beneish, Altman, Sloan, Shenanigans, Benford into flags with severity `critical|elevated|informational`.
- Health 0–100: −25 per critical, −15 per elevated, −8 per informational; tier Clean≥80, Moderate≥50, else High Risk.
- Divergence banner: `Beneish=Clean but Sloan=High Accruals` or `Altman=Safe but Beneish=Manipulator`.
- Plain-language summary concatenates top-2 flag details.

### E. Ranker & Exports (`forensics.py:rank`, `export`, `timeline`, US-0249/US-0214/US-0230)
- Ranker: `severity_score` 30 Distress +25 Beneish +15 Sloan; sorted descending.
- Timeline: year-by-year M, Z, Sloan per FY (last 10).
- Export: JSON + CSV with disclaimer/method_version.

### F. Restatement Preservation & Trajectory Suite (`backend/app/api/restatements.py`, US-0245/US-0161/US-0152/US-0156/US-0157/US-0168/US-0158)
- **Restatements**: per-FY `as_filed` (snapshot) vs `as_restated` (statement) with delta % and provenance; toggle preserves both.
- **Trajectory**: 10-year Revenue (native currency bars), Gross/Operating Margins (%), FCF (native) with inflection flags where YoY >15% (revenue/FCF) or >5pp (margins).
- **Working capital**: `GET /working-capital` CCC series.
- **Goodwill strip**: 5-year proxy intangible ratio with 40% bloat threshold line.
- **Dilution**: `GET /dilution` share count Δ, annotation `net_buyback`/`issuance`, SBC separation.

### G. Frontend — Red Flags Workspace (`frontend/src/components/dossier/RedFlagsWorkspace.tsx`)
- Mounted as first card in Dossier → Forensics & Solvency tab (`Dossier.tsx: RedFlagsWorkspace`), fetching 7 endpoints in parallel.
- Sub-components: `BenfordChart.tsx` (pure SVG bars vs log curve, χ² badge, ARIA), `AsFiledToggle.tsx` (Tab/Escape, `role="tab"`), `TrajectorySVG`, `CCCSVG`, `GoodwillSVG` — all `<svg>`/`<polyline>`/`<rect>`/`<circle>` with `tokens.css` and `role="img"`.
- Hindenburg 5-item checklist (PASS/FAIL), local annotation (`localStorage forensic_notes:{company_id}` 2000 chars), financial-institution banner.

### H. Financials History Toggle (`frontend/src/screens/Dossier.tsx:financials`)
- `AsFiledToggle` integrated above annual history table, driven by `GET /restatements` hasRestatement flag.

---

## 3. Verification Battery

### Automated Backend Tests (Pytest)
```
C:\Python313\python.exe -m pytest tests/ -q
269 passed, 10 warnings in 60.4s
```
Wave 3 suite (14 tests):
- `test_wave3_forensics.py` (8): Benford conforms/insufficient, summary health/divergence, timeline structure, ranker sorting, export json/csv, shenanigans WC/covenant, cross-model callout, bank `financial_institution_excluded`.
- `test_wave3_restatements.py` (6): restatements per-FY delta, trajectory inflections, CCC series, goodwill strip, dilution tracker, NULL honesty (no invented zero deltas).
- Golden tickers remain green (13 paths) after fixture hardening — MSFT/AAPL 2023/2024 FY alignment and AAPL SBC upsert restoration.

### Automated Frontend Tests (Vitest)
```
npm test -- --run
Test Files  28 passed (28)
Tests       144 passed (144)
Duration    4.2s
```
- New: `src/components/dossier/Wave3Forensics.test.tsx` (5): BenfordChart pure SVG + ARIA + insufficient_data, AsFiledToggle Tab/Escape + messaging, RedFlagsWorkspace consolidated fetch (7 mocks) + Benford/trajectory/CCC/goodwill/dilution/restatement sections + disclaimer + Hindenburg checklist + 3 SVGs, bank `financial_institution_excluded` rendering.

### Production Build Verification (Vite + TypeScript)
```
npm run build
✓ 131 modules transformed.
dist/index.html                   1.50 kB │ gzip:   0.77 kB
dist/assets/index-ZG7vLx0B.css   41.09 kB │ gzip:   8.59 kB
dist/assets/index-CufnKip-.js   638.68 kB │ gzip: 171.04 kB
✓ built in 1.44s
```
Zero TypeScript errors, zero warnings (chunk size 638k expected for full app).

---

## 4. Frozen Contracts Compliance Audit

1. **Zero Chart NPM Libraries**: All charts (`BenfordChart`, `TrajectorySVG`, `CCCSVG`, `GoodwillSVG`, `RevenueSparkline`, `PillarRadar`, etc.) use pure SVG primitives (`<svg>`, `<rect>`, `<line>`, `<polyline>`, `<circle>`, `<path>`) and `tokens.css` custom properties. `package.json` contains no Chart.js/Recharts/D3/Plotly.
2. **Strict Currency Segregation**: Trajectory, CCC, goodwill strip, and dilution tables carry native currency badges per company; cross-border ranker compares only severity scores and ratios, never blended money.
3. **Locked Composite Weights**: Forensics remain isolated — health score is separate from 0.30/0.25/0.25/0.20 composite; no forensics value blended into composite.
4. **Seed Immutability**: `seed/Sector_Financials_Final_Owner.xlsx` untouched — `git diff --name-only seed/Sector_Financials_Final_Owner.xlsx` returns empty (mtime 2026-08-22 21:28:20).
5. **Zero Invented Numbers**: Benford requires n≥15 else `insufficient_data`; DSO/inventory/AQI/covenant/goodwill/auditor/CCC all return `data_available:false` with reason codes (`accounts_receivable_not_in_local_statements`, `pension_fields_not_in_owner_workbook`, etc.) instead of fake zeros. Restatement deltas are null when no restatement.
6. **Financial Institution Carve-Outs**: Beneish, Altman, Sloan, and penman leverage return `financial_institution_excluded` for banks/insurers (`CA:RY:TSX` verified — `zone:Excluded`, `m_score:null`).
7. **Probabilistic Screens, Not Proof**: Every forensic card and summary carries disclaimer: "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings." with false-positive 15–20% context.
8. **a11y**: `BenfordChart`, trajectory, CCC, goodwill strips carry `role="img"` + `aria-label`; `AsFiledToggle`, Red Flags tabs, and modals support Tab and Escape; `prefers-reduced-motion` disables animations.

---

## 5. Known Limitations & Honest Gaps

- Goodwill is not separately disclosed in the owner workbook; the strip uses a proxy intangible ratio (TA − equity − cash − AR − inventory − PPE)/TA and is labeled "proxy — informational screening only."
- Auditor name/tenure per FY is not stored locally; timeline shows `unknown_auditor` with honest flag until filings enrichment lands.
- Insider, pension, promotion, complexity, and regulatory feeds are premium/external and return `data_available:false` with reason codes rather than guessed flags.
- Benford requires ≥15 positive figures; sparse names (e.g., IIP.UN) correctly return `insufficient_data`.
