# Investment Stock Application — Master README

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
(`seed/Sector_Financials_Final_Owner.xlsx`) — 720 companies (500 S&P 500 + 220 S&P/TSX
Composite) with latest-fiscal-year financials in each company's **native currency**, plus
custom industry groupings and QC notes. He needed:

1. That frozen snapshot preserved exactly (never overwritten) in a queryable database.
2. Free history (SEC EDGAR for US names, Yahoo Finance for Canadian names and prices)
   layered on top, per company, on demand.
3. A deterministic 0–10 research score (quality/value/growth/risk) that is honest about
   missing data — never inventing numbers.
4. An AAOIFI-style halal *flag* (informational, never a filter).
5. A fast local UI to search, read dossiers, compare up to 8 names, and browse sectors.
6. ETF Universe cohort tags (S&P 500, TSX, SPUS Halal, QQQ Nasdaq 100, VONV Russell 1000 Value) with segmented cohort screening.
7. Deep Forensic Accounting Suite: Altman Z/Z''-Score, Schilit Earnings Quality, Sloan Accruals, Penman Reformulation, and 8-variable Beneish M-Score ($M \le -1.78$) with automatic bank/insurance capital structure exclusion.
8. True Shareholder Yield factoring in Stock-Based Compensation (SBC) dilution offset and tracking organic float shrink.
9. Two-page institutional research factsheet print memo (`@media print`).

**Business constraints (locked):**

- Local Docker only. No Redis, no Celery, no Postgres, no cloud queues, no paid APIs.
- LLM integration (Phase 6 plan) would be OpenRouter-only, cached, and never allowed to
  overwrite fundamentals. Not yet implemented.
- This is **personal research software, not investment advice**. Every API/UI surface
  carries that disclaimer. Scores are research signals, never trade orders.
- The halal flag is an approximation, explicitly "not a religious ruling," and is never
  a default filter (opt-in `?halal=candidate` may return 0 rows — that is correct behavior).

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
   history → growth pillar NULL (with a coverage penalty), never a guess. Missing
   halal inputs → `unknown`, never `halal`.
4. **Company_ID is frozen:** `US:TICKER:US` or `CA:TICKER:TSX` (dots kept,
   `CA:BN:TSX` = Brookfield; `CA:NA:TSX` = National Bank of Canada, *never* NVIDIA).
   Loose IDs like `US:AES:NYSE` normalize to `US:AES:US`; `CA:*:NYSE` is invalid.
5. **Never run `seed/refresh.py --mode all`** (or any scrape of the workbook). The
   statement columns are frozen. Copies of refresh.py live in `legacy/` untouched.
6. **Scoring weights are locked:** 0.30 Quality + 0.25 Value + 0.25 Growth + 0.20 Risk
   (Risk inverted). Coverage penalties: 3 pillars ×0.92, 2 ×0.80, 1 ×0.65, 0 → NULL
   with signal `insufficient_data`.
7. **Money scale:** values are stored verbatim as currency units
   (US:MMM Revenue = 24,948,000,000 ≈ \$24.9B actual). Never divide/multiply by 1e6.
8. **Banks/insurers:** do not invent Total_Debt/FCF/Gross_Profit. The provider fill
   step skips those fields for Financials-sector companies. (Note: many banks DO have
   seed Total_Debt — e.g. RY = 545,439,000,000 — that is owner data; do not null it.)
9. **No chart npm libraries.** SVG + CSS only for all bars/histograms.

---

## 3. Architecture

```
┌─────────────────────────────── Docker Compose ───────────────────────────────┐
│  invest-api (FastAPI, :8000)          invest-frontend (nginx, :5173)         │
│  ├─ alembic upgrade head              ├─ static React build (Vite+TS+TW)     │
│  ├─ python -m app.services.importer   └─ /api/* proxied → host.docker.internal:8000
│  └─ uvicorn + JobWorker daemon thread                                        │
│  volumes: ./seed:/seed:ro   ./data:/app/data (SQLite, WAL)                   │
└──────────────────────────────────────────────────────────────────────────────┘
         │ seed workbook (read-only)            │ browser (localhost:5173)
         ▼                                      ▼
  Sector_Financials_Final_Owner.xlsx    React UI: Desk / Sectors / Dossier /
  (720 rows, 57 cols, 48 sheets)        Compare / Screen / Jobs, persistent search
```

### Backend (Python 3.12-slim container; FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic + SQLite)

| Module | Role |
|--------|------|
| `app/main.py` | FastAPI app; CORS for :5173; lifespan starts the JobWorker daemon thread |
| `app/config.py` | env config; seed-workbook discovery (container `/seed`, repo `seed/`) |
| `app/db.py` | SQLAlchemy engine (SQLite WAL + busy_timeout=5000, FK on) |
| `app/models.py` | companies, financial_snapshots, data_quality_flags, placements, import_runs, scores, halal_flags, jobs |
| `app/services/importer.py` | owner workbook → DB (idempotent, mtime-skipped, `--force`); imports placements (Primary/Extra/GICS) + quality flags (incl. 10 workbook-level rows with NULL company) |
| `app/services/ids.py` | frozen Company_ID parse/format/normalize |
| `app/services/mapping.py` | resolve `AAPL`/`RY.TO`/`CA:RY:TSX`; universe_master.csv authoritative (bare tickers, Yahoo symbols incl. `IIP.UN → IIP-UN.TO`, 500 US CIKs); SEC company_tickers.json fallback (cached) |
| `app/providers/edgar.py` | SEC companyfacts (1 call/CIK), 10-K FY frames incl. instant facts, token bucket 8 req/s (state exposed via `bucket_state()`), 403/429 back-off |
| `app/providers/yahoo.py` | yfinance annual statements + price; lazy import; 0.2s serialization; pure `parse_frames()` |
| `app/providers/registry.py` | US → EDGAR statements + Yahoo price; CA → Yahoo; graceful Yahoo fallback for US on EDGAR failure |
| `app/services/ingest.py` | frozen overwrite policy; first-provider-wins; bank/insurer carve-out (no debt/gross fills on Financials seed rows) |
| `app/services/scoring.py` | pure scoring engine (method_version=v1) — see §6 |
| `app/services/halal.py` | AAOIFI-style flag (activity screen + 30/30 ratios; impure income always unknown in v1) |
| `app/services/scoring_service.py` | peer sets (custom-industry+currency ≥8 else GICS+currency), two-pass compute→rank, seed enrichment, idempotent upserts |
| `app/services/jobs.py` + `job_worker.py` | SQLite-backed job queue (backfill/ingest/recompute); one daemon worker; owns its own session; failures → status=failed |
| `app/api/*` | routers: companies, sectors, stats (P1); phase2 (ingest/financials/coverage); phase3 (scores/rankings/halal); phase4 (search/dossier/compare/similar/sector snapshot/research meta); jobs (6A: 202+poll) |

### Frontend (React 18 + Vite 5 + TypeScript strict + Tailwind 3; "night research desk" theme)

**Design system foundations**

