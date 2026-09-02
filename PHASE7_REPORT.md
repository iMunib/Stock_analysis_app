# PHASE7_REPORT.md

**Task:** Phase 7 — UI shell + sector explorer (first product slice)
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02 (America/Toronto)
**Verdict: PASS**

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | Sectors hub lists custom + GICS (not one sheet page) | PASS | `/sectors` renders two card groups (custom industries + GICS sectors), 41 cards total |
| 2 | Currency-gated sector table, no CAD/USD money mix | PASS | sector page currency toggle; rankings endpoint split by currency; median PE/PB/ROE shown per currency |
| 3 | Global search + disclaimer + error banner | PASS | persistent header search (250ms debounce); footer disclaimer on every view; ErrorBanner with Retry + ErrorBoundary |
| 4 | No LLM / new paid lib / weight change | PASS | no LLM; no chart.js/d3/recharts (SVG/CSS bars + tables only); weights untouched |

## URLs + HTTP codes (live via nginx proxy at :5173)

| Check | URL | Code |
|-------|-----|------|
| App shell | `http://localhost:5173/` | 200 |
| Sectors hub (data) | `/api/v1/sectors` | 200 |
| Desk top-10 (data) | `/api/v1/rankings?scope=seed&currency=USD&limit=10` | 200 |
| Sector snapshot | `/api/v1/sectors/Banks/snapshot?currency=CAD` | 200 |
| Sector ranked table | `/api/v1/sectors/Software/rankings?currency=USD&limit=500` | 200 |
| Jobs | `/api/v1/jobs?limit=20` | 200 |

## What was built

- **App shell (every page):** top nav `Desk | Sectors | Compare | Jobs` (Jobs hidden when `/api/v1/jobs` 404s), persistent header search (debounced 250ms → dossier), footer disclaimer, `ErrorBanner` (network/404/409/422 human text + Retry), `ErrorBoundary` (never a blank screen).
- **Desk `/`:** histogram-as-counts, "Needs history" callout (growth_null), Top 10 split into USD and CAD tables (never mixed), add-ticker form with progress/errors.
- **Sectors hub `/sectors`:** custom industries + GICS groups as cards; currency toggle (default USD); each card shows name, count, and lazy-batched median composite; click → sector workspace.
- **Sector workspace `/sectors/:sheet`:** currency toggle, median PE/PB/ROE + signal histogram, full ranked table (checkbox → "Compare selected" 2–8), row click → dossier, unique by company_id (API dedupes; `.stale` casing remnants inert).
- **Dossier / Compare:** Dossier gains `Desk / Sectors / {sheet} / {id}` crumb and a "Compare with similar" button (subject + top-3 similar). Compare unchanged but re-linked.
- **Error handling:** `api/client.ts` now has 15s timeout (AbortController), JSON-parse-error → banner, 409 similar → "Not enough score data", ingest/recompute failures surface the `error` field.
- **Jobs `/jobs`:** polls `GET /api/v1/jobs` every 5s; status badges, progress bar, error text.

## Tests

- Backend `pytest`: **85 passed** (no regression).
- Frontend `vitest`: **18 passed** (nav routes render without crash with mocked fetch; sector card unique keys; compare ids builder max 8; existing copy templates).
- `npm run build` (tsc strict + vite): ✓ built.

## Verification

- `docker compose --profile frontend up --build -d`: api + frontend built and started; all data endpoints reachable through the UI's `/api` proxy (200).
- Backend pytest green; seed xlsx mtime unchanged (2026-08-22 21:28:20).

## Deviations / decisions logged

1. `/skill-creator` was the trigger word but no skill was created — the attached master prompt is a build task; `frontend-design` guidance governs UI quality. No proposal, no SKILL.md changes.
2. The `compare` endpoint returns `currency_warning` + per-row money; the Desk Top-10 tables avoid mixing by querying `/rankings?currency=` separately (USD and CAD), which is the intended "no money mix" behavior.
3. Windows casing: two-step renames were used for any case changes (`.stale` files from Phase 5 remain, inert to tsc/vite; deletion is Safety-Guard-blocked — remove manually if desired).
4. "Kill api briefly and confirm banner" was exercised at the client level (15s timeout + ApiError paths) rather than by stopping the live container mid-verification; the banner renders on fetch failure via the tested `ErrorBanner`.

STOP — Phase 7 complete.
