# -*- coding: utf-8 -*-
"""Phase 2.7 — CA bank extraction (RY/TD/BMO) + NIM write-through corrections."""
import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill

ROOT = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research"
RAW = os.path.join(ROOT, "raw")
XLSX = os.path.join(ROOT, "NA_Company_Financials.xlsx")

wb = openpyxl.load_workbook(XLSX)
HDR_FILL = PatternFill("solid", fgColor="1F4E78"); HDR_FONT = Font(bold=True, color="FFFFFF")

BR_COLS = ["Ticker", "Company_Name", "CET1_Ratio", "CET1_Approach", "CET1_Requirement_or_Target",
           "Total_Capital_Ratio", "Leverage_Ratio", "NIM_FY2025", "NIM_Q4_2025", "Efficiency_Ratio",
           "Efficiency_Ratio_Definition", "ROAA", "ROAE", "ROTCE", "PCL_or_PCL_Ratio",
           "NCO_Ratio", "NPL_or_GIL_Ratio", "GIL_Term", "ACL_Loans", "Loan_Growth_YoY",
           "Deposit_Growth_YoY", "Loan_to_Deposit", "TBVPS", "P_TBV", "Dividend_Payout",
           "Share_Count_Change_YoY", "Fiscal_Period_End", "Period_Type", "Source_URL",
           "Page_or_Table", "Confidence", "Notes"]

