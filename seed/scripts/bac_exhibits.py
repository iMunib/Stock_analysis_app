import urllib.request, re, os
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()

# 1) WFC: search TBVPS / book value / leverage / loan-deposit
txt = open(os.path.join(D, "wfc_4q25.txt"), encoding="utf-8").read()
print("=== WFC extra searches ===")
for kw in ["book value", "leverage", "total assets", "average loans", "average deposits", "loans", "deposits"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    if hits:
        i = hits[0]
        print(f"\n[{kw}] x{len(hits)}: ...{txt[max(0,i-120):i+220]}...".replace("\n", " "))

# 2) BAC exhibits 99.1 (press release) and 99.2 (supplement)
for exhibit, fn in [("bac12312025ex991.htm", "bac_ex991.htm"), ("bac12312025ex992.htm", "bac_ex992.htm"), ("bac-12312025ex993.htm", "bac_ex993.htm")]:
    url = f"https://www.sec.gov/Archives/edgar/data/70858/000007085826000020/{exhibit}"
    try:
        html = get(url).decode("utf-8", "ignore")
        t = re.sub(r"<[^>]+>", " ", html); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t)
        t = re.sub(r"&#8212;", "--", t); t = re.sub(r"\s+", " ", t)
        open(os.path.join(D, fn.replace(".htm", ".txt")), "w", encoding="utf-8").write(t)
        print(f"\n=== BAC {fn}: {len(t)} chars ===")
        for kw in ["CET1", "common equity tier 1", "net interest margin", "efficiency ratio", "net charge-off", "nonperforming", "tangible book value", "return on average tangible", "ROTCE", "leverage ratio"]:
            hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
            if hits:
                i = hits[0]
                print(f"[{kw}] x{len(hits)}: ...{t[max(0,i-100):i+200]}...".replace("\n", " "))
            else:
                print(f"[{kw}] NOT FOUND")
    except Exception as e:
        print(f"\n=== BAC {fn}: ERR {e} ===")
