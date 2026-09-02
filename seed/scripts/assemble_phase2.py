# -*- coding: utf-8 -*-
"""
Phase 2 — assemble pilot: normalize raw -> Time_Series + Source_Audit + Core_Financials
+ 8 industry sheets + within-peer-group rankings.
Derived metrics computed ONLY where raw inputs valid (else blank + logged).
"""
import os, math
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill

ROOT = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research"
RAW = os.path.join(ROOT, "raw")
XLSX = os.path.join(ROOT, "NA_Company_Financials.xlsx")
TODAY = "2026-08-20"

# ----------------------------------------------------------------------------
# pilot metadata: ticker -> country, industry sheet, fiscal year end, name
# ----------------------------------------------------------------------------
PILOT = {
    # ticker: (country, industry_sheet, fy_month, fy_day, company_name, currency)
    "JPM": ("US", "Banks", 12, 31, "JPMorgan Chase & Co.", "USD"),
    "BAC": ("US", "Banks", 12, 31, "Bank of America Corp.", "USD"),
    "WFC": ("US", "Banks", 12, 31, "Wells Fargo & Co.", "USD"),
    "NEE": ("US", "Utilities_Regulated", 12, 31, "NextEra Energy, Inc.", "USD"),
    "DUK": ("US", "Utilities_Regulated", 12, 31, "Duke Energy Corp.", "USD"),
    "MSFT": ("US", "Software", 6, 30, "Microsoft Corp.", "USD"),
    "AAPL": ("US", "Tech", 9, 30, "Apple Inc.", "USD"),
    "GOOGL": ("US", "Internet_Platforms", 12, 31, "Alphabet Inc.", "USD"),
    "AMZN": ("US", "Consumer_Cyclical", 12, 31, "Amazon.com, Inc.", "USD"),
    "META": ("US", "Internet_Platforms", 12, 31, "Meta Platforms, Inc.", "USD"),
    "UNP": ("US", "Railroads", 12, 31, "Union Pacific Corp.", "USD"),
    "RY": ("CA", "Banks", 10, 31, "Royal Bank of Canada", "CAD"),
    "TD": ("CA", "Banks", 10, 31, "Toronto-Dominion Bank", "CAD"),
    "BNS": ("CA", "Banks", 10, 31, "Bank of Nova Scotia", "CAD"),
    "BMO": ("CA", "Banks", 10, 31, "Bank of Montreal", "CAD"),
    "CM": ("CA", "Banks", 10, 31, "CIBC", "CAD"),
    "NA": ("CA", "Banks", 10, 31, "National Bank of Canada", "CAD"),
    "H": ("CA", "Utilities_Regulated", 12, 31, "Hydro One Limited", "CAD"),
    "FTS": ("CA", "Utilities_Regulated", 12, 31, "Fortis Inc.", "CAD"),
    "EMA": ("CA", "Utilities_Regulated", 12, 31, "Emera Incorporated", "CAD"),
    "ENB": ("CA", "Pipelines_Midstream", 12, 31, "Enbridge Inc.", "CAD"),
    "TRP": ("CA", "Pipelines_Midstream", 12, 31, "TC Energy Corp.", "CAD"),
    "CNR": ("CA", "Railroads", 12, 31, "Canadian National Railway", "CAD"),
    "CP": ("CA", "Railroads", 12, 31, "Canadian Pacific Kansas City", "CAD"),
    "BCE": ("CA", "Telecom", 12, 31, "BCE Inc.", "CAD"),
    "T": ("CA", "Telecom", 12, 31, "Telus Corporation", "CAD"),
    "RCI-B": ("CA", "Telecom", 12, 31, "Rogers Communications", "CAD"),
}
# US EDGAR uses ticker without suffix; CA yfinance uses .TO
YF_TICKER = {t: (t if c == "US" else t + ".TO") for t, (c, *_ ) in PILOT.items()}

