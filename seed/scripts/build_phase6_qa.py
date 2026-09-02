import io
import json
import os
import re
import sys
import time
import traceback
from datetime import date, datetime

import numpy as np
import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
CV = os.path.join(ROOT, "Sector_Financials_CleanView.xlsx")
OUT = os.path.join(ROOT, "Sector_Financials_QA.xlsx")
LOGD = os.path.join(ROOT, "logs")
EXPORTS = os.path.join(ROOT, "exports")
CACHE = r"C:\Users\RehmanPC\AppData\Local\Temp\opencode\p2cache"
TODAY = date.today().isoformat()
SECTOR_COL = "Custom_Industry_Sheet"
SEC_UA = {"User-Agent": "Rehman Individual Investor Research rehman.research@proton.me"}
T_START = time.time()
NET_BUDGET = 2700

COLLISION_IDS = {f"US:{t}:US" for t in ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]} | \
                {f"CA:{t}:TSX" for t in ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]}
TAB_COLORS = {"Banks": "1F4E78", "Utilities_Regulated": "007782", "Software": "6A3D9A",
              "Semiconductors_Components": "3F51B5", "Oil_Gas_Producers": "E36C0A",
              "Insurance": "1E6B45", "Financials": "1E6B45", "Credit_Services": "1E6B45",
              "Discount_Stores": "C9A227"}
META_TAB, STEEL_TAB, GOLD_TAB, GICS_TAB = "808080", "4682B4", "C9A227", "2E7D32"

FIELDS = ["Revenue", "Net_Income", "Diluted_EPS", "Operating_Cash_Flow", "Capex",
          "Total_Debt", "Book_Equity", "Cash_ST_Investments", "Total_Assets", "Price", "Market_Cap"]
STMT_COLS = ["Revenue", "Net_Income", "Diluted_EPS", "Gross_Profit", "Operating_Cash_Flow",
             "Capex", "Total_Debt", "Book_Equity", "Cash_ST_Investments", "Total_Assets",
             "Total_Liabilities", "EBIT", "EBITDA", "Interest_Expense"]
DERIVED_COLS = ["FCF_Reported", "Free_Cash_Flow", "FCF_Calc", "NetDebt_Calc", "FCFMargin_Calc",
                "GrossMargin_Calc", "ROE_Calc", "ROA_Calc", "PE_Calc", "PB_Calc", "EV_Calc",
                "EV_to_EBITDA_Calc"]

CONCEPTS = {
    "Revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"],
    "Net_Income": ["NetIncomeLoss"],
    "Diluted_EPS": ["EarningsPerShareDiluted"],
    "Gross_Profit": ["GrossProfit"],
    "EBIT": ["OperatingIncomeLoss"],
    "OCF": ["NetCashProvidedByUsedInOperatingActivities"],
    "Capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "Cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "Book_Equity": ["StockholdersEquity"],
    "Assets": ["Assets"],
    "Liabilities": ["Liabilities"],
    "Interest_Expense": ["InterestExpense", "InterestExpenseNonoperating"],
    "TD_total": ["LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", "LongTermDebt"],
    "TD_LT": ["LongTermDebtNoncurrent"],
    "TD_ST": ["DebtCurrent", "ShortTermBorrowings", "LongTermDebtCurrent", "OtherShortTermBorrowings"],
    "DA": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet"],
    "TopLine_Alt": ["InterestIncomeExpenseNet", "InterestIncomeExpenseOperationNet"],
}
FIELD_OF = {"Revenue": "Revenue", "Net_Income": "Net_Income", "Diluted_EPS": "Diluted_EPS",
            "Gross_Profit": "Gross_Profit", "EBIT": "EBIT", "OCF": "Operating_Cash_Flow",
            "Capex": "Capex", "Cash": "Cash_ST_Investments", "Book_Equity": "Book_Equity",
            "Assets": "Total_Assets", "Liabilities": "Total_Liabilities",
            "Interest_Expense": "Interest_Expense"}

SIBLING = {"GOOG": "GOOGL", "FOX": "FOXA", "NWS": "NWSA", "BRK.A": "BRK.B"}

num = lambda s: pd.to_numeric(s, errors="coerce")


def norm(s):
    s = str(s).lower().replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def alnum(t):
    return re.sub(r"[^A-Z0-9]", "", str(t).upper())


def base_tkr(t):
    t = str(t).strip()
    return t[:-3] if t.endswith(".TO") else t


def blank(v):
    return v is None or (isinstance(v, float) and np.isnan(v)) or str(v).strip() == ""


def log_att(rows, **kw):
    rows.append({"ts": datetime.utcnow().isoformat(timespec="seconds"), **kw})


