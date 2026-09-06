# 100 EQUITY RESEARCH USER STORIES & MARKET NEEDS SPECIFICATION
## Comprehensive Requirements Taxonomy for Institutional & Independent Equity Analysis
**Platform:** Local Institutional Equity Analysis Terminal  
**Coverage Universe:** S&P 500, S&P/TSX Composite, Global ADRs, and On-Demand Ingested Universe  
**Author:** Sarah (Technical Product Owner & Requirements Specialist)  
**Status:** Certified Ground Truth & Feature Alignment Mapping  

---

## Executive Summary & Market Research

When investors and financial analysts analyze equities to pick financially sound, resilient companies, their decision workflows span distinct mental models and literature-grounded disciplines:
1. **Balance Sheet Fortresses & Solvency Assurance:** Avoiding corporate distress, bankruptcy, and liquidity cliffs (Altman Z, Working Capital, Debt Walls).
2. **True Cash Generation & Owner Earnings:** Peeling back GAAP accounting illusions to evaluate Bruce Greenwald maintenance capex vs. growth capex and Warren Buffett owner earnings.
3. **Forensic Accounting & Deception Defense:** Detecting aggressive revenue recognition, accrual stuffing, channel stuffing, and manipulation (Beneish M-Score, Richard Sloan accrual anomalies, Howard Schilit shenanigans).
4. **Economic Moats & Pricing Power:** Identifying durable competitive advantages (Pat Dorsey 4-moat heuristic: switching costs, intangible brand power, cost leadership, network effects).
5. **Capital Allocation & Anti-Dilution:** Tracking organic float shrink, dividend durability, and penalizing excessive executive stock-based compensation (SBC dilution).
6. **Cross-Border Purity & Currency Isolation:** Ensuring strict non-contamination of currencies between USD, CAD, and foreign reporting currencies without bogus cross-rates.
7. **Ethical & Halal Ratio Compliance:** Screening against AAOIFI financial criteria without exclusionary filtering.
8. **Expectation Investing & Reverse DCF:** Calculating the market-implied growth rate and expectations gap versus historical reality.

Below are **100 concrete, testable user stories** representing the base-case needs across 10 market investor categories, mapped directly against our application's feature set.

---

## Part 1: The 100 Base Case User Stories

### Category 1: Deep Value & Benjamin Graham Disciples (Stories 1–10)

#### Story 1: Graham Net Current Asset Value (NCAV) Margin of Safety
- **As a** deep-value investor seeking extreme downside protection,
- **I want to** filter stocks trading below their Net Current Asset Value ($\text{Current Assets} - \text{Total Liabilities}$),
- **So that** I purchase businesses where liquidation value exceeds the entire market capitalization.
- **Acceptance Criteria:**
  - [ ] Screener provides a "Graham Net-Net Bargains" preset.
  - [ ] Displays $NCAV$ per share alongside current stock price.
  - [ ] Flags negative NCAV clearly without math errors.
- **Feature Alignment:** `/api/v1/screen?preset=graham_net_net_bargains` & Dossier Valuation Tab.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 2: Net-Net Working Capital (NNWC) Ultra-Conservative Liquidation Floor
- **As an** asset-play specialist,
- **I want to** evaluate Net-Net Working Capital with haircuts ($1.0 \times \text{Cash} + 0.75 \times \text{Receivables} + 0.50 \times \text{Inventory} - \text{Total Liabilities}$),
- **So that** I have a haircut-adjusted margin of safety for illiquid inventories and bad receivables.
- **Acceptance Criteria:**
  - [ ] NNWC computed from 10-K balance sheet line items.
  - [ ] Haircut factors documented in interactive glossary.
- **Feature Alignment:** `valuation_engine.py` & Level 3 Dossier Intrinsic Floors.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 3: Graham Number Intrinsic Valuation
- **As a** classical defensive investor,
- **I want to** calculate the Graham Number ($\sqrt{22.5 \times \text{EPS} \times \text{Book Value per Share}}$),
- **So that** I instantly know if a company violates the combined $P/E \times P/B \le 22.5$ rule.
- **Acceptance Criteria:**
  - [ ] Graham Number calculated when EPS > 0 and BVPS > 0.
  - [ ] If EPS or BVPS is negative, displays honest "N/A (Loss/Deficit)".
- **Feature Alignment:** Dossier Level 2 Valuation Tiles.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 4: Price-to-Book Versus Tangible Book Value
- **As an** asset-intensive industry researcher,
- **I want to** strip out goodwill and intangibles to compare Price-to-Tangible-Book,
- **So that** I do not rely on inflated acquisition accounting premiums.
- **Acceptance Criteria:**
  - [ ] Tangible Book Value calculated as $\text{Total Equity} - \text{Goodwill/Intangibles}$.
  - [ ] Displayed on common-size balance sheet table.
- **Feature Alignment:** `CommonSizeTable.tsx` & Snapshot tiles.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 5: EV/EBITDA Multiple Valuation Percentiles
- **As a** private-equity style value acquirer,
- **I want to** view Enterprise Value to EBITDA percentiles within the company's same-currency peer group,
- **So that** I avoid companies with cheap P/E ratios masking mountain-sized debt burdens.
- **Acceptance Criteria:**
  - [ ] EV calculated as $\text{Market Cap} + \text{Total Debt} - \text{Cash/ST Investments}$.
  - [ ] Percentile rank (1–100th) calculated strictly against same-currency industry peers.
- **Feature Alignment:** `PercentileMatrix.tsx` & `/api/v1/benchmarks`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 6: Normalized Mid-Cycle P/E Ratio
- **As a** cyclicals investor,
- **I want to** compute P/E against 5-year average net income,
- **So that** I do not mistake cyclical peak earnings for permanent undervaluation.
- **Acceptance Criteria:**
  - [ ] 5-year statement history calculates average net income.
  - [ ] Archetype classifier flags cyclicals trading at low headline P/E.
- **Feature Alignment:** `archetype_engine.py` & History Table.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 7: Greenblatt Magic Formula Quality & Yield Ranking
- **As a** quantitative value allocator,
- **I want to** rank the entire universe by Return on Capital ($\text{EBIT} / (\text{Net Working Capital} + \text{Net Fixed Assets})$) plus Earnings Yield ($\text{EBIT} / \text{EV}$),
- **So that** I buy above-average companies at below-average prices systematically.
- **Acceptance Criteria:**
  - [ ] Magic Formula preset joins ROC rank and Earnings Yield rank.
  - [ ] Excludes financial institutions where EBIT/NWC are non-applicable.
- **Feature Alignment:** `/api/v1/screen?preset=greenblatt_magic_formula`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 8: Free Cash Flow Yield Hurdle
- **As an** absolute-return investor,
- **I want to** screen for companies offering FCF Yield ($\text{FCF} / \text{Market Cap}$) greater than the 10-year Treasury yield,
- **So that** my equity risk premium is positive in real cash terms.
- **Acceptance Criteria:**
  - [ ] FCF Yield filter slider in Screener (0% to 30%).
  - [ ] Tooltip showing TTM FCF vs Market Cap.
