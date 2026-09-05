# MASTER FUNCTIONAL PHASES: LOCAL CORE APPLICATION & FINANCIAL ENGINES
## Local Development Roadmap for the Definitive Equity Analysis Engine
**Repository:** `Investment Stock Application` ([README.md](README.md) | [AGENTS.md](AGENTS.md))  
**UI/UX Design Reference:** [docs/UI_UX_SPECIFICATION.md](docs/UI_UX_SPECIFICATION.md) (Dedicated future UI session)  
**Status:** Approved Architecture — Tailored for Local Application Functionality  

---

### STRATEGIC FOCUS: UNMATCHED LOCAL RESEARCH POWER

Per user directive, **commercialization, multi-tenant cloud infrastructure, auth, billing, and UI design are deferred to dedicated future sessions**. 

This roadmap focuses 100% on **local development**, **backend financial intelligence**, **data integrity**, and **forensic depth**. The goal is to build an application whose analytical engines, literature grounding, and automated decision synthesis outcompete every existing equity research platform (Simply Wall St, Koyfin, GuruFocus, Fast Graphs, Morningstar) in accuracy, reliability, and insight.

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                           5-PHASE LOCAL FUNCTIONAL ROADMAP                            │
├───────────────┬───────────────────────────────────────────────────────────────────────┤
│ Phase 1       │ Foundation & Data Integrity Hardening (Schema & 10-K Line Items)      │
│ Phase 2       │ Core Analytical Engines & Decision Logic (The 7-Pillar Math Suite)    │
│ Phase 3       │ Forensic Accounting & Capital Allocation Deep Dive                    │
│ Phase 4       │ Advanced Screening, ETF Cohorts & Peer Benchmarking                   │
│ Phase 5       │ Dossier API Synthesis, Async Ingestion & System Hardening             │
└───────────────┴───────────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: FOUNDATION & DATA INTEGRITY HARDENING
**Goal:** Eliminate all heuristic proxies in the scoring and forensic engines by expanding the SQLite database schema to store genuine, multi-line balance sheet and cash flow statement filings from SEC EDGAR, strictly enforcing Rule #3 ("Never invent numbers").

### Tasks:
- [ ] **Task 1.1: Database Schema Expansion (Alembic Migration)**
  - Add missing GAAP/IFRS statement columns to the `financial_snapshots` table:
    - `accounts_receivable` (INTEGER / BIGINT)
    - `inventory` (INTEGER / BIGINT)
    - `current_assets` (INTEGER / BIGINT)
    - `current_liabilities` (INTEGER / BIGINT)
    - `ppe_net` (Property, Plant & Equipment, Net) (INTEGER / BIGINT)
    - `retained_earnings` (INTEGER / BIGINT)
    - `stock_based_compensation` (INTEGER / BIGINT)
    - `interest_income` (INTEGER / BIGINT)
  - Generate and test Alembic migration script (`alembic/versions/*_expand_statement_columns.py`).
  - Ensure zero regression on existing 720 seed snapshot rows (`Sector_Financials_Final_Owner.xlsx` immutability preserved).
- [ ] **Task 1.2: SEC EDGAR Parser Upgrade (`edgar.py`)**
  - Map genuine US-GAAP taxonomy tags in `backend/app/providers/edgar.py`:
    - Accounts Receivable (`AccountsReceivableNetCurrent`, `ReceivablesNetCurrent`)
    - Inventory (`InventoryNet`)
    - Current Assets (`AssetsCurrent`)
    - Current Liabilities (`LiabilitiesCurrent`)
    - Net PP&E (`PropertyPlantAndEquipmentNet`)
    - Retained Earnings (`RetainedEarningsAccumulatedDeficit`)
    - Stock-Based Compensation (`AllocatedShareBasedCompensationExpense`, `ShareBasedCompensation`)
    - Interest Income (`InvestmentIncomeInterest`, `InterestAndDividendIncomeOperating`)
  - Ensure missing provider fields gracefully stay `None`/`NULL` without crashing.
