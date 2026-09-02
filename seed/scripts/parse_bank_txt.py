import urllib.request, re, os
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

# 1) WFC PDF text
try:
    from pypdf import PdfReader
except Exception:
    try:
        from PyPDF2 import PdfReader
    except Exception as e:
        PdfReader = None
        print("no pypdf:", e)

if PdfReader:
    r = PdfReader(os.path.join(D, "wfc_4q25.pdf"))
    txt = "\n".join((p.extract_text() or "") for p in r.pages)
    open(os.path.join(D, "wfc_4q25.txt"), "w", encoding="utf-8").write(txt)
    print("WFC text chars:", len(txt))
    # grep key metrics
    for kw in ["CET1", "efficiency ratio", "net interest margin", "net charge-off", "nonaccrual", "tangible book value", "ROTCE", "common equity tier 1"]:
        for m in re.finditer(re.escape(kw), txt, re.I):
            s = max(0, m.start()-60); e = min(len(txt), m.end()+120)
            print(f"\n[{kw}] ...{txt[s:e]}...".replace("\n", " "))
            break
else:
    print("WFC text extraction skipped")

# 2) BAC press release HTML
def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()
html = get("https://newsroom.bankofamerica.com/content/newsroom/press-releases/2026/01/bank-of-america-reports-fourth-quarter-2025-financial-results.html").decode("utf-8", "ignore")
txt = re.sub(r"<[^>]+>", " ", html); txt = re.sub(r"&nbsp;", " ", txt); txt = re.sub(r"&amp;", "&", txt); txt = re.sub(r"\s+", " ", txt)
open(os.path.join(D, "bac_4q25_press.txt"), "w", encoding="utf-8").write(txt)
print("\nBAC press chars:", len(txt))
for kw in ["CET1", "efficiency ratio", "net interest margin", "net charge-off", "nonperforming", "tangible book value", "return on average tangible"]:
    for m in re.finditer(re.escape(kw), txt, re.I):
        s = max(0, m.start()-80); e = min(len(txt), m.end()+140)
        print(f"\n[{kw}] ...{txt[s:e]}...".replace("\n", " "))
        break