- **Feature Alignment:** `Screener.tsx` slider & `screener_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 9: Debt-Adjusted Price-to-Earnings (EV/FCF)
- **As a** balance-sheet conscious value picker,
- **I want to** compare EV/FCF across industry rivals,
- **So that** cash balances and debt leverage are factored into the acquisition multiple.
- **Acceptance Criteria:**
  - [ ] Both FCF Margin and EV/EBITDA visible side-by-side on Compare screen.
  - [ ] Unitless comparison allows cross-currency evaluation.
- **Feature Alignment:** `Compare.tsx` & `types.ts`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 10: Cash-Rich Negative Enterprise Value Screener
- **As an** activist micro-cap investor,
- **I want to** find companies whose cash and short-term investments exceed their market cap plus debt,
- **So that** I identify negative Enterprise Value situations.
- **Acceptance Criteria:**
  - [ ] Screener flags $\text{EV} < 0$.
  - [ ] Clearly labels "Net Cash > Market Cap".
- **Feature Alignment:** `Screener.tsx` & `DerivedMetric`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 2: Warren Buffett & Charlie Munger Quality Compounders (Stories 11–20)

#### Story 11: True Warren Buffett Owner Earnings Computation
- **As a** business buyer following Berkshire Hathaway methodology,
- **I want to** see Bruce Greenwald's maintenance capex separated from growth capex to calculate Owner Earnings,
- **So that** I know how much cash the owner can withdraw without impairing operations.
- **Acceptance Criteria:**
  - [ ] $\text{Growth CapEx} = \frac{\Delta \text{Revenue}}{\text{Sales/PP&E Ratio}}$.
  - [ ] $\text{Maintenance CapEx} = \text{Total CapEx} - \text{Growth CapEx}$.
  - [ ] Displays Owner Earnings Yield ($\text{Owner Earnings} / \text{Market Cap}$).
- **Feature Alignment:** `backend/app/services/owner_earnings.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 12: Durable High Return on Invested Capital (ROIC)
- **As a** compounder investor,
- **I want to** verify that ROIC has exceeded 15% consistently across 5 fiscal years,
- **So that** I only allocate to businesses with sustainable competitive moats.
- **Acceptance Criteria:**
  - [ ] Multi-year ROIC displayed in 10-year historical statements.
  - [ ] Quality pillar incorporates ROIC consistency.
- **Feature Alignment:** `models.py:DerivedMetric` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 13: Pat Dorsey 4-Moats Heuristic Classifier
- **As an** economic moat analyst,
- **I want to** classify companies into Wide Moat, Narrow Moat, or None based on switching costs, network effects, cost advantage, and intangible pricing power,
- **So that** I evaluate structural business defensibility.
- **Acceptance Criteria:**
  - [ ] `moat_engine.py` generates deterministic rating: `Wide`, `Narrow`, or `None`.
  - [ ] Dossier Overview displays Moat Badge with bullet rationale.
- **Feature Alignment:** `backend/app/services/moat_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 14: Pricing Power via Gross Margin Stability
- **As an** inflation-conscious quality investor,
- **I want to** examine 5-year gross margin expansion or contraction trends,
- **So that** I know if a firm can pass cost inflation onto customers without sacrificing volume.
- **Acceptance Criteria:**
  - [ ] Multi-year gross margin sparklines and common-size statement drift alerts (`GROSS_MARGIN_COMPRESSION`).
- **Feature Alignment:** `CommonSizeTable.tsx` & `alerts.ts`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 15: Cash Conversion Ratio (CFO / Operating Income)
- **As an** earnings quality researcher,
- **I want to** verify Cash Conversion Ratio ($\text{CFO} / \text{EBIT} \ge 1.0$),
- **So that** I confirm reported accounting profits convert into real cold cash.
- **Acceptance Criteria:**
  - [ ] Computed across all historical years.
  - [ ] Screener slider allows filtering on Max/Min cash conversion.
- **Feature Alignment:** `DerivedMetric.cash_conversion_ratio` & `Screener.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 16: Penman Operating Spread ($RNOA - FLEV \times NBC$)
- **As an** advanced fundamental accounting researcher,
- **I want to** decompose headline ROE into Operating Return on Net Operating Assets ($RNOA$) and Financing Leverage ($FLEV$),
- **So that** I verify whether high profitability comes from operations or financial leverage.
- **Acceptance Criteria:**
  - [ ] Displays $NOA, NFO, RNOA, FLEV, NBC,$ and operational spread.
  - [ ] Excludes banks/insurers where operating vs financing split is non-applicable.
- **Feature Alignment:** `penman_engine.py` & Dossier Forensics Tab.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 17: Debt-Funded Buyback Distortion Alert
- **As an** investigative analyst,
- **I want an** alert when headline ROIC is artificially inflated by debt-funded buybacks destroying equity,
- **So that** I am not misled by high financial engineering returns.
- **Acceptance Criteria:**
  - [ ] Flags: "High ROIC is artificially inflated by debt-funded buybacks" when $FLEV > 2.0$ and headline ROIC diverges from $RNOA$.
- **Feature Alignment:** `penman_engine.py` & Dossier Forensics Tab.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 18: Consistent Free Cash Flow Compounders
- **As a** long-term retirement allocator,
- **I want to** verify positive Free Cash Flow in every single fiscal year for at least 5 consecutive years,
- **So that** I eliminate firms with periodic cash flow crises.
- **Acceptance Criteria:**
  - [ ] Statement history flags negative FCF fiscal years.
  - [ ] Quality pillar penalizes volatile cash generation.
- **Feature Alignment:** `StatementHistory` & `Score.quality`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 19: Negative Working Capital Float Beneficiaries
- **As an** admirer of Costco and Dell capital structures,
- **I want to** identify companies operating with negative working capital,
- **So that** I find businesses funded for free by suppliers and customers.
- **Acceptance Criteria:**
  - [ ] Working Capital displayed on balance sheet.
  - [ ] Working Capital delta tracked in cash flow bridge.
- **Feature Alignment:** `FinancialStatement` & `CashFlowBridge.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 20: Pristine Solvency & Negative Net Debt
- **As a** fortress balance sheet seeker,
- **I want to** find companies with Net Debt $\le 0$ ($\text{Cash} \ge \text{Total Debt}$),
- **So that** bankruptcy risk is zero even in prolonged recessions.
- **Acceptance Criteria:**
  - [ ] Net Debt calculated as $\text{Total Debt} - \text{Cash/ST Investments}$.
  - [ ] Net Debt tile displays green "Net Cash" status.
- **Feature Alignment:** `SnapshotOut.netdebt_calc` & Dossier Overview.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 3: Peter Lynch Growth & Archetype Classifiers (Stories 21–30)

#### Story 21: Automated Peter Lynch 6-Archetype Classification
- **As a** Peter Lynch growth investor,
- **I want the** app to automatically classify each stock into Fast Grower, Stalwart, Slow Grower, Cyclical, Turnaround, or Asset Play,
- **So that** I judge the stock using the valuation rules appropriate for its business lifecycle.
- **Acceptance Criteria:**
  - [ ] `archetype_engine.py` classifies stocks using multi-year CAGR, margin volatility, and balance sheet status.
  - [ ] Displayed on Dossier Overview with tailored investment playbook.
- **Feature Alignment:** `backend/app/services/archetype_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 22: Multi-Year PEG Ratio Calculation
- **As a** growth-at-a-reasonable-price (GARP) investor,
- **I want to** compute the PEG Ratio using historical 3-5 year EPS and revenue CAGR,
- **So that** I identify high-growth companies trading at attractive valuations ($\text{PEG} \le 1.0$).
- **Acceptance Criteria:**
  - [ ] $\text{PEG} = \frac{P/E}{\text{CAGR}_{3Y-5Y}}$.
  - [ ] Color-coded rating: Attractive ($\le 1.0$), Fair (1.0–2.0), Stretched ($> 2.0$).
