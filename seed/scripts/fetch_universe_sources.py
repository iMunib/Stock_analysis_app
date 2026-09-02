import requests, io, os, json
import pandas as pd

RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
os.makedirs(RAW, exist_ok=True)

def get(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.text

def tables(url):
    return pd.read_html(io.StringIO(get(url)), keep_default_na=False)

# ---- S&P 500 ----
sp = tables("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
sp.to_csv(os.path.join(RAW, "sp500_wikipedia.csv"), index=False)
print("SP500:", sp.shape, "| sectors:", sorted(sp['GICS Sector'].dropna().unique()))
print("SP500 sub-industries distinct:", sp['GICS Sub-Industry'].nunique())

# ---- S&P/TSX Composite ----
tsx_tables = tables("https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index")
# find the constituent table (has Ticker + Company + Sector)
comp = None
for t in tsx_tables:
    if set(['Ticker','Company']).issubset(set(t.columns)):
        comp = t
        break
print("TSX Composite table:", comp.shape, "| cols:", list(comp.columns))
comp.to_csv(os.path.join(RAW, "tsx_composite_wikipedia.csv"), index=False)
print("TSX sectors:", sorted(comp['Sector [10]'].dropna().unique()))
print("TSX industries distinct:", comp['Industry [10]'].nunique())

# ---- S&P/TSX 60 ----
try:
    t60_tables = tables("https://en.wikipedia.org/wiki/S%26P/TSX_60")
    print("TSX60 page tables:", len(t60_tables))
    for i, t in enumerate(t60_tables):
        print(f"  table[{i}] shape={t.shape} cols={list(t.columns)[:8]}")
    # save all candidate tables
    for i, t in enumerate(t60_tables):
        t.to_csv(os.path.join(RAW, f"tsx60_wikipedia_t{i}.csv"), index=False)
except Exception as e:
    print("TSX60 ERROR:", type(e).__name__, e)
