# DATA_CONTRACT.md — Field Dictionary & Import Rules

Source of record: `seed/Sector_Financials_Final_Owner.xlsx` (owner workbook,
"Phase 7 final polish", 2026-08-22) and its `00_README` sheet / `seed/readme.md`.
Every number is in the company's **native reporting currency** (US names: USD;
Canadian names: CAD). Nothing was converted anywhere.

## Identity rules

### Company_ID (frozen format)

- `US:TICKER:US` for US-listed names, `CA:TICKER:TSX` for Canadian-listed names.
- Dots are kept in tickers (e.g. `CA:BN:TSX` = Brookfield Corporation).
- `CA:NA:TSX` is **National Bank of Canada**, never NVIDIA.
- `Company_ID` is the primary key everywhere; it is never derived from ticker
  alone (collisions exist: HON vs HONA, KEY US vs KEY CA).

### Sheets used by the importer

| Sheet | Role |
|-------|------|
| `01_All_Companies` | master table, exactly 720 rows, one per unique company |
| `06_Placements` | where each company appears: Primary_Sheet + Extra_Sheets (pipe-separated) + GICS_Sheet |
| `03_Data_Quality` | per-company QC notes (Company_ID, Ticker, Field, Issue, Source_Attempted, Retrieval_Date, Resolution, Notes) |
| custom industry tabs, GICS_* tabs | presentation copies — NOT imported as rows; only their placement info matters |

**Extra rows are copies, not companies.** The company count is always 720; the
union of Company_IDs across all tabs equals 01_All_Companies. Placements are
imported as (company_id, sheet_name, role=Primary|Extra|GICS) rows and never
inflate `companies`.

### 03_Data_Quality ID normalization (observed quirk)

Quality-sheet IDs sometimes carry an exchange suffix (`US:AES:NYSE`,
`US:APA:NASDAQ`) instead of the frozen format (`US:AES:US`, `US:APA:US`). The
importer normalizes them (`US:<TICKER>:<anything>` → `US:<TICKER>:US`;
`CA:<TICKER>:<anything>` → `CA:<TICKER>:TSX`) before matching, and keeps the raw
ID text in the flag note when normalization fails.

## Column dictionary — 01_All_Companies (57 columns)

### Identity / classification

| Column | Type | Meaning |
|--------|------|---------|
| Company_ID | text (PK) | frozen ID, see above |
| Company_Name | text | legal/display name |
| Primary_Ticker | text | listing ticker without suffix |
| Country_of_Listing | text | `US` or `CA` |
| Currency | text | native reporting currency of all money fields: `USD` or `CAD` |
| GICS_Sector | text | official GICS sector |
| GICS_Industry | text | GICS industry level for TSX names; GICS **sub**-industry for US names (finest offline level — owner decision, see Phase 7 report) |
| Custom_Industry_Sheet | text | home tab (30 values); drives Primary placement and Phase 3 peer sets |
| Exchange | text | listing exchange (often blank in seed) |
| In_SP500 / In_TSX_Composite | text Yes/No | index membership (stored also as JSON list `indexes`) |
| Extraction_Status | text | build provenance (e.g. COMPLETE) |
| Source_Primary | text | data source (e.g. EDGAR) |
| Fiscal_Year_End | text | FY end marker when present |

### Money / statement columns (native currency, USD millions per owner prose but stored verbatim — see scale note)

| Column | Meaning |
|--------|---------|
| Revenue | latest FY top line; **blank for most banks** (no GAAP revenue concept for deposit-funded lenders) |
| TopLine_Alt | net interest income — bank-equivalent top line; populated for SYF and TFC only |
| Net_Income | FY bottom-line profit |
| Diluted_EPS | diluted EPS for the FY |
| Gross_Profit | revenue − cost of sales; meaningless for banks/insurers → blank |
| Operating_Cash_Flow | cash from operations, FY |
| Capex | purchases of PP&E (negative = cash out) |
| FCF_Reported | vendor-reported FCF when available |
| Free_Cash_Flow | alternate/vendor FCF variant kept for reference |
| FCF_Calc | Operating_Cash_Flow − abs(Capex); **deliberately blank for banks/insurers** |
| NetDebt_Calc | Total_Debt − Cash_ST_Investments |
| Total_Debt | short+long-term debt incl. leases; **mostly blank for banks/insurers on purpose** (deposits fund their assets) |
| Book_Equity | stockholders' equity at FY end |
| Cash_ST_Investments | cash + short-term investments at FY end |
| Total_Assets / Total_Liabilities | balance sheet totals |
| EBIT | operating income, FY |
| EBITDA | EBIT + D&A where disclosed |
| Interest_Expense | FY interest expense |