- [ ] **Task 1.3: Eliminate Beneish M-Score Heuristic Proxies (`beneish_engine.py`)**
  - Refactor `backend/app/services/beneish_engine.py`:
    - Replace fixed $DSRI=1.0$ with genuine Days Sales in Receivables Index:
      $$DSRI = \frac{\text{Receivables}_t / \text{Sales}_t}{\text{Receivables}_{t-1} / \text{Sales}_{t-1}}$$
    - Replace $0.35$ asset multiplier with true Asset Quality Index ($AQI$):
      $$\text{Non-Current Assets} = \text{Total Assets} - \text{Current Assets} - \text{Net PP&E}$$
    - Replace $SGAI$ proxy ($\text{Gross Profit} - \text{EBIT}$) with actual SG&A filings where available.
    - If required historical lines are absent, return `data_available: false` and `beneish_score: None` rather than computing an estimated score.
- [ ] **Task 1.4: Eliminate Altman Z / Z'' Heuristic Proxies (`distress_engine.py`)**
  - Refactor `backend/app/services/distress_engine.py`:
    - Compute genuine Working Capital: $\text{Current Assets} - \text{Current Liabilities}$.
    - Compute genuine $X_2$: $\text{Retained Earnings} / \text{Total Assets}$.
    - Only fall back to Z'' (4-factor non-manufacturing) when PP&E or inventory is inapplicable, logging data quality flags clearly.
- [ ] **Task 1.5: Genuine Shareholder Yield & SBC Dilution (`capital_return_engine.py`)**
  - Refactor `backend/app/services/capital_return_engine.py`:
    - Eliminate hardcoded sector SBC assumptions (e.g., 4% Tech, 2% Other, 5.6% AMD).
    - Extract actual `stock_based_compensation` from cash flow filings.
    - Calculate Net Buyback Yield: $\max\left(0, \frac{\text{Cash Repurchases} - \text{Actual SBC}}{\text{Market Cap}} \times 100\right)$.
    - Calculate True Shareholder Yield: $\text{Dividend Yield} + \text{Net Buyback Yield}$.
- [ ] **Task 1.6: Native AAOIFI Interest Income Calculation (`halal.py`)**
  - Refactor `backend/app/services/halal.py`:
    - Remove hardcoded `overall_unknown = True`.
    - Compute Impure Income Ratio: $\text{Interest Income} / \text{Total Revenue}$.
    - If $\le 5.0\%$, debt $< 30\%$, cash $< 30\%$, and business activity passes $\implies$ mark company as `halal_candidate: true`.
    - Preserve honest `unknown` status if interest income is missing from filings.
- [ ] **Task 1.7: Unit Testing & Integrity Verification**
  - Write dedicated pytest suites for all upgraded engines (`test_beneish_v2.py`, `test_altman_v2.py`, `test_shareholder_yield_v2.py`, `test_halal_v2.py`).
  - Run full backend test suite (`python -m pytest -q`).
  - **Exit Check:** All tests pass, 0 heuristic proxies remain, seed workbook checksum is identical.

---

## PHASE 2: CORE ANALYTICAL ENGINES & DECISION LOGIC
**Goal:** Implement the complete 7-pillar literature formulas, business archetype classifier, Buffett Owner Earnings, and the automated "60-Second Safety Verdict" synthesis algorithm.

### Tasks:
- [ ] **Task 2.1: Peter Lynch 6 Archetypes & PEG Classifier (`archetype_engine.py`)**
  - Create `backend/app/services/archetype_engine.py`:
    - *Fast Growers:* Revenue & EPS CAGR $\ge 20\%$, healthy balance sheet.
    - *Stalwarts:* Revenue CAGR 8%–19%, moderate dividend yield, low cyclicality.
    - *Slow Growers:* Revenue CAGR 1%–7%, dividend payout ratio $> 50\%$.
    - *Cyclicals:* Revenue/EBIT margin volatility $> 2.5\sigma$, concentrated in Energy, Materials, Semis, Autos.
    - *Turnarounds:* Negative EPS recovering to positive, high debt/EBITDA, active deleveraging.
    - *Asset Plays:* Market Cap $\le \text{Net-Net Working Capital (NNWC)}$ or book equity with depressed multiples.
  - Implement PEG Ratio: $\text{PEG} = \frac{P/E}{\text{CAGR}_{3Y-5Y}}$. Flag $\le 1.0$ as Attractive, $> 2.0$ as Stretched.
