# -*- coding: utf-8 -*-
"""Universe builder — refactored. Rebuilds Universe sheet from Wikipedia seeds
(S&P 500 + S&P/TSX Composite + S&P/TSX 60), applies share-class consolidation,
and writes raw/universe_master.csv + tickers.txt. Optional SPY validation.
"""
import os, re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import openpyxl

from common import RAW, XLSX, CFG, cfg_universe

GICS_SECTOR_MAP = {
    "Information Technology": "Information Technology", "Tech": "Information Technology",
    "Health Care": "Health Care", "Healthcare": "Health Care",
    "Communication Services": "Communication Services",
    "Consumer Discretionary": "Consumer Discretionary", "Consumer Staples": "Consumer Staples",
    "Financials": "Financials", "Energy": "Energy", "Industrials": "Industrials",
    "Materials": "Materials", "Utilities": "Utilities", "Real Estate": "Real Estate",
}
SECTOR_SHEET = {
    "Information Technology": "Tech", "Health Care": "Healthcare", "Communication Services": "Comm_Services",
    "Consumer Discretionary": "Consumer_Cyclical", "Consumer Staples": "Consumer_Defensive",
    "Financials": "Financials", "Energy": "Energy", "Industrials": "Industrials",
    "Materials": "Materials", "Utilities": "Utilities", "Real Estate": "Real_Estate",
}


def norm_ticker(x):
    return re.sub(r"[.\-]", "", str(x)).upper()


def custom_industry_sheet(sector, sub):
    t = (sub or "").lower(); s = sector or ""
    if s == "Financials" and ("bank" in t or "thrift" in t or "mortgage" in t): return "Banks"
    if s == "Financials" and "insurance" in t: return "Insurance"
    if s == "Financials" and ("consumer finance" in t or "credit" in t): return "Credit_Services"
    if s == "Information Technology" and "software" in t: return "Software"
    if s == "Information Technology" and "semiconductor" in t: return "Semiconductors_Components"
    if s == "Information Technology" and ("communications equipment" in t or "networking" in t): return "Networking"
    if s == "Communication Services" and ("interactive media" in t or "internet" in t): return "Internet_Platforms"
    if s == "Communication Services" and ("telecommunication" in t or "wireless" in t): return "Telecom"
    if s == "Communication Services" and ("entertainment" in t or "media" in t or "cable" in t or "broadcast" in t or "movies" in t or "advertising" in t): return "Streaming_Entertainment"
    if s == "Consumer Staples" and ("distribution & retail" in t or "hypermarket" in t or "food retail" in t or "drugs retail" in t): return "Discount_Stores"
    if "restaurant" in t: return "Fast_Food_Restaurants"
    if s == "Consumer Discretionary" and ("retail" in t or "distributor" in t or "internet & direct marketing" in t): return "Retail"
    if s == "Consumer Staples" and ("food" in t or "beverage" in t or "tobacco" in t or "household" in t or "personal" in t): return "Consumer_Goods"
    if s == "Consumer Discretionary" and ("automobile" in t or "auto component" in t or "automotive" in t): return "Autos"
    if s == "Health Care" and ("pharmaceutical" in t or "drug" in t): return "Pharma"
    if s == "Health Care" and "biotech" in t: return "Biotech"
    if s == "Health Care": return "Medical_Devices_Services"
    if s == "Industrials" and ("rail" in t or "railroad" in t): return "Railroads"
    if s == "Industrials" and "airline" in t: return "Airlines"
    if s == "Energy" and ("storage & transportation" in t or "pipeline" in t or "midstream" in t): return "Pipelines_Midstream"
    if s == "Energy": return "Oil_Gas_Producers"
    if s == "Utilities": return "Utilities_Regulated"
    return SECTOR_SHEET.get(s, s)


def yahoo_ca(t):
    t = str(t)
    if ".UN" in t: return t.replace(".UN", "-UN") + ".TO"
    if t.endswith(".TO"): return t
    return t + ".TO"


