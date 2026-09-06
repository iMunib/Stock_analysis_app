# Wave 2 Epic Specification: Screener Presets & Watchlist Morning Brief

> **Phase 1 Wave 2 Specification**
> **Objective**: Implement 33 user stories across Epic 7 (Screener Presets & Advanced Multi-Metric Filtering - 28 stories) and Epic 5 (Watchlist 'What Changed' Digest & Morning Brief - 5 stories).
> **Frozen Contracts Maintained**: Locked composite weights (0.30/0.25/0.25/0.20), CAD/USD segregation, owner seed immutability, zero chart npm libraries (pure SVG+CSS), local-only zero-paid-API operation, honest NULL handling (no invented numbers).

---

## Epic 7: Screener Presets & Advanced Multi-Metric Filtering (28 Stories)

### US-0001: Strategy Selection Wizard for Beginners
- **Given** a beginner user arriving on the Screener page with no prior metric filter experience
- **When** the user clicks "Strategy Wizard" or views the onboarding banner
- **Then** the UI presents a guided multi-card strategy picker (e.g., "Compound Quality", "Deep Value Bargain", "Dividend Fortress", "Growth at Reasonable Price")
- **And** selecting a strategy pre-fills the screener filters, applies verified criteria, and instantly displays a sensible shortlist with a summary explanation.

### US-0003: Sustainable Dividend Screen (10+ Year History & Payout < 60%)
- **Given** an income-focused investor seeking durable cash yield
- **When** applying the "Sustainable Dividend" filter (or selecting the dividend preset)
- **Then** the system filters for companies with at least 10 consecutive years of dividend payments and a dividend payout ratio under 60% of earnings/cash flows
- **And** yield-trap names with unsustainable or deteriorating coverage are excluded.

### US-0005: GARP Screen (PEG < 1.0, Positive FCF Margin & Net Cash)
- **Given** an investor seeking Growth at a Reasonable Price
- **When** running the GARP criteria
- **Then** the engine filters for PEG ratio < 1.0, positive FCF margin (> 0.0), and net cash (Total Cash >= Total Debt / net debt <= 0)
- **And** returns matching candidates without manual spreadsheet computation.

### US-0007: Novy-Marx Gross Profitability Screen (GP/Assets Top Quartile)
- **Given** a quality investor targeting superior capital productivity per Novy-Marx (2013)
- **When** screening by gross profitability
- **Then** the system computes Gross Profit / Total Assets and filters for companies in the top 25th percentile (quartile 1) within their respective sector.

### US-0009: One-Word Named Custom Screen Presets
- **Given** an investor configuring a bespoke combination of screener filters
- **When** clicking "Save Preset" and providing a concise name (e.g., "Compounders", "Bargains")
- **Then** the criteria JSON is persisted to the database/local storage and appears in the screener preset dropdown for 1-click execution.

### US-0010: Interactive Criteria Builder with AND/OR Logic & Live Counts
- **Given** an investor configuring up to 10 distinct metric criteria
- **When** toggling between AND logic and OR logic for criteria groups
- **Then** the system evaluates the combined logic dynamically and updates matching count and candidate lists live.

### US-0011: Retiree Fortress Balance Sheet Screen (Debt/EBITDA <= 3x, Interest Coverage >= 8x)
- **Given** a risk-averse or retiree investor sensitive to rising interest rates
- **When** applying the Fortress Balance Sheet filter
- **Then** the screener filters for Total Debt / EBITDA <= 3.0x and Operating Income / Interest Expense >= 8.0x, omitting non-bank companies with heavy debt refinancing risk.

### US-0012: Audit-Ready CSV Screen Export with Embedded Filter Definition
- **Given** an analyst or compliance officer exporting screen results to CSV
- **When** clicking "Export CSV"
- **Then** the generated CSV file contains a metadata header block detailing:
  1. Filter criteria JSON and active bounds applied
  2. Currency view and export timestamp
  3. Methodology version and disclaimer
  4. Full tabular data with calculation provenance.

### US-0014: Dilution / Stock-Based Compensation Screen (SBC > 3% per year)
- **Given** an investor or financial journalist investigating per-share dilution
- **When** applying the Dilution Screen
- **Then** the system screens for companies where Stock-Based Compensation exceeds 3% of market cap or revenue, exposing firms where headline growth masks shareholder dilution.

