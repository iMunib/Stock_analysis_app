# Investment Stock Application — Master README

**Personal, local equity-research desk. Not investment advice. Not a product.**

A deterministic, local-first research system for **928 companies** (720 genesis seed + 208 expanded, incl. NSRGY + 10 quality compounders: RLI/GGG/TTEK/MEDP/ASML/LVMUY/HEI-A/MTY.TO/ENGH.TO/LMN.TO). Every money field stays in native currency (CAD / USD segregated), every missing field stays NULL with a reason flag, and every score is a pure math formula — no LLM overwrites. Baseline is **10 fiscal years** of history per company where available, rendered as interactive hoverable SVG timelines.

---

## 1. Mission & Constraints (Locked)

**User:** Single local operator (Ottawa, Canada). Local Docker only. No cloud, no paid APIs, no auth.

**What it does:**
1. Preserves the frozen owner workbook (`seed/Sector_Financials_Final_Owner.xlsx`, 720 rows, 57 cols, 48 sheets) exactly — never overwrites non-NULL owner values.
2. Layers free history on top: **SEC EDGAR** (US 10-K / 20-F incl. `ifrs-full`) + **Yahoo Finance** (CA annual statements + prices) via `ProviderRegistry`.
3. Serves deterministic 0–10 research scores (Quality/Value/Growth/Risk) with coverage penalties and honest NULLs.
4. Flags AAOIFI-style halal status as informational badge, never a filter.
5. Provides a fast local UI: search, dossier, compare (≤8), sector explorer, screener, portfolio ledger, alerts daemon.

**Frozen contracts (never violate):**
- **SQLite WAL is sole operational source of truth** (`data/app.db` inside Docker, host `./data/app.db`). Excel is genesis-only; runtime never re-imports unless `--force`. Once `data/app.db` exists, `python -m app.services.importer` logs `Excel seed reading skipped (database is primary durable store)` and exits.
- **Never mix CAD & USD money.** Cross-border views show unitless ratios only (ROE, PE, FCF margin, EV/EBITDA). Median money stays per-currency; `ALL` currency view masks money.
- **Never invent numbers.** Banks/insurers: Debt/FCF/Gross profit stay NULL when the seed left them blank; 5-year growth on IPOs is NULL; non-payers have no yield guess. `NULL + flag` is correct.
- **IDs frozen:** `US:TICKER:US` or `CA:TICKER:TSX` (dots kept: `CA:BN:TSX`, `CA:EMP.A:TSX`). Bare tickers normalize.
- **Never run `seed/refresh.py --mode all`.** Legacy copies live in `legacy/` untouched.
- **Weights locked:** `0.30 Quality + 0.25 Value + 0.25 Growth + 0.20 Risk` (Risk inverted). Coverage: 4→×1.0, 3→×0.92, 2→×0.80, 1→×0.65, 0→NULL (`insufficient_data`).
- **Money scale:** stored verbatim as currency units (USD MMM example: `24,948,000,000` = $24.9B actual). Never rescale.
- **No chart npm libs.** Pure SVG + `tokens.css` only. Respects `prefers-reduced-motion`.

---

## 2. Architecture

```
┌────────────────────── Docker Compose ──────────────────────┐
│  invest-api (FastAPI :8000)       invest-frontend (nginx :5173) │
│  ├─ alembic upgrade head          ├─ Vite + React 18 + TS strict   │
│  ├─ python -m app.services.importer └─ /api/* → host.docker.internal:8000 │
│  └─ uvicorn + JobWorker daemon    volumes: ./seed:/seed:ro (genesis) │
│  volumes: ./data:/app/data (SQLite WAL)  ./data → /app/data        │
└───────────────────────────────────────────────────────────┘
         │ seed workbook (read-only, genesis)      │ browser localhost:5173
         ▼                                         ▼
  Sector_Financials_Final_Owner.xlsx      Desk / Sectors / Dossier / Compare / Screen
  (720 rows, read once)                  / Portfolio / Alerts / Ops / Governance
```

### Backend (`backend/app` — Python 3.12, FastAPI + SQLAlchemy 2 + Alembic + SQLite WAL)

| Module | Role |
|---|---|
| `app/main.py` | FastAPI app, CORS for :5173, **millisecond logging** (`%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s`, datefmt `%Y-%m-%d %H:%M:%S`), lifespan migration guard (refuses to boot if `alembic_version != head`), JobWorker daemon |
| `app/config.py` | Env config, seed discovery (`/seed`, `seed/`, `SEED_DIR`) |
| `app/db.py` | SQLite engine (WAL + `busy_timeout=60000`, FK on, `cache_size=-64000`) |
| `app/models.py` | `companies`, `financial_snapshots`, `financial_statements` (3NF), `derived_metrics`, `financial_snapshots_ttm`, `peer_benchmarks`, `scores`, `halal_flags`, `jobs`, `llm_cache`, `company_profiles`, `portfolio_*`, `decision_journal`, `alert_rules` |
| `app/services/importer.py` | **Decoupled genesis importer** — idempotent, mtime-skipped, `--force` to re-import. If DB already has companies, logs `database is primary durable store` and skips Excel entirely; `logger` uses millisecond formatter |
| `app/services/calculation_pipeline.py` | Orchestrates: provider fetch → `ingest_statements` (frozen overwrite policy: first-provider-wins, bank carve-out) → `compute_snapshot_ratios` → TTM/ROIC, Altman, Beneish, Penman, ReverseDCF, CAGRs → `recompute` scores |
| `app/services/ids.py`, `mapping.py` | Frozen ID parse/normalize; `universe_master.csv` authoritative; SEC `company_tickers.json` fallback |
| `app/providers/edgar.py`, `yahoo.py`, `registry.py` | EDGAR `companyfacts` (1 call/CIK, token bucket 8/s, 403/429 back-off); yfinance (0.2s throttle); CA→Yahoo, US→EDGAR+price |
| `app/services/jobs.py`, `job_worker.py` | SQLite job queue (queued→running→succeeded/failed), one daemon worker (owns session). **Millisecond logging** for all worker steps (`resolve → filings → prices_shares → sector_peers → score → done`) |
| `app/jobs/startup_pipeline.py` | Sync startup: `populate_missing_metrics(limit=None, fetch_live=False)` computes all derived metrics for companies already in DB |
| `app/jobs/universe_expansion.py`, `batch_universe_expansion.py` | Curated expansion jobs (Russell 1000, TSX, micro-cap, dining/retail/tech etc.) — also millisecond-logged |
| `app/api/*` | Domain routers (see §7) |

