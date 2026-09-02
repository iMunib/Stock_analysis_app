# -*- coding: utf-8 -*-
"""Batched universe fill: extract EDGAR (US) + yfinance (CA) across all 720 tickers
in GICS-ordered batches of 25, saving (git commit) after each batch. Data only, no ranking.
"""
import os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

from common import XLSX, LOGS
import extract_edgar, extract_ca_ir, assemble

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # na_financials_research/
REPO = os.path.dirname(ROOT)                                                 # workspace (git root)

GICS_ORDER = ["Financials", "Utilities", "Energy", "Industrials", "Communication Services",
              "Consumer Staples", "Consumer Discretionary", "Health Care",
              "Information Technology", "Materials", "Real Estate"]
BATCH = 25
LOG = os.path.join(LOGS, "batch_fill.log")


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def commit(msg):
    subprocess.run(["git", "add", "-A", "na_financials_research"], cwd=REPO, check=False)
    r = subprocess.run(["git", "commit", "-m", msg, "-q"], cwd=REPO, check=False,
                       capture_output=True, text=True)
    return r.returncode


def main():
    univ = pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False)
    univ["_g"] = univ["GICS_Sector"].map({g: i for i, g in enumerate(GICS_ORDER)}).fillna(99)
    univ = univ.sort_values(["_g", "Country_of_Listing"]).reset_index(drop=True)
    us = univ[univ["Country_of_Listing"] == "US"]["Ticker"].tolist()
    ca = univ[univ["Country_of_Listing"] == "CA"]["Yahoo_Ticker"].tolist()
    log(f"Universe: US={len(us)} CA={len(ca)} total={len(us)+len(ca)}")

    for i in range(0, len(us), BATCH):
        chunk = us[i:i + BATCH]
        b = i // BATCH + 1
        log(f"US batch {b}: {len(chunk)} tickers {chunk[0]}..{chunk[-1]}")
        try:
            adf, tdf = extract_edgar.extract(chunk)
            extract_edgar.upsert(adf, tdf)
            log(f"  -> EDGAR annual={len(adf)} ttm={len(tdf)}")
        except Exception as e:
            log(f"  -> ERROR {e}")
        commit(f"core fill: US batch {b} ({len(chunk)} tickers)")

    for i in range(0, len(ca), BATCH):
        chunk = ca[i:i + BATCH]
        b = i // BATCH + 1
        log(f"CA batch {b}: {len(chunk)} tickers {chunk[0]}..{chunk[-1]}")
        try:
            df, mdf = extract_ca_ir.extract(chunk)
            extract_ca_ir.upsert(df, mdf)
            log(f"  -> CA yfinance rows={len(df)}")
        except Exception as e:
            log(f"  -> ERROR {e}")
        commit(f"core fill: CA batch {b} ({len(chunk)} tickers)")

    log("Assembling Core_Financials + Time_Series for full universe...")
    c = assemble.build_core()
    n = assemble.upsert_core(c)
    ts = assemble.build_time_series()
    added = assemble.upsert_time_series(ts)
    commit("core fill: assemble full universe")
    log(f"DONE. Core_Financials={n} tickers | Time_Series +{added} rows")


if __name__ == "__main__":
    main()
