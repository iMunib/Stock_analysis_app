import re, os
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
KWS = ["CET1", "common equity tier 1", "net interest margin", "efficiency ratio", "gross impaired",
       "impaired loans", "net write-off", "provision for credit losses", "tangible book value",
       "return on tangible", "return on equity", "diluted EPS", "net income", "total capital ratio", "leverage ratio"]

def grep_htm(fn):
    t = open(os.path.join(D, fn), encoding="utf-8", errors="ignore").read()
    t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"\s+", " ", t)
    print(f"\n===== {fn} ({len(t)} chars) =====")
    for kw in KWS:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            i = hits[0]
            print(f"[{kw}] x{len(hits)}: ...{t[max(0,i-80):i+200]}...".replace("\n", " "))
        else:
            print(f"[{kw}] NOT FOUND")

def grep_pdf(fn):
    t = "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, fn)).pages)
    print(f"\n===== {fn} ({len(t)} chars) =====")
    for kw in KWS:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            i = hits[0]
            print(f"[{kw}] x{len(hits)}: ...{t[max(0,i-80):i+200]}...".replace("\n", " "))
        else:
            print(f"[{kw}] NOT FOUND")

grep_htm("td_ex992.txt")
grep_pdf("bmo_q4.pdf")
