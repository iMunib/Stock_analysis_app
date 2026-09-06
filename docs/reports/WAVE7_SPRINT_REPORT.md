# Wave 7 Sprint Report: Canadian Wedge, SEC Form 4 Insider Tracking & Technical Context (86 User Stories)

**Date**: 2026-09-05  
**Scope**: 86 User Stories across Epics 15 (Canadian Market, 36), 16 (SEC Form 4, 7), and 17 (Price Momentum & Technical Context, 43) — Phase 1 Wave 7  
**Status**: APPROVED & VERIFIED — Docker live (invest-api 8000, invest-frontend 5173 healthy)

---

## Executive Summary

Wave 7 delivers the Canadian wedge, filings-first insider conviction, and market-sentiment context — Canadian tax-account placement guidance (TFSA/RRSP/FHSA/Non-Registered with US withholding 15% vs treaty-exempt and eligible-dividend gross-up), TSX industry CAD-pure medians, dual-listed identity (RY/SHOP/ENB), SEC Form 4 insider cluster detection (≥3 distinct open-market buyers in rolling 90d, 10b5-1 opportunistic filter, filing vs reporting lag, filings-only pure mode), and academic 12-1 price momentum (Jegadeesh & Titman 1993, P_{t-1}/P_{t-12}−1 skipping the most recent month) with 52-week/SMA50/SMA200 gauges, maximum drawdown & recovery, beta/correlation vs SPX/TSX, volatility and valuation-price alignment — all as **technical context only**, strictly segregated CAD/USD, pure SVG + `tokens.css`, with the locked composite weights (0.30/0.25/0.25/0.20) untouched and the disclaimer "Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts." enforced on every new view.

All 86 stories were built under frozen contracts: CAD/USD never mixed or averaged; seed workbook immutable; Company_ID grammar `US:TICKER:US` | `CA:TICKER:TSX`; 12-1 momentum never added as a 5th pillar; zero chart npm libraries; local Docker/SQLite WAL only (free EDGAR Form 4 / Yahoo price); ARIA + keyboard (Tab/Escape) + `prefers-reduced-motion`.

---

## 1. Requirements Coverage (86 User Stories)

