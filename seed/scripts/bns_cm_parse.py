import json, urllib.request, re, os, time
from pypdf import PdfReader
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
            time.sleep(1.5)
    return None

KWS = ["CET1", "common equity tier 1", "net interest margin", "efficiency ratio", "gross impaired",
       "impaired loans", "net write-off", "provision for credit losses", "tangible book value",
       "return on tangible", "return on equity", "total capital ratio", "leverage ratio"]

def dl_and_grep(bank, c, acc, ex, fn):
    url = f"https://www.sec.gov/Archives/edgar/data/{c}/{acc}/{ex}"
    d = get(url)
    if not d:
        print(f"{bank} {ex}: FAIL")
        return
    ispdf = d[:4] == b"%PDF"
    if ispdf:
        open(os.path.join(D, fn + ".pdf"), "wb").write(d)
        t = "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, fn + ".pdf")).pages)
    else:
        open(os.path.join(D, fn + ".txt"), "wb").write(d)
        t = d.decode("utf-8", "ignore")
        t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t); t = re.sub(r"\s+", " ", t)
    print(f"\n===== {bank} {ex} ({len(t)} chars, pdf={ispdf}) =====")
    for kw in KWS:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            i = hits[0]
            print(f"[{kw}] x{len(hits)}: ...{t[max(0,i-70):i+190]}...".replace("\n", " "))
        else:
            print(f"[{kw}] NOT FOUND")

dl_and_grep("BNS", "9631", "000119312525304627", "d13990dex991.htm", "bns_ex991")
dl_and_grep("BNS", "9631", "000119312525304627", "d13990dex992.htm", "bns_ex992")
dl_and_grep("CM", "1045520", "000119312525307482", "d49585dex991.pdf", "cm_ex991")
dl_and_grep("CM", "1045520", "000119312525307494", "d126518dex991.htm", "cm_ex991b")