- **Feature Alignment:** `archetype_engine.py` & Screener.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 23: Fast Grower High-Quality Screener
- **As a** tech growth investor,
- **I want to** screen for companies with Revenue & EPS CAGR $\ge 20\%$ with Altman Z in the safe zone,
- **So that** I find hyper-growth businesses that are not burning up their balance sheets.
- **Acceptance Criteria:**
  - [ ] Screener preset: `peter_lynch_growth_compounders`.
  - [ ] Joins CAGR $\ge 15\%$, $\text{ROIC} \ge 15\%$, and $\text{Debt/Equity} \le 0.5$.
- **Feature Alignment:** `/api/v1/screen?preset=peter_lynch_growth_compounders`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 24: Turnaround Candidate Discovery
- **As a** contrarian value investor,
- **I want to** identify turnarounds where operating income is recovering from negative to positive with active deleveraging,
- **So that** I catch multi-bagger recovery opportunities early.
- **Acceptance Criteria:**
  - [ ] Piotroski F-Score $\ge 8$ turnaround screener preset available.
  - [ ] Net Debt reduction and margin inflection highlighted.
- **Feature Alignment:** `/api/v1/screen?preset=piotroski_high_quality_turnarounds`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 25: Stalwart Blue-Chip Steady Compounder Identification
- **As a** conservative capital compounder,
- **I want to** spot Stalwarts (Revenue CAGR 8–18%, low cyclicality, moderate dividend),
- **So that** I find recession-resistant core holdings.
- **Acceptance Criteria:**
  - [ ] Archetype classifies stalwarts based on low revenue standard deviation.
  - [ ] Highlights defensive dividend coverage.
- **Feature Alignment:** `archetype_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 26: Cyclical Trough P/E Value Trap Avoidance
- **As a** cyclical analyst,
- **I want an** alert when a cyclical stock looks cheap on trailing P/E at peak earnings,
- **So that** I avoid buying commodity or semiconductor names right before a brutal downcycle.
- **Acceptance Criteria:**
  - [ ] Safety verdict outputs `CYCLICAL PEAK: CAUTION` when margin volatility is high and revenue growth is decelerating.
- **Feature Alignment:** `verdict_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 27: Outlier-Sanitized Multi-Year CAGR
- **As a** quant fundamentalist,
- **I want** anomalous historical spikes (e.g., pandemic recovery 5,000% jump) excluded or winsorized in growth CAGRs,
- **So that** long-term growth scores reflect realistic sustainable rates.
- **Acceptance Criteria:**
  - [ ] Suspect years flagged in `data_quality_flags`.
  - [ ] Excluded from multi-year compound calculations.
- **Feature Alignment:** `fundamentals.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 28: FCF Growth Outpacing Revenue Growth (Operating Leverage)
- **As a** scaling software investor,
- **I want to** verify that 5-year FCF CAGR exceeds 5-year Revenue CAGR,
- **So that** I confirm the business possesses positive structural operating leverage.
- **Acceptance Criteria:**
  - [ ] Historical statement table computes YoY and 5Y CAGR for both metrics.
- **Feature Alignment:** `FinancialStatement` history & `DerivedMetric`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 29: Sustainable Reinvestment Rate Analysis
- **As a** compounder specialist,
- **I want to** calculate Reinvestment Rate ($\text{CapEx} - \text{D&A} + \Delta \text{NWC}) / \text{NOPAT}$,
- **So that** I determine how much capital must be reinvested to generate reported growth.
- **Acceptance Criteria:**
  - [ ] Cash flow waterfall breaks down CapEx, Working Capital changes, and free cash.
- **Feature Alignment:** `CashFlowBridge.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 30: Slow Grower High Dividend Sustainability Check
- **As an** income seeker,
- **I want to** verify that Slow Growers (1–7% growth) maintain payout ratios $< 70\%$ of real FCF,
- **So that** I avoid utility and consumer companies facing dividend cuts.
- **Acceptance Criteria:**
  - [ ] FCF Dividend Payout Ratio displayed on Capital Allocation tab.
- **Feature Alignment:** `CapitalReturnCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 4: Forensic Accounting & Red Flag Deception Defense (Stories 31–40)

#### Story 31: Full 8-Variable Beneish M-Score Calculation
- **As a** forensic accountant,
- **I want to** calculate the genuine 8-variable Beneish M-Score ($DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA$) from 10-K filings,
- **So that** I detect earnings manipulation before catastrophic restatements occur.
- **Acceptance Criteria:**
  - [ ] Evaluates $M > -1.78$ as Manipulation Risk.
  - [ ] Uses real accounts receivable, PP&E, current assets, and depreciation.
  - [ ] Missing historical data returns honest `data_available: false` rather than guessing.
- **Feature Alignment:** `backend/app/services/beneish_engine.py` & `BeneishCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 32: Richard Sloan Accrual Anomaly Screener
- **As an** institutional risk manager,
- **I want to** compute Sloan's Accrual Ratio ($(\text{Net Income} - \text{CFO}) / \text{Average Total Assets}$),
- **So that** I avoid companies with high paper accruals and poor cash conversion.
- **Acceptance Criteria:**
  - [ ] Accrual ratio $> 10\%$ flagged as "Low Quality / Paper Earnings".
  - [ ] Accrual ratio $< -10\%$ highlighted as "High Quality / Cash Rich".
  - [ ] Filterable via Screener slider.
- **Feature Alignment:** `backend/app/services/sloan_engine.py` & `Screener.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 33: Howard Schilit CFO-to-Net-Income Decoupling Alert
- **As an** equity auditor,
- **I want an** alert when Net Income is rising while Operating Cash Flow is collapsing over 2+ consecutive years,
- **So that** I catch classic Shenanigan #2 (recording premature or fictitious revenue).
- **Acceptance Criteria:**
  - [ ] Master Forensic Red Flag Synthesizer checks CFO vs Net Income trajectory.
  - [ ] Displays alert badge in Forensics tab.
- **Feature Alignment:** `forensic_engine.py` & `Forensics.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 34: Days Sales of Inventory (DSI) Spikes & Channel Stuffing
- **As an** inventory-intensive industry specialist,
- **I want to** track Days Sales in Inventory ($(\text{Inventory} / \text{COGS}) \times 365$),
- **So that** I catch obsolete inventory stockpiles and channel stuffing before massive write-downs.
- **Acceptance Criteria:**
  - [ ] 10-K `inventory` and `cogs` stored in `financial_snapshots`.
  - [ ] Significant DSI increases trigger forensic warning.
- **Feature Alignment:** `forensics.py` & `CommonSizeTable.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 35: Days Sales Outstanding (DSO) Revenue Quality Probe
- **As a** credit auditor,
- **I want to** monitor Days Sales Outstanding ($(\text{Accounts Receivable} / \text{Revenue}) \times 365$),
- **So that** I spot companies extending lenient credit terms to artificially inflate sales.
- **Acceptance Criteria:**
  - [ ] Beneish $DSRI$ evaluates receivables growth vs sales growth.
  - [ ] Warning triggers if receivables grow $> 1.3\times$ faster than sales.
- **Feature Alignment:** `beneish_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 36: Martin Fridson EBITDA Reality Spread ($\text{EBITDA} - \text{CFO}$)
- **As a** high-yield debt investor,
- **I want to** compute the Martin Fridson Reality Spread ($\text{EBITDA} - \text{CFO}$),
- **So that** I expose corporate EBITDA figures that fail to generate actual cash flow.
- **Acceptance Criteria:**
  - [ ] Displays EBITDA Reality Spread across multi-year history.
  - [ ] Flags persistent positive spreads as cash drains.
