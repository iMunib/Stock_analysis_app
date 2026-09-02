import json
import os
import re
import sys
import time
import traceback

import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
P1 = os.path.join(ROOT, "Sector_Financials_Phase1.xlsx")
LOGD = os.path.join(ROOT, "logs")
MJ = os.path.join(LOGD, "phase2_market.json")
ATTEMPTS = os.path.join(LOGD, "phase2_attempts.csv")
HOLE_FIELDS = ["Revenue", "Net_Income", "Total_Debt"]


def yahoo_sym(sym):
    return re.sub(r"\.([A-Z])\.TO$", r"-\1.TO", sym)


def log_attempt(row):
    df = pd.DataFrame([row])
    hdr = not os.path.exists(ATTEMPTS)
    df.to_csv(ATTEMPTS, mode="a", header=hdr, index=False, encoding="utf-8")


def main():
    import yfinance as yf
    data = json.load(open(MJ))
    market = data["market"]
    uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
    p1 = pd.read_excel(P1, sheet_name="01_All_Companies", keep_default_na=False)
    uix = uni.set_index("Company_ID")

    failed = [e["company_id"] for e in data.get("errors", [])]
    print("retrying", len(failed), "failed quotes with fixed symbols")
    still_bad = []
    for cid in failed:
        sym0 = str(uix.at[cid, "Primary_Ticker"]).strip()
        sym = yahoo_sym(sym0)
        try:
            info = yf.Ticker(sym).get_info()
            got = {k: info.get(k) for k in ["regularMarketPrice", "marketCap", "sharesOutstanding",
                                            "currency", "financialCurrency", "regularMarketTime"]}
            if got.get("regularMarketPrice") is not None:
                market[cid] = {"symbol": sym, **got}
                print(f"  FIXED {cid}: {sym} price={got['regularMarketPrice']}")
                log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                             "kind": "quote_retry", "cik": "", "symbol": sym, "status": "OK",
                             "fields_filled": "", "note": f"orig {sym0}"})
            else:
                still_bad.append({"company_id": cid, "symbol": sym0, "err": "no price"})
        except Exception as e:
            still_bad.append({"company_id": cid, "symbol": sym0, "err": repr(e)[:140]})
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                         "kind": "quote_retry", "cik": "", "symbol": sym, "status": "ERR",
                         "fields_filled": 0, "note": repr(e)[:120]})
        time.sleep(0.4)

    cur_counts = {}
    for v in market.values():
        c = str(v.get("currency") or "?")
        cur_counts[c] = cur_counts.get(c, 0) + 1
    print("market ok:", len(market), "| currencies:", cur_counts, "| still bad:", len(still_bad))
    for b in still_bad:
        print("   BAD:", b)
    data["market"] = market
    data["errors"] = still_bad
    data["snapshot_ok"] = len(market)
    data["snapshot_err"] = len(still_bad)
    data["retry_generated"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    print("\nCA statements retry with pacing:")
    ca_holes = p1[(p1["Company_ID"].str.startswith("CA:")) &
                  ((p1["Revenue"].astype(str).str.strip() == "") |
                   (p1["Net_Income"].astype(str).str.strip() == "") |
                   (p1["Total_Debt"].astype(str).str.strip() == ""))]
    ca_fills = {}
    for _, row in ca_holes.iterrows():
        cid = row["Company_ID"]
        sym = yahoo_sym(str(row["Primary_Ticker"]).strip())
        out = {}
        try:
            t = yf.Ticker(sym)
            inc = t.get_income_stmt()
            time.sleep(0.8)
            bal = t.get_balance_sheet()
            time.sleep(0.8)
            if inc is not None and not inc.empty:
                col = inc.columns[0]
                fy = str(col.year)
                for lbl, rm in [("Revenue", "TotalRevenue"), ("Net_Income", "NetIncome"),
                                ("Gross_Profit", "GrossProfit"), ("EBIT", "OperatingIncome"),
                                ("EBITDA", "EBITDA"), ("Interest_Expense", "InterestExpense")]:
                    if rm in inc.index and pd.notna(inc.loc[rm, col]):
                        out[lbl] = {"val": float(inc.loc[rm, col]), "fy": fy,
                                    "end": str(col.date()), "tag": rm}
            if bal is not None and not bal.empty:
                col = bal.columns[0]
                fy = str(col.year)
                for lbl, rm in [("Cash_ST_Investments", "CashAndCashEquivalents"),
                                ("Book_Equity", "StockholdersEquity"),
                                ("Total_Assets", "TotalAssets"),
                                ("Total_Liabilities", "TotalLiabilitiesNetMinorityInterest")]:
                    if rm in bal.index and pd.notna(bal.loc[rm, col]):
                        out[lbl] = {"val": float(bal.loc[rm, col]), "fy": fy,
                                    "end": str(col.date()), "tag": rm}
            try:
                td = yf.Ticker(sym).get_info().get("totalDebt")
            except Exception:
                td = None
            time.sleep(0.5)
            if td is not None:
                out["Total_Debt"] = {"val": float(td), "fy": "", "end": "", "tag": "quoteSummary totalDebt"}
            print(f"  {cid} ({sym}): {sorted(out.keys())}")
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                         "kind": "ca_statements_retry", "cik": "", "symbol": sym,
                         "status": "OK" if any(k in HOLE_FIELDS for k in out) else "NO_DATA",
                         "fields_filled": ",".join(k for k in out if k in HOLE_FIELDS), "note": ""})
        except Exception as e:
            print(f"  {cid} ({sym}): ERR {repr(e)[:100]}")
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                         "kind": "ca_statements_retry", "cik": "", "symbol": sym, "status": "ERR",
                         "fields_filled": 0, "note": repr(e)[:120]})
        ca_fills[cid] = {"symbol": sym, "fills": out}

    data["ca_statement_fills"] = ca_fills
    with open(MJ, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("\nupdated", MJ)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