### Ratio columns (unitless — the honest cross-border lens)

| Column | Definition |
|--------|-----------|
| FCFMargin_Calc | FCF_Calc / Revenue |
| GrossMargin_Calc | Gross_Profit / Revenue |
| ROE_Calc | Net_Income / **ending** Book_Equity (not average) |
| ROA_Calc | Net_Income / ending Total_Assets |
| PE_Calc | Price / Diluted_EPS (blank when EPS missing or negative) |
| PB_Calc | Market_Cap / Book_Equity |
| EV_Calc | Market_Cap + Total_Debt − Cash_ST_Investments |
| EV_to_EBITDA_Calc | EV_Calc / EBITDA |

### Price / snapshot

| Column | Meaning |
|--------|---------|
| Price | snapshot share price |
| Price_Currency | trading currency of the price (USD or CAD — NOT both) |
| Price_AsOf | date of the price snapshot (ISO text in seed) |
| Shares_Snapshot | shares outstanding at snapshot date; basis of Market_Cap |
| Market_Cap | Price × Shares_Snapshot in trading currency |
| Fill_OK / Membership_Flag | build QC flags |

### Bank/insurer regulatory fields (populated only where sourced)

| Column | Meaning |
|--------|---------|
| CET1_Ratio | Common Equity Tier 1 ratio |
| CET1_Approach | how CET1 was determined |
| CET1_Requirement_or_Target | regulatory requirement/target for comparison |
| Total_Capital_Ratio | regulatory total capital ratio |
| Leverage_Ratio | regulatory leverage ratio |
| NIM_FY2025 / NIM_Q4_2025 | net interest margin, full year / Q4 |
| Efficiency_Ratio | non-interest expense / revenue (banks) |
| ROAA | return on average assets (banks) |

## Currency rules

1. Every money field carries the company's `Currency` (on the company row and on
   each financial snapshot row). **No conversion ever happens at import or in
   Phase 1 storage.**
2. Comparisons across currencies use **unitless ratios only** (ROE_Calc,
   ROA_Calc, FCFMargin_Calc, GrossMargin_Calc, PE_Calc, PB_Calc,
   EV_to_EBITDA_Calc). Comparing CAD Revenue to USD Revenue is forbidden.
3. Market_Cap is compared within a country/currency only.

## Missing-data policy

- A blank workbook cell is stored as SQL **NULL — never 0, never guessed, never
  backfilled** from another company (e.g. HON numbers must never be copied to
  US:HONA:US; Hydro One is CA:H:TSX and never mixed with either).
- Banks/insurers keep their **intentional blanks** (Total_Debt, Gross_Profit,
  FCF_Calc, ...) — these are design, not defects.
- Import-time gaps discovered in `03_Data_Quality` are carried into
  `data_quality_flags` with the raw note text preserved.
- Known honest leftovers in the seed (kept blank, flagged): US:HONA:US (no annual
  filing yet), CA:IIP.UN:TSX (no reliable annual source), US:APA:US (no standard
  revenue tag), SYF/TFC top line in TopLine_Alt, 26 names with Price but no
  Shares_Snapshot/Market_Cap (never guessed).

## As-of dating rules (Phase 1)

- The workbook has **no fiscal-year column** → `financial_snapshots.fiscal_year`
  is stored **NULL** (never invented). `period_type` = `'FY'`.