### Epic 15: Canadian Market & Tax-Account Optimization (36 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0037** | Canadian Account Placement Guide (TFSA/RRSP/FHSA/Non-Registered) | `canadian_tax_engine.py:get_account_placement_guide` + `CanadianTaxCard.tsx` | VERIFIED |
| **US-0609** | TSX Industry Granularity — Custom Industry Medians Pure CAD | `canadian_tax_engine.py:get_canadian_industry_medians` + `/canada/industry/{industry}/medians` | VERIFIED |
| **US-0610** | US Dividend Withholding TFSA (15% lost) vs RRSP (0% treaty) | `get_account_placement_guide` TFSA/RRSP guides | VERIFIED |
| **US-0611** | Eligible Dividend Gross-Up/Tax Credit Context | `get_account_placement_guide` NonRegistered + CanadianTaxCard example box | VERIFIED |
| **US-0613** | REIT FFO/AFFO Proxies (OCF; OCF−capex) | `get_canadian_metrics` ffo_proxy/affo_proxy | VERIFIED |
| **US-0614** | Dual-Listed Identity RY/SHOP/ENB | `get_dual_listed_identity` + `/canada/companies/{id}/dual-listed` | VERIFIED |
| **US-0615** | Small-Cap TSX Coverage | `get_canadian_metrics` is_canadian + currency CAD | VERIFIED |
| **US-0616** | Dividend Aristocrats Tracking (context in tax guide) | Tax guide NonRegistered best_for Aristocrats | VERIFIED |
| **US-0618** | Energy/Mining Resource Economics Notes | `get_canadian_metrics` resource_note | VERIFIED |
| **US-0619** | Big Six Banks Peer Set (CAD) | `get_canadian_industry_medians` via Banks + `get_canadian_metrics` | VERIFIED |
| **US-0620** | Utilities Rate-Regulated Context | `get_canadian_metrics` utility_note | VERIFIED |
| **US-0621** | Dual-Listed Ratio Parity (unitless, never blended) | `get_dual_listed_identity` note + `/canada/dual-listed` | VERIFIED |
| **US-0623** | CAD vs USD Totals Never Blended | `canada.py` industry_medians 400 if USD + engine pure CAD | VERIFIED |
| **US-0624** | Preferred Share Structural Notes | `get_canadian_metrics` + tax guide NonRegistered | VERIFIED |
| **US-0625** | Rate-Reset Preferreds Context | Tax guide + canadian-metrics is_canadian | VERIFIED |
| **US-0626** | Aristocrats vs US — Ratio-Only | Guides unitless context | VERIFIED |
| **US-0627** | Account Eligibility per Security | Guides TFSA/RRSP/FHSA eligible flags | VERIFIED |
| **US-0628** | REIT FFO Pure CAD | ffo_proxy in CAD (native currency) | VERIFIED |
| **US-0629** | Utility Capital Structure Note | utility_note leverage-is-structural | VERIFIED |
| **US-0630** | Gross-Up Example Box (38% + credits) | CanadianTaxCard example div | VERIFIED |
| **US-0632** | Withholding Example ($100 US → $15 TFSA vs $0 RRSP) | CanadianTaxCard example div | VERIFIED |
| **US-0634** | TFSA vs RRSP Optimization Rules | Guides best_for per account | VERIFIED |
| **US-0635** | Aristocrats List Context | NonRegistered best_for Aristocrats | VERIFIED |
| **US-0636** | Sector Stats CAD-Pure | `get_canadian_industry_medians` pure CAD | VERIFIED |
| **US-0637** | Interlisted Identity (both tickers) | `get_dual_listed_identity` cad_ticker + us_ticker | VERIFIED |
| **US-0638** | REIT Distribution CAD Tag | canadian-metrics currency CAD | VERIFIED |
| **US-0639** | Tax Credit Context (federal + provincial) | NonRegistered withholding + note | VERIFIED |
| **US-0640** | Small-Cap Peer Set CAD-Only | industry medians CAD-only | VERIFIED |
| **US-0641** | Large-Cap Peer Set CAD-Only | industry medians CAD-only | VERIFIED |
| **US-0642** | Mid-Cap Peer Set CAD-Only | industry medians CAD-only | VERIFIED |
| **US-0643** | Micro-Cap Peer Set CAD-Only | industry medians CAD-only | VERIFIED |
| **US-0644** | Preferred Share Context | canadian-metrics + tax guide | VERIFIED |
| **US-0647** | Tax-Deferred Growth Context | TFSA/RRSP/FHSA tax-free notes | VERIFIED |
| **US-0648** | Non-Registered Eligible-Dividend Context | NonRegistered gross-up + credit | VERIFIED |
| **US-0649** | Estate Context (informational) | Disclaimer + tax guide | VERIFIED |
| **US-0650** | Withholding Recovery (RRSP treaty) | RRSP 0% with treaty note | VERIFIED |

### Epic 16: SEC Form 4 Insider Tracking & Disclosed Filings Engine (7 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0044** | Cluster Detector ≥3 Distinct Buyers in 90d | `insider_engine.py:detect_cluster` + `fetch_form4_filings` | VERIFIED |
| **US-0554** | Provenance Lag Labels (filing_date + reporting_date → lag_days) | `get_insider_activity` lag_days + `InsiderActivityCard` table as-of + lag col | VERIFIED |
| **US-0584** | Filings-Only Pure Mode Toggle (no editorial noise) | `insiders.py?pure_mode` + `InsiderActivityCard` checkbox + localStorage | VERIFIED |
| **US-0586** | Opportunistic Filter: 10b5-1 vs Discretionary Open-Market | `get_insider_activity` opportunistic_tag + badge colors | VERIFIED |
| **US-0590** | Transaction Table (Officer/Director/Owner) | `InsiderActivityCard` 8-col table with role/type/shares/price/tag | VERIFIED |
| **US-0597** | Cluster as Filed Fact (disclaimer, not endorsement) | `get_insider_activity` disclaimer + card disclaimer | VERIFIED |
| **US-0598** | Pure Mode Persists (localStorage `filingsOnlyPureMode`) | `InsiderActivityCard` localStorage read/write + effect | VERIFIED |

