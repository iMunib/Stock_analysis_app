NORTH AMERICAN FINANCIALS - OWNER WORKBOOK (Phase 7 final polish)
Prepared: 2026-08-22.  Source of record built through Phase 6 QA.

WHAT THIS FILE IS
This workbook is a research snapshot of the financial statements of the companies in two stock
indexes: the US S&P 500 and the Canadian S&P/TSX Composite - 720 unique companies in total.
Every number is in each company's NATIVE reporting currency: US companies report USD millions,
Canadian companies report CAD millions. Nothing was converted between currencies anywhere in
this file. It covers ONLY index members - it is NOT the whole North American stock market, and
it is NOT investment advice. It is an information compilation for personal research.

WHICH FILE IS THE PRODUCT
This file, Sector_Financials_Final_Owner.xlsx, IS the product. Earlier files in the project
(NA_Company_Financials.xlsx, Sector_Financials_QA.xlsx, CleanView, etc.) are intermediate
build artifacts. If you open any other file you are looking at history, not the deliverable.

SHEET MAP
    00_README                    This explanation sheet.
    01_All_Companies             THE master table: exactly 720 rows, one row per unique company
                                 (key = Company_ID). If it is not here, it is not in the study.
    02_Coverage                  Field-by-field coverage counts (how full each column is).
    03_Data_Quality              Per-company QC notes and flags carried from the build phases.
    04_Collisions                Ticker/name collision audit (e.g. HON vs HONA, KEY US vs CA).
    05_Membership                Which index(es) each company belongs to, with provenance.
    06_Placements                Where each company appears: its home (Primary) sheet plus every
                                 Extra copy, pipe-separated.
Custom industry tabs:
    Airlines                     rows=   4  (Primary=4, Extra=0)
    Autos                        rows=   5  (Primary=4, Extra=1)
    Banks                        rows=  39  (Primary=39, Extra=0)
    Biotech                      rows=   8  (Primary=7, Extra=1)
    Comm_Services                rows=  26  (Primary=1, Extra=25)
    Consumer_Cyclical            rows=  33  (Primary=33, Extra=0)
    Consumer_Defensive           rows=  20  (Primary=20, Extra=0)
    Consumer_Goods               rows=  22  (Primary=22, Extra=0)
    Credit_Services              rows=  14  (Primary=4, Extra=10)
    Discount_Stores              rows=   9  (Primary=2, Extra=7)
    Fast_Food_Restaurants        rows=   7  (Primary=7, Extra=0)
    Financials                   rows=  25  (Primary=25, Extra=0)
    Industrials                  rows= 102  (Primary=102, Extra=0)
    Insurance                    rows=  32  (Primary=32, Extra=0)
    Internet_Platforms           rows=   6  (Primary=4, Extra=2)
    Materials                    rows=  82  (Primary=82, Extra=0)
    Medical_Devices_Services     rows=  45  (Primary=45, Extra=0)
    Networking                   rows=   6  (Primary=6, Extra=0)
    Oil_Gas_Producers            rows=  54  (Primary=54, Extra=0)
    Pharma                       rows=  10  (Primary=10, Extra=0)
    Pipelines_Midstream          rows=  12  (Primary=6, Extra=6)
    Railroads                    rows=   5  (Primary=5, Extra=0)
    Real_Estate                  rows=  50  (Primary=50, Extra=0)
    Retail                       rows=  29  (Primary=18, Extra=11)
    Semiconductors_Components    rows=  20  (Primary=20, Extra=0)
    Software                     rows=  29  (Primary=29, Extra=0)
    Streaming_Entertainment      rows=  12  (Primary=12, Extra=0)
    Tech                         rows=  27  (Primary=27, Extra=0)
    Telecom                      rows=  12  (Primary=9, Extra=3)
    Utilities_Regulated          rows=  41  (Primary=41, Extra=0)
GICS sector tabs:
    GICS_Communication_Services    rows=  26  (copies of rows, grouped by GICS sector)
    GICS_Consumer_Discretionary    rows=  62  (copies of rows, grouped by GICS sector)
    GICS_Consumer_Staples          rows=  44  (copies of rows, grouped by GICS sector)
    GICS_Energy                    rows=  60  (copies of rows, grouped by GICS sector)
    GICS_Financials                rows= 100  (copies of rows, grouped by GICS sector)
    GICS_Health_Care               rows=  62  (copies of rows, grouped by GICS sector)
    GICS_Industrials               rows= 111  (copies of rows, grouped by GICS sector)
    GICS_Information_Technology    rows=  82  (copies of rows, grouped by GICS sector)
    GICS_Materials                 rows=  82  (copies of rows, grouped by GICS sector)
    GICS_Real_Estate               rows=  50  (copies of rows, grouped by GICS sector)
    GICS_Utilities                 rows=  41  (copies of rows, grouped by GICS sector)