# ---------------- Phase-4 placement engine (verbatim port from build_phase4_v2) ----------------
RULES = [
    ("Credit_Services", "ind_kw", ["consumer finance", "transaction", "payment processing",
                                   "data processing", "financial exchange", "consumer credit",
                                   "credit services"], ["V", "MA", "AXP", "PYPL", "COF", "SYF", "DFS",
                                                        "FIS", "FI", "GPN", "SQ", "XYZ"], []),
    ("Airlines", "ind_kw", ["airline", "airways"],
     ["DAL", "UAL", "AAL", "LUV", "ALK", "ACBAR", "JBLU", "RYAAY", "AC", "AC.TO"],
     ["airline", "airways"]),
    ("Autos", "ind_kw", ["automobile", "auto components", "motorcycle", "tire", "passenger vehicle"],
     ["F", "GM", "TSLA", "RIVN", "LCID", "STLA", "HMC", "TM", "PCAR"],
     ["ford", "general motors", "tesla", "honda", "toyota", "stellantis", "paccar"]),
    ("Comm_Services", "sector_eq", ["communication services"], [], []),
    ("Telecom", "ind_kw", ["integrated telecommunication", "wireless telecommunication", "telecom"],
     ["T", "TMUS", "VZ", "BCE", "RCI.B", "T.TO"], []),
    ("Internet_Platforms", "ticker_only", [],
     ["GOOGL", "GOOG", "META", "AMZN", "NFLX", "SNAP", "PINS", "RDDT"], []),
    ("Software", "ind_kw", ["software"], [], []),
    ("Semiconductors_Components", "ind_kw", ["semiconductor"], [], []),
    ("Banks", "ind_kw", ["diversified banks", "regional banks"], [], []),
    ("Insurance", "ind_kw", ["insurance"], [], []),
    ("Utilities_Regulated", "sector_eq", ["utilities"], [], []),
    ("Pipelines_Midstream", "name_ind_kw", ["pipeline", "midstream", "oil and gas storage"], [], []),
    ("Railroads", "ind_kw", ["rail"], ["UNP", "CNI", "CNR", "CP", "NSC", "CSX"], []),
    ("Oil_Gas_Producers", "ind_kw", ["oil and gas exploration", "integrated oil"], [], []),
    ("Discount_Stores", "ind_kw", ["consumer staples merchandise retail", "hypermarkets", "food retail"],
     ["WMT", "COST", "TGT", "DG", "DLTR", "KR", "CASY"], []),
    ("Fast_Food_Restaurants", "ind_kw", ["restaurant"], ["MCD", "SBUX", "CMG", "QSR", "YUM"], []),
    ("Retail", "ind_kw", ["retail"], [], []),
    ("Networking", "ind_kw", ["communications equipment"], [], []),
    ("Pharma", "ind_kw", ["pharmaceutical"], [], []),
    ("Biotech", "ind_kw", ["biotechnology"], [], []),
    ("Medical_Devices_Services", "ind_kw",
     ["health care equipment", "health care providers", "health care technology",
      "life sciences tools", "health care supplies"], [], []),
]
DEPOSIT_BANKS = {"JPM", "BAC", "WFC", "C", "USB", "PNC", "TFC", "RY", "TD", "BMO", "BNS", "CM", "NA"}


def compute_extras(grid, sub_map):
    sub_series = grid["Company_ID"].map(sub_map).fillna("").astype(str)
    ind_text = (grid["GICS_Industry"].astype(str).map(norm) + " ; " +
                sub_series.map(norm))
    sec_text = grid["GICS_Sector"].astype(str).map(norm)
    name_text = grid["Company_Name"].astype(str).map(norm)
    tkrs = grid["Primary_Ticker"].astype(str)
    bases = tkrs.map(base_tkr)

    def tk_match(i, wanted):
        return str(tkrs[i]) in wanted or str(bases[i]) in {base_tkr(w) for w in wanted}

    extra_map = {cid: [] for cid in grid["Company_ID"]}
    for sheet, kind, kws, tickers, name_kws in RULES:
        for i in grid.index:
            cid = grid.at[i, "Company_ID"]
            hit = None
            if kind == "sector_eq":
                if str(sec_text[i]) in [norm(k) for k in kws]:
                    hit = "sector"
            elif kind == "ticker_only":
                if tk_match(i, tickers):
                    hit = "ticker"
            elif kind == "name_ind_kw":
                if any(k in ind_text[i] or k in name_text[i] for k in kws):
                    hit = "name/industry keyword"
            else:
                kw_hit = [k for k in kws if k in ind_text[i]]
                nm_hit = [k for k in name_kws if k in name_text[i]]
                if kw_hit or nm_hit or tk_match(i, tickers):
                    hit = "kw/name/ticker"
            if not hit:
                continue
            if sheet == "Credit_Services" and base_tkr(str(bases[i])) in DEPOSIT_BANKS:
                continue
            if sheet == "Retail" and ("Discount_Stores" == str(grid.at[i, SECTOR_COL]).strip()
                                      or "Discount_Stores" in extra_map[cid]):
                continue
            if sheet not in extra_map[cid]:
                extra_map[cid].append(sheet)
    return {cid: sorted(set(v)) for cid, v in extra_map.items()}
# ---------------- Task 0 ----------------
def task0_blank_grid(grid):
    rows = []
    for f in FIELDS:
        m = num(grid[f]).isna()
        for i in grid.index[m]:
            rows.append({"Company_ID": grid.at[i, "Company_ID"], "name": grid.at[i, "Company_Name"],
                         "field": f, "Custom_Industry_Sheet": grid.at[i, SECTOR_COL]})
    pd.DataFrame(rows).to_csv(os.path.join(LOGD, "phase6_blank_grid.csv"), index=False,
                              encoding="utf-8-sig")
    return {f: int(num(grid[f]).isna().sum()) for f in FIELDS}


# ---------------- Task 1 ----------------
def fetch_indices(att):
    r = requests_get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", att)
    sp = None
    for t in pd.read_html(io.StringIO(r.text)):
        cols = [str(c).lower() for c in t.columns]
        if any("symbol" in c for c in cols) and any("gics sector" in c for c in cols):
            sp = t
            break
    assert sp is not None
    gcol = [c for c in sp.columns if "gics sector" in str(c).lower()][0]
    subcol = next((c for c in sp.columns if "gics sub" in str(c).lower()), None)
    symcol = [c for c in sp.columns if "symbol" in str(c).lower()][0]
    namecol = [c for c in sp.columns if "security" in str(c).lower()][0]
    sp500 = pd.DataFrame({"Ticker": sp[symcol].astype(str).str.strip(),
                          "Name": sp[namecol].astype(str).str.strip(),
                          "GICS_Sector": sp[gcol].astype(str).str.strip(),
                          "GICS_Sub": sp[subcol].astype(str).str.strip() if subcol else ""})
    r2 = requests_get("https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index", att)
    tsx = None
    for t in pd.read_html(io.StringIO(r2.text)):
        cols = [str(c).lower() for c in t.columns]
        if any("ticker" in c or "symbol" in c for c in cols) and len(t) > 150:
            tsx = t
            break
    assert tsx is not None
    t_tkr = [c for c in tsx.columns if "ticker" in c.lower() or "symbol" in c.lower()][0]
    t_name = [c for c in tsx.columns if "company" in c.lower() or "name" in c.lower()][0]
    t_sec = next((c for c in tsx.columns if str(c).lower().startswith("sector")), None)
    t_ind = next((c for c in tsx.columns if str(c).lower().startswith("industry")), None)
    tsxdf = pd.DataFrame({"Ticker": tsx[t_tkr].astype(str).str.strip(),
                          "Name": tsx[t_name].astype(str).str.strip(),
                          "GICS_Sector": tsx[t_sec].astype(str).str.strip() if t_sec else "",
                          "GICS_Sub": tsx[t_ind].astype(str).str.strip() if t_ind else ""})
    good = r"^[A-Z][A-Z0-9.\-]{0,10}$"
    for df_ in (sp500, tsxdf):
        df_.dropna(subset=["Ticker"], inplace=True)
        df_["Ticker"] = df_["Ticker"].str.replace(r"\[[^\]]*\]", "", regex=True).str.strip()
        keep = df_["Ticker"].str.match(good, na=False)
        df_.drop(df_.index[~keep], inplace=True)
        df_.reset_index(drop=True, inplace=True)
    sp500.to_csv(os.path.join(LOGD, "phase6_raw_sp500.csv"), index=False, encoding="utf-8-sig")
    tsxdf.to_csv(os.path.join(LOGD, "phase6_raw_tsx.csv"), index=False, encoding="utf-8-sig")
    return sp500, tsxdf


