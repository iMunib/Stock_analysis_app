# PHASE1_REPORT.md

**Task:** Phase 1 — workbook import + read-only API (no scoring, no live fetch, no LLM, no full UI)
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-01 (America/Toronto)
**Verdict: PASS**

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | AGENTS.md, README.md, docs/SCORING_SPEC.md, docs/DATA_CONTRACT.md, PHASE1_REPORT.md exist | PASS | all present at repo root / docs/ |
| 2 | `docker compose up --build -d` succeeds; GET /health → 200 | PASS | image built; container `invest-api` Up (healthy); `{"status":"ok"}` |
| 3 | pytest passes (no xfail — seed xlsx present) | PASS | **25 passed, 2 warnings in 3.50s** (Python 3.13.7 host venv) |
| 4 | `/api/v1/stats` shows companies = 720 | PASS | `{"companies":720, "by_currency":{"USD":500,"CAD":220}, ...}` |
| 5 | No live scrape, no scoring endpoints, no paid services | PASS | importer reads only the local xlsx; no fetch/score routes exist (test_no_scoring_endpoints asserts 404s) |

## Live API verification (Docker, port 8000)

- `GET /health` → 200 `{"status":"ok"}`
- `GET /ready` → 200 `{"status":"ready","database":"ok"}`
- `GET /api/v1/stats` → companies 720, snapshots 720, placements 1506, flags 2016, USD 500 / CAD 220, fixture=false, source `Sector_Financials_Final_Owner.xlsx`
  - coverage: Revenue 715, Net_Income 718, Total_Debt 679, Gross_Profit 207, FCF_Calc 640, ROE_Calc 680, Market_Cap 694, CET1_Ratio 9
- `GET /api/v1/companies/CA:NA:TSX` → 200, name = "National Bank of Canada" (never NVIDIA)
- `GET /api/v1/sectors` → 30 custom industries + 11 GICS sectors, each totalling 720
- `GET /api/v1/meta/disclaimer` → non-empty disclaimer (explicitly "NOT investment advice")
- Container log: `Imported 720 companies, 1506 placements, 2016 quality flags from Sector_Financials_Final_Owner.xlsx`; alembic ran `-> ccf1cb226400` before uvicorn started.

Placement math checks out: 1506 = 720 Primary + 66 Extra + 720 GICS.

## Test output

```
backend\.venv\Scripts\python.exe -m pytest -q
25 passed, 2 warnings in 3.50s
```

Key tests: 720 unique companies; CAD revenue stored verbatim (no conversion); bank blanks stay NULL (dynamically finds a Financials row with blank Total_Debt); Extras don't inflate companies; idempotent re-import; fiscal_year never invented; MMM revenue == 24,948,000,000 exactly; ID round-trips incl. `CA:BN:TSX` (dots kept) and `CA:NA:TSX` = National Bank; /health 200; disclaimer non-empty.

## Commands run (host, PowerShell)

| Command | Result |
|---|---|
| `pip install -r requirements.txt` (backend/.venv, Python 3.13.7) | ok (fastapi 0.141.1, sqlalchemy 2.0.52, alembic 1.19.1) |
| `python -m alembic revision --autogenerate -m "Phase 1 initial schema"` | generated `alembic/versions/ccf1cb226400_phase_1_initial_schema.py` |
| `python -m pytest -q` | 25 passed (after 2 fixes, see below) |
| `docker compose up --build -d` | image built, `invest-api` started |
| `Invoke-WebRequest http://localhost:8000/...` | see table above |
| `docker compose ps` | `invest-api  Up (healthy)` |

## Seed files used / copied

- Read (only): `seed/Sector_Financials_Final_Owner.xlsx` (sheets 01_All_Companies, 03_Data_Quality, 06_Placements), `seed/readme.md` (data dictionary source).
- Copied to `legacy/`: `refresh.py` and `scripts/refresh.py` (from seed/). **Never executed.** Nothing under `seed/` was modified; the workbook is mounted read-only into the container.

## Bugs found and fixed during verification (honest repair log)

1. **Placements/flags imported 0 rows** — `db.get()` doesn't see session-pending objects, so the placements/quality passes (which run in the same transaction) found no companies. Fixed with `db.flush()` after the company pass. Reproduced via probe before fixing; verified by tests after.
2. **ID validator too loose** — `parse_company_id("CA:BN:NYSE")` validated against the frozen contract. Regex tightened to strict `US:...:US | CA:...:TSX`; loose variants (e.g. `US:AES:NYSE` in 03_Data_Quality) are handled by `normalize_company_id` only.

## Conservative defaults chosen

1. **Frontend behind compose profile `frontend`** — default `docker compose up --build -d` starts only `api`; frontend placeholder builds only with `--profile frontend`.
2. **Importer auto-runs at container start** (`alembic upgrade head && python -m app.services.importer && uvicorn`); idempotent, skips re-import unless the workbook mtime changed or `--force`.
3. **fiscal_year stored NULL** — the seed has no fiscal-year column; inventing one is forbidden. `as_of_date` = `Price_AsOf` (present on all 720 rows).
4. **Values stored verbatim** — no rescaling of the README-prose "millions" (cells hold actual dollars; discrepancy documented in DATA_CONTRACT.md).
5. **03_Data_Quality ID normalization** — IDs like `US:AES:NYSE` are normalized to the frozen format; 2016 of 2026 rows matched (60 unmatched IDs are kept out rather than guessed; raw text remains in the sheet).
6. **Placements include a `GICS` role** for the 11 GICS sector tabs (copies by design, never companies).
7. **Host tests run on Python 3.13.7** (host default), while containers use python:3.12-slim per the locked stack; requirements pinned loosely to install on both.
8. **No `git init`** — repo left as plain directory per brief.

## Deviations / execution notes

- Delegation to the bundled coding agent failed twice on a provider-capacity error ("high demand"); per fallback contract this build was completed with native tools under the same spec. Cursor CLI was requested at one point but is not installed/authenticated on this host.
- The Vite/React/Tailwind placeholder was **not built or typechecked** (it is excluded from the default compose path by design); its build path will be exercised when the profile is first used.

## Unverified / risks

- Frontend image build (profile `frontend`) WAS exercised post-completion: `docker compose --profile frontend up --build -d` built (`tsc && vite build` → ✓ built in 1.01s) and serves the placeholder at http://localhost:5173 (HTTP 200).
- `OPENROUTER_API_KEY` is unused in Phase 1 (config placeholder only).
- Coverage numbers (e.g. Revenue 715/720) reflect the seed's intentional blanks and are surfaced via `/api/v1/stats` rather than corrected.
- Two dev-scratch files remain in `backend/` (`.alembic_draft.db` throwaway migration DB, `.debug_probe.py` importer probe); both are disposable, deletion was blocked by a safety approval timeout — remove manually if desired.
- File-name casing of 5 files (`Dockerfile`s, `App.tsx`, `docs/SCORING_SPEC.md`, `docs/DATA_CONTRACT.md`) was corrected post-build via rename and confirmed by a fresh rebuild + frontend image build.

STOP — Phase 1 complete, do not start Phase 2.
