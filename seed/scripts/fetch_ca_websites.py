import json, os, time
import yfinance as yf

RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"
CA = [("RY","Royal Bank of Canada"),("TD","Toronto-Dominion Bank"),("BNS","Bank of Nova Scotia"),
      ("BMO","Bank of Montreal"),("CM","CIBC"),("NA","National Bank of Canada"),
      ("H","Hydro One"),("FTS","Fortis"),("EMA","Emera"),("ENB","Enbridge"),("TRP","TC Energy"),
      ("CNR","Canadian National Railway"),("CP","Canadian Pacific Kansas City"),
      ("BCE","BCE Inc."),("T","Telus"),("RCI-B","Rogers Communications")]

rows = []
for t, nm in CA:
    yt = t + ".TO"
    site = None
    try:
        info = yf.Ticker(yt).info
        site = info.get("website") or info.get("irWebsite")
    except Exception as e:
        print(yt, "ERR", e)
    rows.append({"ticker": t, "name": nm, "yahoo": yt, "website": site})
    print(t, "->", site)
    time.sleep(0.3)

pd = __import__("pandas")
pd.DataFrame(rows).to_csv(os.path.join(RAW, "ca_websites.csv"), index=False)
print("\nsaved", len(rows), "rows")
