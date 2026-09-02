import re, os
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

def pdf_txt(fn):
    return re.sub(r"\s+", " ", "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, fn)).pages))

def show(name, txt, kws, ctx=180):
    print(f"\n===== {name} ({len(txt)} chars) =====")
    for kw in kws:
        hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
        if hits:
            i = hits[0]
            print(f"[{kw}] x{len(hits)}: {txt[max(0,i-60):i+ctx].encode('ascii','replace').decode()}")
        else:
            print(f"[{kw}] NOT FOUND")

# CM - find loan denominator for GIL ratio and average loans for NCO
cm = pdf_txt("cm_ex991.pdf")
show("CM", cm, ["gross loans", "loans and acceptances", "average loans", "total loans", "net write-offs"])

# NA - find loan denominator
na = open(os.path.join(D, "NA_news.txt"), encoding="utf-8").read()
show("NA", na, ["gross loans", "loans", "total loans", "average loans"])

# BMO - NCO period label + gross loans
bmo = pdf_txt("bmo_q4.pdf")
show("BMO", bmo, ["net write-offs", "write-offs", "gross impaired loans", "gross loans", "average loans"])
