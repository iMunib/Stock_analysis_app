import csv
from pathlib import Path
path = Path("../seed/raw/universe_master.csv")
print("exists:", path.is_file())
with open(path, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
print("rows:", len(rows))
r = next(x for x in rows if x["Ticker"] == "RY")
print("RY row Country_of_Listing:", repr(r["Country_of_Listing"]), "Primary_Ticker:", repr(r["Primary_Ticker"]), "Ticker:", repr(r["Ticker"]))
# replicate mapping loop
ca_keys = []
by_primary_tickers = set()
for row in rows:
    ticker = (row.get("Primary_Ticker") or row.get("Ticker") or "").strip()
    country = (row.get("Country_of_Listing") or "").strip().upper()
    if not ticker or country not in ("US", "CA"):
        continue
    cid = f"US:{ticker.upper()}:US" if country == "US" else f"CA:{ticker.upper()}:TSX"
    if country == "CA":
        ca_keys.append((cid, ticker, repr(row.get("Primary_Ticker")), repr(row.get("Ticker"))))
    by_primary_tickers.add(ticker.upper())
print("CA entries replicated:", len(ca_keys))
print("RY key in replicated:", ("CA:RY:TSX", "RY") in [(k, t) for k, t, _, _ in ca_keys])
print("RY ticker in replicated by_primary:", "RY" in by_primary_tickers)
print("first 3 CA replicated:", ca_keys[:3])
