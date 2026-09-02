# -*- coding: utf-8 -*-
"""
Phase 2.6 — document extraction write-through.
Writes NEE cash-capex FCF, rebuilds Bank_Regulatory (exact schema) with primary-source
JPM/BAC/WFC + RY CET1, updates Utility_Pipeline. No universe expansion.
"""
import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill

ROOT = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research"
RAW = os.path.join(ROOT, "raw")
XLSX = os.path.join(ROOT, "NA_Company_Financials.xlsx")
TODAY = "2026-08-20"

wb = openpyxl.load_workbook(XLSX)
HDR_FILL = PatternFill("solid", fgColor="1F4E78")
HDR_FONT = Font(bold=True, color="FFFFFF")

# ---- NEE FCF (accepted values) ----
NEE_FCF = -11568000000.0          # OCF 12485 - cash capex 24053
NEE_FCF_NUC = -12121000000.0      # also net nuclear fuel 553

us_meta = pd.read_csv(os.path.join(RAW, "us_meta.csv"), index_col=0)
def price_of(t):
    yt = t  # US ticker
    if yt in us_meta.index and pd.notna(us_meta.loc[yt, "price"]):
        return us_meta.loc[yt, "price"]
    return None

# =========================================================================
# Bank_Regulatory rebuild (exact Task A schema)
# =========================================================================
BR_COLS = ["Ticker", "Company_Name", "CET1_Ratio", "CET1_Approach", "CET1_Requirement_or_Target",
           "Total_Capital_Ratio", "Leverage_Ratio", "NIM", "Efficiency_Ratio",
           "Efficiency_Ratio_Definition", "ROAA", "ROAE", "ROTCE", "PCL_or_PCL_Ratio",
           "NCO_Ratio", "NPL_Ratio", "ACL_Loans", "Loan_Growth_YoY", "Deposit_Growth_YoY",
           "Loan_to_Deposit", "TBVPS", "P_TBV", "Dividend_Payout", "Share_Count_Change_YoY",
           "Fiscal_Period_End", "Period_Type", "Source_URL", "Page_or_Table", "Confidence", "Notes"]