- **Feature Alignment:** `backend/app/services/practitioner_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 37: Asset Quality Index ($AQI$) Intangible Ballooning Test
- **As a** balance sheet auditor,
- **I want to** calculate Beneish $AQI$ ($[1 - (\text{Current Assets} + \text{Net PP&E}) / \text{Total Assets}]$ ratio),
- **So that** I catch companies capitalizing operating expenses into non-current assets.
- **Acceptance Criteria:**
  - [ ] Compares year $t$ non-current assets against year $t-1$.
  - [ ] Integrated into the Beneish 8-factor card.
- **Feature Alignment:** `beneish_engine.py` & `BeneishCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 38: Common-Size Expense Creep Alerts
- **As an** operational efficiency analyst,
- **I want an** alert when SG&A or COGS as a percentage of revenue increases by $> 300$ basis points over 3 years,
- **So that** I detect overhead bloat and margin degradation early.
- **Acceptance Criteria:**
  - [ ] CommonSizeTable computes percentage of revenue for all P&L lines.
  - [ ] Automated badges: `COST_CREEP`, `SG&A_BALLOONING`.
- **Feature Alignment:** `CommonSizeTable.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 39: Stock-Based Compensation (SBC) as % of Free Cash Flow
- **As a** tech investor,
- **I want to** inspect genuine SBC extracted from cash flow filings divided by reported Free Cash Flow,
- **So that** I know if "Free Cash Flow" is a mirage subsidized by immense shareholder dilution.
- **Acceptance Criteria:**
  - [ ] Genuine SBC line item from SEC 10-K filings.
  - [ ] Displays SBC Drag % on Capital Return card.
- **Feature Alignment:** `capital_return_engine.py` & `CapitalReturnCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 40: Master 0–100 Forensic Health Score (EQR)
- **As a** chief risk officer,
- **I want an** overall 0–100 Earnings Quality Rating (EQR) synthesizing Beneish, Sloan, Schilit, and debt spikes,
- **So that** I get an executive-level summary of accounting integrity in 5 seconds.
- **Acceptance Criteria:**
  - [ ] EQR computed deterministically from verified forensic tests.
  - [ ] Color-coded score: Green (80–100), Amber (50–79), Red (< 50).
- **Feature Alignment:** `forensic_engine.py` & Screener.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 5: Credit, Solvency & Distress Analysts (Stories 41–50)

#### Story 41: Altman Z-Score Manufacturing Formula
- **As a** credit analyst assessing manufacturing firms,
- **I want to** calculate Edward Altman's original 5-factor Z-Score ($1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 1.0 X_5$),
- **So that** I identify manufacturing companies with high 2-year bankruptcy risk.
- **Acceptance Criteria:**
  - [ ] Uses real Working Capital, Retained Earnings, EBIT, Market Cap, Total Liabilities, and Sales.
  - [ ] Displays segmented gauge with Safe ($Z > 2.99$), Grey ($1.81 \le Z \le 2.99$), and Distress ($Z < 1.81$).
- **Feature Alignment:** `backend/app/services/distress_engine.py` & `AltmanZGauge.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 42: Altman Z'' Non-Manufacturing / Service Model
- **As a** software and services analyst,
- **I want the** system to automatically employ the 4-factor Altman Z'' formula ($6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$),
- **So that** capital-light and service firms are not unfairly penalized by the absence of asset turnover.
- **Acceptance Criteria:**
  - [ ] Automatically selects Z'' for non-manufacturing GICS sectors.
  - [ ] Z'' thresholds: Safe ($Z'' > 2.6$), Grey ($1.1 \le Z'' \le 2.6$), Distress ($Z'' < 1.1$).
- **Feature Alignment:** `distress_engine.py` & `AltmanZGauge.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 43: Financial Institutions Exclusion from Distress Scoring
- **As a** banking compliance reviewer,
- **I want** banks and insurers explicitly excluded from Altman Z-Score and corporate debt gauges with a clear educational banner,
- **So that** deposit liabilities are never misclassified as corporate default risk.
- **Acceptance Criteria:**
  - [ ] Status: `financial_institution_excluded`.
  - [ ] Displays clear architectural banner: "Financial institutions excluded by design".
- **Feature Alignment:** `distress_engine.py` & `AltmanZGauge.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 44: Fixed-Charge Coverage Ratio Under Lease Obligations
- **As a** corporate bondholder,
- **I want to** evaluate Fixed-Charge Coverage ($(\text{EBIT} + \text{Lease Expense}) / (\text{Interest Expense} + \text{Lease Expense})$),
- **So that** I measure solvency including off-balance-sheet operating lease commitments.
- **Acceptance Criteria:**
  - [ ] Computed in practitioner engine.
  - [ ] Displays coverage multiple and stress thresholds.
- **Feature Alignment:** `practitioner_engine.py` & `PractitionerCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 45: Net Debt to EBITDA Refinancing Risk
- **As a** credit rating agency analyst,
- **I want to** calculate Net Debt / EBITDA across all portfolio holdings,
- **So that** I flag companies exceeding $3.5\times$ leverage before debt rating downgrades.
- **Acceptance Criteria:**
  - [ ] Filterable in screener and visible in Compare table.
  - [ ] Net cash companies display $\le 0$ clearly.
- **Feature Alignment:** `DerivedMetric.netdebt_calc` & `Screener.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 46: Liquidity Acid-Test / Quick Ratio
- **As a** short-term liquidity analyst,
- **I want to** compute the Quick Ratio ($(\text{Cash} + \text{Marketable Securities} + \text{Receivables}) / \text{Current Liabilities}$),
- **So that** I verify immediate debt obligations can be satisfied without fire-selling inventory.
- **Acceptance Criteria:**
  - [ ] Derived from 10-K balance sheet lines.
  - [ ] Displayed on balance sheet health tile.
- **Feature Alignment:** `financial_snapshots` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 47: Retained Earnings to Total Assets ($X_2$) Cumulative Profitability
- **As a** solvency auditor,
- **I want to** inspect the Retained Earnings / Total Assets ratio,
- **So that** I distinguish established, cumulatively profitable firms from young or serial-loss capital burning entities.
- **Acceptance Criteria:**
  - [ ] Retained earnings column stored in `financial_snapshots`.
  - [ ] Factor $X_2$ documented in Altman breakdown table.
- **Feature Alignment:** `distress_engine.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 48: Debt-to-Equity and Negative Book Equity Warning
- **As a** conservative allocator,
- **I want a** prominent warning when a company's Book Equity is negative due to accumulated losses or debt-fueled repurchases,
- **So that** I am alerted to technical balance-sheet insolvency.
- **Acceptance Criteria:**
  - [ ] Negative equity badge displayed on dossier header.
  - [ ] Debt/Equity marked as "Deficit" instead of a negative misleading ratio.
- **Feature Alignment:** `format.ts` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 49: Altman Distress Screener Preset
- **As a** distressed debt hunter,
- **I want to** screen specifically for companies in the Altman Z Distress Zone,
- **So that** I identify potential restructuring, debt-for-equity swap, or short targets.
- **Acceptance Criteria:**
  - [ ] Screener button toggles: ALL, Safe, Grey, Distress.
  - [ ] Instant filtering across the 760+ universe.