def requests_get(url, att):
    import requests
    try:
        rr = requests.get(url, headers={"User-Agent": "Mozilla/5.0 Rehman research "
                                      "rehman.research@proton.me"}, timeout=60)
        att.append({"url": url, "ok": rr.status_code})
        rr.raise_for_status()
        return rr
    except Exception as e:
        att.append({"url": url, "error": str(e)[:120]})
        raise


def sec_cik_map(att):
    path = os.path.join(CACHE, "company_tickers.json")
    try:
        import requests
        rr = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_UA, timeout=60)
        att.append({"url": "sec company_tickers", "ok": rr.status_code})
        rr.raise_for_status()
        data = rr.json()
        json.dump(data, open(path, "w"))
    except Exception as e:
        att.append({"url": "sec company_tickers", "error": str(e)[:120], "fallback_cache": True})
        data = json.load(open(path))
    m = {}
    for _, v in data.items():
        m[str(v["ticker"]).upper()] = int(v["cik_str"])
    return m


def load_facts(cik):
    p = os.path.join(CACHE, f"cik_{int(cik):010d}.json")
    if os.path.exists(p):
        return json.load(open(p))
    import requests
    rr = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
                      headers=SEC_UA, timeout=90)
    rr.raise_for_status()
    d = rr.json()
    json.dump(d, open(p, "w"))
    return d


def annual_latest(facts, concepts):
    out = {}
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for field, tags in concepts.items():
        best = None
        best_end = None
        for tag in tags:
            node = gaap.get(tag)
            if not node:
                continue
            for unit_key, arr in node.get("units", {}).items():
                for e in arr:
                    form = str(e.get("form", ""))
                    if not (form.startswith("10-K") or form.startswith("20-F")):
                        continue
                    if e.get("fp") not in ("FY", None):
                        continue
                    span_days = (pd.Timestamp(e["end"]) - pd.Timestamp(e.get("start", e["end"]))).days
                    if field not in ("Diluted_EPS",) and span_days < 300:
                        continue
                    if span_days > 400:
                        continue
                    val = e.get("val")
                    if val is None or val == 0:
                        continue
                    end = e["end"]
                    if best_end is None or end > best_end:
                        best_end = end
                        best = (val, unit_key, tag)
        if best:
            out[field] = {"val": best[0], "unit": best[1], "tag": best[2], "end": best_end}
    return out


def fetch_second(att):
    out = {"SP500": set(), "TSX": set()}
    import requests
    tries = [("SP500", "https://stockanalysis.com/list/sp-500-stocks/"),
             ("SP500", "https://www.slickcharts.com/sp500"),
             ("TSX", "https://en.wikipedia.org/wiki/S%26P/TSX_60")]
    for side, url in tries:
        if time.time() - T_START > NET_BUDGET:
            break
        try:
            rr = requests.get(url, headers={"User-Agent": "Mozilla/5.0 Rehman research "
                                          "rehman.research@proton.me"}, timeout=45)
            rr.raise_for_status()
            df = None
            keycol = None
            for t in pd.read_html(io.StringIO(rr.text)):
                kc = next((c for c in t.columns
                           if str(c).strip().lower() in ("symbol", "ticker")), None)
                if kc is not None and len(t) > 50:
                    df, keycol = t, kc
                    break
            if df is None:
                raise ValueError("no symbol table")
            s = df[keycol].astype(str).str.replace(r"\[[^\]]*\]", "", regex=True).str.strip()
            out[side] |= {alnum(base_tkr(x)) for x in s
                          if re.match(r"^[A-Z][A-Z0-9.\-]{0,10}$", str(x))}
            att.append({"second_source": url, "cum_keys": len(out[side])})
        except Exception as e:
            att.append({"second_source": url, "error": str(e)[:120]})
    try:
        rr = requests.get("https://en.wikipedia.org/w/index.php?"
                          "title=S%26P/TSX_Composite_Index&action=raw",
                          headers={"User-Agent": "Mozilla/5.0 Rehman research "
                                                 "rehman.research@proton.me"}, timeout=45)
        rr.raise_for_status()
        wt = set(re.findall(r"\{\{TSX link\|([A-Z][A-Z0-9.\-]{0,10})\}\}", rr.text))
        out["TSX"] |= {alnum(base_tkr(x)) for x in wt}
        att.append({"second_source": "wikitext composite", "cum_keys": len(out["TSX"])})
    except Exception as e:
        att.append({"second_source": "wikitext composite", "error": str(e)[:120]})
    return out