- [ ] **Task 2.2: Warren Buffett Owner Earnings Engine (`owner_earnings.py`)**
  - Create `backend/app/services/owner_earnings.py`:
    - Estimate Maintenance CapEx vs. Growth CapEx using Bruce Greenwald's methodology:
      $$\text{Growth CapEx} = \frac{\Delta \text{Revenue}}{\text{Sales/PP&E Ratio}}, \quad \text{Maintenance CapEx} = \text{Total CapEx} - \text{Growth CapEx}$$
    - Calculate Owner Earnings: $\text{Net Income} + \text{D&A} - \text{Maintenance CapEx} \pm \Delta \text{Working Capital}$.
    - Output Owner Earnings Yield: $\text{Owner Earnings} / \text{Market Cap}$.
- [ ] **Task 2.3: Pat Dorsey 4-Moat Heuristic Model (`moat_engine.py`)**
  - Create `backend/app/services/moat_engine.py`:
    - Evaluate 4 structural economic moat sources:
      1. *High Switching Costs:* Sustained Gross Margin $> 60\%$ with low customer churn.
      2. *Network Effects:* Exponential revenue growth with declining Customer Acquisition Cost (CAC).
      3. *Cost Advantage:* Lowest SG&A-to-gross-profit ratio in industry peer group.
      4. *Intangible Assets:* Pricing power (ability to raise gross margins over 5 years).
    - Classify Moat Rating: `Wide`, `Narrow`, or `None`.
- [ ] **Task 2.4: Enhanced Penman Reformulation & Buyback Distortion (`penman_engine.py`)**
  - Refine `backend/app/services/penman_engine.py`:
    - Extract Net Operating Assets ($NOA = \text{Operating Assets} - \text{Operating Liabilities}$).
    - Extract Net Financial Obligations ($NFO = \text{Total Debt} + \text{Preferred Stock} - \text{Cash}$).
    - Calculate $RNOA = \text{NOPAT} / NOA$, $FLEV = NFO / \text{Equity}$, and $NBC = \text{Net Interest} / NFO$.
    - Add Buyback Distortion Alert: When headline $\text{ROIC} > 30\%$ but $\text{FLEV} > 2.0$ and $\text{RNOA} < 15\%$, flag: *"High ROIC is artificially inflated by debt-funded buybacks."*
- [ ] **Task 2.5: Reverse DCF Brent Solver Refinement (`valuation_engine.py`)**
  - Enhance Reverse DCF in `backend/app/services/valuation_engine.py`:
    - Solve for Implied Free Cash Flow Growth Rate ($g_{\text{implied}}$) over a 10-year horizon.
    - Compute Expectations Gap: $\Delta g = g_{\text{implied}} - \text{CAGR}_{5Y\text{ FCF}}$.
    - Benchmark against Burton Malkiel & J.L. Collins 8.0% nominal index opportunity cost hurdle.
- [ ] **Task 2.6: The Automated 60-Second Safety Verdict Algorithm**
  - Build deterministic verdict synthesizer in `backend/app/services/verdict_engine.py`:
    - Synthesizes Moat, Solvency (Altman Z), Earnings Quality (Beneish M, Sloan), and Valuation Hurdle into 5 mutually exclusive verdict tags:
      1. `COMPOUNDER AT FAIR VALUE`: Wide/Narrow Moat + Altman Z Safe + Reverse DCF Gap $\le +2\%$.
      2. `UNDERVALUED BARGAIN`: Altman Z Safe + Beneish Clean + Current Price $\le$ Graham Floor / DCF at $>25\%$ margin of safety.
      3. `OVERVALUED QUALITY`: Wide Moat + Pristine Balance Sheet, BUT Reverse DCF Gap $> +6\%$ (Priced for perfection).
      4. `CYCLICAL PEAK: CAUTION`: Cyclical Archetype + Trough P/E multiple at peak earnings + decelerating CFO.
      5. `AVOID: VALUE TRAP / DISTRESS`: Altman Z Distress Zone OR Beneish M-Score flagged OR severe CFO-NI decoupling.