| Module | Role |
|--------|------|
| `src/styles/tokens.css` | Single source of truth for all CSS custom properties: surface layers (`--bg-0…3`), ink hierarchy (`--ink-0…2`), gold accent (`--accent`, `--accent-weak`, `--accent-strong`), directional status (`--pos`, `--neg`, `--warn`, `--info`) + weak variants, borders, spacing scale (4–48 px), radii, elevation, and `--max-page-width` |
| `src/styles/tokens.ts` | Typed JS mirror of tokens for test assertions and runtime usage |
| `src/index.css` | Keyframes (`fadeIn`, `pageEntrance`, `scaleIn`, `shimmer`, `pulseSubtle`), tabular-nums typography, `prefers-reduced-motion` kill-switch for all animations |
| `frontend/index.html` | Google Fonts: Spectral (display serif), IBM Plex Sans (UI body), IBM Plex Mono (data/numbers) |
| `frontend/tailwind.config.js` | Maps every CSS custom property to a Tailwind utility class; preserves legacy class compatibility |

**Layout primitives** (`src/components/layout/`)

| Module | Role |
|--------|------|
| `Page.tsx` | Max-width wrapper with breadcrumb slot, title/description header, and actions slot; `animate-page` entrance animation |
| `Grid.tsx` | 1→2→3→4-column responsive grid with configurable `cols` prop |
| `Card.tsx` | Dark-surface card with optional `tone` left-border (3 px, never background fill), title/subtitle slots, padding variants (`none`, `sm`, `md`, `lg`) |
| `StatTile.tsx` | KPI tile with label, value (tabular-nums), optional YoY delta (▲ `--pos` / ▼ `--neg`) |
| `Chip.tsx` | Mono badge with `tone`, `showIcon` (tone-default glyph), and `size`; `prefers-reduced-motion` respects animate-chip |

**Visualization primitives** (`src/components/viz/`) — pure SVG, no chart libraries

| Module | Role |
|--------|------|
| `PillarRadar.tsx` | 4-axis SVG diamond radar (Q·V·G·R); null pillar → hollow dot; accessible `aria-label` |
| `CompositeGauge.tsx` | 0–10 arc gauge with tri-color gradient fill, needle at computed angle; accessible `aria-label` |
| `Sparkline.tsx` | SVG line + area sparkline with last-point dot; graceful empty-data fallback |
| `MiniPillarBars.tsx` | Compact 4-bar (Q/V/G/R) summary strip with accessible label |

**Feedback primitives** (`src/components/feedback/`)

| Module | Role |
|--------|------|
| `EmptyState.tsx` | Centered empty state with title, body text, optional CTA button |
| `LoadingSkeleton.tsx` | Shimmer-animated placeholder for async content |

**Core utilities**

| Module | Role |
|--------|------|
| `src/lib/useCountUp.ts` | `requestAnimationFrame` count-up hook; returns target immediately under `prefers-reduced-motion` |
| `src/components/AppShell.tsx` | Sticky top nav (Desk/Sectors/Compare/Jobs), persistent debounced search (250ms) with dropdown, compare-count badge, footer disclaimer; fully tokenized |
| `src/components/ui.tsx` | `SignalBadge`, `HalalBadge` (both now `<Chip>`), `Score`, `Spinner`, `ErrorBanner`, `CompanyLink`, `useDebounced` |
| `src/components/bars.tsx` | SVG `ScoreBar` (hollow on NULL), `PillarMiniBars`; `var(--bg-0)` + `var(--accent)` replace hard-coded hex |
| `src/components/NarrationPanel.tsx` | AI narration card converted to `<Card>` with token styling |
| `src/components/InfoTip.tsx` | Accessible glossary tooltip, fully tokenized |
| `src/api/client.ts` | fetch wrapper: 15s timeout, JSON-parse errors → banner, typed ApiError |
| `src/api/copy.ts` | Deterministic grade-10 copy templates (signal/growth/penalty/halal/why-bullets) — no LLM |
| `src/lib/*` | `bars.ts`, `allCurrency.ts` (composeAll — never blends money), `compare.ts` (max-8), `nav.ts`, `sessionCompare.ts`, `watchlist.ts`, `thesis.ts`, `alerts.ts`, `format.ts` |

**Screens** (all refactored to design system)

| Screen | Primitives used |
|--------|-----------------|
| `Home.tsx` | `<Page>`, `<Grid>`, `<StatTile>`, `<Card>`, `<CompositeGauge size="sm">` |
| `Dossier.tsx` | `<CompositeGauge size="md">` verdict, `<PillarRadar>`, `<StatTile>` tiles with YoY arrows, `<Card>` sub-sections |
| `ForensicCard.tsx` / `ReverseDCFCard.tsx` | `<Card tone={…}>` with token SVGs |
| `Compare.tsx` | Sticky first-column card, `<Sparkline>`, `<MiniPillarBars>`, best-value `bg-accent-weak` highlight |
| `Screen.tsx` | Filter sidebar in `<Card>`, segmented presets, `<Chip>` badges, `<EmptyState>` |
| `SectorsHub.tsx` | `<Card>` tiles with `<CompositeGauge size="sm">` |
| `Sector.tsx` | `<StatTile>` grid, tokenized histogram bars, `<Card>` ranked table |
| `Jobs.tsx` | Progress stepper bar, status `<Chip>` |
| `Learn.tsx` | Glossary items in `<Card>` |

---

## 4. Data contracts (deep dives)

- **`docs/DATA_CONTRACT.md`** — the 57-column dictionary for the owner workbook,
  Company_ID rules, currency rules, NULL+flag policy, intentional blanks,
  as-of dating (fiscal_year stays NULL in seed rows; as_of_date = Price_AsOf),
  the value-scale note (verbatim units), Phase 2 provider provenance
  (`source` ∈ owner xlsx | sec_companyfacts | yfinance; fetched_at; provider_as_of),
  Yahoo symbol rules, and the frozen overwrite policy.
- **`docs/SCORING_SPEC.md`** — the locked scoring design (implemented in Phase 3).
- **`seed/readme.md`** — the original owner workbook dictionary (read-only source of truth).

---

## 5. Scoring model (method_version=v1, deterministic, no LLM)

```
Composite = 0.30·Quality + 0.25·Value + 0.25·Growth + 0.20·Risk      (each 0–10; Risk inverted)
Coverage penalty: 4 pillars → ×1.0   3 → ×0.92   2 → ×0.80   1 → ×0.65   0 → NULL
```

- **Quality:** Piotroski-style F-score (impossible tests reduce the denominator; NULL
  debt skips leverage; accruals is a current-year test) mapped 0–10, blended 70/30 with
  level quality (ROE, ROA, FCF margin or gross margin, Novy-Marx GP/Assets) plus
  sector-currency percentiles. Banks/insurers use ROE/ROA/ROAA/Efficiency/CET1/NIM instead.
- **Value:** earnings yield + PE/PB/EV-EBITDA percentiles vs same-currency peers
  (custom industry ≥8 members, else GICS sector; currencies never mixed).
  Negative earnings → PE skipped (not cheap, not zero).
- **Growth:** revenue/EPS/FCF CAGR over min(10, available) FY, needs ≥3 positive points;
  piecewise map (−40%→0 … 0%→5 … +40%→10), winsorized. One-year change is never a CAGR.
- **Risk:** net debt/EBITDA, liabilities/assets, interest coverage; banks invert CET1 and
  leverage ratio; earnings volatility only with ≥5 FY.
- **Peers/rank:** rank 1 = best composite in the peer set; NULL composites excluded.
- **Signal map:** 8–10 Strong candidate · 6.5–7.9 Constructive · 5–6.4 Mixed ·
  3.5–4.9 Weak · 0–3.4 Avoid · NULL → insufficient_data.