PRIMARY VS EXTRA
Every company lives once on 01_All_Companies. On the topic tabs a row is either 'Primary'
(its Custom_Industry_Sheet home tab) or 'Extra'. Extra rows are PALE GREEN and they are
COPIES, not different companies: Dollarama appears on Consumer_Defensive (Primary) and again
on Discount_Stores and Retail (Extra copies). The total number of COMPANIES is always 720;
the tabs just repeat members where the classification overlaps. Never add or sum a company
across tabs.

HOW TO COMPARE COMPANIES
Work one sheet at a time, and within a sheet compare only USD-to-USD or CAD-to-CAD. NEVER
compare CAD millions against USD millions directly - a Canadian bank's Revenue is not
directly comparable to a US bank's. For cross-border comparisons use the unitless ratios:
ROE_Calc, ROA_Calc, FCFMargin_Calc, GrossMargin_Calc, PE_Calc, PB_Calc, EV_to_EBITDA_Calc.
Ratios cancel the currency (mostly) and are the honest cross-border lens. For scale, convert
at your own rate outside this file, or compare Market_Cap within a country only.

COLUMN DICTIONARY (money/ratio columns)
    Revenue                 Latest fiscal-year top line, native currency. Most banks have it blank
                            because GAAP has no revenue concept for deposit-funded lenders.
    TopLine_Alt             Net interest income - the bank-equivalent of revenue; populated for
                            Synchrony (SYF) and Truist (TFC), whose income statement reports it.
    Net_Income              Fiscal-year bottom-line profit, native currency.
    Diluted_EPS             Diluted earnings per share for the fiscal year.
    Gross_Profit            Revenue minus cost of sales. Meaningless for banks/insurers; blank there.
    Operating_Cash_Flow     Cash generated by operations over the fiscal year.
    Capex                   Purchases of property/plant/equipment (shown negative = cash out).
    FCF_Reported            Free cash flow as reported by the vendor, when available.
    Free_Cash_Flow          Alternate/vendor FCF variant retained for reference.
    FCF_Calc                Operating_Cash_Flow - abs(Capex). Deliberately blank for banks and
                            insurers, where OCF/capex is not a meaningful FCF definition.
    NetDebt_Calc            Total_Debt - Cash_ST_Investments.
    FCFMargin_Calc          FCF_Calc divided by Revenue.
    GrossMargin_Calc        Gross_Profit divided by Revenue.
    ROE_Calc                Net_Income divided by ENDING Book_Equity (not average equity).
    ROA_Calc                Net_Income divided by ending Total_Assets.
    PE_Calc                 Price divided by Diluted_EPS; blank when EPS is missing or negative.
    PB_Calc                 Market_Cap divided by Book_Equity.
    EV_Calc                 Market_Cap + Total_Debt - Cash_ST_Investments.
    EV_to_EBITDA_Calc       EV_Calc divided by EBITDA.
    Total_Debt              Short- plus long-term debt incl. lease obligations where tagged.
                            Mostly blank for banks/insurers ON PURPOSE: deposits fund their assets,
                            so a corporate-style debt number would mislead.
    Book_Equity             Stockholders' equity at fiscal year end.
    Cash_ST_Investments     Cash and short-term investments at fiscal year end.
    Total_Assets            Balance-sheet total assets.
    Total_Liabilities       Balance-sheet total liabilities.
    EBIT                    Operating income for the year.
    EBITDA                  EBIT plus depreciation/amortization where disclosed.
    Interest_Expense        Interest expense for the fiscal year.
    Price / Price_Currency  Snapshot share price and its trading currency (USD or CAD).
    Price_AsOf              Date of the price snapshot.
    Shares_Snapshot         Shares outstanding at the snapshot date; basis of Market_Cap.
    Market_Cap              Price x Shares_Snapshot in trading currency (USD or CAD, NOT both).
    CET1_* / Total_Capital_Ratio / Leverage_Ratio   Regulatory capital metrics, big-6 Canadian
                            banks + US peers, taken from filings/supplements.
    NIM_FY2025 / NIM_Q4_2025   Net interest margin, full year and Q4.
    Efficiency_Ratio        Non-interest expense over revenue (banks).
    ROAA                    Return on average assets (banks).
    GICS_Sector             Official GICS sector. GICS_Industry: official industry level for TSX
                            names; for US names this column carries the GICS SUB-industry (the
                            finer level available offline) - see Phase 7 report note.
    Custom_Industry_Sheet   Home tab chosen for the company (drives Primary placement).
    Company_ID              Stable key: US:TICKER:US or CA:TICKER:TSX. Note CA:NA:TSX is National
                            Bank of Canada (ticker NA.TO), NOT NVIDIA-related.
    Placement_Role          'Primary' (home tab row) or 'Extra' (pale-green copy row).
    Extraction_Status / Source_Primary / Fill_OK / Membership_Flag   Build provenance and QC flags.

