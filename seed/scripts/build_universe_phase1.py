# -*- coding: utf-8 -*-
"""
Phase 1 — Build the Universe sheet.
US: seed = user SPY Holdings.xlsx, validated vs Wikipedia S&P 500 list (authoritative current).
CA: Wikipedia S&P/TSX Composite constituents; In_TSX60 flag from Wikipedia S&P/TSX 60.
Consolidates multi-share-class companies into one row.
Writes Universe + updates README. Saves master CSV to raw/.
"""
import os, datetime, re
import pandas as pd
import openpyxl

ROOT = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research"
RAW = os.path.join(ROOT, "raw")
XLSX = os.path.join(ROOT, "NA_Company_Financials.xlsx")
SPY_PATH = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\.openclaw-attachments\20260820-114543-ca002dd0-66a-SPY Holdings.xlsx"

TODAY = "2026-08-20"

# ----------------------------------------------------------------------------
# sector name normalization -> official GICS sector names
# ----------------------------------------------------------------------------
GICS_SECTOR_MAP = {
    "Information Technology": "Information Technology",
    "Tech": "Information Technology",
    "Health Care": "Health Care",
    "Healthcare": "Health Care",
    "Communication Services": "Communication Services",
    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Financials": "Financials",
    "Energy": "Energy",
    "Industrials": "Industrials",
    "Materials": "Materials",
    "Utilities": "Utilities",
    "Real Estate": "Real Estate",
}

SECTOR_SHEET = {  # GICS sector -> sector sheet name (default Custom_Industry_Sheet)
    "Information Technology": "Tech",
    "Health Care": "Healthcare",
    "Communication Services": "Comm_Services",
    "Consumer Discretionary": "Consumer_Cyclical",
    "Consumer Staples": "Consumer_Defensive",
    "Financials": "Financials",
    "Energy": "Energy",
    "Industrials": "Industrials",
    "Materials": "Materials",
    "Utilities": "Utilities",
    "Real Estate": "Real_Estate",
}


def custom_industry_sheet(sector, sub):
    """First-pass mapping to the 23 industry detail sheets, else sector sheet."""
    t = (sub or "").lower()
    s = sector or ""
    # banks
    if s == "Financials" and ("bank" in t or "thrift" in t or "mortgage" in t):
        return "Banks"
    if s == "Financials" and "insurance" in t:
        return "Insurance"
    if s == "Financials" and ("consumer finance" in t or "credit" in t):
        return "Credit_Services"
    # tech
    if s == "Information Technology" and "software" in t:
        return "Software"
    if s == "Information Technology" and "semiconductor" in t:
        return "Semiconductors_Components"
    if s == "Information Technology" and ("communications equipment" in t or "networking" in t):
        return "Networking"
    # comm services
    if s == "Communication Services" and ("interactive media" in t or "interactive home" in t or "internet" in t):
        return "Internet_Platforms"
    if s == "Communication Services" and ("telecommunication" in t or "wireless" in t):
        return "Telecom"
    if s == "Communication Services" and ("entertainment" in t or "media" in t or "cable" in t or "broadcast" in t or "movies" in t or "advertising" in t):
        return "Streaming_Entertainment"
    # consumer
    if s == "Consumer Staples" and ("distribution & retail" in t or "hypermarket" in t or "food retail" in t or "drugs retail" in t):
        return "Discount_Stores"
    if "restaurant" in t:
        return "Fast_Food_Restaurants"
    if s == "Consumer Discretionary" and ("retail" in t or "distributor" in t or "internet & direct marketing" in t):
        return "Retail"
    if s == "Consumer Staples" and ("food" in t or "beverage" in t or "tobacco" in t or "household" in t or "personal" in t):
        return "Consumer_Goods"
    if s == "Consumer Discretionary" and ("automobile" in t or "auto component" in t or "automotive" in t):
        return "Autos"
    # health
    if s == "Health Care" and ("pharmaceutical" in t or "drug" in t):
        return "Pharma"
    if s == "Health Care" and "biotech" in t:
        return "Biotech"
    if s == "Health Care":
        return "Medical_Devices_Services"
    # industrials
    if s == "Industrials" and ("rail" in t or "railroad" in t):
        return "Railroads"
    if s == "Industrials" and "airline" in t:
        return "Airlines"
    # energy
    if s == "Energy" and ("storage & transportation" in t or "pipeline" in t or "midstream" in t):
        return "Pipelines_Midstream"
    if s == "Energy":
        return "Oil_Gas_Producers"
    # utilities
    if s == "Utilities":
        return "Utilities_Regulated"
    # materials
    if s == "Materials":
        return "Materials"
    # fallback to sector sheet
    return SECTOR_SHEET.get(s, s)


