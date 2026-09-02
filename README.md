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