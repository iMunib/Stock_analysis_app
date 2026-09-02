import json, urllib.request, time
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=50) as r:
                return r.read()
        except Exception:
            if a == tries - 1:
                return None
            time.sleep(1.5)
    return None

# BNS + CM earnings-release 6-K candidates (from earlier discovery)
cands = {
    "BNS": [("9631", "000127956925001256"), ("9631", "000119312525304859"), ("9631", "000119312525304627")],
    "CM": [("1045520", "000127956925001272"), ("1045520", "000119312525307494"), ("1045520", "000119312525307482")],
}
for bank, lst in cands.items():
    for c, acc in lst:
        idx = get(f"https://www.sec.gov/Archives/edgar/data/{c}/{acc}/index.json")
        if not idx:
            print(f"{bank} {acc}: index fetch FAIL")
            continue
        idx = json.loads(idx)
        items = idx["directory"]["item"]
        ex = [it["name"] for it in items if it["name"].lower().endswith((".htm", ".html", ".pdf")) and "index" not in it["name"].lower()]
        print(f"\n{bank} {acc} primary={idx['directory'].get('name','')} exhibits: {ex}")
        time.sleep(0.3)
