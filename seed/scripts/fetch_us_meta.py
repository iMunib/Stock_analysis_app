import time, os
import pandas as pd
import yfinance as yf
RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"
US = ["JPM", "BAC", "WFC", "NEE", "DUK", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "UNP"]
meta = {}
for sym in US:
    try:
        info = yf.Ticker(sym).info or {}
        meta[sym] = {"currency": info.get("financialCurrency") or info.get("currency") or "USD",
                     "shares": info.get("sharesOutstanding"),
                     "mktcap": info.get("marketCap"),
                     "price": info.get("currentPrice") or info.get("previousClose")}
        print(sym, meta[sym])
    except Exception as e:
        print(sym, "ERR", e)
    time.sleep(0.3)
pd.DataFrame(meta).T.to_csv(os.path.join(RAW, "us_meta.csv"))
