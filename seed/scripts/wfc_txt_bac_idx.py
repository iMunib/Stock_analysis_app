import urllib.request, re, os, json
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()

# 1) WFC PDF text (small, 374KB)
from pypdf import PdfReader
r = PdfReader(os.path.join(D, "wfc_4q25.pdf"))
txt = "\n".join((p.extract_text() or "") for p in r.pages)
open(os.path.join(D, "wfc_4q25.txt"), "w", encoding="utf-8").write(txt)
print("WFC text chars:", len(txt))
for kw in ["CET1", "common equity tier 1", "net interest margin", "efficiency ratio", "net charge-off", "nonaccrual", "nonperforming", "tangible book value", "return on average tangible", "ROTCE"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    if hits:
        i = hits[0]
        print(f"\n[{kw}] x{len(hits)}: ...{txt[max(0,i-100):i+200]}...".replace("\n", " "))
    else:
        print(f"\n[{kw}] NOT FOUND")

# 2) BAC 8-K filing index (find small exhibits)
idx = json.loads(get("https://www.sec.gov/Archives/edgar/data/70858/000007085826000020/index.json"))
print("\n=== BAC 8-K items ===")
for it in idx["directory"]["item"]:
    print("  ", it["name"])
