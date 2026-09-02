# PHASE2_REPORT.md

**Task:** Phase 2 — history + on-demand data layer (SEC EDGAR + Yahoo), ingest policy, new API surface
**Workspace:** `C:\Users\RehmanPC\Downloads\Investment Stock Application`
**Date:** 2026-09-01 (America/Toronto)
**Verdict: PASS**

## EXIT CHECK results

| # | Requirement | Result | Evidence |
|---|-------------|--------|----------|
| 1 | PHASE2_REPORT.md exists | PASS | this file |
| 2 | Placement roles: Primary=720, Extra≈66, GICS≈720 | PASS | live DB audit: `Extra=66, GICS=720, Primary=720` (Phase 1 already separated GICS; regression test `test_placement_roles_gics_extra_primary` added) |
| 3 | Fixture tests pass; owner rows not overwritten | PASS | `45 passed` total; dedicated tests prove seed Revenue 24,948,000,000 / source owner_xlsx survive provider ingest; NULL-fill + first-provider-wins verified; insurer blank-debt carve-out verified |
| 4 | `/api/v1/coverage` and `/financials` exist | PASS | both verified live (below) |
| 5 | Sample ingest attempted for one US + one CA ticker; year counts logged | PASS | AAPL 20 FY (sec_companyfacts), MSFT 20 FY (sec_companyfacts), RY.TO 5 FY (yfinance, CAD), XOM 5 FY, SHOP.TO 5 FY |
| 6 | No scoring endpoints, no paid services, seed xlsx untouched | PASS | xlsx mtime still 2026-08-22 21:28:20; refresh.py never executed; no score routes |

## Live API verification (Docker, port 8000, final state after repair re-import)

- `GET /health` → 200 `{"status":"ok"}`; `invest-api Up (healthy)`
- `GET /api/v1/stats` → companies=720, financial_snapshots=775 (720 seed + 55 provider history), data_quality_flags=2026, placements=1506, USD 500 / CAD 220
- `GET /api/v1/companies/US:AAPL:US/financials?years=10` → 200, 10 rows, top = FY2025, Revenue 416,161,000,000, source `sec_companyfacts`
- `GET /api/v1/coverage` → companies=720, us=500, ca=220, with_history=5, pct_with_5plus_fy=0.7, years 2006–2026, fixture_flag=false
- `GET /api/v1/tickers/resolve?q=RY.TO` → `CA:RY:TSX`, yahoo=`RY.TO`, in_universe=true
- `GET /api/v1/companies/US:MMM:US/financials` → seed row intact: `fiscal_year NULL : Sector_Financials_Final_Owner.xlsx : 24,948,000,000`
- Phase 1 surface intact: `/health`, `/api/v1/stats` (720), disclaimer unchanged.

## Live sample ingest (the one allowed network use)

| Ticker | Resolved | Provider rows | DB fiscal years | NULLs filled on seed | Notes |
|--------|----------|---------------|-----------------|----------------------|-------|
| AAPL | US:AAPL:US | 20 (sec_companyfacts) | 2006–2025 | 1 | full EDGAR history |
| MSFT | US:MSFT:US | 20 (sec_companyfacts) | 2007–2026 | 0 | June FY end handled |
| RY.TO | CA:RY:TSX | 5 (yfinance) | 2021–2025 (CAD) | 2 | sparse-but-real Yahoo history, no padding |
| XOM | US:XOM:US | 5 (yfinance) | 2021–2025 | 5 | EDGAR call degraded → Yahoo fallback worked as designed |
| SHOP.TO | CA:SHOP:TSX | 5 (yfinance) | 2021–2025 | 6 | CAD verbatim |

Cache rule observed: values persisted verbatim (no 1e6 rescaling), currency stored per provider report.

## Required fixes from Phase 1 — audit outcomes

1. **Placement roles:** already correct in the live DB (Primary=720, Extra=66, GICS=720); regression test added so it cannot drift.
2. **Quality-flag ID normalization:** the 10 rows Phase 1 skipped all carry the pseudo-ID `(workbook)` — workbook-level QC notes (SIGN_CONVENTION_MIXED, BANK_EXCLUSION_BY_DESIGN, MARKET_SNAPSHOT, PHASE3_SUMMARY, ...), not company rows. Phase 2 imports them with `company_id NULL` (schema now nullable); 2,026/2,026 sheet rows are retained. Regression test `test_workbook_level_flags_kept`.
3. **Scratch-file deletion (backend/.alembic_draft.db, backend/.debug_probe.py):** Safety Guard timed out on every delete attempt (3 turns); per prompt instruction this does not fail the phase. Both files are harmless, gitignored, and can be removed manually.
4. **Case-safe names:** Dockerfile, docs/SCORING_SPEC.md, docs/DATA_CONTRACT.md verified correct casing (frontend image build also passed in Phase 1 closeout).

## Implementation summary

