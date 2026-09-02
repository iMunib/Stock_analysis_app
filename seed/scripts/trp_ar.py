import urllib.request, re, time
from pypdf import PdfReader
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
u = "https://www.tcenergy.com/siteassets/pdfs/investors/reports-and-filings/annual-and-quarterly-reports/2025/tce-2025-annual-report.pdf"
d = None
for a in range(3):
    try:
        d = urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=60).read(); break
    except Exception:
        d = None; time.sleep(2)
if not d or d[:4] != b"%PDF":
    print("FAIL")
else:
    kb = len(d) // 1024
    print("size KB:", kb)
    if kb < 8 * 1024:
        open(r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\trp_ar.pdf", "wb").write(d)
        txt = "\n".join((p.extract_text() or "") for p in PdfReader(r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\trp_ar.pdf").pages)
        txt = re.sub(r"\s+", " ", txt)
        open(r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\trp_ar.txt", "w", encoding="utf-8").write(txt)
        for kw in ["distributable cash flow", "coverage ratio", "comparable funds generated", "rate base"]:
            hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
            if hits:
                i = hits[0]
                seg = txt[max(0, i-60):i+200].encode("ascii", "replace").decode()
                print(f"[{kw}] x{len(hits)}: {seg}")
            else:
                print(f"[{kw}] NOT FOUND")
    else:
        print("TOO BIG")
