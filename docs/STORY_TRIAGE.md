# Story Triage — 1,000 User Stories Analysis (Phase 0)

> **Investment Stock Application — Strategic Backlog & Triage Specification**
> Ingesting market research, competitive analysis, and canonical literature to sort all 1,000 user stories (US-0001…US-1000) against current application functionality, frozen contracts, and data availability.

---

## Executive Summary

All 1,000 user stories across the 20 domains have been triaged against:
1. **Current Codebase Capabilities**: FastAPI read-only research layer, 3NF SQLite database, 720-company seed snapshot (500 S&P 500 + 220 TSX), forensic accounting suite (Beneish, Altman, Sloan, Penman), deterministic 4-pillar scoring engine (v1), AAOIFI-style halal flag, and React design system.
2. **Frozen Contracts (README §2)**: Strict currency segregation (CAD vs USD never mixed), owner workbook immutability, missing data honest NULL+flags, Company_ID format (`US:TICKER:US` | `CA:TICKER:TSX`), locked composite scoring weights (0.30 Q / 0.25 V / 0.25 G / 0.20 R), bank/insurer debt carve-outs, SVG+CSS chart rule (no chart npm libraries), and local Docker deployment without paid APIs.
3. **Market Research Guidance (`KEY_NOTES_Market_Research_and_Recommendations.md`)**: Winning the 6-minute research window, radical explainability, base-rate context (Bessembinder), filings-first social layer, and progressive disclosure.

### High-Level Category Counts

| Category | Story Count | Percentage | Description |
|---|:---:|:---:|---|
| **1. Already Satisfied** | **171** | **17.1%** | Covered by existing API surface (README §7) or UI screens with verified evidence. |
| **2. Implementable Now** | **793** | **79.3%** | Achievable using the local stack, SQLite DB, SEC EDGAR free APIs, and Yahoo free endpoints. Clustered into strategic epics with effort (S/M/L) and value tags. |
| **3. Deferred / Blocked** | **36** | **3.6%** | Blocked by paid API subscriptions, cloud multi-user infrastructure, or frozen contract conflicts. Documented with blocker reason and cheapest legitimate future path. |
| **Total** | **1,000** | **100.0%** | Complete accounting across all 20 domains (US-0001 through US-1000). |

---

## Domain-by-Domain Triage Breakdown

| Domain | Domain Name | Total Stories | Already Satisfied | Implementable Now | Deferred / Blocked |
|---|---|:---:|:---:|:---:|:---:|
| **D01** | Screening & Discovery | 50 | 16 | 33 | 1 |
| **D02** | Scoring & Pillar Transparency | 50 | 19 | 29 | 2 |
| **D03** | Valuation & Intrinsic Value | 50 | 11 | 38 | 1 |
| **D04** | Statements & History Deep-Dive | 50 | 12 | 38 | 0 |
| **D05** | Forensic Analysis & Red Flags | 50 | 12 | 38 | 0 |
| **D06** | Comparison & Peer Analysis | 50 | 12 | 38 | 0 |
| **D07** | Portfolio & Holdings Tracking | 50 | 0 | 48 | 2 |
| **D08** | Alerts, Monitoring & Change Detection | 50 | 0 | 47 | 3 |
| **D09** | Reporting, Export & Documentation | 50 | 4 | 44 | 2 |
| **D10** | Data Trust & Provenance | 50 | 17 | 33 | 0 |
| **D11** | Education & Onboarding | 50 | 4 | 46 | 0 |
| **D12** | Social, Community & Sentiment | 50 | 3 | 31 | 16 |
| **D13** | Canadian Market & Halal Screening | 50 | 15 | 35 | 0 |
| **D14** | Price, Momentum & Technical Context | 50 | 5 | 44 | 1 |
| **D15** | AI Narration & Explanation | 50 | 6 | 43 | 1 |
| **D16** | Workflow, UX & Performance | 50 | 11 | 38 | 1 |
| **D17** | Strategy, Roadmap & Monetization | 50 | 4 | 43 | 3 |
| **D18** | Sectors & Market Structure | 50 | 10 | 40 | 0 |
| **D19** | History, Backtesting & Score Behavior | 50 | 3 | 47 | 0 |
| **D20** | Security, Privacy & Local Operations | 50 | 7 | 40 | 3 |

---

## Section 1: Already Satisfied Stories (171 Stories)

These 171 user stories are fully covered by the current codebase implementation. Each is mapped to the exact API endpoint (README §7) or UI screen component with verifiable evidence.