### US-0016: 12-1 Price Momentum Percentile Screen with Quality Floor
- **Given** a quantitative momentum researcher
- **When** screening for momentum candidates
- **Then** the engine filters for 12-1 momentum (12-month return excluding the most recent month) in the top 20th percentile within sector alongside a minimum Quality score floor (Quality >= 6.0).

### US-0020: Small-Cap Explorer Screen by Market-Cap Band & Coverage
- **Given** an investor seeking undiscovered small-cap opportunities
- **When** selecting market-cap bands (Micro: < $300M, Small: $300M - $2B, Mid: $2B - $10B, Large: > $10B)
- **Then** the screener filters companies within the selected market-cap band and flags names with thin coverage or few peer comparisons.

### US-0021: Turnaround Screen (Negative Net Income but Positive & Rising FCF)
- **Given** an investor looking for early inflection and operational turnaround candidates
- **When** running the Turnaround screen
- **Then** the engine matches companies with negative accounting Net Income (< 0) but positive Free Cash Flow (> 0) and expanding FCF margins year-over-year.

### US-0022: 'Boring Great Businesses' Preset for Educational & Family Investing
- **Given** a user introducing fundamental investing principles
- **When** selecting the "Boring Great Businesses" preset
- **Then** the system screens for non-financial companies with ROE >= 15%, Net Debt / EBITDA <= 1.5x, Positive 5-Year FCF, and Altman Z-score in the Safe zone.

### US-0025: Durable Growth Screen (3-Year Revenue CAGR > 15% & Gross Margin Stability)
- **Given** a growth investor distinguishing resilient compounding from temporary spikes
- **When** applying the Durable Growth filter
- **Then** the engine filters for 3-Year Revenue CAGR > 15% and verifies Gross Margin stability (latest gross margin within 2 percentage points of 3-year historical average).

### US-0028: Contrarian Deep Value Screen (Bottom Decile Return + Top Half Piotroski)
- **Given** a contrarian investor hunting for oversold fundamental value
- **When** selecting the Contrarian Value preset
- **Then** the screener filters for stocks in the bottom decile (<= 10th percentile) of 12-month performance whose Piotroski F-Score is >= 5 (top half of financial health).

### US-0030: Formula-Transparent CSV Export with Exact Calculations
- **Given** a spreadsheet analyst exporting screener results
- **When** downloading the CSV export
- **Then** every computed column (PE, ROE, ROIC, FCF Margin, Net Debt) includes calculation notes and explicit component columns (Numerator, Denominator, Units) so numbers can be validated without re-deriving.

### US-0031: Instructive Empty State with Example Prompts
- **Given** a user opening the screener with no filters applied or zero initial matches
- **When** the screen results container renders empty
- **Then** an interactive empty state displays 4 clickable quick-start questions (e.g. "Safe Canadian Dividend Payers", "Discounted Quality Compounders", "Forensic Clean Sheets", "Piotroski Turnarounds") that instantly configure the screener.

### US-0033: Cash Dividend Coverage Screen (FCF Payout Ratio)
- **Given** an income investor who distrusts accounting earnings payout ratios
- **When** screening by Free Cash Flow dividend coverage
- **Then** the engine computes Dividends Paid / Free Cash Flow and filters for companies where FCF payout is strictly between 0% and 75%, flagging any company paying dividends out of debt.

### US-0034: Moat Compounding Screen (ROIC > WACC for 5+ Consecutive Years)
- **Given** a moat-focused investor
- **When** applying the Economic Moat filter
- **Then** the system filters for companies demonstrating ROIC greater than cost of capital (WACC / 9.0% threshold) across available multi-year snapshot statements.

### US-0035: Normalized Mid-Cycle Margins for Cyclicals
- **Given** an investor analyzing cyclical companies (Energy, Materials, Industrials)
- **When** enabling "Mid-Cycle Margin Normalization"
- **Then** the screener compares current operating margins against the company's 5-year historical average, preventing false value signals at cycle peaks.

### US-0038: 'Why These Matched' Statistical Summary Header
- **Given** an active screener result set
- **When** the results table renders
- **Then** a "Why These Matched" banner above the table summarizes the cohort's aggregate properties: Median Composite Score, Median P/E, Median ROE, and Sector Concentration.

### US-0039: Inline 5-Year Revenue Sparklines in Screen Table Rows
- **Given** an analyst scanning through screener results
- **When** viewing each company row
- **Then** an inline pure SVG sparkline displays the 5-year revenue trajectory, showing growth consistency and cyclical dips at a glance without navigating away.