- **Feature Alignment:** `Screener.tsx` & `screener_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 50: 60-Second Safety Verdict "Avoid: Distress / Value Trap"
- **As a** retail investor,
- **I want the** system to issue a prominent red verdict tag `AVOID: VALUE TRAP / DISTRESS` whenever a stock enters the Altman Distress zone or fails forensic checks,
- **So that** I am protected from buying seemingly "cheap" companies headed for bankruptcy.
- **Acceptance Criteria:**
  - [ ] Verdict synthesized deterministically in `verdict_engine.py`.
  - [ ] Red banner with 3 concise warning bullets on Dossier Cockpit.
- **Feature Alignment:** `verdict_engine.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 6: Shareholder Yield, Buyback & Dividend Seekers (Stories 51–60)

#### Story 51: Multi-Year Diluted Share Count CAGR Tracking
- **As an** anti-dilution investor,
- **I want to** track 1-year and 3-year compound annual growth rates of diluted shares outstanding,
- **So that** I verify whether management is shrinking the share count or diluting existing owners.
- **Acceptance Criteria:**
  - [ ] Diluted share count CAGR (1Y/3Y) computed from historical filings.
  - [ ] Visual multi-year share count bar chart rendered in pure SVG.
- **Feature Alignment:** `capital_return_engine.py` & `CapitalReturnCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 52: Net Buyback Yield Net of Stock-Based Compensation
- **As a** capital allocation specialist,
- **I want to** calculate Net Buyback Yield as $(\text{Cash Spent on Repurchases} - \text{Stock-Based Compensation}) / \text{Market Cap}$,
- **So that** I ignore superficial buyback announcements that only neutralize executive option dilution.
- **Acceptance Criteria:**
  - [ ] Eliminates hardcoded sector SBC assumptions.
  - [ ] Subtracts real filing SBC from gross repurchase dollars.
- **Feature Alignment:** `capital_return_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 53: Total Shareholder Yield (TSY) Metric & Screener
- **As a** total-yield investor,
- **I want to** evaluate Total Shareholder Yield ($\text{Dividend Yield} + \text{Net Buyback Yield}$),
- **So that** I focus on the total cash returned directly to equity holders.
- **Acceptance Criteria:**
  - [ ] Screener preset: `true_shareholder_yield_leaders`.
  - [ ] Screener slider allows filtering for $\text{TSY} \ge 6.0\%$.
- **Feature Alignment:** `/api/v1/screen?preset=true_shareholder_yield_leaders`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 54: Accelerated Buyback Versus Shareholder Dilution Badges
- **As a** portfolio reviewer,
- **I want** clear visual badges: `ACCELERATED_BUYBACKS` (share count shrinking $> 2\%$ p.a.) or `SHAREHOLDER_DILUTION` (share count growing $> 2\%$ p.a.),
- **So that** I identify management alignment at a single glance.
- **Acceptance Criteria:**
  - [ ] Dynamic badge on Capital Allocation card based on 3Y share CAGR.
- **Feature Alignment:** `CapitalReturnCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 55: Dividend Coverage by Real Free Cash Flow
- **As an** income retiree,
- **I want to** inspect Dividend Payout Ratio based on Free Cash Flow ($\text{Dividends Paid} / \text{FCF}$) rather than GAAP Net Income,
- **So that** I know if dividends are paid from real cash or funded via debt borrowing.
- **Acceptance Criteria:**
  - [ ] FCF payout ratio calculated in Capital Allocation tab.
  - [ ] Flags payout ratios $> 85\%$ as risky.
- **Feature Alignment:** `CapitalReturnCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 56: Dividend Aristocrat TSX & US Leaderboard
- **As an** income allocator,
- **I want to** review top-ranked dividend-paying companies across TSX and S&P 500,
- **So that** I select reliable dividend payers with strong underlying business quality.
- **Acceptance Criteria:**
  - [ ] Top 10 desk leaderboards sortable by dividend yield and shareholder yield.
- **Feature Alignment:** `Home.tsx` & `/api/v1/rankings`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 57: Organic Float Shrink Compounders (Cannibals)
- **As a** follower of Charlie Munger's "Cannibals" concept,
- **I want to** screen for companies that have retired $\ge 15\%$ of their shares over 5 years without increasing net debt,
- **So that** I own companies where each remaining share owns a growing slice of the business.
- **Acceptance Criteria:**
  - [ ] 5-year float shrink rate calculated.
  - [ ] Cross-referenced against Net Debt growth.
- **Feature Alignment:** `capital_return_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 58: Share Repurchase Price Timing Effectiveness
- **As a** governance analyst,
- **I want to** compare average repurchase prices against current market prices and intrinsic value,
- **So that** I detect whether management buys shares at market peaks or bargain troughs.
- **Acceptance Criteria:**
  - [ ] Capital allocation commentary notes repurchase trajectory vs valuation multiples.
- **Feature Alignment:** Dossier Capital Allocation Tab.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 59: Special Dividend & Return of Capital Tracking
- **As an** energy and mining specialist,
- **I want to** see total cash distributions including variable and special dividends,
- **So that** cyclical cash windfalls are accounted for in total shareholder return.
- **Acceptance Criteria:**
  - [ ] Cash flow statement tracks total cash dividends paid from financing activities.
- **Feature Alignment:** `FinancialStatement` financing cash flow.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 60: Dilution Drag Alert for High-SBC Tech Firms
- **As a** Silicon Valley equity analyst,
- **I want an** explicit "SBC Drag" metric quantifying how many percentage points of market cap are transferred to executives each year,
- **So that** I factor executive compensation into total cost of ownership.
- **Acceptance Criteria:**
  - [ ] `sbc_drag_pct` computed and displayed on Capital Allocation tab.
- **Feature Alignment:** `CapitalReturnCard.tsx` & `types.ts`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 7: Financial Institutions, Banking & Insurance Specialists (Stories 61–70)

#### Story 61: Strict Architectural Separation for Bank Financials
- **As a** banking sector specialist,
- **I want** Corporate Debt, Free Cash Flow, and Gross Margin strictly left blank for banks and insurance companies per Rule #8,
- **So that** the system never produces nonsensical corporate metrics for financial intermediaries.
- **Acceptance Criteria:**
  - [ ] Corporate debt, FCF, and gross margin are `None`/`NULL` for all banks.
  - [ ] UI displays honest "— (Bank/Insurer)" rather than zero or error.
- **Feature Alignment:** `AGENTS.md` Rule #8 & `models.py:Company`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 62: Common Equity Tier 1 (CET1) Capital Ratio Tracking
- **As a** bank regulatory risk analyst,
- **I want to** inspect the CET1 Ratio and regulatory requirement for Canadian and US banks,
- **So that** I verify capital adequacy against Basel III requirements.
- **Acceptance Criteria:**
  - [ ] Stores CET1 ratio, target, and approach in `financial_snapshots`.
  - [ ] Bank metrics card displays CET1 buffer over regulatory minimum.
- **Feature Alignment:** `bank_engine.py` & `SnapshotOut`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 63: Net Interest Margin (NIM) FY and Quarterly Trajectory
- **As a** depository institution analyst,
- **I want to** view Net Interest Margin (NIM) for full year and recent quarters,
- **So that** I evaluate asset yields versus deposit funding costs through interest rate cycles.
- **Acceptance Criteria:**
  - [ ] `nim_fy2025` and `nim_q4_2025` stored and displayed.
- **Feature Alignment:** `FinancialSnapshot` & Bank snapshot card.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 64: Bank Efficiency Ratio Operational Discipline
- **As an** operations analyst,
- **I want to** review Bank Efficiency Ratio ($\text{Non-Interest Expenses} / \text{Net Revenue}$),
- **So that** I identify cost-disciplined banks operating below $55\%$ efficiency.
- **Acceptance Criteria:**
  - [ ] Efficiency ratio populated for TSX and US banking institutions.
  - [ ] Lower values highlighted as favorable.
- **Feature Alignment:** `bank_engine.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 65: Return on Average Assets (ROAA) for Financials
- **As an** asset manager evaluating banks,
- **I want to** measure Return on Average Assets (ROAA),
- **So that** I evaluate earning power over vast balance sheets where $\text{ROAA} \ge 1.0\%$ signifies top-tier performance.
- **Acceptance Criteria:**
  - [ ] ROAA computed as $\text{Net Income} / \text{Average Total Assets}$ for financials.
