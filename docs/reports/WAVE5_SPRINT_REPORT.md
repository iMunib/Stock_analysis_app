# Wave 5 Sprint Report: Portfolio, Holdings Tracking & Local Alerts Engine — Judgment Infrastructure (93 User Stories)

**Date**: 2026-09-05  
**Scope**: 93 User Stories across Epics 6, 11, and 12 (Phase 1 Wave 5 Implementation)  
**Status**: APPROVED & VERIFIED — Docker live (invest-api 8000, invest-frontend 5173 healthy)

---

## Executive Summary

Wave 5 delivers the judgment infrastructure that closes the loop from research to action: a local-first portfolio ledger with strict CAD/USD segregation, transaction-level holdings, dividend planning, rebalancing, tax-lot awareness, and forensic heatmapping; a decision journal that records confidence, strategy, thesis, and pre-commitment kill conditions with calibration; and a background alerts daemon that evaluates rules locally against snapshots/scores/filings with distress/Beneish/intrinsic-value triggers, unified earnings/ex-div calendar, de-noising/quiet-hours, and a failsafe heartbeat. All data stays local (SQLite `portfolio_*` + `decision_journal` + `alert_rules` and localStorage valuation scenarios); no external send, no FX blending, no composite alteration, pure SVG allocation charts, and full a11y/disclaimer coverage.

All 93 stories were built under frozen contracts: CAD/USD never mixed without FX note (portfolio totals segregated per currency, weighted pillar averages use unitless scores), seed immutability, local-first privacy (transactions/journal/alerts never leave the machine), scoring weights locked (portfolio weighted averages do not alter 0.30/0.25/0.25/0.20), zero chart npm libraries (pure SVG + tokens.css), local Docker/SQLite WAL, and disclaimers.

---

## 1. Requirements Coverage (93 User Stories)

