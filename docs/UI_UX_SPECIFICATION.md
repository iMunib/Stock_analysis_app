# UI/UX SPECIFICATION & PROGRESSIVE DISCLOSURE BLUEPRINT
## Designing the "2-Minute Decision Engine" for Retail Equity Research
**Document Version:** 1.0.0 (Dedicated UI/UX Design System Specification)  
**Status:** Frozen Blueprint — Reserved for Dedicated UI/UX Implementation Session  
**Target Repository:** `Investment Stock Application` (`frontend/src/`)  

---

### 1. DESIGN PHILOSOPHY & CORE PRINCIPLES

1. **Strict Progressive Disclosure (3-Tier Hierarchy):**
   - **Level 1 (60-Second Executive Cockpit):** For every beginner retail investor. Answers: *"Is this company safe, is the price fair, and should I buy or hold an index ETF?"* Zero jargon.
   - **Level 2 (5-Minute Flight Deck):** For active DIY investors. Interactive factor scores, Peter Lynch archetypes, True Shareholder Yield, and cash flow waterfalls.
   - **Level 3 (Institutional Engine Room):** For analysts and forensic investors. Full 8-variable Beneish M-Score, Penman reformulated statements, Altman Z 5-factor breakdown, and 10-year common-size filings.
2. **Zero Unexplained Acronyms:** Every technical metric has an inline tooltip and plain-English translation.
3. **Strict Currency Purity:** CAD and USD money are visually quarantined with distinct badges. Never blended or averaged.
4. **No NPM Charting Bloat:** 100% pure SVG + CSS primitives for ultra-fast load times (<50ms render).
5. **Night Research Desk Aesthetics:** High-contrast slate/zinc dark mode optimized for sustained analytical focus.

---

### 2. LEVEL 1: THE 60-SECOND EXECUTIVE COCKPIT

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [US:AAPL:US]  APPLE INC.  •  NASDAQ  •  $228.50 USD  •  Mcap: $3.48T  •  Sector: Technology           │
│ "Apple designs personal electronics (iPhone, Mac, iPad) and sells high-margin digital services."       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ BOTTOM-LINE SAFETY VERDICT:                                                                            │
│ [ COMPOUNDER AT FAIR VALUE ]  •  Confidence: HIGH (4/4 Pillars Complete)                               │
├───────────────────────────────────┬───────────────────────────────────┬────────────────────────────────┤
│ 1. BUSINESS MOAT & QUALITY        │ 2. FINANCIAL SAFETY & SOLVENCY    │ 3. VALUATION & GROWTH HURDLE   │
│   ● [ GREEN: WIDE MOAT ]          │   ● [ GREEN: PRISTINE ]           │   ● [ AMBER: FAIRLY VALUED ]   │
│   ROIC of 58% and 46% gross       │   Net cash balance of $28B.       │   Priced for 11.2% FCF growth. │
│   margins indicate massive        │   Negligible bankruptcy or        │   Historical 5-year growth was │
│   pricing power and ecosystem.    │   distress risk (Altman Z: 4.8).  │   13.8%. Fair margin of safety.│
├───────────────────────────────────┴───────────────────────────────────┴────────────────────────────────┤
│ THE MARKET'S EXPECTATION (REVERSE DCF RULE):                                                           │
│ "To justify today's price of $228.50, Apple must grow its free cash flow by 11.2% every year for the   │
│ next 10 years. Over the last 5 years, it actually compounded cash flow at 13.8% annually."             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PLAIN-ENGLISH DECISION SUMMARY:                                                                        │
│ • Why Buy (Top Strengths):  1. High-margin Services ecosystem. 2. Pristine balance sheet. 3. Strong moat│
│ • Key Risk to Watch:        Heavy reliance on iPhone hardware refresh cycles and China supply chain.   │
│ • Index Opportunity Cost:   Expected annual return: 10.8% vs. S&P 500 nominal baseline of 8.0%.       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 2.1 State Color Rules for Verdict Badges:
- **Green (`var(--color-positive)`):**
  - `COMPOUNDER AT FAIR VALUE`: Wide/Narrow Moat + Altman Safe + Reverse DCF Gap $\le +2\%$.
  - `UNDERVALUED BARGAIN`: Altman Safe + Beneish Clean + Current Price $\le$ Graham Floor / DCF at $>25\%$ margin of safety.
- **Amber (`var(--color-warning)`):**
  - `OVERVALUED QUALITY`: Wide Moat + Pristine Balance Sheet, BUT Reverse DCF Gap $> +6\%$ (Priced for perfection).
  - `CYCLICAL PEAK: CAUTION`: Cyclical Archetype + Trough P/E multiple at peak earnings + decelerating CFO.