- **Halal flag (separate table):** activity screen fails banks/insurers/credit/conventional
  financials + keyword list; ratios vs market cap (debt <30%, cash <30%); impure income is
  unknown in v1 → nothing reaches `halal_candidate`; missing inputs → `unknown`.

**Why scores skew low (by design):** 713/718 scored names lack 3+ years of history, so
growth is NULL and the composite takes the 3-pillar penalty. Current live histogram:
constructive 9 · mixed 136 · weak 345 · avoid 228 · insufficient_data 2 (IIP.UN has no
data at all; HONA-style blanks are preserved). Explain, never hide.

---

## 6. Phase history (all delivered; reports in repo root)

| Phase | Delivered | Report |
|-------|-----------|--------|
| 1 | Owner workbook (720 companies) → SQLite; read-only FastAPI; Docker; docs; AGENTS.md runbook | [PHASE1_REPORT.md](PHASE1_REPORT.md) |
| 2 | History layer: SEC companyfacts + yfinance providers; frozen overwrite policy; mappings; live sample ingest (AAPL/MSFT 20 FY, RY/SHOP 5 FY CAD); provider provenance | [PHASE2_REPORT.md](PHASE2_REPORT.md) |
| 3 | Deterministic scores v1 + signals + halal flags; peer sets; rankings; 718/720 scored (2 honest insufficient_data) | [PHASE3_REPORT.md](PHASE3_REPORT.md) |
| 4 | Research API: search, dossier, compare (mixed-currency warning), similar, sector snapshot, research/meta | [PHASE4_REPORT.md](PHASE4_REPORT.md) |
| 5 | Real React UI (night research desk): Desk/Sectors/Dossier/Compare; vitest; nginx /api proxy | [PHASE5_REPORT.md](PHASE5_REPORT.md) |
| 6A | Async jobs (SQLite queue + worker thread): backfill/ingest/recompute; 202 + poll; SEC limiter stats; WAL | *(folded here — see test_jobs.py; the only report gap)* |
| 7 | UI shell + sector explorer: app nav, persistent search, sectors hub (custom+GICS cards), full ranked sector table, compare-selected, jobs page, error banner/boundary | [PHASE7_REPORT.md](PHASE7_REPORT.md) |
| 8 | Dossier depth: verdict-first, SVG pillar bars, deterministic why-bullets, history bars, gaps panel up, session compare basket, 404 with search | [PHASE8_REPORT.md](PHASE8_REPORT.md) |
| 9 | All-currency default (never blends money), Playwright e2e (7/8, 1 timing flake), reduced-motion CSS, localStorage compare basket, BACKLOG.md | [PHASE9_REPORT.md](PHASE9_REPORT.md) |
| DS | **Visual design system pass:** design tokens (`tokens.css` + `tokens.ts`), layout primitives (`Page`, `Grid`, `Card`, `StatTile`, `Chip`), SVG viz primitives (`PillarRadar`, `CompositeGauge`, `Sparkline`, `MiniPillarBars`), feedback primitives (`EmptyState`, `LoadingSkeleton`), motion hook (`useCountUp`), all 9 screens refactored; 86 vitest tests green; 0 hard-coded hex in component code | *(this README)* |

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
| GET `/api/v1/compare?ids=a,b` | 2–8; mixed-currency warning; money per-row |
| GET `/api/v1/sectors` | custom industries + GICS groups with counts |
| GET `/api/v1/sectors/{sheet}/snapshot?currency=USD\|CAD` | counts, medians, histogram, top/bottom 10 |
| GET `/api/v1/sectors/{sheet}/rankings?currency=ALL\|USD\|CAD&limit=500` | ranked table (ALL = score-only, both currencies, per-row money, no blended medians) |
| GET `/api/v1/rankings?scope=seed&currency=&signal=` | global ranking |
| GET `/api/v1/scores/recompute` (POST) | `{universe: "seed"\|"company_id", company_id}` — CPU only |
| GET `/api/v1/companies/{id}/score`, `/api/v1/scores/summary` | score payload / histogram |
| GET `/api/v1/coverage`, `/api/v1/research/meta` | history coverage / research-layer health |
| POST `/api/v1/tickers/ingest` | `{ticker}` synchronous (seconds) |
| POST `/api/v1/jobs/backfill` | **202 + poll** (async since 6A); 409 if one is queued/running |
| GET `/api/v1/jobs`, `/api/v1/jobs/{id}` | recent jobs / poll status+progress+provider_stats |
| GET `/api/v1/screen` | Full-universe filter (currency, sector, industry, signal, score, PE, ROE, FCF margin, coverage pillars, growth history, bank exclusion) |

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

# Frontend unit tests + build (86 tests, 19 test files)
cd ..\frontend
npx vitest run        # 86 tests across 19 files
npm run build         # tsc strict + vite → dist/

# Playwright e2e (UI must be up; chromium via `npx playwright install chromium`)
npx playwright test app.spec.ts

# Clean-room verification (Trust sprint): prove zero -> migrate -> import -> score -> serve
cd backend
python -m app.jobs.verify_clean_room

# Golden ticker battery (Trust sprint D): 10 deterministic trust paths
python -m pytest tests/test_golden_tickers.py tests/test_zz_golden_tickers.py -v