- [ ] **Task 2.7: Backend Dossier Endpoint Expansion**
  - Update `GET /api/v1/companies/{id}/dossier` payload to return the complete `decision_verdict`, `archetype`, `moat_rating`, and `expectations_gap` objects.
  - **Exit Check:** Backend tests verify 100% deterministic verdicts across diverse test tickers (e.g. AAPL, RY, TSLA, GME).

---

## PHASE 3: FORENSIC ACCOUNTING & CAPITAL ALLOCATION SUITE
**Goal:** Implement deep forensic accounting checks, cash flow bridges, organic float shrink tracking, and specialized financial institution analysis.

### Tasks:
- [ ] **Task 3.1: Richard Sloan Accrual Anomaly Engine (`sloan_engine.py`)**
  - Calculate Balance Sheet and Cash Flow Accruals:
    $$\text{Accrual Ratio} = \frac{\text{Net Income} - \text{CFO}}{\text{Average Total Assets}}$$
  - Flag companies with Accrual Ratio $> 10\%$ as *"Low Quality / Paper Earnings"* and $< -10\%$ as *"High Quality / Cash Rich"*.
- [ ] **Task 3.2: Martin Fridson Reality Spread & Fixed-Charge Coverage (`practitioner_engine.py`)**
  - Compute EBITDA Reality Spread: $\text{Spread} = \text{EBITDA} - \text{CFO}$.
  - Compute Fixed-Charge Coverage Ratio: $(\text{EBIT} + \text{Lease Expense}) / (\text{Interest Expense} + \text{Lease Expense})$.
  - Generate automated cash drain alert when EBITDA grows while CFO contracts over multiple fiscal years.
- [ ] **Task 3.3: Master Forensic Red Flag Synthesizer (`forensic_engine.py`)**
  - Synthesize Howard Schilit Shenanigans (CFO-NI decoupling, revenue growth outstripping receivables growth, inventory build-up), Beneish manipulation flag, and Sloan accrual warnings into an overall Forensic Health Score (0–100).
- [ ] **Task 3.4: Organic Float Shrink & Shareholder Capital Return Engine (`capital_return_engine.py`)**
  - Track 3-year and 5-year compound net share count reduction (Float Shrink).
  - Compare gross cash spent on buybacks against real dilution from Stock-Based Compensation.
  - Compute Dividend Safety Rating based on FCF payout ratio, cash buffer, and debt maturities.
- [ ] **Task 3.5: Specialized Banking & Insurance Model (`bank_engine.py`)**
  - Implement financial institution metrics:
    - Banks: Efficiency Ratio, Return on Average Assets (ROAA), CET1 Capital Ratio, Net Interest Margin (NIM).
    - Strictly enforce rule: Corporate debt, FCF, and Gross Profit remain NULL/blank for financials.
  - **Exit Check:** Pytest suite verifies forensic detection on historical accounting scandals and bank safety models.

---

## PHASE 4: ADVANCED SCREENING, ETF COHORTS & PEER BENCHMARKING
**Goal:** Build multi-metric screening endpoints with certified investment literature presets, ETF cohort universe tagging, and currency-isolated sector benchmarking.

### Tasks:
- [ ] **Task 4.1: Literature-Grounding Screener Presets (`screen_engine.py`)**
  - Enhance `/api/v1/screen` endpoint with pre-built, certified investment filters:
    1. *Greenblatt Magic Formula:* Top 10% Return on Capital + Top 10% Earnings Yield.
    2. *Graham Net-Net Bargains:* Market Cap $\le$ Net Current Asset Value ($NCAV$) or $NNWC$.
    3. *Peter Lynch Growth Compounders:* PEG $\le 1.0$ + ROIC $\ge 15\%$ + Debt/Equity $\le 0.5$.
    4. *Piotroski High-Quality Turnarounds:* F-Score $\ge 8$ + Altman Z safe zone.
    5. *True Shareholder Yield Leaders:* True Shareholder Yield $\ge 6.0\%$ net of SBC dilution.
    6. *AAOIFI Halal Candidates:* Activity screen pass + Debt/Mcap $< 30\%$ + Cash/Mcap $< 30\%$ + Impure Income $< 5\%$.
