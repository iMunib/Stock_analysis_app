# Wave 7 Epic Specification: Canadian Wedge, SEC Form 4 Insider Tracking & Technical Context

> **Phase 1 Wave 7 Specification**
> **Objective**: Deliver 86 user stories across Epics 15 (Canadian Market, 36 stories), 16 (SEC Form 4 Insider Tracking, 7), and 17 (Price Momentum & Technical Context, 43) — Canadian tax-account optimization, TSX granularity, dual-listed identity, insider cluster detection, and 12-1 momentum as pure technical context with SVG primitives, all with currency-segregated CAD purity and frozen composite weights.

---

## Epic 15: Canadian Market & Tax-Account Optimization (36 Stories)

### US-0037: Canadian Account Placement Guide — TFSA vs RRSP vs FHSA vs Non-Registered
- **Given** a Canadian investor holding a US dividend payer vs a Canadian eligible dividend payer
- **When** viewing the Canadian Tax Card for that holding
- **Then** the card shows TFSA (US withholding 15% not recoverable), RRSP (exempt via treaty), FHSA (like TFSA), Non-Registered (eligible dividend gross-up/tax credit context) with informational notes, not tax advice.

### US-0609: TSX Industry Granularity — Custom Canadian Industry Medians in Pure CAD
- **Given** a TSX-listed company with custom_industry_sheet
- **When** requesting Canadian sector benchmarks
- **Then** the API returns median composite, PE, PB, ROE in pure CAD for that custom industry, never blended with USD.

### US-0610: US Dividend Withholding Tax in TFSA vs RRSP
- **Given** a US equity held in TFSA vs RRSP
- **When** viewing the tax card
- **Then** the card shows 15% US withholding in TFSA (lost) vs 0% in RRSP (treaty exempt).

### US-0611: Canadian Eligible Dividend Gross-Up/Tax Credit Context
- **Given** a Canadian corporation paying eligible dividends
- **When** viewing the tax card
- **Then** the card shows gross-up and federal tax credit context as informational, not advice.

### US-0613: Canadian REIT FFO/AFFO Proxies
- **Given** a Canadian REIT (e.g., REIT GICS or REIT custom sheet)
- **When** viewing Canadian metrics
- **Then** FFO/AFFO proxies are derived from operating cash flow and capex where available, with REIT flag.

### US-0614: Dual-Listed Identity — RY, SHOP, ENB Mapping
- **Given** a dual-listed stock (e.g., RY trades as RY on TSX in CAD and RY on NYSE in USD)
- **When** viewing the dossier
- **Then** the identity shows dual-listed badge with native CAD TSX metrics and US ratio parity without blending money.

### US-0615: Canadian Small-Cap TSX Coverage
- **Given** a TSX small-cap
- **When** viewing the dossier
- **Then** the card shows TSX-specific context and CAD purity.

### US-0616: Canadian Dividend Aristocrats Tracking
- **Given** a Canadian Dividend Aristocrat
- **When** viewing the dossier
- **Then** the card shows Aristocrat status and consecutive dividend years.

### US-0618: Canadian Energy/Mining Resource Economics
- **Given** an Energy or Materials TSX name
- **When** viewing Canadian metrics
- **Then** resource economics notes are shown.

### US-0619: Canadian Banks — Big Six Comparison
- **Given** a Canadian bank
- **When** viewing peer comparison
- **Then** the peer set is Big Six CAD banks with CET1/NIM/efficiency in pure CAD.

### US-0620: Canadian Utilities — Rate-Regulated Context
- **Given** a Canadian utility
- **When** viewing the dossier
- **Then** utility capital structure notes are shown.

### US-0621: Dual-Listed Ratio Parity Without Blending
- **Given** a dual-listed name
- **When** viewing valuation multiples
- **Then** the multiples are shown as unitless ratios, never converted money.

### US-0623: Currency Isolation — CAD vs USD Totals Never Blended
- **Given** a portfolio or screener with CAD and USD names
- **When** requesting totals
- **Then** totals are returned per currency with explicit segregation tags.

### US-0624: Canadian Fixed-Income / Preferred Share Structural Notes
- **Given** a Canadian preferred share or rate-reset
- **When** viewing the dossier
- **Then** structural notes on rate-reset preferreds are shown.