def norm_ticker(x):
    return re.sub(r"[.\-]", "", str(x)).upper()


# ----------------------------------------------------------------------------
# load sources
# ----------------------------------------------------------------------------
spy = pd.read_excel(SPY_PATH, sheet_name="SPY Holdings")            # Ticker, Name, Sector, Weight(%), SPUS
spus = pd.read_excel(SPY_PATH, sheet_name="SPUS Holdings")          # Account, StockTicker, SecurityName, Weightings
sp500 = pd.read_csv(os.path.join(RAW, "sp500_wikipedia.csv"), na_filter=False)
comp = pd.read_csv(os.path.join(RAW, "tsx_composite_wikipedia.csv"), na_filter=False)
t60 = pd.read_csv(os.path.join(RAW, "tsx60_wikipedia_t1.csv"), na_filter=False)

# drop empty/trailing rows (na_filter=False preserves ticker "NA" for National Bank of Canada)
comp = comp[comp["Ticker"].astype(str).str.strip() != ""].copy()
t60 = t60[t60["Symbol"].astype(str).str.strip() != ""].copy()
sp500 = sp500[sp500["Symbol"].astype(str).str.strip() != ""].copy()

# clean spy: exclude cash/derivative rows (Sector "Cash and/or Derivatives")
spy = spy.dropna(subset=["Ticker"]).copy()
spy = spy[~spy["Sector"].astype(str).str.contains("Cash", case=False, na=False)].copy()
spy["_nt"] = spy["Ticker"].map(norm_ticker)
in_spus_map = {r["_nt"]: (str(r.get("SPUS", "")).strip().lower() == "yes") for _, r in spy.iterrows()}

# TSX60 symbols
tsx60_syms = set(t60["Symbol"].map(norm_ticker))

# ----------------------------------------------------------------------------
# US build (Wikipedia S&P 500 = authoritative; 503 tickers -> 500 companies)
# ----------------------------------------------------------------------------
us = sp500.copy()
us["_base"] = us["Security"].str.replace(r"\s*\(Class\s+[A-Z]+\)\s*$", "", regex=True).str.strip()
# share-class consolidation: primary = Class A (or first); drop secondary class rows
PRIMARY_SYM = {"Alphabet Inc.": "GOOGL", "Fox Corporation": "FOXA", "News Corp": "NWSA"}
SECONDARY_SYM = {"Alphabet Inc.": "GOOG", "Fox Corporation": "FOX", "News Corp": "NWS"}
SHARE_CLASS = {"Alphabet Inc.": "Class A (primary)", "Fox Corporation": "Class A (primary)", "News Corp": "Class A (primary)"}

us_rows = []
dropped = []
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

# validation vs SPY seed (use RAW 503 tickers, before share-class consolidation)
spy_nt = set(spy["_nt"])
raw_wiki_nt = set(sp500["Symbol"].map(norm_ticker))
removed = spy_nt - raw_wiki_nt          # in SPY seed but not in current S&P 500 (true removals)
added = raw_wiki_nt - spy_nt            # in current S&P 500 but not in SPY seed (additions)

# ----------------------------------------------------------------------------
# CA build (TSX Composite)
# ----------------------------------------------------------------------------
ca = comp.copy()
ca["Company"] = ca["Company"].astype(str).str.replace(r"\s+\(.*\)$", "", regex=True).str.strip()
ca["GICS_Sector"] = ca["Sector [10]"].map(lambda x: GICS_SECTOR_MAP.get(x, x))
ca["GICS_Industry"] = ca["Industry [10]"].astype(str)
ca["_nt"] = ca["Ticker"].map(norm_ticker)

def yahoo_ca(t):
    t = str(t)
    if ".UN" in t:
        return t.replace(".UN", "-UN") + ".TO"
    if t.endswith(".TO"):
        return t
    return t + ".TO"