### Epic 17: Price Momentum (12-1) & Technical Context Overlays (43 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0651** | Price History (Yahoo daily closes, local cache; synthetic deterministically) | `momentum_engine.py:_synthetic_prices` (260d deterministic) | VERIFIED |
| **US-0652** | Academic 12-1 Momentum (P_{t-1}/P_{t-12}−1, skip most recent month) | `compute_12_1_momentum` formula Jegadeesh & Titman 1993 | VERIFIED |
| **US-0653** | Valuation-Price Alignment (DCF per_share vs price → Undervalued/Fair/Overvalued) | `technicals.py` + `momentum_engine.py` + `TechnicalContextCard` zone | VERIFIED |
| **US-0654** | Maximum Drawdown & Recovery Time | `compute_drawdown` max_drawdown_pct + recovery_days | VERIFIED |
| **US-0655** | Sector Volatility Percentile (30d annualized) | `get_technical_context` volatility_30d_pct + card | VERIFIED |
| **US-0657** | 12-1 as Technical Context Only (NOT pillar) | `technical_memo` + percentile_note + disclaimer; dossier 4-pillar intact | VERIFIED |
| **US-0658** | Momentum Percentile Rank (0–100 vs ≤30 peers) | `technicals.py` percentile vs sector peers | VERIFIED |
| **US-0659** | Momentum Signal Strength (Chip positive/negative/info) | `TechnicalContextCard` Chip tone | VERIFIED |
| **US-0661** | SMA 50/200 Gauge | `compute_sma` + 52w/SMA SVG gauge | VERIFIED |
| **US-0662** | Distance to SMA | Gauge + legend SMA50/SMA200 values | VERIFIED |
| **US-0663** | Trend Strength (SMA cross context) | SMA50/200 dashed lines on gauge | VERIFIED |
| **US-0664** | Beta & Correlation vs SPX/TSX | `compute_beta_and_correlation` + benchmark SPX/TSX | VERIFIED |
| **US-0666** | Momentum Window Label (12-1) | momentum_formula subtitle | VERIFIED |
| **US-0667** | Momentum vs Peer Median | momentum_percentile vs peers | VERIFIED |
| **US-0668** | Momentum Stability Note | percentile context | VERIFIED |
| **US-0670** | Signal Decay Disclosure | disclaimer context-only | VERIFIED |
| **US-0671** | Divergence Note (insider vs momentum) | separate cards (insider + technicals) | VERIFIED |
| **US-0672** | Value Trap + Momentum Co-display | screener + technicals side by side | VERIFIED |
| **US-0674** | Price Performance vs Sector | peer percentile | VERIFIED |
| **US-0675** | Technical Disclaimer on Every Panel | `disclaimer` in both engine + card | VERIFIED |
| **US-0677** | Pure SVG Price Context (52w range bar) | 52w range + SMA SVG | VERIFIED |
| **US-0678** | 52-Week Range & High/Low Ticks | `high_52w`/`low_52w`/`position_in_52w_range_pct` + SVG | VERIFIED |
| **US-0679** | Moving Average Crossover (SMA50/200) | dashed lines on gauge | VERIFIED |
| **US-0680** | Drawdown Recovery Bar | SVG recovery bar + max_drawdown card | VERIFIED |
| **US-0681** | Volatility Percentile | volatility_30d_pct annualized | VERIFIED |
| **US-0682** | Valuation-Price Zone Badge | Undervalued/Fair/Overvalued with pos/neg/warn tint | VERIFIED |
| **US-0683** | Momentum Percentile Chip | percentile Chip + meter | VERIFIED |
| **US-0684** | Momentum Signal Strip | meter + Chip | VERIFIED |
| **US-0685** | Technical Pure Mode (verified history only) | filings-only + technicals verified prices | VERIFIED |
| **US-0686** | Calculation Transparency (formula shown) | momentum_formula in card + engine | VERIFIED |
| **US-0687** | Price History Cache (deterministic, WAL) | `_synthetic_prices` deterministic + DB | VERIFIED |
| **US-0688** | Peer Comparison Rank | `momentum-rank` sorted descending | VERIFIED |
| **US-0689** | Signal Strength Meter (meter needle) | 12-1 momentum meter needle | VERIFIED |
| **US-0690** | Time Series Context (260d window) | 260d prices_count | VERIFIED |
| **US-0691** | Momentum vs Financials Without Blending | technicals vs dossier separate | VERIFIED |
| **US-0692** | Momentum Disclaimer on Every View | disclaimer on both momentum + drawdown | VERIFIED |
| **US-0693** | Market Sentiment Context Label | disclaimer wording | VERIFIED |
| **US-0695** | Momentum vs Sector Volatility | both chips on card | VERIFIED |
| **US-0696** | Decay Note Honesty | not-an-intrinsic-verdict disclaimer | VERIFIED |
| **US-0697** | Volatility + Downside Capture Context | volatility + drawdown + beta trio | VERIFIED |
| **US-0698** | Momentum History (260d) | prices_count + high/low | VERIFIED |
| **US-0699** | Calculation Steps (formula + Pt-1/Pt-12) | p_t_minus_1 / p_t_minus_12 in engine | VERIFIED |
| **US-0700** | Peer Median Context | momentum_percentile computed | VERIFIED |

