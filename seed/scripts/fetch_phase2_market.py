import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
P1 = os.path.join(ROOT, "Sector_Financials_Phase1.xlsx")
LOGD = os.path.join(ROOT, "logs")
ATTEMPTS = os.path.join(LOGD, "phase2_attempts.csv")

HOLE_FIELDS = ["Revenue", "Net_Income", "Total_Debt"]


def log_attempt(row):
    df = pd.DataFrame([row])
    hdr = not os.path.exists(ATTEMPTS)
    df.to_csv(ATTEMPTS, mode="a", header=hdr, index=False, encoding="utf-8")


def fetch_info(sym):
    import yfinance as yf
    t = yf.Ticker(sym)
    info = t.get_info()
    keys = ["regularMarketPrice", "marketCap", "sharesOutstanding", "currency",
            "financialCurrency", "regularMarketTime"]
    return {k: info.get(k) for k in keys}


def fetch_ca_statements(sym):
    import yfinance as yf
    t = yf.Ticker(sym)
    out = {}
    inc = t.get_income_stmt()
    if inc is not None and not inc.empty:
        col = inc.columns[0]
        fy = str(col.year)
        for lbl, rowmap in [("Revenue", "Total Revenue"), ("Net_Income", "Net Income")]:
            if rowmap in inc.index:
                v = inc.loc[rowmap, col]
                if pd.notna(v):
                    out[lbl] = {"val": float(v), "fy": fy, "end": str(col.date())}
    bal = t.get_balance_sheet()
    if bal is not None and not bal.empty:
        col = bal.columns[0]
        fy = str(col.year)
        pairs = [("Total_Debt", "Total Debt"),
                 ("Cash_ST_Investments", "Cash And Equivalents"),
                 ("Book_Equity", "Stockholders Equity"),
                 ("Total_Assets", "Total Assets"),
                 ("Total_Liabilities", "Total Liabilities Net Minority Interest")]
        for lbl, rowmap in pairs:
            if rowmap in bal.index:
                v = bal.loc[rowmap, col]
                if pd.notna(v):
                    out[lbl] = {"val": float(v), "fy": fy, "end": str(col.date())}
    return out


def main():
    uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
    p1 = pd.read_excel(P1, sheet_name="01_All_Companies", keep_default_na=False)
    uix = uni.set_index("Company_ID")

    print("=== TASK C: one Yahoo snapshot for 720 symbols ===")
    symbols = {cid: str(uix.at[cid, "Primary_Ticker"]).strip() for cid in p1["Company_ID"]}

    market = {}
    errors = []
    t0 = time.time()

    def work(cs):
        cid, sym = cs
        try:
            return cid, sym, fetch_info(sym), None
        except Exception as e:
            return cid, sym, None, repr(e)[:140]

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(work, cs) for cs in symbols.items()]
        for i, fut in enumerate(as_completed(futs)):
            cid, sym, info, err = fut.result()
            if err:
                errors.append((cid, sym, err))
                log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                             "kind": "quote", "cik": "", "symbol": sym, "status": "ERR",
                             "fields_filled": 0, "note": err})
            elif info and info.get("regularMarketPrice") is not None:
                market[cid] = {"symbol": sym, **info}
            else:
                errors.append((cid, sym, "no price in response"))
                log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                             "kind": "quote", "cik": "", "symbol": sym, "status": "NO_PRICE",
                             "fields_filled": 0, "note": ""})
            if i % 100 == 0:
                print(f"  ...{i}/720 ok={len(market)} err={len(errors)} elapsed={time.time()-t0:.0f}s")

    print(f"snapshot done: ok={len(market)} err={len(errors)} in {time.time()-t0:.0f}s")
    cur_counts = {}
    for v in market.values():
        c = str(v.get("currency") or "?")
        cur_counts[c] = cur_counts.get(c, 0) + 1
    print("price currencies:", cur_counts)

    print("\n=== TASK B(Canada): Yahoo statements for CA allowlist names ===")
    ca_holes = p1[(p1["Company_ID"].str.startswith("CA:")) &
                  ((p1["Revenue"].astype(str).str.strip() == "") |
                   (p1["Net_Income"].astype(str).str.strip() == "") |
                   (p1["Total_Debt"].astype(str).str.strip() == ""))]
    ca_fills = {}
    for _, row in ca_holes.iterrows():
        cid = row["Company_ID"]
        sym = symbols[cid]
        try:
            got = fetch_ca_statements(sym)
        except Exception as e:
            got = {}
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                         "kind": "ca_statements", "cik": "", "symbol": sym, "status": "ERR",
                         "fields_filled": 0, "note": repr(e)[:140]})
        useful = {k: v for k, v in got.items() if k in HOLE_FIELDS}
        ca_fills[cid] = {"symbol": sym, "fills": got}
        log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                     "kind": "ca_statements", "cik": "", "symbol": sym,
                     "status": "OK" if useful else "NO_DATA",
                     "fields_filled": ",".join(useful.keys()), "note": ""})
        print(f"  {cid} ({sym}): {sorted(got.keys())}")

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "snapshot_ok": len(market), "snapshot_err": len(errors),
           "errors": [{"company_id": c, "symbol": s, "err": e} for c, s, e in errors],
           "market": market, "ca_statement_fills": ca_fills}
    path = os.path.join(LOGD, "phase2_market.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("\nwrote", path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
