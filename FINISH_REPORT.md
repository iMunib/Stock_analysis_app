# FINISH_REPORT.md

**Task:** Finish the research app — Stage A (understand + flags + secrets hygiene), Stage B (narration + packed dossier/sectors), Stage C (refresh + jobs UX + learn)
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02
**Verdict: ALL STAGES PASS**

## Stage A — Understand + flags + secrets hygiene: PASS

- **Dossier verdict strip** now carries the provenance line: "Score is math (v1), not AI.
  Quality 30% · Value 25% · Growth 25% · Risk 20%." (`src/lib/flags.ts: provenanceSentence`).
- **Flags row** (max 6, sorted bad→good, 2–3 words): Quality ≥7 "Quality" / ≤3 "Weak quality";
  Value ≥7 "Cheaper vs peers" / ≤3 "Expensive vs peers"; Growth ≥7 "Growth history" /
  **NULL → amber "Not enough history" (never red)**; Risk ≥7 "Lower risk" / ≤3 "Higher risk";
  Signal Avoid → red; halal not_halal → amber "Activity/ratio flag — not a ruling".
- **Glossary** locked at `src/api/glossary.ts` — all 16 terms from the master prompt verbatim
  (Composite, Quality, Value, Growth, Risk, Signal, Peer rank, PE, PB, EV/EBITDA, ROE, ROA,
  FCF margin, Coverage, Currency All, Narration), each `{term, short, why}`.
- **`/learn` page** renders the full glossary; `InfoTerm "?"` tooltips wired on dossier
  (Composite/Coverage, Signal/Peer rank, FCF margin/ROE/PE), compare headers, sector headers.
- **Secrets hygiene:** `.gitignore` now includes `.env`, `.env.local`, `.env.*`, `!.env.example`,
  `*.db`, `.venv/`, `node_modules/`, `playwright-report/`, `test-results/`, `.audit*.py`,
  `.debug*.py`, `__pycache__/`, `.cluster/`. `.env.example` contains placeholders only
  (verified by test). `GET /api/v1/llm/status` returns `{configured, model, fallback,
  free_latch:true}` — never the key (asserted in tests, including a `sk-…` scan of narrate
  responses).

## Stage B — Narration + packed dossier + packed sectors: PASS

- **Narration (OpenRouter, free-only):** `POST /api/v1/companies/{id}/narrate` and
  `POST /api/v1/sectors/{sheet}/narrate?currency=ALL|USD|CAD`. Server builds the facts JSON
  from the DB (identity, pillars, ratios, gaps, peer rank, halal, history years); the model
  gets only that JSON + a grade-10 system prompt ("null = unknown; no advice; score is the
  rating"). **Free latch:** only ids containing `:free`; non-free → refused before any HTTP
  (tested). Default `nvidia/nemotron-3-ultra-550b-a55b:free`, fallback
  `minimax/minimax-m3:free`, both `.env`-configurable. Timeout 45s; 429/402/empty → fallback
  model; still failing → **503 `narration_unavailable`** with the facts attached (UI shows
  facts anyway — never a blank page).
- **Cache:** SQLite `llm_cache` keyed `(kind, subject_id, method_version, score_computed_at,
  model)`. Test proves the second call is `cached: true` with **zero HTTP calls**.
- **Dossier packing:** flags row + provenance sentence + tooltips + narration panel +
  "What is missing" (data gaps) + similar + compare. Layout from Phase 8 preserved.
- **Sector packing:** static 2-sentence blurb per sheet (`sectorCopy.ts`, 21 sectors +
  generic fallback), tooltips on ranked-table headers, green/red count chips
  (Constructive+ vs Weak+Avoid — computed from scores, not AI), money medians split
  USD/CAD, histogram, narration button.
- **Compare:** tooltips on Composite/PE/PB/ROE/EV-EBITDA headers; mixed-currency warning intact.
- **Live narrate (the one allowed use):** `configured:true` from the user's `.env` (read,
  never printed). AAPL narrate ran **live** against the primary free model; first call took
  >90s (free nemotron is slow), the retry returned `cached: True` from SQLite. Honest note:
  the free nemotron model sometimes leaks chain-of-thought into the text — a model quirk,
  not a code bug; switch models via `OPENROUTER_MODEL` in `.env` if unwanted.
- Headlines: not implemented (optional; yfinance news list was not returned in testing —
  fail-closed per contract).

## Stage C — Refresh + Jobs UX + learn: PASS

- **`POST /api/v1/jobs/refresh`** → 202 `{job_id, kind: refresh_universe}`; 409 if one is
  queued/running. Worker runs backfill(sample/limit) then `recompute(seed)`; test proves
  recompute fired with mocked ingest (no network).
- **Periodic refresh:** `REFRESH_ENABLED=0` default. When `1`, the worker probes hourly and
  enqueues a sample refresh only if no job finished within `REFRESH_INTERVAL_HOURS`
  (default 168 = weekly).
- **Jobs page:** always in nav; list + status badges + progress bars + last error;
  **"Refresh sample (5 names)"** button → 202/poll; 409 → inline message; API 404 → setup
  hint ("update the api container").
- **README** documents how next-FY works: EDGAR/Yahoo INSERT new years; the owner row is
  never overwritten; recompute refreshes scores.

## Final EXIT CHECK

| Requirement | Result |
|---|---|
| Dossier: math provenance, tooltips, flags, narration panel (works or honest 503) | ✅ all four present |
| `/learn` glossary complete (16 terms) | ✅ |
| Sectors All default; money not blended; sector page informative (blurb, chips, medians split) | ✅ |
| `.env.example` + gitignore; no secret in repo/responses | ✅ (tests assert) |
| Refresh job 202 + poll; default timer **off** | ✅ |
| pytest 101 ✅ · vitest 29 ✅ · npm build ✅ · Playwright ran (7 passed + 1 flaky-pass-on-retry) | ✅ |
| Weights unchanged; no paid APIs; no LLM in the score | ✅ |

## Verification run

- `pytest`: **101 passed** (13 new Phase 10 tests).
- `vitest`: **29 passed** (nav updated for Learn/Jobs).
- `npm run build`: ✓ (tsc strict + vite).
- Playwright: **7 passed + 1 flaky** (Banks All — passes on retry; documented in PHASE9_REPORT).
- Live narrate: ran once on AAPL against the primary `:free` model; result cached in SQLite.
- Seed xlsx mtime unchanged: 2026-08-22 21:28:20. No real key ever printed/committed.

## Leftover backlog (from BACKLOG.md, not implemented)

Full-720 history backfill · paid news source · auth/multi-user · watchlist · local
telemetry · halal interest-income enrichment · GICS sub-industry drill-down · CSV export ·
snapshot materialization · light mode · swap the chatty free narration model via `.env`.

## Housekeeping left in place (Safety Guard blocked deletes earlier)

`backend/.alembic_draft.db`, `backend/.debug_probe.py`, root `.audit*.py`, probe scripts,
`frontend/src/screens/*.tsx.stale` — all inert/gitignored; remove manually anytime.

STOP — the research app is finished. All stages PASS.