| Story ID | Persona | Summary / Capability | Existing API Surface or UI Screen | Verified Line of Evidence |
|---|---|---|---|---|
| **US-0002** | Value hunter | screen the whole 720-name universe by earnings yield percentile within each sector | `POST /api/v1/screener/run & GET /api/v1/screen` | Filters universe by earnings yield / value percentile relative to sector peers. |
| **US-0004** | Halal investor | run a saved halal-candidate screen that explains each exclusion reason | `GET /api/v1/screen?preset=aaoifi_halal_candidates` | Runs AAOIFI halal-candidate preset and surfaces per-test failure basis from HalalFlag.tests_json. |
| **US-0006** | Canadian saver | restrict any screen to TSX-listed names with CAD reporting | `GET /api/v1/screen?currency=CAD & Screen.tsx` | Restricts universe screening strictly to TSX-listed companies reporting in native CAD. |
| **US-0008** | Skeptic | exclude any company flagged by Beneish M-Score or Altman Z distress zones from my screen | `POST /api/v1/screener/run & Screener.tsx` | Excludes companies flagged with Beneish manipulation (M > -1.78) or Altman distress zones. |
| **US-0013** | Student | use teacher-style preset screens like 'Graham defensive' or 'Lynch fast grower' | `GET /api/v1/screen?preset=graham_net_net_bargains` | Pre-built classic presets (Graham net-nets, Peter Lynch growth, Greenblatt magic formula, Piotroski). |
| **US-0015** | Value trap avoider | pair any cheapness filter with a mandatory quality floor (ROE and accruals) | `POST /api/v1/screener/run & Screener.tsx` | Allows combining value bounds with ROE floors and Sloan accruals quality ceilings. |
| **US-0017** | Sector rotator | screen inside one custom industry group with its own medians | `GET /api/v1/screen?industry=... & sectors.py` | Screens within narrow custom industry sheets using industry-specific peer medians. |
| **US-0019** | Income-focused retiree | screen for shareholder yield (dividends plus net buybacks) above 5% | `GET /api/v1/screen?preset=true_shareholder_yield_leaders` | True Shareholder Yield leader preset combines dividend yield and net share buyback rate. |
| **US-0023** | Data auditor | show a coverage badge on every screen row (how many pillars have data) | `ScreenItem.coverage in GET /api/v1/screen & Screen.tsx` | Surfaces coverage badge (1-4 pillars) on every row to distinguish missing data from poor quality. |
| **US-0024** | Risk-averse investor | screen out banks and insurers automatically when debt metrics don't apply | `GET /api/v1/screen?exclude_banks=true` | Automatically detects Financials sector and excludes banks/insurers where debt ratios do not apply. |
| **US-0026** | Deep value hunter | screen for price below net current asset value where data permits | `GET /api/v1/screen?preset=graham_net_net_bargains` | Screens for market cap below Net Current Asset Value (NCAV = Current Assets - Total Liabilities). |
| **US-0029** | Fintech builder | get an API endpoint that returns any saved screen's results as JSON | `GET /api/v1/screen & POST /api/v1/screener/run` | FastAPI endpoints return typed JSON arrays of screened companies with metadata. |
| **US-0032** | Privacy-focused user | know all screening runs locally with no account required | `Local SQLite (data/app.db) & FastAPI Docker stack` | Entire screening pipeline executes completely locally with zero network calls and no auth. |
| **US-0036** | Bank analyst | screen financials on CET1, NIM, and efficiency ratio instead of standard leverage | `GET /api/v1/sectors/Banks/rankings & FinancialSnapshot` | Dedicated bank analysis treats CET1, NIM, and efficiency ratio as primary regulatory metrics. |
| **US-0040** | Multi-currency household | choose USD-only, CAD-only, or ratio-only result modes on any screen | `GET /api/v1/screen?currency=ALL|USD|CAD` | Segregates currency: ALL mode hides money columns and shows unitless ratios; USD/CAD show native amounts. |
| **US-0050** | Idea streaker | pin any screen row straight into my watchlist with one click | `src/lib/watchlist.ts & Screen.tsx` | Interactive watchlist star toggle on screen table pins any company into local storage watchlist. |
| **US-0054** | Skeptic | view the score's coverage penalty separately from pillar results | `Dossier.tsx & GET /api/v1/companies/{company_id}/dossier` | Displays coverage multiplier (×0.92, ×0.80, ×0.65) separately from underlying pillar scores. |
| **US-0059** | Fairness checker | view peer-set membership for any percentile-based score | `Score.peer_set_type & GET /api/v1/companies/{company_id}/similar` | Displays peer set type (custom industry >= 8 else GICS), peer count, and exact rank. |
| **US-0061** | Numbers person | see the exact percentile rank of every metric inside its sector-currency bucket | `PercentileMatrix.tsx & Score.percentiles_json` | Visualizes exact sector-currency percentile ranks across 8 core fundamental ratios. |
| **US-0062** | Data-safety-first user | see 'insufficient data' states rendered as clearly as strong signals | `VerdictBadge.tsx & copy.ts` | Renders explicit 'insufficient_data' badge and descriptive banner when coverage is below threshold. |
| **US-0065** | Signal mapper | see the mapping table from score ranges to signals (Strong candidate through Avoid) | `src/api/copy.ts signalCopy & README.md §5` | Full deterministic mapping table from score ranges (8-10 Strong Candidate to 0-3.4 Avoid) in UI. |
| **US-0066** | Home-office analyst | get a verdict-first layout with evidence one click deeper | `Dossier.tsx Level 1 VerdictBadge + ExecutiveCockpit` | Verdict-first executive flight deck with 3-tier progressive disclosure meeting 6-minute window. |
| **US-0068** | Forensic purist | see forensic flags displayed beside the composite, never blended into it | `Dossier.tsx Level 3 & ForensicCard.tsx` | Forensic accounting models (Beneish, Altman, Sloan) rendered in dedicated card, isolated from composite. |
| **US-0071** | Non-numeric learner | get a colorblind-safe, icon-reinforced signal badge system | `src/components/layout/Chip.tsx & tokens.css` | Accessible semantic status chips using distinct shapes, icons, and WCAG contrast-verified tokens. |
| **US-0073** | Version-conscious user | know the method_version stamp on every score I export | `Score.method_version='v1' across all score payloads` | Explicit method_version stamp included in all database models, API responses, and dossier exports. |
| **US-0078** | Pesky-details person | see which tests were skipped in F-Score because inputs were NULL | `app/services/scoring.py F-score computation` | Impossible Piotroski accounting tests reduce the denominator dynamically rather than scoring zero. |
| **US-0081** | Dividend researcher | see payout sustainability inputs reflected inside quality and risk pillars | `app/services/scoring.py Quality & Risk calculations` | FCF margin, interest coverage, and net debt/EBITDA integrate directly into Quality and Risk pillars. |
| **US-0082** | Bank-focused analyst | see bank-specific pillar inputs (ROE, ROA, NIM, efficiency, CET1) in the quality view | `app/services/scoring.py bank scoring branch` | Banks and insurers scored on ROE, ROA, ROAA, Efficiency, CET1, and NIM instead of corporate debt/FCF. |
| **US-0087** | Accessibility-first user | navigate the whole score UI by keyboard with screen-reader labels on every gauge | `src/components/AppShell.tsx & CompositeGauge.tsx` | Full keyboard tab navigation with accessible aria-label on all SVGs and composite gauges. |
| **US-0089** | Skeptical spouse | share a company verdict link that renders the evidence without login | `Local web app at /c/:companyId` | Permalinks render full dossier with transparent evidence without requiring login or session auth. |
| **US-0091** | Truth-in-labeling advocate | read 'research signal, not investment advice' directly under every score with reasoning | `DISCLAIMER constant in config.py & UI footer` | Prominent 'Personal research software, not investment advice' disclaimer displayed across all views. |
| **US-0093** | Metric learner | hover any unfamiliar metric to get a 2-line definition plus why it matters | `src/components/InfoTip.tsx & src/api/glossary.ts` | Accessible 22KB glossary dictionary provides hover tooltips with definitions across all metrics. |
| **US-0096** | Honest-gap user | see a globe-with-dashes state when a pillar is NULL with a link to the missing-input list | `src/components/viz/MiniPillarBars.tsx & CompositeGauge.tsx` | Hollow bar and globe indicator rendered whenever a pillar is NULL, paired with data gap notice. |
| **US-0098** | Framework teacher | print a one-page score explainer per company for my investment club | `FactsheetPrintView.tsx (@media print)` | Two-page institutional research factsheet print memo formatted for physical paper or PDF export. |
| **US-0099** | Decisive user | get a clear 'no verdict available' with reasons when coverage is too thin | `Score.signal = 'insufficient_data' in scoring engine` | Emits explicit 'insufficient_data' signal and suppresses composite when zero pillars are computable. |
| **US-0103** | Margin-of-safety investor | see price versus my intrinsic-value range as a visual margin gauge | `GrahamCard.tsx & ToyDcfCard.tsx` | Renders visual margin of safety gauge comparing current price against Graham intrinsic value. |
| **US-0104** | Reverse-DCF user | read the growth expectation the current price implies | `GET /api/v1/companies/{company_id}/valuation & ReverseDCFCard.tsx` | Deterministic reverse DCF computes market-implied 10-year FCF growth and expectations gap. |
| **US-0107** | Comparables user | see a comps table across â‰¤8 custom-industry peers with median lines | `PeerMatrixCard.tsx & GET /api/v1/compare` | Side-by-side comps table across up to 8 peer companies with median benchmarks. |
| **US-0110** | Owner-earnings follower | see Buffett-style owner earnings computed and used in valuation | `CashFlowWaterfall.tsx & app/services/owner_earnings.py` | Computes Buffett owner earnings (Operating Cash Flow minus Maintenance Capex) in cash flow waterfall. |
| **US-0112** | Asset-based valuer | see book value, tangible book, and net cash per share alongside earnings-based values | `DerivedMetric.book_equity & ToyDcfCard.tsx` | Surfaces book value, tangible book, and net debt per share alongside earnings-based valuation. |
| **US-0124** | International comparer | run valuation ratios in native currency with unitless comparisons across borders | `README.md §2.1 & src/lib/allCurrency.ts` | Ratios displayed unitless for cross-border comparison; money fields strictly tagged with native currency. |
| **US-0127** | Buyback-aware valuer | see per-share value effects of SBC dilution and net share shrink inside the model | `DerivedMetric.stock_based_compensation & ShareholderYieldBar.tsx` | Nets SBC dilution against share buybacks in True Shareholder Yield calculation. |
| **US-0133** | Cautious newcomer | get plain warnings when a company has negative earnings making PE-based views meaningless | `pe_flag = 'Loss / Deficit' in app/api/dossier.py` | Contextual pe_flag explicitly labels negative-earnings companies as 'Loss / Deficit' rather than showing zero. |
| **US-0136** | Realistic planner | see valuation outputs labeled with as-of price and date | `ValuationReverseDCF.price_as_of & valuation_computed_at` | Reverse DCF output explicitly displays price_as_of timestamp and valuation calculation date. |
| **US-0139** | Data-realism advocate | see which valuation inputs came from the owner workbook versus providers | `FinancialSnapshot.source & provenanceSentence in flags.ts` | Displays source badge (Owner Workbook vs SEC EDGAR vs Yahoo Finance) for every valuation input. |
| **US-0140** | Decision-ready user | get a printable one-page valuation summary per company | `FactsheetPrintView.tsx (@media print)` | Dedicated printable 2-page factsheet includes complete valuation and expectation gap summary. |
| **US-0151** | Fundamental analyst | view 10+ years of income statement, balance sheet, and cash flow side by side | `GET /api/v1/companies/{company_id}/financials` | Returns up to 10 fiscal years of income statement, balance sheet, and cash flow items. |
| **US-0153** | Statement purist | view figures exactly as reported in native currency with unit scale preserved | `FinancialSnapshot verbatim storage & DATA_CONTRACT.md §7` | Financial amounts stored verbatim in native currency units without division or rescaling. |
| **US-0154** | Common-size analyst | switch any statement to common-size (percent of revenue) view | `src/components/financials/CommonSizeTable.tsx` | Toggles financial statement lines into common-size percentages of total revenue. |
| **US-0160** | Cash-flow purist | compare net income to operating cash flow line by line across years | `CashFlowWaterfall.tsx & CashFlowBridge.tsx` | Compares Net Income to Operating Cash Flow and FCF to expose accrual divergences. |
| **US-0165** | TTM believer | see trailing-twelve-month views that update between annual filings | `FinancialSnapshotTTM & app/services/ttm_engine.py` | Normalized 4-quarter rolling TTM financials update continuously between annual 10-K filings. |
| **US-0175** | Data-freshness checker | see last-updated stamps per statement line | `FinancialSnapshot.fetched_at & provider_as_of in dossier.py` | Displays provider fetch timestamp and period end date on historical statement rows. |
| **US-0179** | Currency-purist Canadian | see CAD companies only in CAD and US only in USD with no blended view | `README.md §2.1 & src/lib/allCurrency.ts` | Strict segregation: Canadian names render exclusively in CAD, US names exclusively in USD. |
| **US-0185** | Profit-quality learner | see a bridge from revenue to FCF year by year | `CashFlowWaterfall.tsx & CashFlowBridge.tsx` | Step-by-step waterfall chart bridges Net Income through Working Capital and Capex to FCF. |
| **US-0189** | Statement completionist | request ingestion of any additional ticker and get full statement history on demand | `POST /api/v1/tickers/ingest` | Synchronously ingests any new US or Canadian ticker, fetches SEC/Yahoo filings, and scores it. |
| **US-0190** | Banking specialist | read bank statements with NIM, provisions, and CET1 given first-class treatment | `FinancialStatement bank columns (cet1_ratio, nim, efficiency)` | Financial statement schema models regulatory banking metrics natively. |
| **US-0192** | History skeptic | see coverage indicators showing which years came from seed workbook versus providers | `dossier.py statement_history_10y source badge` | Labels each historical fiscal year row with its provenance source (owner xlsx vs provider). |
| **US-0193** | Long-memory investor | see the company's own 5 and 10-year CAGR summary block | `DerivedMetric CAGRs (revenue_cagr_3y/5y, eps_cagr_3y/5y, fcf_cagr_5y)` | Derived metrics table precomputes 3-year and 5-year compound annual growth rates. |
| **US-0201** | Fraud-wary investor | run the full forensic suite on any new name before buying | `GET /api/v1/companies/{company_id}/forensics & BeneishMatrix.tsx` | Full forensic accounting suite runs Beneish M, Altman Z, Sloan accruals, and Penman analysis. |
| **US-0203** | Detailed reader | see Beneish M-Score component values (DSRI, GMI, AQI, SGI...) with which components drive the result | `beneish_engine.py & BeneishMatrix.tsx` | Decomposes Beneish M-Score into 8 sub-indices (DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA). |
| **US-0204** | Distress avoider | see Altman Z and Z'' zones rendered as colored bands with the company's position | `AltmanZGauge.tsx & AltmanZScoreCard.tsx` | Visualizes Altman Z and Z'' bankruptcy risk scores mapped into Safe, Grey, and Distress zones. |
| **US-0205** | Accrual skeptic | see Sloan accruals percentile with a plain explanation of why high accruals precede underperformance | `ttm_engine.py & ForensicCard.tsx` | Calculates Sloan accrual ratio with green/amber/red indicator and plain-English explanation. |
| **US-0206** | Earnings-quality auditor | see Schilit-style tactic flags mapped to actual financial patterns in this company | `forensic_flags_json in FinancialSnapshotTTM` | Flags Schilit-style shenanigans including aggressive revenue recognition and DSO spikes. |
| **US-0207** | Reformulation student | see Penman reformulated statements separating operating from financing activities | `FinancialPenmanAnalysis & PenmanCard.tsx` | Reformulates financial statements into Net Operating Assets (NOA) and Net Financial Obligations (NFO). |
| **US-0208** | Bank-exclusion checker | see forensic debt-based models automatically skipped for banks with explanation | `penman_engine.py & distress_engine.py bank exclusion` | Automatically marks financial institutions as excluded for leverage-based forensic models. |
| **US-0219** | Dilution forensics user | see SBC as percent of revenue and dilution-adjusted EPS growth side by side | `ShareholderYieldBar.tsx & ttm_engine.py` | Tracks stock-based compensation (SBC) as percentage of revenue and calculates dilution offset. |
| **US-0225** | Skeptical newcomer | read a 'forensic models are screens, not proof' explainer with false-positive context | `ForensicCard.tsx disclaimer banner` | Explicitly warns that forensic models are probabilistic screens, not conclusive fraud determinations. |
| **US-0237** | First-principles learner | read why each of the 8 Beneish variables exists with this company's value | `BeneishMatrix.tsx tooltip glossary` | Explains the economic meaning and formula for each of the 8 Beneish index variables on hover. |
| **US-0248** | Data-complete skeptic | see which forensic inputs were missing and how that limited each score | `forensics.py insufficient_data flags` | Surfaces missing forensic input variables and explains why particular models could not compute. |
| **US-0250** | Model-curious quant | see methodology references (original papers) linked from every model | `src/api/glossary.ts & SCORING_SPEC.md` | Directly cites academic literature (Piotroski 2000, Beneish 1999, Altman 1968, Sloan 1996). |
| **US-0251** | Comparative shopper | compare up to 8 companies across all four pillars on one screen | `GET /api/v1/compare?ids=a,b & Compare.tsx` | Side-by-side comparison screen supports between 2 and 8 companies across all four pillars. |
| **US-0252** | Industry learner | ask 'show me similar companies' from any dossier | `GET /api/v1/companies/{company_id}/similar` | Returns up to 5 closest peer companies from the identical sector-currency peer set. |
| **US-0253** | Cross-border comparer | compare a Canadian name against US peers with ratio-only money display | `Compare.tsx & src/lib/allCurrency.ts` | Cross-border comparison displays unitless ratios (PE, ROE, FCF margin) without currency mixing. |
| **US-0254** | DuPont student | see ROE decomposed into margin, turnover, and leverage for all compared names | `DuPontCard.tsx & Compare.tsx` | Decomposes ROE into Profit Margin × Asset Turnover × Financial Leverage across compared firms. |
| **US-0255** | Bank comparer | compare banks on CET1, ROA, NIM, and efficiency ratio natively | `Compare.tsx bank comparison mode` | Switches to bank-specific metrics (CET1, NIM, ROAA, efficiency) when comparing financial peers. |
| **US-0256** | Growth-vs-value decider | see two candidates' quality, value, growth, and risk pillars side by side with deltas | `Compare.tsx 4-pillar radar & deltas` | Compares Quality, Value, Growth, and Risk pillars side by side with visual difference indicators. |
| **US-0260** | Risk comparer | see leverage, coverage, and volatility side by side | `Compare.tsx Risk section` | Compares Net Debt / EBITDA, Liabilities / Assets, and Interest Coverage across peers. |
| **US-0262** | Valuation comparer | see PE, EV/EBIT, P/B, and FCF yield against peer medians in one table | `Compare.tsx Valuation table` | Compares PE, PB, EV/EBITDA, and FCF Yield alongside sector-currency median benchmarks. |
| **US-0274** | Speed comparer | get a one-line 'best value here / best quality there' summary above the detail table | `Compare.tsx Best-in-Class highlight banner` | Highlights peer with top composite score and best relative value in compare header. |
| **US-0275** | Peer-set auditor | inspect and challenge who's in the peer set and why | `Score.peer_set_type & similar endpoint` | Discloses peer group selection rule (custom industry >= 8 members else GICS sector). |
| **US-0279** | Income-bridge comparer | see total shareholder yield (dividends plus buybacks) compared across peers | `ShareholderYieldBar.tsx & CapitalReturnCard.tsx` | Compares Total Shareholder Yield (dividend yield + net buyback rate) across peer firms. |
| **US-0286** | Coverage-realistic user | see which comparison cells are NULL versus zero | `Compare.tsx cell formatting rules` | Explicitly formats missing data as '—' (NULL) rather than displaying misleading zero values. |
| **US-0401** | Factsheet lover | print a beautiful two-page institutional research factsheet per company | `FactsheetPrintView.tsx (@media print)` | Generates two-page institutional equity research factsheet formatted for print and PDF export. |
| **US-0404** | Data scientist | pull every company's key metrics via a stable API for my own models | `GET /api/v1/companies/{company_id}/dossier` | Complete machine-readable JSON API delivers full dossier, financial history, and scores. |
| **US-0415** | Print purist | get print stylesheets that never cut tables mid-row | `FactsheetPrintView.tsx break-inside-avoid CSS` | Print media stylesheets enforce clean page breaks and prevent tables splitting across pages. |
| **US-0432** | Data-quality reporter | include data-coverage and quality flags in every export | `FactsheetPrintView.tsx data quality section` | Includes data completeness score and active data quality flags in factsheet print export. |
| **US-0451** | Trust-first user | see the exact source (owner workbook, SEC EDGAR, Yahoo) on every number | `FinancialSnapshot.source & provenanceSentence` | Every individual metric carries explicit source provenance (Owner XLSX, SEC EDGAR, Yahoo). |
| **US-0452** | Data auditor | click any metric to see its fetch date, provider, and filing period | `FinancialSnapshot.fetched_at & provider_as_of` | Clicking any metric exposes exact retrieval timestamp, filing period, and provider origin. |
| **US-0454** | Immutability believer | know seed workbook values can never be overwritten and see that status flagged | `app/services/importer.py frozen overwrite policy` | Owner workbook seed rows are permanently immutable; external providers only fill NULL values. |
| **US-0456** | Missing-data realist | see NULL rendered as an explicit state with reason flags everywhere | `src/components/viz/MiniPillarBars.tsx & Dossier.tsx gap labels` | Missing data rendered as explicit NULL with contextual reason flags; never converted to zero. |
| **US-0457** | Currency purist | see every money figure with its native currency badge and never blended totals | `CurrencyBadge.tsx & src/lib/allCurrency.ts` | Every monetary amount tagged with native ISO currency; currency blending strictly prohibited. |
| **US-0458** | Quality-flag reader | browse all data-quality flags for a company in one panel | `data_quality_flags database table & Dossier.tsx` | Dedicated Data Quality Flags drawer displays all 2,026 curated workbook notes and QC flags. |
| **US-0471** | Job curious user | see the job queue state and history | `GET /api/v1/jobs & Jobs.tsx` | Visualizes background job queue status, worker progress stepper, and provider fetch telemetry. |
| **US-0476** | Ticker-disambiguator | see explicit disambiguation for tickers that collide across markets (BN, NA) | `app/services/ids.py Company_ID normalization` | Strict Company_ID grammar (US:TICKER:US | CA:TICKER:TSX) eliminates cross-market ticker collisions. |
| **US-0477** | Format inspector | see raw units (actual dollars) with smart display formatting | `src/lib/format.ts money() formatter` | Values stored in verbatim base currency units; UI formats with appropriate unit suffix (B/M/K). |
| **US-0478** | API consumer | get provenance metadata attached to every API response | `source & fetched_at fields on API schemas` | API responses include full provenance metadata on company snapshots and historical statements. |
| **US-0480** | Data-policy reader | read the plain-language data policy (what gets frozen, filled, flagged) | `docs/DATA_CONTRACT.md` | Comprehensive 57-column data dictionary defines data types, scale rules, and provenance policy. |
| **US-0483** | Local-first advocate | know all data lives in my local database with no external calls on read | `Local SQLite (data/app.db) & FastAPI Lifespan` | All fundamentals stored in local SQLite database; read queries never execute external network calls. |
| **US-0484** | Recovery planner | verify database integrity and repair paths after crashes | `SQLite WAL mode & Alembic migration head guard` | FastAPI startup lifespan validates Alembic migration head and prevents running on mismatched schema. |
| **US-0486** | Schema-curious user | read the data dictionary for every table and field | `docs/DATA_CONTRACT.md & METRIC_CATALOG.md` | Detailed documentation cataloging every database table, column specification, and ratio formula. |
| **US-0494** | Transparency advocate | read how scores, screens, and models each consume data | `docs/SCORING_SPEC.md` | Full mathematical specification of the 4-pillar deterministic scoring algorithm and weights. |
| **US-0496** | Bank-data specialist | understand why certain fields don't exist for banks and aren't guessed | `README.md §2.8 bank carve-outs` | Explicit documentation of why banks/insurers omit corporate debt, FCF, and gross margin. |
| **US-0500** | Peace-of-mind user | see a system status page proving data, scoring, and jobs are healthy | `GET /health & GET /ready & GET /api/v1/research/meta` | System health and telemetry endpoints verify database connectivity and research layer readiness. |
| **US-0505** | Glossary user | get every jargon term defined inline via InfoTips | `src/components/InfoTip.tsx & glossary.ts` | Hovering financial terminology displays accessible inline tooltip definitions with real examples. |
| **US-0512** | Metric-curious user | learn why F-Score has 9 checks and what each detects | `PiotroskiCard.tsx & glossary.ts` | Breaks down all 9 Piotroski fundamental signals across profitability, leverage, and efficiency. |
| **US-0535** | First-time halal user | learn what AAOIFI-style screening does and doesn't certify | `src/api/copy.ts halalCopy & SCORING_SPEC.md` | Explains the exact scope and rules of AAOIFI Shariah financial ratio screening in plain terms. |
| **US-0546** | Methodology reader | read why the scoring weights are what they are | `README.md §5 Scoring Model` | Documents the empirical justification for locked composite weights (0.30 Q, 0.25 V, 0.25 G, 0.20 R). |
| **US-0558** | Noise-hater | choose to see only filings-based signals with social layer fully off | `Default architecture of application` | Application operates in clean, filings-first research mode with zero social media chatter. |
| **US-0566** | Privacy-first user | know the app never posts, likes, or transmits anything social on my behalf | `Local Docker & read-only architecture` | Zero telemetry and zero outbound social media API integrations; research habits never leak. |
| **US-0600** | Responsible-innovation reader | read what the app deliberately does NOT build (influencer rankings, auto-following) and why | `KEY_NOTES §4.5 'Deliberately do NOT build'` | Research document articulates why influencer rankings and auto-trading are deliberately excluded. |
| **US-0601** | Canadian investor | see every Canadian company with native-currency financials and TSX context | `seed/Sector_Financials_Final_Owner.xlsx (220 TSX names)` | Includes 220 S&P/TSX Composite companies with native CAD financial statements. |
| **US-0602** | Cross-border investor | compare a TSX name against its US-listed peers with ratio-only comparisons | `Compare.tsx & src/lib/allCurrency.ts` | Enforces unitless ratio comparison for cross-border US and Canadian stock evaluation. |
| **US-0603** | Halal investor | see the halal flag with full calculation transparency (activity screen, 30/30 ratios) | `app/services/halal.py & HalalBadge in Dossier.tsx` | Full transparency into AAOIFI screening: business activity screen plus 30/30 debt/cash ratios. |
| **US-0604** | Halal researcher | see WHY a company failed the flag with each failing input shown | `HalalFlag.tests_json rendered in Dossier.tsx` | Displays specific failed test reason (e.g. debt > 30% of market cap) for non-compliant companies. |
| **US-0605** | Halal-uncertain user | see 'unknown' whenever inputs are missing rather than a false pass | `app/services/halal.py conservative default` | Emits status='unknown' when financial inputs are incomplete; never guesses compliance. |
| **US-0606** | SPUS cohort user | screen within the SPUS halal ETF cohort against my own stricter checks | `Company.universe_tags & Home.tsx cohort chips` | Cohort filtering supports SPUS Halal ETF constituents alongside S&P 500 and TSX cohorts. |
| **US-0607** | Islamic-finance student | learn what AAOIFI screening does and does not certify religiously | `src/api/copy.ts halalCopy` | Explicitly disclaims that halal flag is an informational calculation, not an official religious ruling. |
| **US-0608** | Dividend-focused Canadian | screen TSX names for sustainable payouts in CAD | `GET /api/v1/screen?currency=CAD & Screen.tsx` | Screens Canadian dividend payers with FCF payout ratio calculations strictly denominated in CAD. |
| **US-0612** | Big-bank comparer | compare RY, TD, BNS, BMO, CM, NA on proper bank metrics natively | `Compare.tsx & Sector.tsx?sheet=Banks` | Side-by-side comparison of Big Six Canadian banks (RY, TD, BNS, BMO, CM, NA) on bank metrics. |
| **US-0617** | Halal-portfolio planner | maintain a halal-only watchlist with the flag as an opt-in filter exactly as designed | `Screen.tsx Halal filter preset` | Opt-in halal screening filter isolates halal candidates without imposing religious filter as default. |
| **US-0622** | TSX-completer | request ingestion of any TSX name outside the 720 and get honest coverage answers | `POST /api/v1/tickers/ingest` | Accepts TSX tickers (e.g. SHOP.TO) and ingests Yahoo Finance annual statements dynamically. |
| **US-0631** | Halal-ETF comparer | compare my halal-screen results against SPUS/QQQ-halal cohort tags | `Home.tsx cohort chips & Screen.tsx` | Compares screened halal candidates against SPUS ETF cohort tags. |
| **US-0633** | Currency-purist | see the explicit rule 'never mix CAD and USD' enforced in every view | `README.md §2.1 frozen contract & allCurrency.ts` | Never mixes CAD and USD money; cross-border views operate exclusively on unitless ratios. |
| **US-0645** | Secular investor | see halal flag as informational only, never imposed | `app/services/halal.py & screen.py` | Halal status operates strictly as an optional informational tag, never a forced default filter. |
| **US-0646** | Institutional-style analyst | run sector medians separately per currency as designed | `app/api/sectors.py & sector_cache_summaries` | Sector benchmark medians computed and stored separately per currency; never blended across currencies. |
| **US-0656** | Chart minimalist | get sparkline-level context by default with full charts on demand | `src/components/viz/Sparkline.tsx & bars.tsx` | Pure SVG and CSS sparklines deliver visual trend context without heavyweight chart npm libraries. |
| **US-0660** | 52-week-context user | see the 52-week range with current position marked simply | `DerivedMetric & company_key_stats in Dossier.tsx` | Displays 52-week trading range with current price position marked as minimal context. |
| **US-0669** | Trend-skeptic | see explicit 'price is not a verdict' framing on every chart | `TradingViewChart.tsx & Dossier.tsx header` | Labels price charts with explicit note that market price is sentiment context, not an intrinsic verdict. |
| **US-0673** | Currency-aware chart viewer | see TSX charts in CAD and US names in USD natively | `TradingViewChart.tsx & Sparkline.tsx` | TSX price charts quote natively in CAD, US charts quote natively in USD. |
| **US-0694** | Long-only purist | see no intraday noise, daily closes only | `TradingViewChart.tsx timeframe config` | Configured for daily closing price bars; suppresses distracting intraday tick noise. |
| **US-0708** | Privacy-conscious user | know narration requests are cached, opt-in, and never send my personal data | `LlmCache table & app/api/chat.py` | AI narration requests are cached in SQLite and opt-in; user research habits never leave local machine. |
| **US-0709** | Truth-in-labeling user | see 'AI narration — not the score' separation maintained strictly | `NarrationPanel.tsx header banner` | Explicitly labeled 'AI Narration — not the score' to separate qualitative narration from math. |
| **US-0710** | Hallucination-wary user | get narration that can only reference data present in the local database | `chat.py grounded prompt & research_evidence` | LLM prompt injection strictly grounded on verified local database facts and 10-K filing text. |
| **US-0718** | Offline user | rely on deterministic local templates when no API is available | `src/api/copy.ts deterministic copy templates` | Deterministic local template engine generates structured explanations when offline without LLM. |
| **US-0721** | Narrative auditor | view the cache: when each narration was generated and from what data | `GET /api/v1/llm/status & llm_admin.py` | Admin router provides cache inspection, token stats, and cache invalidation controls. |
| **US-0732** | Skeptical-of-AI user | disable all narration globally and keep pure deterministic output | `NarrationPanel.tsx global toggle` | Allows disabling LLM narration globally in favor of pure deterministic quantitative displays. |
| **US-0751** | Efficiency-obsessed user | reach any company in under 3 keystrokes via persistent search | `src/components/AppShell.tsx persistent search` | Debounced search in top navbar reaches any stock in under 3 keystrokes with keyboard navigation. |
| **US-0753** | Tired-evening user | use dark 'night research desk' theme with proper contrast | `src/styles/tokens.css 'night research desk'` | Dark research desk visual theme with CSS custom properties calibrated for prolonged evening work. |
| **US-0754** | Accessibility-first user | rely on full ARIA labels on all charts and gauges | `CompositeGauge.tsx, PillarRadar.tsx, Sparkline.tsx` | Pure SVG primitives provide comprehensive aria-label attributes for screen-reader accessibility. |
| **US-0755** | Motion-sensitive user | have all animations disable under prefers-reduced-motion | `src/index.css prefers-reduced-motion & useCountUp.ts` | CSS kill-switch immediately disables transitions and count-ups when prefers-reduced-motion is active. |
| **US-0756** | Print-oriented reviewer | print any view with clean pagination | `FactsheetPrintView.tsx print media styles` | CSS @media print rules format dossiers into clean multi-page documents without table clipping. |
| **US-0757** | Slow-internet user | get fast loads from the local server regardless of connection | `Local SQLite WAL mode & Docker Compose` | Sub-50ms query response times served directly from local database regardless of internet connectivity. |
| **US-0766** | Impatient user | see skeletons and progress for any wait over 300ms | `LoadingSkeleton.tsx & Spinner in ui.tsx` | Shimmer skeletons and spinners provide immediate visual feedback for operations over 300ms. |
| **US-0772** | Colorblind user | distinguish all statuses via shapes and labels, not color alone | `Chip.tsx tone glyphs & tokens.css` | All statuses and signals reinforced with geometric glyphs (▲, ▼, ●, ■) for colorblind independence. |
| **US-0782** | Search-perfectionist | search by ticker, name, ISIN-like ID, or partial words | `app/api/dossier.py search() endpoint` | Fuzzy search resolves tickers, company names, Company_IDs, and Yahoo finance symbols. |
| **US-0790** | Privacy-paranoid user | verify zero network calls carry my research behavior | `Local Docker & offline SQLite database` | Read requests execute completely on localhost; zero analytics or tracking telemetry. |
| **US-0800** | Perfectionist-finisher | see every pixel aligned to a token system | `tokens.css & tokens.ts design system` | Every surface, border, spacing unit, and font size aligned to formal typed design token system. |
| **US-0805** | Differentiation seeker | see which unique assets (forensics, provenance, TSX, NULL-honesty) map to unmet demand | `README.md §1 & §2 Core Mission` | Architectural focus on verified differentiators: forensics, provenance, TSX depth, and NULL honesty. |
| **US-0806** | Feature-scope defender | see a 'what we deliberately won't build' list with reasons | `KEY_NOTES §4.5 'Deliberately do NOT build'` | Explicitly defines features excluded from product scope (influencer rankings, auto-trading). |
| **US-0810** | Trust-strategy writer | document the trust architecture as the core brand asset | `docs/reports/TRUST_REPORT.md` | Documents the trust architecture, source provenance, and data quality flags as core product asset. |
| **US-0821** | Compliance-planner | map disclaimer and advice-boundary requirements to every surface | `DISCLAIMER constant in config.py & UI footers` | Prominent regulatory disclaimer displayed on all API routes, UI screens, and print exports. |
| **US-0851** | Top-down investor | start from sector medians before picking names | `src/screens/SectorsHub.tsx` | Sector Explorer hub presents sector-level composite medians before drilling into individual stocks. |
| **US-0853** | Industry-map learner | browse the custom industry groupings with counts | `GET /api/v1/sectors & SectorsHub.tsx` | Lists all 48 custom industry sheets and 11 GICS sectors with constituent company counts. |
| **US-0854** | Outlier-hunter | see top and bottom 10 names per sector on any metric | `GET /api/v1/sectors/{sheet}/snapshot` | Returns top-10 and bottom-10 ranked companies within each sector peer group. |
| **US-0855** | Bank-analyst | see financials sector treated with bank-specific metrics automatically | `app/services/scoring.py bank scoring model` | Automatically routes financial institutions to regulatory bank metrics (CET1, NIM, efficiency). |
| **US-0856** | Histogram-reader | see score distributions per sector as clean histograms | `src/screens/Sector.tsx & sector_cache_summaries` | Visualizes score distribution per sector as tokenized SVG histogram with median line. |
| **US-0857** | Median-comparer | see a name against its sector median on every key metric | `PercentileMatrix.tsx in Dossier.tsx` | Positions company ratios directly against same-currency sector peer group medians. |
| **US-0859** | Currency-split analyst | see sector stats split CAD versus USD as designed | `Sector.tsx & sector_cache_summaries` | Sector benchmark medians calculated and displayed separately per currency (USD vs CAD). |
| **US-0873** | GICS-skeptic | see both GICS and custom groupings side by side | `SectorsHub.tsx tab navigation` | Provides side-by-side exploration of custom owner industry sheets and official GICS sectors. |
| **US-0878** | Sector-ETF comparer | compare sector names against their ETF cohort tags | `Company.universe_tags & Home.tsx cohort filters` | Segments sector companies across ETF cohort tags (S&P 500, TSX Composite, QQQ, SPUS). |
| **US-0889** | Fair-comparison enforcer | never see money medians blended across currencies in All view | `app/api/sectors.py & README.md §2.1` | Strict frozen contract: 'All' sector view is ratio-only; money medians are never blended across currencies. |
| **US-0902** | Score-historian | see every past score snapshot for a company | `DerivedMetric & Score tables in app/models.py` | Stores historical derived metrics and score snapshots keyed by fiscal year. |
| **US-0903** | Methodology-version watcher | see which methodology version produced each historical score | `Score.method_version in database schema` | Attaches immutable method_version (e.g. 'v1') to every computed score snapshot. |
| **US-0920** | Papers-reader | access original research papers linked from every model | `src/api/glossary.ts & SCORING_SPEC.md` | Directly cites original academic research papers for Piotroski, Beneish, Altman, and Sloan models. |
| **US-0951** | Privacy-fundamentalist | verify the app makes zero external calls with my research data | `FastAPI read-only architecture over local SQLite` | Read endpoints never initiate outbound network requests; personal research data stays on disk. |
| **US-0955** | Docker-comfortable user | manage the stack with simple commands | `docker-compose.yml & README.md §8` | Complete application stack runs via standard docker compose commands. |
| **US-0966** | Crash-recovery user | resume cleanly after power loss with WAL protection | `app/db.py SQLite WAL & busy_timeout=5000` | Write-Ahead Logging guarantees clean database recovery without corruption after power loss. |
| **US-0969** | Automation-tinkerer | script the API for my own nightly routines | `REST API surface under http://localhost:8000` | FastAPI endpoints allow local shell scripting and automated query routines. |
| **US-0981** | Test-driven operator | run the full test suite before trusting an update | `pytest (234 passed) & vitest (123 passed)` | Comprehensive test battery verifies backend and frontend integrity before updates. |
| **US-0994** | Secret-free believer | keep the system running with zero credentials | `docker-compose.yml & .env.example` | Application operates fully with zero mandatory external API keys or credentials. |
| **US-1000** | Final-peace user | trust that my life's research is safe, private, and permanent | `Local Docker + SQLite architecture` | Complete independence from cloud services ensures research archives remain safe and permanent. |