### US-0041: Academic Book Checklist Scorer (Graham, Lynch, Greenblatt, Piotroski)
- **Given** an investor evaluating screen candidates
- **When** opening the Checklist overlay on any screen result row
- **Then** the company is scored against 4 canonical book checklists:
  1. Benjamin Graham Defensive Checklist (P/E * P/B <= 22.5, Current Ratio >= 2.0, Positive 10y EPS)
  2. Peter Lynch Fast Grower / Stalwart (PEG <= 1.0, Low Debt/Equity)
  3. Joel Greenblatt Magic Formula (Top ROIC + High Earnings Yield)
  4. Joseph Piotroski F-Score (Score 7-9 Financial Health).

### US-0042: Screener Auto-Run Queue on Data Refresh
- **Given** an investor maintaining a favorite recurring screen
- **When** marking a saved preset as "Auto-run on refresh"
- **Then** the system tags the preset so background ingest/backfill jobs record refreshed match lists for immediate review.

### US-0046: Thematic Tag Filtering (Custom & Thematic Universe Tags)
- **Given** an investor exploring thematic baskets (e.g. AI Supply Chain, Critical Minerals, Clean Tech, SPUS)
- **When** filtering by universe or theme tag
- **Then** the screener filters exclusively for companies tagged with that theme.

### US-0047: Portfolio Diversifier Screen (Uncorrelated Sector & Geography)
- **Given** an investor holding a portfolio concentrated in a specific sector or geography (e.g. US Tech)
- **When** selecting "Diversify Against [Sector / Country]"
- **Then** the screener surfaces top-scoring companies strictly outside the specified sector and country cohort.

### US-0048: Steady Compounders Screen (10-Year Revenue CAGR > 5% & Drawdown Resilient)
- **Given** a long-term compounder investor
- **When** applying the Steady Compounder filter
- **Then** the system filters for companies with long-term revenue CAGR >= 5% and no single fiscal year revenue decline exceeding 10%.

### US-0049: NULL vs Zero Match Disambiguation Warning
- **Given** a user setting strict multi-metric filter criteria that produces 0 matching rows
- **When** the empty result set is returned
- **Then** the system inspects the criteria and displays a distinct diagnostic banner explaining whether the 0 results resulted from true filter stringency or from NULL data availability in the universe.

---

## Epic 5: Watchlist 'What Changed' Digest & Morning Brief (5 Stories)

### US-0084: Re-Rating & Signal Shift Change Detection
- **Given** a user tracking stocks in their watchlist
- **When** a periodic data refresh or recompute modifies a company's signal (e.g. from 'fair_value' to 'strong_candidate' or 'deteriorating')
- **Then** the system logs the signal transition event with the before/after status and rationale for immediate notification.

### US-0092: Weekly Watchlist Pillar Delta Digest
- **Given** a busy investor reviewing their portfolio on a weekly cadence
- **When** navigating to the Watchlist Digest
- **Then** a dedicated digest presents a structured view of weekly pillar score changes (+/- Quality, Value, Growth, Risk) strictly for the user's watched tickers.

### US-0351: 1-Page Morning Brief of Watchlist Overnight Deltas
- **Given** an investor starting their morning research routine
- **When** opening the Morning Brief at `/watchlist/digest` (or on the Desk)
- **Then** a concise 1-page summary synthesizes:
  1. Material pillar and composite score shifts
  2. Fresh SEC/SEDAR+ regulatory filings released within the last 7 days
  3. Key financial indicator movements and distress alert triggers.

### US-0367: Per-Alert Severity & Channel Routing (Digest vs Immediate)
- **Given** an investor configuring alert preferences for watched tickers
- **When** creating or editing an alert rule
- **Then** the user can designate severity ('Critical' / 'Elevated' / 'Informational') and routing channel ('Immediate Banner' vs 'Morning Digest Only'), ensuring signal-to-noise control.

### US-0377: Post-Earnings Morning Delta Comparison View
- **Given** a watched company that recently reported quarterly or annual earnings
- **When** viewing the Morning Brief
- **Then** a Post-Earnings comparison card displays:
  1. Actuals vs Prior Year for Revenue, Operating Income, and EPS
  2. Any newly triggered forensic or data quality flags
  3. Directional movement of Quality, Value, Growth, and Composite scores.