# Narration (LLM, optional): copy .env.example to .env, set OPENROUTER_API_KEY.
# Free models only (ids containing :free). Cached in SQLite; "Narration (not the score)".
# Next fiscal year: Jobs page → "Refresh sample (5 names)" (202 + poll), or set
# REFRESH_ENABLED=1 + REFRESH_INTERVAL_HOURS=168 in .env for a weekly auto-refresh.
# The owner row is never overwritten; new years are INSERTed by EDGAR/Yahoo.
```

Adding a ticker not in the 720: Desk → "Add & score" (ingest → recompute → dossier),
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
- Alembic head: `23317f57050f` (decision_quality_key_stats_evidence; chain ends ccf1cb226400 <- b7f2a91c4d50 <- c3d4e5f6a780 <- d6e7f8a9b001 <- e7f9a0b1c200 <- a1b2c3d4e5f6 <- 23317f57050f). Earlier note: ← c3d4e5f6a780 (scores/halal) ←
  b7f2a91c4d50 (provider provenance) ← ccf1cb226400 (initial).
- **Tests:** backend pytest **138 passed**; frontend vitest **86 passed** (19 test files including design-system token, primitive, and viz unit tests); `npm run build` ✓ (tsc + vite, 0 errors).
- Playwright 7/8 (one timing flake, passes individually).
- Seed workbook untouched throughout (mtime 2026-08-22 21:28:20).

**Design system (DS pass, 2026-09-02):**
- `tokens.css` defines 30+ CSS custom properties; `tokens.ts` is a typed JS mirror.
- All directional colors (`--pos`, `--neg`, `--warn`) are reserved exclusively for numeric direction and status flags — never decorative.
- Card tones apply to left border tint (`border-l-[3px]`), never background fill.
- `prefers-reduced-motion` immediately disables all transitions, keyframes, and count-up animations.
- Zero hard-coded hex codes remain in component source (only in `tokens.css`).

---

## 10. Known quirks & housekeeping (safe to clean)

- `backend/.alembic_draft.db`, `backend/.debug_probe.py`, root `.audit2_phase2.py`,
  `.audit3_phase2.py`, and a `.probe_*.py` — dev scratch files. Deletion was blocked by
  the host Safety Guard during the builds; they are inert and gitignored. Remove manually.
- `backend/alembic/versions/__pycache__` — Python bytecode, harmless.
- Playwright "Banks All" spec is timing-flaky in full-suite runs (passes individually,
  866ms; page verified correct via debug spec). Test-env contention, not a code bug.
- Windows lesson: never rely on case-only overwrites (`compare.tsx` → `Compare.tsx`);
  always two-step rename through a temp name. The `.stale` leftovers have been cleaned.

---


### Startup migration guard (Trust sprint A2) — manual recovery

`app.main.lifespan` compares the live DB's `alembic_version` against
`alembic.ScriptDirectory.get_current_head()` and **refuses to boot** on
mismatch (missing / behind / diverged). The app never stamps or migrates
automatically. Recovery:

```powershell
cd backend
# If the schema was created out-of-band (e.g. create_all) and matches head:
$env:DATABASE_URL = 'sqlite:///../data/app.db'
python -m alembic stamp head
# If the schema genuinely lacks migrations:
python -m alembic upgrade head
```

Then restart the container. `GET /api/v1/system/health/telemetry` shows
`migration_revision` vs `alembic_head` and `schema_verified` at any time.

### ROIC denominator caveats (Trust sprint B)

`invested_capital = total_debt + book_equity - cash`. Buybacks shrink book
equity, inflating ROIC for genuinely strong compounders (AAPL-class). Rules:
- `invested_capital <= 0` -> ROIC NULL, `negative_capital`, confidence low.
- `invested_capital / total_assets < 0.05` or `roic > 1.0` -> confidence low,
  `distorted_low_denominator` ("small_invested_capital_denominator").
- Banks / insurers / credit (GICS Financials or Banks/Insurance/Credit custom
  sheets) -> ROIC `not_meaningful` / `bank_excluded`; use CET1 + efficiency.
The UI suppresses the green "ROIC 20%+" / "MOAT (>=15%)" badge whenever
confidence is low and shows an amber "ROIC distorted" chip instead; the
ForensicCard tooltip explains the buyback mechanics. Read ROIC alongside
ROE, ROA and FCF margin.
---

## 11. Roadmap

See **[BACKLOG.md](BACKLOG.md)** (written in Phase 9, intentionally not implemented):
watchlist/portfolio · LLM summaries via OpenRouter (cached, disclaimer, never overwriting
fundamentals) · full-720 history backfill via the async worker · local telemetry ·
halal interest-income enrichment (would make `halal_candidate` reachable) · GICS
sub-industry drill-down · CSV export · snapshot performance materialization · light mode.

Phase 6B–6D (cache/telemetry/config YAML) were never started — per the Phase 6A STOP.

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
frontend/                  React app, vitest (86, 19 files), playwright e2e (8), Dockerfile
  src/styles/              tokens.css (CSS vars), tokens.ts (typed mirror)
  src/components/layout/  Page, Grid, Card, StatTile, Chip
  src/components/viz/     PillarRadar, CompositeGauge, Sparkline, MiniPillarBars
  src/components/feedback/ EmptyState, LoadingSkeleton
  src/lib/useCountUp.ts    animation hook with reduced-motion fallback
seed/                      READ-ONLY owner data: xlsx + readme + raw + scripts (+refresh.py — never run)
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

---

## Master Sprint (2026-09-02): Dynamic Ingest State Machine, ADR Pipeline, Narration Resilience & UX Redesign

- **Narration Stability & UI Proxy:** `proxy_read_timeout 180s` in `frontend/nginx.conf`. API client safely detects HTML error pages (502/504) from gateways to prevent `SyntaxError: Unexpected token '<'`. UI renders loading spinner *"Writing explanation… 30–90s on free models"* and disables flight buttons. OpenRouter models strictly require `:free`.
- **Hover Help & Accessible Glossary:** Full Grade-10 glossary `{ short, why, how_to_read }` added in `frontend/src/api/glossary.ts`. Interactive and accessible `InfoTip` buttons wired to Compare headers, Dossier snapshot tiles, score pillar cards, and Sector headers. Fully keyboard accessible (Tab + Enter/Space) and mobile tap enabled with `aria-describedby`.
- **Async Ingest State Machine (202 Protocol):** `POST /api/v1/tickers/ingest` returns 202 `{job_id}` immediately without blocking HTTP requests. Worker transitions through 6 deterministic steps: `resolve` → `filings` → `prices_shares` → `sector_peers` → `score` → `done` | `failed`. Frontend polls `/api/v1/jobs/{id}` every 1s with live step progress pills. Comprehensive error catalog maps codes (`SYMBOL_NOT_FOUND`, `LISTING_AMBIGUOUS`, `SCORE_PARTIAL`, etc.) to human guidance.
- **Foreign ADR & Native Currency Pipeline (BABA-Class):** EDGAR parser supports foreign private issuer forms `20-F` and `20-F/A` under `ifrs-full` and `us-gaap`. Native filing currencies (e.g., `CNY`) are preserved on `Company.reporting_currency`. Cross-border currency mismatches suppress price multiples (`PE`, `PB`) with reason `currency_mismatch` to prevent fake ratios. CIK lookup attaches direct SEC filing links to EDGAR. Dual currency display renders transparently: *"Revenue CNY 996.00B · trading USD"*.
- **Peer Set Widening (Eliminating Fake Trophies):** In `build_peer_sets`, solo stocks without sufficient category peers are widened to the full same-currency universe labeled `"broad peer set (n=N)"`. Misleading "#1 of 1" trophies are eliminated. Single-company scoring updates target scores against full universe distributions.
- **Dossier Status Ribbon & Actionable Missing Blocks:** 12-column status ribbon displays Source, As-of date, Reporting vs Trading Currency, Coverage, and Peer Set size. Actionable 1-click buttons *"Fetch shares from Yahoo"* and *"Retry EDGAR filings"* appear under "What is missing" to resolve data gaps.
- **100-Persona Battery & 3-Click Journey Audit:** Comprehensive `docs/PERSONAS.md` documents 100 user jobs across Retail Investors, Value Investors, Shariah/Halal Investors, Cross-Border Traders, Sector Specialists, and Executives, with all 100 passing a strict 3-click workflow audit.
- **Automated Test Suites:** 112 Backend Pytest tests passing 100% green; 49 Frontend Vitest tests across 11 test files passing 100% green.

---

## Research-Desk Upgrade Sprint (2026-09-02): Repeatable 7-Step Equity-Research Loop

- **Screening Engine (`GET /api/v1/screen` & `/screen`):**
  - Full-universe filtering by currency (`ALL`, `USD`, `CAD`), GICS sector, custom industry sheet, signal (`undervalued`, `fair_value`, `overvalued`, `speculative`, `insufficient_data`), min composite (0–10), max PE (excluding blanks when set), min ROE %, min FCF margin %, min coverage pillars (1–4), growth history flag, and bank exclusion.
  - Multi-currency safety: In `ALL` currency view, native money figures are masked to prevent cross-border distortion, displaying only unitless ratios and composite scores.
  - Sortable table columns with multi-select comparison: "Compare Selected (N) →" transfers IDs directly to `/compare?ids=...`.
  - Responsive empty state: *"No names match — loosen PE or coverage."*
- **Company Research Pack on Dossier:**
  - **Business in one line:** 280-character snapshot extracted from Yahoo Finance (`longBusinessSummary`).
  - **Dividend & Earnings:** Yield %, DPS (\$), and next upcoming earnings date.
  - **Quarterly Financials:** Displays last 4 quarters (revenue, net income, diluted EPS) under annual history when available.
  - **Moat / SWOT Card (`POST /api/v1/companies/{id}/research`):** Deterministic facts JSON fed to an OpenRouter `:free` model, cached in `LlmCache` (`kind="swot"`). Emits Strengths, Weaknesses, Opportunities, Threats, and Competitive Advantage (1 line). Labeled *"LLM draft from our facts. Not a 10-K."* Fundamentals are never overwritten.
  - **Thesis Notepad:** Local `localStorage` scratchpad (`thesis:{company_id}`) capped at 1000 characters with auto-saved timestamps. *"Your notes stay on this browser."*
  - **Toy DCF Calculator Card:** Local DCF calculator (FCF, growth rate %, discount rate/WACC %, years). Not stored as ground truth. Intentionally disabled for financial institutions (banks/insurers) without auto-filling fake FCF.
  - **Print / Save PDF:** Clean `@media print` styling removes navbar, action buttons, and dark background colors for 1-page paper or PDF output.
- **Watchlist & Local Alerts:**
  - Fixed Desk Watchlist key to `watchIds` (`getWatchlist()`), displaying ticker, latest composite score, signal badge, and last-opened timestamp.
  - Local alerts (`localStorage stockAlerts` `{id, pe_above, composite_below}`) evaluated locally on screen/dossier load, displaying warning banner when thresholds trigger.
- **UX & Flow Shortcuts:**
  - Keyboard `/` shortcut instantly focuses search from anywhere in the app.
  - Sector page header includes direct link to `"Screen this sector →"` with pre-populated sector filters.
  - 404 company page features a 1-click `"Fetch {ticker} from SEC / Yahoo"` chip to pull missing names into the universe.
- **Documentation:**
  - See `docs/RESEARCH_LOOP.md` for a comprehensive mapping of the 7-step equity-research loop to application screens.

---

## Visual Design System Pass (2026-09-02): Polished product, not ad-hoc pages

- **Design tokens (`tokens.css`):** 30+ CSS custom properties for surfaces, ink hierarchy, gold accent, directional status (never decorative), borders, spacing scale (4–48 px), radii, and elevation. `tokens.ts` provides a typed JS mirror.
- **Layout primitives:** `Page`, `Grid`, `Card` (tone border, never tone background fill), `StatTile` (YoY ▲/▼), `Chip` (`showIcon` with tone-default glyph).
- **SVG visualization primitives (no chart libraries):** `PillarRadar` (4-axis diamond), `CompositeGauge` (arc with tri-color gradient + needle), `Sparkline` (line+area), `MiniPillarBars` (compact Q/V/G/R strip). All have accessible `role="img"` + `aria-label`.
- **Motion system:** `useCountUp` hook with `requestAnimationFrame`; `prefers-reduced-motion` kills all transitions, keyframes, and count-up animations site-wide.
- **Feedback primitives:** `EmptyState`, `LoadingSkeleton` (shimmer).
- **All 9 screens refactored:** Home, Dossier, Compare, Screen, SectorsHub, Sector, Jobs, Learn, AppShell — every screen uses the shared primitives.
- **Zero hard-coded hex in components:** all colors go through `var(--token)` or Tailwind token classes. Hex lives only in `tokens.css`.
- **Test coverage:** 86 vitest tests pass (19 files), including token-structure tests, layout primitive render tests, SVG viz render tests, and `useCountUp` hook tests.
- **Build:** `tsc && vite build` — 0 TypeScript errors, 0 warnings.


---

## Forensic + Expectations Sprint (2026-09-02): TTM forensics, reverse DCF, multi-metric screener

Directive delivered in four suites on top of the frozen architecture (no chart libs, USD/CAD never mixed, owner seed rows immutable).

**Backend**
- **Schema (alembic `a1b2c3d4e5f6` + `23317f57050f`):** `financial_snapshots_ttm` (rolling 4-quarter flows + NOPAT/invested capital/ROIC/FCF yield/EV-EBITDA/PE/Sloan accruals/cash conversion), `valuation_reverse_dcf` (implied 10-yr growth, expectations gap vs 5-yr FCF CAGR, 3x3 WACC/growth sensitivity), `screener_presets` (system presets seeded idempotently).
- **TTM engine** (`app/services/ttm_engine.py`): NOPAT = operating income x (1 - clamp(effective tax, 0.15, 0.30)); invested capital = total debt + equity - cash; Sloan accruals = (NI - OCF)/assets; cash conversion = FCF/NI.
- **Reverse DCF engine** (`app/services/valuation_engine.py`): solves the 10-year DCF polynomial (EV = discounted FCFs + Gordon terminal) for implied growth with a pure-Python Brent solver (bracket [-0.40, +0.60]); negative-FCF companies bypass cleanly with `dcf_unviable_negative_fcf`; 3x3 sensitivity at WACC {8,9,10%} x terminal {2.0, 2.5, 3.0%}.
- **Screener engine** (`app/services/screener_engine.py`): SQLAlchemy query across companies x TTM x reverse-DCF x scores; supports AND and OR (`flag_logic`) forensic flags; system presets "Buffett-Burry Deep Value", "Forensic Red Flags" (OR logic), "Discounted Compounders".
- **API:** `GET /api/v1/screener/presets`, `POST /api/v1/screener/run` (paginated, per-row currency tag), `GET /api/v1/companies/{id}/forensics`, `GET /api/v1/companies/{id}/valuation` (computes+stores on first request).
- **Data-trust extras:** dossier payload now carries `history_warnings` (aggregated FY-level trust warnings) and identity `ticker`/`cik`; dossier shows a warning banner + per-year chips; EDGAR link falls back to a ticker search while CIK is still NULL (fills after the first refresh job).

**Frontend**
- **`src/screens/Screener.tsx` (nav "Forensic", route `/screener`):** collapsible criteria sidebar with sliders (composite/ROIC/FCF yield/EV-EBITDA/Sloan/cash conversion/expectations gap), system preset tabs, sortable sticky-first-column table with conditional badges (ROIC >= 20% emerald-tone positive chip; Sloan > 0.10 "High accruals"; cash conversion < 0.70 "Weak conversion"), one-click **Export to CSV** (verbatim units, per-row currency column, never mixed). Criteria and presets persist in the URL (`?preset=...&roic_min=...`).
- **`ForensicCard` + `ReverseDCFCard` on every dossier:** implied growth vs historical CAGR SVG bars, accessible 3x3 sensitivity grid with dynamic cell coloring, FCF-vs-NI history chart, Sloan/cash-conversion status chips.

**Verification (all green)**
- Alembic `upgrade head` clean on the live DB (after stamping `a1b2c3d4e5f6 -> 23317f57050f`; the DB had been created via `create_all`, so the migration body was a no-op on identical schema).
- `pytest tests/test_ttm_engine.py tests/test_valuation_engine.py tests/test_screener.py`: **12 passed inside the api container**; full backend **138 passed** (includes 6 new screener tests: preset seeding, AND/OR logic, expectations gap, currency purity with NULL-DCF joins).
- Frontend vitest **86 passed**; `npm run build` 0 errors; Playwright **8 passed + 2 flaky-recovered** (both pass individually).
- Numeric sanity: AAPL reverse DCF **converges**; implied growth 12.9% at the fixture price $230 (inside the directive's 7-13% band; unit test asserts 7-14% across realistic EVs). The live DB's stored price ($309.35) implies 16.8% - a data-freshness artifact, not an engine error; refresh updates prices and the implied rate moves accordingly.
- Live screener smoke: `roic_min=0.15` returns ACN 29.7%, MSFT 25.1%, PYPL 17.4%, AAPL 278% (tiny TTM invested capital); CAD-only run keeps every row `currency=CAD` with honest NULLs where quarterly data is not yet ingested.

---

## Analytical Engines Sprint (2026-09-02): Penman, Schilit, Graham + Ittelson bridge

**Backend (`app/services/`):**
- **`penman_engine.py` (WS2):** reformulated statements — OA/OL/NOA/NFO with the
  equity identity check (5%-of-assets tolerance, honest `identity_ok` flag for
  minority-interest gaps), NOPAT (tax clamped 15-30%), RNOA, FLEV, NBC, and the
  Penman DuPont spread. Materialized in `financial_penman_analysis` (migration
  `f4c8d9e2a603`) for 396 balance-sheet-complete rows (SEED basis) + 100
  `financial_institution_excluded` tags. 36 companies carry
  `leverage_distortion=true` (FLEV > 3 or equity < 10% of assets) — the AAPL-class
  ROIC distortion is now quantified as leverage, not operations.
- **`forensic_engine.py` (WS3):** Schilit shenanigans workup. Given the stored
  schema, CFO-vs-NI decoupling is fully computed (2 consecutive FY years);
  DSO/inventory/AQI are reported as `data_available: false` rather than guessed.
  Earnings Quality Rating (EQR 0-100, -25 per triggered flag) is stored on the
  TTM row and filterable in the screener (`eqr_min`/`eqr_max`). AMD correctly
  triggers `RED_FLAG_CFO_EARNINGS_DECOUPLING` (EQR 75).
- **`graham_engine.py` (WS4):** Graham Number = sqrt(22.5 x EPS x BVPS), NCAV and
  NNWC per share (documented 35%-current-asset proxy where AR/inventory detail is
  absent), margin-of-safety vs price, `deep_net_net` chip when price < NCAV.

**API:** `GET /api/v1/companies/{id}/penman`, `/schilit`, `/graham`.

**Frontend:**
- `PenmanCard` — RNOA alongside naive ROIC, FLEV, borrowing cost, spread; amber
  leverage notice; `financial_institution_excluded` state for banks/insurers.
- `GrahamCard` — price-vs-floors CSS range meter (NNWC/NCAV/Graham Number ticks),
  margin-of-safety table, green "Graham Deep Net-Net" chip when applicable.
- `ForensicCard` — live EQR badge (pos/warn/neg tone by band).
- `ReverseDCFCard` — "Opportunity cost vs index" panel: owner FCF yield vs the
  4.5% index baseline and the required growth to clear an 8% compounding hurdle,
  with the plain-language ETF takeaway.
- `viz/CashFlowBridge.tsx` (WS5) — pure-SVG Ittelson waterfall (NI -> ±WC -> CFO
  -> CapEx -> FCF -> debt service -> retained cash) with `role="img"` labeling
  and a tabular fallback for screen readers. No chart libraries.

---

## Universal Analytics & Decision-Quality Desk Sprint (2026-09-02)

Delivers all 7 workstreams of the Master Directive:

### 1. Data Completeness Engine & Full History Backfill (WS1)
- **CLI:** `python -m app.jobs.run_full_backfill --limit 720 --concurrency 2`
  * Options: `--limit N`, `--concurrency 1-4`, `--resume` (skips companies with >= 4 FY rows), `--country US|CA`, `--dry-run`.
  * SEC EDGAR `companyfacts` integration: ~365-day annual duration filter; inserts distinct `period_type='FY'` rows (`source='sec_companyfacts'`).
  * Canadian TSX equities: Yahoo Finance annual periods with 0.2s polite delay.
  * Seed protection: rows with `source='Sector_Financials_Final_Owner.xlsx'` are permanently read-only and never overwritten.
  * Automatic trigger: `scoring_service.recompute_universe()` runs upon backfill completion.

### 2. Database Performance & Timeout Hardening (WS2)
- **Materialization (`sector_cache_summaries` table, Alembic `a7b8c9d0e1f2`):**
  * Materializes sector counts, medians (composite, PE, PB, ROE), signal histogram, and top/bottom rankings per `(sector_name, currency)`.
  * `GET /api/v1/sectors/{sheet}/snapshot` rewritten to read directly from cache: **< 5ms response time** (target < 25ms).
  * `GET /api/v1/sectors/{sheet}/rankings?currency=ALL` optimized with scoped snapshot queries: **~10ms response time** (target < 250ms).
- **SQLite Pragmas & Indexing:**
  * WAL mode asserted, `busy_timeout=15000` (15s), `synchronous=NORMAL`, `cache_size=-64000` (64MB memory cache), `temp_store=MEMORY`.
  * Indexes on `financial_snapshots(company_id, fiscal_year, period_type)`, `scores(peer_group, composite_score)`, `placements(company_id, sheet_name)`.
- **Nginx Timeout Hardening:**
  * `frontend/nginx.conf` hardened: `proxy_connect_timeout 30s; proxy_read_timeout 120s; proxy_send_timeout 60s;` (90s for `/api/v1/companies/`).

### 3. Practitioner Literature Analytical Suite (WS3)
- **`app/services/practitioner_engine.py`:**
  * **Stephen Penman:** ROE = RNOA + FLEV x (RNOA - NBC), NOA, NFO, buyback distortion guardrail (`ROIC > 50%` and `FLEV > 2.5`).
  * **Howard Schilit:** Accrual decoupling, DSO surge, inventory buildup, capitalized expenses, 0–100 Earnings Quality Rating (EQR).
  * **Martin Fridson Reality Check:** EBITDA Reality Spread = EBITDA - CFO (positive & widening for 2 years -> "Aggressive accrual capitalization"), Fixed-Charge Coverage = (EBIT + Lease) / (Interest + Lease).
  * **Benjamin Graham Floors:** Graham Number, NCAV per share, NNWC per share, margin of safety.
  * **Burton Malkiel & JL Collins Index Hurdle:** 8.0% long-term nominal index hurdle, Required FCF Growth = 8.0% - FCF Yield.
  * **Morgan Housel & Ramit Sethi Behavioral Guard:** Anti-FOMO 2-sigma valuation stretch warning, 60-Second Executive Safety Verdict (Moat Durability, Solvency Runway, Valuation Safety -> Pass/Caution).
- **API:** `GET /api/v1/companies/{id}/practitioner`.

### 4. Zero-NPM Interactive Stock Chart (WS4)
- **`frontend/src/components/viz/TradingViewChart.tsx`:**
  * Official TradingView technical widget embed in zero-npm iframe.
  * Dynamic symbol formatting: `US:AAPL:US` -> `NASDAQ:AAPL`, `US:JNJ:US` -> `NYSE:JNJ`, `CA:RY:TSX` -> `TSX:RY`.
  * Dark theme matching design tokens (`#0d1117`), daily interval, technical toolbar.
  * Resilient SVG sparkline fallback with graceful empty state on iframe timeout or offline.
  * Expandable "Price Chart" section with toggle in `Dossier.tsx`.