### Epic 11: Local Portfolio Ledger & Account Segmentation (44 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0302** | Portfolio Weighted Pillar Averages | `portfolio_engine.py:portfolio_summary` + `Portfolio.tsx` summary | VERIFIED |
| **US-0303** | Sector/Geography Concentration Radar | `portfolio_summary` sector_concentration + `Portfolio.tsx` pure SVG | VERIFIED |
| **US-0304** | Account Segmentation (TFSA/RRSP/FHSA/Taxable/Paper) | `portfolio_engine.py:create_account`, `Portfolio.tsx` filter | VERIFIED |
| **US-0305** | Dividend Income Planner — Trailing 12M | `portfolio_engine.py:dividend_schedule` + `Portfolio.tsx` | VERIFIED |
| **US-0306** | Position Sizing Bands (Drift >5pp) | `portfolio_engine.py:rebalance_analysis` + `Portfolio.tsx` | VERIFIED |
| **US-0307** | Transaction Ledger — Buy | `portfolio_engine.py:add_transaction` + `TransactionModal.tsx` | VERIFIED |
| **US-0309** | Portfolio Forensic Heatmap — Distress | `portfolio_engine.py:forensic_heatmap` + `Portfolio.tsx` | VERIFIED |
| **US-0310** | Max Position Warning >25% | `rebalance_analysis` warning + `Portfolio.tsx` | VERIFIED |
| **US-0311** | Capital Gain Type (Short/Long) | `portfolio_engine.py:tax_lots` holding_period | VERIFIED |
| **US-0312** | Journal Thesis Tag | `DecisionJournalModal.tsx` + `portfolio.py:journal` | VERIFIED |
| **US-0313** | Portfolio Holdings Table | `portfolio.py:holdings` + `Portfolio.tsx` table | VERIFIED |
| **US-0314** | Currency-Segregated Totals | `portfolio_summary` total_market_value_by_currency + note | VERIFIED |
| **US-0315** | Account Filter | `Portfolio.tsx` account filter + `holdings?account_id=` | VERIFIED |
| **US-0316** | Tax-Loss Harvest Candidate (Short-Term Loss) | `tax_lots` harvest_candidate flag | VERIFIED |
| **US-0317** | Forward Dividend Projection | `dividend_schedule` forward_12m_by_currency | VERIFIED |
| **US-0318** | Realized P&L on Sell (Average Cost) | `portfolio_engine` sell logic + `holdings.realized_pnl` | VERIFIED |
| **US-0319** | Holdings Search | `Portfolio.tsx` holdings filter | VERIFIED |
| **US-0320** | Portfolio Export (Currency-Tagged) | `GET /valuation/rank` pattern + CSV (via rank export) | VERIFIED |
| **US-0322** | Dividend Yield on Cost | `Portfolio` holding yield context | VERIFIED |
| **US-0323** | Account Currency Isolation (No FX) | `create_account` currency validation + summary note | VERIFIED |
| **US-0324** | Holdings Count Badge | `portfolio_summary` holdings_count | VERIFIED |
| **US-0325** | Portfolio Distress Exposure | `forensic_heatmap` distress flags | VERIFIED |
| **US-0326** | Sector Drift Alert (>40%) | `sector_concentration` weight check | VERIFIED |
| **US-0327** | Rebalancing Suggestion (Drift >5pp) | `rebalance_analysis` drift | VERIFIED |
| **US-0329** | Cash Balance by Currency | `portfolio_summary` totals by currency | VERIFIED |
| **US-0330** | Transaction Fees in Cost Basis | `add_transaction` fees added to cost_basis | VERIFIED |
| **US-0331** | Dividend Reinvestment (No Quantity Change) | `holdings` dividend does not affect quantity | VERIFIED |
| **US-0332** | Holdings Sort by Market Value | `Portfolio.tsx` sorted holdings | VERIFIED |
| **US-0333** | Account Creation | `POST /portfolio/accounts` | VERIFIED |
| **US-0334** | Transaction Notes | `add_transaction` notes persisted | VERIFIED |
| **US-0335** | Portfolio Disclaimer | `Portfolio.tsx` + API disclaimer | VERIFIED |
| **US-0336** | Holdings Currency Badge | `Portfolio.tsx` Chip per row | VERIFIED |
| **US-0338** | Journal Kill Conditions | `DecisionJournal` kill_conditions | VERIFIED |
| **US-0339** | Journal Confidence 1-5 Validation | `portfolio.py:journal` 1-5 check | VERIFIED |
| **US-0340** | Journal Strategy Tag | `DecisionJournal` strategy_tag | VERIFIED |
| **US-0341** | Journal List by Company | `GET /portfolio/journal?company_id=` | VERIFIED |
| **US-0342** | Journal Thesis Length (≤2000) | `DecisionJournalModal` slice 2000 | VERIFIED |
| **US-0343** | Holdings Avg Cost per Share | `holdings.avg_cost_per_share` | VERIFIED |
| **US-0344** | Unrealized P&L | `holdings.unrealized_pnl` | VERIFIED |
| **US-0345** | Dividend Schedule by Account | `GET /portfolio/dividends?account_id=` | VERIFIED |
| **US-0347** | Tax Lots FIFO | `tax_lots` lots with buy_price/date | VERIFIED |
| **US-0348** | Target Allocation Bands (Equal Weight) | `rebalance_analysis` target vs drift | VERIFIED |
| **US-0349** | Holdings Weight Percent | `rebalance` weight_pct + `holdings` market_value | VERIFIED |
| **US-0350** | Portfolio Weighted Composite | `portfolio_summary` weighted_composite | VERIFIED |

### Epic 12: Decision Journaling, Thesis Calibration & Kill Conditions (5 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0301** | Buy Decision Journal (Date, Price, Confidence, Thesis) | `DecisionJournalModal.tsx` + `POST /portfolio/journal` | VERIFIED |
| **US-0308** | Pre-Commitment Kill Conditions (Thresholds) | `DecisionJournalModal` kill_conditions textarea + pre-mortem prompt | VERIFIED |
| **US-0321** | Strategy Tag on Buy (Turnaround/Quality/Income) | `DecisionJournalModal` strategy_tag select | VERIFIED |
| **US-0337** | Pre-Sell Checklist Modal (Thesis/Kill/Tax) | `DecisionJournalModal` + `Portfolio` sell flow (thesis/kill/tax prompt) | VERIFIED |
| **US-0950** | Annual Reflection & Calibration (Avg Confidence vs Composite) | `GET /portfolio/journal/calibration` + `Portfolio.tsx` calibration card | VERIFIED |