# metric -> primary us-gaap tag (for Source_Audit Page_or_XBRL_Tag)
TAG = {
    "Revenue": "Revenues", "CostOfRevenue": "CostOfRevenue", "GrossProfit": "GrossProfit",
    "OperatingIncome": "OperatingIncomeLoss", "NetIncome": "NetIncomeLoss",
    "EPS_diluted": "EarningsPerShareDiluted", "InterestExpense": "InterestExpense",
    "R&D": "ResearchAndDevelopmentExpense", "SG&A": "SellingGeneralAndAdministrativeExpense",
    "D&A": "DepreciationDepletionAndAmortization",
    "OCF": "NetCashProvidedByUsedInOperatingActivities", "Capex": "PaymentsToAcquirePropertyPlantAndEquipment",
    "PretaxIncome": "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "TaxProvision": "IncomeTaxExpenseBenefit",
    "Cash": "CashAndCashEquivalentsAtCarryingValue", "STInvestments": "ShortTermInvestments",
    "Receivables": "AccountsReceivableNetCurrent", "Inventory": "InventoryNet", "Payables": "AccountsPayableCurrent",
    "CurrentAssets": "AssetsCurrent", "CurrentLiabilities": "LiabilitiesCurrent", "TotalAssets": "Assets",
    "LongTermDebt": "LongTermDebtNoncurrent", "ShortTermDebt": "LongTermDebtCurrent",
    "TotalDebt": "TotalDebt", "Equity": "StockholdersEquity", "Goodwill": "Goodwill",
    "Intangibles": "FiniteLivedIntangibleAssetsNet", "EBITDA": "EBITDA",
    "SharesDiluted": "WeightedAverageNumberOfDilutedSharesOutstanding",
}

# ----------------------------------------------------------------------------
# load raw
# ----------------------------------------------------------------------------
us_annual = pd.read_csv(os.path.join(RAW, "edgar_annual.csv"))
us_ttm = pd.read_csv(os.path.join(RAW, "edgar_ttm.csv"))
ca = pd.read_csv(os.path.join(RAW, "yfinance_ca.csv"))
ca_meta = pd.read_csv(os.path.join(RAW, "yfinance_ca_meta.csv"), index_col=0)
us_meta = pd.read_csv(os.path.join(RAW, "us_meta.csv"), index_col=0)

# unify: build long df with ticker(base), metric, fy, value
us_annual["fy"] = us_annual["fy"].astype(int)
ca["fy"] = pd.to_datetime(ca["period"]).dt.year.astype(int)
ca["ticker"] = ca["ticker"].str.replace(".TO", "", regex=False)

long = pd.concat([
    us_annual[["ticker", "metric", "fy", "value"]],
    ca[["ticker", "metric", "fy", "value"]],
], ignore_index=True)

def get_hist(t, metric):
    s = long[(long["ticker"] == t) & (long["metric"] == metric)].dropna(subset=["value"])
    return {int(fy): v for fy, v in zip(s["fy"], s["value"])}

def latest(t, metric, max_fy=None):
    h = get_hist(t, metric)
    if not h:
        return None
    if max_fy is not None:
        h = {fy: v for fy, v in h.items() if fy <= max_fy}
    if not h:
        return None
    if max_fy is not None and max(h) < max_fy - 1:
        return None  # stale metric (not current) -> treat as missing
    return h[max(h)]

def safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b

def _f(x): return "n/a" if x is None else f"{x:,.0f}"
def _p(x): return "n/a" if x is None else f"{x*100:.1f}%"
def _f2(x): return "n/a" if x is None else f"{x:.2f}"

# latest completed fiscal year per company (max fy with Revenue)
latest_fy = {}
for t in PILOT:
    h = get_hist(t, "Revenue")
    latest_fy[t] = max(h) if h else None