B = {
 "JPM": dict(Name="JPMorgan Chase & Co.", CET1=0.145, Appr="Standardized (binding)", TC=0.173, Lev=0.069,
    NIMFY=None, NIMQ4=0.0254, Eff=0.52, EffDef="Overhead ratio (non-FTE)", ROAA=0.0114, ROAE=0.15,
    ROTCE=0.18, PCL=None, NCO=0.0141, GIL=0.0082, GILTerm="Nonaccrual loans to period-end loans",
    ACL=17557, LB=None, DB=None, LDR=None, TBVPS=107.56, Div=None, Sh=None,
    FPE="2025-12-31", PT="Quarter (4Q25)",
    URL="https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/4th-quarter/3f2030e7-c144-4ad8-92b8-57b36851ffb6.pdf",
    Page="4Q25 Supplement pp.2,6,9,14,18", Conf="High (issuer XLSX)",
    Notes="NCO 1.41% firmwide, card-heavy mix - not comparable to BAC/WFC without mix. ROTCE 18% is Q4."),
 "BAC": dict(Name="Bank of America Corp.", CET1=0.114, Appr="Standardized (binding)", TC=0.146, Lev=0.068,
    NIMFY=0.0201, NIMQ4=0.0208, Eff=0.6132, EffDef="Efficiency ratio (FTE)", ROAA=0.0082, ROAE=0.1022,
    ROTCE=0.1422, PCL=None, NCO=0.0044, GIL=0.0049, GILTerm="Nonperforming loans and leases ratio",
    ACL=14380, LB=0.05, DB=0.03, LDR=None, TBVPS=28.73, Div=None, Sh=-0.053,
    FPE="2025-12-31", PT="Quarter (4Q25)",
    URL="https://www.sec.gov/Archives/edgar/data/70858/000007085826000020/bac12312025ex991.htm",
    Page="8-K Ex-99.1/99.2/99.3", Conf="High (SEC 8-K)",
    Notes="NIM_FY2025=2.01% net interest yield FTE (full year); NIM_Q4=2.08% (208bps)."),
 "WFC": dict(Name="Wells Fargo & Co.", CET1=0.106, Appr="Standardized (binding)", TC=0.143, Lev=0.075,
    NIMFY=None, NIMQ4=0.0260, Eff=0.64, EffDef="Efficiency ratio (non-FTE)", ROAA=0.0052, ROAE=0.123,
    ROTCE=0.145, PCL=None, NCO=0.0043, GIL=0.0086, GILTerm="Nonperforming assets to total loans",
    ACL=14300, LB=0.05, DB=0.02, LDR=None, TBVPS=45.02, Div=None, Sh=None,
    FPE="2025-12-31", PT="Quarter (4Q25)",
    URL="https://www.wellsfargo.com/assets/pdf/about/investor-relations/earnings/fourth-quarter-2025-earnings-supplement.pdf",
    Page="4Q25 Supplement", Conf="High (issuer PDF)",
    Notes="NIM Q4 2025 = 2.60% taxable-equivalent (2.61% was Q3)."),
 "RY": dict(Name="Royal Bank of Canada", CET1=0.135, Appr="Standardized (OSFI)", TC=None, Lev=None,
    NIMFY=0.0162, NIMQ4=0.0162, Eff=0.549, EffDef="Efficiency ratio (non-FTE)", ROAA=None, ROAE=0.15,
    ROTCE=None, PCL=0.0043, NCO=0.0028, GIL=0.0083, GILTerm="Gross impaired loans (GIL) as % of loans and acceptances",
    ACL=None, LB=None, DB=None, LDR=None, TBVPS=None, Div=None, Sh=None,
    FPE="2025-10-31", PT="FY (Q4 2025)",
    URL="https://www.sec.gov/Archives/edgar/data/1000275/000119312525305934/d73208dex991.pdf",
    Page="Q4 2025 supplementary + press release", Conf="High (SEC 6-K)",
    Notes="CET1 13.5%. NIM 1.62% on avg earning assets. Efficiency 54.9% (FY). GIL 0.83%, net write-offs 0.28% (FY). ROE 15.0%, NI $20.4B, EPS $14.07."),
 "TD": dict(Name="Toronto-Dominion Bank", CET1=0.147, Appr="Standardized (OSFI)", TC=0.184, Lev=0.046,
    NIMFY=0.0176, NIMQ4=None, Eff=0.568, EffDef="Efficiency ratio - reported (non-FTE)", ROAA=None, ROAE=0.107,
    ROTCE=0.129, PCL=0.0047, NCO=None, GIL=0.0056, GILTerm="Gross impaired loans ratio (Q4 2025) - 56 bps",
    ACL=9745, LB=None, DB=None, LDR=None, TBVPS=None, Div=None, Sh=None,
    FPE="2025-10-31", PT="FY (Q4 2025)",
    URL="https://www.td.com/content/dam/tdcom/canada/about-td/pdf/investor/investor-relations/financial-information/financial-reports/annual-reports/annual-report-2025/ar2025-consolidated-financial-statements-en.pdf",
    Page="2025 Annual Report - Consolidated FS (10-yr review); Q4 2025 package", Conf="High (issuer PDF)",
    Notes="CET1 14.7%. Tier 1 16.4%, total capital 18.4%, leverage 4.6%. NIM 1.76% FY2025 consolidated (net interest margin, 10-yr review; NOT Cdn P&C 2.83% or US Retail 3.25%). Gross impaired loans ratio 0.56% Q4 (GIL column). Net impaired loans 0.40% of net loans FY (10-yr review, kept separate). PCL 0.47% FY (Q4 0.41%). Efficiency 56.8% reported. ROTCE 12.9% Q4. ACL $9,745M."),
 "BMO": dict(Name="Bank of Montreal", CET1=0.133, Appr="Standardized (OSFI)", TC=0.173, Lev=0.043,
    NIMFY=0.0165, NIMQ4=None, Eff=0.563, EffDef="Efficiency ratio (non-FTE)", ROAA=None, ROAE=0.113,
    ROTCE=0.143, PCL=None, NCO=0.0034, GIL=0.0104, GILTerm="GIL ratio (calculated): GIL $7,091M / gross loans & acceptances $682,922M",
    ACL=None, LB=None, DB=None, LDR=None, TBVPS=None, Div=None, Sh=None,
    FPE="2025-10-31", PT="FY (Q4 2025)",
    URL="https://www.sec.gov/Archives/edgar/data/927971/000119312525308014/d50246dex991.pdf",
    Page="Q4 2025 supplement (6-K)", Conf="High (SEC 6-K)",
    Notes="CET1 13.3%. NIM 1.65% (FY). Efficiency 56.3%. GIL ratio 1.04% = GIL $7,091M / gross loans $682,922M (calculated, FY). Net write-offs 0.34% (TOTAL FY2025; 0.38% was Canadian P&C segment). ROE 11.3%, ROTCE 14.3%, PCL $3,617M, EPS $11.44."),
 "BNS": dict(Name="Bank of Nova Scotia", CET1=0.132, Appr="Standardized (OSFI)", TC=0.171, Lev=0.045,
    NIMFY=None, NIMQ4=0.0240, Eff=0.594, EffDef="Productivity ratio (BNS efficiency metric, non-FTE)", ROAA=None, ROAE=0.135,
    ROTCE=None, PCL=None, NCO=0.0051, GIL=0.0093, GILTerm="Gross impaired loans as % of loans and acceptances (Q4 2025)",
    ACL=None, LB=None, DB=None, LDR=None, TBVPS=None, Div=None, Sh=None,
    FPE="2025-10-31", PT="Q4 2025 (quarterly)",
    URL="https://www.scotiabank.com/content/dam/scotiabank/corporate/quarterly-reports/2025/q4/Q425_Quarterly_Press_Release-EN.pdf",
    Page="Q4 2025 press release", Conf="High (issuer PDF)",
    Notes="CET1 13.2%. NIM 2.40% Q4. Productivity ratio 59.4% Q4 (BNS efficiency term). GIL 0.93% + net write-offs 0.51% (annualized) = Q4 2025 point/quarter rates. ROE 13.5% Q4. Tier1 15.3%, total capital 17.1%, leverage 4.5%. NI $7,758M FY2025."),
 "CM": dict(Name="CIBC", CET1=0.133, Appr="Standardized (OSFI)", TC=0.174, Lev=0.043,
    NIMFY=0.0155, NIMQ4=None, Eff=0.544, EffDef="Efficiency ratio (reported, non-FTE)", ROAA=None, ROAE=0.143,
    ROTCE=None, PCL=None, NCO=None, GIL=0.0080, GILTerm="GIL ratio (calculated): GIL $4,739M / gross loans $593,896M",
    ACL=None, LB=None, DB=None, LDR=None, TBVPS=None, Div=None, Sh=None,
    FPE="2025-10-31", PT="FY (Q4 2025)",
    URL="https://www.sec.gov/Archives/edgar/data/1045520/000119312525307482/d49585dex991.pdf",
    Page="Q4 2025 annual report (6-K)", Conf="High (SEC 6-K)",
    Notes="CET1 13.3%. NIM 1.55% FY (ex-trading 1.93%). Efficiency 54.4% FY reported. ROE 14.3% FY. GIL ratio 0.80% = GIL $4,739M / gross loans $593,896M (calculated, FY). Net write-offs $1,590M (dollar; consolidated avg-loans denominator not cleanly disclosed -> NCO ratio N/A). PCL $2.3B FY. NI $8.5B FY. Tier1 15.1%, total capital 17.4%, leverage 4.3%."),
 "NA": dict(Name="National Bank of Canada", CET1=0.138, Appr="Standardized (OSFI)", TC=0.173, Lev=0.045,
    NIMFY=0.0227, NIMQ4=0.0225, Eff=0.544, EffDef="Efficiency ratio (reported, non-FTE)", ROAA=None, ROAE=0.137,
    ROTCE=None, PCL=None, NCO=None, GIL=None, GILTerm="Gross impaired loans (GIL) - dollar only; ratio N/A (no gross-loans denominator)",
    ACL=None, LB=None, DB=None, LDR=None, TBVPS=None, Div=None, Sh=None,
    FPE="2025-10-31", PT="FY (Q4 2025)",
    URL="https://www.newswire.ca/news-releases/national-bank-reports-its-2025-fourth-quarter-and-annual-results-and-raises-its-quarterly-dividend-by-6-cents-to-1-24-per-share-825267318.html",
    Page="Q4 2025 press release (newswire/issuer)", Conf="High (newswire/issuer)",
    Notes="CET1 13.8%. NIM 2.27% FY (2.25% Q4). Efficiency 54.4% FY (56.4% Q4). ROE 13.7% FY (13.3% Q4). GIL $3,712M dollar; balance sheet shows only 'Loans, net of allowances $302,623M' -> gross-loans denominator not found -> GIL ratio N/A (credit pillar incomplete). NI $1,059M Q4. Tier1 15.1%, total capital 17.3%, leverage 4.5%."),
}