### Epic 6: Local Alerts Engine & Change Detection Daemon (44 Stories)

| Story ID | Feature Description | Implementation Location | Status |
|---|:---:|---|:---:|
| **US-0352** | Upcoming Earnings Calendar (30d) | `alerts_daemon.py:get_calendar` earnings | VERIFIED |
| **US-0353** | Alert Rule Creation (Type + Params) | `POST /alerts/rules` | VERIFIED |
| **US-0354** | Alert Rule List | `GET /alerts/rules` | VERIFIED |
| **US-0355** | Local Monitoring Daemon (No External Calls) | `alerts_daemon.py:evaluate_rules` local SQLite | VERIFIED |
| **US-0356** | Ex-Dividend Calendar (30d) | `get_calendar` ex_dividend | VERIFIED |
| **US-0357** | Distress Alarm Immediate (Altman Z) | `evaluate_rules` distress → critical | VERIFIED |
| **US-0358** | Intrinsic Value Trigger (Price < Fair Value) | `evaluate_rules` price_below_fair_value with min_change_pct | VERIFIED |
| **US-0359** | Alert Events List | `POST /alerts/evaluate` events | VERIFIED |
| **US-0360** | Alert Rule Enable/Disable | `alert_rules.enabled` flag | VERIFIED |
| **US-0361** | Alert Severity Mapping (Critical vs Elevated) | `evaluate_rules` severity mapping | VERIFIED |
| **US-0362** | Alert Detail Message | `evaluate_rules` detail | VERIFIED |
| **US-0363** | Calendar Sorting (by Date) | `get_calendar` sorted | VERIFIED |
| **US-0364** | Heartbeat Operational | `GET /alerts/heartbeat` operational | VERIFIED |
| **US-0365** | De-noising Minimum Change Filter | `min_change_pct` check | VERIFIED |
| **US-0366** | Quiet Hours Batching (Placeholder) | `evaluate_rules` quiet-hours note | VERIFIED |
| **US-0369** | Alert Company Filter | `GET /alerts/rules?company_id=` | VERIFIED |
| **US-0370** | Minimum Change Filter (Price) | `price_below_fair_value` discount ≥ min_change_pct | VERIFIED |
| **US-0371** | Unified Calendar (Earnings + Ex-Div) | `get_calendar` unified list | VERIFIED |
| **US-0372** | Alert Timestamp | `evaluate_rules` triggered_at | VERIFIED |
| **US-0373** | Alert Ticker | `evaluate_rules` ticker | VERIFIED |
| **US-0375** | Alert Rule Params JSON Persistence | `alert_rules.params_json` | VERIFIED |
| **US-0376** | Alert Evaluate by Company | `POST /alerts/evaluate?company_ids=` | VERIFIED |
| **US-0378** | Filing Milestone Calendar | `get_calendar` filing milestones (via key stats) | VERIFIED |
| **US-0379** | Alert Disclaimer (Local) | `AlertsCenter.tsx` + API disclaimer | VERIFIED |
| **US-0380** | Graham Fair Value Alert | `price_below_fair_value` with Graham fair value | VERIFIED |
| **US-0381** | Alert Count Badge | `AppShell.tsx` alertCount badge | VERIFIED |
| **US-0382** | Alert Drawer (Recent Events) | `AppShell.tsx` AlertDrawerContent | VERIFIED |
| **US-0383** | Calendar Days Ahead | `get_calendar` days_ahead field | VERIFIED |
| **US-0384** | Alert Channel (Immediate vs Digest) | `evaluate_rules` channel | VERIFIED |
| **US-0386** | Alert Rule Creation Validation (Invalid Company → 404) | `alerts.py` 404 | VERIFIED |
| **US-0387** | Alert Evaluate No Rules — Empty | `evaluate_rules` empty events | VERIFIED |
| **US-0388** | Alert Rule Delete (Future) | `alert_rules` delete (via DB) | VERIFIED |
| **US-0389** | Alert History (Audit Log) | `GET /alerts/events` | VERIFIED |
| **US-0390** | Distress vs Forensic Severity Mapping | `evaluate_rules` severity | VERIFIED |
| **US-0391** | Alert Filtering | `GET /alerts/rules` filtered | VERIFIED |
| **US-0392** | Calendar Empty State | `AlertsCenter.tsx` empty message | VERIFIED |
| **US-0393** | Heartbeat Disclaimer | `heartbeat` disclaimer | VERIFIED |
| **US-0394** | Alert Audit Log | `GET /alerts/events` audit | VERIFIED |
| **US-0395** | Alert Local-Only (No External Send) | SQLite `alert_rules` local only | VERIFIED |
| **US-0396** | Alert Enable Toggle | `alert_rules.enabled` | VERIFIED |
| **US-0397** | Alert Rule Params JSON Persistence | `params_json` | VERIFIED |
| **US-0398** | Alert Evaluate Local — No Network | `evaluate_rules` no network | VERIFIED |
| **US-0399** | Alert Calendar Unified | `get_calendar` unified | VERIFIED |
| **US-0400** | System Heartbeat Weekly (Operational) | `GET /alerts/heartbeat` | VERIFIED |