---

## Section 2: Implementable Now Stories (793 Stories)

These 793 user stories are achievable using the existing local stack (FastAPI, SQLAlchemy 2, SQLite WAL, React 18, TypeScript strict, Tailwind 3, pure SVG visual primitives) and free local/public data sources (SEC EDGAR companyfacts/submissions/Form 4, Yahoo Finance free data, existing database tables).

They are clustered into strategic Epics with development effort (**S** = 1-2 days, **M** = 3-5 days, **L** = 1-2 weeks) and research value tags (**differentiator**, **table-stakes**, **whitespace**).

### Epic 10: Guided DCF, Reverse-DCF & Valuation Sensitivity Matrix
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `M`, Story Count = `38`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0101** | D03 | Valuation learner | walk through a guided DCF with each assumption explained in plain English | intrinsic value stops being a black art. |
| **US-0102** | D03 | Assumption auditor | see every DCF driver (revenue growth, margins, discount rate) with its source and history | defaults are grounded in the company's actual record. |
| **US-0105** | D03 | Conservative valuer | run DCF scenarios at bear, base, and bull margins with a sensitivity table | downside cases are explicit before I commit. |
| **US-0106** | D03 | EPV follower | see Greenwald-style earnings power value versus market cap | reproduction-cost value anchors my floor estimates. |
| **US-0108** | D03 | Student | experiment with a valuation sandbox where changing one input shows value impact instantly | learning compounds through interaction. |
| **US-0109** | D03 | Dividend discount follower | value steady payers with a DDM view using actual payout history | income stocks get the right model. |
| **US-0111** | D03 | Skeptical valuer | get warnings when valuation inputs rely on too few historical points | thin-history valuations carry visible uncertainty. |
| **US-0113** | D03 | Scenario planner | save multiple named valuation scenarios per company with notes | my bull and bear cases persist for review. |
| **US-0114** | D03 | Valuation historian | see past years' implied expectations versus what actually happened | expectation misses teach cycles better than textbooks. |
| **US-0115** | D03 | Contrarian checker | see when price sits below EPV but quality flags are failing | cheap-for-a-reason candidates get scrutiny before excitement. |
| **US-0116** | D03 | Bank valuer | value financials with residual-income or dividend-based methods instead of FCF DCF | sector-appropriate models replace forced frameworks. |
| **US-0117** | D03 | Cyclical analyst | see mid-cycle normalized earnings used in valuation for cyclical names | peak-year earnings don't inflate intrinsic value. |
| **US-0118** | D03 | Quick estimator | get a simple 'fair multiple' view: current PE versus justified PE from growth and ROE | fast sanity checks precede deep work. |
| **US-0119** | D03 | Portfolio reviewer | export all my holdings' price-versus-value gaps as one table | portfolio-level margin of safety becomes visible. |
| **US-0120** | D03 | Educator | project a live valuation exercise for students using any real company | teaching uses the same tool students keep. |
| **US-0121** | D03 | Diligent buyer | get an alert when a watched name crosses below my saved intrinsic-value threshold | discipline executes automatically. |
| **US-0122** | D03 | Growth valuer | see reverse-DCF growth expectation decomposed into volume, price, and margin components where data permits | what the market prices becomes arguable in detail. |
| **US-0123** | D03 | DCF skeptic | see model uncertainty ranges instead of single-point fair values | false precision is designed out. |
| **US-0125** | D03 | First-principles user | see the discount-rate assumption built from risk-free rate plus equity risk premium visibly | the biggest lever is never hidden. |
| **US-0126** | D03 | Terminal-value checker | see what share of value comes from terminal assumptions | fragile valuations identify themselves. |
| **US-0128** | D03 | Impatient learner | get a 3-minute 'valuation in one screen' walkthrough with a real example | the core skill is approachable immediately. |
| **US-0129** | D03 | Value trap checker | see quality and distress flags displayed next to any 'undervalued' verdict | cheapness alone never triggers action. |
| **US-0130** | D03 | Retirement planner | see dividend-adjusted total return scenarios from current price to my horizon | long-horizon planning gets concrete. |
| **US-0131** | D03 | Note-taking valuer | attach my valuation thesis directly to the company record | assumptions live beside evidence. |
| **US-0132** | D03 | Peer-relative valuer | see where current multiples sit in the company's own 10-year range | historical valuation context is one glance. |
| **US-0134** | D03 | Model tinkerer | edit and fork built-in valuation templates | the tool adapts to my process. |
| **US-0135** | D03 | Analyst climbing the curve | see the delta between my scenario and the market-implied scenario side by side | my disagreement with the market becomes specific. |
| **US-0138** | D03 | Cash-flow purist | see FCF conversion (FCF over net income) trend before trusting earnings-based value | earnings quality gates valuation trust. |
| **US-0141** | D03 | Risk-first valuer | see required return scenarios (10%, 12%, 15%) rather than obsessing over one discount rate | humility about inputs is built in. |
| **US-0142** | D03 | Cycle-aware valuer | see where margins sit versus their 10-year range before normalizing | normalization choices are informed, not automatic. |
| **US-0143** | D03 | Detail-oriented buyer | see inventory and receivables trends flagged inside valuation notes | working-capital red flags meet the model. |
| **US-0144** | D03 | Portfolio builder | rank watchlist names by discount to my saved intrinsic values | capital allocation follows the biggest gaps. |
| **US-0145** | D03 | Show-me user | see the math rendered step by step, not just the answer | trust comes from visible arithmetic. |
| **US-0146** | D03 | Repeat user | clone last year's valuation assumptions into this year's update | annual reviews start from my own baseline. |
| **US-0147** | D03 | Skeptic of everything | see a 'ways this valuation fails' list (assumption breaks) per model | failure modes are documented. |
| **US-0148** | D03 | Income-and-growth balancer | see total-yield (dividend plus buyback) used alongside DCF outputs | capital-return view complements growth view. |
| **US-0149** | D03 | Teacher of clubs | run a valuation comparing two companies side by side for a workshop | the tool doubles as a teaching aid. |
| **US-0150** | D03 | Humble forecaster | get automatic reminder that valuation is a range with confidence levels | the tool models its own uncertainty. |

### Epic 11: Local Portfolio Ledger & Account Segmentation
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `L`, Story Count = `44`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0302** | D07 | Portfolio reviewer | see total portfolio quality/value/growth/risk pillar averages | portfolio-level research view exists, not just P/L. |
| **US-0303** | D07 | Diversification checker | see sector, geography, and currency concentration in one view | hidden concentration becomes visible. |
| **US-0304** | D07 | Canadian account organizer | group holdings by TFSA, RRSP, FHSA, and taxable accounts | placement logic and tax awareness stay organized. |
| **US-0305** | D07 | Dividend-income planner | see projected annual dividend income per account and in total | income planning runs on actual holdings. |
| **US-0306** | D07 | Position-sizing learner | record intended position size and max size before buying | sizing discipline is decided calmly, not in the moment. |
| **US-0307** | D07 | Journal keeper | append dated notes to each holding over time | the investment story stays continuous. |
| **US-0309** | D07 | Risk manager | see my largest positions' forensic flag counts together | portfolio risk review is proactive. |
| **US-0310** | D07 | Rebalancing planner | see which holdings drifted past my target bands | rebalancing cues are mechanical. |
| **US-0311** | D07 | Cost-basis realist | see unrealized gains split by account for tax-aware selling choices | tax placement is part of returns. |
| **US-0312** | D07 | Emotion-aware investor | log my confidence level at purchase and compare with outcomes later | calibration improves through evidence. |
| **US-0313** | D07 | Buy-and-hold believer | mark holdings as core or watch and keep stats separate | attention follows intention. |
| **US-0314** | D07 | Review scheduler | set a review cadence per holding and get prompted | thesis re-checks happen by design. |
| **US-0315** | D07 | Family treasurer | track the family portfolio with per-member sub-portfolios | shared stewardship stays organized. |
| **US-0316** | D07 | Sale-preparer | see holding period and gain type (short/long, Canadian treatment) before selling | tax awareness precedes the trade. |
| **US-0317** | D07 | Income retiree | see trailing twelve months of received dividends per holding | cash reality confirms the plan. |
| **US-0318** | D07 | New-money planner | see which current names offer the best value gap for fresh contributions | new savings deploy by evidence. |
| **US-0319** | D07 | Diversified-curious | see how correlated my holdings' sector fundamentals are | diversification gets tested beyond name count. |
| **US-0320** | D07 | Buyback beneficiary | see net share-count change per holding per year | my ownership slice evolution is tracked. |
| **US-0322** | D07 | Mistake archivist | record sell decisions with reasons and review them annually | lessons become systematic. |
| **US-0323** | D07 | Paper-trader | maintain a paper portfolio alongside real holdings | experimentation stays costless. |
| **US-0324** | D07 | Benchmark pragmatist | see my portfolio's pillar profile versus the index cohort's | my deviations from the market are explicit. |
| **US-0325** | D07 | Risk-budget keeper | set a max forensic-flag or distress-zone exposure for the portfolio and monitor it | risk limits become enforceable. |
| **US-0326** | D07 | Dividend-cut watcher | get alerted the moment any held name's coverage deteriorates | income threats reach me early. |
| **US-0327** | D07 | Review-proof user | generate a quarterly portfolio review document automatically | discipline gets documented. |
| **US-0329** | D07 | Holdings historian | see any past date's portfolio composition | history is reconstructable. |
| **US-0330** | D07 | Morning-checker | see a 'what changed in my holdings overnight' summary | attention focuses on changes. |
| **US-0331** | D07 | Currency-aware holder | see each holding's native currency and my exposure split | FX exposure is explicit. |
| **US-0332** | D07 | Ethical investor | tag holdings by personal values criteria and review the mix | values and portfolio stay aligned. |
| **US-0333** | D07 | Risk-parity tinkerer | see volatility estimates per holding to balance risk contributions | sizing follows risk, not price. |
| **US-0334** | D07 | Legacy planner | document intended long-term holdings with permanent notes | stewardship spans generations. |
| **US-0335** | D07 | Course-taker | practice building a model portfolio with lessons interleaved | education uses the same ledger. |
| **US-0336** | D07 | Drawdown planner | see estimated portfolio drawdown in a repeat of each holding's worst year | downside expectation is quantified. |
| **US-0338** | D07 | Yield-on-cost follower | see yield-on-cost evolution per income holding | compounding income is visible. |
| **US-0339** | D07 | New-idea gatekeeper | see how a candidate would change portfolio concentration before buying | every addition is judged in context. |
| **US-0340** | D07 | Portfolio photographer | snapshot portfolio state at any date with annotations | moments in time are preserved. |
| **US-0341** | D07 | Diligent executor | track whether I followed my own checklist per trade | process adherence is measurable. |
| **US-0342** | D07 | Crisis prepper | maintain a 'if market drops 30%' plan attached to the portfolio | pre-commitment beats panic. |
| **US-0343** | D07 | Multi-currency consolidator | see total portfolio in CAD or USD with clear conversion notes | consolidation never fakes precision. |
| **US-0344** | D07 | Silent reviewer | spend ten minutes quarterly reviewing flags, theses, and sizing without any news noise | reviewing is curated, not reactive. |
| **US-0345** | D07 | Long-game investor | see 10-year projections of dividend income under my current holdings | the future income curve motivates patience. |
| **US-0347** | D07 | Loss-tax planner | see candidates for tax-loss harvesting in Canadian taxable accounts | harvesting candidates surface seasonally. |
| **US-0348** | D07 | Concentration-braker | get warned when one position exceeds my set percentage | discipline fires automatically. |
| **US-0349** | D07 | First-portfolio builder | get guided steps to build a starter portfolio from research screens | the blank-page problem disappears. |
| **US-0350** | D07 | Whole-life tracker | include watch history, rejected ideas, and reasons in my permanent record | the full decision archive has value. |

### Epic 12: Decision Journaling, Thesis Calibration & Kill Conditions
- **Strategic Priority**: Value Tag = `whitespace`, Estimated Effort = `M`, Story Count = `5`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0301** | D07 | Long-term holder | record each buy with date, price, account type, and my thesis at purchase | my reasoning is preserved against hindsight bias. |
| **US-0308** | D07 | Thesis tester | define kill conditions at purchase and see them listed for review | pre-commitment counters rationalization. |
| **US-0321** | D07 | Turnaround holder | track original thesis tags (turnaround, quality, income) and outcome stats per tag | strategy self-knowledge grows. |
| **US-0337** | D07 | Position-closer | get a pre-sell checklist (thesis status, flags, tax) before marking a sale | exits match entry discipline. |
| **US-0950** | D19 | Wisdom-synthesizer | combine score history, base rates, and journals into annual reflections | the system produces wisdom. |

### Epic 13: Institutional Export Suite (CSV, PDF, Batch Reporting)
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `S`, Story Count = `48`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0266** | D06 | Investment-club presenter | print a clean multi-company comparison for the club vote | group decisions get a shared artifact. |
| **US-0267** | D06 | Diligent notetaker | attach verdict notes per compared name and export them | rationale travels with the comparison. |
| **US-0293** | D06 | Board-report builder | export board-ready comparison packets | professional reporting is native. |
| **US-0300** | D06 | Presentation purist | export comparisons as clean PDF one-pagers | sharing quality matches analysis quality. |
| **US-0402** | D09 | Thesis writer | draft a full research memo inside the app with auto-filled current numbers | writing and evidence share one place. |
| **US-0403** | D09 | Record keeper | export any dossier with provenance stamps as PDF | records are courtship-grade clean. |
| **US-0405** | D09 | Spreadsheet native | export statements and screens to CSV with documented column meanings | downstream Excel work stays sane. |
| **US-0406** | D09 | Club secretary | prepare meeting packets: agenda names, one-page summaries, comparisons | investment-club admin shrinks. |
| **US-0407** | D09 | Family-teacher | print beginner-friendly company explainers for teaching sessions | education materials generate themselves. |
| **US-0408** | D09 | Auditor of self | export my complete decision journal annually | self-review has real material. |
| **US-0409** | D09 | Compliance-minded advisor | produce research trails showing sources and dates for recommendations | professional standards survive audits. |
| **US-0410** | D09 | Presentation builder | export comparison charts as images for slides | my decks get native visuals. |
| **US-0411** | D09 | Note historian | see every note I ever wrote about a company in one timeline | institutional memory is personal too. |
| **US-0412** | D09 | Quarterly reporter | generate a quarterly review doc: moves, theses status, flags, income | reporting takes minutes, not evenings. |
| **US-0413** | D09 | Backup believer | export a full backup of all my data in open formats | my life's work is never locked in. |
| **US-0414** | D09 | Migration pragmatist | import transactions and notes from CSV created elsewhere | switching tools doesn't lose history. |
| **US-0416** | D09 | Data journalist | export chart data series for use in articles | facts flow to publication. |
| **US-0417** | D09 | Multi-language household | print summaries in clear simple English regardless of complexity | accessibility extends to family. |
| **US-0418** | D09 | Model builder | export cleaned historical statement datasets | quant work starts from clean inputs. |
| **US-0419** | D09 | Watchlist exporter | share a watchlist with annotations as a portable file | ideas travel between tools. |
| **US-0420** | D09 | Version archivist | keep dated exports so old analyses remain reproducible | yesterday's evidence stays authentic. |
| **US-0421** | D09 | Tax preparer | get an end-of-year package: transactions, income, account splits | tax season loses its dread. |
| **US-0422** | D09 | Milestone keeper | record portfolio milestones (first 100k, income targets) with context | the journey is documented. |
| **US-0423** | D09 | Research librarian | tag and search across all my memos and notes | my own corpus becomes searchable. |
| **US-0425** | D09 | Security-conscious user | verify exports carry no more data than intended | privacy extends to sharing. |
| **US-0426** | D09 | Template builder | design my own report templates once and reuse | formatting work happens once. |
| **US-0427** | D09 | Continuity planner | document a 'how to run this research desk' file for succession | the system outlives me. |
| **US-0428** | D09 | Verbose thinker | write long-form theses with inline metric references that auto-update | documents stay current. |
| **US-0429** | D09 | Minimalist reporter | generate a one-glance weekly summary card | light needs get light answers. |
| **US-0431** | D09 | Presentation-day user | present live from the app in presentation mode | meetings run on the real tool. |
| **US-0433** | D09 | Historian | export the full scoring-methodology version history | methodology is auditable. |
| **US-0434** | D09 | Teacher | distribute read-only research snapshots to students | classroom use is safe and simple. |
| **US-0435** | D09 | Handoff manager | package a complete research file when handing coverage to someone else | continuity survives transitions. |
| **US-0436** | D09 | Journalist | cite exact figures with source stamps in published work | accuracy is effortless. |
| **US-0437** | D09 | Curious archivist | browse my own research activity statistics | my process becomes visible. |
| **US-0438** | D09 | Diligent comparer | export multiple dossiers as a batch | bulk workflows exist. |
| **US-0439** | D09 | Screen-sharing educator | project clean high-contrast layouts for workshops | presentations look professional. |
| **US-0440** | D09 | Long-term diarist | append an annual letter to myself about the portfolio | future-me gets context. |
| **US-0441** | D09 | Data hoarder | export raw JSON of everything | no format barriers exist. |
| **US-0442** | D09 | Club archivist | maintain the club's decade of decisions in one place | institutional history lives on. |
| **US-0443** | D09 | Paranoid backer-upper | schedule automatic local backups of the database | disaster recovery is automatic. |
| **US-0444** | D09 | Format perfectionist | get exports that respect my date and number-format preferences | details stay mine. |
| **US-0445** | D09 | Research summarizer | auto-generate an executive summary from my own memo | editing starts from structure. |
| **US-0446** | D09 | Checklist executor | attach completed checklists to memos as records | process evidence is preserved. |
| **US-0447** | D09 | Multi-entity manager | separate reports per account or mandate | professional structure is supported. |
| **US-0448** | D09 | Speed-run reviewer | get a one-page 'year in review' auto-report | annual reflection is effortless. |
| **US-0449** | D09 | Open-data supporter | export datasets under open licenses to share | community benefit is possible. |
| **US-0450** | D09 | Last-mile user | print mailing-label-sized company quick-reference cards for a physical binder | analog systems integrate. |