### 5. Thomas Ittelson Cash Flow Bridge (WS5)
- **`frontend/src/components/viz/CashFlowBridge.tsx`:**
  * Pure SVG + CSS tokens (no npm chart libraries).
  * Horizontal waterfall flow: Net Income -> +/- Working Capital -> CFO -> -CapEx -> FCF -> -Debt Repayment -> -Dividends/Buybacks -> Delta Cash.
  * Accessible tabular fallback.

### 6. Fact-Grounded Stock Research AI Assistant (WS6)
- **Backend (`app/api/chat.py`):**
  * `POST /api/v1/companies/{id}/chat`
  * Assembles deterministic facts JSON strictly from local DB (identity, financials, scores, flags, Penman, Schilit, Graham, Malkiel, Housel).
  * Adversarial equity analyst system prompt; 45s timeout guard; OpenRouter free-tier models (`meta-llama/llama-3.3-70b-instruct:free` with `mistralai/mistral-small-24b-instruct-2501:free` fallback).
  * Hard invariant: AI cannot alter or overwrite fundamental numbers; currency is always explicitly attached to money.
- **Frontend (`StockChatDrawer.tsx`):**
  * Slide-over drawer on Dossier screen: "💬 AI Chat" hero action.
  * Starter prompt chips ("Biggest accounting red flags?", "Dividend covered by real cash flow?", "Justify beating S&P 500 index?", "ROIC vs Penman RNOA").
  * Markdown rendering with disclaimer.