# ----------------------------------------------------------------------------
# build per-company latest-FY raw dict + derived metrics
# ----------------------------------------------------------------------------
records = {}
for t, (country, sheet, mm, dd, name, curr) in PILOT.items():
    fy = latest_fy[t]
    d = {}
    def L(m): return latest(t, m, fy)
    d["Ticker"] = t; d["Company_Name"] = name; d["Custom_Industry_Sheet"] = sheet
    d["Country"] = country; d["Currency"] = curr; d["Latest_FY"] = fy
    d["Fiscal_Period_End"] = f"{fy}-{mm:02d}-{dd:02d}" if fy else ""
    # raw
    d["Revenue"] = L("Revenue"); d["CostOfRevenue"] = L("CostOfRevenue"); d["GrossProfit"] = L("GrossProfit")
    d["OperatingIncome"] = L("OperatingIncome"); d["NetIncome"] = L("NetIncome")
    d["EPS"] = L("EPS_diluted"); d["InterestExpense"] = L("InterestExpense")
    d["RnD"] = L("R&D"); d["SGA"] = L("SG&A"); d["DA"] = L("D&A")
    d["EBITDA_reported"] = L("EBITDA")
    d["PretaxIncome"] = L("PretaxIncome"); d["TaxProvision"] = L("TaxProvision")
    d["Cash"] = L("Cash"); d["STInv"] = L("STInvestments")
    d["Receivables"] = L("Receivables"); d["Inventory"] = L("Inventory")
    d["Payables"] = L("Payables"); d["CurrentAssets"] = L("CurrentAssets")
    d["CurrentLiabilities"] = L("CurrentLiabilities"); d["TotalAssets"] = L("TotalAssets")
    d["TotalDebt"] = L("TotalDebt")
    if d["TotalDebt"] is None:
        lt = L("LongTermDebt"); st = L("ShortTermDebt")
        d["TotalDebt"] = (lt if lt is not None else 0) + (st if st is not None else 0)
    d["Equity"] = L("Equity"); d["Goodwill"] = L("Goodwill"); d["Intangibles"] = L("Intangibles")
    d["OCF"] = L("OCF"); d["Capex"] = L("Capex")
    # market data
    meta = us_meta if country == "US" else ca_meta
    mrow = meta.loc[YF_TICKER[t]] if YF_TICKER[t] in meta.index else None
    d["Price"] = mrow["price"] if mrow is not None and pd.notna(mrow["price"]) else None
    d["SharesDiluted"] = mrow["shares"] if mrow is not None and pd.notna(mrow["shares"]) else None
    d["MarketCap"] = mrow["mktcap"] if mrow is not None and pd.notna(mrow["mktcap"]) else None
    # ---- derived (validated) ----
    is_bank = sheet == "Banks"
    d["CashST"] = (d["Cash"] or 0) + (d["STInv"] or 0) if (d["Cash"] is not None or d["STInv"] is not None) else None
    # gross profit: prefer Revenue - CostOfRevenue (XBRL most reliable); banks have no COGS -> NA
    if d["CostOfRevenue"] is not None and d["Revenue"] is not None:
        d["GrossProfit"] = d["Revenue"] - d["CostOfRevenue"]
    d["GrossMargin"] = safe_div(d["GrossProfit"], d["Revenue"])
    d["OperatingMargin"] = safe_div(d["OperatingIncome"], d["Revenue"])
    d["NetMargin"] = safe_div(d["NetIncome"], d["Revenue"])
    d["EBITDA"] = d["EBITDA_reported"] if d["EBITDA_reported"] is not None else (
        (d["OperatingIncome"] + d["DA"]) if (d["OperatingIncome"] is not None and d["DA"] is not None) else None)
    d["TaxRate"] = safe_div(d["TaxProvision"], d["PretaxIncome"])
    if d["TaxRate"] is not None:
        d["TaxRate"] = max(0.0, min(0.35, d["TaxRate"]))
    d["NetDebt"] = (d["TotalDebt"] - d["CashST"]) if (d["TotalDebt"] is not None and d["CashST"] is not None) else None
    d["CurrentRatio"] = safe_div(d["CurrentAssets"], d["CurrentLiabilities"])
    d["QuickRatio"] = safe_div((d["CashST"] or 0) + (d["Receivables"] or 0), d["CurrentLiabilities"]) if d["CurrentLiabilities"] is not None else None
    d["DebtEquity"] = None if is_bank else safe_div(d["TotalDebt"], d["Equity"])
    d["NetDebtEBITDA"] = None if is_bank else safe_div(d["NetDebt"], d["EBITDA"])
    d["InterestCoverage"] = safe_div(d["OperatingIncome"], d["InterestExpense"])
    d["ROE"] = safe_div(d["NetIncome"], d["Equity"])
    d["ROA"] = safe_div(d["NetIncome"], d["TotalAssets"])
    nopat = (d["OperatingIncome"] * (1 - (d["TaxRate"] if d["TaxRate"] is not None else 0))) if d["OperatingIncome"] is not None else None
    invcap = ((d["Equity"] or 0) + (d["TotalDebt"] or 0) - (d["CashST"] or 0)) if (d["Equity"] is not None or d["TotalDebt"] is not None) else None
    d["ROIC"] = safe_div(nopat, invcap) if nopat is not None else None
    d["GrossProfitability"] = safe_div(d["GrossProfit"], d["TotalAssets"])
    d["FCF"] = (d["OCF"] - d["Capex"]) if (d["OCF"] is not None and d["Capex"] is not None) else None
    d["FCFMargin"] = safe_div(d["FCF"], d["Revenue"])
    d["FCFF_NI"] = safe_div(d["FCF"], d["NetIncome"])
    d["Accruals"] = safe_div((d["NetIncome"] - d["OCF"]) if (d["NetIncome"] is not None and d["OCF"] is not None) else None, d["TotalAssets"])
    # valuation
    d["BVPS"] = safe_div(d["Equity"], d["SharesDiluted"])
    d["PE"] = safe_div(d["Price"], d["EPS"])
    d["PB"] = safe_div(d["Price"], d["BVPS"])
    ev = ((d["MarketCap"] or 0) + (d["TotalDebt"] or 0) - (d["CashST"] or 0)) if d["MarketCap"] is not None else None
    d["EV"] = ev
    d["EV_EBITDA"] = safe_div(ev, d["EBITDA"])
    d["EV_EBIT"] = safe_div(ev, d["OperatingIncome"])
    d["EV_Sales"] = safe_div(ev, d["Revenue"])
    d["EarningsYield"] = safe_div(d["OperatingIncome"], ev)
    d["FCFYield"] = safe_div(d["FCF"], d["MarketCap"])
    records[t] = d