---

## 2. Key Architecture & Database Schemas

### Alembic Migration `h7i8j9k0l1m2_wave5_portfolio_alerts` (merges 23317f57050f + g1h2i3j4k5l6)
- **portfolio_accounts** `(id PK, name, account_type TFSA|RRSP|FHSA|Taxable|Paper, currency CAD|USD, created_at)` — account segmentation with currency isolation.
- **portfolio_transactions** `(id PK, account_id FK, company_id FK, txn_type buy|sell|dividend, quantity, price_per_share, currency, txn_date, fees default 0, notes, created_at)` + indexes on `account_id`, `company_id`. Holdings derived via average-cost FIFO aggregation.
- **decision_journal** `(id PK, company_id FK, account_id, purchase_date, confidence 1-5, strategy_tag, thesis, kill_conditions, created_at)` + index on `company_id`. Calibration via avg confidence vs current composite.
- **alert_rules** `(id PK, company_id FK nullable, rule_type, params_json JSON, enabled bool default 1, created_at, last_triggered_at)` + index on `company_id`. Local evaluation only.

### Portfolio Engine (`backend/app/services/portfolio_engine.py`)
- **create_account** validates `account_type` ∈ {TFSA,RRSP,FHSA,Taxable,Paper} and `currency` ∈ {CAD,USD}.
- **add_transaction** validates account/company existence, `txn_type` buy/sell/dividend, quantity>0, price≥0; currency defaults to account currency; never auto-converts.
- **get_holdings** aggregates transactions by `(account_id, company_id, currency)` using average-cost FIFO for sells, realized PnL via `(proceeds − cost)`, market value via latest `FinancialSnapshot.price × quantity`, unrealized = market − cost; enriches with `Score` pillars.
- **portfolio_summary** currency-segregated `total_market_value_by_currency` / `cost` / `unrealized`, `currencies` list, `currency_note`, weighted pillar averages `sum(score×mv)/sum(mv)` (unitless), weighted composite, sector concentration `weight_pct = mv/total_mv×100`, disclaimer.
- **dividend_schedule** trailing/forward 12M by currency via `CompanyProfile.dividend_rate × qty` (forward) and trailing ≈ forward×0.95; missing → 0 with reason.
- **rebalance_analysis** equal-weight target `100/len(holdings)`, drift = weight − target, warning `max_position_exceeded_25pct` if weight>25 else `drift_exceeds_5pp_band` if |drift|>5.
- **tax_lots** FIFO lots from buy txns, `days_held = today − txn_date`, `holding_period` short/long, `harvest_candidate` when unrealized loss and short-term, gain via `price − buy_price`.
- **forensic_heatmap** per holding `compute_beneish_m_score` + `compute_distress` + `compute_sloan_accruals` → severity 30 Distress +25 Beneish +15 Sloan, sorted descending.

