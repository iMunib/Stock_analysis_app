import re, os
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
f = os.path.join(D, "bns_Q425_Quarterly_Press_Release-EN.pdf")
txt = "\n".join((p.extract_text() or "") for p in PdfReader(f).pages)
txt = re.sub(r"\s+", " ", txt)
# save unicode-safe
open(os.path.join(D, "bns_q425.txt"), "w", encoding="utf-8").write(txt)
for kw in ["efficiency", "productivity ratio", "return on equity", "total capital", "Tier 1 capital",
           "net interest margin", "gross impaired loans as a", "net write-offs as a % of average net"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    if hits:
        i = hits[0]
        seg = txt[max(0, i-50):i+200].encode("ascii", "replace").decode()
        print(f"[{kw}] x{len(hits)}: {seg}")
    else:
        print(f"[{kw}] NOT FOUND")