# ----------------------------------------------------------------------------
# CAGR helpers
# ----------------------------------------------------------------------------
def cagr(t, metric, years):
    h = get_hist(t, metric)
    fy = latest_fy[t]
    if not fy or len(h) < 2:
        return None
    end = h.get(fy); start = h.get(fy - years)
    if end is None or start is None or start == 0:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except Exception:
        return None

# ----------------------------------------------------------------------------
# write to workbook
# ----------------------------------------------------------------------------
wb = openpyxl.load_workbook(XLSX)

# --- Time_Series ---
ts = wb["Time_Series"]
if ts.max_row > 1:
    ts.delete_rows(2, ts.max_row - 1)
ts_cols = ["Ticker", "Fiscal_Year", "Field", "Value", "Unit", "Currency", "Source", "Retrieval_Date", "Notes"]
tsr = 2
for t in PILOT:
    country, sheet, mm, dd, name, curr = PILOT[t]
    for metric in long[long["ticker"] == t]["metric"].unique():
        h = get_hist(t, metric)
        for fy in sorted(h):
            src = "SEC EDGAR XBRL (10-K)" if country == "US" else "Aggregator (Yahoo Finance)"
            for j, v in enumerate([t, fy, metric, h[fy], "native", curr, src, TODAY, ""], start=1):
                ts.cell(row=tsr, column=j, value=v)
            tsr += 1

# --- Source_Audit (latest FY values feeding Core_Financials) ---
sa = wb["Source_Audit"]
if sa.max_row > 1:
    sa.delete_rows(2, sa.max_row - 1)
sa_cols = ["Ticker", "Fiscal_Period", "Metric", "Value", "Unit", "Source_URL", "Filing_Type",
           "Filing_Date", "Page_or_XBRL_Tag", "Retrieval_Date", "Extraction_Method", "Confidence", "Notes"]
