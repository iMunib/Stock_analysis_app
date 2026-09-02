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
            time.sleep(1)
    return None

def grep(fn, kws, ispdf=False):
    if ispdf:
        t = "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, fn)).pages)
    else:
        t = open(os.path.join(D, fn), encoding="utf-8", errors="ignore").read()
        t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t)
        t = re.sub(r"\s+", " ", t)
    print(f"\n===== {fn} ({len(t)} chars) =====")
    for kw in kws:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            i = hits[0]
            print(f"[{kw}] x{len(hits)}: ...{t[max(0,i-90):i+220]}...".replace("\n", " "))
        else:
            print(f"[{kw}] NOT FOUND")
    return t

# RY press release (HTML)
ry_press = grep("ry_press.htm", ["CET1", "common equity tier 1", "net interest margin", "efficiency ratio",
                                 "impaired", "provision for credit losses", "tangible book value", "return on tangible",
                                 "diluted EPS", "net income", "return on equity"])

# RY supplementary (PDF)
grep("ry_supp.pdf", ["CET1", "net interest margin", "efficiency ratio", "gross impaired", "impaired loans",
                     "provision for credit losses", "net write-offs", "tangible book value", "return on tangible common equity"], ispdf=True)

# TD exhibits
for acc, c in [("000156276225000287", 947263)]:
    for ex in ["ex991.htm", "ex992.htm", "ex993.htm", "ex994.htm", "ex995.htm", "ex996.htm"]:
        url = f"https://www.sec.gov/Archives/edgar/data/{c}/{acc}/{ex}"
        d = get(url)
        if d:
            open(os.path.join(D, f"td_{ex.replace('.htm','.txt')}"), "wb").write(d)
            print(f"OK td {ex} {len(d)//1024}KB")

# BMO PDF
d = get("https://www.sec.gov/Archives/edgar/data/927971/000119312525308014/d50246dex991.pdf")
if d:
    open(os.path.join(D, "bmo_q4.pdf"), "wb").write(d)
    print(f"OK bmo_q4.pdf {len(d)//1024}KB pdf={d[:4]==b'%PDF'}")