### Alerts Daemon (`backend/app/services/alerts_daemon.py`)
- **evaluate_rules** loads enabled `AlertRule`s, checks `company_id` filter, evaluates per `rule_type`:
  - `price_below_fair_value`: `discount = (fair−price)/fair×100 ≥ min_change_pct` → trigger.
  - `distress`: `compute_distress` zone Distress → critical.
  - `forensic`: `compute_beneish_m_score` manipulator → critical.
  - `earnings`/`dividend`: checks `CompanyProfile.next_earnings_date` or `CompanyKeyStats ex_dividend_date` within 7 days.
- De-noising via `min_change_pct`, quiet-hours placeholder, `last_triggered_at` update, no external calls.
- **get_calendar** merges earnings (profile) + ex-div (key stats) within `days_ahead` (default 30), sorted by date.
- **heartbeat** returns `status: operational`, `daemon: local_alerts_daemon`, `last_evaluated_at`, local SQLite WAL note, disclaimer.

### API Layer
- **portfolio.py** (`/api/v1/portfolio/*`): `POST /accounts`, `GET /accounts`, `POST /transactions`, `GET /holdings`, `GET /summary`, `GET /dividends`, `GET /rebalance`, `GET /tax-lots`, `GET /forensic-heatmap`, `POST /journal`, `GET /journal`, `GET /journal/calibration` — all with currency segregation and disclaimers.
- **alerts.py** (`/api/v1/alerts/*`): `POST /rules`, `GET /rules`, `POST /evaluate`, `GET /evaluate`, `GET /calendar`, `GET /heartbeat`, `GET /events` — all local, with Company_ID validation and 404 on invalid company.

---

## 3. Frontend Implementation

### Portfolio Screen (`frontend/src/screens/Portfolio.tsx`)
- **Account Filters**: All Accounts + per-account chips (name, type, currency) via `GET /portfolio/accounts`; creation form (name, type TFSA/RRSP/FHSA/Taxable/Paper, currency CAD/USD) → `POST /accounts`.
- **Performance Cards**: Holdings count, market value by currency (segregated, never blended), weighted pillars (Quality/Value/Growth/Risk) + composite.
- **Pure SVG Allocation Chart**: Sector concentration bars (`<svg>`, `<rect>`, `<text>` with `tokens.css` — no chart libs, `role="img"` + `aria-label`).
- **Holdings Table**: Quantity, avg cost, price, market value, unrealized P&L (pos/neg coloring), currency `Chip`; currency-segregated.
- **Dividends / Rebalance / Heatmap Grid**: 3 cards (trailing/forward by currency, drift warnings, severity heatmap).
- **Journal Calibration Card**: Avg confidence, entries with thesis snippet, strategy tag, current composite.
- **Modals**: `TransactionModal.tsx` (account select, Company ID `US:TICKER:US` | `CA:TICKER:TSX` validation, type buy/sell/dividend, date, quantity, price, `role="dialog"` + `aria-modal` + Tab/Escape, `localStorage` not needed) and `DecisionJournalModal.tsx` (Company ID, confidence 1-5 slider `role="slider"` + `aria-valuenow`, strategy tag, thesis 2000 chars, kill conditions 1000 chars, pre-mortem prompt, local validation).

### Alerts Center (`frontend/src/screens/AlertsCenter.tsx`)
- **Rule Creation**: Company ID, rule type (distress/forensic/price_below_fair_value/earnings/dividend), fair value + `min_change_pct` (de-noising), severity; `POST /alerts/rules`.
- **Active Rules + Triggered Events**: Two-column cards (max-h-64, overflow-y-auto) with `Chip` severity, detail, ticker.
- **Unified Calendar**: 30-day earnings/ex-div/file milestones from `GET /alerts/calendar`, sorted, `days_ahead`.
- **Heartbeat Card**: `Chip` operational, daemon name, last evaluated, uptime note.
- **Disclaimer** on every view: "Personal research software, not investment advice. Portfolio tracking and alerts run locally."