- `app/providers/`: `base.py` (Protocol + CompanyRef/AnnualStatement/PriceQuote), `edgar.py` (companyfacts fetch, 8 req/s token bucket, 403/429 back-off, 10-K FY-frame parsing incl. instant facts), `yahoo.py` (lazy yfinance, 0.2s serialisation, pure `parse_frames`), `registry.py` (US→EDGAR+Yahoo price; CA→Yahoo; graceful degradation).
- `app/services/`: `mapping.py` (resolve `AAPL`/`RY.TO`/`CA:RY:TSX`/`US:MMM:US`; universe_master.csv authoritative — bare CA tickers, ready Yahoo symbols, 500 US CIKs; SEC company_tickers.json fallback cached at data/sec_tickers_cache.json), `fundamentals.py` (provider fields → snapshot columns, derived FCF_Calc/NetDebt_Calc only when inputs exist), `ingest.py` (frozen overwrite policy).
- `app/jobs/backfill.py` (CLI `python -m app.jobs.backfill --mode sample|all`).
- `app/api/phase2.py`: `/companies/{id}/financials`, `/tickers/resolve`, `POST /tickers/ingest`, `POST /jobs/backfill`, `/coverage`. Phase 1 endpoints untouched.
- Schema migration `b7f2a91c4d50` (applied to data/app.db and to fresh containers via `alembic upgrade head`): `financial_snapshots.fetched_at` + `.provider_as_of`, `data_quality_flags.company_id` nullable.
- Tests: 20 new network-free fixture tests (45 total). Fixtures: `edgar_aapl_companyfacts_stub.json`, `yahoo_ry_stub.json`.

## Bugs found and fixed during verification (honest repair log)

1. **CA ticker mapping** — universe_master.csv `Primary_Ticker` is Yahoo-style (`RY.TO`) for CA rows; loader initially built `CA:RY.TO:TSX`, so `RY.TO` resolved as not-in-universe. Fixed to prefer bare `Ticker`; caught by test, confirmed by probe.
2. **Quality-flag duplication on re-import** — the first forced re-import with workbook-level flags grew the live table 2,016 → 2,095 (the `raw_id:` note prefix broke note-based dedup). Fix 1: dedup key changed to `(company_id, field, code)` with note updated in place. Fix 2: the already-polluted live DB then crashed the fixed importer (`MultipleResultsFound`), so the importer is now self-healing — first row wins, note updated in place, redundant rows removed via ORM in the same transaction (`dupes removed: 69` in the live repair run). Post-fix state: exactly 2,026 flags (2,016 company + 10 workbook-level). Regression test `test_quality_flags_dedup_across_versions`.
3. **RY "bank debt filled" was a false alarm (self-caught)** — the live Total_Debt delta +12 was provider HISTORY rows, not a seed overwrite; probe showed RY's seed Total_Debt = 545,439,000,000 comes from the owner workbook itself (90 Financials carry debt; only ~10 insurers are blank). The real carve-out implemented: providers never fill NULL Total_Debt/Gross_Profit on Financials-sector seed rows (regression test on US:AFL:US, the actual blank-debt insurer).
4. **Test hygiene** — ingests that `commit()`ed polluted the shared session fixture (duplicate 2024 rows, 721 companies). Switched to flush+rollback; suite re-ran green.
5. **Fake-frame test double** — `__getitem__` returned the whole frame dict instead of the column row; KeyError in Yahoo fixture test. Fixed.
6. **EDGAR instant-fact year inference** — balance-sheet facts (no `start`, no `frame`) initially dropped → AAPL fixture would have lost Assets/Equity. Now keyed by period-end year.
7. **backfill.py module paths** — wrong import (`app.mapping`) and misplaced model import; corrected.

## Conservative defaults chosen

1. `POST /jobs/backfill` runs **inline** (personal single-user app, no queue); `mode=all` is rate-limited by the providers themselves (SEC bucket, Yahoo 0.2s serialisation) and capped at limit=750 per call.
2. Yahoo fallback for US statements when the EDGAR call fails (logged, flagged by source), so history survives single-provider blocks.
3. Diluted_EPS falls back to Basic EPS label only when Diluted is absent (Yahoo), never invented.
4. Unknown plain tickers default to US listing (US:<TICKER>:US); resolve never fabricates a CIK — it looks one up via the SEC ticker file.
5. `price_filled=False` for the 720 seed names: Phase 1 prices already exist and the overwrite policy forbids refreshing them; provider prices only fill NULLs.

## Unverified / risks

- `--mode all` mass ingest not executed (would be a long, fully rate-limited run); sample path proves the machinery end-to-end.
- Two scratch files remain (Safety Guard blocked deletion; documented above).
- Yahoo column labels drift over time; the COLUMN_MAP covers current labels and unknown labels degrade to NULL rather than error.
- SEC company_tickers.json fallback is network-dependent on first use (cached afterwards); offline use with unknown tickers will resolve with cik=None until a cache exists.

STOP — Phase 2 complete, do not start Phase 3.
