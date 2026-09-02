import json, urllib.request, re, os
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()

# NEE CIK 753308
sub = json.loads(get("https://data.sec.gov/submissions/CIK0000753308.json"))
recent = sub["filings"]["recent"]
tenk = []
for i in range(len(recent["form"])):
    if recent["form"][i] == "10-K":
        acc = recent["accessionNumber"][i].replace("-", "")
        tenk.append((recent["filingDate"][i], acc, recent["primaryDocument"][i]))
tenk.sort(reverse=True)
print("Latest 10-K:", tenk[0])
acc = tenk[0][1]; primary = tenk[0][2]
# filing index
idx = json.loads(get(f"https://www.sec.gov/Archives/edgar/data/753308/{acc}/index.json"))
print("Items in 10-K filing:")
for it in idx["directory"]["item"]:
    n = it["name"]
    if any(k in n.lower() for k in ["r.htm", "fin", "fs", "10-k", ".htm", "exhibit"]):
        print("  ", n)