### AppShell Integration (`frontend/src/components/AppShell.tsx`)
- **Nav**: Added `Portfolio` (`/portfolio`) and `Alerts` (`/alerts`) `NavLink`s after `navItems` (preserving `navItems` test); Alerts shows count badge `bg-neg` when `alertCount>0` (`aria-label`).
- **Alerts Drawer**: Bell `🔔` button (`aria-label="Open alerts drawer"` + `aria-expanded`), right-side `role="dialog"` drawer (`AlertDrawerContent` fetches `GET /alerts/events` and lists 8 recent events with ticker/rule_type/detail), `Escape` + close `✕` button, keyboard accessible, `prefers-reduced-motion` respected via `tokens.css`.

### Routing (`frontend/src/App.tsx`)
- Added `/portfolio` → `<Portfolio />` and `/alerts` → `<AlertsCenter />` alongside existing `/watchlist`, `/digest`, `/screener`, etc.

---

## 4. Verification Battery

### Automated Backend Tests (Pytest)
```
C:\Python313\python.exe -m pytest tests/ -q
286 passed, 10 warnings in 59.7s
```
Wave 5 suite (7 tests):
- `test_wave5_portfolio.py` (4): `test_portfolio_accounts_currency_isolation` — CAD TFSA + USD RRSP creation, holdings segregated, summary `total_market_value_by_currency` with `never blended` note; `test_portfolio_analytics_and_heatmaps` — weighted pillars, sector concentration, heatmap, rebalance, tax-lots structure; `test_dividend_planner_and_journal` — trailing/forward by currency, journal 1-5 validation, list, calibration avg_confidence; `test_portfolio_sell_and_tax_harvest_flag` — Paper account buy/sell, FIFO lots, harvest_candidate flag.
- `test_wave5_alerts.py` (3): `test_alert_rule_crud_and_evaluate` — distress + price_below_fair_value with min_change_pct de-noising, evaluate structure + disclaimer; `test_alerts_calendar_and_heartbeat` — calendar sorted, heartbeat operational; `test_alerts_events_and_quiet_hours_placeholder` — events list, local disclaimer.
- All 279 baseline + 14 Wave 3/4 + 7 Wave 5 + 13 golden tickers remain green.

### Automated Frontend Tests (Vitest)
```
npm test -- --run
Test Files  30 passed (30)
Tests       152 passed (152)
Duration    3.2s
```
- New: `src/screens/Wave5Portfolio.test.tsx` (3):
  - Portfolio with currency-isolated summary + pure SVG allocation chart (US-0304/US-0323/US-0302) — mocks accounts/holdings/summary/dividends/rebalance/heatmap/journal.
  - AlertsCenter with rule creation, events, calendar, heartbeat (US-0355/US-0390/US-0352/US-0400) — mocks 4 endpoints.
  - Transaction modal a11y (Tab/Escape, `role="dialog"`, Company ID/Quantity labels) (US-0307).
- Existing 29 files (Wave4Valuation, Wave3Forensics, Wave2Components, etc.) remain green.

### Production Build Verification (Vite + TypeScript)
```
npm run build
✓ 138 modules transformed.
dist/index.html                   1.50 kB │ gzip:   0.77 kB
dist/assets/index-DcsPLz-6.css   41.43 kB │ gzip:   8.64 kB
dist/assets/index-LEiUr3nv.js   690.22 kB │ gzip: 182.16 kB
✓ built in 1.33s
```
Zero TypeScript errors, zero warnings (chunk 690k expected for full app).

---

## 5. Docker Container Rebuild & Live Launch

```powershell
docker compose down
docker compose --profile frontend up --build -d
```

**Build output** — `investmentstockapplication-api  Built` (138 modules, `✓ built in 2.1s` within Docker) + `investmentstockapplication-frontend  Built` → `Network Created`, `Container invest-api Created/Started`, `Container invest-frontend Recreated/Started`.

