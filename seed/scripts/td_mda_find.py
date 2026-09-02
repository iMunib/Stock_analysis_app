import re, os, time, urllib.request
from pypdf import PdfReader
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
HEADERS = {"User-Agent": "Mozilla/5.0 (research) contact@openclaw.local"}
def get(u):
    for a in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=50).read()
        except Exception as e:
            if a == 2: return None
            time.sleep(1.5)

html = get("https://www.td.com/ca/en/about-td/for-investors/investor-relations/financial-information/financial-reports/annual-reports")
links = []
if html:
    h = html.decode("utf-8", "ignore")
    links = sorted(set(re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)))
    print("TD annual-reports page PDF links:", len(links))
    for l in links:
        print("  ", l)

# try the MD&A / annual report for 2025
cand = [l for l in links if re.search(r'(2025|md-a|mda|annual)', l, re.I)]
tried = set()
for l in cand[:6]:
    full = l if l.startswith("http") else ("https://www.td.com" + l if l.startswith("/") else "https://www.td.com/" + l)
    if full in tried: continue
    tried.add(full)
    d = get(full)
    if d and d[:4] == b"%PDF":
        kb = len(d)//1024
        print(f"\n{full.split('/')[-1]}: {kb} KB")
        if kb < 8*1024:
            open(os.path.join(D, "td_mda.pdf"), "wb").write(d)
            txt = re.sub(r"\s+", " ", "\n".join((p.extract_text() or "") for p in PdfReader(os.path.join(D, "td_mda.pdf")).pages))
            for kw in ["gross impaired loans", "net interest margin", "net write-offs"]:
                hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
                if hits:
                    i = hits[0]; print(f"  [{kw}] x{len(hits)}: {txt[max(0,i-60):i+180].encode('ascii','replace').decode()}")
                else:
                    print(f"  [{kw}] NOT FOUND")
            break
        else:
            print("  TOO BIG")
