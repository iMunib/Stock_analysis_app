import json, urllib.request, re, os, time
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if a == tries - 1:
                return None
            time.sleep(1)
    return None

# ---- RY: download 3 exhibits ----
ry_files = [
    ("https://www.sec.gov/Archives/edgar/data/1000275/000119312525305934/d73208dex991.pdf", "ry_supp.pdf"),
    ("https://www.sec.gov/Archives/edgar/data/1000275/000119312525305922/d95169dex991.htm", "ry_press.htm"),
    ("https://www.sec.gov/Archives/edgar/data/1000275/000119312525305932/d46032dex991.htm", "ry_mda.htm"),
]
for url, fn in ry_files:
    d = get(url)
    if d:
        open(os.path.join(D, fn), "wb").write(d)
        print(f"OK  {fn}  {len(d)//1024} KB  pdf={d[:4]==b'%PDF'}")
    else:
        print(f"FAIL {fn}")

# ---- TD + BMO 6-K index exhibits ----
for t, c, acc in [("TD", 947263, "000156276225000287"), ("BMO", 927971, "000119312525308014")]:
    idx = json.loads(get(f"https://www.sec.gov/Archives/edgar/data/{c}/{acc}/index.json"))
    print(f"\n=== {t} {acc} exhibits ===")
    for it in idx["directory"]["item"]:
        n = it["name"]
        if n.lower().endswith((".htm", ".html", ".pdf")):
            print("  ", n)
