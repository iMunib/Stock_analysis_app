import json, urllib.request, time
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception:
            if a == tries - 1:
                return None
            time.sleep(1)
    return None

# RY Dec 3 2025 6-Ks -> list exhibits
for acc in ["000119312525305934", "000119312525305932", "000119312525305922"]:
    idx = json.loads(get(f"https://www.sec.gov/Archives/edgar/data/1000275/{acc}/index.json"))
    print(f"\n=== RY {acc} ===")
    for it in idx["directory"]["item"]:
        n = it["name"]
        if n.lower().endswith((".htm", ".html", ".pdf", ".xlsx")):
            print("  ", n)

# TD + BMO: find Dec 2025 6-K
for t, c in [("TD", 947263), ("BMO", 927971), ("BNS", 9631), ("CM", 1045520)]:
    sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{c:010d}.json"))
    rec = sub["filings"]["recent"]
    hits = []
    for i in range(len(rec["form"])):
        if rec["form"][i] in ("6-K", "40-F", "8-K") and "2025-12-01" <= rec["filingDate"][i] <= "2025-12-10":
            hits.append((rec["filingDate"][i], rec["accessionNumber"][i].replace("-", ""), rec["primaryDocument"][i], rec["form"][i]))
    print(f"\n=== {t} Dec 2025 filings ===")
    for h in hits:
        print("  ", h)
    time.sleep(0.3)