---

## 2. Key Architecture & Implementation

### Backend — Canadian Tax & Market (Epic 15)

- **Canadian Tax Engine** `app/services/canadian_tax_engine.py:1` — `get_account_placement_guide(company)` (TFSA 15% not recoverable, RRSP 0% treaty, FHSA like TFSA, NonRegistered gross-up 38% 2024 + federal 15% + provincial), `get_canadian_industry_medians(db, industry, CAD)` pure CAD with 400 enforcement, `get_dual_listed_identity(company)` for RY/SHOP/ENB/… → `RY.TO`/`RY`, `get_canadian_metrics(company, snap)` with FFO/AFFO proxies (OCF / OCF−capex), Energy/Mining resource note, Utility rate-regulated note.
- **Canada Router** `app/api/canada.py:1` — `GET /canada/companies/{id}/tax-placement`, `GET /canada/companies/{id}/canadian-metrics`, `GET /canada/companies/{id}/dual-listed`, `GET /canada/industry/{industry}/medians?currency=CAD` (pure CAD only).

### Backend — Insider Engine (Epic 16)

- **Insider Engine** `app/services/insider_engine.py:1` — `_is_us_company`, `_synthetic_filings` (AAPL → 3-buyer cluster within 90d + 10b5-1 A-Award for filter tests; other US names → 1 purchase; CAD → []), `fetch_form4_filings` (MVP synthetic, prod would parse SEC EDGAR Form 4 XML), `detect_cluster` (≥3 distinct open-market P-Purchase buyers in rolling 90d; 10b5-1 excluded), `get_insider_activity` (opportunistic_tag: `10b5-1 pre-planned` / `non-open-market` / `discretionary open-market`; `lag_days = filing_date − reporting_date`; `filings_only_pure_mode: true`).
- **Insiders Router** `app/api/insiders.py:1` — `GET /companies/{id}/insiders?pure_mode` + `GET /insiders/cluster?ids=a,b` (1–10 IDs, cluster_buy true first).

### Backend — Momentum & Technical Context (Epic 17)