- **Red (`var(--color-negative)`):**
  - `AVOID: VALUE TRAP / DISTRESS`: Altman Z Distress Zone OR Beneish M-Score flagged OR severe CFO-NI decoupling.

---

### 3. LEVEL 2: THE 5-MINUTE FLIGHT DECK

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  [ LEVEL 1: COCKPIT ]        ★ [ LEVEL 2: FLIGHT DECK ]          [ LEVEL 3: ENGINE ROOM ]              │
├───────────────────────────────────────────────────┬────────────────────────────────────────────────────┤
│ 4-PILLAR RESEARCH RADAR                           │ PETER LYNCH ARCHETYPE & VALUATION                  │
│                                                   │                                                    │
│               Quality (8.2/10)                    │ Classification: [ STALWART COMPOUNDER ]            │
│                     ▲                             │ • 5-Year EPS CAGR: 14.2%                           │
│                    / \                            │ • Trailing P/E: 32.4x                              │
│                   /   \                           │ • PEG Ratio: 2.28  (Stretched valuation)           │
│   Risk (7.9/10) ◄───────► Value (4.1/10)          │                                                    │
│                   \   /                           │ Buffett Owner Earnings:                            │
│                    \ /                            │ • Net Income: $100.4B | Maint. CapEx: $8.2B        │
│                     ▼                             │ • Owner Earnings: $98.1B (Yield: 2.82%)            │
│               Growth (6.8/10)                     │                                                    │
├───────────────────────────────────────────────────┴────────────────────────────────────────────────────┤
│ TRUE SHAREHOLDER YIELD (ACCOUNTING FOR STOCK-BASED COMPENSATION DILUTION)                             │
│                                                                                                        │
│ Dividend Yield:      [ 0.44% ]                                                                         │
│ Gross Buyback Yield: [ 3.12% ] ($108.0B repurchased)                                                   │
│ Less: Actual SBC:   -[ 0.32% ] ($11.2B executive stock compensation)                                   │
│ ────────────────────────────────────────────────────────────────────────────────                      │
│ True Shareholder Yield: = 3.24%  (Net Float Shrink: -2.8% per year)                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ITTELSON CASH FLOW WATERFALL (CONVERTING REVENUE TO REAL CASH)                                         │
│                                                                                                        │
│ Revenue: $383.3B  ═══════════════════════════════════════════════════════════════════════════════════╗ │
│ Gross Profit: $170.8B (Margin: 44.6%)  ═══════════════════════════════════════════════╗              ║ │
│ Net Income: $100.4B (Margin: 26.2%)    ═══════════════════════════════╗              ║              ║ │
│ Cash Flow from Operations (CFO): $110.5B (CFO/NI: 1.10x - Clean) ═════╝              ║              ║ │
│ Free Cash Flow (FCF): $99.6B (FCF Conversion: 99.2%)                                 ║              ║ │
└───────────────────────────────────────────────────────────────────────────────────────┴──────────────┴─┘
```

---

### 4. LEVEL 3: THE INSTITUTIONAL ENGINE ROOM

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  [ LEVEL 1: COCKPIT ]          [ LEVEL 2: FLIGHT DECK ]        ★ [ LEVEL 3: ENGINE ROOM ]              │
├───────────────────────────────────────────────────┬────────────────────────────────────────────────────┤
│ BENEISH 8-VARIABLE FORENSIC MATRIX                │ STEPHEN PENMAN REFORMULATION (OPERATING VS FINANC) │
│ Threshold: M > -1.78 = Red Flag                   │                                                    │
│ Overall Beneish M-Score: -2.94 [ CLEAN ]          │ ROE = RNOA + [ FLEV × (RNOA - NBC) ]               │
│                                                   │ • RNOA (Core Operating Return): 48.2%              │
│ • DSRI  (Days Sales in Receivables):  1.02 [PASS] │ • FLEV (Debt Leverage Multiplier):  1.14           │
│ • GMI   (Gross Margin Index):         0.96 [PASS] │ • NBC  (Net Borrowing Cost):       3.2%            │
│ • AQI   (Asset Quality Index):        0.91 [PASS] │ • Spread (RNOA - NBC):             45.0%           │
│ • SGI   (Sales Growth Index):         1.06 [PASS] │ • Buyback Distortion Alert:        NONE            │
│ • DEPI  (Depreciation Rate Index):    0.98 [PASS] │                                                    │
│ • SGAI  (SG&A Efficiency Index):      0.97 [PASS] │ MARTIN FRIDSON REALITY SPREAD                      │
│ • LVGI  (Leverage Index):             0.94 [PASS] │ • EBITDA: $125.8B                                  │
│ • TATA  (Total Accruals to Assets):   0.02 [PASS] │ • CFO:    $110.5B                                  │
│                                                   │ • Spread (EBITDA - CFO): $15.3B (Normal working cap│
├───────────────────────────────────────────────────┴────────────────────────────────────────────────────┤
│ EDWARD ALTMAN DISTRESS & SOLVENCY SUITE                                                               │
│ • Altman Z-Score: 4.82  [ SAFE ZONE (Threshold > 2.99) ]                                               │
│   - X1 (Working Capital / Assets): 0.08                                                                │
│   - X2 (Retained Earnings / Assets): 0.22                                                              │
│   - X3 (EBIT / Assets): 0.34                                                                           │
│   - X4 (Market Value Equity / Liabilities): 3.82                                                       │
│   - X5 (Sales / Assets): 1.10                                                                          │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 10-YEAR COMMON-SIZE HISTORICAL STATEMENTS & MARGIN DRIFT                                               │
│ [Interactive Table: Income Statement % | Balance Sheet % | Cash Flow % | SEC EDGAR 10-K Links]       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 5. PLAIN-ENGLISH MICRO-COPY DICTIONARY

To eliminate financial jargon, tooltips and subtitles must translate technical ratios into human language:

| Technical Ratio | Plain-English Label | Beginner Tooltip / Translation |
|---|---|---|
| **FLEV** | Debt Leverage Multiplier | *"Measures how much debt magnifies returns. High leverage boosts profits in good times, but increases bankruptcy risk during recessions."* |
| **Sloan Accruals** | Cash Earnings Quality | *"Compares reported accounting profit to actual cash in the bank. High accruals warn that paper earnings may not turn into cash."* |
| **Beneish M-Score** | Accounting Red Flag Check | *"Statistically tests 8 accounting relationships to detect aggressive revenue recognition, capitalized expenses, or hidden costs."* |
| **Altman Z-Score** | Bankruptcy Safety Score | *"Evaluates debt, working capital, and earnings to determine if a company faces insolvency risk over the next 24 months."* |
| **Reverse DCF Hurdle** | Market Growth Hurdle | *"The annual free cash flow growth rate required over the next 10 years to justify today's stock price."* |
| **True Shareholder Yield**| Net Cash Returned to Owners | *"Total dividends and share repurchases, reduced by the new shares issued to executives as stock-based compensation."* |
| **Fridson Reality Spread**| EBITDA vs. Real Cash Spread | *"Checks if paper EBITDA is backed by actual cash flow. A large gap indicates cash is trapped in unpaid customer bills or unsold inventory."* |
| **Owner Earnings** | Buffett True Owner Profit | *"The actual cash a business generates after paying for the maintenance investments needed to protect its competitive position."* |

---

### 6. COMPONENT ARCHITECTURE (FOR FUTURE FRONTEND SPRINT)

```
frontend/src/
├── components/
│   ├── dossier/
│   │   ├── ExecutiveCockpit.tsx         # Level 1: 60s Cockpit
│   │   ├── VerdictBadge.tsx             # Safety verdict with color design tokens
│   │   ├── TrafficLightTile.tsx         # Moat / Solvency / Valuation cards
│   │   ├── ReverseDcfRuleBox.tsx        # Plain-English expectation translation
│   │   ├── DecisionBullets.tsx          # 3 Strengths, 1 Risk, 1 Index Hurdle
│   │   ├── FlightDeck.tsx               # Level 2: 5m Flight Deck
│   │   ├── LynchArchetypeCard.tsx       # Archetype classification & PEG
│   │   ├── ShareholderYieldBar.tsx      # Dividends + Buybacks - SBC SVG bar
│   │   ├── CashFlowWaterfall.tsx        # Pure SVG Ittelson conversion flow
│   │   ├── EngineRoom.tsx               # Level 3: Institutional Engine Room
│   │   ├── BeneishMatrix.tsx            # 8-variable manipulation breakdown
│   │   ├── PenmanDecompositionTable.tsx # Reformulated statements & FLEV
│   │   ├── AltmanZScoreCard.tsx         # 5-factor distress visualization
│   │   └── FactsheetPrintView.tsx       # Production-grade @media print memo
│   └── ui/
│       ├── Tooltip.tsx                  # Instant plain-English definition
│       └── CurrencyBadge.tsx            # Strict USD / CAD isolation pill
```

---
*Specification completed and saved. When ready for UI implementation, this blueprint will guide the frontend components.*