sar = 2
AUDIT_METRICS = ["Revenue", "GrossProfit", "OperatingIncome", "NetIncome", "EPS_diluted",
                 "InterestExpense", "R&D", "SG&A", "D&A", "PretaxIncome", "TaxProvision",
                 "Cash", "STInvestments", "Receivables", "Inventory", "Payables",
                 "CurrentAssets", "CurrentLiabilities", "TotalAssets", "TotalDebt",
                 "Equity", "Goodwill", "Intangibles", "OCF", "Capex", "EBITDA"]
for t in PILOT:
    country, sheet, mm, dd, name, curr = PILOT[t]
    fy = latest_fy[t]
    if not fy:
        continue
    for metric in AUDIT_METRICS:
        v = latest(t, metric, fy)
        if v is None:
            continue
        if country == "US":
            url = "https://data.sec.gov/api/xbrl/companyfacts/CIK.json"
            ftype = "10-K (annual)"; tag = TAG.get(metric, metric)
            meth = "XBRL companyfacts (us-gaap)"; conf = "High"
        else:
            url = f"https://finance.yahoo.com/quote/{YF_TICKER[t]}/financials"
            ftype = "Annual (aggregator)"; tag = metric
            meth = "Aggregator (Yahoo Finance)"; conf = "Medium (aggregator, not primary filing)"
        row = [t, f"{fy}-{mm:02d}-{dd:02d}", metric, v, "native", url, ftype,
               f"{fy}-{mm:02d}-{dd:02d}", tag, TODAY, meth, conf, ""]
        for j, val in enumerate(row, start=1):
            sa.cell(row=sar, column=j, value=val)
        sar += 1

# --- Core_Financials ---
cf = wb["Core_Financials"]
cfh = [c.value for c in cf[1]]
cfidx = {h: i + 1 for i, h in enumerate(cfh)}
if cf.max_row > 1:
    cf.delete_rows(2, cf.max_row - 1)
CORE_MAP = {
    "Ticker": "Ticker", "Company_Name": "Company_Name", "Custom_Industry_Sheet": "Custom_Industry_Sheet",
    "Revenue": "Revenue", "Gross_Profit": "GrossProfit", "Gross_Margin": "GrossMargin",
    "Operating_Income_EBIT": "OperatingIncome", "Operating_Margin": "OperatingMargin",
    "EBITDA": "EBITDA", "Net_Income": "NetIncome", "Diluted_EPS": "EPS",
    "Interest_Expense": "InterestExpense", "Tax_Rate_Effective": "TaxRate",
    "R_D": "RnD", "SG_A": "SGA",
    "Cash_ST_Investments": "CashST", "Receivables": "Receivables", "Inventory": "Inventory",
    "Payables": "Payables", "Current_Assets": "CurrentAssets", "Current_Liabilities": "CurrentLiabilities",
    "Total_Assets": "TotalAssets", "Total_Debt": "TotalDebt", "Net_Debt": "NetDebt",
    "Book_Equity": "Equity", "Current_Ratio": "CurrentRatio", "Quick_Ratio": "QuickRatio",
    "Debt_Equity": "DebtEquity", "Net_Debt_EBITDA": "NetDebtEBITDA", "Interest_Coverage": "InterestCoverage",
    "Operating_Cash_Flow": "OCF", "Capex": "Capex", "Free_Cash_Flow": "FCF",
    "FCF_Margin": "FCFMargin", "FCF_NI": "FCFF_NI", "Accruals": "Accruals",
    "ROE": "ROE", "ROA": "ROA", "ROIC": "ROIC", "Gross_Profitability": "GrossProfitability",
    "DuPont_Net_Margin": "NetMargin", "PE_Trailing": "PE", "PB": "PB",
    "EV_EBITDA": "EV_EBITDA", "EV_EBIT": "EV_EBIT", "EV_Sales": "EV_Sales",
    "Earnings_Yield": "EarningsYield", "FCF_Yield_MktCap": "FCFYield",
    "Price": "Price", "Market_Cap": "MarketCap", "Enterprise_Value": "EV", "Shares_Diluted": "SharesDiluted",
    "Source_Primary": "src_primary", "Source_Aggregator": "src_agg", "Retrieval_Date": "src_date",
}
cfr = 2
for t in PILOT:
    d = records[t]
    country = PILOT[t][0]
    d["src_primary"] = "SEC EDGAR 10-K" if country == "US" else "SEDAR+ (pending); Yahoo used"
    d["src_agg"] = "" if country == "US" else "Yahoo Finance"
    d["src_date"] = TODAY
    for col, key in CORE_MAP.items():
        if col in cfidx:
            cf.cell(row=cfr, column=cfidx[col], value=d.get(key))
    cfr += 1