**3NF pipeline:** `financial_statements` (raw GAAP line items) → `derived_metrics` (ratios/CAGRs/forensics) → `financial_snapshots` (seed FY rows with `fiscal_year NULL`) + `financial_snapshots_ttm` (NOPAT/invested capital/ROIC/Sloan).

### Frontend (`frontend` — React 18 + Vite 5 + TS strict + Tailwind 3, night research desk)

| Area | Modules |
|---|---|
| Design tokens | `src/styles/tokens.css` (30+ CSS vars), `tokens.ts` typed mirror, `index.css` keyframes + `prefers-reduced-motion` kill-switch, Spectral / IBM Plex Sans / Mono |
| Layout | `Page`, `Grid`, `Card` (tone = left-border 3px), `StatTile` (YoY ▲/▼), `Chip` |
| Viz (pure SVG) | `PillarRadar`, `CompositeGauge`, `Sparkline`, `MiniPillarBars`, `AltmanZGauge`, `PercentileMatrix`, `CashFlowBridge` |
| Feedback | `EmptyState`, `LoadingSkeleton` |
| Lib | `sessionCompare.ts` (**atomic `useCompare` hook** + `clearCompare()`), `compare.ts`, `watchlist.ts`, `alerts.ts`, `format.ts`, `allCurrency.ts`, `useCountUp.ts` |
| Shell | `AppShell.tsx` (sticky nav, debounced search 200ms, **compare badge via `compare-updated` event**, alerts drawer, `Cmd+K` palette) |

All screens use design-system primitives, tokenized colors, ARIA labels.

---

## 3. Data Contracts

- **Dictionary:** `docs/DATA_CONTRACT.md` — 57-col owner workbook spec, ID/currency/NULL+flag rules, provenance (`source` ∈ owner xlsx / sec_companyfacts / yfinance; `fetched_at`; `provider_as_of`), overwrites.
- **Scoring spec:** `docs/SCORING_SPEC.md` — locked v1 math (12-1 momentum is technical context only, not a 5th pillar).
- **Seed readme:** `seed/readme.md` — owner workbook dictionary (read-only).

**Honest missing data:** 100% completeness = pull all available EDGAR/Yahoo history; inapplicable lines remain NULL with `data_quality_flags` reason (e.g., banks: `Gross_Profit` `Debt` blank). Growth pillar needs ≥3 positive FY points; otherwise NULL + 3-pillar penalty.

---

## 4. Scoring Model (`method_version=v1`, deterministic)

```
Composite = 0.30·Quality + 0.25·Value + 0.25·Growth + 0.20·Risk
Coverage penalty: 4→×1.0  3→×0.92  2→×0.80  1→×0.65  0→NULL (insufficient_data)
Signal: 8–10 Strong candidate · 6.5–7.9 Constructive · 5–6.4 Mixed · 3.5–4.9 Weak · 0–3.4 Avoid
```

- **Quality:** Piotroski F-score + level quality (ROE/ROA/FCF margin or gross margin, GP/Assets) vs same-currency peers; banks use ROE/ROA/ROAA/Efficiency/CET1/NIM.
- **Value:** earnings yield + PE/PB/EV-EBITDA percentiles vs same-currency peer set (custom industry ≥8 else GICS; negative earnings → PE skipped).
- **Growth:** revenue/EPS/FCF CAGR over min(10, available) FY, ≥3 positive points, piecewise −40%→0 / 0%→5 / +40%→10.
- **Risk:** net debt/EBITDA, liabilities/assets, interest coverage; banks invert CET1/leverage; volatility needs ≥5 FY.
- **Halal:** activity screen + 30/30 debt/cash vs market cap; impure income unknown in v1 → `unknown`.

Scores skew low by design: until full history backfill, growth is NULL for many names and the 3-pillar penalty applies. Explain, never hide.

---

## 5. Consumer Staples & Quality Compounders (Completed 2026-09-06)

**29 premier quality compounders ingested with 10-year histories, TTM, forensics, and valuation (expanded 2026-09-06):**

| Market | Tickers |
|---|---|
| US Staples (13) | PG, KO, PEP, COST, WMT, CL, GIS, KMB, HSY, CHD, MKC, MDLZ, **JNJ**, **NSRGY** (Nestlé ADR) — each 18–20 FY via EDGAR |
| CA Staples (6) | ATD.TO, L.TO, MRU.TO, WN.TO, EMP.A.TO (`CA:EMP.A:TSX`), SAP.TO — each 5 FY via Yahoo |
| US Quality Add-ons (7) | **RLI** (specialty insurance), **GGG** (Graco), **TTEK** (Tetra Tech), **MEDP** (Medpace), **ASML** (ASML ADR), **LVMUY** (LVMH ADR), **HEI-A** (HEICO Class A) — each 12–19 FY via EDGAR/Yahoo, durable ROIC & moat |
| CA Quality Add-ons (3) | **MTY.TO** (MTY Food), **ENGH.TO** (Enghouse), **LMN.TO** (Lumine) — TSX small/mid compounders; honest `insufficient_data` for LMN 0 FY (no invented history) |

All 29 with 3NF statements, `derived_metrics` (Altman Z/Zʺ, Beneish M, Sloan, Piotroski), TTM (NOPAT, invested capital, ROIC, Sloan accruals), ReverseDCF, Greenwald EPV, Penman, and v1 composite (coverage 4/4 where history permits; LMN `insufficient_data` is correct).

All histories are **10-year standardized** (FY2016–2025) with interactive SVG hover points (FY, native currency, YoY, filing source) and click-to-pin. All derivable ratios honour currency isolation and honest NULLs (`Not reported in filing` / `Not applicable: Bank model` / `Requires 3+ fiscal years` / `0.00`). Cross-border comparison uses ratios only.

**Industry consolidation:** 48 custom sheets merged into cohesive peer groups (e.g., `Retail & Consumer Commerce`, `Enterprise Software & Cloud Platforms`, `Canadian Banking & Financials`). Every `Sectors` card and filter now shows explicit constituent counts (e.g., `Enterprise Software (38 companies)`, `GICS Information Technology (74 companies)`) and currency-split medians.