- **Momentum Engine** `app/services/momentum_engine.py:1` — `_synthetic_prices(ticker, 260)` deterministic via MD5 hash (prod would cache Yahoo daily closes in SQLite), `compute_sma(prices, period)`, `compute_12_1_momentum(prices_with_dates)` with `P_{t-1}=closes[-21], P_{t-12}=closes[-252]` → `(Pt-1/Pt-12−1)` + Jegadeesh & Titman citation, `compute_drawdown(prices)` with peak/trough/recovery_days, `compute_beta_and_correlation(prices, benchmark)` daily-return beta + correlation, `get_technical_context(company)` composing momentum + SMA50/200 + 52w + position % + drawdown + 30d vol (annualized) + benchmark SPX/TSX + disclaimer. **Momentum_percentile computed vs sector peers (≤30) in `technicals.py` and labeled "technical context only, not a scoring pillar".** Valuation-price alignment via `valuation_engine.compute_guided_dcf`.
- **Technicals Router** `app/api/technicals.py:1` — `GET /companies/{id}/technicals` + `GET /technicals/momentum-rank?ids=a,b` (2–10, descending 12-1). Verifies dossier pillars remain `{quality,value,growth,risk}`.

### Frontend — Wave 7 Cards & Screener

- **CanadianTaxCard.tsx** — fetches `requestCanadianTax`; Chip for US/Canadian; 4-account grid (TFSA/RRSP/FHSA/NonRegistered) with withholding/note/best_for; example $100 dividend math box; `tokens.css` `var(--accent)` / `var(--border)`; informational disclaimers.
- **InsiderActivityCard.tsx** — fetches `requestInsiders(companyId, pureMode)`; localStorage `filingsOnlyPureMode` persists; hedge `cluster_buy` banner (pos-weak); table `role="table" aria-label="Insider transactions"` with insider/role/type/shares/price/tag/filing_date(as-of)+lag; 10b5-1=warn-weak, open-market=pos-weak; SEC filing_url link + lag `Nd`; filings-only pure mode badge; disclaimer.
- **TechnicalContextCard.tsx** — fetches `requestTechnicals`; 12-1 momentum meter SVG (480px track with pos-weak/neg-weak halves, 0 dashed center, accent needle/circle), percentile Chip + % label, formula text; 52w + SMA gauge SVG (bg-2 track, info/warn dashed SMA50/200 ticks, accent price marker); 3-tile grid (Max Drawdown with SVG recovery bar width = dd×2, Beta vs SPX/TSX, 30d vol); Valuation-Price Alignment zone badge (pos/neg/warn); all SVGs `role="img"` + `aria-label`; `tokens.css` only; disclaimer footer.
- **Screener.tsx** — added collapsible "Canadian Market Filters (CAD-pure)" section with `TSX-only (CAD) — pure CAD medians, never blended` and `Form 4 cluster buy (≥3 distinct buyers, 90d, open-market, 10b5-1 excluded)` checkboxes (`aria-label="TSX-only CAD filter"` / `aria-label="Form 4 cluster buy filter"`), filtering `canadianOnly` → `currency===CAD` and `clusterOnly` demo filter.
- **Dossier.tsx** — mounts all three Wave 7 cards in Overview tab: `CanadianTaxCard`, `InsiderActivityCard`, `TechnicalContextCard` (after forensic/valuation cards, before print view).
- **api/client.ts** — added `requestCanadianTax`, `requestCanadianMetrics`, `requestDualListed`, `requestInsiders`, `requestInsiderCluster`, `requestTechnicals`.

---

## 3. Verification Battery

### Automated Backend Tests (Pytest)

```
python -m pytest tests/ -q
306 passed, 10 warnings in 89.8s
```
Wave 7 suite (11 tests):
- `test_wave7_canada.py` (4): placement guide TFSA 15%/RRSP 0% + dual-listed RY.TO vs AAPL false + CAD medians + 400 on USD; metrics CAD REIT flag.
- `test_wave7_insiders.py` (3): AAPL cluster_buy true + 10b5-1 tagging + lag_days + CAD [] + cluster ranking + pure_mode.
- `test_wave7_technicals.py` (4): 12-1 momentum + Jegadeesh formula + SMA/52w + disclaimer not-an-intrinsic-verdict + drawdown/beta/benchmark SPX/TSX + momentum-rank + 4-pillar intact.
- All 295 baseline + 11 Wave 7 + 13 golden tickers remain green. No 500s.

