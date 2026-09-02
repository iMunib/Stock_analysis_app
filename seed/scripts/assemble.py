# -*- coding: utf-8 -*-
"""Assemble: merge raw extraction into Time_Series (long) + Core_Financials (latest FY).
Idempotent upsert. Atomic workbook writes. Bulk Time_Series write.
Ticker disambiguation: 7 US/CA pairs share a bare ticker (e.g. T=AT&T vs Telus);
the CA company keeps its Yahoo ".TO" suffix so every universe company has a unique ticker.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
import urllib.request
import pandas as pd
import openpyxl

from common import RAW, XLSX, save_workbook_atomic, canonical_field


# ---------------------------------------------------------------------------
# Company_ID: permanent, collision-free key = Country:Primary_Ticker:Exchange
# ---------------------------------------------------------------------------
_US_EXCH = None


def _sec_exchange_map():
    """SEC ticker -> exchange (cached in raw/sec_ticker_exchange.json)."""
    global _US_EXCH
    if _US_EXCH is not None:
        return _US_EXCH
    fp = os.path.join(RAW, "sec_ticker_exchange.json")
    if os.path.exists(fp):
        try:
            _US_EXCH = json.load(open(fp, encoding="utf-8"))
            return _US_EXCH
        except Exception:
            _US_EXCH = {}
    try:
        req = urllib.request.Request(
            "https://www.sec.gov/files/company_tickers_exchange.json",
            headers={"User-Agent": "NA Financials Research admin@example.com"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        m = {}
        if isinstance(data, dict) and "data" in data and "fields" in data:
            fields = list(data["fields"])
            ti = fields.index("ticker") if "ticker" in fields else -1
            ei = fields.index("exchange") if "exchange" in fields else -1
            if ti >= 0 and ei >= 0:
                for row in data["data"]:
                    if len(row) > max(ti, ei):
                        m[str(row[ti])] = str(row[ei]).upper()
        else:
            for d in data.values():
                if isinstance(d, dict) and d.get("ticker") and d.get("exchange"):
                    m[str(d["ticker"])] = str(d["exchange"]).upper()
        _US_EXCH = m
        try:
            json.dump(m, open(fp, "w", encoding="utf-8"))
        except Exception:
            pass
    except Exception as e:
        print(f"[warn] SEC exchange map fetch failed: {e}")
        _US_EXCH = {}
    return _US_EXCH


def _normalize_exchange(ex):
    ex = (ex or "").strip().upper()
    if ex.startswith("NYSE AMERICAN"):
        return "NYSEAM"
    if ex.startswith("NYSE ARCA"):
        return "NYSEARCA"
    if ex.startswith("NASDAQ"):
        return "NASDAQ"
    if ex.startswith("NYSE"):
        return "NYSE"
    return ex


def resolve_company_id(country, bare_ticker, exchange_col):
    """Return the permanent Company_ID for a universe row."""
    country = str(country).strip()
    tk = str(bare_ticker).strip()
    if country == "CA":
        ex = "TSX"
    else:
        m = _sec_exchange_map()
        ex = m.get(tk) or m.get(tk.replace(".", "-")) or (exchange_col or "").strip() or "US"
        ex = _normalize_exchange(ex)
    return f"{country}:{tk}:{ex}"

CORE_COLS = ["Company_ID", "Ticker", "Company_Name", "Country_of_Listing", "GICS_Sector", "Primary_Currency",
             "Fiscal_Year_End", "Revenue", "Pretax_Income", "Tax_Provision", "Net_Income",
             "Diluted_EPS", "Operating_Cash_Flow", "Capex", "Free_Cash_Flow", "Cash_ST_Investments",
             "Total_Debt", "Total_Debt_Method", "Book_Equity", "Equity_Method", "Total_Assets", "Shares_Diluted",
             "Price", "Market_Cap", "Source_Primary", "Source_Aggregator", "Retrieval_Date", "Extraction_Status"]

TS_KEYS = ["Company_ID", "Fiscal_Year", "Field"]  # idempotency key for Time_Series

FIVE_FIELDS = ["Revenue", "Net_Income", "Book_Equity", "Total_Debt", "Operating_Cash_Flow"]


def load_universe():
    return pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False)


def load_raw():
    a = pd.read_csv(os.path.join(RAW, "edgar_annual.csv"), keep_default_na=False)
    t = pd.read_csv(os.path.join(RAW, "edgar_ttm.csv"), keep_default_na=False)
    y = pd.read_csv(os.path.join(RAW, "yfinance_ca.csv"), keep_default_na=False)
    ym = pd.read_csv(os.path.join(RAW, "yfinance_ca_meta.csv"), keep_default_na=False)
    um = pd.read_csv(os.path.join(RAW, "us_meta.csv"), keep_default_na=False)
    return a, t, y, ym, um


def _us_ticker_set(univ):
    return set(univ[univ["Country_of_Listing"].astype(str) == "US"]["Ticker"].astype(str))


def _unique_core_ticker(tk, yt, country, us_set):
    """Disambiguate a bare CA ticker that collides with a US ticker (Telus 'T' -> 'T.TO')."""
    tk, yt = str(tk), str(yt)
    if country == "CA" and tk in us_set:
        return yt
    return tk


def _ca_ticker_map(univ, us_set):
    """Map raw yfinance ticker (e.g. 'T.TO') -> unique ticker ('T.TO' if collision else 'T')."""
    m = {}
    for _, u in univ.iterrows():
        if str(u["Country_of_Listing"]) == "CA":
            yt = str(u["Yahoo_Ticker"]); tk = str(u["Ticker"])
            m[yt] = yt if tk in us_set else tk
    return m


def _extraction_status(rec):
    present = sum(1 for f in FIVE_FIELDS if rec.get(f) is not None)
    if present == 0:
        return "MISSING_SOURCE"
    if present == len(FIVE_FIELDS):
        return "COMPLETE"
    return "PARTIAL"


def _ts_company_id_map(univ):
    """Map every raw extraction ticker form (SEC for US, Yahoo for CA) -> (Company_ID, bare_ticker)."""
    m = {}
    for _, u in univ.iterrows():
        country = str(u["Country_of_Listing"])
        tk = str(u["Ticker"])
        yt = str(u["Yahoo_Ticker"])
        cid = resolve_company_id(country, tk, u.get("Exchange", ""))
        if country == "US":
            # edgar_annual stores under SEC ticker (bare or hyphen for dual-class)
            m[tk] = (cid, tk)
            m[tk.replace(".", "-")] = (cid, tk)
        else:
            # yfinance_ca stores under Yahoo ticker (dot, e.g. T.TO)
            m[yt] = (cid, tk)
            m[yt.replace(".", "-")] = (cid, tk)
    return m


def build_time_series():
    """Long-format rows matching Time_Series sheet, keyed by Company_ID."""
    a, t, y, ym, um = load_raw()
    univ = load_universe()
    cid_map = _ts_company_id_map(univ)
    rows = []
    for _, r in a.iterrows():
        try:
            fy = int(r["fy"])
        except (ValueError, TypeError):
            fy = r["fy"]
        tk = str(r["ticker"])
        hit = cid_map.get(tk) or cid_map.get(tk.replace(".", "-"))
        cid, bare = hit if hit else (f"US:{tk}:US", tk)
        rows.append({"Company_ID": cid, "Ticker": bare, "Fiscal_Year": fy, "Field": canonical_field(r["metric"]),
                     "Value": r["value"], "Unit": "native", "Currency": "USD",
                     "Source": "SEC EDGAR XBRL (10-K)", "Retrieval_Date": "2026-08-21", "Notes": None})
    for _, r in y.iterrows():
        raw = str(r["ticker"])
        hit = cid_map.get(raw) or cid_map.get(raw.replace(".", "-"))
        if hit:
            cid, bare = hit
        else:
            bare = raw.replace(".TO", "").replace("-TO", "")
            cid = f"CA:{bare}:TSX"
        p = str(r["period"])
        fy = int(p[:4]) if p[:4].isdigit() else p
        rows.append({"Company_ID": cid, "Ticker": bare, "Fiscal_Year": fy, "Field": canonical_field(r["metric"]),
                     "Value": r["value"], "Unit": "native", "Currency": "CAD",
                     "Source": "Yahoo Finance", "Retrieval_Date": "2026-08-21", "Notes": None})
    df = pd.DataFrame(rows, columns=["Company_ID", "Ticker", "Fiscal_Year", "Field", "Value", "Unit", "Currency", "Source", "Retrieval_Date", "Notes"])
    # Dedup by Company_ID + Fiscal_Year + Field + Currency (keep the most recent source).
    df = df.drop_duplicates(subset=["Company_ID", "Fiscal_Year", "Field", "Currency"], keep="last")
    return df


def build_core(tickers=None):
    """One row per universe company (latest FY), with disambiguated tickers + Extraction_Status."""
    a, t, y, ym, um = load_raw()
    univ = load_universe()
    if tickers is not None:
        univ = univ[univ["Ticker"].astype(str).isin([str(x) for x in tickers])]
    us_set = _us_ticker_set(univ)

    def latest_fy(df, ticker_col, metric_col, fy_col, val_col):
        out = {}
        for _, r in df.iterrows():
            key = (r[ticker_col], r[metric_col])
            if key not in out or str(r[fy_col]) > str(out[key][0]):
                out[key] = (r[fy_col], r[val_col])
        return out

    us_latest = latest_fy(a, "ticker", "metric", "fy", "value")
    ca_latest = latest_fy(y, "ticker", "metric", "period", "value")

    metric_col = {
        "Revenue": "Revenue", "NetIncome": "Net_Income", "PretaxIncome": "Pretax_Income",
        "TaxProvision": "Tax_Provision", "EPS_diluted": "Diluted_EPS", "OCF": "Operating_Cash_Flow",
        "Capex": "Capex", "Cash": "Cash_ST_Investments", "TotalDebt": "Total_Debt",
        "TotalAssets": "Total_Assets", "Equity": "Book_Equity", "SharesDiluted": "Shares_Diluted",
        # intermediate metrics used only for fallback derivation (not written to the sheet)
        "LongTermDebt": "_LTD", "ShortTermDebt": "_STD", "TotalEquity": "_TE",
    }

    records = []
    for _, u in univ.iterrows():
        tk = str(u["Ticker"]); yt = str(u["Yahoo_Ticker"]); country = str(u["Country_of_Listing"])
        cid = resolve_company_id(country, tk, u.get("Exchange", ""))
        src = us_latest if country == "US" else ca_latest
        key_tk = tk if country == "US" else yt
        rec = {"Company_ID": cid, "Ticker": tk, "Company_Name": u["Company_Name"],
               "Country_of_Listing": country, "GICS_Sector": u["GICS_Sector"],
               "Primary_Currency": u["Primary_Currency"],
               "Fiscal_Year_End": u.get("Fiscal_Year_End", ""), "Source_Aggregator": ""}
        for m, col in metric_col.items():
            v = src.get((key_tk, m))
            if v is None and "." in str(key_tk):
                v = src.get((str(key_tk).replace(".", "-"), m))
            rec[col] = v[1] if v else None
        # Total debt: prefer reported tag, else ShortTermDebt + LongTermDebt (Calculated).
        td_method = "Reported" if rec.get("Total_Debt") is not None else None
        if rec.get("Total_Debt") is None:
            ltd, std = rec.get("_LTD"), rec.get("_STD")
            if ltd is not None and std is not None:
                rec["Total_Debt"] = ltd + std
                td_method = "Calculated"
            elif ltd is not None:
                rec["Total_Debt"] = ltd
                td_method = "Calculated"
        rec["Total_Debt_Method"] = td_method or ""
        # Equity: StockholdersEquity first, else TotalEquity (Calculated).
        eq_method = "Reported" if rec.get("Book_Equity") is not None else None
        if rec.get("Book_Equity") is None and rec.get("_TE") is not None:
            rec["Book_Equity"] = rec["_TE"]
            eq_method = "Calculated"
        rec["Equity_Method"] = eq_method or ""
        for k in ("_LTD", "_STD", "_TE"):
            rec.pop(k, None)
        if rec.get("Operating_Cash_Flow") is not None and rec.get("Capex") is not None:
            rec["Free_Cash_Flow"] = rec["Operating_Cash_Flow"] - rec["Capex"]
        rec["Source_Primary"] = "EDGAR" if country == "US" else "IR/Yahoo"
        rec["Source_Aggregator"] = "" if country == "US" else "Yahoo Finance"
        rec["Retrieval_Date"] = "2026-08-21"
        rec["Extraction_Status"] = _extraction_status(rec)
        records.append(rec)
    return pd.DataFrame(records)


def _clean(v):
    return None if pd.isna(v) else v


def _upsert_core(wb, core_df):
    """Upsert Core_Financials into an already-loaded workbook (no save). Returns ticker count."""
    ws = wb["Core_Financials"]
    hdr = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    if "Extraction_Status" not in col:
        ws.cell(row=1, column=len(hdr) + 1, value="Extraction_Status")
        col["Extraction_Status"] = len(hdr) + 1
    existing = {}
    for r in range(2, ws.max_row + 1):
        tk = ws.cell(row=r, column=col["Ticker"]).value
        if tk:
            existing[tk] = r
    for _, row in core_df.iterrows():
        tk = row["Ticker"]
        r = existing.get(tk)
        if r is None:
            r = ws.max_row + 1
            existing[tk] = r
        for c in CORE_COLS:
            if c in col and c in row and pd.notna(row[c]):
                ws.cell(row=r, column=col[c], value=_clean(row[c]))
    return len(core_df)


def _upsert_time_series(wb, ts_df):
    """Bulk idempotent upsert into Time_Series (no save). Returns rows added."""
    ws = wb["Time_Series"]
    hdr = [c.value for c in ws[1]]
    existing = pd.read_excel(XLSX, sheet_name="Time_Series", keep_default_na=False)
    n_before = len(existing)
    merged = pd.concat([existing, ts_df], ignore_index=True)
    for k in TS_KEYS:
        merged["_k_" + k] = merged[k].astype(str)
    merged = merged.drop_duplicates(subset=["_k_" + k for k in TS_KEYS], keep="last")
    merged = merged.drop(columns=[c for c in merged.columns if c.startswith("_k_")])
    cols = [h for h in hdr if h in merged.columns]
    merged = merged[cols]
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    for row in merged.itertuples(index=False, name=None):
        ws.append([_clean(v) for v in row])
    return len(merged) - n_before


def render(tickers=None):
    """Full assemble in one atomic save: build core + time series, upsert both."""
    c = build_core(tickers=tickers)
    ts = build_time_series()
    wb = openpyxl.load_workbook(XLSX)
    n = _upsert_core(wb, c)
    added = _upsert_time_series(wb, ts)
    save_workbook_atomic(wb)
    return n, added


def upsert_core(core_df):
    wb = openpyxl.load_workbook(XLSX)
    n = _upsert_core(wb, core_df)
    save_workbook_atomic(wb)
    return n


def upsert_time_series(ts_df):
    wb = openpyxl.load_workbook(XLSX)
    added = _upsert_time_series(wb, ts_df)
    save_workbook_atomic(wb)
    return added


if __name__ == "__main__":
    n, added = render()
    print(f"Core_Financials upserted: {n} tickers | Time_Series +{added} rows")
