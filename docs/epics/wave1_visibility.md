# Wave 1 Epic Specification: Visibility of What Exists

> **Phase 1 Epic Specification**
> **Objective**: Implement 21 high-impact user stories across 4 epics delivering radical explainability, empirical base-rate context, data provenance, and pre-mortem counter-weights over the existing fundamental dataset.
> **Frozen Contracts Maintained**: Locked composite weights (0.30/0.25/0.25/0.20), CAD/USD segregation, owner seed immutability, zero chart npm libraries (pure SVG+CSS), local-only zero-paid-API operation.

---

## Epic 1: Evidence-First Pillar UI & Methodology Drilldown (8 Stories)

### US-0051: Exact Inputs, Formula, and Weight Breakdown Drilldown
- **Given** a user viewing any of the 4 pillar scores (Quality, Value, Growth, Risk) on the Company Dossier
- **When** the user clicks or hovers the pillar score card or bar
- **Then** a drilldown modal or drawer opens displaying:
  1. The exact formula used to compute that pillar
  2. The raw metric inputs (e.g. ROE, ROIC, Gross Margin for Quality)
  3. The weight of each sub-metric within the pillar
  4. The normalized 0-10 score contribution of each sub-metric.

### US-0052: Plain-English 1-Line Interpretation Under Each Pillar Score
- **Given** a company's pillar scores are rendered on the Dossier Executive Cockpit
- **When** the pillar score cards render
- **Then** a clear, plain-English 1-line interpretation appears directly beneath each score (e.g., "Top-quartile profitability driven by 24% ROIC, partially offset by declining 3-year margins").

### US-0056: Link Pillar Contributions to Raw Statement Line Items & Sources
- **Given** an open pillar drilldown view showing an input metric (e.g., Free Cash Flow Margin)
- **When** the user clicks on the metric name or contribution row
- **Then** the view expands to show the exact financial statement line items (Operating Cash Flow - Capital Expenditures / Total Revenue) with filing provenance and reporting period.

### US-0064: Pillar Disagreement Radar (Highlight Core Tensions)
- **Given** a company has starkly diverging pillar scores (e.g. Quality >= 7.5 but Value <= 3.0, or Value >= 8.0 but Risk >= 7.0)
- **When** the dossier summary card renders
- **Then** a prominent "Tension Callout" chip/banner appears highlighting the exact trade-off (e.g., "High Quality but Expensive: Quality 8.4/10 vs Value 2.8/10") rather than hiding the tension behind a blended composite.

### US-0067: Overlay Pillar Bars Against Sector-Currency Peer Medians
- **Given** the company belongs to a sector-currency cohort (e.g., US Technology or Canadian Financials)
- **When** the pillar score visualizer renders
- **Then** each pillar bar displays a distinct marker/line indicating the sector peer median score, allowing instant visual benchmarking of relative outperformance or underperformance.

### US-0080: Decompose Risk Pillar Into Visible Sub-Bars
- **Given** the Risk pillar score is displayed on the company dossier
- **When** the user views the Risk breakdown
- **Then** the Risk pillar is visually decomposed into three distinct sub-bars:
  1. Leverage (Debt/Equity, Net Debt/EBITDA)
  2. Coverage (Interest Coverage, Cash Coverage)
  3. Volatility (Historical Beta, Margin Volatility).

### US-0083: Per-Pillar Missing Data Explainer FAQ
- **Given** a company has a NULL or incomplete pillar (e.g., Bank missing Total Debt or FCF)
- **When** the user inspects the pillar score
- **Then** an honest explainer note is displayed explaining exactly why the data is absent (e.g., "Debt metrics are intentionally omitted for commercial banks where customer deposits represent operating liabilities rather than corporate debt per frozen accounting rules").

### US-0100: Interactive Coverage Penalty Visualizer
- **Given** a company has missing pillars resulting in a coverage multiplier (e.g. x0.92 for 3 pillars, x0.80 for 2 pillars)
- **When** the user hovers or clicks the Coverage Badge
- **Then** an interactive breakdown shows:
  1. Unadjusted weighted score
  2. Coverage penalty deduction formula
  3. Final published composite score.

---

## Epic 2: Bessembinder Base-Rate Context & Factor Evidence (6 Stories)

### US-0060: Regime Sensitivity Notes on Factor Edges
- **Given** the user is viewing model scores or factor definitions in the Research/Factor module
- **When** viewing factors like Value or Quality
- **Then** regime sensitivity notes are displayed explaining macroeconomic conditions where the factor historically struggled (e.g., "Value underperforms during sustained low-rate, high-multiple regimes as observed 2010-2020").

