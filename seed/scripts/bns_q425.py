import urllib.request, re, time, os
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
HEADERS = {"User-Agent": "Mozilla/5.0 (research) contact@openclaw.local"}
def get(u):
    for a in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=60).read()
        except Exception as e:
            if a == 2:
                print("  FAIL", u.split("/")[-1], str(e)[:60]); return None
            time.sleep(1.5)
base = "https://www.scotiabank.com/content/dam/scotiabank/corporate/quarterly-reports/2025/q4/"
for fn in ["Q425_Quarterly_Press_Release-EN.pdf", "Q425_Supplementary_Financial_Information-EN.pdf"]:
    d = get(base + fn)
    if not d or d[:4] != b"%PDF":
        continue
    kb = len(d)//1024
    print(f"{fn}: {kb} KB")
    if kb > 8*1024:
        print("  -> TOO BIG, skip"); continue
    open(os.path.join(D, "bns_"+fn), "wb").write(d)
    txt = "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, "bns_"+fn)).pages)
    txt = re.sub(r"\s+", " ", txt)
    print("  chars:", len(txt))
    for kw in ["CET1", "Common Equity Tier 1", "net interest margin", "efficiency ratio",
               "gross impaired", "net write-off", "return on equity", "total capital ratio"]:
        hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
        if hits:
            i = hits[0]
            print(f"  [{kw}] x{len(hits)}: ...{txt[max(0,i-60):i+180]}...".replace(chr(10), " "))
        else:
            print(f"  [{kw}] NOT FOUND")