### 7. Verification & Golden Ticker Battery (WS7)
- **Clean-room verification:** `python -m app.jobs.verify_clean_room` passes exit code 0 against an isolated fresh database.
- **Golden tickers (`pytest tests/test_golden_tickers.py`):** 13 deterministic golden paths (MSFT history trust, AAPL ROIC/leverage decomposition, PYPL commercial metrics, RY Canadian bank CAD isolation, KITS symbol resolution, BABA ADR currency suppression, AFL insurer path, IIP.UN sparse data, AMD ingest state machine, invalid ticker graceful failure, Penman AAPL vs RY, Schilit MSFT clean, Graham MSFT floor).
- **Latency verified:** Sector snapshot < 5ms (cached), rankings < 15ms.
- **Backend tests:** 100% green across all 175 tests.
- **Frontend tests:** 100% green across all 86 vitest unit tests.
- **Playwright E2E:** 100% green across all 19 tests.
- **TypeScript build:** `npm run build` exit code 0.

---

## Universal History Backfill & Competitor Fundamental Solidification (2026-09-02)

### 1. Full Universe Multi-Year Statement Ingestion (WS1)
- Ingested **9,601 dated annual (FY) statements** across all 720 companies in the universe (10,321 total snapshots including immutable owner seed rows).
- Scored companies with Growth pillar populated rose from 8 to **682** (well exceeding directive threshold of 650).
- "Growth not scored" warning on Home/Desk resolved; Desk now displays "Universe History Active (95%)".