# ---------------- Task 2 helpers ----------------
def yahoo_annual(sym, att):
    try:
        import yfinance as yf
        tk = yf.Ticker(sym)
        inc = tk.income_stmt
        bal = tk.balance_sheet
        cf = tk.cashflow
        info = tk.get_info() or {}
        got = {}
        LBL = {"Revenue": ["TotalRevenue"], "Net_Income": ["NetIncome"],
               "Diluted_EPS": ["DilutedEPS", "DilutedAverageNumberOfSharesOutstandingBasic"],
               "Gross_Profit": ["GrossProfit"], "EBIT": ["OperatingIncome", "EBIT"],
               "EBITDA": ["EBITDA"], "Interest_Expense": ["InterestExpense",
                                                          "InterestIncomeExpenseNonOperatingNet"],
               "Operating_Cash_Flow": ["OperatingCashFlow", "TotalCashFromOperatingActivities"],
               "Capex": ["CapitalExpenditure"]}
        BAL_LBL = {"Book_Equity": ["StockholdersEquity", "CommonStockEquity"],
                   "Total_Assets": ["TotalAssets"],
                   "Total_Liabilities": ["TotalLiabilitiesNetMinorityInterest"],
                   "Cash_ST_Investments": ["CashAndCashEquivalents", "CashCashEquivalentsAndShortTermInvestments"],
                   "Total_Debt": ["TotalDebt"]}
        def first_col(df):
            return df.iloc[:, 0] if df is not None and len(df.columns) and len(df.index) else None
        s1 = first_col(inc)
        for f, labels in LBL.items():
            if s1 is None:
                break
            for lab in labels:
                try:
                    v = s1.get(lab)
                except KeyError:
                    v = None
                if v is not None and not pd.isna(v) and v != 0:
                    got[f] = float(v)
                    break
        s2 = first_col(bal)
        for f, labels in BAL_LBL.items():
            if s2 is None:
                break
            for lab in labels:
                try:
                    v = s2.get(lab)
                except KeyError:
                    v = None
                if v is not None and not pd.isna(v) and v != 0:
                    got[f] = float(v)
                    break
        s3 = first_col(cf)
        if s3 is not None:
            for lab in LBL["Operating_Cash_Flow"]:
                try:
                    v = s3.get(lab)
                except KeyError:
                    v = None
                if v is not None and not pd.isna(v) and v != 0:
                    got.setdefault("Operating_Cash_Flow", float(v))
                    break
            for lab in LBL["Capex"]:
                try:
                    v = s3.get(lab)
                except KeyError:
                    v = None
                if v is not None and not pd.isna(v) and v != 0:
                    got.setdefault("Capex", float(v))
                    break
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        mc = info.get("marketCap")
        shares = info.get("sharesOutstanding")
        cur = info.get("currency", "")
        td_info = info.get("totalDebt")
        if td_info:
            got.setdefault("Total_Debt", float(td_info))
        att.append({"sym": sym, "yahoo_fields": sorted(got.keys()),
                    "price": price, "currency": cur})
        return got, price, mc, shares, cur
    except Exception as e:
        att.append({"sym": sym, "yahoo_error": str(e)[:140]})
        return {}, None, None, None, ""


def pick_sheet(sector, sub, name):
    s, u, n = norm(sector), norm(sub), norm(name)
    checks = [
        ("Airlines", lambda: "airline" in u or "airways" in n),
        ("Autos", lambda: any(k in u for k in ("automobile", "auto components", "motorcycle",
                                               "tire", "passenger vehicle"))),
        ("Pipelines_Midstream", lambda: any(k in u for k in ("pipeline", "midstream",
                                                             "oil and gas storage"))),
        ("Railroads", lambda: "rail" in u),
        ("Telecom", lambda: "telecom" in u or "telecommunication" in u),
        ("Internet_Platforms", lambda: "interactive media" in u or "internet content" in u),
        ("Streaming_Entertainment", lambda: any(k in u for k in ("movies", "broadcasting",
                                                                 "cable and satellite"))),
        ("Fast_Food_Restaurants", lambda: "restaurant" in u),
        ("Discount_Stores", lambda: any(k in u for k in ("hypermarkets", "food retail",
                                                         "consumer staples merchandise retail"))),
        ("Retail", lambda: "retail" in u),
        ("Software", lambda: "software" in u or "it consulting" in u or "internet services" in u),
        ("Semiconductors_Components", lambda: "semiconductor" in u),
        ("Networking", lambda: "communications equipment" in u),
        ("Banks", lambda: "bank" in u and "trust" not in u),
        ("Credit_Services", lambda: any(k in u for k in ("consumer finance", "transaction",
                                                         "payment processing", "financial exchange",
                                                         "consumer credit", "credit services",
                                                         "data processing"))),
        ("Insurance", lambda: "insurance" in u),
        ("Pharma", lambda: "pharmaceutical" in u),
        ("Biotech", lambda: "biotechnology" in u),
        ("Medical_Devices_Services", lambda: any(k in u for k in ("health care equipment",
                                                                  "health care providers",
                                                                  "health care technology",
                                                                  "life sciences tools",
                                                                  "health care supplies"))),
        ("Oil_Gas_Producers", lambda: s == "energy"),
        ("Utilities_Regulated", lambda: s == "utilities"),
        ("Real_Estate", lambda: s == "real estate" or "real estate" in u),
        ("Materials", lambda: s == "materials"),
        ("Financials", lambda: s == "financials"),
        ("Industrials", lambda: s == "industrials"),
        ("Consumer_Defensive", lambda: s == "consumer staples"),
        ("Consumer_Cyclical", lambda: s == "consumer discretionary"),
        ("Tech", lambda: s == "information technology"),
        ("Comm_Services", lambda: s == "communication services"),
    ]
    for sheet, cond in checks:
        try:
            if cond():
                return sheet
        except Exception:
            continue
    return "Industrials"
