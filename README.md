# Investment Stock Application â€” Master README

**A personal, local equity-research desk for the S&P 500 + S&P/TSX Composite (720 companies).**
Personal research software. **Not investment advice.** Not a product, not a broker, not a subscription service.

> This file is the complete project context for any AI (or human) taking over the project.
> It contains the mission, business constraints, hard rules, architecture, phase history,
> API surface, data contracts, scoring design, run/test commands, current state, and known
> quirks. Read it top to bottom once, then use the linked deep-dive docs.

---

## 1. Mission and business context

**Owner/user:** Munib (Ottawa, Canada). Single user. Local-first. No cloud, no paid APIs, no auth.

**The problem it solves:** The user compiled a hand-curated owner workbook
(`seed/Sector_Financials_Final_Owner.xlsx`) â€” 720 companies (500 S&P 500 + 220 S&P/TSX
Composite) with latest-fiscal-year financials in each company's **native currency**, plus
custom industry groupings and QC notes. He needed:

1. That frozen snapshot preserved exactly (never overwritten) in a queryable database.
2. Free history (SEC EDGAR for US names, Yahoo Finance for Canadian names and prices)
   layered on top, per company, on demand.
3. A deterministic 0â€“10 research score (quality/value/growth/risk) that is honest about
   missing data â€” never inventing numbers.
4. An AAOIFI-style halal *flag* (informational, never a filter).
5. A fast local UI to search, read dossiers, compare up to 8 names, and browse sectors.

**Business constraints (locked):**

- Local Docker only. No Redis, no Celery, no Postgres, no cloud queues, no paid APIs.
- LLM integration (Phase 6 plan) would be OpenRouter-only, cached, and never allowed to
  overwrite fundamentals. Not yet implemented.
- This is **personal research software, not investment advice**. Every API/UI surface
  carries that disclaimer. Scores are research signals, never trade orders.
- The halal flag is an approximation, explicitly "not a religious ruling," and is never
  a default filter (opt-in `?halal=candidate` may return 0 rows â€” that is correct behavior).

---

## 2. Hard rules an AI must never violate

These are frozen contracts. Breaking any of them is a regression:

1. **Never mix CAD and USD money.** Every money field carries its company's native
   currency. Cross-border comparison uses unitless ratios only (ROE, ROA, PE, PB,
   FCF margin, EV/EBITDA). The "All" sector view is score/ratio-only; money medians
   stay split per currency. Never average money across currencies.
2. **Never overwrite owner-workbook values.** Seed FY rows (`fiscal_year IS NULL`,
   `source = Sector_Financials_Final_Owner.xlsx`) are immutable. Providers may only
   FILL NULLs on that row, and non-NULL owner values are restored even if a provider
   returned something different. Provider statements INSERT their own
   `(company_id, fiscal_year, period_type='FY')` rows.
3. **Never invent numbers.** Missing data is NULL + a quality flag. Missing growth
   history â†’ growth pillar NULL (with a coverage penalty), never a guess. Missing
   halal inputs â†’ `unknown`, never `halal`.
4. **Company_ID is frozen:** `US:TICKER:US` or `CA:TICKER:TSX` (dots kept,
   `CA:BN:TSX` = Brookfield; `CA:NA:TSX` = National Bank of Canada, *never* NVIDIA).
   Loose IDs like `US:AES:NYSE` normalize to `US:AES:US`; `CA:*:NYSE` is invalid.
5. **Never run `seed/refresh.py --mode all`** (or any scrape of the workbook). The
   statement columns are frozen. Copies of refresh.py live in `legacy/` untouched.
6. **Scoring weights are locked:** 0.30 Quality + 0.25 Value + 0.25 Growth + 0.20 Risk
   (Risk inverted). Coverage penalties: 3 pillars Ã—0.92, 2 Ã—0.80, 1 Ã—0.65, 0 â†’ NULL
   with signal `insufficient_data`.
7. **Money scale:** values are stored verbatim as currency units
   (US:MMM Revenue = 24,948,000,000 â‰ˆ $24.9B actual). Never divide/multiply by 1e6.