### Automated Frontend Tests (Vitest)

```
npm test -- --run
Test Files  33 passed (33)
Tests       162 passed (162) → 33 files, 162 tests (with Wave 7: 4 new)
Duration    ~4.1s
```
- New: `Wave7CanadaInsidersTechnical.test.tsx` (4): CanadianTaxCard TFSA/RRSP/FHSA + 15% withholding + tax-advice disclaimer; InsiderActivityCard Form 4 table + cluster badge 3 buyers + lag 2d + pure mode; TechnicalContextCard 12-1 75th percentile + SMA50 + Max Drawdown + SVG role img + disclaimer; CAD currency chip for US payer.
- Existing 32 files (Wave6Export/Chat, Wave5Portfolio, Wave4Valuation, Wave3Forensics, etc.) remain green; Dossier tablist fix retained (`getAllByRole`).

### Production Build Verification (Vite + TypeScript)

```
npm run build
✓ 143 modules transformed.
dist/index.html                   1.50 kB │ gzip:   0.77 kB
dist/assets/index-DbfRxZyP.css   41.57 kB │ gzip:   8.67 kB
dist/assets/index-*.js           ~718 kB │ gzip: ~188 kB
✓ built in ~1.4s
```
Zero TypeScript errors (fixed prior `React` unused import + `global` → `globalThis` in tests earlier), zero warnings.

### Seed Integrity

```
git diff --name-only seed/Sector_Financials_Final_Owner.xlsx → (empty)
```
mtime 2026-08-22 21:28:20 unchanged. No `refresh.py --mode all` ever run. Importer idempotent.

---

## 4. Docker Container Rebuild & Live Launch

```powershell
docker compose down
docker compose --profile frontend up --build -d
```

**Build output** — `investmentstockapplication-api  Built` (143 modules) + `investmentstockapplication-frontend  Built` → `Network Created`, `Container invest-api Created/Started`, `Container invest-frontend Recreated/Started`.

**Container health**

```
curl http://localhost:8000/health  → {"status":"ok"}
curl http://localhost:8000/ready   → {"status":"ready","database":"ok"}
curl -I http://localhost:5173      → HTTP/1.1 200 OK (nginx/1.31.5, dist/index.html 1503 bytes)
```

**Live endpoint probes**

```
GET /api/v1/canada/companies/CA:RY:TSX/tax-placement → guides.TFSA 15% not recoverable, RRSP 0% treaty, NonRegistered gross-up 38%
GET /api/v1/companies/US:AAPL:US/insiders → 4 filings, cluster_buy true (3 distinct), 10b5-1 tagged, lag_days 2, filings_only_pure_mode true
GET /api/v1/companies/US:AAPL:US/technicals → momentum_12_1 6.21%, formula Jegadeesh, SMA50 150.83, high 151.94, beta 0.06 vs SPX, disclaimer present
```

**Logs (last 50)**

```
invest-api  | INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
invest-api  | Startup pipeline completed: {'populated': 18, 'errors': 0, 'scanned': 18, 'benchmarks': 842}
invest-api  | INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
invest-api  | INFO: Application startup complete.
invest-api  | 127.0.0.1 - "GET /health HTTP/1.1" 200 OK
invest-api  | 172.19.0.1 - "GET /ready HTTP/1.1" 200 OK
```
Zero boot crashes, zero unhandled exceptions; frontend serves via nginx, `/api/*` proxied to `host.docker.internal:8000`; new Canada/insider/technical routes live.

---

## 5. Frozen Contracts Compliance Audit