BANK = {
    "JPM": {
        "Company_Name": "JPMorgan Chase & Co.",
        "CET1_Ratio": 0.145, "CET1_Approach": "Standardized (binding)",
        "Total_Capital_Ratio": 0.173, "Leverage_Ratio": 0.069,
        "NIM": 0.0254, "Efficiency_Ratio": 0.52,
        "Efficiency_Ratio_Definition": "Overhead ratio (non-FTE): noninterest expense / total net revenue",
        "ROAE": 0.15, "ROAA": 0.0114, "ROTCE": 0.18,
        "NCO_Ratio": 0.0141, "NPL_Ratio": 0.0082, "ACL_Loans": 17557,
        "TBVPS": 107.56, "Dividend_Payout": None, "Share_Count_Change_YoY": None,
        "Fiscal_Period_End": "2025-12-31", "Period_Type": "Quarter (4Q25)",
        "Source_URL": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/4th-quarter/3f2030e7-c144-4ad8-92b8-57b36851ffb6.pdf",
        "Page_or_Table": "4Q25 Earnings Supplement (pp.2,6,9,14,18)",
        "Confidence": "High (issuer supplement XLSX)",
        "Notes": "CET1 Std 14.5% (binding; Std RWA $1.98T < Adv $2.05T), Advanced 14.1%. NIM=net yield on interest-earning assets 2.54%. NCO rate 1.41%, nonaccrual-to-loans 0.82%. ROTCE/NIM/efficiency are 4Q25 quarterly; CET1/TBVPS period-end.",
    },
    "BAC": {
        "Company_Name": "Bank of America Corp.",
        "CET1_Ratio": 0.114, "CET1_Approach": "Standardized (binding)",
        "Total_Capital_Ratio": 0.146, "Leverage_Ratio": 0.068,
        "NIM": 0.0201, "Efficiency_Ratio": 0.6132,
        "Efficiency_Ratio_Definition": "Efficiency ratio (FTE): noninterest expense / total revenue, net of interest expense",
        "ROAE": 0.1022, "ROAA": 0.0082, "ROTCE": 0.1422,
        "NCO_Ratio": 0.0044, "NPL_Ratio": 0.0049, "ACL_Loans": 14380,
        "Loan_Growth_YoY": 0.05, "Deposit_Growth_YoY": 0.03,
        "TBVPS": 28.73, "Dividend_Payout": None, "Share_Count_Change_YoY": -0.053,
        "Fiscal_Period_End": "2025-12-31", "Period_Type": "Quarter (4Q25)",
        "Source_URL": "https://www.sec.gov/Archives/edgar/data/70858/000007085826000020/bac12312025ex991.htm",
        "Page_or_Table": "8-K Ex-99.1/99.2/99.3 (4Q25)",
        "Confidence": "High (SEC 8-K exhibits)",
        "Notes": "CET1 Std 11.4% (binding; preliminary), Advanced ~12.8%. NIM='net interest yield' 2.01% (FTE). Efficiency 61.32% (FTE). NCO 0.44%, NPL 0.49%. ROTCE/NIM/efficiency are 4Q25 quarterly.",
    },
    "WFC": {
        "Company_Name": "Wells Fargo & Co.",
        "CET1_Ratio": 0.106, "CET1_Approach": "Standardized (binding)",
        "Total_Capital_Ratio": 0.143, "Leverage_Ratio": 0.075,
        "NIM": 0.0261, "Efficiency_Ratio": 0.64,
        "Efficiency_Ratio_Definition": "Efficiency ratio (non-FTE): noninterest expense / total revenue",
        "ROAE": 0.123, "ROAA": 0.0052, "ROTCE": 0.145,
        "NCO_Ratio": 0.0043, "NPL_Ratio": 0.0086, "ACL_Loans": 14300,
        "Loan_Growth_YoY": 0.05, "Deposit_Growth_YoY": 0.02,
        "TBVPS": 45.02, "Dividend_Payout": None, "Share_Count_Change_YoY": None,
        "Fiscal_Period_End": "2025-12-31", "Period_Type": "Quarter (4Q25)",
        "Source_URL": "https://www.wellsfargo.com/assets/pdf/about/investor-relations/earnings/fourth-quarter-2025-earnings-supplement.pdf",
        "Page_or_Table": "4Q25 Financial Results + Earnings Supplement",
        "Confidence": "High (issuer PDF)",
        "Notes": "CET1 Std 10.6% (binding; Standardized Approach). NIM 2.61% (FTE). Efficiency 64%. NCO 0.43% of avg loans, NPA 0.86% of loans. ROTCE/NIM/efficiency are 4Q25 quarterly.",
    },
    "RY": {
        "Company_Name": "Royal Bank of Canada",
        "CET1_Ratio": 0.135, "CET1_Approach": "Standardized (OSFI)",
        "NIM": None, "Efficiency_Ratio": None, "Efficiency_Ratio_Definition": None,
        "ROAE": None, "ROAA": None, "ROTCE": None,
        "NCO_Ratio": None, "NPL_Ratio": None, "ACL_Loans": None,
        "TBVPS": None, "Dividend_Payout": None, "Share_Count_Change_YoY": None,
        "Fiscal_Period_End": "2025-10-31", "Period_Type": "FY (Q4 2025)",
        "Source_URL": "https://www.rbc.com/newsroom/news/article.html?article=126055",
        "Page_or_Table": "Q4 2025 results / annual package",
        "Confidence": "High (issuer newsroom)",
        "Notes": "CET1 13.5% at Oct 31 2025. NIM/efficiency/NPL/NCO/ROTCE/TBVPS require FY2025 supplementary financial information PDF (not extracted this pass).",
    },
}

# CA banks with no extraction yet
for t, nm in [("TD", "Toronto-Dominion Bank"), ("BNS", "Bank of Nova Scotia"),
              ("BMO", "Bank of Montreal"), ("CM", "CIBC"), ("NA", "National Bank of Canada")]:
    BANK[t] = {
        "Company_Name": nm, "CET1_Ratio": None, "CET1_Approach": "Standardized (OSFI)",
        "NIM": None, "Efficiency_Ratio": None, "Efficiency_Ratio_Definition": None,
        "ROAE": None, "ROAA": None, "ROTCE": None,
        "NCO_Ratio": None, "NPL_Ratio": None, "ACL_Loans": None,
        "TBVPS": None, "Dividend_Payout": None, "Share_Count_Change_YoY": None,
        "Fiscal_Period_End": "2025-10-31", "Period_Type": "FY (Q4 2025)",
        "Source_URL": "", "Page_or_Table": "", "Confidence": "n/a",
        "Notes": "CET1/NIM/efficiency/NPL/NCO/ROTCE/TBVPS require FY2025 supplementary financial information PDF (SEDAR+/IR, not extracted this pass).",
    }

# map IR websites
ca_web = pd.read_csv(os.path.join(RAW, "ca_websites.csv"), keep_default_na=False)
webmap = dict(zip(ca_web["ticker"], ca_web["website"]))