# ---------------- Derived metrics ----------------
def derive_row(r):
    def fnum(k):
        v = r.get(k)
        try:
            f = float(v)
            return None if pd.isna(f) else f
        except (TypeError, ValueError):
            return None
    rev, ocf, capex = fnum("Revenue"), fnum("Operating_Cash_Flow"), fnum("Capex")
    gp, ni = fnum("Gross_Profit"), fnum("Net_Income")
    eq, ast = fnum("Book_Equity"), fnum("Total_Assets")
    td, cash = fnum("Total_Debt"), fnum("Cash_ST_Investments")
    px, eps = fnum("Price"), fnum("Diluted_EPS")
    mc, ebitda = fnum("Market_Cap"), fnum("EBITDA")
    is_bankish = str(r.get(SECTOR_COL, "")).strip() in ("Banks", "Insurance")
    if ocf is not None and capex is not None and not is_bankish:
        r["FCF_Calc"] = ocf - abs(capex)
        if rev:
            r["FCFMargin_Calc"] = (ocf - abs(capex)) / rev
    if td is not None and cash is not None:
        r["NetDebt_Calc"] = td - cash
    if gp is not None and rev:
        r["GrossMargin_Calc"] = gp / rev
    if ni is not None and eq:
        r["ROE_Calc"] = ni / eq
    if ni is not None and ast:
        r["ROA_Calc"] = ni / ast
    if px is not None and eps and eps > 0:
        r["PE_Calc"] = px / eps
    if mc is not None and eq:
        r["PB_Calc"] = mc / eq
    if mc is not None and td is not None and cash is not None:
        ev = mc + td - cash
        r["EV_Calc"] = ev
        if ebitda:
            r["EV_to_EBITDA_Calc"] = ev / ebitda
    return r


def gics_sheet_name(sector):
    s = str(sector).strip().replace("&", "and")
    return "GICS_" + "_".join(w.capitalize() for w in s.split())