## 5b. Valuation, Timeline & Experience Overhaul (2026-09-06)

**Valuation & Expectations — institutional-grade pure SVG:**
- **Guided DCF Fan Chart:** 10-year projected FCF trajectories rendered as distinct vector lines (Bear tan `var(--warn)` dashed, Base accent solid, Bull pos) with subtle confidence band (`var(--accent)` 8% opacity). Interactive hover points for each year t+1..t+10 show exact FCF, discount factor, and PV. WACC build (`Rf + ERP × Beta`) and terminal share of EV prominently displayed with high-contrast warning when terminal >70% (`High terminal >70% - fragile`).
- **Greenwald EPV Spectrum:** Redesign to Valuation Spectrum & Margin of Safety Floor — horizontal reproduction-cost spectrum: Reproduction Cost Floor (warn) vs Normalized Earnings Power Value (info) vs Market Enterprise Value (accent needle). Franchise Margin (EPV - Reproduction) shaded pos when economic rents present. Margin of Safety chips: `var(--pos)` when market < EPV (value opportunity), `var(--warn)`/`var(--neg)` when speculative >30% premium, with `Cheap for reason` flag linked to forensic health.
- **Bank Valuation:** For `Financials/Banks/Insurance/Credit` the FCF DCF is disabled with professional notice `Not applicable: Bank capital structures prioritize regulatory capital (CET1) and net interest margins over enterprise free cash flow.` and the Multi-Stage DDM and Residual Income / Excess ROE models are surfaced via `BankValuationCard` (DDM, Residual).

**10-Year Interactive Timeline:**
- All historical financials standardized to **10 fiscal years** (`history_annual` last 10 sorted). Backend queries `period_type='FY'` up to 10 rows, derived CAGRs span full window.
- New `HistoricalTimelineChart.tsx` — pure SVG trend chart with per-year `<circle>` hover targets, tooltip with FY, native currency (e.g., `$365.82B USD`), YoY %, filing source stamp, and click-to-pin. Replaces static bar chart in `Dossier.tsx` Financials tab.
- Screener and Sector rankings remain 10-year aware.

**Compare — side-by-side institutional board:**
- **Trend overlays:** Synchronized 10-year revenue growth SVG overlay for 2–8 companies, per-company color (`accent/info/pos/warn/neg`), hover title with native figures.
- **Consolidated KPIs:** New card `Consolidated KPI Detail` with Market Cap, ROIC, FCF Yield, Altman Z, Net Debt/EBITDA — honest `Not reported in filing` / `Not applicable: Bank model` per stock.
- **Column selector:** Toggle groups `Core KPIs` / `Forensics` / `Dividend Safety` / `Bank Ratios` without clutter; Core shows Composite, P/E, EV/EBITDA, ROE, etc., with best-value accent band retained.

**Learn / Curriculum — Analyst Academy:**
- Milestone Progression Rail with 4 stages (Fundamentals, Forensics, Valuation, Capital Allocation) and progress bar.
- Interactive 10-K Walkthrough side-by-side annotated filing explorer (Balance Sheet excerpts linked to ROA, Sloan, Altman; Income/Cash bridge linked to NOPAT/EPV) using design tokens and monospaced figures.
- Concept cards, spaced-repetition quizzes, and case studies retain clean typography (`var(--font-serif)`, `var(--font-sans)`, `var(--font-mono)`) and ARIA.

**Copy & Accessibility:**
- Em-dash `—` eliminated across `frontend/src` and `backend/app` (135 source files). Replaced with `Not reported in filing` (missing), `Not applicable: Bank model` (banks), `Requires 3+ fiscal years` (thin history), `0.00`/`0.0%` (zero), `Under review` (unrated), or ` - ` for separators.
- Institutional tone: formulaic AI summaries replaced with authoritative research phrasing (e.g., `Normalized Earnings Power`, `Reproduction Cost Floor`, `Capital Allocation Discipline`) with plain-English definitions. No `Recharts`/`Chart.js`/`D3` — all visuals pure SVG + `tokens.css`, `prefers-reduced-motion` respected, `role="img"`/`slider`/`tab` and keyboard (Tab/Enter/Escape) throughout.

---

## 6. Compare Tray Fix (2026-09-05)

**Files:** `frontend/src/lib/sessionCompare.ts`, `frontend/src/screens/Compare.tsx` (with `AppShell.tsx` + `Dossier.tsx` patched for sync).

- `sessionCompare.ts` now exports **atomic event-driven `useCompare` hook** (`ids`, `count`, `has`, `add`, `remove`, `toggle`, `set`, `clear`, `clearCompare`) plus `COMPARE_EVENT = "compare-updated"` and helpers `addCompareSelection` / `removeCompareSelection` / `setCompareSelection`.
  - Every mutation writes `localStorage["compareIds"]` (max 8, filtered to strings) and **dispatches** both `CustomEvent("compare-updated", {detail: ids})` and plain `Event("compare-updated")`; storage events propagate across tabs; `visibilitychange` re-sync handles bfcache.
  - `clearCompareSelection()` and exported `clearCompare()` clear `localStorage`, dispatch `compare-updated` with `[]`, and patch `window.history` to remove `?ids` / `?compareIds` query params (then dispatches `popstate` so routers update without reload).
- `Compare.tsx` uses `useCompare()` atomically: `setIds` persists to `localStorage` and dispatches before calling `setParams`; `clearCompare` is explicit: `clearCompareSelection()` → `setParams({}, {replace:true})`. A “Basket vs URL” strip shows `Load basket → Compare` and `Clear basket` when `compare.ids` diverges from `?ids`, ensuring **clicking “Add to Compare” in any dossier immediately updates the global badge and Compare table**.
- `AppShell.tsx` subscribes to `compare-updated` + `storage` to update the badge instantly (not only on `loc` change).
- `Dossier.tsx` uses `useCompare().toggle` for the “Add to compare” checkbox so the Compare view and AppShell see it in the same tick.

No direct `localStorage` writes remain outside the atomic helpers.

---

## 7. Logging — Millisecond Precision