### US-0625: Canadian Rate-Reset Preferreds Context
- **Given** a Canadian rate-reset preferred
- **When** viewing the dossier
- **Then** the card explains the rate-reset mechanism.

### US-0626: Canadian Dividend Aristocrats vs US
- **Given** a Canadian Aristocrat
- **When** comparing to US peers
- **Then** the comparison uses unitless yield ratios.

### US-0627: Canadian Tax-Account Eligibility
- **Given** a Canadian account type
- **When** viewing eligibility
- **Then** the card shows which securities are eligible for TFSA/RRSP/FHSA.

### US-0628: Canadian REIT FFO/AFFO vs US REIT
- **Given** a Canadian REIT
- **When** comparing FFO
- **Then** the comparison is pure CAD.

### US-0629: Canadian Utility Capital Structure
- **Given** a Canadian utility
- **When** viewing capital structure
- **Then** the card shows utility-specific leverage notes.

### US-0630: Canadian Dividend Gross-Up Example
- **Given** a Canadian eligible dividend
- **When** viewing the tax card
- **Then** an example gross-up calculation is shown.

### US-0632: Canadian Withholding Tax Example
- **Given** a US dividend in TFSA
- **When** viewing the tax card
- **Then** an example 15% withholding calculation is shown.

### US-0634: TFSA vs RRSP Optimization Rules
- **Given** a Canadian investor
- **When** viewing the placement guide
- **Then** the guide shows optimization rules for each account.

### US-0635: Canadian Dividend Aristocrats List
- **Given** a TSX name
- **When** requesting Aristocrat list
- **Then** the API returns Aristocrat status.

### US-0636: Canadian Sector Stats CAD-Pure
- **Given** a TSX sector
- **When** requesting sector stats
- **Then** the stats are returned in pure CAD.

### US-0637: Dual-Listed Interlisted Identity
- **Given** an interlisted stock
- **When** viewing identity
- **Then** the dossier shows both CAD and USD tickers.

### US-0638: Canadian REIT Distribution
- **Given** a Canadian REIT distribution
- **When** viewing the dossier
- **Then** the distribution is shown with CAD tag.

### US-0639: Canadian Tax Credit Context
- **Given** a Canadian dividend
- **When** viewing the tax card
- **Then** the federal tax credit context is shown.

### US-0640: Canadian Small-Cap Peer Set
- **Given** a TSX small-cap
- **When** requesting peers
- **Then** the peer set is CAD-only.

### US-0641: Canadian Large-Cap Peer Set
- **Given** a TSX large-cap
- **When** requesting peers
- **Then** the peer set is CAD-only.

### US-0642: Canadian Mid-Cap Peer Set
- **Given** a TSX mid-cap
- **When** requesting peers
- **Then** the peer set is CAD-only.

### US-0643: Canadian Micro-Cap Peer Set
- **Given** a TSX micro-cap
- **When** requesting peers
- **Then** the peer set is CAD-only.

### US-0644: Canadian Preferred Share Context
- **Given** a Canadian preferred
- **When** viewing the dossier
- **Then** preferred share notes are shown.

### US-0647: Canadian Tax-Deferred Growth
- **Given** a TFSA/RRSP holding
- **When** viewing the tax card
- **Then** deferred growth context is shown.

### US-0648: Canadian Non-Registered Tax Context
- **Given** a non-registered holding
- **When** viewing the tax card
- **Then** capital gains and dividend tax context are shown.

### US-0649: Canadian Estate Context
- **Given** a Canadian holding
- **When** viewing the tax card
- **Then** estate context is shown as informational.

### US-0650: Canadian Withholding Tax Recovery
- **Given** a US dividend in RRSP
- **When** viewing the tax card
- **Then** the card shows withholding is recoverable via treaty.

---

## Epic 16: SEC Form 4 Insider Tracking & Disclosed Filings Engine (7 Stories)

### US-0044: Insider Cluster Detector — 3+ Distinct Buyers in 90 Days
- **Given** a US equity with Form 4 filings
- **When** evaluating the 90-day rolling window
- **Then** the engine flags a cluster buy when ≥3 distinct insiders have open-market buys.

### US-0554: Provenance Lag Labels — Filing Timestamp & As-Of Date
- **Given** a Form 4 filing
- **When** displaying the transaction
- **Then** the filing timestamp and reporting date are shown with lag.