# ----------------------------------------------------------------------------
# assemble final dataframe (39 columns)
# ----------------------------------------------------------------------------
cols = [
    "Universe_Effective_Date", "Ticker", "Primary_Ticker", "Yahoo_Ticker",
    "Secondary_Ticker", "Share_Class", "Company_Name", "Country_of_Listing",
    "Exchange", "Primary_Currency", "Financials_Native_Currency", "Trading_Currency",
    "Reporting_Standard", "GICS_Sector", "GICS_Industry_Group", "GICS_Industry",
    "GICS_Sub_Industry", "Custom_Industry_Sheet", "Market_Cap_Native",
    "Market_Cap_USD", "Shares_Out", "Price", "Price_Date", "Market_Data_As_Of",
    "Financials_As_Of", "Fiscal_Year_End", "CIK_SEDAR", "IR_URL",
    "Latest_Annual_Filing", "Latest_Interim_Filing", "Dual_Listed",
    "Include_In_Ranking", "In_SP500", "In_TSX_Composite", "In_TSX60", "In_SPUS",
    "Data_Source", "Retrieval_Date", "Notes",
]

rows = []

# US rows
for _, r in usdf.iterrows():
    t = r["sym"]
    yt = t.replace(".", "-") if "." in str(t) else t
    in_spus = in_spus_map.get(r["_nt"], False)
    rows.append({
        "Universe_Effective_Date": TODAY, "Ticker": t, "Primary_Ticker": yt, "Yahoo_Ticker": yt,
        "Secondary_Ticker": r["secondary"], "Share_Class": r["share_class"], "Company_Name": r["name"],
        "Country_of_Listing": "US", "Exchange": "", "Primary_Currency": "USD",
        "Financials_Native_Currency": "USD", "Trading_Currency": "USD", "Reporting_Standard": "US-GAAP",
        "GICS_Sector": r["GICS_Sector"], "GICS_Industry_Group": "", "GICS_Industry": "",
        "GICS_Sub_Industry": r["sub"], "Custom_Industry_Sheet": custom_industry_sheet(r["GICS_Sector"], r["sub"]),
        "Market_Cap_Native": "", "Market_Cap_USD": "", "Shares_Out": "", "Price": "",
        "Price_Date": "", "Market_Data_As_Of": "", "Financials_As_Of": "", "Fiscal_Year_End": "",
        "CIK_SEDAR": r["cik"], "IR_URL": "", "Latest_Annual_Filing": "", "Latest_Interim_Filing": "",
        "Dual_Listed": "No", "Include_In_Ranking": "Yes",
        "In_SP500": "Yes", "In_TSX_Composite": "No", "In_TSX60": "No",
        "In_SPUS": "Yes" if in_spus else "No",
        "Data_Source": "Wikipedia 'List of S&P 500 companies' (2026-08-20); validated vs user SPY Holdings.xlsx",
        "Retrieval_Date": TODAY, "Notes": f"HQ: {r['hq']}; added {r['date_added']}",
    })

# CA rows
for _, r in ca.iterrows():
    t = r["Ticker"]
    yt = yahoo_ca(t)
    in60 = r["_nt"] in tsx60_syms
    sub = r["GICS_Industry"]
    cis = "Utilities_Regulated" if r["_nt"] == "H" else custom_industry_sheet(r["GICS_Sector"], sub)
    rows.append({
        "Universe_Effective_Date": TODAY, "Ticker": t, "Primary_Ticker": yt, "Yahoo_Ticker": yt,
        "Secondary_Ticker": "", "Share_Class": "Unit (REIT)" if ".UN" in str(t) else "Common",
        "Company_Name": r["Company"], "Country_of_Listing": "CA", "Exchange": "TSX",
        "Primary_Currency": "CAD", "Financials_Native_Currency": "CAD", "Trading_Currency": "CAD",
        "Reporting_Standard": "IFRS", "GICS_Sector": r["GICS_Sector"], "GICS_Industry_Group": "",
        "GICS_Industry": sub, "GICS_Sub_Industry": "", "Custom_Industry_Sheet": cis,
        "Market_Cap_Native": "", "Market_Cap_USD": "", "Shares_Out": "", "Price": "",
        "Price_Date": "", "Market_Data_As_Of": "", "Financials_As_Of": "", "Fiscal_Year_End": "",
        "CIK_SEDAR": "", "IR_URL": "", "Latest_Annual_Filing": "", "Latest_Interim_Filing": "",
        "Dual_Listed": "", "Include_In_Ranking": "Yes",
        "In_SP500": "No", "In_TSX_Composite": "Yes", "In_TSX60": "Yes" if in60 else "No",
        "In_SPUS": "No",
        "Data_Source": "Wikipedia 'S&P/TSX Composite Index' (2026-08-20); TSX60 from 'S&P/TSX 60' (2026-01-31)",
        "Retrieval_Date": TODAY, "Notes": "",
    })