- `as_of_date` = the row's `Price_AsOf` date (the only firm as-of in the seed),
  else NULL.
- `source` = the source workbook filename. `imported_at` and the workbook's
  filename + mtime are recorded in `import_runs` for provenance.
- Future phases may add annual rows (fiscal_year set); the schema
  (unique on company_id + fiscal_year + period_type) already supports that
  without a rewrite.

## Observed value-scale note (honest discrepancy)

The owner README prose says money is in "millions", but the observed workbook
cells store values **verbatim in actual dollars** (e.g. US:MMM Revenue =
24,948,000,000 ≈ $24.9B actual). The importer stores what the cell says, without
rescaling. Consumers must treat magnitudes as raw workbook values and rely on
ratios for comparison until a later phase documents a normalization step.
**Phase 2 confirms the same convention for providers**: SEC XBRL and Yahoo both
report actual currency units and are persisted as given. Do not divide or
multiply by 1e6 anywhere; treat all stored statement values as currency units.

## Phase 2 — provider layer, provenance, and ingest policy

### Provenance on every snapshot

- `source` ∈ {`Sector_Financials_Final_Owner.xlsx` (seed rows), `sec_companyfacts`, `yfinance`}.
- `fetched_at` — UTC timestamp of the provider pull.
- `provider_as_of` — provider-reported period end for that fiscal year
  (statement as-of; price snapshots keep the separate `price_asof`).

### Provider routing (registry)

| Listing | Statements | Price |
|---------|-----------|-------|
| US | SEC companyfacts (one call per CIK, 10-K FY frames; User-Agent from SEC_USER_AGENT; token bucket 8 req/s; back off on 403/429) | yfinance |
| CA | yfinance annual financials/balance/cashflow (sparse history accepted, never padded; serialised 0.2s) | yfinance |

SEDAR+ has no public bulk API and is NOT scraped in v1. CIK lookups for unknown
US tickers use https://www.sec.gov/files/company_tickers.json (cached at
`data/sec_tickers_cache.json`).

### Identity mapping (`seed/raw/universe_master.csv` is authoritative)

- All 720 seed names carry a ready `Yahoo_Ticker` (incl. share-class conversions
  such as `IIP.UN` → `IIP-UN.TO`); the 500 US names also carry numeric CIKs in
  `CIK_SEDAR`.
- For CA rows the csv `Ticker` column is the bare ticker (`RY`) while
  `Primary_Ticker` is Yahoo-style (`RY.TO`); Company_IDs always use the bare form.
- Yahoo symbol rules: US = plain ticker (`AAPL`); CA = `.TO` suffix with dots
  converted to hyphens (`IIP.UN` → `IIP-UN.TO`); a csv `Yahoo_Ticker` wins when present.
- Quality-sheet loose IDs normalize (`US:AES:NYSE` → `US:AES:US`); the frozen-format
  validator strictly rejects `CA:*:NYSE`-style ids.

### Overwrite policy (frozen)

1. Seed FY rows (`fiscal_year NULL`, `source` = owner xlsx filename) are **never
   overwritten** by providers on that pseudo-year.
2. Providers may **FILL NULLS** on the seed row; non-NULL owner values are
   restored even if a provider returned a different number.
3. Provider statements **INSERT** their own rows keyed
   `(company_id, fiscal_year, period_type='FY')` with their own `source`.
4. When two providers claim the same fiscal year, the first provider's non-NULL
   values win; the second only fills NULL fields.
5. Cache rule: an existing `fiscal_year` row from the same `source` means **no
   network re-hit** unless `refresh=true`.

### Quality-flag audit (Phase 2)

Phase 1 stored 2,016 of 2,026 quality-sheet rows. The 10 unmatched rows all carry
the pseudo-ID `(workbook)` — they are workbook-level QC notes
(SIGN_CONVENTION_MIXED, BANK_EXCLUSION_BY_DESIGN, PHASE3_SUMMARY, ...), not
company rows. Phase 2 stores them with `company_id NULL` (workbook-level flags),
so 2,026/2,026 rows are retained and nothing is silently dropped.
