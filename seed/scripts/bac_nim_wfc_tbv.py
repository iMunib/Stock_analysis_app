import urllib.request, re, os
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()

# 1) BAC net interest yield (NIM-equivalent) from ex993 financial data
t = open(os.path.join(D, "bac_ex993.txt"), encoding="utf-8").read()
print("=== BAC net interest yield/margin search ===")
for kw in ["net interest yield", "net interest margin", "interest yield", "NII", "net interest income"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
    if hits:
        i = hits[0]
        print(f"[{kw}] x{len(hits)}: ...{t[max(0,i-100):i+240]}...".replace("\n", " "))
    else:
        print(f"[{kw}] NOT FOUND")

# 2) WFC earnings supplement (for TBVPS)
url = "https://www.wellsfargo.com/assets/pdf/about/investor-relations/earnings/fourth-quarter-2025-earnings-supplement.pdf"
try:
    data = get(url)
    print(f"\nWFC supplement size: {len(data)//1024} KB")
    if len(data) < 8*1024*1024:
        open(os.path.join(D, "wfc_4q25_supp.pdf"), "wb").write(data)
        from pypdf import PdfReader
        r = PdfReader(os.path.join(D, "wfc_4q25_supp.pdf"))
        st = "\n".join((p.extract_text() or "") for p in r.pages)
        open(os.path.join(D, "wfc_4q25_supp.txt"), "w", encoding="utf-8").write(st)
        print("WFC supp text chars:", len(st))
        for kw in ["tangible book value per", "book value per", "common equity tier 1", "CET1", "leverage ratio", "average loans", "average deposits"]:
            hits = [m.start() for m in re.finditer(re.escape(kw), st, re.I)]
            if hits:
                i = hits[0]
                print(f"[{kw}] x{len(hits)}: ...{st[max(0,i-100):i+200]}...".replace("\n", " "))
            else:
                print(f"[{kw}] NOT FOUND")
    else:
        print("supplement > 8MB, skipped")
except Exception as e:
    print("WFC supplement ERR:", e)
