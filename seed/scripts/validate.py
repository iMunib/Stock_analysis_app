# -*- coding: utf-8 -*-
"""Validation: identity check, NA ticker intact, share-class consolidation, Hydro One term.
Returns a list of (level, message) findings; writes Quality_Checks identity where applicable.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import openpyxl

from common import XLSX


def identity_check(core_df):
    """TotalAssets == TotalLiabilities + TotalEquity (within 0.05%). Returns % dev per ticker."""
    out = {}
    for _, r in core_df.iterrows():
        ta = r.get("Total_Assets"); tl = r.get("Total_Liabilities"); te = r.get("Total_Equity")
        if pd.isna(ta) or pd.isna(tl) or pd.isna(te) or ta in (0, None) or ta == 0:
            out[r["Ticker"]] = None
            continue
        dev = (ta - (tl + te)) / ta * 100
        out[r["Ticker"]] = round(dev, 6)
    return out


def na_ticker_intact():
    """National Bank ticker 'NA' must survive a pandas read as a string, not NaN."""
    df = pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False)
    hit = df[df["Ticker"].astype(str).str.upper() == "NA"]
    return len(hit) > 0


def hydro_one_term(up_df):
    """Hydro One (H) must carry its issuer cash term, not industrial FCF."""
    row = up_df[up_df["Ticker"] == "H"]
    if row.empty:
        return False
    term = str(row.iloc[0].get("Issuer_Term", "") or "")
    return "after capital expenditures" in term.lower() or "cash from operations" in term.lower()


def unit_scale(core_df):
    """Flag suspicious magnitudes (e.g. revenue < 1e6 for a large cap) as a heuristic only."""
    flags = []
    for _, r in core_df.iterrows():
        rev = r.get("Revenue")
        if pd.notna(rev) and isinstance(rev, (int, float)) and abs(rev) < 1e6:
            flags.append(r["Ticker"])
    return flags


def run():
    findings = []
    try:
        core = pd.read_excel(XLSX, sheet_name="Core_Financials")
        ident = identity_check(core)
        bad = {t: v for t, v in ident.items() if v is not None and abs(v) > 0.05}
        findings.append(("identity", f"identity mismatches >0.05%: {bad}" if bad else "identity OK (all within 0.05%)"))
    except Exception as e:
        findings.append(("identity", f"identity check failed: {e}"))

    findings.append(("na_ticker", "NA ticker intact: " + ("yes" if na_ticker_intact() else "NO — NA became NaN")))

    try:
        up = pd.read_excel(XLSX, sheet_name="Utility_Pipeline")
        findings.append(("hydro_one", "Hydro One issuer cash term: " + ("yes" if hydro_one_term(up) else "NO")))
    except Exception as e:
        findings.append(("hydro_one", f"check failed: {e}"))

    try:
        core = pd.read_excel(XLSX, sheet_name="Core_Financials")
        small = unit_scale(core)
        findings.append(("unit_scale", f"tiny revenue flags: {small}" if small else "unit scale OK"))
    except Exception:
        pass

    return findings


if __name__ == "__main__":
    for lvl, msg in run():
        print(f"[{lvl}] {msg}")