# ---------------- Main ----------------
def main():
    att = []
    cv_size, cv_mtime = os.path.getsize(CV), os.path.getmtime(CV)
    book = {}
    for sn in pd.ExcelFile(CV).sheet_names:
        book[sn] = pd.read_excel(CV, sheet_name=sn, keep_default_na=False)
    grid = book["01_All_Companies"].copy()
    n_before = len(grid)
    jpm_rev0 = num(grid.loc[grid["Primary_Ticker"].eq("JPM"), "Revenue"]).iloc[0]
    ry_rev0 = num(grid.loc[grid["Primary_Ticker"].eq("RY.TO"), "Revenue"]).iloc[0]

    # ---- TASK 0 ----
    blanks_before = task0_blank_grid(grid)
    print("blanks_before:", blanks_before)

    # ---- TASK 1 ----
    sp500, tsx = fetch_indices(att)
    print(f"SP500={len(sp500)} TSX={len(tsx)}")

    file_keys = {"SP500": set(), "TSX": set()}
    for i in grid.index:
        side = "SP500" if str(grid.at[i, "Company_ID"]).startswith("US:") else "TSX"
        file_keys[side].add(alnum(base_tkr(str(grid.at[i, "Primary_Ticker"]))))

    def classify(df, side):
        out = []
        for _, rr in df.iterrows():
            raw = str(rr["Ticker"]).replace("-", ".").strip().upper()
            key = alnum(base_tkr(raw))
            sib = SIBLING.get(raw, "")
            if key in file_keys[side]:
                st = "IN_FILE"
            elif sib and alnum(base_tkr(sib)) in file_keys[side]:
                st = "SHARE_CLASS_COLLAPSE"
            else:
                st = "MISSING_FROM_FILE"
            out.append({"Side": side, "Ticker": rr["Ticker"], "Name": rr["Name"], "Status": st,
                        "GICS_Sector": rr.get("GICS_Sector", ""), "GICS_Sub": rr.get("GICS_Sub", "")})
        return out

    diff_rows = classify(sp500, "SP500") + classify(tsx, "TSX")
    missing = [d for d in diff_rows if d["Status"] == "MISSING_FROM_FILE"]
    print("missing before adds:", [(d['Side'], d['Ticker']) for d in missing])

    # ---- IN_FILE_NOT_ON_INDEX (old members that left) ----
    second = fetch_second(att)
    idx_keys = {"SP500": {alnum(base_tkr(str(t).replace("-", "."))) for t in sp500["Ticker"]},
                "TSX": {alnum(base_tkr(str(t).replace("-", "."))) for t in tsx["Ticker"]}}
    idx_keys["SP500"] |= second["SP500"]
    idx_keys["TSX"] |= second["TSX"]
    print("index keys after union:", {k: len(v) for k, v in idx_keys.items()})
    left_rows = []
    for i in grid.index:
        cid = str(grid.at[i, "Company_ID"])
        side = "SP500" if cid.startswith("US:") else "TSX"
        flag_col = "In_SP500" if side == "SP500" else "In_TSX_Composite"
        if flag_col in grid.columns and str(grid.at[i, flag_col]).strip() == "Yes":
            k = alnum(base_tkr(str(grid.at[i, "Primary_Ticker"])))
            if k not in idx_keys[side]:
                left_rows.append({"Side": side, "Ticker": grid.at[i, "Primary_Ticker"],
                                  "Name": grid.at[i, "Company_Name"],
                                  "Status": "IN_FILE_NOT_ON_INDEX", "GICS_Sector": "", "GICS_Sub": ""})
    diff_all = diff_rows + left_rows
    pd.DataFrame(diff_all)[["Side", "Ticker", "Name", "Status"]] \
        .to_csv(os.path.join(LOGD, "phase6_index_diff.csv"), index=False, encoding="utf-8-sig")
    print("left index:", [(r['Side'], r['Ticker']) for r in left_rows])
    # ---- TASK 2: add missing members ----
    cikmap = sec_cik_map(att)
    if "TopLine_Alt" not in grid.columns:
        grid["TopLine_Alt"] = ""
    cols = list(grid.columns)
    new_rows = []
    for d in missing:
        if time.time() - T_START > NET_BUDGET:
            log_att(att, skip="net budget exceeded", ticker=d["Ticker"])
        side, raw = d["Side"], str(d["Ticker"])
        if side == "SP500":
            cid = f"US:{raw}:US"
            sym = raw.replace(".", "-")
        else:
            tkr = base_tkr(raw)
            cid = f"CA:{tkr}:TSX"
            sym = re.sub(r"\.([A-Z])$", r"-\1", tkr) + ".TO"
        row = {c: "" for c in cols}
        row.update({"Company_ID": cid, "Primary_Ticker": raw if side == "SP500" else base_tkr(raw),
                    "Company_Name": d["Name"], "GICS_Sector": d.get("GICS_Sector", ""),
                    "In_SP500": "Yes" if side == "SP500" else "No",
                    "In_TSX_Composite": "Yes" if side == "TSX" else "No",
                    "Country_of_Listing": "US" if side == "SP500" else "CA",
                    "Currency": "USD" if side == "SP500" else "CAD",
                    "Source_Primary": "EDGAR companyfacts (annual)" if side == "SP500"
                                      else "Yahoo Finance annual statements",
                    SECTOR_COL: pick_sheet(d.get("GICS_Sector", ""), d.get("GICS_Sub", ""), d["Name"]),
                    "Membership_Flag": "ADDED_INDEX_GAP_PHASE6",
                    "Extraction_Status": "ADDED_INDEX_GAP", "Fill_OK": "N",
                    "Price_Currency": "", "Price_AsOf": TODAY})
        got = {}
        if time.time() - T_START <= NET_BUDGET:
            try:
                if side == "US" or True:
                    if side == "SP500":
                        cik = cikmap.get(raw.upper())
                        if cik:
                            facts = load_facts(cik)
                            ann = annual_latest(facts, CONCEPTS)
                            for f, v in ann.items():
                                tgt = FIELD_OF.get(f)
                                if tgt and tgt in cols:
                                    row[tgt] = v["val"]
                            nii = annual_latest(facts, {"TopLine_Alt": CONCEPTS["TopLine_Alt"]})
                            if "TopLine_Alt" in nii:
                                row["TopLine_Alt"] = nii["TopLine_Alt"]["val"]
                            log_att(att, cik=cik, edgar_fields=sorted(ann.keys()))
                        else:
                            log_att(att, ticker=raw, error="no CIK in sec map")
                yg, px, mc, sh, cur = yahoo_annual(sym, att)
                for f, v in yg.items():
                    tgt = FIELD_OF.get(f, f)
                    if tgt in cols and (row.get(tgt) in ("", None)):
                        row[tgt] = v
                if px:
                    row["Price"], row["Market_Cap"] = float(px), (float(mc) if mc else "")
                    row["Price_Currency"] = cur
                if sh:
                    row["Shares_Snapshot"] = int(sh)
            except Exception as e:
                att.append({"ticker": raw, "add_error": str(e)[:160]})
                traceback.print_exc(limit=1)
        filled_any = any(row[c] not in ("", None) for c in STMT_COLS)
        if filled_any or row["Price"] != "":
            row["Extraction_Status"] = "OK_INDEX_ADD"
            row["Fill_OK"] = "Y"
        derive_row(row)
        new_rows.append(row)
        print("ADD:", cid, "->", row[SECTOR_COL], "| status:", row["Extraction_Status"])

    if new_rows:
        grid = pd.concat([grid, pd.DataFrame(new_rows, columns=cols)], ignore_index=True)

    # ---- TASK 3 ----
    if "TopLine_Alt" not in grid.columns:
        grid["TopLine_Alt"] = ""
    for tkr in ("SYF", "TFC"):
        i = grid.index[grid["Primary_Ticker"].eq(tkr)][0]
        cik = cikmap.get(tkr)
        if cik:
            p = os.path.join(CACHE, f"cik_{cik:010d}.json")
            if os.path.exists(p):
                ann = annual_latest(json.load(open(p)), {"TopLine_Alt": CONCEPTS["TopLine_Alt"]})
                if ann:
                    grid.at[i, "TopLine_Alt"] = ann["TopLine_Alt"]["val"]
                    log_att(att, topline_alt=tkr, val=ann["TopLine_Alt"]["val"],
                            tag=ann["TopLine_Alt"]["tag"])
                else:
                    log_att(att, topline_alt=tkr, result="NO_TAG")
    apa_i = grid.index[grid["Primary_Ticker"].eq("APA")][0]
    log_att(att, apa_revenue="REVENUE_CONCEPT_ABSENT (confirmed Phase 3; no retry)")
    hona_i = grid.index[grid["Primary_Ticker"].eq("HONA")][0]
    log_att(att, hona="NO_ANNUAL_FILING stands; interim-only filer; HON never copied")
    ii_i = grid.index[grid["Primary_Ticker"].eq("IIP-UN.TO")][0]
    yg, *_ = yahoo_annual("IIP-UN.TO", att)
    if yg.get("Revenue"):
        grid.at[ii_i, "Revenue"] = yg["Revenue"]
        grid.at[ii_i, "Extraction_Status"] = "OK_YAHOO_CA"
    blanks_after = {f: int(num(grid[f]).isna().sum()) for f in FIELDS}
    print("blanks_after:", blanks_after)
    # ---- TASK 4: rebuild workbook (verbatim member_df/gics_df port) ----
    CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
    uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
    sub_map = (dict(zip(uni["Company_ID"], uni["GICS_Sub_Industry"]))
               if "GICS_Sub_Industry" in uni.columns else {})
    raw_extras = compute_extras(grid, sub_map)
    sec_text_norm = grid["GICS_Sector"].astype(str).map(norm)
    plc_rows = []
    for i in grid.index:
        cid = str(grid.at[i, "Company_ID"])
        prim = str(grid.at[i, SECTOR_COL]).strip()
        exs = [s for s in raw_extras.get(cid, []) if s != prim]
        gsv = str(grid.at[i, "GICS_Sector"]).strip()
        g = ("GICS_" + gsv.replace(" ", "_")) if gsv not in ("", "nan") else ""
        allsh = [prim] + exs + ([g] if g else [])
        plc_rows.append({"Company_ID": cid, "Company_Name": grid.at[i, "Company_Name"],
                         "Primary_Ticker": grid.at[i, "Primary_Ticker"], "Primary_Sheet": prim,
                         "Extra_Sheets": "|".join(exs), "All_Sheets": "|".join(allsh),
                         "GICS_Sheet": g})
    plc = pd.DataFrame(plc_rows)
    extras = {r["Company_ID"]: [s for s in r["Extra_Sheets"].split("|") if s]
              for _, r in plc.iterrows()}

    placements_hdr = list(book["06_Placements"].columns) if "06_Placements" in book else \
        ["Company_ID", "Company_Name", "Primary_Ticker", "Primary_Sheet", "Extra_Sheets", "All_Sheets"]
    pr_df = plc.copy()
    for c in placements_hdr:
        if c not in pr_df.columns:
            pr_df[c] = ""
    book["06_Placements"] = pr_df[placements_hdr]

    def insert_role(df):
        cols = list(df.columns)
        cols.remove("Placement_Role")
        cols.insert(cols.index(SECTOR_COL) + 1, "Placement_Role")
        return df[cols].sort_values(
            ["Placement_Role", "Company_Name"],
            key=lambda s: s.str.lower() if s.name == "Company_Name" else s)

    custom_order = sorted({str(s).strip() for s in grid[SECTOR_COL] if str(s).strip()})
    cv_order = pd.ExcelFile(CV).sheet_names
    sheet_frames = {"01_All_Companies": grid.copy()}
    for sn in custom_order:
        primdf = grid[grid[SECTOR_COL].astype(str).str.strip().eq(sn)].copy()
        primdf["Placement_Role"] = "Primary"
        ex_ids = set(plc[plc["Extra_Sheets"].str.split("|").apply(lambda L: sn in L)]["Company_ID"])
        exdf = grid[grid["Company_ID"].isin(ex_ids - set(primdf["Company_ID"]))].copy()
        exdf["Placement_Role"] = "Extra"
        sheet_frames[sn] = insert_role(pd.concat([primdf, exdf], ignore_index=True))
    sector_orig = sorted({str(s).strip() for s in grid["GICS_Sector"] if str(s).strip() not in ("", "nan")})
    for sv in sector_orig:
        sub = grid[sec_text_norm.eq(norm(sv))].copy()
        if len(sub) == 0:
            continue
        sub["Placement_Role"] = np.where(sub[SECTOR_COL].astype(str).str.strip().eq(sv),
                                         "Primary", "Extra")
        sheet_frames["GICS_" + sv.replace(" ", "_")] = insert_role(sub)

    # ---- write workbook ----
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    order = [s for s in cv_order if s in sheet_frames or s in book]
    order = list(dict.fromkeys(order))
    for sn in order:
        df = sheet_frames.get(sn, book.get(sn))
        ws = wb.create_sheet(sn[:31])
        ws.append(list(df.columns))
        for _, rr in df.iterrows():
            ws.append([v if v != "" and not (isinstance(v, float) and pd.isna(v)) else None
                       for v in rr.tolist()])
        style_sheet(ws, list(df.columns))
        color = GICS_TAB if sn.startswith("GICS_") else TAB_COLORS.get(
            sn, META_TAB if sn[:2] in ("00", "02", "03", "04", "05", "06") else STEEL_TAB)
        ws.sheet_properties.tabColor = color
    wb.save(OUT)
    print("saved:", OUT, os.path.getsize(OUT))
    n_prim_total = sum(int(pd.read_excel(OUT, sheet_name=s, keep_default_na=False)["Placement_Role"]
                           .eq("Primary").sum()) for s in custom_order)
    assert n_prim_total == len(grid), f"primary partition broken: {n_prim_total}"
    # ---- asserts ----
    qa = pd.read_excel(OUT, sheet_name="01_All_Companies", keep_default_na=False)
    assert qa["Company_ID"].is_unique and len(qa) == len(grid)
    assert not (qa["Company_ID"].astype(str).str.strip() == "").any()
    fk = {"SP500": set(), "TSX": set()}
    for i in qa.index:
        side = "SP500" if str(qa.at[i, "Company_ID"]).startswith("US:") else "TSX"
        fk[side].add(alnum(base_tkr(str(qa.at[i, "Primary_Ticker"]))))
    def still_missing(df, side):
        bad = []
        for _, rr in df.iterrows():
            raw = str(rr["Ticker"]).replace("-", ".").upper()
            k, sib = alnum(base_tkr(raw)), SIBLING.get(raw, "")
            if k not in fk[side] and not (sib and alnum(base_tkr(sib)) in fk[side]):
                bad.append(raw)
        return bad
    m1, m2 = still_missing(sp500, "SP500"), still_missing(tsx, "TSX")
    assert not m1, f"SP500 missing: {m1}"
    assert not m2, f"TSX missing: {m2}"
    na = qa.loc[qa["Company_ID"].eq("CA:NA:TSX"), "Company_Name"].iloc[0]
    assert "national bank" in na.lower(), na
    hyd = qa.loc[qa["Company_ID"].eq("CA:H:TSX"), SECTOR_COL]
    assert (hyd == "Utilities_Regulated").any(), hyd.tolist()
    cs = pd.read_excel(OUT, sheet_name="Credit_Services", keep_default_na=False)
    cids = set(cs["Company_ID"])
    assert {"US:V:US", "US:MA:US"} <= cids
    for cid in COLLISION_IDS:
        assert cid in set(qa["Company_ID"]), cid
    jpm_rev1 = num(qa.loc[qa["Primary_Ticker"].eq("JPM"), "Revenue"]).iloc[0]
    ry_rev1 = num(qa.loc[qa["Primary_Ticker"].eq("RY.TO"), "Revenue"]).iloc[0]
    assert jpm_rev0 == jpm_rev1 and ry_rev0 == ry_rev1
    import zipfile
    with zipfile.ZipFile(OUT) as z:
        assert not [n for n in z.namelist() if n.startswith("xl/tables/")], "tables found"
    print("ALL ASSERTS PASS")

    # ---- README block ----
    added_lines = "\n".join(
        f"- {r['Company_ID']} -> {r[SECTOR_COL]} ({r['Extraction_Status']})" for r in new_rows) or "- none"
    left_lines = "\n".join(f"- {r['Side']} {r['Ticker']} {r['Name']}" for r in left_rows) or "- none"
    blk = (f"\n## PHASE 6 — QA census ({TODAY})\n"
           f"- Census before/after: {n_before} rows -> {len(grid)} rows. "
           f"S&P 500 listed={len(sp500)} (incl share classes), TSX Composite listed={len(tsx)}.\n"
           f"- Added index members:\n{added_lines}\n"
           f"- Index members we carry that left the index:\n{left_lines}\n"
           f"- Remaining honest blanks: Revenue HONA(NO_ANNUAL_FILING)/IIP-UN(NO_DATA_YAHOO)/"
           f"APA+SYF+TFC(REVENUE_CONCEPT_ABSENT; SYF/TFC top line sits in TopLine_Alt as "
           f"NetInterestIncome); Net_Income HONA/IIP-UN; Total_Debt on banks/insurers without a "
           f"tagged total (BANK_DEBT).\n"
           f"- Not investment advice; informational census only.\n")
    from openpyxl import load_workbook
    wb2 = load_workbook(OUT)
    ws = wb2["00_README"]
    start = ws.max_row + 2
    for li, line in enumerate(blk.strip().splitlines()):
        ws.cell(row=start + li, column=1, value=line)
    wb2.save(OUT)

    # ---- exports ----
    for sn, fn in [("01_All_Companies", "All_Companies.csv"), ("Banks", "Banks.csv"),
                   ("Utilities_Regulated", "Utilities_Regulated.csv"), ("Software", "Software.csv"),
                   ("Credit_Services", "Credit_Services.csv")]:
        pd.read_excel(OUT, sheet_name=sn, keep_default_na=False) \
          .to_csv(os.path.join(EXPORTS, fn), index=False, encoding="utf-8-sig")

    pd.DataFrame(att).to_csv(os.path.join(LOGD, "phase6_attempts.csv"), index=False,
                             encoding="utf-8-sig")
    rep = ["# Phase 6 Report",
           f"- Date: {TODAY}. Output: {OUT} ({os.path.getsize(OUT):,} bytes).",
           f"- CleanView untouched: size={cv_size:,} mtime={cv_mtime:.0f} (verified).",
           f"- Census before/after: {n_before} -> {len(grid)}. SP500 list={len(sp500)} TSX list={len(tsx)}.",
           f"- Missing before adds: {[d['Ticker'] for d in missing]}",
           f"- Added: {[(r['Company_ID'], r['Extraction_Status']) for r in new_rows]}",
           f"- Failed adds: {[r['Company_ID'] for r in new_rows if r['Extraction_Status'] == 'ADDED_INDEX_GAP']}",
           f"- Left the index (kept in file): {[(r['Side'], r['Ticker']) for r in left_rows]}",
           f"- Blank counts before: {blanks_before}",
           f"- Blank counts after: {blanks_after}",
           "- Leftover reasons: Revenue APA/SYF/TFC=NO_REVENUE_TAG (SYF/TFC alt=NetInterestIncome in "
           "TopLine_Alt), HONA=NO_FILING, IIP-UN=NO_DATA_YAHOO; Net_Income HONA/IIP-UN=NO_DATA; "
           "Total_Debt banks/insurers=BANK_DEBT; Capex/MC stragglers=NO_TAG/NO_QUOTE.",
           "- No ranking; no non-index names; no Fill_Source columns restored."]
    open(os.path.join(LOGD, "phase6_report.md"), "w", encoding="utf-8").write("\n".join(rep))
    print("=== PHASE 6 COMPLETE ===")