def build(as_of="2026-08-21", spy_path=None):
    sp500 = pd.read_csv(os.path.join(RAW, "sp500_wikipedia.csv"), na_filter=False)
    comp = pd.read_csv(os.path.join(RAW, "tsx_composite_wikipedia.csv"), na_filter=False)
    comp = comp[comp["Ticker"].astype(str).str.strip() != ""].copy()
    sp500 = sp500[sp500["Symbol"].astype(str).str.strip() != ""].copy()

    # US share-class consolidation
    us = sp500.copy()
    us["_base"] = us["Security"].str.replace(r"\s*\(Class\s+[A-Z]+\)\s*$", "", regex=True).str.strip()
    PRIMARY_SYM = {"Alphabet Inc.": "GOOGL", "Fox Corporation": "FOXA", "News Corp": "NWSA"}
    SECONDARY_SYM = {"Alphabet Inc.": "GOOG", "Fox Corporation": "FOX", "News Corp": "NWS"}
    SHARE_CLASS = {"Alphabet Inc.": "Class A (primary)", "Fox Corporation": "Class A (primary)", "News Corp": "Class A (primary)"}
    us_rows = []
    for base, g in us.groupby("_base"):
        if len(g) == 1:
            r = g.iloc[0]
            cls = "Class B" if str(r["Symbol"]).endswith(".B") else "Common"
            us_rows.append(dict(base=base, sym=r["Symbol"], name=r["Security"], sector=r["GICS Sector"],
                                sub=r["GICS Sub-Industry"], cik=r["CIK"], hq=r["Headquarters Location"],
                                date_added=r["Date added"], share_class=cls, secondary=""))
        else:
            prim = PRIMARY_SYM.get(base, g.iloc[0]["Symbol"])
            r = g[g["Symbol"] == prim].iloc[0]
            secs = ",".join([s for s in g["Symbol"] if s != prim])
            us_rows.append(dict(base=base, sym=prim, name=base, sector=r["GICS Sector"],
                                sub=r["GICS Sub-Industry"], cik=r["CIK"], hq=r["Headquarters Location"],
                                date_added=r["Date added"], share_class=SHARE_CLASS.get(base, "Common (multi-class)"),
                                secondary=secs))
    usdf = pd.DataFrame(us_rows)
    usdf["GICS_Sector"] = usdf["sector"].map(lambda x: GICS_SECTOR_MAP.get(x, x))
    usdf["_nt"] = usdf["sym"].map(norm_ticker)

    # CA
    ca = comp.copy()
    ca["Company"] = ca["Company"].astype(str).str.replace(r"\s+\(.*\)$", "", regex=True).str.strip()
    ca["GICS_Sector"] = ca["Sector [10]"].map(lambda x: GICS_SECTOR_MAP.get(x, x))
    ca["GICS_Industry"] = ca["Industry [10]"].astype(str)
    ca["_nt"] = ca["Ticker"].map(norm_ticker)

    cols = ["Universe_Effective_Date", "Ticker", "Primary_Ticker", "Yahoo_Ticker", "Secondary_Ticker",
            "Share_Class", "Company_Name", "Country_of_Listing", "Exchange", "Primary_Currency",
            "Financials_Native_Currency", "Trading_Currency", "Reporting_Standard", "GICS_Sector",
            "GICS_Industry_Group", "GICS_Industry", "GICS_Sub_Industry", "Custom_Industry_Sheet",
            "Market_Cap_Native", "Market_Cap_USD", "Shares_Out", "Price", "Price_Date", "Market_Data_As_Of",
            "Financials_As_Of", "Fiscal_Year_End", "CIK_SEDAR", "IR_URL", "Latest_Annual_Filing",
            "Latest_Interim_Filing", "Dual_Listed", "Include_In_Ranking", "In_SP500", "In_TSX_Composite",
            "In_TSX60", "In_SPUS", "Data_Source", "Retrieval_Date", "Notes"]
    rows = []
    for _, r in usdf.iterrows():
        t = r["sym"]; yt = t.replace(".", "-") if "." in str(t) else t
        rows.append({"Universe_Effective_Date": as_of, "Ticker": t, "Primary_Ticker": yt, "Yahoo_Ticker": yt,
            "Secondary_Ticker": r["secondary"], "Share_Class": r["share_class"], "Company_Name": r["name"],
            "Country_of_Listing": "US", "Exchange": "", "Primary_Currency": "USD", "Financials_Native_Currency": "USD",
            "Trading_Currency": "USD", "Reporting_Standard": "US-GAAP", "GICS_Sector": r["GICS_Sector"],
            "GICS_Industry_Group": "", "GICS_Industry": "", "GICS_Sub_Industry": r["sub"],
            "Custom_Industry_Sheet": custom_industry_sheet(r["GICS_Sector"], r["sub"]),
            "Market_Cap_Native": "", "Market_Cap_USD": "", "Shares_Out": "", "Price": "", "Price_Date": "",
            "Market_Data_As_Of": "", "Financials_As_Of": "", "Fiscal_Year_End": "", "CIK_SEDAR": r["cik"],
            "IR_URL": "", "Latest_Annual_Filing": "", "Latest_Interim_Filing": "", "Dual_Listed": "No",
            "Include_In_Ranking": "Yes", "In_SP500": "Yes", "In_TSX_Composite": "No", "In_TSX60": "No",
            "In_SPUS": "No", "Data_Source": f"Wikipedia 'List of S&P 500 companies' ({as_of})",
            "Retrieval_Date": as_of, "Notes": f"HQ: {r['hq']}; added {r['date_added']}"})
    for _, r in ca.iterrows():
        t = r["Ticker"]; yt = yahoo_ca(t)
        cis = "Utilities_Regulated" if r["_nt"] == "H" else custom_industry_sheet(r["GICS_Sector"], r["GICS_Industry"])
        rows.append({"Universe_Effective_Date": as_of, "Ticker": t, "Primary_Ticker": yt, "Yahoo_Ticker": yt,
            "Secondary_Ticker": "", "Share_Class": "Unit (REIT)" if ".UN" in str(t) else "Common",
            "Company_Name": r["Company"], "Country_of_Listing": "CA", "Exchange": "TSX", "Primary_Currency": "CAD",
            "Financials_Native_Currency": "CAD", "Trading_Currency": "CAD", "Reporting_Standard": "IFRS",
            "GICS_Sector": r["GICS_Sector"], "GICS_Industry_Group": "", "GICS_Industry": r["GICS_Industry"],
            "GICS_Sub_Industry": "", "Custom_Industry_Sheet": cis, "Market_Cap_Native": "", "Market_Cap_USD": "",
            "Shares_Out": "", "Price": "", "Price_Date": "", "Market_Data_As_Of": "", "Financials_As_Of": "",
            "Fiscal_Year_End": "", "CIK_SEDAR": "", "IR_URL": "", "Latest_Annual_Filing": "", "Latest_Interim_Filing": "",
            "Dual_Listed": "", "Include_In_Ranking": "Yes", "In_SP500": "No", "In_TSX_Composite": "Yes",
            "In_TSX60": "No", "In_SPUS": "No",
            "Data_Source": f"Wikipedia 'S&P/TSX Composite Index' ({as_of})", "Retrieval_Date": as_of, "Notes": ""})
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(os.path.join(RAW, "universe_master.csv"), index=False)

    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Universe"]
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    for i, row in enumerate(df.itertuples(index=False), start=2):
        for j, v in enumerate(row, start=1):
            ws.cell(row=i, column=j, value=v)
    wb.save(XLSX)
    return df


def write_tickers():
    """Generate config/tickers.txt from the Universe sheet (one Yahoo_Ticker per line)."""
    df = pd.read_excel(XLSX, sheet_name="Universe")
    tk = df["Yahoo_Ticker"].fillna(df["Ticker"]).astype(str).tolist()
    tk = [t for t in tk if t and t.strip()]
    out = os.path.join(CFG, "tickers.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(tk) + "\n")
    return len(tk)


if __name__ == "__main__":
    import sys
    if "--tickers" in sys.argv:
        print("tickers.txt entries:", write_tickers())
    else:
        c = cfg_universe()
        df = build(as_of=c.get("as_of", "2026-08-21"))
        print(f"Universe rebuilt: {len(df)} companies")
        print("tickers.txt entries:", write_tickers())
