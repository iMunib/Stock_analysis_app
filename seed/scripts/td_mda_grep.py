import re, os
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
txt = re.sub(r"\s+", " ", "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, "td_mda.pdf")).pages))
open(os.path.join(D, "td_mda.txt"), "w", encoding="utf-8").write(txt)

def show(kw, before=80, after=320, n=3):
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    print(f"\n[{kw}] x{len(hits)}")
    for i in hits[:n]:
        print("   ", txt[max(0, i-before):i+after].encode("ascii", "replace").decode())
        print("   ---")

show("total gross impaired loans")
show("gross impaired loans were")
show("impaired loans totalled")
show("net interest margin", n=2)
show("impaired loans as a %", n=2)