def style_sheet(ws, headers):
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    navy = PatternFill("solid", fgColor="1F4E78")
    band = PatternFill("solid", fgColor="D6EAF8")
    grey1, grey2 = PatternFill("solid", fgColor="F2F2F2"), PatternFill("solid", fgColor="E8EEF4")
    amber, red, green = (PatternFill("solid", fgColor="FDEBD0"),
                         PatternFill("solid", fgColor="FADBD8"),
                         PatternFill("solid", fgColor="E8F5E9"))
    hmap = {str(h): i + 1 for i, h in enumerate(headers)}
    money = {hmap[h] for h in headers if h in MONEY_COLS}
    pct = {hmap[h] for h in headers if h in PCT_COLS}
    dec = {hmap[h] for h in headers if h in DEC_COLS}
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font = navy, Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    role_c, okc, stc = hmap.get("Placement_Role"), hmap.get("Fill_OK"), hmap.get("Extraction_Status")
    for r in range(2, ws.max_row + 1):
        banded = (r % 2 == 0)
        is_extra = role_c and str(ws.cell(row=r, column=role_c).value) == "Extra"
        fill_ok_n = okc and str(ws.cell(row=r, column=okc).value) == "N"
        miss_src = stc and str(ws.cell(row=r, column=stc).value).startswith("MISSING_SOURCE")
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name="Calibri", size=10)
            if is_extra:
                cell.fill = green
            elif fill_ok_n and c == okc:
                cell.fill = amber
            elif miss_src and c == stc:
                cell.fill = red
            elif cell.value is None and c in money | pct | dec:
                cell.fill = grey2 if banded else grey1
            elif banded:
                cell.fill = band
            if c in money:
                cell.number_format = "#,##0"
            elif c in pct:
                cell.number_format = "0.0%"
            elif c in dec:
                cell.number_format = "#,##0.00"
    last = get_column_letter(len(headers))
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{last}{ws.max_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    from openpyxl.worksheet.properties import PageSetupProperties
    if ws.sheet_properties.pageSetUpPr is None:
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    else:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"


MONEY_COLS = {"Revenue", "Net_Income", "Gross_Profit", "Operating_Cash_Flow", "Capex",
              "Total_Debt", "Book_Equity", "Cash_ST_Investments", "Total_Assets",
              "Total_Liabilities", "EBIT", "EBITDA", "Interest_Expense", "Market_Cap",
              "EV_Calc", "NetDebt_Calc", "FCF_Calc", "Free_Cash_Flow", "FCF_Reported",
              "TopLine_Alt", "Shares_Snapshot"}
PCT_COLS = {"FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc"}
DEC_COLS = {"Diluted_EPS", "PE_Calc", "PB_Calc", "EV_to_EBITDA_Calc"}

if __name__ == "__main__":
    main()