### US-0584: Filings-Only Pure Mode Toggle
- **Given** a dossier with insider and technical panels
- **When** toggling filings-only pure mode
- **Then** only verified SEC/SEDAR+ events are shown without editorial noise.

### US-0586: Opportunistic Timing Filter — 10b5-1 vs Discretionary
- **Given** a Form 4 transaction
- **When** classifying the transaction
- **Then** 10b5-1 pre-planned exercises are tagged vs discretionary open-market buys.

### US-0590: Insider Transaction Table with Officer/Director/Owner Roles
- **Given** a US equity
- **When** viewing insider activity
- **Then** a table shows insider name, role, transaction type, shares, price, and filing date.

### US-0597: Insider Buying as Sentiment Context
- **Given** a cluster buy
- **When** viewing the dossier
- **Then** the cluster is shown as filed historical fact with disclaimer not an endorsement.

### US-0598: Filings-Only Mode Persists
- **Given** filings-only mode is enabled
- **When** navigating between companies
- **Then** the mode persists via localStorage.

---

## Epic 17: Price Momentum (12-1) & Technical Context Overlays (43 Stories)

### US-0651: Price History Fetch — Yahoo Finance Daily Closes
- **Given** a company with ticker
- **When** requesting price history
- **Then** daily closes are fetched via Yahoo Finance and cached locally.

### US-0652: Academic 12-1 Momentum Percentile (Jegadeesh & Titman 1993)
- **Given** 12 months of daily closes
- **When** computing 12-1 momentum
- **Then** the 12-month return skipping the most recent month is computed as (P_{t-1}/P_{t-12} -1) and ranked vs sector peers.

### US-0653: Valuation-Price Alignment — DCF vs Current Price
- **Given** a company with DCF and Graham floor
- **When** viewing technical context
- **Then** the current price is mapped against intrinsic value zones.

### US-0654: Maximum Historical Drawdown & Recovery Time
- **Given** price history
- **When** computing drawdown
- **Then** maximum drawdown and recovery days are computed.

### US-0655: Sector Volatility Percentile
- **Given** price history and sector peers
- **When** computing volatility
- **Then** the 30-day volatility percentile vs sector is shown.

### US-0657: Price Momentum as Technical Context, Not Scoring Pillar
- **Given** a company with 12-1 momentum
- **When** viewing the dossier
- **Then** the momentum is shown as technical context, never added to composite.

### US-0658: Momentum Percentile Rank
- **Given** a company with 12-1 momentum
- **When** viewing technicals
- **Then** the percentile rank (0-100) is shown.

### US-0659: Momentum Signal Strength
- **Given** a momentum percentile
- **When** viewing
- **Then** the signal is Weak/Medium/Strong based on percentile.

### US-0661: SMA 50 vs SMA 200 Gauge
- **Given** price history
- **When** viewing technicals
- **Then** a gauge shows price vs SMA50 vs SMA200.

### US-0662: Price vs Moving Average
- **Given** price and SMAs
- **When** viewing
- **Then** the distance to each SMA is shown.

### US-0663: Trend Strength
- **Given** SMA50 vs SMA200
- **When** viewing
- **Then** trend strength is shown (e.g., Golden Cross).

### US-0664: Beta & Index Correlation Matrix
- **Given** price history and benchmark (S&P 500 / TSX Composite)
- **When** computing
- **Then** beta and correlation vs benchmark are shown.

### US-0666: Price Momentum Timeframe
- **Given** a momentum window
- **When** viewing
- **Then** the 12-1 window is labeled.

### US-0667: Momentum vs Peer Median
- **Given** a company and sector peers
- **When** viewing momentum
- **Then** the peer median momentum is shown.

### US-0668: Momentum Stability
- **Given** 12-1 momentum over time
- **When** viewing
- **Then** stability vs history is shown.

### US-0670: Momentum Signal Decay
- **Given** a momentum signal
- **When** viewing
- **Then** the signal includes decay note.

### US-0671: Insider vs Momentum Divergence
- **Given** insider cluster and momentum
- **When** viewing
- **Then** divergence is noted.

### US-0672: Momentum and Value Trap
- **Given** a value trap
- **When** viewing momentum
- **Then** the value trap flag is shown alongside momentum.