**Formatter:** `%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s:%(lineno)d] %(message)s`  
**Datefmt:** `%Y-%m-%d %H:%M:%S` (example: `2026-09-05 22:59:23.835 [INFO] [job_worker:42] periodic refresh enqueued`)

Configured in:
- `backend/app/main.py` — `logging.basicConfig(..., force=True)` at import time; also patches `uvicorn`/`uvicorn.error`/`uvicorn.access` handlers so every API request line carries msecs + file:line.
- `backend/app/services/importer.py` (`logger = getLogger("importer")`) — genesis skip / fixture fallback now logged, not printed.
- `backend/app/services/job_worker.py` (`logger = getLogger("job_worker")`) — `price fetch error`, `pipeline computation error`, `[job X] ticker failed` all via `logger.warning`.
- `backend/app/jobs/startup_pipeline.py`, `batch_universe_expansion.py`, `universe_expansion.py` — `basicConfig` with same formatter, `logger = getLogger(...)`.

Result: `docker compose logs api` shows every ingestion job, background worker poll, and HTTP access with the same `.SSS` timestamp.

---

## 8. API Surface (all under `http://localhost:8000`)

**Meta & Health**

| Method & path | Purpose |
|---|---|
| `GET /health`, `GET /ready` | liveness / DB ping (`SELECT 1`) |
| `GET /api/v1/meta/disclaimer` | static disclaimer |
| `GET /api/v1/stats` | universe counts (companies, FY snapshots, scored) |
| `GET /api/v1/system/health/telemetry` | `alembic_version` vs `alembic_head`, `schema_verified`, worker heartbeat |

**Companies & Dossier**

| `GET /api/v1/companies?q=&sector=&industry=&country=&limit=&offset=` | list (928) |
| `GET /api/v1/companies/{id}` | identity + latest snapshot + flags + placements |
| `GET /api/v1/companies/{id}/financials?years=10` | annual rows newest-first (snapshot + 3NF statements) |
| `GET /api/v1/companies/{id}/statements`, `/derived-metrics`, `/benchmarks`, `/piotroski`, `/dupont`, `/peer-matrix` | 3NF reads |
| `GET /api/v1/companies/{id}/dossier` | one payload: identity + enriched snapshot + history + score + halal + data_gaps + drilldown + tensions + bear case + vintage + practitioner |
| `GET /api/v1/companies/{id}/similar?n=5` | same peer set; 409 if subject score NULL |
| `GET /api/v1/companies/{id}/pillar-drilldown` | formula decomposition, sub-metrics, line items, provenance URLs |
| `GET /api/v1/companies/{company_id}/ratios/{ratio_name}/inspect` | step-by-step arithmetic inspector |
| `GET /api/v1/companies/{id}/bear-case` | 3 lowest percentiles + forensic flags + pre-mortem prompt |
| `GET /api/v1/search?q=&limit=`, `GET /api/v1/search/suggestions`, `GET /api/v1/tickers/resolve?ticker=` | ticker/name/ID/Yahoo symbol search (+ ingest suggestion) |
| `GET /api/v1/compare?ids=a,b` | 2–8; mixed-currency warning; money per-row |
| `DELETE /api/v1/companies/{id}`, `POST /api/v1/companies/{id}/restore` | soft-delete / restore (local) |

**Sectors & Screening**

| `GET /api/v1/sectors`, `GET /api/v1/benchmarks` | custom industries + GICS groups |
| `GET /api/v1/sectors/{sheet}/snapshot?currency=USD\|CAD` | cached counts, medians, histogram, top/bottom 10 |
| `GET /api/v1/sectors/{sheet}/rankings?currency=ALL\|USD\|CAD` | ranked table (ALL = score-only, both currencies) |
| `GET /api/v1/screener/presets`, `POST`, `DELETE /screener/presets/{id}`, `PUT .../auto-run` | screener presets CRUD |
| `POST /api/v1/screener/run` | forensic screener (altman_z, Sloan, etc.) |
| `GET /api/v1/screen`, `GET /api/v1/screen/export` | full-universe filter + formula-transparent CSV |
| `GET /api/v1/sectors/rotation?currency=`, `GET /api/v1/sectors/{sheet}/cycle-tag`, `/barrier`, `/histogram` | **Sector Rotation** (quarterly Δ, cycle tags, barrier proxy, SVG histogram) |
| `GET /api/v1/sectors/{sheet}/rankings` already covers histogram median line; `GET /api/v1/coverage`, `/api/v1/coverage/health`, `GET /api/v1/factors/evidence` | coverage health + factor base rates |

**Forensics, Trajectory & Restatements**

| `GET /api/v1/companies/{id}/forensics{,/summary,/benford,/timeline,/quality,/penman,/schilit,/graham,/practitioner,/valuation}` | Forensics suite (Altman/Beneish/Sloan/Penman/Schilit/Graham + Benford χ²) |
| `GET /api/v1/forensics/rank?ids=a,b` | portfolio forensic ranker |
| `GET /api/v1/companies/{id}/restatements` | as-filed vs as-restated per FY |
| `GET /api/v1/companies/{id}/trajectory` | 10-yr Revenue/Margin/FCF |
| `GET /api/v1/companies/{id}/working-capital` | CCC (DSO/DIO/DPO) |
| `GET /api/v1/companies/{id}/goodwill-risk`, `/dilution` | goodwill strip + share dilution |

**Valuation**

| `GET /api/v1/companies/{id}/valuation{,/guided,/epv,/ddm,/residual-income,/decomposition,/normalized}` | Guided DCF (Bear/Base/Bull, WACC), Greenwald EPV, DDM, Residual Income, reverse-DCF, mid-cycle normalization |
| `GET /api/v1/valuation/rank`, `/valuation/compare` | valuation rankers |

**Jobs & Ingest**

| `POST /api/v1/tickers/ingest {ticker}` | **async 202 + poll** — `resolve → filings → prices_shares → sector_peers → score → done` |
| `GET /api/v1/tickers/ingest` (via `financials.py` alias) | sync helper |
| `POST /api/v1/jobs/backfill {mode, limit}` | 202 + poll (409 if one queued/running) |
| `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}` | list / poll status + provider_stats |
| `POST /api/v1/scores/recompute`, `GET /api/v1/companies/{id}/score`, `GET /api/v1/scores/summary`, `GET /api/v1/rankings?scope=` | scoring |