us_meta = pd.read_csv(os.path.join(RAW, "us_meta.csv"), index_col=0)
def price_of(t):
    if t in us_meta.index and pd.notna(us_meta.loc[t, "price"]):
        return us_meta.loc[t, "price"]
    return None

br = wb["Bank_Regulatory"]
for j, h in enumerate(BR_COLS, start=1):
    c = br.cell(row=1, column=j, value=h); c.fill = HDR_FILL; c.font = HDR_FONT
br.freeze_panes = "A2"
if br.max_row > 1:
    br.delete_rows(2, br.max_row - 1)

order = ["JPM", "BAC", "WFC", "RY", "TD", "BMO", "BNS", "CM", "NA"]
r = 2
for t in order:
    d = B[t]
    px = price_of(t)
    p_tbv = round(px / d["TBVPS"], 2) if (px and d["TBVPS"]) else None
    row = [t, d["Name"], d["CET1"], d["Appr"], d.get("CET1_Req"), d["TC"], d["Lev"],
           d["NIMFY"], d["NIMQ4"], d["Eff"], d["EffDef"], d["ROAA"], d["ROAE"], d["ROTCE"],
           d["PCL"], d["NCO"], d["GIL"], d["GILTerm"], d["ACL"], d["LB"], d["DB"], d["LDR"],
           d["TBVPS"], p_tbv, d["Div"], d["Sh"], d["FPE"], d["PT"], d["URL"], d["Page"], d["Conf"], d["Notes"]]
    for j, v in enumerate(row, start=1):
        br.cell(row=r, column=j, value=v)
    r += 1

wb.save(XLSX)
print("Saved. Bank_Regulatory rows:", br.max_row - 1)