# --- industry sheets (8) + rankings ---
SHEETS = ["Banks", "Utilities_Regulated", "Pipelines_Midstream", "Railroads", "Telecom",
          "Software", "Semiconductors_Components", "Internet_Platforms"]
IND_HEADER = ["Ticker", "Company_Name", "Custom_Industry_Sheet", "Revenue", "Net_Income",
              "ROE", "ROIC", "Gross_Margin", "Interest_Coverage", "Net_Debt_EBITDA",
              "PE", "PB", "Earnings_Yield", "FCF_Yield", "Composite_Score", "Sector_Rank"]
HDR_FILL = PatternFill("solid", fgColor="1F4E78")
HDR_FONT = Font(bold=True, color="FFFFFF")
for s in SHEETS:
    if s not in wb.sheetnames:
        ws = wb.create_sheet(s)
    else:
        ws = wb[s]
    for j, h in enumerate(IND_HEADER, start=1):
        c = ws.cell(row=1, column=j, value=h)
        c.fill = HDR_FILL; c.font = HDR_FONT
    ws.freeze_panes = "A2"

def pct_rank(vals, higher_better=True):
    """percentile 0-100 for a list, ignoring None."""
    idx = [i for i, v in enumerate(vals) if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if len(idx) < 2:
        return [None] * len(vals)
    arr = np.array([vals[i] for i in idx])
    ranks = pd.Series(arr).rank(pct=True).to_numpy()
    out = [None] * len(vals)
    for k, i in enumerate(idx):
        p = ranks[k] * 100
        out[i] = p if higher_better else 100 - p
    return out

# compute scores per industry sheet
rankings = {}
for sheet in SHEETS:
    members = [t for t in PILOT if PILOT[t][1] == sheet]
    if not members:
        rankings[sheet] = []
        continue
    roe = [records[t]["ROE"] for t in members]
    roic = [records[t]["ROIC"] for t in members]
    gm = [records[t]["GrossMargin"] for t in members]
    ic = [records[t]["InterestCoverage"] for t in members]
    nde = [records[t]["NetDebtEBITDA"] for t in members]
    ey = [records[t]["EarningsYield"] for t in members]
    fy = [records[t]["FCFYield"] for t in members]
    pb = [records[t]["PB"] for t in members]
    pe = [records[t]["PE"] for t in members]
    is_bank = sheet == "Banks"
    # composite: quality (ROE/ROIC) + health (IC, ND/EBITDA) + value (EY, PB/PE inverted)
    q = [pct_rank(roe)[i] if roe[i] is not None else (pct_rank(roic)[i] if roic[i] is not None else None) for i in range(len(members))]
    h_ic = pct_rank(ic); h_nde = pct_rank(nde)
    v_ey = pct_rank(ey); v_pb = pct_rank(pb, higher_better=False); v_pe = pct_rank(pe, higher_better=False)
    comp = []
    for i in range(len(members)):
        parts = []
        if q[i] is not None: parts.append(q[i])
        if is_bank:
            if v_pb[i] is not None: parts.append(v_pb[i]); parts.append(v_pb[i])  # banks: value heavy, no nde
        else:
            if h_nde[i] is not None: parts.append(h_nde[i])
            if h_ic[i] is not None: parts.append(h_ic[i])
        if v_ey[i] is not None: parts.append(v_ey[i])
        if v_pe[i] is not None: parts.append(v_pe[i])
        comp.append(np.mean(parts) if parts else None)
    ranked = sorted(range(len(members)), key=lambda i: (comp[i] is None, -(comp[i] or 0)))
    rank_map = {members[i]: rk + 1 for rk, i in enumerate(ranked)}
    rankings[sheet] = [(members[i], records[members[i]]["Company_Name"], round(comp[i], 1) if comp[i] is not None else None,
                        rank_map[members[i]]) for i in range(len(members))]
    rankings[sheet].sort(key=lambda x: x[3])
    # write to sheet
    ws = wb[sheet]
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    for i in range(len(members)):
        t = members[i]
        d = records[t]
        row_vals = [t, d["Company_Name"], sheet,
                    d["Revenue"], d["NetIncome"], d["ROE"], d["ROIC"], d["GrossMargin"],
                    d["InterestCoverage"], d["NetDebtEBITDA"], d["PE"], d["PB"],
                    d["EarningsYield"], d["FCFYield"], round(comp[i], 1) if comp[i] is not None else None,
                    rank_map[t]]
        for j, v in enumerate(row_vals, start=1):
            ws.cell(row=2 + i, column=j, value=v)

wb.save(XLSX)

# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------
print("=" * 80)
print("PHASE 2 PILOT REPORT")
print("=" * 80)
n = len(records)
print(f"Companies: {n} (US {sum(1 for t in PILOT if PILOT[t][0]=='US')} | CA {sum(1 for t in PILOT if PILOT[t][0]=='CA')})")
print(f"Latest FY per company (Revenue): { {t: latest_fy[t] for t in PILOT} }")

# metric coverage
cov = {}
for t in PILOT:
    for k, v in records[t].items():
        cov.setdefault(k, 0)
        if v is not None and v != "":
            cov[k] += 1
print("\nMetric coverage (non-null across 27 companies):")
NA_heavy = []
for k in sorted(cov):
    c = cov[k]
    pct = c / n
    if k in ("Revenue","NetIncome","TotalAssets","Equity","OCF","Capex","TotalDebt","EPS","OperatingIncome","InterestExpense","D&A","CashST","Receivables","Payables","CurrentAssets","CurrentLiabilities","Inventory","GrossProfit","SGA","RnD","PretaxIncome","TaxProvision","EBITDA","FCF","ROE","ROA","ROIC","GrossMargin","OperatingMargin","NetMargin","CurrentRatio","InterestCoverage","NetDebt","NetDebtEBITDA","DebtEquity","FCFMargin","FCFF_NI","Accruals","PE","PB","EV_EBITDA","EarningsYield","FCFYield"):
        flag = "  <-- NA-heavy" if c < n * 0.5 else ""
        if c < n * 0.5:
            NA_heavy.append((k, c))
        print(f"  {k:22s} {c:2d}/{n}{flag}")

print(f"\nNA-heavy fields ({len(NA_heavy)}):", [k for k, _ in NA_heavy])

# Source_Audit count
print(f"\nSource_Audit rows: {sar - 2}")

print("\nRankings:")
for sheet in SHEETS:
    if rankings[sheet]:
        print(f"\n  {sheet} ({len(rankings[sheet])} members):")
        for t, name, comp, rk in rankings[sheet]:
            print(f"    #{rk} {t:8s} {name:34s} composite={comp}")
    else:
        print(f"\n  {sheet}: no pilot members")

# reconciliation sample (raw vs derived) for 10 companies
print("\n10-company reconciliation sample (raw -> derived):")
for t in list(PILOT)[:10]:
    d = records[t]
    print(f"  {t:6s} Rev={_f(d['Revenue'])} NI={_f(d['NetIncome'])} GM={_p(d['GrossMargin'])} "
          f"ROE={_p(d['ROE'])} FCF={_f(d['FCF'])} ND/EBITDA={_f2(d['NetDebtEBITDA'])} PE={_f2(d['PE'])}")