**Portfolio, Alerts, Exports**

| `POST/GET /api/v1/portfolio/accounts`, `/transactions`, `/holdings`, `/summary`, `/dividends`, `/rebalance`, `/tax-lots`, `/forensic-heatmap` | Local ledger (TFSA/RRSP/FHSA/Taxable/Paper, CAD/USD isolated) |
| `POST/GET /api/v1/portfolio/journal`, `GET /journal/calibration` | decision journal |
| `POST/GET /api/v1/alerts/rules`, `POST /alerts/evaluate`, `GET /alerts/{calendar,heartbeat,events,evaluate}` | local alerts daemon |
| `GET /api/v1/companies/{id}/export/{memo,raw,factsheet}`, `GET /api/v1/export/{batch,journal}`, `GET /api/v1/portfolio/export/review` | Memo/batch/JSON/factsheet exports |
| `GET /api/v1/watchlist/digest` (GET+POST), `GET /api/v1/watchlist/deltas` | Watchlist morning brief + deltas |

**Canada, Insiders, Technicals**

| `GET /api/v1/canada/companies/{id}/{tax-placement,canadian-metrics,dual-listed}`, `GET /api/v1/canada/industry/.../medians?currency=CAD` | TFSA/RRSP placement, REIT/sector notes, dual-listed identity |
| `GET /api/v1/companies/{id}/insiders?pure_mode=`, `GET /api/v1/insiders/cluster?ids=` | Form 4 clusters (≥3 buyers 90d, 10b5-1 filter) |
| `GET /api/v1/companies/{id}/technicals`, `GET /api/v1/technicals/momentum-rank?ids=` | **Technicals (context only, NOT a scoring pillar):** 12-1 momentum, SMA50/200, 52w, drawdown/recovery, beta/correlation, valuation-price alignment |

**Curriculum, Backtesting, Ops, Governance**

| `GET /api/v1/curriculum/modules`, `/modules/{id}`, `/flashcards`, `/quiz/{id}`, `/case-studies`, `/10k-reader/{id}` | **Curriculum** (6 modules, Enron/WorldCom/Berkshire cases) |
| `GET /api/v1/backtesting/{factor-decay,survivorship,signal-follow-through}`, `POST /api/v1/backtesting/overfitting-check` | **Backtesting** (factor decay −58% McLean & Pontiff, survivorship auditor) |
| `POST /api/v1/ops/backup`, `GET /api/v1/ops/backups`, `POST /ops/{restore, vacuum}`, `GET /ops/{integrity,seed-checksum,diagnostics}` | **Ops** (one-click backup, integrity_check, VACUUM, seed SHA256) |
| `GET /api/v1/governance/{model-risk,canon-map,diff-matrix}` | **Governance** (8-model risk register, canon cross-ref, SA/SWS/TIKR/GF diff) |
| `GET /api/v1/llm/status`, `POST /api/v1/companies/{id}/{chat,narrate,research}`, `POST /api/v1/sectors/{sheet}/narrate` | **LLM** (OpenRouter `:free` only, `minimax/minimax-m3:free` default, fallback `mistralai/mistral-small-24b-instruct-2501:free`, 45s guard, `llm_cache`) |

`GET`s never hit the network. No scraping.

---

## 9. Running It (Windows PowerShell)

```powershell
cd "C:\Users\RehmanPC\Downloads\Investment Stock Application"

# API + UI
docker compose up --build -d
docker compose --profile frontend up --build -d

# Verify
curl http://localhost:8000/health          # {"status":"ok"}
curl http://localhost:8000/ready           # {"status":"ready","database":"ok"}
# UI: http://localhost:5173  (nginx :80 in-container, /api proxied → api)

# Logs carry millisecond timestamps in every line:
docker compose logs api --tail 50
# 2026-09-05 22:59:23.835 [INFO] [importer:373] Operational SQLite database already populated ...
# 2026-09-05 22:59:24.101 [INFO] [job_worker:67] periodic refresh enqueued
# 2026-09-05 22:59:24.512 [INFO] [uvicorn.access:45] 127.0.0.1:54321 - "GET /health HTTP/1.1" 200

# Backend tests — 322 passed, 10 warnings (322 baseline; includes trust/forensics/valuation/portfolio/chat/canada/insiders/technicals/curriculum/sector/backtesting/ops/governance)
cd backend
python -m pytest tests/ -q   # 322 passed in ~86s

# Frontend — 170 tests across 34 files, 149 modules Vite, 0 TypeScript errors
cd ..\frontend
npm test -- --run        # vitest run → 170 passed
npm run build            # tsc strict + vite → dist/ (✓ 149 modules, JS 834 kB / gzip 218 kB)

# Playwright e2e (UI must be up; then `npx playwright install chromium`)
npx playwright test app.spec.ts
```

**One-click ops (no CLI):**

- **Backups:** `POST /api/v1/ops/backup` → `data/backups/app_backup_YYYYMMDD_HHMMSS.db` (WAL checkpoint + `integrity_check`). `GET /api/v1/ops/backups` lists newest-first (max 20). Restore via `POST /api/v1/ops/restore/{file}` then `VACUUM`.
- **Diagnostics:** `GET /api/v1/ops/diagnostics` → db size, WAL size, page count, worker last heartbeat, `alembic_head` vs `migration_revision`.
- **Seed checksum:** `GET /api/v1/ops/seed-checksum` → SHA256 of `Sector_Financials_Final_Owner.xlsx` (immutability proof).
- **Ingest a ticker not in seed:** Desk → “Add & score” or `curl -X POST http://localhost:8000/api/v1/tickers/ingest -H "Content-Type: application/json" -d '{"ticker":"SHOP.TO"}'` → `{job_id}` poll `GET /api/v1/jobs/{id}` every 1s until `done`.

**Background tasks:** `JobWorker` daemon thread claims one queued job at a time (backfill / ingest / recompute / refresh_universe). `REFRESH_ENABLED=1` + `REFRESH_INTERVAL_HOURS=168` in `.env` enables weekly sample refresh (`AAPL, MSFT, RY.TO, XOM, SHOP.TO`). At startup, `startup_pipeline --sync-only` recomputes missing `derived_metrics`/`scores` locally (no network).

Importer is idempotent and mtime-skipped. Force re-import: `docker compose exec api python -m app.services.importer --force`.