### US-0063: Factor Historical Behavior & In-Sample vs Out-of-Sample Decay Dates
- **Given** an investor evaluating an academic fundamental model (Piotroski F-Score, Beneish M-Score, Altman Z-Score)
- **When** expanding the model methodology card
- **Then** the UI displays the canonical paper publication date and the empirical factor decay observed out-of-sample (e.g., "Piotroski published 2000; post-2000 out-of-sample alpha decayed by ~40% due to factor crowding").

### US-0676: Bessembinder Base-Rate Panel Beside Single-Stock Verdict
- **Given** the user is viewing any single-stock dossier verdict
- **When** the Executive Cockpit renders
- **Then** an explicit Base-Rate Callout panel appears stating:
  "Empirical Base Rate: Only 42% of US common stocks beat 1-month T-Bills over their full lifetime; the median stock generates a cumulative lifetime return of -100% relative to T-Bills (Bessembinder 2018/2024)."
  Providing essential probabilistic humility against single-stock conviction.

### US-0905: Historical Evidence Date-Stamps on Every Quantitative Model
- **Given** any forensic or valuation card displayed on the platform
- **When** the card header is inspected
- **Then** an immutable date badge displays the sample study window (e.g., "Altman (1968): 1946-1965 Manufacturing sample", "Beneish (1999): 1982-1992 Compustat sample").

### US-0919: Historical Factor Performance Summary Cards
- **Given** the user navigates to the Factor Methodology reference screen
- **When** inspecting canonical investment factors (Quality, Value, Momentum, Low Volatility)
- **Then** summary cards display long-term annualized returns, Sharpe ratios, and maximum drawdowns sourced from Kenneth French Data Library and published literature.

### US-0947: Transparent Disclosure of Model False-Positive Rates & Limitations
- **Given** a forensic model emits a warning flag (e.g. Beneish M-Score > -1.78 or Altman Z < 1.81)
- **When** the flag is displayed
- **Then** the card transparently reports the empirical false-positive rate (e.g., "Beneish M-Score false positive rate is ~14% among fast-growing firms; capital expenditure growth can simulate sales manipulation").

---

## Epic 3: Data Trust & Provenance Inspector (4 Stories)

### US-0453: Direct Link From Metric to SEC Filing Accession & Date
- **Given** a US company fundamental metric derived from SEC filings (e.g. 10-K or 10-Q)
- **When** the user clicks the provenance tag or accession link
- **Then** the system opens the exact SEC EDGAR filing viewer URL for that accession number and fiscal period.

### US-0460: Ratio Calculation Inspector (Numerator, Denominator & As-Of Dates)
- **Given** any computed financial ratio (e.g., Current Ratio, EV/EBITDA, Net Debt/FCF)
- **When** the user selects "Inspect Calculation"
- **Then** a modal presents:
  1. Exact formula definition
  2. Numerator value, units, currency, and as-of fiscal date
  3. Denominator value, units, currency, and as-of fiscal date
  4. Step-by-step arithmetic resolution.

### US-0466: Universe Data Coverage & Health Dashboard
- **Given** an administrator or researcher auditing the system
- **When** navigating to /coverage or /data-health
- **Then** a comprehensive health matrix shows:
  1. Total coverage across the 720 universe names
  2. Seed workbook completeness vs provider backfill
  3. Per-pillar data completeness breakdown by sector
  4. Total count and percentage of NULL fields.

### US-0481: Prominent As-Of Vintage Timestamps on Every Metric Card
- **Given** any metric card or financial table on the Dossier or Screener
- **When** the component renders
- **Then** an explicit vintage timestamp is prominently displayed (e.g., "FY2023 10-K filed 2024-02-15 | Market Price as of 2024-08-22") preventing temporal confusion.

---

## Epic 4: Bear Case & Pre-Mortem Counter-Weight Engine (3 Stories)

### US-0074: Auto-Generated "Case Against This Stock" Panel
- **Given** a stock has strong composite and pillar scores
- **When** viewing the company overview
- **Then** an automated "Case Against This Stock" panel synthesizes the company's 3 lowest percentile metrics or failing forensic tests into a coherent bear thesis.

### US-0705: Structural Equal-Billing Requirement for Bear Signals
- **Given** the Dossier layout architecture
- **When** positive summary cards (e.g., "Investment Thesis Highlights") are rendered
- **Then** the UI layout enforces identical visual weight, typography, and card size for the "Key Vulnerabilities / Bear Case" card directly adjacent.

### US-0725: Pre-Mortem Thesis Challenge Prompt
- **Given** a user recording or editing their investment thesis in the Thesis Notepad
- **When** opening the thesis workspace
- **Then** a prominent Pre-Mortem Prompt is presented:
  *"Assume you bought this stock today and over the next 24 months it suffered a catastrophic 50% drawdown. Looking backward from 2026, what was the obvious reason this investment failed?"*
  Requiring explicit consideration of failure modes before committing capital.
