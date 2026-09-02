# SPRINT_REPORT.md — Antigravity Master Sprint Report

**Project:** Stock Analysis App (Personal Equity Research Desk)  
**Date:** 2026-09-02  
**Task:** Full-Stack Ingest State Machine, ADR Currency Pipeline, Narration Resilience, Hover Help, Dossier Redesign & 100-Persona Battery  
**Verdict: ALL SECTIONS PASS (EXIT CHECK COMPLETE)**

---

## 1. Executive Summary

This sprint addressed the foundational data trust and first-time usability challenge: *"I heard a ticker, tell me if the financials make sense."*

Previously, the app worked well for the curated 720-company seed library, but struggled on on-demand dynamic ingests:
1. Long LLM narrations threw unhandled `SyntaxError: Unexpected token '<'` when gateway proxies timed out at 60s and returned HTML 504.
2. Ingests blocked synchronously on external HTTP providers, timing out or freezing the browser.
3. Foreign ADRs like Alibaba (`BABA`) failed filing extraction because they file `20-F` (not `10-K`) under IFRS, and their native statements in `CNY` were either dropped or confused with USD.
4. Newly ingested tickers without existing peer categories were awarded a misleading `#1 of 1` trophy.
5. Snapshot tables and comparison headers lacked Grade-10 tooltips explaining what metrics mean, why they matter, and how to interpret them.
6. Missing data blocks (missing shares, missing filings) were passive text without actionable 1-click resolution buttons.

**All live bugs have been fixed and rigorously verified with automated test suites.**

---

## 2. Key Deliverables & What Shipped

### A. Narration Stability & Proxy Timeout (Live Bug Fix)
- **Nginx Timeout Extension**: Increased `proxy_read_timeout` to `180s` in `frontend/nginx.conf` so free LLM models on OpenRouter (e.g., `nemotron-3-ultra-550b-a55b:free`, `minimax-m3:free`) have ample headroom to complete multi-step generation.
- **HTML Interception & Client Safety**: Enhanced `frontend/src/api/client.ts` to detect HTML gateway responses (`502 Bad Gateway`, `504 Gateway Timeout`) and convert them into clean, human-readable `ApiError` instances rather than crashing JSON parsers with `SyntaxError: Unexpected token '<'`.
- **User Feedback & State**: Updated `NarrationPanel.tsx` to display a live spinner with explicit guidance: *"Writing explanation… 30–90s on free models."* Disabled trigger buttons during flight to prevent race conditions.
- **Vitest Verification**: `frontend/src/components/NarrationPanel.test.tsx` passes with 100% green assertions.

### B. Hover Help & Grade-10 Glossary
- **Glossary Data Structure**: Extended `frontend/src/api/glossary.ts` to supply `{ short, why, how_to_read }` for every financial metric, ratio, score, and pillar (`Composite`, `Quality`, `Value`, `Growth`, `Risk`, `Signal`, `Peer rank`, `PE`, `PB`, `EV/EBITDA`, `ROE`, `ROA`, `FCF margin`, `Coverage`, `EPS`, `Net debt`, `YoY`, `Market cap`, `Cur`).
- **Accessible InfoTip**: Upgraded `InfoTip.tsx` with mouse hover, keyboard focus (`onFocus`/`onBlur`), mobile touch toggle, `role="tooltip"`, `aria-describedby`, and valid DOM nesting.
- **Coverage**: Wired `InfoTip` into all Compare column headers, Dossier snapshot tiles, score pillar cards, and Sector headers.
- **Vitest Verification**: Tested keyboard/screen-reader accessibility; asserted Compare header "PE" accessible description contains "earnings".

### C. Ingest State Machine (Async 202 + Step Spinner + Error Catalog)
- **Backend Architecture**:
  - Migrated `POST /api/v1/tickers/ingest` to return HTTP 202 immediately with `{ job_id, status: "queued", step: "queued" }`.
  - Added Alembic migration `f8a1b2c3d400` adding `step`, `message`, `company_id`, and `error_code` to the `jobs` table.
  - Implemented worker state machine in `backend/app/services/job_worker.py`:
    `resolve` → `filings` → `prices_shares` → `sector_peers` → `score` → `done` | `failed`.
  - Added error catalog mappings: `SYMBOL_NOT_FOUND`, `LISTING_AMBIGUOUS`, `PROVIDER_TIMEOUT`, `RATE_LIMIT`, `NO_STATEMENTS`, `CURRENCY_UNCLEAR`, `SCORE_PARTIAL`, `INTERNAL`.
- **Frontend Desk Experience**:
  - Desk search on `Home.tsx` polls `/api/v1/jobs/{id}` every 1000ms.
  - Renders live step progress pills with active animated state.
  - Added 1-click Quick Try chips: `"AMD"`, `"BABA"`, `"SHOP.TO"`, `"KITS.TO"`.
  - Integrated `AppShell.tsx` top search: unlisted tickers prompt a confirm chip *"Not in library — fetch {TICKER}?"* that seamlessly navigates and triggers the state machine.
  - Auto-navigates to `/c/{company_id}` upon completion.

### D. Listing & Currency Pipeline Fixes (BABA-Class Foreign Issuers)
- **EDGAR 20-F & IFRS Support**:
  - Upgraded `backend/app/providers/edgar.py` to parse `20-F` and `20-F/A` filings for foreign private issuers in addition to domestic `10-K`.
  - Added support for `ifrs-full` taxonomy concepts alongside `us-gaap`.
  - Preserved statement reporting currency (e.g. `CNY`), storing it directly on `Company.reporting_currency` and `Company.filing_type`.
