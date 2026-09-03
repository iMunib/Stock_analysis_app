# Metric Catalog — Personal Equity Research Desk

> All metrics are deterministic math from filed data or the owner workbook. The AI assistant may reference these but cannot create, alter, or invent their values.

## Score Pillars (v1 — frozen, do not change weights)

| Pillar | Weight | What it measures |
|--------|--------|-----------------|
| **Quality** | 30% | Profitability and accounting quality: gross margin, FCF margin, ROE, ROA, CFO vs net income ratio |
| **Value** | 25% | Relative cheapness: PE, PB, EV/EBITDA vs peer set (same currency + industry) |
| **Growth** | 25% | Multi-year revenue, earnings, FCF CAGR — requires ≥3 sanitized FY rows |
| **Risk** | 20% | Solvency safety: D/E, interest coverage, altman-style leverage. Higher = safer |
| **Composite** | 0–10 | Weighted average. Reduced by coverage penalty if pillars are missing |

Coverage penalties: 4/4 = full, 3/4 = −8%, 2/4 = −20%, 1/4 = −35%.

---

## Valuation Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| **PE** | Price / Diluted EPS | Suppressed when price_currency ≠ reporting_currency |
| **PB** | Price / (Book Equity / Shares) | Blank if equity is negative |
| **EV/EBITDA** | Enterprise Value / EBITDA | Blank for banks/insurers by design |
| **EV** | Market Cap + Net Debt + Minority Interest | Debt-inclusive company price |
| **PEG** | PE / Expected EPS Growth | Unreliable if PE < 0 or growth undefined |
| **Graham Number** | √(22.5 × EPS × BVPS) | Graham floor value; not a target price |
| **NCAV/share** | (Current Assets − Total Liabilities) / Shares | Net-net deep value screen |
| **NNWC/share** | NCAV with receivable (0.75×) and inventory (0.5×) haircuts | Conservative net-net |
| **Margin of Safety** | (Graham Number − Price) / Graham Number | Negative = above intrinsic estimate |

---

## Profitability Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| **Gross Margin** | (Revenue − COGS) / Revenue | Blank for banks/insurers |
| **FCF Margin** | FCF / Revenue | Blank for banks/insurers |
| **ROE** | Net Income / Book Equity | Can be distorted by buybacks (AAPL case) |
| **ROA** | Net Income / Total Assets | Better cross-leverage comparison for banks |
| **ROIC** | NOPAT / Invested Capital | Suppressed when IC < 5% of assets (distortion) |
| **ROAA** | Net Income / Avg. Total Assets | Bank solvency profitability metric |
| **Operating Margin** | EBIT / Revenue | — |
| **Net Margin** | Net Income / Revenue | — |

---

## Penman Reformulated Statement Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| **NOA** | (Total Assets − Cash) − (Total Liabilities − Total Debt) | Net operating assets |
| **NFO** | Total Debt − Cash & ST Investments | Net financial obligations |
| **NOPAT** | EBIT × (1 − tax rate) | Tax clamped 15%–30%, default 21% |
| **RNOA** | NOPAT / NOA | Core operating return |
| **FLEV** | NFO / Book Equity | Financial leverage ratio |
| **NBC** | (Interest Expense × (1−tax)) / NFO | Net borrowing cost |
| **Penman ROE** | RNOA + FLEV × (RNOA − NBC) | Decomposes operating vs. leverage returns |
| **Identity Check** | Book Equity ≈ NOA − NFO (2% tolerance) | Data integrity flag |

> Banks and insurers are excluded from Penman analysis (financing/operating split not meaningful).

---

## Forensic / Earnings Quality Metrics (Schilit Framework)