- [ ] **Task 4.2: ETF Cohort Segmentation & Universe Tagging (`etf_resolver.py`)**
  - Maintain and expand cohort tags across the 720 universe:
    - `S&P 500` (US Large Cap Core)
    - `S&P/TSX Composite` (Canadian Core)
    - `SPUS` (S&P 500 Shariah Halal ETF constituents)
    - `QQQ` (Nasdaq 100 Innovation)
    - `VONV` (Russell 1000 Value)
  - Allow users to filter or benchmark any stock against its specific ETF peer cohort.
- [ ] **Task 4.3: Peer Benchmarking & Percentile Distribution Matrices (`peer_engine.py`)**
  - Compute sector and custom-industry percentile ranks (1–100) for Quality, Value, Growth, and Risk.
  - Strictly enforce Rule #1: Money values are never mixed across USD and CAD; percentile comparisons use unitless ratios only.
  - **Exit Check:** Screener queries execute in $<100\text{ ms}$ over the entire 720 universe.

---

## PHASE 5: DOSSIER API SYNTHESIS, ASYNC INGESTION & SYSTEM HARDENING
**Goal:** Unify all engines into an ultra-fast, robust API surface, harden the asynchronous background ingest queue, and verify complete system stability.

### Tasks:
- [ ] **Task 5.1: Unified Decision & Dossier API Payloads**
  - Optimize `GET /api/v1/companies/{id}/dossier` to deliver the comprehensive 3-tier data model:
    - Level 1 payload: Identity, Verdict Badge, 3 Traffic Lights, Reverse DCF Rule, Decision Bullets.
    - Level 2 payload: 4-Pillar Radar, Lynch Archetype, True Shareholder Yield, Cash Flow Waterfall.
    - Level 3 payload: Beneish Matrix, Penman Table, Altman Breakdown, 10-Year Statement History.
- [ ] **Task 5.2: Asynchronous Multi-Year SEC EDGAR Ingest & Worker Thread (`JobWorker`)**
  - Harden the background queue in `backend/app/services/jobs.py` to ingest 5–10 years of SEC 10-K filings for US companies with SEC rate limiting (10 req/sec limit).
  - Ensure background ingestion never locks SQLite or crashes the main server.
- [ ] **Task 5.3: SQLite Performance Optimization & Query Indexing**
  - Ensure WAL mode is active (`PRAGMA journal_mode=WAL;`).
  - Create database indices on `(company_id, fiscal_year)`, `(ticker, exchange)`, and scoring columns to guarantee sub-20ms query responses.
- [ ] **Task 5.4: Comprehensive Test Suite & Integrity Audit**
  - Run full backend test suite (`pytest`) verifying:
    - Zero crashes across all 720 companies.
    - Rule #1: No CAD/USD money blending.
    - Rule #2: Seed workbook immutability.
    - Rule #3: Zero invented numbers (honest NULLs).
    - Rule #6: Score weights locked (0.30/0.25/0.25/0.20).
    - Rule #8: Banks/insurers debt and FCF preserved blank.
  - **Exit Check:** 100% test pass rate, zero regressions, phase completion report generated.

---

## EXECUTION ROADMAP SUMMARY

| Phase | Functional Focus | Key Deliverable |
|---|---|---|
| **Phase 1** | Foundation & Data Integrity | Schema expansion + genuine 10-K filings (Eliminates all heuristic proxies) |
| **Phase 2** | Core Analytical Engines & Verdict | Lynch archetypes, Owner Earnings, Dorsey moats, Reverse DCF & Safety Verdict |
| **Phase 3** | Forensic Accounting & Capital Return | Sloan accruals, Fridson spread, Schilit flags, True Shareholder Yield & Bank model |
| **Phase 4** | Advanced Screening & Benchmarking | Literature screener presets (Magic Formula, Net-Nets, Halal) & ETF cohorts |
| **Phase 5** | Dossier API Synthesis & Hardening | Unified 3-tier API payloads, async EDGAR worker, sub-20ms SQLite performance |

### Next Step:
With the functional roadmap approved and UI/UX design specifications securely preserved in `docs/UI_UX_SPECIFICATION.md`, we are ready to commence **Phase 1: Foundation & Data Integrity Hardening** on your next command.