### US-0674: Price Performance vs Sector
- **Given** price history
- **When** viewing
- **Then** performance vs sector median is shown.

### US-0675: Technical Context Disclaimer
- **Given** any technical panel
- **When** viewing
- **Then** disclaimer Price momentum is market sentiment context, not an intrinsic verdict is displayed.

### US-0677: Price History Chart
- **Given** daily closes
- **When** viewing technicals
- **Then** a pure SVG price chart is shown.

### US-0678: 52-Week Range & High/Low Ticks
- **Given** 52-week high/low
- **When** viewing
- **Then** a gauge shows price vs 52-week range.

### US-0679: Moving Average Crossover
- **Given** SMA50 and SMA200
- **When** viewing
- **Then** crossover signals are shown.

### US-0680: Drawdown Recovery Bar
- **Given** maximum drawdown
- **When** viewing
- **Then** a recovery bar shows drawdown vs recovery.

### US-0681: Volatility Smile
- **Given** volatility history
- **When** viewing
- **Then** volatility percentile is shown.

### US-0682: Valuation-Price Alignment Zone
- **Given** DCF and Graham floors
- **When** viewing
- **Then** price is mapped to Undervalued/Fair/Overvalued zones.

### US-0683: Price Momentum Percentile Chart
- **Given** momentum percentile
- **When** viewing
- **Then** a chart shows percentile.

### US-0684: Price Momentum Signal
- **Given** momentum
- **When** viewing
- **Then** the signal is shown.

### US-0685: Technical Context Pure Mode
- **Given** filings-only pure mode
- **When** viewing technicals
- **Then** only verified price history is shown.

### US-0686: Price Momentum Calculation Transparency
- **Given** 12-1 momentum
- **When** viewing details
- **Then** the formula (P_{t-1}/P_{t-12} -1) is shown.

### US-0687: Price History Cache
- **Given** price history
- **When** fetching
- **Then** the history is cached locally in SQLite.

### US-0688: Price Momentum Peer Comparison
- **Given** a company and peers
- **When** viewing
- **Then** peer momentum percentiles are shown.

### US-0689: Price Momentum Signal Strength Meter
- **Given** momentum percentile
- **When** viewing
- **Then** a meter shows signal strength.

### US-0690: Price Momentum Time Series
- **Given** momentum over time
- **When** viewing
- **Then** a time series is shown.

### US-0691: Price Momentum vs Financials
- **Given** momentum and financials
- **When** viewing
- **Then** both are shown without blending.

### US-0692: Price Momentum Disclaimer
- **Given** any momentum view
- **When** viewing
- **Then** disclaimer is displayed.

### US-0693: Price Momentum as Market Sentiment Context
- **Given** momentum
- **When** viewing
- **Then** it is labeled as market sentiment context.

### US-0695: Price Momentum vs Sector Volatility
- **Given** momentum and volatility
- **When** viewing
- **Then** both are shown.

### US-0696: Price Momentum Signal Decay Note
- **Given** momentum signal
- **When** viewing
- **Then** decay note is shown.

### US-0697: Sector Volatility Percentile and Downside Capture
- **Given** price history and sector
- **When** computing
- **Then** volatility percentile and downside capture vs sector are shown.

### US-0698: Price Momentum History
- **Given** price history
- **When** viewing momentum history
- **Then** history is shown.

### US-0699: Price Momentum Calculation Steps
- **Given** 12-1 momentum
- **When** viewing steps
- **Then** calculation steps are shown.

### US-0700: Price Momentum Peer Median
- **Given** a company
- **When** viewing momentum
- **Then** peer median is shown.

---

## Cross-Cutting Acceptance Notes

- CAD and USD are strictly segregated; all cross-border comparisons remain unitless ratios with explicit segregation tags.
- Missing price history → momentum NULL + flag; missing Form 4 → insider table shows filings-only pure mode with honest empty state.
- 12-1 momentum is technical CONTEXT only, never a 5th scoring pillar, and does not alter locked composite math.
- Pure SVG technical primitives use <svg>, <line>, <rect>, <circle>, <polyline> with tokens.css.
- a11y: panels, tables, and SVG charts have ARIA roles/labels and Tab/Escape.
- Disclaimers: Personal research software, not investment advice. Price momentum is market sentiment context, not an intrinsic verdict. Insider transactions are filed historical facts.