- **Feature Alignment:** `bank_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 66: Cross-Border Banking ROE Comparison (CAD vs USD)
- **As a** North American bank allocator,
- **I want to** compare Canadian Big 6 banks (e.g. Royal Bank of Canada) with US money center banks (e.g. JPMorgan Chase) on unitless ROE,
- **So that** I compare profitability across borders without invalid currency blending.
- **Acceptance Criteria:**
  - [ ] Compare table displays unitless ROE and ROA for both CA:RY:TSX and US:JPM:US side-by-side.
  - [ ] Preserves native CAD and USD money columns separately.
- **Feature Alignment:** `Compare.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 67: Insurance Combined Ratio & Underwriting Profitability
- **As an** insurance sector analyst,
- **I want to** track property and casualty underwriting performance,
- **So that** I verify whether insurance operations generate positive float at zero cost.
- **Acceptance Criteria:**
  - [ ] Insurance metrics cataloged under GICS Insurance industry.
- **Feature Alignment:** `METRIC_CATALOG.md`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 68: Canadian Bank Dividend Yield & Payout Stability
- **As an** income investor,
- **I want to** evaluate dividend yield and historical stability across the TSX Big 6 banks,
- **So that** I choose the safest income streams for tax-advantaged Canadian accounts.
- **Acceptance Criteria:**
  - [ ] Sector snapshot for Canadian Banks shows rankings by yield and composite score.
- **Feature Alignment:** `/api/v1/sectors/Banks/snapshot?currency=CAD`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 69: Bank Credit Loss Provision Trend
- **As a** macro credit researcher,
- **I want to** monitor provisions for credit losses (PCL) as a percentage of loans,
- **So that** I detect deterioration in consumer and commercial loan books early.
- **Acceptance Criteria:**
  - [ ] Financial statement lines capture loan loss provisions where filed.
- **Feature Alignment:** `FinancialStatement`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 70: Automatic Banking Health Rating Badge
- **As a** generalist investor reviewing a bank dossier,
- **I want an** unambiguous "Bank Safety Rating" summarizing capital, margin, and efficiency,
- **So that** I know if a bank is healthy without having to be a specialized credit analyst.
- **Acceptance Criteria:**
  - [ ] Bank safety summary card displayed on Dossier overview for financial institutions.
- **Feature Alignment:** `bank_engine.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 8: Shariah & Halal (AAOIFI) Ethical Investors (Stories 71–80)

#### Story 71: AAOIFI Total Debt to Market Capitalization Screen
- **As a** Shariah-compliant fund manager,
- **I want to** evaluate whether $\text{Total Debt} / \text{Market Cap} < 30.0\%$,
- **So that** companies exceeding Islamic leverage thresholds are flagged.
- **Acceptance Criteria:**
  - [ ] Threshold evaluated against verified total debt and market cap.
  - [ ] Test status clearly labeled: Pass / Fail / Data Incomplete.
- **Feature Alignment:** `backend/app/services/halal.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 72: Cash & Interest-Bearing Securities Threshold Test
- **As an** Islamic ethical investor,
- **I want to** check whether $(\text{Cash} + \text{Short-Term Investments}) / \text{Market Cap} < 30.0\%$,
- **So that** firms whose assets are primarily interest-bearing cash deposits are flagged.
- **Acceptance Criteria:**
  - [ ] Compares cash + ST investments against 30% of market capitalization.
- **Feature Alignment:** `halal.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 73: Accounts Receivable to Market Capitalization Test
- **As an** AAOIFI compliance researcher,
- **I want to** verify whether $\text{Accounts Receivable} / \text{Market Cap} < 33.0\%$,
- **So that** firms violating Islamic trade debt limits are identified.
- **Acceptance Criteria:**
  - [ ] 10-K accounts receivable evaluated against the 33% threshold.
- **Feature Alignment:** `halal.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 74: Impure Interest Income Ratio Calculation
- **As a** practicing investor,
- **I want to** compute the Impure Income Ratio ($\text{Interest Income} / \text{Total Revenue}$),
- **So that** I know if non-operating interest income is $\le 5.0\%$ and can calculate exact dividend purification amounts.
- **Acceptance Criteria:**
  - [ ] Sourced directly from SEC EDGAR `InvestmentIncomeInterest` or filing line items.
  - [ ] Displays exact impure percentage and purification guidance.
- **Feature Alignment:** `halal.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 75: Halal Status as Informative Flag, Never an Exclusionary Filter
- **As an** equity researcher following AGENTS.md,
- **I want** Halal status to act as an informative badge rather than an exclusionary filter,
- **So that** non-halal companies remain fully searchable and benchmarkable across all sectors.
- **Acceptance Criteria:**
  - [ ] All 764 companies remain accessible regardless of Halal status.
  - [ ] Halal is an optional preset/filter in the screener.
- **Feature Alignment:** `AGENTS.md` & `Screener.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 76: AAOIFI Halal Candidates Screener Preset
- **As a** Halal equity portfolio builder,
- **I want a** 1-click screener preset that surfaces all companies meeting AAOIFI financial criteria,
- **So that** I assemble Shariah-compliant portfolios in seconds.
- **Acceptance Criteria:**
  - [ ] Screener preset: `aaoifi_halal_candidates`.
  - [ ] Returns filtered candidates with compliance test breakdown.
- **Feature Alignment:** `/api/v1/screen?preset=aaoifi_halal_candidates`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 77: Halal Compliance Drill-Down Explainer Modal
- **As a** wealth advisor explaining compliance to a client,
- **I want to** click on a company's Halal badge and view an itemized breakdown of every AAOIFI test,
- **So that** I can show the exact numbers behind a compliant or non-compliant verdict.
- **Acceptance Criteria:**
  - [ ] Halal details drawer/card shows all 4 ratio tests with numerator, denominator, and threshold.
- **Feature Alignment:** `Dossier.tsx` Halal card.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 78: TSX Composite Halal Screening in CAD
- **As a** Canadian Muslim investor,
- **I want to** screen the TSX Composite for Halal companies in native CAD,
- **So that** I invest domestically without incurring US currency exchange fees.
- **Acceptance Criteria:**
  - [ ] Screener supports filtering by `currency=CAD` and `preset=aaoifi_halal_candidates`.
