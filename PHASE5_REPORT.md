# PHASE5_REPORT.md

**Task:** Phase 5 — real local UI (React + Vite + TS + Tailwind): search, dossier, compare, sector, add-ticker
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-02 (America/Toronto)
**Verdict: PASS**

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | PHASE5_REPORT.md exists | PASS | this file |
| 2 | UI loads (HTTP 200); search/dossier/compare/sector work against live API | PASS | UI index 200; UI→API proxy through nginx 200 (`/api/v1/research/meta` → scored=718); click-path endpoints all 200 |
| 3 | Peer rank + gaps + disclaimer visible in dossier | PASS | "Peer rank X of N" header, "Data gaps on file" list, disclaimer footer on every view |
| 4 | Mixed-currency compare shows warning | PASS | amber banner: "Mixed currencies: USD vs CAD … never converted" |
| 5 | No LLM / weight changes / scrape / new paid service | PASS | UI only; deterministic copy templates; no new backend routes or deps beyond fonts/router/vitest |

## URLs + HTTP codes (live verification)

| Check | URL | Code |
|-------|-----|------|
| UI index | `http://localhost:5173/` | 200 |
| UI→API proxy (nginx → host.docker.internal:8000) | `http://localhost:5173/api/v1/research/meta` | 200 |
| search | `/api/v1/search?q=AAPL` | 200 |
| dossier | `/api/v1/companies/US:AAPL:US/dossier`, `CA:RY:TSX`, `US:MMM:US` | 200 / 200 / 200 |
| compare (same currency) | `/api/v1/compare?ids=US:AAPL:US,US:MSFT:US` | 200 |
| compare (mixed) | `/api/v1/compare?ids=US:AAPL:US,CA:RY:TSX` | 200, `currency_warning=true` |
| sector snapshot | `/sectors/Software/snapshot?currency=USD`, `/sectors/Banks/snapshot?currency=CAD` | 200 / 200 |
| Backend regression | pytest | **79 passed** |

## What was built

- Screens (exactly the four required + flows): Home (search + histogram-as-counts + 2-sentence legend + add-ticker flow with progress/errors), Dossier (`/c/:companyId`), Compare (`/compare?ids=`), Sector (`/sectors/:sheet?currency=`).
- Deterministic copy templates in `src/api/copy.ts` (growth NULL, coverage penalty, mixed signal, halal notes) — no LLM, grade-10 language.
- Shared typed API layer `src/api/types.ts` + `src/api/client.ts` (typed errors, `enc()` for company_id URLs).
- "Night research desk" aesthetic: dark ink surfaces, Spectral display serif, IBM Plex Sans/Mono (self-hosted via @fontsource — no CDN), gold accent, hairline borders, tabular numerals. No chart library — histogram is div bars, everything else tables.
- Product rules honored: peer rank + signal lead the dossier; left-skew explained in copy ("Growth not scored — fewer than 3 years…"); currency shown on every money cell ("— " when NULL); halal is a badge with failed-test explanations and "Not a religious ruling"; default views unfiltered.
- A11y: labeled search inputs, aria-pressed currency toggle, role=alert banners, keyboard-usable search, focus rings.
- Vite dev proxies `/api` → `http://localhost:8000`; Docker nginx proxies `/api` → `host.docker.internal:8000`. Serving choice: nginx on container :80 → host :5173 (documented in README).

## Verification run

- `npm run build` (tsc strict + vite): ✓ built (196 kB JS / 61.9 kB gzip).
- `npx vitest run`: **10 passed** (URL encode/decode of company_id, mixed-currency warning, pillar/halal/money copy templates).
- `docker compose --profile frontend up --build -d`: api + frontend built and started.
- Backend `pytest`: **79 passed** (no regression).
- Seed xlsx mtime unchanged: 2026-08-22 21:28:20.

## Deviations / decisions logged

1. Old lowercase screen files (`compare.tsx`, `sector.tsx`, …) collided case-insensitively with the new PascalCase modules (TS1261). They were renamed to `*.stale` beside the live files (deletion is blocked by Safety Guard in this environment); remove them manually if desired. Root cause: Windows copies preserve destination casing; TS is case-sensitive.
2. Phase-1 placeholder files were replaced in place; `invest-api` untouched (rebuilt only to pick up Phase 4 router which was already live).
3. Screenshots not included (optional per prompt); all URLs + codes are listed above.
4. Port serving choice: UI on `http://localhost:5173` (nginx 80 in-container). Vite dev also available at 5173 when running outside Docker.

STOP — Phase 5 complete, do not start Phase 6.