---

## 10. Current State (2026-09-06 12:00 UTC)

- **Universe:** 928 companies (US 700 / CA 228 — added NSRGY + 10 quality compounders: RLI/GGG/TTEK/MEDP/ASML/LVMUY/HEI-A + MTY.TO/ENGH.TO/LMN.TO). Genesis seed 720 preserved: `financial_snapshots` contains 720 rows with `fiscal_year NULL` + `source='Sector_Financials_Final_Owner.xlsx'` (immutable). Provider history adds ~12,177 dated FY rows.
- **Snapshots:** 12,897 `financial_snapshots` (720 seed + 12,177 provider) + 12,897 `derived_metrics` + 928 TTM rows + 928 valuation rows. Every CA/US name has price/shares/market cap filled where available; banks/insurers keep `total_debt`/`gross_profit` NULL where seed left them blank but retain owner-provided debt where it existed (e.g., RY 545,439,000,000). All histories 10-year where provider permits (US 18–20 FY, CA 5 FY).
- **Scores:** 924 scored (`composite` non-NULL), 4 `insufficient_data` (LMN.TO 0 FY + 3 sparse micro-caps are honest). Growth pillar populated for ~690+ names with ≥3 FY; staples + new quality are 4/4 where history permits (LMN `insufficient_data` is correct).
- **Quality compounders verified:** Staples PG (5.89), KO (5.08), PEP (4.99), COST (4.30), WMT (5.00), CL (4.66), GIS (3.95), KMB (6.32), HSY (4.54), CHD (5.74), MKC (6.22), MDLZ (4.46), JNJ, NSRGY + New: RLI (0.44 Altman, 17.9% ROIC), GGG (14.5 Altman, 24.3% ROIC), TTEK (4.47), MEDP (11.31), ASML, LVMUY (6.8), HEI-A (7.25), MTY.TO (3.17), ENGH.TO (8.62) — each with 10-year timeline, Sloan/Beneish/Altman/TTM.
- **Migrations:** head `h7i8j9k0l1m2` (wave5 portfolio/alerts, merges `23317f57050f` + `g1h2i3j4k5l6`). Chain: `ccf1cb226400` (initial) → `b7f2a91c4d50` → `c3d4e5f6a780` → `d6e7f8a9b001` → … → `a1b2c3d4e5f6` → `23317f57050f` → `h7i8j9k0l1m2`. Live DB `alembic_version = h7i8j9k0l1m2` matches head. `lifespan` refuses to boot on mismatch (manual `alembic upgrade head` or `stamp head`).
- **Tests:** backend `pytest` **322 passed** (10 warnings); frontend `vitest` **170 passed** across **34 files**; `tsc && vite build` **0 errors, 149 modules** (CSS 48.1 kB gzip 9.9 kB, JS 834.8 kB gzip 218.4 kB).
- **Docker:** `invest-api` (:8000) and `invest-frontend` (:5173) both `healthy` on `0.0.0.0`, `restart: unless-stopped`, `service_healthy` gate; `GET /health` → `{"status":"ok"}`, `GET /ready` → `{"status":"ready","database":"ok"}`; logs show `.SSS` millisecond timestamps; zero crashes.
- **Config:** LLM `minimax/minimax-m3:free` (fallback `mistralai/mistral-small-24b-instruct-2501:free`, 45s guard, cached in `llm_cache`); HALAL `unknown` by default; 12-1 momentum is **technical context outside composite**; factor backtests never alter scores; CAD/USD never blended.

**Design system 2026-09-02:**
- `tokens.css` = 30+ vars; `tokens.ts` typed mirror; directional `--pos/--neg/--warn` reserved for numeric direction only; card tone = left border, never background; `prefers-reduced-motion` kills all animations; zero hard-coded hex in components.

---

## 11. File Map

```
AGENTS.md                  ← ops runbook (short, authoritative)
README.md                  ← this file (sole definitive guide)
.github/workflows/deploy.yml ← CI: test-and-verify (pytest+vitest+build) → deploy-to-oci (appleboy/ssh-action, git pull + compose up)
scripts/setup_oci_server.sh ← OCI bootstrap: 4GB swap, Docker, iptables (80,443,5173,8000) + UFW, /home/ubuntu/app/data/backups
scripts/ship_to_oci.ps1    ← one-click helper: -OciIp <IP>, bootstraps + scp data/app.db + scp .env (PowerShell 5.1)
docs/
  DATA_CONTRACT.md         ← 57-col dictionary + currency/ID/provenance rules
  SCORING_SPEC.md          ← locked v1 scoring design
  reports/INDEX.md         ← engineering milestone archive index (historical)
docker-compose.yml         ← api 0.0.0.0:8000 (restart unless-stopped, healthcheck, ./data:/app/data) + frontend profile 0.0.0.0:5173 (service_healthy)
.env.example               ← OPENROUTER_API_KEY / SEC_USER_AGENT / DATABASE_URL=sqlite:////app/data/app.db / ENVIRONMENT=production / VITE_API_BASE_URL= / REFRESH_*
backend/
  app/main.py              ← FastAPI + millisecond logging + migration guard + JobWorker
  app/config.py            ← env + seed discovery
  app/db.py                ← SQLite WAL engine
  app/models.py            ← 3NF models (companies, snapshots, statements, derived, TTM, scores, halal, jobs, llm_cache, portfolio)
  app/services/            ← 64 modules: importer (genesis-decoupled, ms-logged), calculation_pipeline, ingest, mapping, scoring, forensic (Altman/Beneish/Sloan/Piotroski), valuation, portfolio, alerts_daemon, etc.
  app/providers/           ← edgar, yahoo, registry (CA→Yahoo, US→EDGAR+price)
  app/jobs/                ← startup_pipeline, batch_universe_expansion, universe_expansion (ms-logged), backfill, verify_clean_room
  app/api/                 ← 33 routers: wave1/wave2/phase2-4, dossier, forensics, valuation_suite, sectors, stats, screen, restatements, portfolio, alerts, exports, canada, insiders, technicals, curriculum, sector_rotation, backtesting, ops, governance, jobs, chat, llm_admin
  alembic/versions/        ← 17 revisions, head h7i8j9k0l1m2 (no draft files)
  tests/                   ← 55 files, 322 tests (conftest uses isolated .pytest_app.db, JOBS_WORKER_DISABLED=1)
  Dockerfile               ← python:3.12-slim, alembic upgrade head + importer + startup_pipeline + uvicorn
frontend/
  src/styles/tokens.css    ← CSS vars
  src/styles/tokens.ts     ← typed mirror
  src/components/layout/   ← Page, Grid, Card, StatTile, Chip
  src/components/viz/      ← PillarRadar, CompositeGauge, Sparkline, MiniPillarBars, AltmanZGauge, etc.
  src/components/dossier/  ← BankValuationCard, BeneishMatrix, CanadianTaxCard, InsiderActivityCard, TechnicalContextCard, GuidedDCFModal, etc.
  src/lib/sessionCompare.ts← atomic useCompare hook + clearCompare (event-driven, MAX 8)
  src/screens/             ← Home, Dossier, Compare (with clearCompare + basket strip), Screen, Sector, Portfolio, Ops, Governance, Curriculum, SectorRotation, etc.
  vite.config.ts           ← jsdom, localStorage, coverage
  package.json             ← scripts: dev / build (tsc && vite) / test (vitest run) / e2e (playwright)
  nginx.conf               ← proxy /api → api:8000, proxy_read_timeout 120s (LLM), listen 80
  dist/                    ← static build (149 modules)
seed/                      ← READ-ONLY genesis: Sector_Financials_Final_Owner.xlsx (mtime 2026-08-22, git diff clean) + raw/sec_ticker_exchange.json
legacy/                    ← archived refresh.py copies (never executed)
data/                      ← SQLite app.db (WAL, gitignored — data/app.db + data/backups/ + WAL/SHM, 16 MB, host ./data → /app/data), backups/, sec_tickers_cache.json
.gitignore                 ← .env + *.key/*.pem/*.pub/*.p12/*.pfx + data/app.db + data/backups/ + WAL/SHM strict
.env                       ← (gitignored) local secrets; production on OCI at /home/ubuntu/app/.env
```