| Flag | Signal | Interpretation |
|------|--------|----------------|
| **EQR** | 0–100 composite | Higher = cleaner accounting. <50 = forensic scrutiny needed |
| **CFO Decoupled** | CFO growth << Net Income growth | Accrual-heavy earnings — Sloan anomaly |
| **DSO Surge** | Receivables growing faster than revenue | Possible channel stuffing |
| **Inventory Buildup** | Inventory growing >> revenue | Demand weakness or production issues |
| **AQI Expense Cap** | Asset base growing >> revenue | Possible expense capitalization |
| **Accruals** | Net Income − CFO | High sustained accruals precede earnings disappointments |

---

## DCF / Valuation Engines

| Metric | Description | Invariants |
|--------|-------------|------------|
| **Reverse DCF** | FCF growth rate that justifies the current price (10yr, terminal 2.5%, WACC 9%) | Label: "market-implied" only — not a prediction |
| **Expectations Gap** | Market-implied growth minus historical 5yr FCF CAGR | Positive = market expects acceleration |
| **Sensitivity Matrix** | 5×5 grid of WACC × terminal growth → implied FCF growth | Deterministic only |
| **FCF Growth Hurdle** | Historical FCF CAGR vs 8% index benchmark (Malkiel) | Pass/Fail informational only |

---

## Balance Sheet / Capital Structure

| Metric | Formula | Notes |
|--------|---------|-------|
| **Net Debt** | Total Debt − Cash & ST Investments | Negative = net cash |
| **D/E Ratio** | Total Debt / Book Equity | — |
| **Interest Coverage** | EBIT / Interest Expense | <2x is elevated risk |
| **Book Equity** | Total Assets − Total Liabilities | Accounting net worth |
| **Total Assets** | Balance sheet total | — |
| **Working Capital** | Current Assets − Current Liabilities | — |

---

## Bank / Financial Institution Metrics

| Metric | Description | Notes |
|--------|-------------|-------|
| **CET1 Ratio** | Core equity tier 1 / Risk-weighted assets | >12% = well-capitalized; regulatory minimum ~8% |
| **NIM** | Net interest income / Earning assets | >3% healthy for North American banks |
| **Efficiency Ratio** | Non-interest expense / Revenue | Lower = better; <55% excellent, >65% weak |
| **ROAA** | Net income / Average total assets | >1% healthy; <0.5% weak |
| **Leverage Ratio** | Tier 1 capital / Total exposure | Regulatory solvency measure |
| **Total Capital Ratio** | All qualifying capital / Risk-weighted assets | Includes Tier 2 |

---

## Market / Trading Data

| Metric | Source | Currency Rule |
|--------|--------|--------------|
| **Price** | Yahoo Finance / provider | Always trading currency |
| **Market Cap** | Price × Shares | Trading currency |
| **Beta** | 5yr monthly vs S&P 500 | Unitless |
| **52w High/Low** | Provider | Trading currency |
| **50d / 200d MA** | Provider | Trading currency |
| **Short Ratio** | Shares short / Avg daily volume | Days to cover |
| **Institutional %** | Provider | % of float |
| **Insider %** | Provider | % of shares outstanding |
| **Short % of Float** | Short interest / Float | — |

---

## Data Confidence Levels

| Level | Criteria |
|-------|----------|
| **High** | Price ≤1 day old + filings ≤15 months + 4/4 pillars + same currency |
| **Medium** | Price 2–7 days old OR filings 15–24 months OR 3/4 pillars |
| **Low** | Price >7 days OR filings >24 months OR ≤2/4 pillars |
| **Insufficient** | <2/4 pillars — composite not computed |

---

## Score Signals

| Signal | Composite Range | Meaning |
|--------|-----------------|---------|
| `strong_candidate` | 8.0–10.0 | Strong on this method — investigate further |
| `constructive` | 6.5–8.0 | Solid but not exceptional |
| `mixed` | 5.0–6.5 | Trade-offs; more research needed |
| `weak` | 3.5–5.0 | Multiple concerns; caution warranted |
| `avoid` | 0–3.5 | Multiple red flags |
| `insufficient_data` | — | Not enough data for composite |

> These are research labels, not investment advice.

---

## Currency Rules (Invariant — Never Violate)