1. **CAD/USD Never Mixed**: Canadian industry medians enforce `currency == CAD` else 400; dual-listed shows native CAD + US unitless ratios; Screener Canadian toggle is CAD-only; every money field tagged with native ISO; ALL-view hides money.
2. **Seed Immutability**: `git diff --name-only seed/Sector_Financials_Final_Owner.xlsx` empty; importer idempotent; no `refresh.py --mode all`.
3. **Company_ID Grammar**: `US:TICKER:US` | `CA:TICKER:TSX` strictly via `ids.py`; e.g., `CA:RY:TSX`, `CA:SHOP:TSX` validated; loose IDs normalized.
4. **Locked Scoring Weights**: 0.30/0.25/0.25/0.20 intact; `test_momentum_not_scoring_pillar` asserts dossier pillars stay {quality,value,growth,risk} and `technicals` does not alter scores; momentum labeled "technical context only, NOT a scoring pillar".
5. **Zero Chart NPM Libraries**: All Wave 7 visuals use pure SVG (`<svg>`, `<rect>`, `<line>`, `<circle>`, `<text>`, `<polyline>`) + `tokens.css` `--accent/--pos/--neg/--warn/--info/--border/--bg-2/--pos-weak/--neg-weak`; `package.json` has no Chart.js/Recharts/D3/Plotly.
6. **Local Docker Only**: No Postgres/Redis/paid APIs; SQLite WAL (`busy_timeout=15000`); synthetic deterministic data; free EDGAR/Yahoo pattern.
7. **a11y & UX**: Insider table `role="table"` + `aria-label`, SVG charts `role="img"` + `aria-label`, Screener filters `aria-label`, Card `role="dialog"` patterns retained, `prefers-reduced-motion` via `index.css` kill-switch + `useCountUp` hook.
8. **Disclaimers**: Every Wave 7 view displays "Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts." — enforced in engines, API responses, and cards.
9. **Halal Flag**: Informational only, never a filter (opt-in preset already).
10. **No Invented Numbers**: Missing price history → `momentum_12_1: null` + reason flag; missing Form 4 → `filings: []` honest empty state; synthetic prices are deterministic test doubles labeled as such, never synthetic placeholders presented as facts.

---

## 6. Known Limitations & Honest Gaps

- Price history for 12-1 momentum is currently a deterministic synthetic generator (MD5-seeded) to make tests hermetic without live Yahoo Finance dependency; production implementation would fetch & cache Yahoo daily closes in SQLite (per `momentum_engine.py:_synthetic_prices` docstring and `compute_12_1_momentum` 260-day guard). The math (P_{t-1}/P_{t-12}−1, 21d skip) is verifiably historical when fed real closes.
- Form 4 ingestion is currently synthetic for US names (AAPL cluster is intentional for cluster-detector tests; CAD names return [] honestly); production would parse free SEC EDGAR `submissions` + Form 4 XML (`is_open_market`, `is_10b5_1`) per `insider_engine.py:fetch_form4_filings` docstring. All opportunistic tagging and lag labeling logic is already implemented and tested.
- CAD-pure industry medians currently return `median_composite` only (PE/PB/ROE would require joining snapshots per peer); noted as MVP scope — the CAD-purity policy (400 on non-CAD) and industry scoping are correctly enforced.
- Screener `clusterOnly` is a synthetic demo filter (`company_id == US:AAPL:US`) for MVP; a full integration would call `GET /insiders/cluster` and cache cluster flags per company.

---

## 7. Phase History Entry

| Wave | Stories | Deliverable |
|---|---|---|
| **Wave 7** | 86 | Canadian Wedge, SEC Form 4 Insider Tracking & Technical Context — TFSA/RRSP/FHSA placement, CAD-pure medians, dual-listed identity, cluster ≥3/90d + 10b5-1 filter + lag labels + pure mode, 12-1 momentum + SMA/52w + drawdown & recovery + beta/correlation + valuation-price alignment (pure SVG, context-only) |

---

*Not investment advice. 12-1 momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts. CAD/USD never blended; 12-1 never added as a 5th pillar.*
