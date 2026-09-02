# The 7-Step Equity Research Loop

This personal research application implements a repeatable 7-step equity-research loop designed to go from discovery to conviction without relying on black-box AI ratings or mixing currencies.

---

## 1. Find / Add Name
* **Screens:** `Desk (/)`, `Screen (/screen)`, `Search (App Header)`
* **Keyboard Shortcut:** Press `/` from any screen to focus the global search bar.
* **Actions:**
  * Search by ticker, company name, or composite ID (`US:TICKER:US` or `CA:TICKER:TSX`).
  * If a ticker is not in the library of ~720 pre-seeded companies, click **"Fetch from SEC / Yahoo"** to run an asynchronous ingest pipeline (`POST /api/v1/tickers/ingest`).
  * The state machine resolves identifiers, fetches annual 10-K/SEDAR filings, live prices/shares from Yahoo Finance, maps sector peers, and deterministically scores the company.

---

## 2. Business in One Sentence
* **Screen:** `Dossier (/c/:companyId)`
* **Section:** Header identity block
* **Actions:**
  * View the business summary (extracted from Yahoo Finance `longBusinessSummary`, truncated to 280 characters).
  * Direct links to primary SEC EDGAR filings (for US names and foreign ADRs like BABA via CIK) and SEDAR+ (for Canadian issuers).
  * Review trading currency, reporting currency, and filing type (`10-K`, `20-F`, `40-F`).

---

## 3. Financials + YoY
* **Screen:** `Dossier (/c/:companyId)`
* **Sections:**
  * **Latest Snapshot:** 18 key metrics including revenue, net income, EPS, FCF, gross margin, ROE, ROA, net debt, and market cap.
  * **Dividend Pack:** Current dividend yield and dividend per share (DPS).
  * **Annual History Table:** Audited multi-year history with YoY percentage change calculations.
  * **Quarterly Income Statement:** Last 4 quarters (revenue, net income, diluted EPS) when available.
  * **Trend Graph:** Visual revenue trend using only sanitized years (restated or suspect filings are cleanly flagged and excluded from growth math).

---

## 4. Valuation vs. Peers
* **Screens:** `Compare (/compare?ids=...)`, `Screen (/screen)`, `Sector (/sectors/:sheet)`
* **Actions:**
  * In Screener, multi-select rows and click **"Compare Selected (N) →"**; IDs stay persisted in the URL query string.
  * Valuation pillar compares PE, PB, and EV/EBITDA strictly against peers within the **same trading currency**.
  * Multi-currency views (`ALL`) hide native money columns to prevent cross-border currency distortion.

---

## 5. Risks / Flags
* **Screen:** `Dossier (/c/:companyId)`
* **Sections:**
  * **Coverage Status Ribbon:** Displays computed pillar coverage (e.g. `4/4 pillars`). Missing data triggers deterministic composite penalties (8% for 3/4, 20% for 2/4, 35% for 1/4).
  * **Provenance & Data Gaps:** Explicit warnings if shares, capex, or debt are missing. No invented numbers; missing fields remain `NULL`.
  * **Halal Screen:** AAOIFI compliance check (debt-to-market cap, interest-bearing deposits, impermissible revenue).
  * **Bank Path Flag:** For banks and financial institutions, corporate net debt, FCF, and gross margins are left blank by design.

---

## 6. Write a 5-Line Thesis
* **Screen:** `Dossier (/c/:companyId)`
* **Sections:**
  * **Moat & SWOT Draft:** Click **"Draft SWOT from numbers (not AI score)"** to generate a qualitative qualitative SWOT analysis via OpenRouter free model. Outputs: Strengths, Weaknesses, Opportunities, Threats, and Competitive Advantage (1 line). Deterministic fundamentals are never overwritten.
  * **Thesis Notepad:** Local notebook saved directly to browser `localStorage` (`thesis:{company_id}`). Enforces a 1000-character limit and displays an auto-saved timestamp.
  * **Toy DCF Calculator:** Exploratory valuation scratchpad (FCF, growth rate, WACC, projection years). Results are scratch calculations and never stored as ground truth. Automatically disabled for financial institutions.

---

## 7. Watch + Next Earnings
* **Screens:** `Dossier (/c/:companyId)`, `Desk (/)`
* **Actions:**
  * On Dossier, check the **Next Earnings** date card and click **"☆ Watch"** to pin the company to your desk.
  * On the Desk, the **Watchlist** displays current composite scores, signal badges, and the date the dossier was last opened.
  * Set local price or score threshold alerts (`localStorage stockAlerts`). If PE rises above your threshold or composite drops, an alert banner immediately surfaces on load.
  * Click **"Print / Save PDF"** for a clean, navigation-free one-page research briefing.
