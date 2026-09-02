import re, os
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

def pdf_txt(fn):
    return re.sub(r"\s+", " ", "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, fn)).pages))

def ctx(name, txt, kw, before=200, after=500):
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    print(f"\n===== {name} [{kw}] x{len(hits)} =====")
    for i in hits[:2]:
        print(txt[max(0, i-before):i+after].encode("ascii", "replace").decode())
        print("---")

bmo = pdf_txt("bmo_q4.pdf")
ctx("BMO", bmo, "Net write-offs as a %")

cm = pdf_txt("cm_ex991.pdf")
ctx("CM", cm, "average loans and acceptances", before=100, after=300)
ctx("CM", cm, "write-offs as a % of average", before=100, after=300)

na = open(os.path.join(D, "NA_news.txt"), encoding="utf-8").read()
ctx("NA", na, "gross impaired loans", before=50, after=300)
ctx("NA", na, "Net impaired loans as a %", before=150, after=200)