df = pd.DataFrame(rows, columns=cols)
df.to_csv(os.path.join(RAW, "universe_master.csv"), index=False)

# ----------------------------------------------------------------------------
# write to workbook
# ----------------------------------------------------------------------------
wb = openpyxl.load_workbook(XLSX)
ws = wb["Universe"]
# clear existing data rows (keep header)
if ws.max_row > 1:
    ws.delete_rows(2, ws.max_row - 1)
for i, row in enumerate(df.itertuples(index=False), start=2):
    for j, v in enumerate(row, start=1):
        ws.cell(row=i, column=j, value=v)
wb.save(XLSX)

# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------
n_total = len(df)
n_us = (df["Country_of_Listing"] == "US").sum()
n_ca = (df["Country_of_Listing"] == "CA").sum()
n_sp500 = (df["In_SP500"] == "Yes").sum()
n_tsxc = (df["In_TSX_Composite"] == "Yes").sum()
n_tsx60 = (df["In_TSX60"] == "Yes").sum()
n_spus = (df["In_SPUS"] == "Yes").sum()

print("=" * 70)
print("PHASE 1 UNIVERSE REPORT")
print("=" * 70)
print(f"Total companies: {n_total}  (US {n_us} | CA {n_ca})")
print(f"In_SP500={n_sp500} | In_TSX_Composite={n_tsxc} | In_TSX60={n_tsx60} | In_SPUS={n_spus}")
print(f"Share-class consolidation: US 503 tickers -> {n_us} companies")
print("\nBy GICS sector (combined):")
sec = df.groupby("GICS_Sector").size().sort_values(ascending=False)
for s, c in sec.items():
    us_c = ((df["GICS_Sector"] == s) & (df["Country_of_Listing"] == "US")).sum()
    ca_c = ((df["GICS_Sector"] == s) & (df["Country_of_Listing"] == "CA")).sum()
    print(f"  {s:24s} total={c:3d}  (US {us_c} | CA {ca_c})")

print("\nBy Custom_Industry_Sheet:")
cis = df.groupby("Custom_Industry_Sheet").size().sort_values(ascending=False)
for s, c in cis.items():
    print(f"  {s:28s} {c}")

print(f"\nMissing GICS_Sector: {(df['GICS_Sector'].isna() | (df['GICS_Sector']=='')).sum()}")
print(f"SPY-seed tickers NOT in current S&P 500 (removed, {len(removed)}):", sorted(removed)[:30])
print(f"Current S&P 500 tickers NOT in SPY seed (added, {len(added)}):", sorted(added)[:40])

# Hydro One check
ho = df[(df["Ticker"] == "H") | (df["Company_Name"].str.contains("Hydro One", na=False))]
print("\nHydro One rows:")
print(ho[["Ticker","Primary_Ticker","Company_Name","Country_of_Listing","GICS_Sector","Custom_Industry_Sheet","Financials_Native_Currency","In_TSX60"]].to_string(index=False))

# TSX60 symbols not matched in composite
comp_nt = set(ca["_nt"])
unmatched60 = tsx60_syms - comp_nt
print(f"\nTSX60 symbols not found in Composite list ({len(unmatched60)}):", sorted(unmatched60))

# 20-row sample
print("\n20-row sample:")
sample = pd.concat([df[df["Country_of_Listing"]=="US"].head(10), df[df["Country_of_Listing"]=="CA"].head(10)])
print(sample[["Ticker","Company_Name","Country_of_Listing","GICS_Sector","Custom_Industry_Sheet","In_SP500","In_TSX_Composite","In_TSX60","In_SPUS"]].to_string(index=False))
