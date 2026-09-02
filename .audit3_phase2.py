import csv
with open("seed/raw/universe_master.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
print("rows:", len(rows))
us = [r for r in rows if r["Country_of_Listing"] == "US"]
ca = [r for r in rows if r["Country_of_Listing"] == "CA"]
cik_us = sum(1 for r in us if r["CIK_SEDAR"].strip().isdigit())
cik_ca = sum(1 for r in ca if r["CIK_SEDAR"].strip().isdigit())
print(f"US rows: {len(us)}, with numeric CIK: {cik_us}")
print(f"CA rows: {len(ca)}, with numeric CIK: {cik_ca}")
yt_dot = [r["Yahoo_Ticker"] for r in rows if "." in r["Yahoo_Ticker"]][:6]
print("yahoo tickers with dots:", yt_dot)
for t in ("AAPL", "MMM", "RY", "IIP.UN"):
    m = [r for r in rows if r["Ticker"] == t or r["Primary_Ticker"] == t]
    if m:
        r = m[0]
        print(t, "->", {k: r[k] for k in ("Ticker","Yahoo_Ticker","Country_of_Listing","Exchange","Primary_Currency","CIK_SEDAR")})
