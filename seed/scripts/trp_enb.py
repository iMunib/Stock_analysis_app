import urllib.request, re, time
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
def get(u):
    for a in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=50).read()
        except Exception as e:
            if a == 2:
                print("  FAIL", u.split("/")[-1], str(e)[:60]); return None
            time.sleep(1.5)

def grep(name, d, kws):
    if not d:
        print(f"--- {name}: NO DATA ---"); return
    t = d.decode("utf-8", "ignore")
    if name.endswith("(html)"):
        t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"\s+", " ", t)
    print(f"--- {name}: {len(t)} chars ---")
    for kw in kws:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            i = hits[0]
            seg = t[max(0, i-70):i+200].encode("ascii", "replace").decode()
            print(f"[{kw}] x{len(hits)}: {seg}")
        else:
            print(f"[{kw}] NOT FOUND")

grep("TC Energy Q4 (html)", get("https://www.globenewswire.com/news-release/2026/02/13/3237978/0/en/tc-energy-reports-fourth-quarter-and-full-year-2025-results.html"),
     ["comparable distributable cash flow", "coverage", "comparable EBITDA", "comparable earnings per common share"])
grep("Enbridge 8-K ex991 (html)", get("https://www.sec.gov/Archives/edgar/data/895728/000119312525306723/d85502dex991.htm"),
     ["distributable cash flow", "DCF", "coverage", "adjusted EBITDA"])