### 2. Koyfin-Style Common-Size Financial Statement Engine (WS2)
- **Engine:** `app/services/common_size_engine.py`
  * Normalizes income statement items to Total Revenue and balance sheet items to Total Assets.
  * Multi-year margin drift detection: flags `MARGIN_CONTRACTION` (> 300 bps operating margin drop over 3 years) and `COST_CREEP` (> 200 bps OpEx/Revenue expansion over 3 years).
- **API:** `GET /api/v1/companies/{id}/financials/common-size?years=5`

### 3. GuruFocus-Style Solvency & Distress Engine (Altman Z-Score) (WS3)
- **Engine:** `app/services/distress_engine.py`
  * **Manufacturing / Capital-Intensive:** 5-factor Altman Z-Score: $Z = 1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 0.999 X_5$. Safe > 2.99, Grey 1.81-2.99, Distress < 1.81.
  * **Service / Tech / Asset-Light:** 4-factor Altman Z''-Score: $Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$. Safe > 2.60, Grey 1.10-2.60, Distress < 1.10.
  * **Financial Exclusions:** Automatically tags banks and insurers with `status: "financial_institution_excluded"`.
- **API:** Integrated into `GET /api/v1/companies/{id}/practitioner` payload under `distress_analysis`.

### 4. Simply Wall St-Style Dilution & Total Shareholder Yield (WS4)
- **Engine:** `app/services/capital_return_engine.py`
  * Diluted share count tracking: 1-Year Delta % and 3-Year CAGR %.
  * Flags `SHAREHOLDER_DILUTION` (> +2.0% annual expansion) and `ACCELERATED_BUYBACKS` (< -2.0% annual contraction).
  * Net Buyback Yield (%) + Dividend Yield (%) = **Total Shareholder Yield (TSY)**.
- **API:** Integrated into `GET /api/v1/companies/{id}/practitioner` payload under `shareholder_yield`.

### 5. Koyfin-Style Sector Percentile Matrix Engine (WS5)
- **Engine:** `app/services/percentile_engine.py`
  * Computes 0–100 percentile rank within same-currency sector peer group across 8 core ratios: P/E, EV/EBITDA, P/B, ROE, ROIC/RNOA, FCF Margin, Net Debt / EBITDA, and Total Shareholder Yield.
  * Valuation multiples inverted so lower ratios map to higher percentiles.
  * Materialized into `scores.percentiles_json` (Alembic migration `b8c9d0e1f2a3`) for instantaneous reads on `/dossier` and `/score`.

---

## Institutional UI/UX Research Desk & Visual Synthesis Pass (2026-09-02)

### 1. Dossier Workspace Architecture & Tab Navigation
- **8 Dedicated Research Tabs:**
  1. `Overview`: 60s verdict, Composite Gauge, 4-Pillar Radar/Bars, StatTiles, Executive Safety Verdict.
  2. `Financials`: Annual & TTM statements, Common-Size Income Statement & Balance Sheet (% of Revenue/Assets), YoY growth deltas, Ittelson SVG Cash Flow Bridge.
  3. `Valuation & Expectations`: Reverse DCF sensitivity matrix, Graham Intrinsic Floors (Graham Number, NCAV, NNWC), Peer percentile comparisons, Index Opportunity Cost Hurdle (Malkiel/Collins 8% benchmark).
  4. `Forensics & Solvency`: Penman Operating-vs-Financing Decomposition ($RNOA$ vs $FLEV$), Schilit Forensic Red Flags, Earnings Quality Rating (EQR), Altman Z/Z'' Distress Gauge.
  5. `Capital Allocation`: Diluted Share Count CAGR (1Y/3Y), Shareholder Dilution vs Buyback flags, Dividend Yield, Net Buyback Yield, Total Shareholder Yield (TSY).
  6. `Technicals & Chart`: Responsive TradingView interactive chart iframe with SVG sparkline fallback.
  7. `Filings & Sources`: Provenance table, SEC EDGAR 10-K/20-F links with verified CIK, SEDAR+ links, fetch timestamps.
  8. `Thesis & Notes`: LocalStorage scratchpad, bull/bear checklist, print-friendly export view.
- **URL-Persisted State:** Persists tab state via search params (`/c/{id}?tab=financials`), supporting browser forward/back buttons.

### 2. Pure SVG Visual Analytical Primitives
- `PercentileMatrix.tsx`: Koyfin-style percentile distribution bars with quartile tick lines (25th, median 50th, 75th), tokenized gradient fills, and accessible screen-reader table alternative.
- `AltmanZGauge.tsx`: Multi-factor distress meter with dynamic pointer needle, segmented color zones (Distress < 1.1, Grey 1.1–2.6, Safe > 2.6), and explicit bank/insurer exclusion banner.
- `CommonSizeTable.tsx`: Multi-year common-size % and raw statements with automated margin drift alert badges (`COST_CREEP`, `GROSS_MARGIN_COMPRESSION`).
- `CapitalReturnCard.tsx`: Diluted share count CAGR (1Y/3Y), buyback contraction vs dilution tags, Total Shareholder Yield (TSY) card, and pure SVG multi-year share count bar chart.

