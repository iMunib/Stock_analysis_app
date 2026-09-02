# -*- coding: utf-8 -*-
"""SEC EDGAR XBRL (companyfacts) extraction — refactored, config-driven.
Reads tag priority from maps/xbrl_tags.yaml, tickers from Universe sheet,
and writes raw/edgar_annual.csv + raw/edgar_ttm.csv (upsert by ticker+metric+fy/end).
"""
import json, os, time
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

from common import RAW, get, xbrl_tags, log_parse

CACHE = RAW  # companyfacts JSON cached as edgar_cik{cik}.json


_CIK_MAP = None


def cik_map(force=False):
    """CIK map cached at module level so per-ticker extraction doesn't refetch it."""
    global _CIK_MAP
    if _CIK_MAP is None or force:
        data = json.loads(get("https://www.sec.gov/files/company_tickers.json"))
        _CIK_MAP = {d["ticker"]: d["cik_str"] for d in data.values()}
    return _CIK_MAP


def facts(cik, force=False):
    fp = os.path.join(CACHE, f"edgar_cik{cik}.json")
    if os.path.exists(fp) and not force:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    data = json.loads(get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"))
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    time.sleep(0.2)
    return data


def _annual_vals(d, candidates, is_per_share=False):
    """Return ({fy: val}, tag_name) using the candidate tag with the most recent data.
    For each fy, the annual figure is the fact with the latest 'end' (FY year-end)."""
    keys = ["USD/shares", "USD"] if is_per_share else ["USD"]
    best_series, best_max, best_tag = {}, -1, None
    for tag in candidates:
        node = d.get(tag)
        if not node:
            continue
        for k in keys:
            if k not in node.get("units", {}):
                continue
            by_fy = {}
            for it in node["units"][k]:
                if it.get("form") == "10-K" and it.get("fp") == "FY" and it.get("fy") is not None:
                    by_fy.setdefault(it["fy"], []).append(it)
            series = {}
            for fy, lst in by_fy.items():
                b = max(lst, key=lambda x: (x.get("end") or "", x.get("filed") or ""))
                series[fy] = b.get("val")
            if series and max(series) > best_max:
                best_max = max(series)
                best_series = series
                best_tag = tag
    return best_series, best_tag


def _ttm_vals(d, candidates, is_per_share=False):
    keys = ["USD/shares", "USD"] if is_per_share else ["USD"]
    best_series, best_end = {}, ""
    for tag in candidates:
        node = d.get(tag)
        if not node:
            continue
        for k in keys:
            if k not in node.get("units", {}):
                continue
            best = {}
            for it in node["units"][k]:
                fp = it.get("fp"); end = it.get("end")
                if fp in ("Q1", "Q2", "Q3", "Q4") and end:
                    if end not in best or it.get("filed", "") > best[end]["filed"]:
                        best[end] = {"val": it.get("val"), "filed": it.get("filed", "")}
            ends = sorted(best)
            if len(ends) >= 4:
                last4 = ends[-4:]
                series = {"value": sum(best[e]["val"] for e in last4), "end": last4[-1], "n_quarters": 4}
                if last4[-1] > best_end:
                    best_end = last4[-1]
                    best_series = series
    return best_series


def extract(tickers, force=False):
    """tickers: list of US tickers. Returns (annual_df, ttm_df)."""
    tags = xbrl_tags()
    flow = tags["flow_metrics"]
    bs = tags["balance_sheet_metrics"]
    eps = tags["eps_metrics"]
    shares = tags["shares_metrics"]
    cmap = cik_map()
    annual_rows, ttm_rows = [], []
    for t in tickers:
        cik = cmap.get(t)
        if not cik:
            log_parse(t, "ALL", "CIK not found"); continue
        d = facts(cik, force=force)
        gaap = d.get("facts", {}).get("us-gaap", {})
        for m, cands in {**flow, **eps}.items():
            av, tag = _annual_vals(gaap, cands, is_per_share=(m == "EPS_diluted"))
            for fy in sorted(av):
                annual_rows.append({"ticker": t, "metric": m, "fy": fy, "value": av[fy], "type": "annual", "tag": tag})
            tv = _ttm_vals(gaap, cands, is_per_share=(m == "EPS_diluted"))
            if tv:
                ttm_rows.append({"ticker": t, "metric": m, "value": tv["value"], "end": tv["end"], "type": "ttm"})
        for m, cands in {**bs, **shares}.items():
            av, tag = _annual_vals(gaap, cands, is_per_share=False)
            for fy in sorted(av):
                annual_rows.append({"ticker": t, "metric": m, "fy": fy, "value": av[fy], "type": "annual", "tag": tag})
    adf = pd.DataFrame(annual_rows, columns=["ticker", "metric", "fy", "value", "type", "tag"])
    tdf = pd.DataFrame(ttm_rows, columns=["ticker", "metric", "value", "end", "type"])
    return adf, tdf


def upsert(adf, tdf):
    """Idempotent upsert into raw/edgar_annual.csv + edgar_ttm.csv on (ticker,metric,fy/end)."""
    for fname, df, keys in [("edgar_annual.csv", adf, ["ticker", "metric", "fy"]),
                            ("edgar_ttm.csv", tdf, ["ticker", "metric", "end"])]:
        fp = os.path.join(RAW, fname)
        if os.path.exists(fp) and len(df):
            old = pd.read_csv(fp, keep_default_na=False)
            df = pd.concat([old, df]).drop_duplicates(subset=keys, keep="last")
        if len(df):
            df.to_csv(fp, index=False)
    return len(adf), len(tdf)


if __name__ == "__main__":
    import sys
    tk = sys.argv[1:] or ["JPM", "BAC", "WFC", "MSFT", "AAPL"]
    a, t = extract(tk)
    n1, n2 = upsert(a, t)
    print(f"EDGAR annual rows (this run): {n1} | ttm rows: {n2}")
