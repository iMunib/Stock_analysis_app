# -*- coding: utf-8 -*-
"""FINAL LOCAL DATA REPAIR — four items:
1. CA:EFX:TSX -> Enerflex (name + source verification).
2. Rogers Time_Series dedup by Company_ID + Fiscal_Year + Field + Currency.
3. Retry TECK.B / IIP.UN / BRK.B (share-class symbols).
4. Rebuild + validate + save.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/scripts")
sys.path.insert(0, "scripts")
import pandas as pd
import openpyxl

from common import XLSX, RAW, save_workbook_atomic
import assemble, extract_edgar, extract_ca_ir

RETRIEVAL = "2026-08-21"


def clean(v):
    return None if pd.isna(v) else v


def isblank(v):
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    return False


# ---------------------------------------------------------------------------
# 0. Re-fetch SEC exchange map (parser fixed)
# ---------------------------------------------------------------------------
cache = os.path.join(RAW, "sec_ticker_exchange.json")
if os.path.exists(cache):
    try:
        if not json.load(open(cache, encoding="utf-8")):
            os.remove(cache)
    except Exception:
        os.remove(cache)
assemble._US_EXCH = None
exm = assemble._sec_exchange_map()
print(f"[0] SEC exchange map: {len(exm)} entries")
print(f"    EFX->{exm.get('EFX')} | T->{exm.get('T')} | KEY->{exm.get('KEY')} | BRK-B->{exm.get('BRK-B')} | MSFT->{exm.get('MSFT')}")

# ---------------------------------------------------------------------------
# 1. Fix CA:EFX:TSX Company_Name -> Enerflex Ltd. in Universe
# ---------------------------------------------------------------------------
wb = openpyxl.load_workbook(XLSX)
ws_u = wb["Universe"]
uh = [c.value for c in ws_u[1]]
i_tk = uh.index("Ticker") + 1
i_nm = uh.index("Company_Name") + 1
i_co = uh.index("Country_of_Listing") + 1
fixed = 0
for r in range(2, ws_u.max_row + 1):
    if str(ws_u.cell(row=r, column=i_tk).value) == "EFX" and str(ws_u.cell(row=r, column=i_co).value) == "CA":
        ws_u.cell(row=r, column=i_nm).value = "Enerflex Ltd."
        fixed += 1
print(f"[1] CA:EFX Universe name fixed to Enerflex Ltd.: {fixed} row(s)")
save_workbook_atomic(wb)
wb = None

# ---------------------------------------------------------------------------
# 2. Retry share-class tickers (max 3 attempts each)
# ---------------------------------------------------------------------------
def retry_ca(syms):
    got = False
    for attempt in range(3):
        try:
            df, mdf = extract_ca_ir.extract(syms)
            if len(df):
                extract_ca_ir.upsert(df, mdf)
                got = True
        except Exception as e:
            print(f"    CA retry {attempt+1}: {type(e).__name__}: {e}")
        time.sleep(1)
    return got

print("[2] retrying share-class tickers...")
retry_ca(["TECK.B.TO", "IIP-UN.TO"])
for attempt in range(3):
    try:
        adf, tdf = extract_edgar.extract(["BRK-B"], force=True)
        if len(adf):
            extract_edgar.upsert(adf, tdf)
    except Exception as e:
        print(f"    EDGAR BRK-B retry {attempt+1}: {type(e).__name__}: {e}")
    time.sleep(1)

# ---------------------------------------------------------------------------
# 3. Rebuild
# ---------------------------------------------------------------------------
core = assemble.build_core()
ts = assemble.build_time_series()
print(f"[3] core={len(core)} unique_cid={core['Company_ID'].nunique()} | ts={len(ts)}")

# ---------------------------------------------------------------------------
# 4. Rogers duplicate conflict detection (raw RCI.B.TO vs RCI-B.TO)
# ---------------------------------------------------------------------------
y = pd.read_csv(os.path.join(RAW, "yfinance_ca.csv"), keep_default_na=False)
rog = y[y["ticker"].isin(["RCI.B.TO", "RCI-B.TO"])].copy()
rog_conflict = 0
if len(rog):
    rog["period"] = rog["period"].str[:4]
    piv = rog.pivot_table(index=["metric", "period"], columns="ticker", values="value", aggfunc="last")
    piv = piv.dropna()
    for (m, p), row in piv.iterrows():
        a, b = row.get("RCI.B.TO"), row.get("RCI-B.TO")
        if a is not None and b is not None and abs(float(a) - float(b)) > 1e-6:
            rog_conflict += 1
print(f"[4] Rogers raw rows={len(rog)}; conflicting (dot vs hyphen) value pairs={rog_conflict}")

# ---------------------------------------------------------------------------
# 5. Full-replace Core_Financials + Time_Series + Data_Quality
# ---------------------------------------------------------------------------
existing = pd.read_excel(XLSX, sheet_name="Core_Financials", keep_default_na=False)
existing_cols = list(existing.columns)
new_cols = [c for c in assemble.CORE_COLS if c not in existing_cols]
derived_cols = [c for c in existing_cols if c not in assemble.CORE_COLS]

name_map = {}
for _, r in existing.iterrows():
    cn = str(r["Company_Name"])
    key = "Rogers Communications Inc." if cn == "Rogers Communications" else cn
    cur = name_map.setdefault(key, {})
    cand = {c: r[c] for c in derived_cols if pd.notna(r[c])}
    if len(cand) > len(cur):
        name_map[key] = cand

wb = openpyxl.load_workbook(XLSX)

# Core
ws = wb["Core_Financials"]
final_hdr = ["Company_ID"] + existing_cols + new_cols
for i, h in enumerate(final_hdr, start=1):
    ws.cell(row=1, column=i, value=h)
if ws.max_row > 1:
    ws.delete_rows(2, ws.max_row - 1)
for _, row in core.iterrows():
    extra = name_map.get(str(row["Company_Name"]), {})
    vals = []
    for h in final_hdr:
        if h == "Company_ID":
            vals.append(row["Company_ID"])
        elif h in assemble.CORE_COLS and h in row.index:
            vals.append(clean(row[h]))
        elif h in extra:
            vals.append(clean(extra[h]))
        else:
            vals.append(None)
    ws.append(vals)

# Time_Series
ts_ws = wb["Time_Series"]
ts_cols = ["Company_ID", "Ticker", "Fiscal_Year", "Field", "Value", "Unit", "Currency",
           "Source", "Retrieval_Date", "Notes"]
for i, h in enumerate(ts_cols, start=1):
    ts_ws.cell(row=1, column=i, value=h)
if ts_ws.max_row > 1:
    ts_ws.delete_rows(2, ts_ws.max_row - 1)
for row in ts.itertuples(index=False, name=None):
    ts_ws.append([clean(v) for v in row])

# Source_Audit: ensure Company_ID column
sa_ws = wb["Source_Audit"]
tk2cid = {}
for _, u in assemble.load_universe().iterrows():
    cid = assemble.resolve_company_id(u["Country_of_Listing"], u["Ticker"], u.get("Exchange", ""))
    tk2cid[str(u["Ticker"])] = cid
    tk2cid[str(u["Yahoo_Ticker"])] = cid
sa_hdr = [c.value for c in sa_ws[1]]
if "Company_ID" not in sa_hdr:
    sa_ws.insert_cols(2)
    sa_ws.cell(row=1, column=2, value="Company_ID")
    for r in range(2, sa_ws.max_row + 1):
        tk = sa_ws.cell(row=r, column=1).value
        sa_ws.cell(row=r, column=2, value=tk2cid.get(str(tk), ""))

# Data_Quality
dq_ws = wb["Data_Quality"]
dq_hdr = ["Company_ID", "Ticker", "Field", "Issue", "Source_Attempted", "Retrieval_Date", "Resolution", "Notes"]
for i, h in enumerate(dq_hdr, start=1):
    dq_ws.cell(row=1, column=i, value=h)
if dq_ws.max_row > 1:
    dq_ws.delete_rows(2, dq_ws.max_row - 1)

FIVE = ["Revenue", "Net_Income", "Book_Equity", "Total_Debt", "Operating_Cash_Flow"]
dq_rows = 0
for _, row in core.iterrows():
    st = row["Extraction_Status"]
    if st == "COMPLETE":
        continue
    if st == "MISSING_SOURCE":
        dq_ws.append([row["Company_ID"], row["Ticker"], "ALL", "MISSING_SOURCE",
                      "EDGAR/Yahoo", RETRIEVAL,
                      "No source financials available (share-class symbol failed or no filing yet)", ""])
        dq_rows += 1
    else:
        for f in FIVE:
            if isblank(row.get(f)):
                dq_ws.append([row["Company_ID"], row["Ticker"], f, "MISSING_FIELD",
                              "EDGAR/Yahoo", RETRIEVAL,
                              "Field tag not present in source; kept N/A", ""])
                dq_rows += 1
# Rogers conflict note
if rog_conflict:
    dq_ws.append(["CA:RCI.B:TSX", "RCI.B", "ALL", "DUPLICATE_CONFLICT",
                  "Yahoo", RETRIEVAL,
                  f"{rog_conflict} dot-vs-hyphen value conflicts resolved; latest source kept", ""])
    dq_rows += 1

# ---------------------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------------------
save_workbook_atomic(wb)
print(f"[6] saved. Data_Quality rows={dq_rows}")

# ---------------------------------------------------------------------------
# 7. Validation
# ---------------------------------------------------------------------------
u = pd.read_excel(XLSX, sheet_name="Universe", keep_default_na=False)
c = pd.read_excel(XLSX, sheet_name="Core_Financials", keep_default_na=False)
t = pd.read_excel(XLSX, sheet_name="Time_Series", keep_default_na=False)

t["_k"] = t["Company_ID"].astype(str) + "|" + t["Fiscal_Year"].astype(str) + "|" + t["Field"].astype(str) + "|" + t["Currency"].astype(str)
dup_ts = int(t.duplicated(subset=["_k"]).sum())
dup_core = int(c.duplicated(subset=["Company_ID"]).sum())
full = c[~c[FIVE].apply(lambda r: any(isblank(x) for x in r), axis=1)]

efx_ca = c[c["Company_ID"] == "CA:EFX:TSX"]
efx_us = c[c["Company_ID"] == "US:EFX:NYSE"]
efx_ca_name = efx_ca["Company_Name"].iloc[0] if len(efx_ca) else "N/A"
efx_ca_rev = efx_ca["Revenue"].iloc[0] if len(efx_ca) else "N/A"
efx_us_rev = efx_us["Revenue"].iloc[0] if len(efx_us) else "N/A"

rog_ts = t[t["Company_ID"] == "CA:RCI.B:TSX"]
rog_dup = int(rog_ts.duplicated(subset=["Company_ID", "Fiscal_Year", "Field", "Currency"]).sum())

st = c["Extraction_Status"].value_counts().to_dict()
partial = int(st.get("PARTIAL", 0)); missing = int(st.get("MISSING_SOURCE", 0))
na_ok = len(c[c["Ticker"] == "NA"]) > 0
h_ok = len(c[c["Ticker"] == "H"]) > 0

print("\n========== FINAL VALIDATION ==========")
print(f"Universe rows: {len(u)}")
print(f"Core_Financials rows: {len(c)}")
print(f"Unique Company_ID count: {c['Company_ID'].nunique()}")
print(f"Time_Series rows: {len(t)}")
print(f"Duplicate Core_Financials Company_ID count: {dup_core}")
print(f"Duplicate Time_Series key count: {dup_ts}")
print(f"Full core coverage count: {len(full)}")
print(f"Partial count: {partial}")
print(f"Missing-source count: {missing}")
print(f"CA:EFX:TSX Company_Name: {efx_ca_name} | Revenue={efx_ca_rev}")
print(f"  US:EFX:NYSE Revenue={efx_us_rev} (Equifax)")
print(f"Rogers duplicate count (CA:RCI.B:TSX): {rog_dup}")
for tk, cid, name in [("TECK.B", "CA:TECK.B:TSX", None), ("IIP.UN", "CA:IIP.UN:TSX", None), ("BRK.B", "US:BRK.B:NYSE", None)]:
    sub = c[c["Company_ID"] == cid]
    print(f"{tk} status: {sub['Extraction_Status'].iloc[0] if len(sub) else 'NOT FOUND'}")
print(f"NA ticker intact: {na_ok}")
print(f"Hydro One present: {h_ok}")
print(f"Ranking computed: NO")
print(f"File saved: NA_Company_Financials.xlsx")
