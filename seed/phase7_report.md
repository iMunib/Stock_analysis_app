# Phase 7 Report -- 2026-08-22
- Input: Sector_Financials_QA.xlsx (read-only, 1,096,408 bytes, mtime untouched).
- Output: Sector_Financials_Final_Owner.xlsx (1,015,448 bytes).
- Scope: polish only. No scrape, no ranking, no refresh.py, no universe change. Rows remain 720.

## Task A -- placements
- Removed Hartford (US:HIG:US) Extra from Autos ('Hartford' substring-of-'Ford' accident).
- Removed 9 Credit_Services false positives (exchange/data businesses):
  - US:CME:US (financial exchanges and data)
  - US:CBOE:US (financial exchanges and data)
  - US:ICE:US (financial exchanges and data)
  - US:NDAQ:US (financial exchanges and data)
  - US:MCO:US (financial exchanges and data)
  - US:MSCI:US (financial exchanges and data)
  - US:SPGI:US (financial exchanges and data)
  - US:FDS:US (financial exchanges and data)
  - US:BR:US (data processing and outsourced services)
- Kept JKHY on Credit_Services: GICS sub-industry 'transaction and payment processing services' is clearly Transaction & Payment Processing.
- Added Extras (no Primary touched): Dollarama CA:DOL:TSX + Couche-Tard CA:ATD:TSX -> Discount_Stores.
- Pipelines_Midstream: CA:KEY:TSX and CA:PPL:TSX were already Extra there -- no-op, verified.
- Placement diffs applied: 12 companies.
- Union of Company_IDs across all topic sheets re-verified == 720. No new companies. No AAL.

## Task B -- formatting
- Helper columns dropped (100% blank): ['Fill_Notes', 'Net_Income_TS_Fill_FY', 'Revenue_TS_Fill_FY', 'Total_Debt_TS_Fill_FY'] on 42 sheets. TopLine_Alt (SYF/TFC) and Placement_Role kept.
- Widths: Company_ID 18 / Company_Name 34 / Primary_Ticker 12 / GICS_Sector 22 / GICS_Industry 28 / Custom_Industry_Sheet 22 / money 14 / ratios 10 / Price 10 / Market_Cap 16 / Extraction_Status 14 / Source_Primary 12; others autofit clamped 9-26.
- Header row 36px, wrap, vertical center; data rows 16px, no wrap; freeze B2; autofilter; navy header; banded rows; grey blanks; pale-green Extras. No padding to 1500 rows. No ListObjects.

## Task C -- cheap fills
- GICS_Industry filled for 500 US rows from Universe.GICS_Sub_Industry (Universe.GICS_Industry is blank for ALL 500 US rows -- noted honestly in README; TSX rows already had true industry values and were not touched).
- Market_Cap = Price x Shares_Snapshot: 0 rows qualified (none had all three conditions). 26 rows have Price but neither MC nor Shares -- left blank by rule:
  - US:ADI:US, US:AZO:US, US:BBY:US, US:COO:US, US:DAL:US, US:EL:US, US:HPQ:US, US:HD:US, US:HRL:US, US:KR:US, US:LOW:US, US:MU:US, US:PHM:US, US:CRM:US, US:TGT:US, US:VMRK:US, CA:BLX:TSX, CA:DOO:TSX, CA:DOL:TSX, CA:KEY:TSX, CA:NFI:TSX, CA:NWC:TSX, CA:NPI:TSX, CA:PBH:TSX, CA:RCH:TSX, CA:WPK:TSX
- No Revenue/NI/Debt invented. HON never copied onto HONA.

## Task D -- README
- README.md written at project root; identical content placed on 00_README sheet (wrapped, col A width 110). Covers: what the file is, product-file status, sheet map, Primary vs Extra, cross-border comparison rules, full column dictionary, honest leftovers, update instructions.

## Task E -- asserts
- 720 unique on 01_All_Companies: PASS
- Costco+Walmart+Dollarama on Discount_Stores: PASS
- Hartford NOT on Autos: PASS
- Hydro One on Utilities_Regulated: PASS
- V and MA on Credit_Services: PASS
- No Excel Tables (zip-level check): PASS
- README.md exists and 00_README detailed (>60 lines): PASS
- Company_Name width >= 28 on All_Companies (set 34): PASS
- CA:NA:TSX = 'National Bank of Canada': PASS
- US:HONA:US='Honeywell Aerospace' - US:HON:US='Honeywell Technologies' - 'Hydro One Limited': PASS
- Airlines == DAL/UAL/LUV/AC exactly: PASS; primary partition sums to 720: PASS

## Sheet row counts after Phase 7
- 00_README: 184 lines
- 01_All_Companies: 720
- 02_Coverage: 31
- 03_Data_Quality: 2026
- 04_Collisions: 14
- 05_Membership: 720
- 06_Placements: 720
- Airlines: 4 (P=4, E=0)
- Autos: 5 (P=4, E=1)
- Banks: 39 (P=39, E=0)
- Biotech: 8 (P=7, E=1)
- Comm_Services: 26 (P=1, E=25)
- Consumer_Cyclical: 33 (P=33, E=0)
- Consumer_Defensive: 20 (P=20, E=0)
- Consumer_Goods: 22 (P=22, E=0)
- Credit_Services: 14 (P=4, E=10)
- Discount_Stores: 9 (P=2, E=7)
- Fast_Food_Restaurants: 7 (P=7, E=0)
- Financials: 25 (P=25, E=0)
- Industrials: 102 (P=102, E=0)
- Insurance: 32 (P=32, E=0)
- Internet_Platforms: 6 (P=4, E=2)
- Materials: 82 (P=82, E=0)
- Medical_Devices_Services: 45 (P=45, E=0)
- Networking: 6 (P=6, E=0)
- Oil_Gas_Producers: 54 (P=54, E=0)
- Pharma: 10 (P=10, E=0)
- Pipelines_Midstream: 12 (P=6, E=6)
- Railroads: 5 (P=5, E=0)
- Real_Estate: 50 (P=50, E=0)
- Retail: 29 (P=18, E=11)
- Semiconductors_Components: 20 (P=20, E=0)
- Software: 29 (P=29, E=0)
- Streaming_Entertainment: 12 (P=12, E=0)
- Tech: 27 (P=27, E=0)
- Telecom: 12 (P=9, E=3)
- Utilities_Regulated: 41 (P=41, E=0)
- GICS_Communication_Services: 26 (P=0, E=26)
- GICS_Consumer_Discretionary: 62 (P=0, E=62)
- GICS_Consumer_Staples: 44 (P=0, E=44)
- GICS_Energy: 60 (P=0, E=60)
- GICS_Financials: 100 (P=25, E=75)
- GICS_Health_Care: 62 (P=0, E=62)
- GICS_Industrials: 111 (P=102, E=9)
- GICS_Information_Technology: 82 (P=0, E=82)
- GICS_Materials: 82 (P=82, E=0)
- GICS_Real_Estate: 50 (P=0, E=50)
- GICS_Utilities: 41 (P=0, E=41)