### 3. Interactive Technical Chart & Fact-Grounded AI Drawer
- `TradingViewChart.tsx`: Official TradingView widget embed matching dark theme tokens (`#0d1117`), with responsive SVG sparkline fallback.
- `StockChatDrawer.tsx`: Fact-grounded AI research assistant slide-over drawer triggered by `"💬 Ask Analyst AI"`, 4 starter chips, disclaimer enforcement, and accessible hidden state transitions.

### 4. Screener & Sector Navigation Polish
- `Screener.tsx`: Materialized Altman Z Zone buttons (`ALL`, `Safe`, `Grey`, `Distress`), slider bounds for TSY %, EQR, and Percentiles.
- **Institutional CSV Export:** Materialized export columns: `altman_z`, `altman_zone`, `penman_rnoa`, `penman_flev`, `total_shareholder_yield`, and `eqr`.

### 5. Automated Verification Battery
- **Vitest Unit Tests:** 94 / 94 tests passing across 20 files (100% green).
- **Playwright E2E Tests:** 19 / 19 tests passing (100% green).
- **Pytest Backend Tests:** 175 / 175 tests passing (100% green).
- **CSS Design Token Conformance:** 0 hard-coded hex colors in components (`tokens.css` strict conformance).

## ETF Universe Expansion, Forensic Moat & Final Hardening (2026-09-03)

### 1. ETF Universe Expansion & Setup (SPUS, QQQ, VONV)
- **Constituent Resolution:** Multi-tier resolver (`backend/app/services/etf_resolver.py`):
  1. SEC EDGAR N-PORT XML filings (CIK-based holdings extraction).
  2. Yahoo Finance `quoteSummary` holdings scraping.
  3. Pre-curated seed lists in `seed/etf_constituents/` (`spus.csv`, `qqq.csv`, `vonv.csv`).
- **Database Schema:** Alembic migration `c9d0e1f2a3b4_companies_universe_tags.py` adding `universe_tags` JSON column to `companies`.
- **Constituent Counts (720 Core Universe):**
  - S&P 500: 500 companies
  - S&P/TSX: 220 companies
  - SPUS (Halal): 121 companies
  - QQQ (Nasdaq 100): 66 companies
  - VONV (Value): 55 companies
- **UI Cohorts & Segmented Screener:**
  - `GET /api/v1/etfs/top-cohorts`: returns top 5 composite scorers per active basket for Desk cards (`Home.tsx`).
  - Segmented selector in `Screener.tsx`: `ALL` | `S&P 500` | `S&P/TSX` | `SPUS (Halal)` | `QQQ (Nasdaq 100)` | `VONV (Value)`.

### 2. Beneish M-Score 8-Variable Manipulation Engine
- **Engine:** `backend/app/services/beneish_engine.py` implementing the complete 8-variable probabilistic model:
  $$M = -4.84 + 0.920 \cdot DSRI + 0.528 \cdot GMI + 0.404 \cdot AQI + 0.892 \cdot SGI + 0.115 \cdot DEPI - 0.172 \cdot SGAI + 4.037 \cdot TATA + 0.0327 \cdot LVGI$$
  - $DSRI$: $\frac{\text{Receivables}_t / \text{Revenue}_t}{\text{Receivables}_{t-1} / \text{Revenue}_{t-1}}$
  - $GMI$: $\frac{\text{Gross Margin}_{t-1}}{\text{Gross Margin}_t}$
  - $AQI$: $\frac{1 - (\text{Current Assets}_t + \text{PPE}_t) / \text{TA}_t}{1 - (\text{Current Assets}_{t-1} + \text{PPE}_{t-1}) / \text{TA}_{t-1}}$
  - $SGI$: $\frac{\text{Revenue}_t}{\text{Revenue}_{t-1}}$
  - $DEPI$: $\frac{\text{Depreciation Rate}_{t-1}}{\text{Depreciation Rate}_t}$
  - $SGAI$: $\frac{\text{SGA}_t / \text{Revenue}_t}{\text{SGA}_{t-1} / \text{Revenue}_{t-1}}$
  - $LVGI$: $\frac{\text{Total Debt}_t / \text{TA}_t}{\text{Total Debt}_{t-1} / \text{TA}_{t-1}}$
  - $TATA$: $\frac{\text{Net Income}_t - \text{CFO}_t}{\text{TA}_t}$
- **Thresholds & Exclusions:**
  - $M \le -1.78$: Clean status / non-manipulator.
  - $M > -1.78$: High probability of earnings manipulation.
  - Banks and insurers: automatically marked `financial_institution_excluded` (no false alarms on regulated balance sheets).
- **UI:** Mounted in `BeneishCard.tsx` under Dossier `Forensics & Solvency` tab.

### 3. True Shareholder Yield & SBC Dilution Engine
- **Engine:** `backend/app/services/capital_return_engine.py`:
  - $\text{Net Repurchase Rate} = -\frac{\Delta \text{Diluted Shares}}{\text{Diluted Shares}_{t-1}} \times 100$
  - $\text{SBC Drag \%} = \frac{\text{SBC Expense}}{\text{Total Revenue}} \times 100$
  - $\text{Gross Buyback Yield} = \frac{\text{Repurchases}}{\text{Market Cap}} \times 100$
  - $\text{SBC Dilution Offset} = \frac{\text{SBC Expense}}{\text{Market Cap}} \times 100$
  - $\text{Net Buyback Yield} = \max(0, \text{Gross Buyback Yield} - \text{SBC Dilution Offset})$
  - $\text{True Shareholder Yield} = \text{Dividend Yield} + \text{Net Buyback Yield}$
- **Flags:**
  - `ORGANIC_FLOAT_SHRINK`: Net Repurchase Rate $> 2.0\%$ and SBC Drag $< 3.0\%$.
  - `DILUTIVE_BUYBACKS`: Gross repurchases $> 0$ but share count expanded year-over-year.
- **UI:** Horizontal buyback vs SBC decomposition bar in `CapitalReturnCard.tsx`.

### 4. 2-Page Institutional Factsheet Print Memo
- **Component:** `frontend/src/components/dossier/FactsheetPrintView.tsx` with dedicated `@media print` 2-page stylesheet.
  - Page 1: Hero header, 60s Executive Safety Verdict, 4-pillar scores, fundamental snapshot, Altman Z + Beneish M-Score solvency/distress matrix.
  - Page 2: 5-Year common-size history, Reverse DCF implied growth vs historical CAGR, investment checklist, and compliance disclaimers.

### 5. Final Verification Battery
- **Clean-Room Verification:** `python -m app.jobs.verify_clean_room` PASSED (0 to 13 migrations, 720/1506 placements, 0 invented fiscal years).
- **Golden Ticker Battery:** `pytest tests/test_golden_tickers.py` 16/16 PASSED (100%).
- **Pytest Suite:** 185 / 185 passed (100% green).
- **Vitest Suite:** 97 / 97 passed across 22 test files (100% green).
- **Production Build:** `npm run build` exits 0 with 0 errors.
- **Playwright E2E Suite:** 19 / 19 passed (100% green).