br = wb["Bank_Regulatory"] if "Bank_Regulatory" in wb.sheetnames else wb.create_sheet("Bank_Regulatory")
for j, h in enumerate(BR_COLS, start=1):
    c = br.cell(row=1, column=j, value=h); c.fill = HDR_FILL; c.font = HDR_FONT
br.freeze_panes = "A2"
if br.max_row > 1:
    br.delete_rows(2, br.max_row - 1)

def set_row(ws, r, values):
    for j, v in enumerate(values, start=1):
        ws.cell(row=r, column=j, value=v)

order = ["JPM", "BAC", "WFC", "RY", "TD", "BNS", "BMO", "CM", "NA"]
r = 2
for t in order:
    b = BANK[t]
    if not b["Source_URL"] and t not in ("JPM", "BAC", "WFC", "RY"):
        b["Source_URL"] = webmap.get(t, "")
    px = price_of(t)
    p_tbv = round(px / b["TBVPS"], 2) if (px and b["TBVPS"]) else None
    set_row(br, r, [t, b["Company_Name"], b["CET1_Ratio"], b["CET1_Approach"],
                    b.get("CET1_Requirement_or_Target"), b.get("Total_Capital_Ratio"),
                    b.get("Leverage_Ratio"), b["NIM"], b["Efficiency_Ratio"],
                    b["Efficiency_Ratio_Definition"], b.get("ROAA"), b.get("ROAE"),
                    b.get("ROTCE"), b.get("PCL_or_PCL_Ratio"), b.get("NCO_Ratio"),
                    b.get("NPL_Ratio"), b.get("ACL_Loans"), b.get("Loan_Growth_YoY"),
                    b.get("Deposit_Growth_YoY"), b.get("Loan_to_Deposit"), b["TBVPS"],
                    p_tbv, b.get("Dividend_Payout"), b.get("Share_Count_Change_YoY"),
                    b["Fiscal_Period_End"], b["Period_Type"], b["Source_URL"],
                    b["Page_or_Table"], b["Confidence"], b["Notes"]])
    r += 1

# ---- Core_Financials: NEE FCF ----
cf = wb["Core_Financials"]
cfh = [c.value for c in cf[1]]
cfidx = {h: i + 1 for i, h in enumerate(cfh)}
def ensure_col(name):
    if name not in cfidx:
        nxt = len(cfh) + 1
        c = cf.cell(row=1, column=nxt, value=name); c.fill = HDR_FILL; c.font = HDR_FONT
        cfidx[name] = nxt; cfh.append(name)
    return cfidx[name]
ensure_col("FCF_incl_Nuclear_Fuel")
for rr in range(2, cf.max_row + 1):
    if cf.cell(row=rr, column=cfidx["Ticker"]).value == "NEE":
        cf.cell(row=rr, column=cfidx["Free_Cash_Flow"], value=NEE_FCF)
        cf.cell(row=rr, column=cfidx["FCF_incl_Nuclear_Fuel"], value=NEE_FCF_NUC)
        cf.cell(row=rr, column=cfidx["FCF_Note"], value=("10-K cash-flow: OCF 12,485 - cash capex 24,053 (FPL 8,719 + NEER investments 15,332 + other 2). "
            "Nuclear fuel purchases 553 recorded separately (not netted). Negative = utility growth capex. Source: 10-K nee-20251231.htm (Feb 13 2026)."))
        # also record capex value now sourced
        cf.cell(row=rr, column=cfidx["Capex"], value=24053000000.0)

# ---- Utility_Pipeline: NEE FCF + Hydro One term ----
up = wb["Utility_Pipeline"]
upidx = {c.value: i + 1 for i, c in enumerate(up[1])}
def up_set(t, field, val):
    for rr in range(2, up.max_row + 1):
        if up.cell(row=rr, column=upidx["Ticker"]).value == t:
            up.cell(row=rr, column=upidx[field], value=val)
# NEE: cash metric = FCF (OCF - cash capex), with nuclear fuel noted
up_set("NEE", "Issuer_Term", "Cash from operations less capital expenditures (GAAP-derived)")
up_set("NEE", "FFO_or_Equivalent", -11568000000.0)
up_set("NEE", "Capex", 24053000000.0)
up_set("NEE", "Notes", "Cash capex from 10-K cash-flow stmt (not XBRL-tagged): FPL 8,719 + NEER 15,332 + other 2 = 24,053; nuclear fuel 553 separate (not netted). FCF = -11,568 (growth capex).")
up_set("H", "Issuer_Term", "Cash from operations after capital expenditures (management MD&A)")

wb.save(XLSX)
print("Saved. Bank_Regulatory rows:", br.max_row - 1)
print("NEE FCF written:", NEE_FCF, "| incl nuclear:", NEE_FCF_NUC)