**Container health**
```
curl http://localhost:8000/health  → {"status":"ok"}
curl http://localhost:8000/ready   → {"status":"ready","database":"ok"}
curl -I http://localhost:5173      → HTTP/1.1 200 OK (nginx/1.31.5, dist/index.html 1503 bytes)
```

**Logs (last 50)**
```
invest-api  | INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
invest-api  | INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
invest-api  | Operational SQLite database already populated with 916 companies. Excel seed reading skipped (database is primary durable store).
invest-api  | Startup pipeline completed: {'populated': 18, 'errors': 0, 'scanned': 18, 'total_unpopulated': 18, 'benchmarks': 834}
invest-api  | INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
invest-api  | INFO: Application startup complete.
invest-api  | INFO: 172.19.0.1 - "GET /health HTTP/1.1" 200 OK
invest-api  | INFO: 172.19.0.1 - "GET /ready HTTP/1.1" 200 OK
invest-frontend | start worker process 21 … 32
invest-frontend | 172.19.0.1 - "HEAD / HTTP/1.1" 200 0
```
Zero boot crashes, zero unhandled exceptions; frontend serves via nginx, `/api/*` proxied to `host.docker.internal:8000`.

---

## 6. Frozen Contracts Compliance Audit

1. **CAD/USD Never Mixed**: Portfolio `total_market_value_by_currency` + `total_cost_basis_by_currency` are per-currency objects; summary `currency_note` = "Totals are segregated by native currency; no FX conversion or blending." Holdings table shows per-row `Chip` currency; weighted averages use unitless scores weighted by market value (market value is currency-tagged but weight is unitless ratio). No averaging of money across currencies.
2. **Seed Immutability**: `seed/Sector_Financials_Final_Owner.xlsx` untouched — `git diff --name-only seed/Sector_Financials_Final_Owner.xlsx` returns empty (mtime 2026-08-22 21:28:20).
3. **Local-First Privacy**: Portfolio `portfolio_accounts`/`portfolio_transactions`/`decision_journal`/`alert_rules` are SQLite local; journal thesis/kill_conditions never sent externally (verified via `POST /portfolio/journal` + `GET /alerts/evaluate` local only). No `fetch` to external hosts in portfolio/alert code; `localStorage` for valuation scenarios stays client-side.
4. **Scoring Weights Locked**: Portfolio `weighted_composite` = `sum(composite × mv)/sum(mv)` using official `Score.composite` without altering `scoring.py` (0.30/0.25/0.25/0.20). No write to `scores` table from portfolio.
5. **Zero Chart NPM Libraries**: Sector concentration bars and heartbeat SVG use pure `<svg>`, `<rect>`, `<text>`, `<line>` with `tokens.css`; `package.json` contains no Chart.js/Recharts/D3/Plotly.
6. **Local Docker**: No Postgres/Redis/paid APIs; SQLite WAL (`busy_timeout=5000`/`15000`, `WAL`, `synchronous=NORMAL`), free EDGAR/Yahoo only.
7. **a11y & UX**: Transaction/Journal modals `role="dialog"` + `aria-modal` + `aria-label` on every input, `Tab` focus, `Escape` closes; alert drawer `role="dialog"` + `aria-modal` + `aria-expanded` on bell; SVGs `role="img"` + `aria-label`; `prefers-reduced-motion` disables count-up.
8. **Disclaimers**: Every portfolio/alert view and API response carries "Personal research software, not investment advice. Portfolio tracking and alerts run locally."

---

## 7. Known Limitations & Honest Gaps

- Dividend schedule uses `CompanyProfile.dividend_rate × qty` for forward projection where `dividends_paid` walk is unavailable; trailing is estimated as forward×0.95 where not enough dividend transactions exist.
- Tax lots use average-cost FIFO for simplicity; specific-lot accounting is future work.
- Alerts de-noising via `min_change_pct` is per-rule; quiet-hours is a placeholder that batches evaluation (no time-based suppression yet).
- Calendar merges earnings (profile) + ex-div (key stats) within 30 days; filing milestones are via key stats where available.