Hidden/temp files (`__pycache__/`, `.pytest_cache/`, backend `app.db` 4096-byte stub, `test_ephem2.db`) are gitignored and pruned; only `data/app.db` is operational.

---

## 12. Operational Runbook — One-Page Checklist

**Cold boot (empty `data/`):**
```powershell
docker compose up --build -d   # alembic upgrade head → importer reads seed (720) → startup_pipeline computes derived → uvicorn
docker compose logs api -f      # watch millisecond logs; healthcheck passes in ~40s
curl http://localhost:8000/health; curl http://localhost:8000/ready
docker compose --profile frontend up --build -d   # UI at :5173
```
**Warm restart (DB exists):** importer logs `Operational SQLite database already populated … Excel seed reading skipped` and exits instantly — seed file not required.

**Add & score a ticker:** UI Desk “Add & score” input → `POST /api/v1/tickers/ingest {"ticker":"SHOP.TO"}` → poll `GET /api/v1/jobs/{id}` → dossier at `/c/CA:SHOP:TSX`. Or CLI: `docker compose exec api python -m app.services.calculation_pipeline --ticker SHOP.TO` (runs pipeline for one name).

**Backfill / expand:** `docker compose exec api python -m app.jobs.batch_universe_expansion` (85+ curated names) or `python -m app.jobs.universe_expansion` (Russell/TSX/micro). Each run tags `universe_tags`, recomputes global percentiles, and materializes `sector_cache_summaries`.

**Backups:** `POST /api/v1/ops/backup` → checkpoint + copy; list via `GET /api/v1/ops/backups`; Vacuums via `POST /api/v1/ops/vacuum`.

**Compare:** Dossier “Add to compare” toggles the atomic basket (max 8, `compare-updated` event). Compare page shows `Selected (?/8)` from `?ids=` plus `Basket (n/8)` strip with `Load basket` and `Clear basket`. `Clear all` empties `localStorage`, dispatches `compare-updated`, and clears `?ids`.

---

## 13. Governance & Not Advice

Personal research software. **Not investment advice.** Scores are research signals, never trade orders. The halal flag is an approximation, not a religious ruling. Verify everything before relying on it. LLM narration is OpenRouter `:free` only, cached in `llm_cache`, never overwrites fundamentals, carries its own disclaimer.

**Secrets in `.env`** (never committed). No paid APIs in v1. OpenRouter key is optional; without it, chat endpoints return deterministic grade-10 fallback from `llm.py`.

---

## 14. Startup Migration Guard — Manual Recovery

`app.main.lifespan` compares live DB `alembic_version` vs `ScriptDirectory.get_current_head()` and **refuses to boot** on mismatch (missing / behind / diverged). The app never stamps or migrates automatically.

```powershell
cd backend
# If schema was created out-of-band (create_all) and matches head:
$env:DATABASE_URL = 'sqlite:///../data/app.db'
python -m alembic stamp head
# If schema genuinely lacks migrations:
python -m alembic upgrade head
```
Then `docker compose restart api`. `GET /api/v1/system/health/telemetry` shows `migration_revision` vs `alembic_head`.

---

## 15. ROIC Denominator Caveats

`invested_capital = total_debt + book_equity - cash`. Buybacks shrink book equity, inflating ROIC for compounders (AAPL-class):
- `invested_capital <= 0` → ROIC NULL, `negative_capital`, confidence low.
- `invested_capital / total_assets < 0.05` or `roic > 1.0` → confidence low, `distorted_low_denominator`.
- Banks/insurers/credit (GICS Financials or Banks/Insurance/Credit sheets) → ROIC `not_meaningful` / `bank_excluded`; use CET1 + efficiency. UI suppresses green “ROIC 20%+” / “MOAT” badges when confidence low and shows amber “ROIC distorted” chip.

---

## 16. Oracle Cloud (OCI) Deployment — Automated CI/CD (2026-09-06)

**Target:** `VM.Standard.E2.1.Micro` — Ubuntu 24.04, AMD64, 1 OCPU, 1 GB RAM, 50 GB boot — `https://github.com/iMunib/Stock_analysis_app`

The repository is fully automated for OCI. Manual work is limited to one local command and three GitHub secrets.

### 16.1 What the automation does