### Epic 14: Grounded AI Narration & Balanced Dialogue Expansion
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `M`, Story Count = `39`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0701** | D15 | Overwhelmed newcomer | get a plain-English paragraph explaining what this company does and how it makes money | complexity translates on demand. |
| **US-0702** | D15 | Time-pressed user | get a 100-word verdict summary with the three strongest evidence points | the six-minute window shrinks further. |
| **US-0703** | D15 | Deep-dive reader | get an AI walkthrough of what changed in the latest filing versus prior year | changes are narrated, not just diffed. |
| **US-0704** | D15 | Skeptical reader | see every AI claim with clickable links to the underlying numbers | narratives are checkable. |
| **US-0706** | D15 | Non-native speaker | get explanations in simple language on request | clarity crosses language barriers. |
| **US-0707** | D15 | Learning-mode user | ask follow-up questions about any metric with cached local answers | dialogue deepens understanding. |
| **US-0711** | D15 | Comparison narrator | get AI comparisons of two candidates grounded in their actual numbers | relative stories stay factual. |
| **US-0712** | D15 | Earnings-morning user | get a structured 'what happened this quarter' narration | reaction time improves. |
| **US-0713** | D15 | Trend explainer | get plain-language explanations of why a pillar changed | score movements become stories with receipts. |
| **US-0714** | D15 | Cold-open user | get an instant summary when opening a company for the first time today | orientation is automatic. |
| **US-0715** | D15 | Verbose-option user | request a full multi-page narrated research brief | depth is available on demand. |
| **US-0716** | D15 | Terseness user | request bullet-only summaries | some days need 30 seconds. |
| **US-0717** | D15 | Consistency checker | compare AI narration against the deterministic copy templates for drift | two engines check each other. |
| **US-0719** | D15 | Language-learner | see technical terms auto-glossed in narration | finance vocabulary grows with use. |
| **US-0720** | D15 | Model-curious user | choose which LLM model narrates and see cost/latency trade-offs | control stays with me. |
| **US-0722** | D15 | Fiction-detector trainer | see deliberate 'spot the unsupported claim' exercises using AI output | critical AI reading is practiced. |
| **US-0723** | D15 | Board-prep user | get narration formatted as formal briefing language | professional documents start drafted. |
| **US-0724** | D15 | Child-explainer user | get 'explain like I'm twelve' versions | family teaching simplifies. |
| **US-0726** | D15 | Question-driven researcher | ask my own questions ('how exposed is revenue to one customer?') with honest 'not in data' answers when unknown | questions meet evidence or honest limits. |
| **US-0727** | D15 | Retirement narrator | get income-focused narration for dividend names | framing matches my goal. |
| **US-0728** | D15 | Speed-reader | see key sentences bolded with expandable detail | scanning works with depth available. |
| **US-0729** | D15 | Risk-narrator user | get risk sections that cite the specific forensic flags | risk talk is evidence-backed. |
| **US-0730** | D15 | Historical narrator | get 'this company's decade' narrative with real milestone data | history is narrated accurately. |
| **US-0731** | D15 | Multi-company summarizer | get a combined narration of my whole watchlist's week | portfolio-level synthesis exists. |
| **US-0733** | D15 | Analyst assistant | get narration that drafts my memo sections for my own editing | writing starts structured. |
| **US-0734** | D15 | Consistency-across-names user | get the same question answered with the same structure for any company | systematic coverage replaces ad-hoc takes. |
| **US-0735** | D15 | Curious beginner | get every jargon term in narration clickable for definition | narrations teach while informing. |
| **US-0736** | D15 | Detail-verifier | expand any narrated claim to its table row and formula | prose always bottoms out in numbers. |
| **US-0737** | D15 | Fault-injector | test narration behavior when data is deliberately missing | graceful degradation is verifiable. |
| **US-0739** | D15 | Memory-user | get narrations referencing my own past notes where relevant | personal context enriches output. |
| **US-0740** | D15 | Diligent reader | rate narrations for accuracy and see my feedback stored | quality feedback loop exists. |
| **US-0741** | D15 | Tone-preferencer | choose neutral, cautious, or curious narration tones | voice matches my temperament. |
| **US-0742** | D15 | Earnings-call follow-up user | paste management quotes and ask for comparison against the numbers | claims get checked. |
| **US-0744** | D15 | Learning-journey user | see my narration history as a learning log | progress is reviewable. |
| **US-0745** | D15 | Cost-conscious user | see token/cache statistics and keep usage minimal | resource use is transparent. |
| **US-0746** | D15 | Multi-model comparer | compare two models' answers to the same question | model differences become visible. |
| **US-0747** | D15 | Narration-skeptic tester | inject numbers manually and verify narration never contradicts the database | grounding is testable. |
| **US-0748** | D15 | Formal-writer | export narrations into memo drafts with citations intact | AI output integrates professionally. |
| **US-0750** | D15 | System-philosopher | read the narration design policy: what AI may never do here | boundaries are documented. |

### Epic 15: Canadian Market & Tax-Account Optimization (TFSA/RRSP/FHSA)
- **Strategic Priority**: Value Tag = `whitespace`, Estimated Effort = `S`, Story Count = `36`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0037** | D01 | Tax-aware Canadian | screen separately inside TFSA-eligible and non-eligible structures context | placement decisions start from research, not afterthoughts. |
| **US-0609** | D13 | Small-cap Canadian explorer | browse TSX names by custom industry with medians per industry | the smaller market gets granular tools. |
| **US-0610** | D13 | RRSP-aware investor | see US-listed holdings context for RRSP tax-treatment awareness | placement consequences surface at research time. |
| **US-0611** | D13 | FHSA planner | research qualifying investments for my first-home timeline | goal-based context joins research. |
| **US-0613** | D13 | Energy-sector watcher | analyze Canadian energy names with appropriate metrics (reserve-context where available) | sector realism applies. |
| **US-0614** | D13 | Interlisted arbitrage-curious | see interlisted names' ratio identity across exchanges | dual listings stop confusing comparisons. |
| **US-0615** | D13 | Currency-hedging decider | see FX-exposed Canadian names' revenue geography where disclosed | currency risk informs decisions. |
| **US-0616** | D13 | Quebec investor | identify Quebec-headquartered names for regional preference screening | local knowledge becomes filterable. |
| **US-0618** | D13 | Pension-conscious Canadian | screen for dividend stability suited to long retirement horizons | income durability matters at home. |
| **US-0619** | D13 | Immigrant investor | learn Canadian market structure basics inline (TSX vs TSXV, settlement) | market mechanics are taught. |
| **US-0620** | D13 | Bilingual household | read summaries in clear English with French-name recognition for Quebec companies | inclusivity extends to naming. |
| **US-0621** | D13 | Cross-listed researcher | see US and Canadian filings for dual filers in one dossier | two disclosure regimes become one view. |
| **US-0623** | D13 | Sharia-adjacent researcher | see debt-ratio and cash-ratio components historically per company | compliance trajectories are visible. |
| **US-0624** | D13 | Canadian student | study Canadian companies I recognize for learning | familiarity accelerates education. |
| **US-0625** | D13 | Preferred-share curious | see preferred-share context for Canadian issuers where applicable | the distinctive Canadian instrument gets acknowledgment. |
| **US-0626** | D13 | REIT-focused investor | analyze Canadian REITs with FFO/AFFO-appropriate metrics | sector-correct metrics apply. |
| **US-0627** | D13 | Cannabis-sector watcher | see sector names with extra forensic attention given historical accounting issues | sector history informs scrutiny. |
| **US-0628** | D13 | Mining-sector analyst | see junior producers with commodity-sensitive metrics contextualized | resource economics get fair treatment. |
| **US-0629** | D13 | Utility-income seeker | compare Canadian utilities on regulated-return metrics | the sector's own logic applies. |
| **US-0630** | D13 | Family-office Canadian | document TSX research with full provenance for governance | professional standards apply domestically. |
| **US-0632** | D13 | New-Canadian investor | start from banks and staples I know, with guided paths | entry points are familiar. |
| **US-0634** | D13 | Tax-planning Canadian | see eligible-dividend designation context for Canadian payers | after-tax income is clearer. |
| **US-0635** | D13 | Dividend-growth Canadian | track Canadian Dividend Aristocrats-style lists with coverage checks | income growth lists get local depth. |
| **US-0636** | D13 | Halal-skeptic Muslim investor | verify the flag's limits and choose deliberately | informed consent precedes reliance. |
| **US-0637** | D13 | Interlisted-fee-aware user | see spreads and listing differences for interlisted names | friction awareness improves execution. |
| **US-0638** | D13 | Regional-economy watcher | tag names by resource, manufacturing, and service economy exposure | macro themes get structure. |
| **US-0639** | D13 | Calgary-based energy worker | research within my industry knowledge for edge | professional expertise becomes investing input. |
| **US-0640** | D13 | Retired-teacher income planner | build a CAD income ladder from screened payers | income planning uses real tools. |
| **US-0641** | D13 | Young Canadian saver | start with FHSA-appropriate, lower-risk research paths | life stage meets research. |
| **US-0642** | D13 | Diaspora investor | follow names from my heritage market within a rigorous framework | connection meets discipline. |
| **US-0643** | D13 | Halal-community educator | teach screening basics using the flag's transparent methodology | community education uses honest tools. |
| **US-0644** | D13 | Cross-border retiree | manage a two-currency retirement portfolio with clear separation | bilateral retirement is supported. |
| **US-0647** | D13 | Sovereign-curious user | see Canadian government-policy exposure tags (subsidies, regulation) where documentable | policy risk gets visible. |
| **US-0648** | D13 | First-time TSX user | get a guided tour of the Canadian market layout | orientation is instant. |
| **US-0649** | D13 | Conservative Canadian | screen for low-debt Canadian compounders with long histories | temperament matches tools. |
| **US-0650** | D13 | Documentation-proud Canadian | export bilingual-aware research packages | professional artifacts stay flexible. |

### Epic 16: SEC Form 4 Insider Tracking & Disclosed Filings Engine
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `M`, Story Count = `7`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0044** | D01 | Insider-follower | screen for recent cluster insider buys (3+ buyers in 90 days) | conviction signals from people with the best information lead my list. |
| **US-0554** | D12 | Filings-first user | see insider cluster activity and 13F position changes with as-of lag labels beside social buzz | filed facts anchor the social layer. |
| **US-0584** | D12 | News-minimalist | get only filings and calendar events, never headlines | news noise is optional. |
| **US-0586** | D12 | Skeptic's toolkit user | one-click verify any social claim against filings via linked evidence | verification is frictionless. |
| **US-0590** | D12 | Institutional-curious user | see 13F changes of selected quality-focused investors with quarter-lag labels | tracking is honest about timing. |
| **US-0597** | D12 | Signal-architect | compose my own composite of filings signals with weights I choose | sophistication is available. |
| **US-0598** | D12 | Quiet-VIP user | follow only filings and insider data for privacy-critical research | sensitive research stays discreet. |

### Epic 17: Price Momentum (12-1) & Technical Context Overlays
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `S`, Story Count = `43`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0651** | D14 | Fundamentals-first investor | see a clean price history with fundamental events annotated (earnings, dividend changes) | price moves gain context without chart-clutter. |
| **US-0652** | D14 | Momentum-aware user | see the 12-1 momentum percentile computed exactly as research defines it (skipping the most recent month) | academic momentum joins my research correctly. |
| **US-0653** | D14 | Entry-point planner | see current price versus my valuation bands on a simple visual | timing serves valuation, not the reverse. |
| **US-0654** | D14 | Drawdown checker | see maximum historical drawdowns per name | pain history calibrates expectations. |
| **US-0655** | D14 | Volatility-aware user | see volatility percentile within sector | risk context is visible before position sizing. |
| **US-0657** | D14 | Reverse-checker | see how price reacted after past score-signal changes | verdict changes get empirical follow-through. |
| **US-0658** | D14 | Long-view user | see 10-year price on log scale beside 10-year revenue and EPS | price and business track together or diverge visibly. |
| **US-0659** | D14 | DCA practitioner | see my scheduled buy dates versus valuation zones on a timeline | dollar-cost averaging meets evidence. |
| **US-0661** | D14 | Reversion watcher | see distance from 200-day average as one context line | trend extremes are noted, not worshipped. |
| **US-0662** | D14 | Event-student | see past earnings-day gap sizes for this name | surprise history informs event preparation. |
| **US-0663** | D14 | Seasonal watcher | see month-by-month historical return patterns labeled as descriptive only | seasonality is visible but honest. |
| **US-0664** | D14 | Beta-curious user | see beta and correlation to index and to sector | market sensitivity joins the profile. |
| **US-0666** | D14 | Buyback-price analyst | see the price range at which the company repurchased shares | management's own entry points inform mine. |
| **US-0667** | D14 | Insider-price follower | see insider transaction prices alongside recent ranges | conviction trades get price context. |
| **US-0668** | D14 | Gap-explainer | see what fundamental data changed on big price-move days | moves attach to causes or lack thereof. |
| **US-0670** | D14 | Volatile-holder coach | see my held names' historical annual ranges to set expectations | panic is pre-empted by data. |
| **US-0671** | D14 | Multi-timeframe user | toggle 1M/1Y/5Y/MAX views instantly | every horizon is one click. |
| **US-0672** | D14 | Dividend-adjuster | see total-return (dividend-adjusted) price history by default | income-adjusted reality replaces raw price. |
| **US-0674** | D14 | Anomaly-curious user | see flags on days where price moved against significant news absence | unexplained moves get curiosity. |
| **US-0675** | D14 | Comparison chart user | overlay compared names' total returns rebased to 100 | relative performance is visual. |
| **US-0677** | D14 | Split-aware viewer | see split markers with adjusted history | history is never visually broken. |
| **US-0678** | D14 | Technical-curious fundamentalist | see just three simple overlays (SMA50, SMA200, 52w) to respect my bias | minimal technical context exists without rabbit holes. |
| **US-0679** | D14 | Volatility-event planner | see historical volatility around earnings windows | event risk is sized beforehand. |
| **US-0680** | D14 | Recovery-student | see how long past drawdowns took to recover per name | patience gets quantified. |
| **US-0681** | D14 | Range-trader-adjacent user | see simple support/resistance notes labeled as descriptive | level-watching gets honest framing. |
| **US-0682** | D14 | Position-averager | see my average cost versus price and valuation zones | averaging decisions gain context. |
| **US-0683** | D14 | Momentum-crash aware user | see warnings when momentum is extreme per research on crashes | famous momentum traps get flagged. |
| **US-0684** | D14 | Pictographic learner | see return distributions as simple bar histograms | statistical thinking becomes visual. |
| **US-0685** | D14 | Chart-sharing user | export clean chart images with annotations | sharing stays professional. |
| **US-0686** | D14 | Chart-accessibility user | navigate charts with keyboard and get textual summaries | visual data has text equivalents. |
| **US-0687** | D14 | Data-honest viewer | see charts labeled with their data vintage | charts never mix fresh and stale. |
| **US-0688** | D14 | Hypothesis tester | mark my predicted direction before revealing subsequent price | prediction practice builds calibration. |
| **US-0689** | D14 | Quiet-period user | hide all price data deliberately for a 'blind verdict' exercise | judgment isolates from anchoring. |
| **US-0690** | D14 | Crisis-student | see how this name behaved in 2008, 2020, 2022 style stress windows | crisis behavior is studyable. |
| **US-0691** | D14 | Volatility-adjusted comparer | compare names on risk-adjusted returns | return comparisons respect risk. |
| **US-0692** | D14 | First-chart learner | learn to read price charts with an interactive tutorial | chart literacy is taught. |
| **US-0693** | D14 | Earnings-anticipator | see the historical pattern of drift after earnings for this name | post-earnings behavior is empirical. |
| **US-0695** | D14 | Retro-researcher | study any past date's price with that date's fundamentals as known | honest hindsight-free study exists. |
| **US-0696** | D14 | Story-stock watcher | see narrative-driven names labeled with attention-versus-fundamentals divergence | hype decouples are visible. |
| **US-0697** | D14 | Defensive-chart user | see downside capture statistics versus index | defensiveness is quantified. |
| **US-0698** | D14 | Yield-chart user | see dividend yield history band per name | yield ranges inform entry. |
| **US-0699** | D14 | Macro-adapter | see rate-sensitivity context on rate-sensitive names | macro linkage is acknowledged. |
| **US-0700** | D14 | Final-glance user | get a one-line 'price context' summary in every dossier header | context arrives without work. |