8. **Banks/insurers:** do not invent Total_Debt/FCF/Gross_Profit. The provider fill
   step skips those fields for Financials-sector companies. (Note: many banks DO have
   seed Total_Debt â€” e.g. RY = 545,439,000,000 â€” that is owner data; do not null it.)
9. **No chart npm libraries.** SVG + CSS only for all bars/histograms.

---

## 3. Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Docker Compose â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  invest-api (FastAPI, :8000)          invest-frontend (nginx, :5173)         â”‚
â”‚  â”œâ”€ alembic upgrade head              â”œâ”€ static React build (Vite+TS+TW)     â”‚
â”‚  â”œâ”€ python -m app.services.importer   â””â”€ /api/* proxied â†’ host.docker.internal:8000
â”‚  â””â”€ uvicorn + JobWorker daemon thread                                        â”‚
â”‚  volumes: ./seed:/seed:ro   ./data:/app/data (SQLite, WAL)                   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚ seed workbook (read-only)            â”‚ browser (localhost:5173)
         â–¼                                      â–¼
  Sector_Financials_Final_Owner.xlsx    React UI: Desk / Sectors / Dossier /
  (720 rows, 57 cols, 48 sheets)        Compare / Jobs, persistent search
```

### Backend (Python 3.12-slim container; FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic + SQLite)

| Module | Role |
|--------|------|
| `app/main.py` | FastAPI app; CORS for :5173; lifespan starts the JobWorker daemon thread |
| `app/config.py` | env config; seed-workbook discovery (container `/seed`, repo `seed/`) |
| `app/db.py` | SQLAlchemy engine (SQLite WAL + busy_timeout=5000, FK on) |
| `app/models.py` | companies, financial_snapshots, data_quality_flags, placements, import_runs, scores, halal_flags, jobs |
| `app/services/importer.py` | owner workbook â†’ DB (idempotent, mtime-skipped, `--force`); imports placements (Primary/Extra/GICS) + quality flags (incl. 10 workbook-level rows with NULL company) |
| `app/services/ids.py` | frozen Company_ID parse/format/normalize |
| `app/services/mapping.py` | resolve `AAPL`/`RY.TO`/`CA:RY:TSX`; universe_master.csv authoritative (bare tickers, Yahoo symbols incl. `IIP.UN â†’ IIP-UN.TO`, 500 US CIKs); SEC company_tickers.json fallback (cached) |
| `app/providers/edgar.py` | SEC companyfacts (1 call/CIK), 10-K FY frames incl. instant facts, token bucket 8 req/s (state exposed via `bucket_state()`), 403/429 back-off |
| `app/providers/yahoo.py` | yfinance annual statements + price; lazy import; 0.2s serialization; pure `parse_frames()` |
| `app/providers/registry.py` | US â†’ EDGAR statements + Yahoo price; CA â†’ Yahoo; graceful Yahoo fallback for US on EDGAR failure |
| `app/services/ingest.py` | frozen overwrite policy; first-provider-wins; bank/insurer carve-out (no debt/gross fills on Financials seed rows) |
| `app/services/scoring.py` | pure scoring engine (method_version=v1) â€” see Â§6 |
| `app/services/halal.py` | AAOIFI-style flag (activity screen + 30/30 ratios; impure income always unknown in v1) |
| `app/services/scoring_service.py` | peer sets (custom-industry+currency â‰¥8 else GICS+currency), two-pass computeâ†’rank, seed enrichment, idempotent upserts |
| `app/services/jobs.py` + `job_worker.py` | SQLite-backed job queue (backfill/ingest/recompute); one daemon worker; owns its own session; failures â†’ status=failed |
| `app/api/*` | routers: companies, sectors, stats (P1); phase2 (ingest/financials/coverage); phase3 (scores/rankings/halal); phase4 (search/dossier/compare/similar/sector snapshot/research meta); jobs (6A: 202+poll) |

### Frontend (React 18 + Vite 5 + TypeScript strict + Tailwind 3; "night research desk" theme)

| Module | Role |
|--------|------|
| `src/components/AppShell.tsx` | sticky top nav (Desk/Sectors/Compare/Jobs â€” Jobs hidden if API 404s), persistent debounced search (250ms) with dropdown, compare-count badge, footer disclaimer |
| `src/components/ErrorBoundary.tsx` | never a blank screen |
| `src/components/ui.tsx` | SignalBadge, HalalBadge, Score, Spinner, ErrorBanner (retry), CompanyLink, useDebounced |
| `src/components/bars.tsx` | SVG ScoreBar (hollow on NULL), PillarMiniBars (QÂ·VÂ·GÂ·R) |
| `src/screens/Home.tsx` | Desk: status stats, signal histogram (CSS bars), "Needs history" callout, Top 10 USD + CAD + Top 10 All (score-only), add-ticker flow (ingest â†’ recompute â†’ dossier) |
| `src/screens/SectorsHub.tsx` | 41 cards (30 custom industries + 11 GICS groups), All/USD/CAD toggle (All default), counts + lazy medians |
| `src/screens/Sector.tsx` | currency view toggle; ALL = score-only table (both currencies) + split USD/CAD money panels; USD/CAD = classic table + money medians; checkbox â†’ "Compare selected (2â€“8)" |
| `src/screens/Dossier.tsx` | identity â†’ verdict (signal + peer rank first) â†’ gaps â†’ pillar board â†’ why bullets â†’ snapshot â†’ history (table + SVG bars, <3 rows = callout) â†’ similar â†’ halal â†’ actions (session/localStorage compare basket, "Compare with similar") |
| `src/screens/Compare.tsx` | 2â€“8 ids via URL, per-row pillar mini-bars, best-cell highlighting, mixed-currency warning banner |
| `src/screens/Jobs.tsx` | polls `/api/v1/jobs` every 5s |
| `src/api/client.ts` | fetch wrapper: 15s timeout, JSON-parse errors â†’ banner, typed ApiError |
| `src/api/copy.ts` | deterministic grade-10 copy templates (signal/growth/penalty/halal/why-bullets) â€” no LLM |
| `src/lib/*` | `bars.ts` (SVG math), `allCurrency.ts` (composeAll â€” never blends money), `compare.ts` (max-8 builder), `nav.ts` (nav items + sector keys), `sessionCompare.ts` (localStorage `compareIds`, max 8) |

---

## 4. Data contracts (deep dives)

- **`docs/DATA_CONTRACT.md`** â€” the 57-column dictionary for the owner workbook,
  Company_ID rules, currency rules, NULL+flag policy, intentional blanks,
  as-of dating (fiscal_year stays NULL in seed rows; as_of_date = Price_AsOf),
  the value-scale note (verbatim units), Phase 2 provider provenance
  (`source` âˆˆ owner xlsx | sec_companyfacts | yfinance; fetched_at; provider_as_of),
  Yahoo symbol rules, and the frozen overwrite policy.
- **`docs/SCORING_SPEC.md`** â€” the locked scoring design (implemented in Phase 3).
- **`seed/readme.md`** â€” the original owner workbook dictionary (read-only source of truth).

---

## 5. Scoring model (method_version=v1, deterministic, no LLM)

```
Composite = 0.30Â·Quality + 0.25Â·Value + 0.25Â·Growth + 0.20Â·Risk      (each 0â€“10; Risk inverted)
Coverage penalty: 4 pillars â†’ Ã—1.0   3 â†’ Ã—0.92   2 â†’ Ã—0.80   1 â†’ Ã—0.65   0 â†’ NULL
```

- **Quality:** Piotroski-style F-score (impossible tests reduce the denominator; NULL
  debt skips leverage; accruals is a current-year test) mapped 0â€“10, blended 70/30 with
  level quality (ROE, ROA, FCF margin or gross margin, Novy-Marx GP/Assets) plus
  sector-currency percentiles. Banks/insurers use ROE/ROA/ROAA/Efficiency/CET1/NIM instead.
- **Value:** earnings yield + PE/PB/EV-EBITDA percentiles vs same-currency peers
  (custom industry â‰¥8 members, else GICS sector; currencies never mixed).
  Negative earnings â†’ PE skipped (not cheap, not zero).
- **Growth:** revenue/EPS/FCF CAGR over min(10, available) FY, needs â‰¥3 positive points;
  piecewise map (âˆ’40%â†’0 â€¦ 0%â†’5 â€¦ +40%â†’10), winsorized. One-year change is never a CAGR.
- **Risk:** net debt/EBITDA, liabilities/assets, interest coverage; banks invert CET1 and
  leverage ratio; earnings volatility only with â‰¥5 FY.
- **Peers/rank:** rank 1 = best composite in the peer set; NULL composites excluded.
- **Signal map:** 8â€“10 Strong candidate Â· 6.5â€“7.9 Constructive Â· 5â€“6.4 Mixed Â·
  3.5â€“4.9 Weak Â· 0â€“3.4 Avoid Â· NULL â†’ insufficient_data.
- **Halal flag (separate table):** activity screen fails banks/insurers/credit/conventional
  financials + keyword list; ratios vs market cap (debt <30%, cash <30%); impure income is
  unknown in v1 â†’ nothing reaches `halal_candidate`; missing inputs â†’ `unknown`.

**Why scores skew low (by design):** 713/718 scored names lack 3+ years of history, so
growth is NULL and the composite takes the 3-pillar penalty. Current live histogram:
constructive 9 Â· mixed 136 Â· weak 345 Â· avoid 228 Â· insufficient_data 2 (IIP.UN has no
data at all; HONA-style blanks are preserved). Explain, never hide.

---

## 6. Phase history (all delivered; reports in repo root)

| Phase | Delivered | Report |
|-------|-----------|--------|
| 1 | Owner workbook (720 companies) â†’ SQLite; read-only FastAPI; Docker; docs; AGENTS.md runbook | [PHASE1_REPORT.md](PHASE1_REPORT.md) |
| 2 | History layer: SEC companyfacts + yfinance providers; frozen overwrite policy; mappings; live sample ingest (AAPL/MSFT 20 FY, RY/SHOP 5 FY CAD); provider provenance | [PHASE2_REPORT.md](PHASE2_REPORT.md) |
| 3 | Deterministic scores v1 + signals + halal flags; peer sets; rankings; 718/720 scored (2 honest insufficient_data) | [PHASE3_REPORT.md](PHASE3_REPORT.md) |
| 4 | Research API: search, dossier, compare (mixed-currency warning), similar, sector snapshot, research/meta | [PHASE4_REPORT.md](PHASE4_REPORT.md) |
| 5 | Real React UI (night research desk): Desk/Sectors/Dossier/Compare; vitest; nginx /api proxy | [PHASE5_REPORT.md](PHASE5_REPORT.md) |
| 6A | Async jobs (SQLite queue + worker thread): backfill/ingest/recompute; 202 + poll; SEC limiter stats; WAL | *(folded here â€” see test_jobs.py; the only report gap)* |
| 7 | UI shell + sector explorer: app nav, persistent search, sectors hub (custom+GICS cards), full ranked sector table, compare-selected, jobs page, error banner/boundary | [PHASE7_REPORT.md](PHASE7_REPORT.md) |
| 8 | Dossier depth: verdict-first, SVG pillar bars, deterministic why-bullets, history bars, gaps panel up, session compare basket, 404 with search | [PHASE8_REPORT.md](PHASE8_REPORT.md) |
| 9 | All-currency default (never blends money), Playwright e2e (7/8, 1 timing flake), reduced-motion CSS, localStorage compare basket, BACKLOG.md | [PHASE9_REPORT.md](PHASE9_REPORT.md) |

---

## 7. API surface (all under http://localhost:8000)

| Method & path | Purpose |
|---|---|
| GET `/health`, `/ready` | liveness / DB ping |
| GET `/api/v1/meta/disclaimer` | disclaimer string |
| GET `/api/v1/companies?q=&sector=&industry=&country=&limit=&offset=` | list (720) |
| GET `/api/v1/companies/{id}` | identity + latest snapshot + flags + placements |
| GET `/api/v1/companies/{id}/financials?years=10` | annual rows newest-first |
| GET `/api/v1/companies/{id}/dossier` | one payload: identity + enriched snapshot + history + score + halal + data_gaps |
| GET `/api/v1/companies/{id}/similar?n=5` | same peer set; 409 if subject score NULL |
| GET `/api/v1/search?q=&limit=` | ticker/name/ID/Yahoo symbol |
| GET `/api/v1/compare?ids=a,b` | 2â€“8; mixed-currency warning; money per-row |
| GET `/api/v1/sectors` | custom industries + GICS groups with counts |
| GET `/api/v1/sectors/{sheet}/snapshot?currency=USD|CAD` | counts, medians, histogram, top/bottom 10 |
| GET `/api/v1/sectors/{sheet}/rankings?currency=ALL|USD|CAD&limit=500` | ranked table (ALL = score-only, both currencies, per-row money, no blended medians) |
| GET `/api/v1/rankings?scope=seed&currency=&signal=` | global ranking |
| GET `/api/v1/scores/recompute` (POST) | `{universe: "seed"|"company_id", company_id}` â€” CPU only |
| GET `/api/v1/companies/{id}/score`, `/api/v1/scores/summary` | score payload / histogram |
| GET `/api/v1/coverage`, `/api/v1/research/meta` | history coverage / research-layer health |
| POST `/api/v1/tickers/ingest` | `{ticker}` synchronous (seconds) |
| POST `/api/v1/jobs/backfill` | **202 + poll** (async since 6A); 409 if one is queued/running |
| GET `/api/v1/jobs`, `/api/v1/jobs/{id}` | recent jobs / poll status+progress+provider_stats |

No scoring endpoints existed before Phase 3; no LLM endpoints exist; no fetch-on-GET
(GETs never hit the network).

---

## 8. Running it (Windows PowerShell)

```powershell
cd "C:\Users\RehmanPC\Downloads\Investment Stock Application"

# API + UI (UI is optional profile)
docker compose up --build -d
docker compose --profile frontend up --build -d

# Verify
curl http://localhost:8000/health                 # {"status":"ok"}
curl http://localhost:8000/api/v1/stats           # companies: 720
# UI:  http://localhost:5173   (nginx :80 in-container; /api proxied to the API)

# Backend tests (85 + jobs/phase9 = 88)
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q

# Frontend unit tests + build
cd ..\frontend
npx vitest run        # 29 tests
npm run build         # tsc strict + vite

# Playwright e2e (UI must be up; chromium via `npx playwright install chromium`)
npx playwright test app.spec.ts

# Narration (LLM, optional): copy .env.example to .env, set OPENROUTER_API_KEY.
# Free models only (ids containing :free). Cached in SQLite; "Narration (not the score)".
# Next fiscal year: Jobs page â†’ "Refresh sample (5 names)" (202 + poll), or set
# REFRESH_ENABLED=1 + REFRESH_INTERVAL_HOURS=168 in .env for a weekly auto-refresh.
# The owner row is never overwritten; new years are INSERTed by EDGAR/Yahoo.
```

Adding a ticker not in the 720: Desk â†’ "Add & score" (ingest â†’ recompute â†’ dossier),
or `POST /api/v1/tickers/ingest {"ticker":"SHOP.TO"}`.

The importer is idempotent and skips re-import unless the workbook mtime changed
(`docker compose exec api python -m app.services.importer --force` to force).

---

## 9. Current state (as of 2026-09-02)

- 720 companies imported (500 USD / 220 CAD); placements 1,506 = 720 Primary + 66 Extra
  + 720 GICS; quality flags 2,026 (incl. 10 workbook-level with NULL company).
- Snapshots: 720 seed rows + ~55 provider history rows (AAPL/MSFT 20 FY each from EDGAR;
  RY/SHOP/XOM 5 FY from Yahoo). Scores: 718 scored, 2 insufficient_data, 0 errors;
  growth NULL on 713 (expected until the full-history backfill runs).
- Alembic heads: `d6e7f8a9b001` (phase6a_jobs) â† c3d4e5f6a780 (scores/halal) â†
  b7f2a91c4d50 (provider provenance) â† ccf1cb226400 (initial).
- Tests: backend pytest **88 passed**; frontend vitest **29 passed**; `npm run build` âœ“;
  Playwright 7/8 (one timing flake, passes individually).
- Seed workbook untouched throughout (mtime 2026-08-22 21:28:20).

---

## 10. Known quirks & housekeeping (safe to clean)

- `backend/.alembic_draft.db`, `backend/.debug_probe.py`, root `.audit2_phase2.py`,
  `.audit3_phase2.py`, and a `.probe_*.py` â€” dev scratch files. Deletion was blocked by
  the host Safety Guard during the builds; they are inert and gitignored. Remove manually.
- `frontend/src/screens/*.tsx.stale` â€” Phase 5 Windows-casing leftovers (lowercase
  duplicates renamed aside so the PascalCase modules compile). Inert to tsc/vite.
- `backend/alembic/versions/__pycache__` â€” Python bytecode, harmless.
- Playwright "Banks All" spec is timing-flaky in full-suite runs (passes individually,
  866ms; page verified correct via debug spec). Test-env contention, not a code bug.
- `compare.tsx.stale`/`sector.tsx.stale` follow the same pattern as above.
- Windows lesson: never rely on case-only overwrites (`compare.tsx` â†’ `Compare.tsx`);
  always two-step rename through a temp name.

---

## 11. Roadmap

See **[BACKLOG.md](BACKLOG.md)** (written in Phase 9, intentionally not implemented):
watchlist/portfolio Â· LLM summaries via OpenRouter (cached, disclaimer, never overwriting
fundamentals) Â· full-720 history backfill via the async worker Â· local telemetry Â·
halal interest-income enrichment (would make `halal_candidate` reachable) Â· GICS
sub-industry drill-down Â· CSV export Â· snapshot performance materialization Â· light mode.

Phase 6Bâ€“6D (cache/telemetry/config YAML) were never started â€” per the Phase 6A STOP.

---

## 12. File map (repo root)

```
AGENTS.md                  ops runbook (short, authoritative)
BACKLOG.md                 future stories (do not implement without a phase prompt)
PHASE*_REPORT.md           per-phase evidence: verdicts, commands, URLs, deviations
README.md                  this file
docs/DATA_CONTRACT.md      field dictionary + currency/ID/provenance/overwrite rules
docs/SCORING_SPEC.md       locked scoring design (implemented v1)
docker-compose.yml         api (8000) + frontend profile (5173)
.env.example               OPENROUTER_API_KEY / SEC_USER_AGENT / DATABASE_URL
backend/                   FastAPI app, alembic, tests (88), Dockerfile
frontend/                  React app, vitest (29), playwright e2e (8), Dockerfile
seed/                      READ-ONLY owner data: xlsx + readme + raw + scripts (+refresh.py â€” never run)
legacy/                    archived copies of refresh.py (never executed)
data/                      SQLite app.db (gitignored), .gitkeep
```

---

*Not investment advice. Scores are research signals, never trade orders. The halal flag
is an approximation, not a religious ruling. All data is local; verify everything before
relying on it.*


---

## Sprint (2026-09-02): layout + data trust — what changed

- **History sanity (backend):** EDGAR parser now rejects quarterly facts (duration gate ~300-400d, no `CY####Q1` frames, prefers 365d duplicates) — the root cause of MSFT's fake $23-31B "FY2017-2019". `app/services/history_sanity.py::sanitize_history` runs on the read path: suspect years (revenue < 0.25x or > 4x the strong-year median) stay in the table with a chip "excluded from growth — possible filing tag error" but are excluded from growth CAGR and bars. Real holes (2022 NULL) stay holes.
- **Number formatting:** `frontend/src/lib/format.ts` — `percentish()` shows ROE/ROA/margins as `30.2%` whether stored as 0.302 or 30.2 (compare no longer shows 0.3); multiples one decimal; money always carries currency; NULL is "—".
- **Dossier 12-column grid (~1280px):** identity hero (8) + verdict card (4) in one row; 4 pillar bars in ONE row; why+gaps (7) beside a compact similar-table (5); snapshot as a 4-wide tile grid with YoY deltas (green/red) incl. debt/cash/net-debt/shares; history table with YoY column + suspect chips beside sanitized-only bars; watch toggle; 10-K (EDGAR) / SEDAR+ link; narration collapsed below. Mobile collapses to 1 column <900px.
- **Compare research board:** sticky company column, percent/multiple formatting, per-row SVG pillar bars primary, best-value highlight row under headers, Halal column only with `?halal=1`.
- **Watchlist:** localStorage `watchIds` (max 50), star on dossier, Desk watchlist grid.
- Phase 6A-era bug fixed: compare basket key was a placeholder; now the contracted `compareIds`.