| Layer | File | Role |
|---|---|---|
| **Bootstrap** | `scripts/setup_oci_server.sh` | Idempotent one-shot: 4 GB swap (`/swapfile` + `vm.swappiness=10` + `/etc/fstab`), `apt-get update` + `ca-certificates curl gnupg git ufw iptables-persistent`, Docker Engine + Compose via `get.docker.com` + `usermod -aG docker ubuntu`, Oracle iptables unlock (`INPUT 6 … --dports 80,443,5173,8000`), `netfilter-persistent save`, `ufw allow 22/80/443/5173/8000` + `ufw --force enable`, `mkdir -p /home/ubuntu/app/data/backups` |
| **CI** | `.github/workflows/deploy.yml` | `test-and-verify` (ubuntu-latest, Python 3.12 `pip install -r backend/requirements.txt` → `python -m pytest tests/ -q`, Node 20 `npm ci` → `npm test -- --run` + `npm run build`) — gate for deploy. `deploy-to-oci` (only on `push` to `main` after tests pass) via `appleboy/ssh-action@v1.0.3` with `OCI_HOST / OCI_USERNAME / OCI_SSH_KEY` → `git clone || fetch+reset`, `docker compose --profile frontend down && up --build -d`, `docker compose ps` + logs |
| **Local helper** | `scripts/ship_to_oci.ps1 -OciIp <IP>` | One-click: (1) bootstrap remote via `ssh -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ubuntu@$OciIp "curl -fsSL https://raw.githubusercontent.com/iMunib/Stock_analysis_app/main/scripts/setup_oci_server.sh -o setup.sh && chmod +x setup.sh && ./setup.sh"` (uploads local script if present, else curls from GitHub), (2) `scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" "data/app.db" ubuntu@${OciIp}:/home/ubuntu/app/data/app.db`, (3) `scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ".env" ubuntu@${OciIp}:/home/ubuntu/app/.env`, then prints next-step `docker compose --profile frontend up --build -d` |
| **Persistence** | `docker-compose.yml` + `.gitignore` + `.env.example` | `docker-compose.yml` binds `./data:/app/data` (SQLite WAL durable store), `0.0.0.0:8000:8000` + `0.0.0.0:5173:80` with `restart: unless-stopped` and `service_healthy` gate; `frontend/nginx.conf` proxies `/api/` → `api:8000` with `proxy_read_timeout 120s`; `.gitignore` strictly ignores `.env`, `*.key/*.pem/*.pub/*.p12/*.pfx`, `data/app.db`, `data/*.db-journal|wal|shm`, `data/backups/`; `.env.example` documents production defaults `DATABASE_URL=sqlite:////app/data/app.db`, `ENVIRONMENT=production`, `VITE_API_BASE_URL=` (same-origin) |

### 16.2 One-time setup (operator)

```powershell
# 1. Create three GitHub repo secrets (Settings → Secrets → Actions):
#    OCI_HOST      = <OCI public IP>         e.g., 129.80.x.x
#    OCI_USERNAME  = ubuntu
#    OCI_SSH_KEY   = <contents of ssh-key-2026-09-06.key> (private key, no passphrase)

# 2. Open OCI Console → VCN → Security List → Ingress: allow 22, 80, 443, 5173, 8000 from 0.0.0.0/0
#    (OS-level iptables/UFW is handled by setup_oci_server.sh, but VCN still gates externally.)

# 3. From your Windows workstation (repo root), one command ships everything:
powershell -ExecutionPolicy Bypass -File scripts/ship_to_oci.ps1 -OciIp 129.80.x.x

# 4. SSH and bring stack up (if not already via CI push):
ssh -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ubuntu@129.80.x.x
cd /home/ubuntu/app
# helper already created /home/ubuntu/app/data/backups; if fresh VM without DB/.env, the helper uploaded them
docker compose --profile frontend up --build -d
docker compose ps
docker compose logs api --tail 50
curl http://localhost:8000/health   # {"status":"ok"}
curl http://localhost:8000/ready    # {"status":"ready","database":"ok"}
# UI: http://<OCI_IP>:5173   API: http://<OCI_IP>:8000
```

After this, **every `git push` to `main` auto-runs tests and redeploys** via GitHub Actions — no manual SSH required. `data/app.db` and `.env` are never overwritten by `git reset --hard` (deploy script preserves them; `.gitignore` prevents commits).

### 16.3 Persistence & safety guarantees

- **DB is gitignored live state.** `data/app.db` + `data/backups/` + WAL/SHM files are ignored, so local mutations and remote 928-company production DB never collide in Git. CI `git fetch && reset --hard origin/main` preserves `data/app.db` and `.env` via the deploy script’s stash/restore guard.
- **`.env` never committed.** `.env`, `*.key`, `*.pem`, `*.pub` are strictly ignored; `.env.example` is the only template. Production `DATABASE_URL` is `sqlite:////app/data/app.db` (absolute Docker path); local dev may use `sqlite:///./data/app.db`.
- **Swap prevents OOM.** 1 GB Micro without swap OOM-kills `uvicorn` + `alembic` + `importer` during cold build. 4 GB `/swapfile` + `vm.swappiness=10` + `fstab` persistence is created idempotently; re-running the script is safe.
- **Firewall dual-layer.** Oracle Ubuntu images ship restrictive `iptables INPUT` chain — the script inserts `ACCEPT` for `80,443,5173,8000` and persists via `netfilter-persistent`, then enables `UFW` for the same ports + `22`. VCN Security List must still allow them externally (step 2 above).

### 16.4 Verify after deploy

```bash
# On OCI host:
free -h                          # Swap: 4.0G
swapon --show                    # /swapfile 4G
sudo ufw status verbose          # 22,80,443,5173,8000 ALLOW
sudo iptables -L INPUT -n --line-numbers | head -20
docker compose --profile frontend ps   # invest-api (healthy) + invest-frontend (Up)
docker compose logs api --tail 30    # millisecond timestamps .SSS
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/api/v1/stats | jq
```

---

*Generated 2026-09-06 — 322 backend / 170 frontend tests green, 149 Vite modules (834 kB / 218 kB gzip), 928-company quality universe verified, OCI bootstrap + GitHub Actions CI/CD automated (VM.Standard.E2.1.Micro, 4 GB swap, UFW+iptables unlock, 0.0.0.0 binds, DB/.env gitignored persistence).* 