1. `USD` money values are never added to, subtracted from, or averaged with `CAD` values.
2. Cross-border comparisons use unitless ratios only (PE, PB, scores).
3. ADR companies with `reporting_currency ≠ price_currency` (e.g., BABA: CNY financials, USD price) have valuation multiples suppressed.
4. Scores and peer rankings may combine USD and CAD companies only because scores are unitless.

---

## Common-Size Financial Statements (Koyfin-Style)

| Metric | Normalization Base | Description & Drift Rules |
|--------|--------------------|---------------------------|
| **Common-Size Income Statement** | Total Revenue | Gross Profit, EBIT, EBITDA, Net Income, CFO, CapEx, FCF as % of Revenue |
| **Common-Size Balance Sheet** | Total Assets | Cash, Total Debt, Liabilities, Book Equity, Net Debt as % of Total Assets |
| **`MARGIN_CONTRACTION`** | 3-Year Drift | Flagged if Operating Margin declines by > 300 bps over up to 3 years |
| **`COST_CREEP`** | 3-Year Drift | Flagged if (Operating Expenses / Revenue) expands by > 200 bps over up to 3 years |

---

## Solvency & Distress Engine (Altman Z-Score)

| Metric | Formula | Interpretation & Exclusions |
|--------|---------|-----------------------------|
| **Altman Z-Score (Manufacturing)** | $1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 0.999 X_5$ | Safe: $Z > 2.99$; Grey: $1.81 \le Z \le 2.99$; Distress: $Z < 1.81$ |
| **Altman Z''-Score (Service / Tech)** | $6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$ | Safe: $Z'' > 2.60$; Grey: $1.10 \le Z'' \le 2.60$; Distress: $Z'' < 1.10$ |
| **$X_1$ (Working Capital / TA)** | $(Cash + 0.35 \times [TA - Cash] - CL) / TA$ | Liquidity factor |
| **$X_2$ (Retained Earnings / TA)** | Book Equity / Total Assets | Cumulative profitability / leverage proxy |
| **$X_3$ (EBIT / TA)** | Operating Income / Total Assets | Asset productivity / operating return |
| **$X_4$ (Market Value / TL)** | Market Capitalization / Total Liabilities | Insolvency buffer |
| **$X_5$ (Sales / TA)** | Total Revenue / Total Assets | Asset turnover (omitted from Z'' to prevent service distortion) |
| **Financial Institution Exclusion** | `financial_institution_excluded` | Automatically bypasses Banks and Insurers whose leverage profiles distort Z-scores |

---

## Capital Return & Shareholder Yield (Simply Wall St-Style)

| Metric | Formula | Description |
|--------|---------|-------------|
| **Net Repurchase Rate** | $-\frac{\Delta S}{S_{t-1}} \times 100$ | 1-year annual percentage reduction in shares outstanding |
| **Gross Buyback Yield** | $\text{Gross Buyback Cash} / \text{Market Cap} \times 100$ | Capital returned through market repurchases |
| **SBC Dilution Offset** | $\text{SBC Expense} / \text{Market Cap} \times 100$ | Drag from executive stock compensation dilution |
| **Net Buyback Yield** | $\max(0, \text{Gross Buyback Yield} - \text{SBC Offset})$ | True economic share count reduction yield |
| **SBC Drag %** | $\text{SBC Expense} / \text{Revenue} \times 100$ | Dilution overhead relative to annual revenue |
| **True Shareholder Yield (TSY)** | $\text{Dividend Yield} + \text{Net Buyback Yield}$ | Clean economic yield returned to public equity holders |
| **`ORGANIC_FLOAT_SHRINK`** | Net Repurchase Rate $> 2.0\%$ and SBC Drag $< 3.0\%$ | Authentic, disciplined equity float reduction |
| **`DILUTIVE_BUYBACKS`** | Repurchases $> 0$ but shares outstanding increased | Buybacks consumed entirely by executive stock options |

---