HONEST LEFTOVERS (things we could NOT fill and why
    - US:HONA:US Honeywell Aerospace: interim-only SEC filer, no annual filing exists yet, so
      Revenue/Net_Income are blank. We did NOT copy numbers from HON (Honeywell Technologies) -
      different company. Hydro One is CA:H:TSX and is likewise never mixed up with either.
    - CA:IIP.UN:TSX InterRent REIT: no reliable annual data source found; statement fields blank.
    - US:APA:US APA Corporation: EDGAR tags no standard annual revenue concept; left blank rather
      than invented. SYF/TFC top line sits in TopLine_Alt as net interest income (see above).
    - Total_Debt on most banks/insurers: intentionally blank (not comparable; see dictionary).
    - Airlines tab has exactly 4 companies because only DAL, UAL, LUV (S&P 500) and AC (TSX
      Composite) are index members. AAL is NOT in the S&P 500, so it is not in this universe.
    - 26 companies show a Price but no Market_Cap and no shares snapshot; we do not guess.

HOW TO UPDATE THIS FILE (for whoever comes next)
    1. DO NOT run refresh.py --mode all. It re-scrapes everything and can overwrite hand-fixed
       values. Treat the statement columns as frozen unless you fix a specific company.
    2. Index membership changes only: add/remove members when S&P announces changes. Keep the
       Company_ID convention exactly: US:TICKER:US or CA:TICKER:TSX (dots kept, e.g. CA:BN:TSX).
    3. To add a company: one row on 01_All_Companies, set Custom_Industry_Sheet, then add it to
       06_Placements and to whichever topic tabs need an Extra copy (pale green). The union of
       Company_IDs across all tabs must stay equal to 01_All_Companies.
    4. Re-run the Phase 7 assert block after any change; it fails loudly on drift.

PHASE 7 CHANGELOG (2026-08-22)
    - Removed false-positive Extra placements:
        * Hartford (HIG) off Autos (name-substring accident: 'Hartford' contains 'Ford').
        * CME Group (CME) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * Cboe Global Markets (CBOE) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * Intercontinental Exchange (ICE) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * Nasdaq, Inc. (NDAQ) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * Moody's Corporation (MCO) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * MSCI (MSCI) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * S&P Global (SPGI) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * FactSet (FDS) off Credit_Services (industry='financial exchanges and data' - exchange/data, not payments).
        * Broadridge Financial Solutions (BR) off Credit_Services (industry='data processing and outsourced services' - exchange/data, not payments).
        Kept despite ticker list: US:JKHY:US (transaction and payment processing services).
    - Added Extra copies (Primary rows untouched, no new companies):
        * Dollarama (CA:DOL:TSX) and Couche-Tard (CA:ATD:TSX) onto Discount_Stores.
        * Keyera (CA:KEY:TSX) and Pembina (CA:PPL:TSX) were already Extra on Pipelines_Midstream.
    - Dropped 100%-blank helper columns (Fill_Notes, *_TS_Fill_FY) from every data sheet.
    - Standardized formatting: widths, 36px wrapped navy headers, 16px data rows, freeze B2,
      autofilter, banded rows, grey blanks, pale-green Extras. No Excel Tables anywhere.
    - Filled US GICS_Industry display field from Universe GICS Sub-Industry (US industry level
      was blank offline); 500 rows updated. No scrape performed.
    - Market_Cap back-fill check: 0 rows were fillable (every Price-without-MC row also lacks
      Shares_Snapshot); those 26 IDs are listed in logs/phase7_report.md.

NOT INVESTMENT ADVICE.