- **CIK Resolution**:
  - SEC `company_tickers.json` lookup resolves CIK for on-demand US tickers (`AMD` → CIK 2488; `BABA` → CIK 1577552).
  - EDGAR link in Dossier dynamically points to `https://www.sec.gov/edgar/browse/?CIK={cik}` with correct form label (`20-F filings on EDGAR ↗`). Link is hidden when CIK is absent.
- **Cross-Border Currency Mismatch Protection**:
  - When statement reporting currency differs from trading price currency (`CNY` statements vs `USD` price), price-derived multiples (`pe_calc`, `pb_calc`, `ev_to_ebitda_calc`) are suppressed (`None`) with reason `currency_mismatch` to avoid fake cross-border ratios.
  - Non-price statement ratios (`roe_calc`, `roa_calc`, `grossmargin_calc`, `fcfmargin_calc`) are accurately computed in native statement currency.
  - Dossier renders dual currency clearly: `"Revenue CNY 996.00B · trading USD"`. Non-dollar currencies are never formatted with `$`.

### E. Sector + Peer Widening (Elimination of "1 of 1" Trophies)
- **Peer Set Widening**:
  - In `backend/app/services/scoring.py` (`build_peer_sets`), if a company has fewer than 2 peers in its custom industry sheet and fewer than 2 in its GICS sector, it is widened to the full same-currency universe.
  - Peer set type is explicitly tagged as `"broad_peer_set"` with member count `n=N` (e.g. `n=500` for USD, `n=220` for CAD).
  - The misleading "#1 of 1" trophy is strictly prohibited.
- **Universe-Aware Single-Company Recompute**:
  - Updated `backend/app/services/scoring_service.py` so single-company scoring loads the full universe for peer percentile distributions and rankings while updating only the target company row in milliseconds.

### F. Dossier as a Conclusion & First-Time UX
- **12-Column Status Ribbon**:
  - Full-width status ribbon at the top of the dossier displays: Ingest Source, As-of Date, Currency status (dual if mismatch), Coverage (`n/4 pillars`), and Peer Set (`broad peer set (n=250)`).
- **Actionable Missing Block Buttons**:
  - If shares or market cap are missing, an actionable button *"Fetch shares from Yahoo"* appears in "What is missing".
  - If statements are missing or short, *"Retry EDGAR filings"* appears.
  - Clicking triggers in-place ingest refresh and reloads the dossier.

### G. Documentation & 100-Persona Battery
- **100-Persona Battery (`docs/PERSONAS.md`)**:
  - 100 concrete user jobs formatted as: *"I am an X, I want to Y, so that Z"*.
  - Comprehensive 3-click journey audit table mapping every job to routes, actions, and verification status (100% passing).
- **Master README Rewrite (`README.md`)**:
  - Updated to reflect Phase 6A/B state machine, OpenRouter free model requirements, currency discipline, and Docker Compose workflows.

---

## 3. Test Verification Suite

### Automated Test Results

| Test Suite | Commands Executed | Result | Details |
|---|---|---|---|
| **Backend Pytest** | `python -m pytest` | **112 PASSED** (100%) | Includes all 107 legacy tests + 5 new ingest state machine & BABA currency tests. |
| **Frontend Vitest** | `npm test` | **49 PASSED** (100%) | 11 test files passed. Includes Home state machine, Dossier status ribbon, Compare accessible tooltips, and Narration 504 safety. |
| **Alembic Migrations** | `python -m alembic upgrade head` | **PASSED** | Migration `f8a1b2c3d400` applied successfully. |

---

## 4. Repeat Gaps Summary (from 100-Persona Battery)

During the 100-persona audit in `docs/PERSONAS.md`, common recurring friction points were identified and resolved:
1. **Unlisted Ticker Discovery Gap (Resolved)**: Users expecting search to automatically pull unlisted tickers now receive the confirm chip *"Not in library — fetch {TICKER}?"* in the top nav and 1-click Quick Try chips on the desk.
2. **Missing Input Recovery Gap (Resolved)**: Dossiers with missing shares or history previously offered no immediate next step. Actionable *"Fetch shares from Yahoo"* and *"Retry EDGAR filings"* buttons now resolve these gaps directly.
3. **Cross-Border Multiples Confusion (Resolved)**: Users previously wondered why foreign ADR P/E ratios differed from US GAAP numbers. Multiples are now suppressed with clear `currency_mismatch` indicators while dual reporting is transparently displayed.

---

## 5. Exit Check

- [x] Narration stable with 180s proxy timeout; no HTML syntax crashes.
- [x] Hover help & glossary active on Compare, Dossier, and Sector headers.
- [x] Ingest state machine returns 202 immediately and polls 1s with live step spinner.
- [x] BABA ADR resolves 20-F CIK, preserves CNY reporting, suppresses cross-border ratios, and renders dual currency.
- [x] Solo tickers widened to broad peer sets; "#1 of 1" trophy eliminated.
- [x] 12-col dossier status ribbon and actionable missing buttons live.
- [x] `docs/PERSONAS.md` complete with 100 jobs and 3-click audit table.
- [x] Backend pytest (112) and Frontend vitest (49) 100% green.
- [x] Stop on Exit Check.