- **Feature Alignment:** `Screener.tsx` & `screener_engine.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 79: SPUS (S&P 500 Shariah ETF) Cohort Tagging
- **As an** index benchmarker,
- **I want to** filter companies that belong to the SPUS Halal ETF cohort,
- **So that** I compare my individual picks against the premier Islamic ETF benchmark.
- **Acceptance Criteria:**
  - [ ] `universe_tags` includes `SPUS` for constituent companies.
  - [ ] Screener supports filtering by universe tag `SPUS`.
- **Feature Alignment:** `etf_resolver.py` & `Screener.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 80: Dynamic Halal Recalculation on Market Cap Shifts
- **As a** risk manager during volatile markets,
- **I want** Halal ratios automatically recomputed when market prices and valuations update,
- **So that** companies that breach the 30% threshold during market sell-offs are flagged immediately.
- **Acceptance Criteria:**
  - [ ] Pipeline recalculates halal ratios during price refresh.
- **Feature Alignment:** `calculation_pipeline.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 9: Cross-Border US / Canadian Allocators (Stories 81–90)

#### Story 81: Strict Non-Contamination of CAD and USD Money
- **As a** cross-border allocator,
- **I want** USD and CAD monetary values never summed, averaged, or converted using arbitrary FX rates,
- **So that** original financial statement integrity is strictly preserved per Rule #1.
- **Acceptance Criteria:**
  - [ ] No mixed-currency money calculations anywhere in backend or frontend.
  - [ ] Cross-border comparisons use unitless ratios only (P/E, ROE, margins, percentiles).
- **Feature Alignment:** `AGENTS.md` Rule #1 & `compare.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 82: Cross-Border Compare Table with Currency Warning Banner
- **As a** dual-currency researcher comparing US and Canadian peers (e.g. SHOP.TO vs MSFT),
- **I want a** prominent banner highlighting cross-border currency differences,
- **So that** I am alerted that monetary amounts are in native currencies while ratios are normalized.
- **Acceptance Criteria:**
  - [ ] `currency_warning: true` returned by `/api/v1/compare`.
  - [ ] UI displays amber banner: "Cross-border comparison: Monetary values shown in native currencies (CAD & USD)".
- **Feature Alignment:** `Compare.tsx` & `CompareOut`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 83: Dual-Desk Home View (Top 10 USD & Top 10 CAD)
- **As a** North American equity trader,
- **I want** separate Top 10 USD and Top 10 CAD leaderboards visible immediately on the desk home screen,
- **So that** I see top fundamental ideas in both markets without changing settings.
- **Acceptance Criteria:**
  - [ ] Home screen renders Top 10 USD and Top 10 CAD tables side-by-side.
- **Feature Alignment:** `Home.tsx` & `rankings.py`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 84: Same-Currency Valuation Percentile Benchmarking
- **As a** Canadian value investor,
- **I want** TSX companies ranked against Canadian sector peers and US companies ranked against US peers,
- **So that** valuation multiples reflect local market capital cost environments.
- **Acceptance Criteria:**
  - [ ] Percentiles calculated strictly within `(peer_group, currency)` buckets.
  - [ ] 3NF `peer_benchmarks` table stores discrete currency percentiles.
- **Feature Alignment:** `peer_engine.py` & `PeerBenchmark`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 85: Canadian Oil Majors Versus US Energy Giants Comparison
- **As an** energy strategist,
- **I want to** contrast Canadian heavy oil producers (CNQ.TO, SU.TO) with US integrated majors (XOM, CVX) on FCF margin and debt,
- **So that** I decide which side of the border offers superior capital efficiency.
- **Acceptance Criteria:**
  - [ ] Compare view plots FCF Margin, ROIC, and Debt-to-EBITDA side-by-side.
- **Feature Alignment:** `Compare.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 86: Foreign ADR Reporting vs Trading Currency Transparency
- **As an** investor in foreign ADRs (e.g. Alibaba BABA),
- **I want to** see financial statements reported in native CNY while the stock price is in USD,
- **So that** I am never misled into thinking revenue is in US Dollars.
- **Acceptance Criteria:**
  - [ ] Status ribbon explicitly displays: "Statements in CNY · Trades in USD".
  - [ ] Suppresses bogus direct price-to-statement multiples.
- **Feature Alignment:** `Dossier.tsx` & `allCurrency.ts`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 87: Sector Overview Currency Switcher
- **As a** sector researcher,
- **I want a** 1-click toggle between ALL, USD, and CAD on sector overview screens,
- **So that** I can isolate TSX stocks or S&P 500 stocks within any GICS sector.
- **Acceptance Criteria:**
  - [ ] Currency pills (`ALL | USD | CAD`) instantly filter sector ranking tables.
- **Feature Alignment:** `Sector.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 88: TSX SEDAR+ Direct Filing Verification
- **As a** Canadian fundamental researcher,
- **I want a** direct link to SEDAR+ on TSX company dossiers,
- **So that** I inspect original Canadian regulatory filings and MD&A reports.
- **Acceptance Criteria:**
  - [ ] TSX dossiers display direct link to SEDAR+ portal.
- **Feature Alignment:** `Dossier.tsx` Filings tab.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 89: US SEC EDGAR CIK Direct Repository Link
- **As a** US institutional analyst,
- **I want a** direct link to the SEC EDGAR company repository utilizing the verified CIK number,
- **So that** I inspect the original 10-K and 10-Q XBRL documents.
- **Acceptance Criteria:**
  - [ ] US dossiers display verified CIK and direct SEC search link.
- **Feature Alignment:** `Dossier.tsx` Filings tab.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 90: Dual-Currency Watchlist Persistence
- **As an** active trader managing both US and Canadian positions,
- **I want to** save both USD and CAD tickers to a persistent local watchlist,
- **So that** my personalized coverage universe is preserved across browser sessions.
- **Acceptance Criteria:**
  - [ ] Watchlist stored in browser `localStorage`.
  - [ ] Displays composite score, signal badge, and native currency chip.
- **Feature Alignment:** `Home.tsx` & `lib/watchlist.ts`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

### Category 10: Executive Portfolio Managers & Rapid Decision Makers (Stories 91–100)

#### Story 91: The 60-Second Automated Safety Verdict
- **As a** busy portfolio manager who hears 50 stock pitches a week,
- **I want an** executive synthesis algorithm classifying any stock into 1 of 5 decisive verdict tags,
- **So that** I know in under 60 seconds whether a stock deserves deep diligence or immediate rejection.
- **Acceptance Criteria:**
  - [ ] Deterministic verdict tags:
    1. `COMPOUNDER AT FAIR VALUE`
    2. `UNDERVALUED BARGAIN`
    3. `OVERVALUED QUALITY`
    4. `CYCLICAL PEAK: CAUTION`
    5. `AVOID: VALUE TRAP / DISTRESS`
  - [ ] Accompanied by 3 concise factual rationale bullets.