## Beneish M-Score & Forensic Manipulation Engine (1999)

The 8-variable probabilistic model for detecting earnings manipulation:
$$M = -4.84 + 0.920 \cdot DSRI + 0.528 \cdot GMI + 0.404 \cdot AQI + 0.892 \cdot SGI + 0.115 \cdot DEPI - 0.172 \cdot SGAI + 4.037 \cdot TATA + 0.0327 \cdot LVGI$$

| Variable | Name | Formula | Red Flag Threshold | Meaning |
|----------|------|---------|--------------------|---------|
| **DSRI** | Days Sales in Receivables Index | $(AR_t / Rev_t) / (AR_{t-1} / Rev_{t-1})$ | $> 1.0$ | Receivables growing faster than revenues (channel stuffing) |
| **GMI** | Gross Margin Index | Gross Margin$_{t-1}$ / Gross Margin$_t$ | $> 1.0$ | Deteriorating margin, incentive to manipulate |
| **AQI** | Asset Quality Index | $[1 - (CA_t + PPE_t) / TA_t] / [1 - (CA_{t-1} + PPE_{t-1}) / TA_{t-1}]$ | $> 1.0$ | Increasing capitalization of non-core expenses into assets |
| **SGI** | Sales Growth Index | $Rev_t / Rev_{t-1}$ | $> 1.0$ | High growth creates pressure to maintain trajectory |
| **DEPI** | Depreciation Index | Depr Rate$_{t-1}$ / Depr Rate$_t$ | $> 1.0$ | Slowing depreciation to inflate current earnings |
| **SGAI** | Sales & General Admin Index | $(SGA_t / Rev_t) / (SGA_{t-1} / Rev_{t-1})$ | $> 1.0$ | Decreasing administrative efficiency |
| **LVGI** | Leverage Index | Total Debt$_t$ / Total Debt$_{t-1}$ | $> 1.0$ | Increasing financial leverage and covenant pressure |
| **TATA** | Total Accruals to Total Assets | $(\text{Net Income}_t - CFO_t) / TA_t$ | $> 0.0$ | Non-cash accounting accruals relative to asset base |

- **Threshold**: $M > -1.78$ indicates high probability of accounting manipulation (**Red Flag / Manipulator Zone**). $M \le -1.78$ indicates low probability (**Clean Profile / Non-manipulator Zone**).
- **Exclusion**: Regulated financial institutions (Banks & Insurers) are excluded automatically (`financial_institution_excluded`) as standard accrual formulations do not apply to bank capital structures.

---

## ETF & Index Universe Cohorts

| Universe Tag | Index / Basket | Inclusion & Screening Criteria |
|--------------|----------------|--------------------------------|
| **SP500** | S&P 500 | US large-cap benchmark |
| **TSX** | S&P/TSX Composite | Canadian equities benchmark |
| **SPUS** | SP Funds S&P 500 Sharia Industry ETF | Sharia-compliant US large caps (AAOIFI debt & cash filters) |
| **QQQ** | Invesco QQQ Trust | Nasdaq 100 top non-financial innovative secular leaders |
| **VONV** | Vanguard Russell 1000 Value ETF | High book-to-price, low EV/EBITDA, Graham value floor candidates |

---

## Sector Percentile Matrix (Koyfin-Style)

Calculated across 8 core ratios against same-currency sector peer groups:
$$\text{Percentile} = \frac{\text{Number of peers with worse metric}}{\text{Total peers in group}} \times 100$$

1. **P/E Ratio** (Inverted: lower P/E = higher percentile)
2. **EV/EBITDA** (Inverted: lower multiple = higher percentile)
3. **P/B Ratio** (Inverted: lower P/B = higher percentile)
4. **ROE** (Higher is better)
5. **ROIC / Penman RNOA** (Higher is better)
6. **FCF Margin** (Higher is better)
7. **Net Debt / EBITDA** (Inverted: lower leverage = higher percentile)
8. **Total Shareholder Yield** (Higher is better)