### Epic 18: Embedded Investment Curriculum & Interactive Case Studies
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `M`, Story Count = `46`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0501** | D11 | Total beginner | take a 10-minute guided tour using a real famous company | learning happens on real data immediately. |
| **US-0502** | D11 | Book reader | see each classic book's key concepts mapped to app features (where is 'owner earnings' in this tool?) | reading turns into practice. |
| **US-0503** | D11 | Concept learner | hover any metric for a 2-minute explainer with a real example number | education is ambient. |
| **US-0504** | D11 | Skill tracker | follow a structured curriculum from 'what is a balance sheet' to 'run a forensic screen' | progression is designed. |
| **US-0506** | D11 | First-analysis completer | be walked through my first complete company analysis step by step | the first win happens on day one. |
| **US-0507** | D11 | Mistake learner | see common beginner mistakes (chasing yield, ignoring dilution) as interactive checks | pitfalls get pre-empted. |
| **US-0508** | D11 | Strategy explorer | read one-page summaries of value, quality, growth, income, and index strategies with pro/con | strategy choice is informed. |
| **US-0509** | D11 | Case-study reader | study historical case studies (a famous collapse, a famous compounder) with real data in-app | history teaches with evidence. |
| **US-0510** | D11 | Quiz taker | test myself with 'score this company' exercises against expert baselines | self-assessment is built in. |
| **US-0511** | D11 | Parent-teacher | set up a simplified learning mode for my teenager | the next generation gets a safe on-ramp. |
| **US-0513** | D11 | Skeptic-in-training | learn the limits of each model (false positive rates, decay evidence) | calibrated skepticism forms early. |
| **US-0514** | D11 | Reading-group host | follow a book-club guide that assigns app exercises per chapter | group learning has structure. |
| **US-0515** | D11 | Video-preference learner | link each concept to recommended external videos and articles | diverse learning styles are served. |
| **US-0516** | D11 | Checklist traditionalist | adopt pre-built checklists from the canon with explanations | expert process transfers. |
| **US-0517** | D11 | Confidence builder | get graduated challenges: screen, then analyze, then compare, then decide | skill builds by doing. |
| **US-0518** | D11 | Memory refresher | get periodic 'remember why this matters' micro-lessons on underused features | feature discovery is continuous. |
| **US-0519** | D11 | Terminology bilingual user | see Canadian and US terminology variations explained (RRSP vs 401k contexts) | cross-border vocabulary is handled. |
| **US-0520** | D11 | Financial-planning linker | understand how stock research fits into my larger financial plan | context prevents tunnel vision. |
| **US-0521** | D11 | Behavioral student | learn my own biases via optional judgment-tracking exercises | self-knowledge is supported. |
| **US-0522** | D11 | Depth seeker | toggle expert mode revealing advanced metrics and options | growth path exists for power users. |
| **US-0523** | D11 | Patient learner | get a 'concept of the week' tied to current market events | learning stays fresh. |
| **US-0524** | D11 | Regression learner | see worked examples of how NOT to interpret a metric (PE across sectors) | common misuse gets corrected. |
| **US-0525** | D11 | Curious retiree | attend a structured 'research desk for beginners' pathway at my own pace | age is no barrier. |
| **US-0526** | D11 | Student analyst | complete assignments: analyze a company per a rubric the app can check | coursework integrates with tooling. |
| **US-0527** | D11 | Second-language user | read plain-language explanations avoiding idiom-heavy finance speak | clarity crosses cultures. |
| **US-0528** | D11 | Math-hesitant user | see every ratio explained as a simple story before any formula | numerical anxiety is respected. |
| **US-0529** | D11 | Dashboard-overwhelmed user | start with a deliberately minimal UI and unlock sections gradually | complexity is progressive. |
| **US-0530** | D11 | Interview prepper | practice explaining metrics and models in plain language | professional readiness builds. |
| **US-0531** | D11 | Mentor | assign and review exercises for a mentee inside the app | teaching scales. |
| **US-0532** | D11 | Self-directed learner | follow interest-led paths (start from a company I like, learn what's needed) | curiosity drives structure. |
| **US-0533** | D11 | Fundamentals-first trader | learn why fundamentals matter even for short horizons | perspectives broaden. |
| **US-0534** | D11 | Bias-checker | get gentle nudges when my behavior suggests bias (overtrading watchlist, ignoring bear cases) | awareness grows with use. |
| **US-0536** | D11 | History-curious user | explore how past crises showed up in fundamentals before index crashes | macro history becomes micro-visible. |
| **US-0537** | D11 | Document reader | learn to read an actual 10-K with guided annotations | primary-source literacy grows. |
| **US-0538** | D11 | Skeptical spouse | get a neutral 'explain this analysis to a partner' summary | household communication improves. |
| **US-0539** | D11 | Lifetime learner | see my full learning history and concepts mastered | growth is visible over years. |
| **US-0540** | D11 | Community teacher | share my custom checklists and lessons with others | knowledge flows outward. |
| **US-0541** | D11 | Refresher seeker | revisit fundamentals with spaced-repetition flashcards built from real data | retention is engineered. |
| **US-0542** | D11 | Curiosity-driven user | ask 'why did this company's score drop?' and get a teaching answer | every anomaly is a lesson. |
| **US-0543** | D11 | Conservative learner | practice on paper portfolios before committing money | risk-free practice exists. |
| **US-0544** | D11 | Experienced-but-rusty user | take a fast-track refresher skipping basics | prior knowledge is respected. |
| **US-0545** | D11 | Visual learner | see concepts as annotated charts on real companies | visual explanation dominates. |
| **US-0547** | D11 | First-paycheck investor | start with small, safe, educational workflows | early habits form well. |
| **US-0548** | D11 | Retirement-focused learner | connect research skills to retirement planning decisions | purpose motivates learning. |
| **US-0549** | D11 | Curious-about-AI user | learn how the AI narration works, its limits, and how to verify it | AI literacy is included. |
| **US-0550** | D11 | Graduate | earn a completion certificate when finishing the curriculum | achievement is marked. |

### Epic 19: Keyboard Ergonomics, Command Palette & Responsive Layouts
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `S`, Story Count = `38`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0752** | D16 | Keyboard-only user | operate the entire app without touching the mouse | flow never breaks. |
| **US-0758** | D16 | Multi-monitor analyst | use wide layouts with compare-and-dossier side by side | screen real estate is respected. |
| **US-0759** | D16 | Tab-heavy user | keep many company tabs open with state preserved | parallel research is supported. |
| **US-0760** | D16 | Session-continuity user | return next day to exactly where I left off | context survives restarts. |
| **US-0761** | D16 | Habit-former | pin my daily-start screen (watchlist digest) | mornings start on my terms. |
| **US-0762** | D16 | Minimalist | hide every panel I don't use | the UI adapts to me. |
| **US-0763** | D16 | Mobile-checker | review watchlist alerts from phone-format layouts | monitoring travels. |
| **US-0764** | D16 | Fast-comparer | drag companies into the compare tray from anywhere | comparison assembly is fluid. |
| **US-0765** | D16 | Context-switcher | jump between sectors, screens, and dossiers without losing state | navigation is forgiving. |
| **US-0767** | D16 | Error-averse user | get clear, human error messages with recovery actions | failures teach next steps. |
| **US-0768** | D16 | Bookmark-heavy user | bookmark any filtered view or company state | deep links work forever. |
| **US-0769** | D16 | Title-scanner | see meaningful browser tab titles per view | multi-tab life stays organized. |
| **US-0770** | D16 | History-user | navigate back through my research trail with browser back | flow matches web conventions. |
| **US-0771** | D16 | Font-scaler | increase text size without breaking layout | vision comfort is adjustable. |
| **US-0773** | D16 | Left-handed mobile user | reach primary actions comfortably | ergonomics applies to everyone. |
| **US-0774** | D16 | Night-shift user | get warm-shift-friendly high contrast | evening eyes are considered. |
| **US-0775** | D16 | Focus-mode user | enter distraction-free single-company research mode | deep work is supported. |
| **US-0776** | D16 | Speed-run analyst | complete a full 8-name comparison in under 10 minutes through flows | professional throughput is possible. |
| **US-0777** | D16 | Data-entry-averse user | never retype anything the system knows | redundant work is eliminated. |
| **US-0778** | D16 | Undo-anxious user | undo any destructive action | mistakes are always recoverable. |
| **US-0779** | D16 | Confirmation-careful user | get confirmations only for truly destructive actions | dialogue fatigue is avoided. |
| **US-0780** | D16 | Lazy-loading skeptic | see critical content first with progressive enhancement | perceived speed is engineered. |
| **US-0781** | D16 | Big-universe scroller | virtually scroll 720-row tables smoothly | large data never jams UI. |
| **US-0783** | D16 | Typo-forgiving user | get results despite spelling mistakes | fuzzy matching saves time. |
| **US-0784** | D16 | Multi-language-future user | see the UI structured for future localization | inclusivity is architecturally ready. |
| **US-0785** | D16 | Theme-customizer | adjust accent density and contrast to taste | visual comfort is personal. |
| **US-0786** | D16 | Status-glancer | see system health (data freshness, jobs) at a glance in the header | operational state is ambient. |
| **US-0787** | D16 | Onboarding-fresh user | get a checklist-driven first-week path | early value arrives fast. |
| **US-0788** | D16 | Power-user | memorize a small set of shortcuts covering 90% of actions | efficiency has a ceiling worth reaching. |
| **US-0789** | D16 | Documentation-reader | access in-app help matching the actual UI | help never drifts from reality. |
| **US-0791** | D16 | Update-cautious user | see clear release notes on version changes | changes never surprise. |
| **US-0792** | D16 | Feature-discoverer | see contextual hints for unused-but-relevant features | depth surfaces when relevant. |
| **US-0793** | D16 | Flow-interrupt-hater | never lose form inputs to accidental navigation | state protection is total. |
| **US-0794** | D16 | Retina-display user | see crisp visuals on high-DPI screens | rendering quality is maintained. |
| **US-0795** | D16 | Older-device user | run smoothly on modest hardware | performance floor is respectful. |
| **US-0797** | D16 | Presentation-mode user | project clean views for group sessions | public display is polished. |
| **US-0798** | D16 | Watchlist-heavy user | organize hundreds of watchlist names in folders | scale organization exists. |
| **US-0799** | D16 | Cross-app worker | deep-link from notes apps into exact app states | interoperability is real. |

### Epic 1: Evidence-First Pillar UI & Methodology Drilldown
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `S`, Story Count = `58`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0051** | D02 | Trust-focused user | see every pillar score's inputs listed with its formula on hover | a 7.2 is never a mystery number. |
| **US-0052** | D02 | Beginner | read a one-sentence plain-English translation under each pillar score | I learn what quality, value, growth, and risk mean while using them. |
| **US-0053** | D02 | Diligent comparer | see how much each pillar moved since the last data refresh | score changes trace to new filings, not silent recomputation. |
| **US-0055** | D02 | Methodology auditor | open a methodology changelog showing every scoring-rule version and date | I can judge whether my old notes still apply after rule updates. |
| **US-0056** | D02 | Fact checker | click any pillar contribution to see the underlying raw values and their sources | verification takes seconds, not a separate terminal session. |
| **US-0057** | D02 | Score skeptic | see a 'what would change this verdict' list per company (specific thresholds) | I know exactly which upcoming filing could flip the signal. |
| **US-0058** | D02 | Experienced analyst | toggle between the composite score and raw pillar data view | I can form my own opinion before seeing the aggregate. |
| **US-0064** | D02 | Disagreement seeker | see where pillars conflict (high quality but expensive) called out explicitly | tensions surface instead of averaging into mush. |
| **US-0067** | D02 | Comparative learner | see my selected company's pillar bars against the sector median overlay | context replaces absolutes. |
| **US-0069** | D02 | Checklist traditionalist | see which classic checklist items each pillar covers and which it ignores | I know the score's philosophy and its blind spots. |
| **US-0070** | D02 | Careful comparer | see score stability history (how often this company's signal changed in 5 years) | flippy signals get appropriate suspicion. |
| **US-0072** | D02 | Analyst trainee | view a worked example walking through how one company's quality pillar was computed | learning happens on real numbers. |
| **US-0075** | D02 | Minimalist | choose a simple 3-band display (attractive, mixed, avoid) with depth on demand | simplicity is available without sacrificing rigor underneath. |
| **US-0076** | D02 | Score historian | see a mini timeline of pillar changes across available fiscal years | trajectory reads faster than tables. |
| **US-0077** | D02 | Cross-checker | compare my app's score for a name against its 1-year price path with a 'price is not verdict' label | I'm reminded verdicts and momentum differ. |
| **US-0079** | D02 | Peer-set skeptic | flag a peer set as unrepresentative and preview an alternative grouping | relative scores can be interrogated, not just accepted. |
| **US-0080** | D02 | Risk-aware user | see risk pillar components (leverage, coverage, volatility) each as sub-bars | risk isn't one opaque number. |
| **US-0083** | D02 | Documentation lover | open a per-pillar FAQ answering 'why is this NULL for this company' | every absence has an explanation. |
| **US-0085** | D02 | Contrarian user | sort my watchlist by 'distance from consensus-style verdict' to find debated names | controversy becomes a feature, not noise. |
| **US-0086** | D02 | Detail auditor | see the exact winsorization applied to extreme growth values | statistical plumbing is disclosed. |
| **US-0088** | D02 | Mobile checker | see the same pillar transparency in a mobile-optimized layout | depth survives small screens. |
| **US-0095** | D02 | Score archaeologist | view archived score snapshots for a company at past dates | I can study how verdicts evolved with information. |
| **US-0097** | D02 | Second-opinion seeker | see which pillar would need to change for the composite to cross into the next signal band | thresholds make the score actionable. |
| **US-0100** | D02 | System thinker | view how coverage penalties interact with pillar scores in a formula diagram | the whole model is inspectable. |
| **US-0257** | D06 | Moat comparer | compare gross-margin stability and ROIC trends across peers as moat proxies | durability differences quantify. |
| **US-0258** | D06 | Efficiency analyst | see asset-turnover and cash-conversion comparisons | operational quality ranks itself. |
| **US-0259** | D06 | Dividend comparer | compare yield, payout, growth history, and coverage across income candidates | income choices rest on full context. |
| **US-0261** | D06 | Size-aware comparer | see market-cap and float differences flagged in comparisons | scale effects are acknowledged. |
| **US-0263** | D06 | History comparer | overlay 10-year revenue and margin trajectories of compared names | paths matter as much as points. |
| **US-0264** | D06 | Footprint comparer | see geographic and segment mix side by side where disclosed | business-model overlap is checkable. |
| **US-0265** | D06 | Family-account comparer | compare candidates for one slot in my portfolio as a saved comparison | decision context persists. |
| **US-0268** | D06 | Cyclicality comparer | see each name's worst-year performance side by side | downcycle behavior differentiates. |
| **US-0269** | D06 | Management comparer | see insider ownership and capital-allocation history compared | stewardship differences surface. |
| **US-0270** | D06 | Currencysavvy expat | compare TSX and NYSE listings of similar businesses with currency-aware ratios | cross-border opportunities are fairly judged. |
| **US-0271** | D06 | Momentum checker | see 12-1 momentum percentile alongside fundamentals in comparison | price context joins fundamentals without dominating. |
| **US-0272** | D06 | Re-rating historian | see how each peer's multiple re-rated over 5 years | valuation mean-reversion gets empirical. |
| **US-0273** | D06 | Analyst-in-training | hide scores and form my own ranking, then reveal for comparison | self-testing builds skill. |
| **US-0276** | D06 | Sector-switcher | compare a company against both its narrow industry and broader sector | two lenses calibrate each other. |
| **US-0277** | D06 | Capital-intensity comparer | see capex intensity and FCF conversion compared | business-model weight classes matter. |
| **US-0278** | D06 | Turnaround comparer | compare recovery candidates on FCF inflection and flag trajectories | recoveries rank on evidence. |
| **US-0280** | D06 | Thesis A/B decider | save two competing comparisons with names like 'bet A vs bet B' and revisit after earnings | decision journals attach to artifacts. |
| **US-0281** | D06 | Spreadsheet refuser | never leave the app for a side-by-side view | the built-in comparison replaces my old spreadsheet. |
| **US-0282** | D06 | Detail maximalist | add any metric column I want to a comparison | comparison tables are user-extensible. |
| **US-0283** | D06 | Visual thinker | see radar overlays of compared names on one chart | shapes of companies compare at a glance. |
| **US-0284** | D06 | Simple-preference user | compare with plain tables and clean typography, no clutter | clarity beats dashboard cosplay. |
| **US-0285** | D06 | Retention analyst | compare employee-productivity proxies (revenue per employee) where computable | operating leverage quality is comparable. |
| **US-0287** | D06 | Long-cycle comparer | compare companies on 10-year CAGRs rather than 1-year snapshots | patience metrics lead. |
| **US-0288** | D06 | Quantitative psychologist | see how correlated the compared names' earnings are | hidden concentration reveals itself. |
| **US-0289** | D06 | Dividend-growth comparer | compare 10-year dividend CAGR and cut history | income growth quality ranks. |
| **US-0290** | D06 | Contrarian comparer | compare the market's worst performers within a quality screen | handicapped names get fair hearing. |
| **US-0291** | D06 | Capital-allocation comparer | see buyback prices versus subsequent performance per peer | repurchase skill is evaluated. |
| **US-0292** | D06 | Sector-expert builder | study every company in a niche industry via its peer map | expertise compounds within industries. |
| **US-0294** | D06 | Curious newcomer | start comparing from plain-English questions ('compare the big Canadian banks') | natural language shortcuts the mechanics. |
| **US-0295** | D06 | Diligent risk-taker | compare downside scenarios across candidates before sizing positions | position sizing follows comparison. |
| **US-0296** | D06 | Cross-checker | see each compared name's data freshness side by side | comparisons never mix fresh and stale data silently. |
| **US-0297** | D06 | Theme validator | compare every name in my custom theme on identical metrics | thematic conviction gets tested. |
| **US-0298** | D06 | Rebalancing advisor | rank holdings by pillar weakness to guide what to trim | rebalancing follows evidence. |
| **US-0299** | D06 | Simple ranker | sort the comparison by any column with one click | control stays minimal and complete. |

### Epic 20: Historical Sector Medians, Rotation & Market Structure
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `M`, Story Count = `40`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0852** | D18 | Sector rotator | see which sectors' median multiples compressed most this quarter | rotation candidates emerge from data. |
| **US-0858** | D18 | Sector-health watcher | see sector-level quality and value pillar medians over time | structural shifts surface early. |
| **US-0860** | D18 | Custom-industry curator | create and maintain my own industry groupings | classification serves my expertise. |
| **US-0861** | D18 | Sector-newcomer | get a one-paragraph primer on how this sector makes money | sector literacy builds. |
| **US-0862** | D18 | Value-sector screener | screen only within cheap sectors for quality names | top-down meets bottom-up. |
| **US-0863** | D18 | Concentration checker | see my portfolio's sector weights versus the universe | hidden bets become explicit. |
| **US-0864** | D18 | Cycle-mapper | tag sectors by cycle sensitivity (early/late/defensive) | macro positioning gets grounded. |
| **US-0865** | D18 | Competitive-landscape student | see industry member lists with comparable metrics side by side | industry structure is visible. |
| **US-0866** | D18 | Reit-specialist | see REITs grouped with appropriate metrics | sector correctness applies. |
| **US-0867** | D18 | Energy-cycle student | see energy sector's historical median margins across cycles | cycle context informs entry. |
| **US-0868** | D18 | Tech-dilution watcher | see tech sector's SBC-heavy reality flagged in sector stats | sector-level dilution is visible. |
| **US-0869** | D18 | Defensive-sector planner | identify high-quality defensive names for storm preparation | preparation uses data. |
| **US-0870** | D18 | Cross-sector value hunter | rank sectors by value pillar then dive into the cheapest | funnel efficiency exists. |
| **US-0871** | D18 | Sector-rotation historian | see how sector rankings shifted over 5 years | mean reversion in sectors is studyable. |
| **US-0872** | D18 | Custom-view builder | save sector dashboards I arrange myself | personal workflows persist. |
| **US-0874** | D18 | Sector-teaching user | teach sector analysis using live histograms | education uses real distributions. |
| **US-0875** | D18 | Peer-pressure checker | see when a name is ranked top only because peers are worse | relative claims stay honest. |
| **US-0876** | D18 | Regulatory-affected watcher | see policy-sensitive sectors tagged where documentable | regulation risk is contextual. |
| **US-0877** | D18 | Small-industry specialist | work within tiny custom industries where medians still compute | niche coverage works. |
| **US-0879** | D18 | Global-sector comparer | compare US versus Canadian sector medians | cross-border structure is visible. |
| **US-0880** | D18 | Histogram-curious user | understand why medians beat averages from the visuals themselves | statistical intuition grows. |
| **US-0881** | D18 | New-name placer | see where a newly ingested name lands in sector distributions | context arrives instantly. |
| **US-0882** | D18 | Seasonal-sector watcher | see seasonal patterns per sector labeled descriptive | timing context is honest. |
| **US-0883** | D18 | Distress-mapper | see which sectors carry most distress-zone names | systemic risk is visible. |
| **US-0884** | D18 | Quality-sector seeker | find sectors where quality medians are highest for long-hold hunting | structural quality locates. |
| **US-0885** | D18 | Sector-momentum watcher | see 12-1 momentum at sector level | top-down momentum joins. |
| **US-0886** | D18 | Barrier-to-entry student | see gross-margin stability across an industry as an entry-barrier proxy | industry economics are assessed. |
| **US-0887** | D18 | Overlapping-owner checker | see conglomerate names appearing in multiple industries handled correctly | classification edge cases work. |
| **US-0888** | D18 | Sector-median skeptic | see how many names back each median | statistical trust is earned. |
| **US-0890** | D18 | Sector-story narrator | get narrated sector overviews grounded in median data | orientation is fast. |
| **US-0891** | D18 | Bottom-up convert | discover sectors through names I researched | organic structure discovery exists. |
| **US-0892** | D18 | Watchlist-sector auditor | see my watchlist's sector spread | attention concentration is visible. |
| **US-0893** | D18 | Mean-reversion planner | favor sectors at historical-low relative multiples within quality bounds | contrarian sector timing is grounded. |
| **US-0894** | D18 | Innovation-tracker | see R&D intensity by sector where computable | future-orientation is quantified. |
| **US-0895** | D18 | Monopoly-watcher | see industry concentration proxies where computable | competitive dynamics are visible. |
| **US-0896** | D18 | Barbell-strategist | combine deep value and high quality sectors deliberately | strategy execution gets tools. |
| **US-0897** | D18 | Sector-history teacher | show students 10 years of sector medians | long view is teachable. |
| **US-0898** | D18 | Panel-preparer | prepare sector overview packets for discussions | group contexts arrive prepared. |
| **US-0899** | D18 | Cross-listed sector analyst | analyze sectors spanning both exchanges seamlessly | binational coverage works. |
| **US-0900** | D18 | Structure-curious user | read how sector statistics are computed and why | methodology reaches sector views too. |

### Epic 21: Historical Backtesting, Factor Decay & Survivorship Documentation
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `M`, Story Count = `43`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0901** | D19 | Backtest-curious user | see how a screen's rules would have performed historically with honest survivorship labels | strategy testing exists with integrity. |
| **US-0904** | D19 | Signal-follow-through analyst | see what happened to prices after past signal changes across the universe | the system's own track record is measurable. |
| **US-0906** | D19 | Hindsight-free researcher | replay the database at past dates without future data leaking | honest historical study is possible. |
| **US-0907** | D19 | Survivorship-skeptic | see universe construction documented including delisted names where available | base data honesty matters. |
| **US-0908** | D19 | Strategy-journaler | record strategy hypotheses and check outcomes later | systematic learning exists. |
| **US-0909** | D19 | Backtest-limit reader | read clear statements of what backtests here can and cannot claim | overconfidence is pre-empted. |
| **US-0910** | D19 | Regime-student | see score behavior split by market regimes where data allows | context-dependence is visible. |
| **US-0911** | D19 | Rebalancing-historian | simulate periodic rebalancing of screen results with costs labeled zero (research only) | strategy mechanics are exploreable. |
| **US-0912** | D19 | Quant-curious user | export score histories for my own analysis | raw research material is available. |
| **US-0913** | D19 | False-positive student | see historical forensic flags that did not lead to problems | model imperfection is taught. |
| **US-0914** | D19 | Hit-rate viewer | see per-model historical hit rates with confidence intervals | evidence quality is quantified. |
| **US-0915** | D19 | Overfit-detector-in-training | learn why single-number strategies decay from real examples | skepticism is educated. |
| **US-0916** | D19 | Long-memory user | see company score timelines across methodology versions side by side | evolution is transparent. |
| **US-0917** | D19 | Event-backpacker | attach major events to score timeline inflections | causes and effects are studyable. |
| **US-0918** | D19 | Strategy-comparer | compare two saved screens' historical behavior side by side | competition between ideas is fair. |
| **US-0921** | D19 | Assumption-stressor | stress historical strategies against realistic cost assumptions | fantasies deflate honestly. |
| **US-0922** | D19 | Data-vintage auditor | see which backtests used which data vintages | reproducibility is real. |
| **US-0923** | D19 | Research-replicator | reproduce published factor sorts from local data where feasible | verification culture exists. |
| **US-0924** | D19 | Curriculum-builder | assemble historical case studies into a personal course | learning paths are self-made. |
| **US-0925** | D19 | Score-evolution watcher | see how a company's composite moved as backfill added years | data arrival is visible in verdicts. |
| **US-0926** | D19 | Prediction-journaler | log explicit predictions with confidence and revisit later | calibration improves. |
| **US-0927** | D19 | Model-risk-committee-of-one | review my own reliance on each model annually | governance applies personally. |
| **US-0928** | D19 | Simulation-skeptic | prefer replay of real history over hypothetical simulation | realism dominates. |
| **US-0929** | D19 | Out-of-sample purist | see in-sample versus out-of-sample periods separated | evidence quality is visible. |
| **US-0930** | D19 | Crowding-aware user | read about factor crowding with historical unwind examples | systemic context informs. |
| **US-0931** | D19 | Version-pinning user | pin my research to specific methodology versions | reproducibility is deliberate. |
| **US-0932** | D19 | Behavioral-tracker | see my own historical verdicts versus outcomes summarized | self-knowledge is data-driven. |
| **US-0933** | D19 | Long-horizon validator | check whether quality signals held over 5+ year holds | patience is validated. |
| **US-0934** | D19 | Lesson-collector | document each year's key investing lessons with data attached | wisdom compounds deliberately. |
| **US-0935** | D19 | Backtest-boundary teacher | teach students the difference between backtest and promise | honesty spreads. |
| **US-0936** | D19 | Strategy-archivist | archive retired strategies with their full evidence | the graveyard teaches. |
| **US-0937** | D19 | Hypothesis-killer | actively seek disconfirming evidence for my favorite strategy | falsification is habitual. |
| **US-0938** | D19 | Research-calendar user | schedule annual reviews of each model's continued validity | maintenance is scheduled. |
| **US-0939** | D19 | Sample-size respecter | see confidence labels respecting actual sample sizes | small samples never overclaim. |
| **US-0940** | D19 | Anomaly-historian | study documented anomalies' life cycles from discovery to decay | intellectual history informs. |
| **US-0941** | D19 | Personal-index builder | track my own decision quality index over time | meta-performance exists. |
| **US-0942** | D19 | Curve-fitting guard | get warnings when my custom screens have too many parameters | overfitting meets resistance. |
| **US-0943** | D19 | Historical-replay educator | teach with replay-mode demonstrations | education is vivid. |
| **US-0944** | D19 | Score-interval checker | see score confidence intervals not just point estimates | uncertainty is quantified. |
| **US-0945** | D19 | Forward-stressor | apply historical stress patterns to current portfolios | preparedness is tested. |
| **US-0946** | D19 | Documentation-historian | browse the full changelog of analytical changes | every change is auditable. |
| **US-0948** | D19 | Quant-bridge builder | move from screens to systematic strategies gradually | sophistication has a path. |
| **US-0949** | D19 | Research-ethics reader | read how survivorship and lookahead are handled in every feature | methodological ethics are visible. |

### Epic 22: Local Backup, Recovery & Operational Tooling
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `S`, Story Count = `40`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0952** | D20 | Backup-ritualist | run one-click full backups to my chosen folder | disaster recovery is trivial. |
| **US-0953** | D20 | Restore-tester | restore a backup on a clean machine successfully | recovery is verified, not assumed. |
| **US-0954** | D20 | Update-cautious user | review what changed before applying updates | control stays mine. |
| **US-0956** | D20 | Resource-conscious user | see CPU/memory usage of background jobs | my machine stays responsive. |
| **US-0957** | D20 | Scheduled-maintenance user | run vacuum and integrity checks on a schedule | health maintenance is automatic. |
| **US-0958** | D20 | Data-owner | export or delete every piece of my data at will | ownership is absolute. |
| **US-0959** | D20 | Network-isolationist | run the app fully offline for months | connectivity is optional. |
| **US-0960** | D20 | Multi-machine user | move the whole research desk between machines | portability exists. |
| **US-0962** | D20 | Key-custodian | store my API keys (if any) locally with care | secrets never leave the machine. |
| **US-0963** | D20 | Log-reader | browse structured logs when diagnosing | transparency aids troubleshooting. |
| **US-0964** | D20 | Version-pinner | freeze a known-good version for stability | stability is choosable. |
| **US-0965** | D20 | Disk-space watcher | see database size growth and reclaim tools | storage stays manageable. |
| **US-0967** | D20 | Integrity-verifier | run checksum verification of the seed workbook | immutability is testable. |
| **US-0968** | D20 | Security-reader | read the threat model: what's protected and from whom | security posture is documented. |
| **US-0970** | D20 | Migration-planner | test schema migrations on a copy before applying | upgrades are safe. |
| **US-0971** | D20 | Screen-locker | lock the UI when stepping away in shared spaces | privacy extends to physical space. |
| **US-0972** | D20 | Quiet-hours operator | schedule heavy jobs for off-hours | resource use respects my day. |
| **US-0974** | D20 | Cold-standby keeper | maintain a second copy updated weekly | redundancy is practical. |
| **US-0975** | D20 | Documentation-self-sufficient user | solve problems from built-in docs alone | self-service is complete. |
| **US-0976** | D20 | Permission-minimalist | run everything without elevated privileges | least privilege applies. |
| **US-0978** | D20 | Data-retention decider | choose how long logs and caches persist | retention is configurable. |
| **US-0979** | D20 | Audit-prepared user | produce a full activity log on demand | accountability exists. |
| **US-0980** | D20 | Firewall-friendly user | know exactly which ports and hosts are involved | network behavior is explicit. |
| **US-0982** | D20 | Fail-safe designer | know what happens when each dependency fails | failure modes are mapped. |
| **US-0983** | D20 | Household-IT support | troubleshoot for family from one status page | support burden is minimal. |
| **US-0984** | D20 | Power-user operator | tune worker concurrency for my hardware | performance is tunable. |
| **US-0985** | D20 | Green-computing user | schedule work to minimize energy use | efficiency matters beyond speed. |
| **US-0986** | D20 | Longevity-planner | know the exit path: data outlives the app | future-proofing is honest. |
| **US-0987** | D20 | Sandbox-tester | experiment on a database copy without risk | experimentation is safe. |
| **US-0988** | D20 | Incident-reviewer | review any past data incident end-to-end | learning from failure is supported. |
| **US-0989** | D20 | Configuration-versioner | track my configuration changes over time | ops history exists. |
| **US-0990** | D20 | Minimal-surface user | disable every feature I don't use | attack surface shrinks. |
| **US-0991** | D20 | Trust-but-verify user | independently verify any provider data against originals | verification is always possible. |
| **US-0992** | D20 | Read-only auditor | grant an auditor pure read access | oversight is supported. |
| **US-0993** | D20 | Uptime-pragmatist | accept downtime when local, with honest status display | reliability is contextual. |
| **US-0995** | D20 | Recovery-drill scheduler | practice recovery quarterly like a fire drill | preparedness is routine. |
| **US-0996** | D20 | Backup-verifier | see backups verified automatically after creation | backups prove themselves. |
| **US-0997** | D20 | Local-AI operator | run narration models locally when available | AI works without cloud. |
| **US-0998** | D20 | Hardware-upgrade planner | move to a new PC with one documented procedure | transitions are smooth. |
| **US-0999** | D20 | Access-reviewer | periodically review who/what has access | hygiene is scheduled. |

### Epic 23: Strategy, Model Risk Register & Canon Governance
- **Strategic Priority**: Value Tag = `whitespace`, Estimated Effort = `S`, Story Count = `43`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0801** | D17 | Product strategist | see the full current-feature inventory mapped against competitor matrices | gap analysis drives the roadmap. |
| **US-0802** | D17 | Roadmap planner | get the research-backed feature list ranked by value-per-effort | prioritization starts from evidence. |
| **US-0803** | D17 | Positioning writer | draft the 'why this beats incumbents' narrative from verified differentiators | marketing starts from truth. |
| **US-0804** | D17 | Pricing researcher | review willingness-to-pay evidence across the $0–250/yr band | future monetization has a factual base. |
| **US-0807** | D17 | MVP-cutter | identify the 20% of features delivering 80% of research value | sequencing follows value. |
| **US-0808** | D17 | Quality gatekeeper | define acceptance criteria per new feature from the user-story corpus | definition-of-done is empirical. |
| **US-0809** | D17 | Data-strategy planner | map data needs (filings, prices, social) against free/local sources | no-paid-API constraint stays feasible. |
| **US-0811** | D17 | Beta-program planner | identify which user archetypes to invite first | early adopters match design targets. |
| **US-0812** | D17 | Support-planner | anticipate the top-20 questions from story frequency | support scales preemptively. |
| **US-0813** | D17 | Launch-checklist owner | derive launch-blocking items from the story corpus | readiness is measurable. |
| **US-0814** | D17 | Metrics-definer | choose product KPIs aligned with user value (time-to-verdict, alerts acted-on) | measurement serves users. |
| **US-0815** | D17 | Feedback-loop designer | plan in-app feedback capture per feature | learning loops are native. |
| **US-0816** | D17 | Ethics-reviewer | review the responsible-design commitments (no influencer ranks, no dark patterns) | values are operationalized. |
| **US-0818** | D17 | Competitor-watcher | maintain a living competitor-feature diff from this research | market awareness stays current. |
| **US-0819** | D17 | Narrative-builder | compose the product story: local-first, explainable, honest, Canadian-capable | identity crystallizes. |
| **US-0820** | D17 | Risk-registrer | document model-risk register for every scoring feature | professional governance applies. |
| **US-0822** | D17 | International-dreamer | plan universe expansion beyond 720 with cost estimates | growth has a data plan. |
| **US-0823** | D17 | Community-strategist | design how future users share checklists and screens | network effects start ethical. |
| **US-0824** | D17 | API-strategist | plan the public API surface for power users | platform thinking begins. |
| **US-0825** | D17 | Mobile-strategist | decide responsive-first versus app-shell approach pragmatically | mobile reality gets planned. |
| **US-0826** | D17 | Performance-budgeter | set load-time budgets per surface | speed is a requirement, not hope. |
| **US-0827** | D17 | Accessibility-auditor | plan WCAG-compliance verification across flows | inclusion is verifiable. |
| **US-0829** | D17 | Release-train planner | organize delivery into value-bearing increments | shipping stays continuous. |
| **US-0830** | D17 | Technical-debt governor | balance new features against infrastructure health | sustainability wins. |
| **US-0831** | D17 | Story-corpus curator | maintain the 1000-story corpus as living backlog material | research becomes backlog. |
| **US-0832** | D17 | Validation-planner | define how each hypothesis (e.g., 'base rates increase trust') gets tested | roadmap stays scientific. |
| **US-0834** | D17 | Brand-voice writer | establish the honest, no-hype voice guidelines | communication standards exist. |
| **US-0835** | D17 | Onboarding-economist | measure how fast new users reach first value | time-to-value is the growth engine. |
| **US-0836** | D17 | Retention-strategist | identify the habits (digests, reviews, journals) that create stickiness ethically | retention serves users. |
| **US-0837** | D17 | Referral-designer | plan shareable artifacts (factsheets, comparisons) as organic growth | marketing embeds in product. |
| **US-0838** | D17 | Supportbot-planner | scope AI-assisted support grounded in documentation | help scales affordably. |
| **US-0839** | D17 | Roadmap-communicator | publish the public roadmap with confidence levels | transparency extends outward. |
| **US-0840** | D17 | Ecosystem-mapper | identify adjacent tools (brokers, tax software) for integrations | position in the ecosystem is strategic. |
| **US-0841** | D17 | Scenario-planner | plan responses to competitor moves (free-tier escalation, AI bundling) | strategy is pre-lived. |
| **US-0842** | D17 | Moat-builder | deepen hard-to-copy assets: forensic suite, provenance, local-first privacy | defensibility is deliberate. |
| **US-0843** | D17 | International-expansion planner | sequence UK/Australia universes after Canada proves the model | expansion follows evidence. |
| **US-0844** | D17 | Final-arbiter | weigh every proposed feature against the mission: accurate, understandable, time-saving research | mission governs roadmap. |
| **US-0845** | D17 | Legacy-definer | articulate what this product should be in 10 years | long-term thinking anchors today. |
| **US-0846** | D17 | First-hire planner | define the role that would multiply output earliest | team scaling starts clear. |
| **US-0847** | D17 | Buyer-persona writer | document the core personas from the story corpus | design targets real people. |
| **US-0848** | D17 | Success-definer | define what success means beyond revenue (trust, accuracy, time saved) | values precede metrics. |
| **US-0849** | D17 | End-state composer | visualize the fully-realized product from all story domains | vision completes the research. |
| **US-0850** | D17 | Momentum-keeper | schedule quarterly re-review of this research for market shifts | the research stays alive. |

### Epic 2: Bessembinder Base-Rate Context & Factor Evidence
- **Strategic Priority**: Value Tag = `whitespace`, Estimated Effort = `S`, Story Count = `6`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0060** | D02 | Regime-aware investor | see a note when a pillar's historical edge is known to vary by regime (e.g., size) | I'm not over-trusting a factor in the wrong environment. |
| **US-0063** | D02 | Backtest-curious user | read a 'how has this score behaved historically' summary per pillar | I know the evidence and its decay behind each signal. |
| **US-0676** | D14 | Base-rate context user | see sector and index return context beside each name | individual performance has a reference class. |
| **US-0905** | D19 | Decay-aware user | see factor-evidence dates on every model ('this edge was documented 1976-96') | evidence aging is explicit. |
| **US-0919** | D19 | Base-rate collector | accumulate personal statistics on which signals worked for ME | personal evidence accumulates. |
| **US-0947** | D19 | Intellectual-honesty fan | see the app publish its own models' weaknesses | trust through vulnerability. |

### Epic 3: Data Trust & Provenance Inspector
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `S`, Story Count = `33`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0453** | D10 | Cross-checker | compare provider values against the original filing link in one click | discrepancies surface before they bite. |
| **US-0455** | D10 | Revision watcher | see when a provider retroactively changes a previously fetched value | silent revisions become visible events. |
| **US-0459** | D10 | Freshness checker | see a data-freshness indicator per company and per universe slice | old data announces itself. |
| **US-0460** | D10 | Skeptic of aggregates | understand how ratios were computed (which numerator, which denominator, which year) | derivation is never a mystery. |
| **US-0461** | D10 | Seed-workbook owner | see which columns came from my own curated workbook versus providers | personal curation stays authoritative. |
| **US-0462** | D10 | Error reporter | flag a suspicious number and attach evidence | the feedback loop improves the data. |
| **US-0463** | D10 | Conflict resolver | see when two providers disagree on the same metric and which wins per policy | conflict policy is explicit. |
| **US-0464** | D10 | Point-in-time purist | see values as known at a past date for honest historical study | lookahead bias is designed out of research. |
| **US-0465** | D10 | Corporate-actions watcher | see splits, ticker changes, and reorganizations reflected with dates | identity continuity is maintained. |
| **US-0466** | D10 | Coverage planner | see the universe coverage dashboard: what's filled, what's missing, what's queued | data health is a first-class view. |
| **US-0467** | D10 | Reconciliation professional | export provider-versus-filing deltas as a report | reconciliation work is half automated. |
| **US-0468** | D10 | Provenance educator | teach students to check sources using built-in provenance as the lesson | good habits form from day one. |
| **US-0469** | D10 | Audit trail requester | get a complete log of every data fetch and transformation for a company | full lineage is exportable. |
| **US-0470** | D10 | Backfill monitor | watch progress of historical backfill jobs per company with ETA | long jobs are transparent. |
| **US-0472** | D10 | Multi-provider realist | know which provider served which field and why (fallback policy) | provider priority is documented. |
| **US-0473** | D10 | Gap-filling skeptic | choose to leave gaps visible rather than accept lower-quality fills | conservatism is configurable. |
| **US-0474** | D10 | Slow-trust builder | see the system's own data-health score per provider over time | providers earn or lose trust empirically. |
| **US-0475** | D10 | Restatement guardian | get alerted when as-reported history is revised upstream | history rewrites are never silent. |
| **US-0479** | D10 | Manual-verifier | open the SEC filing at the exact section behind a filled value | manual verification takes one click. |
| **US-0481** | D10 | Perfectionist comparer | see data vintage labels when comparing companies (this one from Q3 filings, that from Q4) | as-of mismatches are visible. |
| **US-0482** | D10 | History teacher | show students how data errors propagate when sources aren't checked | the tool embodies the lesson. |
| **US-0485** | D10 | Cold-start user | ingest a brand-new ticker and see exactly which fields resolved versus missing | new-name data quality is immediate and honest. |
| **US-0487** | D10 | Silent-failure hater | get loud errors instead of empty sections when data pipelines fail | failures are never cosmetic. |
| **US-0488** | D10 | Reconciliation skeptic | see an explicit warning when comparing names with different fiscal-year ends | calendar mismatches are flagged. |
| **US-0489** | D10 | Single-source-of-truth builder | deduplicate conflicting snapshot rows with visible policy | the database stays clean. |
| **US-0490** | D10 | Time-travel researcher | browse the database as it looked on any past date | historical states are reconstructable. |
| **US-0491** | D10 | Provider-outage survivor | see graceful degradation when one provider is down, with clear labeling | outages never corrupt data. |
| **US-0492** | D10 | Family-office controller | require provenance on everything before it enters committee reports | professional standards are enforceable. |
| **US-0493** | D10 | Neurotic checker | re-verify any number with a single keystroke | verification friction is near zero. |
| **US-0495** | D10 | Error historian | browse past data incidents and their resolutions | trust is built on demonstrated repair. |
| **US-0497** | D10 | Diligent importer | see exactly what an ingest will change before running it | mutations are previewed. |
| **US-0498** | D10 | Update scheduler | choose refresh cadence per segment of the universe | freshness effort matches importance. |
| **US-0499** | D10 | Zero-trust verifier | download the original owner workbook checksum comparison | immutability is provable. |

### Epic 4: Bear Case & Pre-Mortem Counter-Weight Engine
- **Strategic Priority**: Value Tag = `whitespace`, Estimated Effort = `S`, Story Count = `29`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0074** | D02 | Devil's advocate | get an auto-generated 'case against this score' panel citing weak inputs | confirmation bias meets structured opposition. |
| **US-0553** | D12 | Contrarian monitor | see when social attention spikes while fundamentals deteriorate | divergence flags potential traps. |
| **US-0556** | D12 | Meme-stock historian | study documented squeeze case studies with the social and fundamental timelines | history teaches mechanics. |
| **US-0557** | D12 | Community learner | browse curated summaries of high-quality long-form analysis posts (DD) with attribution and links | the best of the crowd is accessible. |
| **US-0560** | D12 | Pump-and-dump guardian | see structured warnings when promotion patterns match documented manipulation playbooks | late-joiner risk gets flagged. |
| **US-0562** | D12 | Herd-aware investor | see my portfolio's overlap with heavily-socialized names | accidental herding is visible. |
| **US-0563** | D12 | Social-research student | read the actual academic evidence summaries on social-signal predictability | claims meet evidence. |
| **US-0565** | D12 | Trend watcher | see which sectors are gaining social attention week over week | attention flows map to themes. |
| **US-0569** | D12 | FOMO-resistant user | see 'this moved X% since attention spike began' context to discourage chasing | the cost of chasing is quantified. |
| **US-0570** | D12 | Diligent cross-checker | compare social sentiment extremes against quality and forensic flags | sentiment meets evidence. |
| **US-0572** | D12 | Congressional-trades watcher | see disclosed political trades where data is available | public-interest transparency is supported. |
| **US-0573** | D12 | Short-squeeze student | simulate historically how squeeze plays resolved for latecomers | mechanics beat mythology. |
| **US-0574** | D12 | Boomer-GenZ bridge user | explain social-driven names to family using neutral evidence panels | generational divides get factual bridges. |
| **US-0576** | D12 | Signal-vs-noise learner | complete a mini-course distinguishing attention, sentiment, and fundamentals | the core confusion gets resolved. |
| **US-0577** | D12 | Earnings-reaction watcher | see social reaction magnitude versus actual results divergence | crowd mood versus reality is measurable. |
| **US-0579** | D12 | Bias-checker | see a warning when I research only names that are socially popular | my own herding gets surfaced. |
| **US-0580** | D12 | Sentiment historian | browse past attention spikes and what followed | base rates on hype exist. |
| **US-0583** | D12 | Long-horizon anchor | deliberately hide all social and price signals for a 'fundamentals only' mode | my environment matches my strategy. |
| **US-0585** | D12 | Community-standards reader | read the responsible-social-data policy explaining what's shown and why | design ethics are transparent. |
| **US-0587** | D12 | Educator | teach a media-literacy module using the app's social panel | critical thinking is trainable. |
| **US-0589** | D12 | Meme-adjacent avoider | auto-flag when a holdings-list name enters viral status for review | my names' status changes reach me. |
| **US-0591** | D12 | Deplatforming-proof user | know my research doesn't depend on any social platform's availability | core workflow never breaks. |
| **US-0593** | D12 | First-impression guard | see a neutral evidence-first page before any social sentiment when opening a name | priming is minimized. |
| **US-0595** | D12 | Historical-hype user | replay famous hype cycles month by month | pattern recognition builds. |
| **US-0596** | D12 | Cross-checking parent | monitor a teen's watchlist for high-risk social-driven names together | family risk conversations start early. |
| **US-0705** | D15 | Bias-guardian | get the AI required to generate the bear case as often as the bull case | narrative balance is enforced. |
| **US-0725** | D15 | Bull-bear balancer | see both cases generated with equal rigor and length | structural balance fights narrative bias. |
| **US-0743** | D15 | Thesis-challenger | ask AI to argue against my own stored thesis | structured self-challenge exists. |
| **US-0749** | D15 | Final-check user | get a pre-purchase 'last look' narration summarizing all evidence including bear points | commitment moments get full context. |

### Epic 5: Watchlist 'What Changed' Digest & Morning Brief
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `M`, Story Count = `5`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0084** | D02 | Signal historian | get notified when a company's signal changes between refreshes | material re-ratings reach me without rechecking. |
| **US-0092** | D02 | Busy parent | get a weekly digest of pillar changes only for my watched names | I stay current in five minutes. |
| **US-0351** | D08 | Busy professional | get a single morning digest of everything material that changed across my watchlist | five minutes covers the overnight world. |
| **US-0367** | D08 | Escalation planner | set per-alert severity and channels (digest versus immediate) | signal hierarchy is mine to define. |
| **US-0377** | D08 | Post-earnings processor | get an earnings-morning view: actuals versus prior year, flags changed, score moved | reaction time improves with structure. |

### Epic 6: Local Alerts Engine & Change Detection Daemon
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `M`, Story Count = `44`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0352** | D08 | Earnings-calendar user | see upcoming earnings dates for every watched name | surprises stop ambushing me. |
| **US-0353** | D08 | Filings watcher | get alerted within minutes of a new 10-K, 10-Q, or 6-K filing for watched names | primary documents reach me first. |
| **US-0354** | D08 | Insider-activity follower | get alerted on cluster insider buys or sells with sizes | conviction signals arrive without manual checking. |
| **US-0355** | D08 | Score-change watcher | get alerted when any watched name's signal band changes | re-ratings are push, not pull. |
| **US-0356** | D08 | Dividend-calendar keeper | see ex-dividend and payment dates for income names | cash-flow planning stays current. |
| **US-0357** | D08 | Distress sentinel | get immediate alerts when any watched name enters an Altman or Beneish danger zone | deterioration gets no hiding place. |
| **US-0358** | D08 | Price-level planner | set alert levels tied to my intrinsic-value bands, not round numbers | alerts follow valuation discipline. |
| **US-0359** | D08 | Coverage-gap watcher | get told when a watched name's data refresh completes with gaps filled | backfill progress is observable. |
| **US-0360** | D08 | Volume-anomaly watcher | get flagged when trading volume deviates sharply from norms | market attention shifts surface early. |
| **US-0361** | D08 | Short-interest watcher | see short-interest updates with as-of dates and get change alerts | squeeze conditions are tracked honestly. |
| **US-0362** | D08 | Guidance watcher | get alerted on guidance changes extracted from filings | the outlook shifts that matter arrive fast. |
| **US-0363** | D08 | Buyback watcher | get alerted when buyback programs are announced, amended, or completed | capital-return events are tracked. |
| **US-0364** | D08 | Sector-event watcher | see sector-level shifts (median multiple moves) for industries I follow | context moves reach me too. |
| **US-0365** | D08 | Holder-at-risk user | prioritize alerts for names I actually own versus watch | attention follows capital. |
| **US-0366** | D08 | Quiet-hours respecter | receive alerts batched on my schedule, never 3am | the tool respects my life. |
| **US-0369** | D08 | Audit-oriented user | see a full history of every alert and what data triggered it | alert provenance is permanent. |
| **US-0370** | D08 | De-noiser | tune minimum-change thresholds so trivial moves never alert | signal-to-noise stays high. |
| **US-0371** | D08 | Calendar-first user | start my week from a combined earnings, ex-div, and filing calendar | planning anchors on dates. |
| **US-0372** | D08 | Thesis-change watcher | get alerted when a holding's pillar profile breaks my stated kill conditions | pre-commitments execute automatically. |
| **US-0373** | D08 | Macro-adjacent watcher | see rate-sensitive and cycle-sensitive tags trigger on relevant macro data where available | macro context touches my names. |
| **US-0375** | D08 | Freshness watchdog | get alerted if any watched name's data goes stale past its normal cadence | data health monitors itself. |
| **US-0376** | D08 | First-hour reviewer | get a pre-market brief of filings and events for my names in one page | mornings start synthesized. |
| **US-0378** | D08 | Multi-portfolio steward | route different alert sets to different portfolios (family, experiments) | attention segments cleanly. |
| **US-0379** | D08 | Watchlist curator | get suggestions of watched names whose research quality is poor (thin data) to prune | the watchlist stays high-quality. |
| **US-0380** | D08 | Opportunity spotter | get alerted when a high-quality name falls into my value zone | patience gets automated. |
| **US-0381** | D08 | Event-driven researcher | track special situations (spinoffs, mergers, restructurings) on my names | corporate actions get structured. |
| **US-0382** | D08 | Risk-parity watcher | see alerts that materially change my portfolio's risk concentration | portfolio-level triggers exist. |
| **US-0383** | D08 | Learning-mode user | get one 'concept in the news' explainer tied to my watchlist daily | education rides real events. |
| **US-0384** | D08 | Data-trust auditor | get notified when provider data conflicts with prior values beyond tolerance | revisions never slip in silently. |
| **US-0386** | D08 | Diligent AGM attendee | see AGM and special-meeting dates with proxy links | governance participation stays possible. |
| **US-0387** | D08 | Quiet-name watcher | follow thinly covered names where filings are the only news | small-cap coverage works anyway. |
| **US-0388** | D08 | Momentum-aware holder | get flagged when 12-1 momentum turns negative on quality holdings | trend shifts reach fundamental investors. |
| **US-0389** | D08 | Pattern-completer | get notified when a watched name completes a multi-year pattern I defined (e.g., margin recovery) | complex conditions are watchable. |
| **US-0390** | D08 | Peace-of-mind user | know alerts come from local data with no external service reading my portfolio | privacy survives vigilance. |
| **US-0391** | D08 | Seasonal planner | see seasonally recurring events (dividend raises, sector patterns) | the calendar's rhythm becomes an asset. |
| **US-0392** | D08 | Retention user | see which alerts I actually act on and prune the rest | alert effectiveness is measurable. |
| **US-0393** | D08 | Team lead | share alert definitions across a small research group | collaboration starts with shared triggers. |
| **US-0394** | D08 | Context keeper | see the related research note attached when an alert fires | alerts arrive with their story. |
| **US-0395** | D08 | Gradual-accumulator | get scheduled buy-window reminders per my DCA plan | discipline runs on rails. |
| **US-0396** | D08 | Bankrupt-or-bought watcher | track corporate actions that would end a holding (acquisition, delisting) | endings never surprise. |
| **US-0397** | D08 | Threshold philosopher | document why each alert threshold is what it is | my own rules stay inspectable. |
| **US-0398** | D08 | Wrap-up user | get an end-of-week 'nothing changed on 14 of 16 names' confirmation | silence gets confirmed on purpose. |
| **US-0399** | D08 | Beta-tester | see a preview of upcoming alert types and opt in early | the alert system evolves with me. |
| **US-0400** | D08 | Final-line user | get a fail-safe weekly heartbeat proving monitoring is alive | monitoring monitors itself. |

### Epic 7: Screener Presets & Advanced Multi-Metric Filtering
- **Strategic Priority**: Value Tag = `table-stakes`, Estimated Effort = `M`, Story Count = `28`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0001** | D01 | Beginner | start with a guided 'pick a strategy' wizard instead of a blank filter grid | I can get a sensible shortlist without knowing which metrics matter yet. |
| **US-0003** | D01 | Dividend investor | filter for 10+ consecutive years of dividends with payout ratio under 60% | survivors are genuinely sustainable payers, not yield traps. |
| **US-0005** | D01 | GARP investor | screen for PEG below 1.0 with positive FCF margin and net cash | growth at a reasonable price candidates appear without manual spreadsheet work. |
| **US-0007** | D01 | Quality seeker | screen for gross profitability (GP/Assets) in the top quartile of sector | I start from businesses with proven unit economics like Novy-Marx research suggests. |
| **US-0009** | D01 | Busy professional | save a custom screen as a preset with a one-word name | I rerun my Monday routine in one click instead of rebuilding filters. |
| **US-0010** | D01 | Quant tinkerer | combine up to ten filter criteria with AND/OR logic and see match counts update live | I can experiment with factor ideas interactively. |
| **US-0011** | D01 | Retiree | screen for low debt-to-EBITDA and interest coverage above 8x | the names I see can survive higher-rate environments. |
| **US-0012** | D01 | Financial advisor | export any screen result with the filter definition embedded in the file | my compliance trail shows exactly how the list was produced. |
| **US-0014** | D01 | Journalist | screen for companies with SBC dilution above 3% per year despite buybacks | I can investigate firms whose per-share growth hides dilution. |
| **US-0016** | D01 | Momentum-curious | filter for 12-1 price momentum percentile within sector alongside quality checks | I explore momentum the academically supported way, skipping the most recent month. |
| **US-0020** | D01 | Small-cap explorer | screen by market-cap band and flag names with thin analyst coverage | I find neglected names before the crowd. |
| **US-0021** | D01 | Turnaround watcher | screen for negative earnings but positive and rising free cash flow | I see potential recoveries the income statement alone would hide. |
| **US-0022** | D01 | Parent teaching kids | save a 'boring great businesses' preset with high ROE and low debt for our weekend sessions | lessons use real, understandable companies. |
| **US-0025** | D01 | Growth investor | screen for 3-year revenue CAGR above 15% with gross margin stability | growth candidates are filtered for durability, not just speed. |
| **US-0028** | D01 | Contrarian | screen for names in the bottom decile of 12-month performance but top half on F-Score | statistically supported beat-down candidates appear for review. |
| **US-0030** | D01 | Excel-first analyst | export screen results to CSV with formula-transparent columns | I can continue work in spreadsheets without re-deriving numbers. |
| **US-0031** | D01 | First-time user | see example questions on the empty screen page ('show me safe dividend payers') | the empty state teaches instead of dead-ending. |
| **US-0033** | D01 | Income investor | screen for dividend coverage using FCF payout rather than accounting EPS payout | the yield I buy is backed by cash, not accruals. |
| **US-0034** | D01 | Moat follower | filter for companies with ROIC above cost of capital for 5+ years | compounding machines with real moats anchor my list. |
| **US-0035** | D01 | Cyclical watcher | screen cyclicals on mid-cycle margins instead of current-year peaks | I don't mistake peak earnings for sustainable power. |
| **US-0038** | D01 | Pattern learner | see 'why these matched' summary stats (median PE, score spread) above results | I learn what my filter actually selected, not just rows. |
| **US-0039** | D01 | Speed reader | get screen results with inline sparkline of 5-year revenue | the shape of the business is visible without opening each dossier. |
| **US-0041** | D01 | Checklist investor | run a screen that scores each result against the book checklists (Graham, Lynch, Fisher) | strategy alignment is visible per name. |
| **US-0042** | D01 | Weekend researcher | queue a screen to run after the weekly data refresh completes | Saturday morning always starts with fresh results. |
| **US-0046** | D01 | Theme investor | screen by custom tags I assign (AI supply chain, uranium, payments) | my own market themes become reusable filters. |
| **US-0047** | D01 | Portfolio completer | screen for names uncorrelated with my largest holding's sector and geography | new ideas actually diversify what I already own. |
| **US-0048** | D01 | Conservative compounder | screen for 10-year revenue CAGR above 5% with max drawdown years under 10% | steady growers replace lottery tickets on my list. |
| **US-0049** | D01 | Screen perfectionist | get a warning when a filter combination matches zero names due to NULL data rather than true emptiness | empty results are explained, not misleading. |

### Epic 8: Consolidated Forensic Red Flags Workspace & Shenanigans Engine
- **Strategic Priority**: Value Tag = `differentiator`, Estimated Effort = `M`, Story Count = `42`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0018** | D01 | Forensic hobbyist | screen for receivables growing faster than revenue for two straight years | potential aggressive revenue recognition candidates surface early. |
| **US-0027** | D01 | ESG-curious investor | screen for companies with no goodwill exceeding 40% of assets | I avoid serial overpayers whose balance sheets hide impairment risk. |
| **US-0045** | D01 | Diligent avoider | exclude names with auditor changes or going-concern language in the last year | known red flags never sneak into candidates. |
| **US-0202** | D05 | Short-seller student | see a Hindenburg-style first-pass checklist (related-party signals, revenue recognition, auditor changes) per company | professional skepticism is systematized. |
| **US-0209** | D05 | Historical pattern learner | see what Beneish and Altman scores looked like for famous collapses (Enron-era examples) before their failures | the models' real behavior calibrates trust. |
| **US-0210** | D05 | Audit-quality skeptic | see auditor name, tenure, and any changes or opinions notes per year | audited never silently means safe. |
| **US-0211** | D05 | Benford-curious user | see a first-pass Benford's Law digit test on reported figures where feasible | statistical irregularity screening becomes accessible. |
| **US-0212** | D05 | Insider-timing watcher | see insider selling clustered before guidance cuts flagged in the forensic view | behavioral evidence complements accounting evidence. |
| **US-0213** | D05 | Red-flag tracker | get a consolidated red-flag count and severity per company | overall skepticism level is quantified. |
| **US-0214** | D05 | DD writer | export a forensic section with every flag, value, and threshold for my due-diligence doc | my writeups cite exact numbers. |
| **US-0215** | D05 | Related-party watcher | see disclosures about related-party transactions summarized per year | self-dealing risk gets surface area. |
| **US-0216** | D05 | Revenue-quality hunter | see DSO trend plus channel-stuffing indicators (receivables vs revenue divergence) | classic manipulation patterns are monitored. |
| **US-0217** | D05 | Margin-anomaly hunter | see flags when margins diverge wildly from peer medians without explanation | outliers attract scrutiny first. |
| **US-0218** | D05 | Going-concern watcher | get flagged immediately when going-concern language appears in any filing | existential risk never waits for me to find it. |
| **US-0220** | D05 | Pension-flag watcher | see pension underfunding warnings in the forensic panel | balance-sheet time bombs get visibility. |
| **US-0221** | D05 | Score-threshold learner | see exactly why a company crossed from grey zone into distress (which variable moved) | thresholds teach rather than just classify. |
| **US-0222** | D05 | Cross-model comparer | see Beneish, Altman, and Ohlson side by side with their disagreement noted | multiple lenses beat one. |
| **US-0223** | D05 | Case builder | annotate forensic flags with my own notes and evidence links | investigations accumulate in one place. |
| **US-0224** | D05 | Watchful holder | get re-alerted when any forensic flag appears on a company I own | deterioration reaches me between annual reviews. |
| **US-0226** | D05 | Meme-stock avoider | see pump-and-dump style red flags (promotion spikes, listing changes) alongside fundamentals | manipulation-adjacent names get caution labels. |
| **US-0227** | D05 | Historian of frauds | browse a learning gallery of documented fraud cases mapped to which flags they would have triggered | education runs on real history. |
| **US-0228** | D05 | CFO-analyst | see cash conversion cycle trend with forensic interpretation notes | operational cash reality is tracked. |
| **US-0229** | D05 | Cross-border comparer | see which forensic models are validated for Canadian filers versus US-only | model applicability is disclosed. |
| **US-0230** | D05 | Journalist | pull a company's full forensic timeline as a structured export | investigative writing starts from data. |
| **US-0231** | D05 | Paranoid-but-systematic user | set forensic thresholds I personally care about and get custom flagging | my risk appetite tunes the alarms. |
| **US-0232** | D05 | Complex-structure avoider | see complexity flags for multi-layer holding structures and heavy intercompany items | opacity itself gets flagged. |
| **US-0233** | D05 | Inventory watcher | see inventory growth versus sales growth with divergence flags | channel stuffing and obsolescence surface. |
| **US-0234** | D05 | Capitalization watcher | see flags when costs move from expensed to capitalized between years | accounting-choice shifts get caught. |
| **US-0235** | D05 | Debt-covenant watcher | see covenant pressure indicators where disclosures allow | distress spirals start with covenants. |
| **US-0236** | D05 | Regulatory-risk tracker | see investigations, settlements, and regulatory actions summarized per company | legal overhang is always visible. |
| **US-0238** | D05 | Quiet-quality hunter | screen for zero red flags plus high F-Score as my 'clean compounders' list | cleanliness becomes a screenable asset. |
| **US-0239** | D05 | Buy-here-first-timer | get a plain-language 'what could go wrong' summary generated from flags | risk reading is approachable. |
| **US-0240** | D05 | Conservative fiduciary | document forensic due diligence per holding for my board or family office | governance duties get tool support. |
| **US-0241** | D05 | Earnings-call cross-checker | compare management's narrative claims against flag trajectories | story versus numbers tension is visible. |
| **US-0242** | D05 | Delisted-case student | see how flags behaved for companies that later delisted or were acquired | model behavior on true positives teaches calibration. |
| **US-0243** | D05 | High-yield chaser | run forensics before chasing any double-digit yield | the trap check precedes the yield grab. |
| **US-0244** | D05 | Serial-acquirer tracker | see acquisition cadence and goodwill accumulation flagged | empire-building risk is visible. |
| **US-0245** | D05 | Restatement historian | see whether past figures were later restated with before/after values | data integrity history is permanent. |
| **US-0246** | D05 | Forensic educator | use the suite to teach a university accounting module with live companies | practice and theory share one tool. |
| **US-0247** | D05 | Turnaround evaluator | see whether improving results coincide with falling manipulation flags | recoveries verify through multiple lenses. |
| **US-0249** | D05 | Risk-manager | rank my entire portfolio by forensic flag severity | the riskiest holding gets attention first. |
| **US-0555** | D12 | Short-interest watcher | see SI% float and days-to-cover with twice-monthly staleness dates clearly marked | squeeze context is honest about lag. |

### Epic 9: As-Filed vs As-Restated Reporting & Financials History
- **Strategic Priority**: Value Tag = `whitespace`, Estimated Effort = `M`, Story Count = `38`

| Story ID | Domain | Persona | User Want | Verifiable Benefit |
|---|:---:|---|---|---|
| **US-0152** | D04 | Trend reader | see revenue, margins, and FCF as synchronized multi-year charts | the business's shape emerges visually. |
| **US-0155** | D04 | Growth decomposer | see revenue growth split into volume, price, and mix commentary where disclosures allow | growth quality gets parsed, not just measured. |
| **US-0156** | D04 | Margin forensics user | trace gross, operating, and net margin trajectories with inflection markers | deterioration shows up before headlines. |
| **US-0157** | D04 | Working-capital watcher | see receivables, inventory, and payables days plotted over time | cash conversion stories are visible. |
| **US-0158** | D04 | Dilution tracker | see share count history with buybacks and issuance annotated | per-share math starts with honest share counts. |
| **US-0159** | D04 | Capex analyst | see maintenance versus growth capex estimates side by side | owner-earnings calculations get real inputs. |
| **US-0161** | D04 | Restatement watcher | see as-originally-reported versus as-restated toggles when restatements exist | history never gets silently rewritten. |
| **US-0162** | D04 | Segment analyst | view revenue and profit by segment where filings provide them | the parts explain the whole. |
| **US-0163** | D04 | Seasonality student | compare quarterly patterns across years with a seasonality strip | timing effects stop masquerading as trends. |
| **US-0164** | D04 | FX-aware analyst | see which portion of revenue is foreign-currency exposed where disclosed | currency risk enters statement reading. |
| **US-0166** | D04 | Debt mapper | see debt maturity and composition (fixed versus floating) where disclosed | refinancing risk is concrete. |
| **US-0167** | D04 | Pension and obligation checker | see pension funded status and lease obligations summarized | hidden liabilities surface in one place. |
| **US-0168** | D04 | Goodwill skeptic | see goodwill versus tangible assets trend with impairment history | overpayment legacies are quantified. |
| **US-0169** | D04 | R&D follower | see R&D spend capitalized versus expensed treatment notes | innovation accounting stops distorting comparisons. |
| **US-0170** | D04 | Dividend historian | see every dividend declaration, special, and cut across the company's history | income reliability is documented. |
| **US-0171** | D04 | Shareholder-letter reader | access links to original filings and annual letters per year | primary sources are always one click away. |
| **US-0172** | D04 | Detail verif Rider | open the exact filing page (accession, page) behind any number | verification is native, not external. |
| **US-0173** | D04 | Comparative historian | place the company's 10-year record beside its top-3 peers on one screen | relative history beats isolated history. |
| **US-0174** | D04 | Accounting-policy watcher | see notes on revenue recognition and policy changes between years | apples-to-apples reading is informed. |
| **US-0176** | D04 | Export-oriented analyst | download the full statement history as clean CSV | my own models consume clean inputs. |
| **US-0177** | D04 | Chart minimalist | toggle tables to compact sparklines when surveying many names | overview mode respects attention. |
| **US-0178** | D04 | Student of cycles | overlay statement history with recession and rate-cycle markers | context explains turns. |
| **US-0180** | D04 | Quarterly-to-annual reconciler | see TTM versus fiscal-year deltas explained | interim noise is decodable. |
| **US-0181** | D04 | Forensic scout | see automatic highlight of lines that deviate sharply from their 5-year norm | anomalies announce themselves. |
| **US-0182** | D04 | Cash conversion analyst | see FCF margin, ROIC, and asset turns trended together | capital efficiency has a dashboard. |
| **US-0183** | D04 | Inflation-aware analyst | view revenue in real terms using CPI adjustment as an option | nominal illusions get an antidote. |
| **US-0184** | D04 | Parent-teaching moment | walk through a simple company's statements with guided annotations | family investing lessons use real reports. |
| **US-0186** | D04 | Small-print reader | expand footnotes inline without leaving the statement view | context lives where the number is. |
| **US-0187** | D04 | Efficiency hunter | see asset-turnover and inventory-turnover trends versus peers | operational quality is comparable. |
| **US-0188** | D04 | Debt-burden comparer | see net-debt-to-EBITDA trajectory versus sector median | leverage context is immediate. |
| **US-0191** | D04 | Insurer specialist | see combined ratio and float metrics for insurers as primary lines | insurance economics get native metrics. |
| **US-0194** | D04 | Anomaly chaser | get flagged when a margin jumps without revenue explanation | unexplained improvement gets scrutiny. |
| **US-0195** | D04 | Presentation-sensitive user | print the full statement history in a clean ledger format | paper review remains excellent. |
| **US-0196** | D04 | Multi-company lecturer | pull three companies' statements into one synchronized view for teaching | comparison teaching is friction-free. |
| **US-0197** | D04 | Skeptical comparer | normalize one-off items (restructuring, impairments) with a toggle | adjusted views are explicit and reversible. |
| **US-0198** | D04 | Early-retirement researcher | focus on FCF stability metrics across 10 years | income durability is the lens. |
| **US-0199** | D04 | Revenue-quality analyst | see deferred revenue and backlog trends where disclosed | forward visibility is part of quality. |
| **US-0200** | D04 | Trend forecaster | see simple extrapolation bands on key lines labeled as mechanical, not predictions | projection is honest about being naive. |

---

## Section 3: Deferred / Blocked Stories (36 Stories)

These 36 user stories cannot be implemented in the current local phase due to external paid API subscriptions, cloud multi-user infrastructure requirements, or direct conflicts with frozen contracts (README §2).

| Story ID | Domain | Persona | User Story Capability | Blocker Reason (Frozen Contract / Paid API / Cloud) | Cheapest Legitimate Future Path |
|---|:---:|---|---|---|---|
| **US-0043** | D01 | Options-curious investor | overlay short interest and days-to-cover on screen results | Requires commercial/paid short interest data feed (Ortex / S3 Partners / FINRA paid feed). | Parse free bi-monthly FINRA equity short interest text dumps into local SQLite table. |
| **US-0090** | D02 | Rule tinkerer | preview how my proposed weight changes would re-rank a saved list | Conflicts with frozen contract README §2.6: 'Scoring weights are locked... you may NOT change the locked composite weights'. | Implement sandboxed 'what-if' custom factor simulator strictly isolated from official scores. |
| **US-0094** | D02 | Long-horizon investor | weight my displayed pillars toward quality and risk via a saved preference | Conflicts with frozen contract on locked composite weights (0.30 Q, 0.25 V, 0.25 G, 0.20 R). | Support view-only column sorting preference without altering composite scoring math. |
| **US-0137** | D03 | Consensus comparer | see analyst consensus targets alongside intrinsic ranges when available | Requires commercial/paid consensus analyst estimate feed (FactSet / Refinitiv / S&P Capital IQ). | Scrape free Yahoo Finance consensus price targets into company_key_stats table. |
| **US-0328** | D07 | Accountant-friendly user | export all transactions with clean columns | Requires commercial bank aggregation API (Plaid / SnapTrade) and cloud credential vault. | Provide standard OFX / CSV brokerage transaction import/export. |
| **US-0346** | D07 | Account migrator | record transfers between accounts with cost-base continuation | Requires cloud multi-tenant database synchronization infrastructure. | Support local JSON/CSV export and import for transferring portfolios between computers. |
| **US-0368** | D08 | Cross-device user | see alerts acknowledged and synced everywhere | Requires cloud push notification infrastructure (Apple APNs / Google FCM / web push server). | Use local browser Notification API and desktop system tray notifications. |
| **US-0374** | D08 | Meme-attention watcher | see social-attention spikes on watched names labeled 'attention, not endorsement' | Requires paid commercial social sentiment firehose (Twitter Enterprise / StockTwits Enterprise). | Detect trading volume spikes from free Yahoo Finance daily volume data. |
| **US-0385** | D08 | Sell-side skeptic | track analyst estimate changes and their historical accuracy for my names | Requires paid sell-side consensus revision feeds (FactSet / Refinitiv IBES). | Track SEC 8-K guidance updates and free Yahoo revision disclosures. |
| **US-0424** | D09 | Email preferencer | email myself any report for records | Requires outbound SMTP server or cloud transactional email service (SendGrid / Postmark). | Generate PDF reports directly to local downloads folder with print shortcut. |
| **US-0430** | D09 | Cross-tool user | push watchlists to my broker app via standard formats | Requires proprietary broker trading APIs and order-routing infrastructure. | Support standardized CSV / JSON watchlist export formatted for major broker imports. |
| **US-0551** | D12 | Curious observer | see Reddit mention volume for a stock with a 1-year price overlay and 'attention is not endorsement' labeling | Requires paid Reddit Data API subscription tier ($0.24 per 1k requests). | Query free Google Trends RSS for ticker attention proxies. |
| **US-0552** | D12 | Sentiment skeptic | see bull/bear tag ratios with sample sizes and timestamps | Requires paid StockTwits Enterprise or Twitter API Enterprise ($42k/yr). | Utilize crowdsourced Estimize public web scraper if legally compliant. |
| **US-0559** | D12 | Earnings-expectation tracker | see crowdsourced versus analyst estimates side by side where available | Requires commercial Estimize API enterprise license. | Rely on historical earnings beat/miss disclosures from SEC 10-Q/10-K filings. |
| **US-0561** | D12 | Influencer skeptic | never see influencer recommendations ranked as signals, only as attributed quotes with track-record context | Violates frozen contract & Research §4.5: 'Deliberately do NOT build influencer-ranking signals'. | Surface documented research citations only with academic author attribution. |
| **US-0564** | D12 | Options-flow curious user | see unusual options activity with context on interpretation risk | Requires paid OPRA / CBOE options flow streaming data feed ($500+/mo). | Deliberately excluded per Research §4.5 (day-trading features out of mission). |
| **US-0567** | D12 | Community contributor | share my own research memos publicly with provenance-rich exports | Requires hosted public web application server and public community database. | Export standalone HTML / PDF dossier packets for manual sharing. |
| **US-0568** | D12 | Discussion moderator | moderate a small research group with shared watchlists and memos | Requires cloud multi-user account management and permissions backend. | Keep application local-first single-user; export shareable encrypted research archives. |
| **US-0571** | D12 | Alternative-data tinkerer | see available alt-data series (web traffic, app rankings) with source and collection-lag labels | Requires paid alternative data feeds (SimilarWeb / App Annie / Sensor Tower at $10k+/yr). | Extract official segment customer and geographic revenue from SEC 10-K disclosures. |
| **US-0575** | D12 | Reddit-lurker | see WSB daily thread highlights for my watchlist without leaving the app | Requires paid Reddit Data API commercial license. | Perform full-text regex searches over local SEC 10-K Risk Factors filings. |
| **US-0578** | D12 | Cooperative researcher | pool anonymized screens with my club to compare member hit rates | Requires cloud multi-tenant database synchronization and live peer networking. | Support export and import of screener preset JSON definition files. |
| **US-0581** | D12 | Alt-score skeptic | see that composite social scores (like AltIndex-style) are labeled as unvalidated methodology | Requires commercial alternative data aggregator subscription (AltIndex / Thinknum). | Build derived signals strictly from filed SEC facts and Yahoo Finance data. |
| **US-0582** | D12 | Quant-curious user | export social-signal series for my own analysis | Requires commercial social sentiment data feeds. | Export historical SEC Form 4 insider transaction time-series. |
| **US-0588** | D12 | Earnings-season socializer | see attention heatmaps around earnings dates | Requires paid real-time social attention firehose. | Construct trading volume anomaly heatmaps from free historical Yahoo volume. |
| **US-0592** | D12 | Community-comparison user | see how my verdicts compare with community consensus distributions | Requires centralized cloud community voting database. | Display academic baseline distributions from published financial literature. |
| **US-0594** | D12 | Thoughtful follower | subscribe to specific high-quality contributors' long-form pieces only | Requires cloud content publication and user subscription infrastructure. | Integrate local RSS feed reader for curated financial blogs and research feeds. |
| **US-0599** | D12 | Deliberate contrarian | get alerted when consensus social mood reaches extremes on quality names | Requires paid real-time sentiment stream. | Trigger contrarian alerts from valuation expectations gap and valuation percentiles. |
| **US-0665** | D14 | Liquidity checker | see average dollar volume for position-size feasibility | Requires paid NASDAQ / OPRA Level 2 market data streaming feed ($1,000+/mo). | Calculate average daily dollar trading volume from free Yahoo historical price data. |
| **US-0738** | D15 | Podcast-style learner | listen to narrated summaries via TTS | Requires paid AI voice synthesis API (ElevenLabs / OpenAI Audio API). | Use client-side in-browser Web Speech API (window.speechSynthesis) for offline audio. |
| **US-0796** | D16 | Household-shared user | keep separate profiles per family member | Requires multi-tenant user authentication and session management backend. | Implement client-side localStorage profile switcher for local family profiles. |
| **US-0817** | D17 | Future-monetizer | tag which features could tier later without breaking the free core | Application is strictly personal equity-research software; commercial paywalls conflict with mission. | Document future subscription tier specifications in architectural backlog. |
| **US-0828** | D17 | Data-vendor evaluator | evaluate when paid data would become necessary and what it would unlock | Conflicts with frozen contract README §2: 'no paid APIs in v1'. | Audit commercial data vendors only when scoping potential future v2 commercial version. |
| **US-0833** | D17 | Pricing-simulator | model free/paid tier boundaries against competitor value anchors | Requires payment gateway integration (Stripe / LemonSqueezy) and subscription billing engine. | Maintain free open local-first core architecture. |
| **US-0961** | D20 | Family-admin | give family read-only access without exposing write powers | Requires multi-user RBAC and permission management service. | Use basic HTTP auth reverse proxy in Nginx for simple local network read access. |
| **US-0973** | D20 | Alert-delivery purist | receive alerts through local channels only | Requires custom physical IoT hardware beacon integration. | Trigger desktop system notifications using standard Web Notifications API. |
| **US-0977** | D20 | Certificate-cautious user | understand local HTTPS setup for sensitive contexts | Local HTTPS setup is unnecessary and complex for desktop localhost Docker setup. | Document self-signed mkcert certificate generation in Docker reverse proxy docs. |

---

## Section 4: Proposed Wave 1 Scope & Implementation Plan

### Strategic Objective
As recommended in `KEY_NOTES_Market_Research_and_Recommendations.md` §8:
> **Wave 1 — Visibility of what exists:** Evidence-first pillar UI (click-through inputs/formulas/percentiles); provenance made loud; base-rate panel. *Why first:* Pure presentation over existing data; instant differentiation.

The goal of Wave 1 is to extract massive research value from the rich fundamentals already stored in SQLite (`financial_snapshots`, `derived_metrics`, `scores`, `sector_cache_summaries`) by eliminating the '#1 complaint against retail platforms': **black-box ratings and lack of explainability**.

### Proposed Wave 1 Story IDs (21 Stories)

| Story ID | Epic Cluster | Effort | Value Tag | Deliverable Summary |
|---|---|:---:|:---:|---|
| **US-0051** | Epic 1: Evidence-First Pillar UI | S | differentiator | Click/hover pillar score shows exact inputs, formula, and weight breakdown. |
| **US-0052** | Epic 1: Evidence-First Pillar UI | S | table-stakes | Plain-English 1-line interpretation under each of the 4 pillar scores. |
| **US-0056** | Epic 1: Evidence-First Pillar UI | S | differentiator | Click any pillar contribution to see raw financial statement line items and sources. |
| **US-0064** | Epic 1: Evidence-First Pillar UI | S | differentiator | Pillar Disagreement Radar: explicitly highlight tensions (e.g. 'High Quality but Expensive'). |
| **US-0067** | Epic 1: Evidence-First Pillar UI | S | differentiator | Overlay company's pillar bars directly against sector-currency peer medians. |
| **US-0080** | Epic 1: Evidence-First Pillar UI | S | differentiator | Decompose Risk pillar into visible sub-bars: Leverage, Coverage, and Volatility. |
| **US-0083** | Epic 1: Evidence-First Pillar UI | S | differentiator | Per-pillar missing data explainer FAQ ('Why is this NULL for this company?'). |
| **US-0100** | Epic 1: Evidence-First Pillar UI | S | table-stakes | Interactive formula visualizer showing how coverage penalties interact with composite score. |
| **US-0060** | Epic 2: Base-Rate & Factor Evidence | S | differentiator | Regime sensitivity notes on factor edges (e.g. size premium decay, quality stability). |
| **US-0063** | Epic 2: Base-Rate & Factor Evidence | S | differentiator | 'How this signal behaved historically' evidence card with publication decay dates. |
| **US-0676** | Epic 2: Base-Rate & Factor Evidence | S | whitespace | **Bessembinder Base-Rate Panel**: displays % of stocks that beat T-bills (58% lifetime failure base-rate) beside single-stock verdict. |
| **US-0905** | Epic 2: Base-Rate & Factor Evidence | S | differentiator | Historical evidence date-stamps on every model (e.g. Piotroski 1976–1996 in-sample period). |
| **US-0919** | Epic 2: Base-Rate & Factor Evidence | S | whitespace | Historical factor performance summary cards grounded in canonical empirical literature. |
| **US-0947** | Epic 2: Base-Rate & Factor Evidence | S | whitespace | Transparent disclosure of each model's known false-positive rates and structural limitations. |
| **US-0453** | Epic 3: Data Trust & Provenance | S | differentiator | Click-through link from metric to filing source accession and date. |
| **US-0460** | Epic 3: Data Trust & Provenance | S | differentiator | Ratio calculation inspector detailing numerator, denominator, and as-of dates. |
| **US-0466** | Epic 3: Data Trust & Provenance | S | differentiator | Universe Data Coverage & Health Dashboard (seed completeness vs provider backfill). |
| **US-0481** | Epic 3: Data Trust & Provenance | S | table-stakes | Prominent as-of vintage timestamps on every dossier metric card and table. |
| **US-0074** | Epic 4: Bear Case Counter-Weight | S | whitespace | Auto-generated 'Case Against This Stock' panel balancing bull narrative with weakest metrics. |
| **US-0705** | Epic 4: Bear Case Counter-Weight | S | whitespace | Structural equal-billing requirement: bear points displayed with equal prominence to positive signals. |
| **US-0725** | Epic 4: Bear Case Counter-Weight | S | whitespace | Pre-mortem thesis challenge prompt: 'Assume this stock underperforms over 2 years — why?'. |

### Implementation Architecture for Wave 1
1. **Backend Additions (FastAPI + SQLAlchemy)**:
   - Enhance `/api/v1/companies/{id}/score` and `/dossier` to include structured pillar input formulas, raw component values, and sector peer median benchmarks.
   - Add static academic factor evidence endpoint `GET /api/v1/research/factor-evidence` returning Bessembinder (2018/2024), Piotroski (2000), Novy-Marx (2013), and Beneish (1999) historical parameters and decay dates.
   - Enhance `/api/v1/coverage` to return comprehensive universe coverage statistics by sector and pillar.
2. **Frontend Additions (React + TypeScript Strict + Design Tokens)**:
   - Create `PillarDrilldownModal.tsx` / `PillarInspectorDrawer.tsx` allowing users to click any radar axis or score bar to inspect exact inputs, formula, peer percentiles, and missing data reasons.
   - Create `BaseRatePanel.tsx` in Dossier header displaying Bessembinder lifetime underperformance base rates (58% US / 55.2% non-US) and sector excess return odds.
   - Create `BearCasePanel.tsx` directly beside Executive Cockpit displaying the 3 weakest inputs and structured pre-mortem prompts.
   - Add `ProvenanceInspectorCard.tsx` providing one-click source inspection with as-of timestamps and SEC EDGAR accession links.
   - Strictly respect House Rules: zero chart npm libraries (pure SVG + CSS), tokenized styling (`tokens.css`), `prefers-reduced-motion` compliance, full keyboard accessibility, and visible disclaimers.
3. **Verification Plan**:
   - Backend unit and integration tests (`pytest tests/test_pillar_drilldown.py`, `pytest tests/test_base_rate.py`).
   - Frontend component tests (`vitest src/components/dossier/PillarInspector.test.tsx`, `BaseRatePanel.test.tsx`).
   - Zero-warning TypeScript compilation (`npm run build`).
   - End-to-end user flow verification using Playwright.

---

## STOP & AWAIT APPROVAL

Phase 0 Triage is complete. The exact scope of **Wave 1 (21 story IDs across 4 core epics)** is proposed above.
Awaiting owner approval before creating epic specifications in `docs/epics/` or implementing any code.