- **Feature Alignment:** `backend/app/services/verdict_engine.py` & `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 92: Expectation Investing Reverse DCF Solver
- **As a** Michael Mauboussin disciple,
- **I want to** reverse engineer the current stock price using a 10-year Reverse DCF Brent solver,
- **So that** I solve for the market-implied growth rate and determine if expectations are priced for perfection.
- **Acceptance Criteria:**
  - [ ] Calculates Implied 10-Year FCF Growth Rate ($g_{\text{implied}}$).
  - [ ] Computes Expectations Gap ($\Delta g = g_{\text{implied}} - \text{CAGR}_{5Y}$).
  - [ ] Benchmarks against Malkiel/Collins 8.0% index opportunity cost hurdle.
- **Feature Alignment:** `backend/app/services/valuation_engine.py` & `ReverseDcfCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 93: Reverse DCF Interactive Sensitivity Matrix
- **As a** valuation modeller,
- **I want an** interactive sensitivity grid showing intrinsic share values across varying WACCs (7%–11%) and Terminal Growth Rates (1.5%–3.5%),
- **So that** I stress-test my valuation assumptions under different interest rate regimes.
- **Acceptance Criteria:**
  - [ ] $5 \times 5$ matrix rendered in pure responsive HTML/SVG.
  - [ ] Current stock price benchmarked against matrix cells.
- **Feature Alignment:** `ReverseDcfCard.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 94: Ittelson SVG Cash Flow Waterfall Bridge
- **As a** financial analyst reviewing cash flows,
- **I want a** visual waterfall bridge connecting Net Income to Operating Cash Flow to Free Cash Flow,
- **So that** I see non-cash D&A add-backs, working capital drains, and capex deductions clearly.
- **Acceptance Criteria:**
  - [ ] Rendered in pure responsive SVG with zero npm chart dependencies.
  - [ ] Accessible table alternative for screen readers.
- **Feature Alignment:** `CashFlowBridge.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 95: TradingView Interactive Technical Chart with Fallback
- **As a** fundamental analyst seeking trade entry timing,
- **I want an** interactive candlestick chart with volume and technical overlays,
- **So that** I align fundamental analysis with technical support and resistance levels.
- **Acceptance Criteria:**
  - [ ] Zero-npm sandbox-isolated TradingView embed.
  - [ ] Automatic SVG sparkline fallback if offline or blocked.
- **Feature Alignment:** `TradingViewChart.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 96: Slide-Over Fact-Grounded Analyst AI Assistant
- **As a** research analyst investigating a company,
- **I want a** slide-over AI research assistant grounded strictly in verified database financial rows,
- **So that** I ask natural language questions ("Is the dividend safe?", "What are the accounting red flags?") without AI hallucinations.
- **Acceptance Criteria:**
  - [ ] Backend prompt strictly injects verified SQLite DB rows.
  - [ ] Prominent disclaimer: "AI draft grounded in verified local facts. Not investment advice."
  - [ ] Zero capability for LLM to overwrite fundamental numbers.
- **Feature Alignment:** `StockChatDrawer.tsx` & `/api/v1/companies/{id}/chat`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 97: Comprehensive Institutional CSV Export
- **As an** institutional analyst building models in Excel,
- **I want to** export screener results and sector snapshots to CSV with all institutional metrics included,
- **So that** I seamlessly feed local research data into proprietary spreadsheets.
- **Acceptance Criteria:**
  - [ ] CSV export includes Altman Z, Altman Zone, Penman RNOA/FLEV, TSY, EQR, and percentiles.
  - [ ] Correctly escapes commas and quotes.
- **Feature Alignment:** `Screener.tsx:exportCsv`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 98: High-Density 8-Tab Dossier Workspace Navigation
- **As a** power user conducting deep company research,
- **I want to** navigate across 8 specialized research tabs with URL-persisted state (`?tab=financials`),
- **So that** I bookmark and share specific analytical perspectives effortlessly.
- **Acceptance Criteria:**
  - [ ] Tabs: Overview, Financials, Valuation, Forensics, Capital Allocation, Technicals, Filings, Thesis.
  - [ ] Synced with browser history (`useSearchParams`).
- **Feature Alignment:** `Dossier.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 99: Local Scratchpad & Investment Thesis Checklist
- **As an** active investor developing high-conviction theses,
- **I want a** local scratchpad and Bull/Bear checklist that persists in browser localStorage,
- **So that** my personal investment notes remain private and saved on my local machine.
- **Acceptance Criteria:**
  - [ ] Text scratchpad auto-saves to `localStorage`.
  - [ ] Printable factsheet export view (`FactsheetPrintView.tsx`).
- **Feature Alignment:** `Dossier.tsx` & `FactsheetPrintView.tsx`.
- **System Status:** IMPLEMENTED & VERIFIED.

#### Story 100: Zero-Cloud, Zero-Paid-API Local Sovereign Research
- **As an** independent investor and privacy advocate,
- **I want the** entire system to operate 100% locally via Docker with SQLite and free public SEC data,
- **So that** my research is private, free from subscription paywalls, and fully sovereign.
- **Acceptance Criteria:**
  - [ ] Zero paid API keys required for core functionality.
  - [ ] Local SQLite WAL with sub-20ms queries.
  - [ ] Complete local Docker Compose deployment.
- **Feature Alignment:** Full application architecture & `AGENTS.md`.
- **System Status:** IMPLEMENTED & VERIFIED.

---

## Part 2: Feature Alignment & Value Assessment Matrix

| Story ID Range | Category | Feature Set | High-Value Additions Delivered |
|---|---|---|---|
| **1–10** | Deep Value & Graham | Graham Net-Net, NNWC, Graham Number, EV/EBITDA Percentiles | Added Net-Net Working Capital haircut valuation, Graham Floor benchmarks, and Greenblatt Magic Formula screener preset. |
| **11–20** | Buffett Compounders & Quality | Owner Earnings, ROIC durability, Dorsey Moats, Penman Spread | Implemented Bruce Greenwald Maintenance vs Growth CapEx engine and automated debt-funded buyback distortion alerts. |
| **21–30** | Peter Lynch Growth | 6 Archetypes, PEG Classifier, Outlier-Sanitized CAGR | Built Lynch Archetype classifier (Fast Grower, Stalwart, Cyclical, etc.) and PEG ratio evaluation against multi-year CAGR. |
| **31–40** | Forensic Accounting | Beneish M-Score, Sloan Accruals, Schilit Decoupling, EQR | Eliminated all heuristic proxies; built 8-variable Beneish and Sloan accruals from genuine 10-K balance sheet lines. |
| **41–50** | Credit & Solvency | Altman Z (Mfg) & Z'' (Service), Fixed-Charge Coverage, Debt Walls | Built dual-model Altman engine with bank exclusion banner and automated distress safety verdicts. |
| **51–60** | Shareholder Yield & Buybacks | Diluted Share CAGR, Net Buyback Yield, True Shareholder Yield | Subtracted genuine filing SBC from repurchases to evaluate true cash returned to owners; added TSY screener slider. |
| **61–70** | Financial Institutions | CET1 Ratio, NIM, Efficiency Ratio, ROAA | Preserved Rule #8 (blank corporate debt/FCF) while surfacing specialized banking health metrics for Big 6 and US banks. |
| **71–80** | Shariah & Halal (AAOIFI) | AAOIFI Debt, Cash, Receivables, Impure Income | Sourced interest income from SEC filings to compute impure income ratio; non-exclusionary flag architecture. |
| **81–90** | Cross-Border Allocators | Currency Segregation, Unitless Ratios, Dual Top 10 | Strict currency isolation (USD vs CAD); verified CIK EDGAR and SEDAR+ direct filing links. |
| **91–100** | Executive Decision Makers | 60-Second Verdict, Reverse DCF Solver, Fact-Grounded AI | Implemented 5 mutually exclusive safety verdict tags, Reverse DCF Brent solver, TradingView chart, and Analyst AI drawer. |

---

*This document serves as the certified Master User Story Catalog for the Local Equity Research Terminal.*
