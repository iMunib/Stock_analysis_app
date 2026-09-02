import json, urllib.request, os, time
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}

def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception as e:
            if a == tries - 1:
                return None
            time.sleep(1)
    return None

# ticker -> CIK (verify via company_tickers)
cm = json.loads(get("https://www.sec.gov/files/company_tickers.json"))
cik = {d["ticker"]: d["cik_str"] for d in cm.values()}
for t in ["RY", "TD", "BMO", "BNS", "CM"]:
    print(f"{t} -> CIK {cik.get(t)}")

banks = {"RY": cik.get("RY"), "TD": cik.get("TD"), "BMO": cik.get("BMO"),
         "BNS": cik.get("BNS"), "CM": cik.get("CM")}
for t, c in banks.items():
    if not c:
        continue
    sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{c:010d}.json"))
    rec = sub["filings"]["recent"]
    print(f"\n=== {t} (CIK {c}) recent 6-K ===")
    for i in range(len(rec["form"])):
        if rec["form"][i] == "6-K" and rec["filingDate"][i] >= "2025-12-01":
            acc = rec["accessionNumber"][i].replace("-", "")
            print(f"  {rec['filingDate'][i]}  {acc}  {rec['primaryDocument'][i]}")
    time.sleep(0.3)
