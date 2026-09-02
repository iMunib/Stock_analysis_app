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
    t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"\s+", " ", t)
    print(f"--- {name}: {len(t)} chars ---")
    for kw in kws:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            i = hits[0]
            seg = t[max(0, i-70):i+220].encode("ascii", "replace").decode()
            print(f"[{kw}] x{len(hits)}: {seg}")
        else:
            print(f"[{kw}] NOT FOUND")

grep("Enbridge Q4 (prnewswire)", get("https://www.prnewswire.com/news-releases/enbridge-reports-record-2025-financial-results-reaffirms-2026-financial-guidance-and-grows-secured-backlog-to-39-billion-302687600.html"),
     ["distributable cash flow", "DCF per share", "DCF", "coverage"])
grep("TC Energy Q4 (tcenergy.com)", get("https://www.tcenergy.com/announcements/2026/2026-02-13-tc-energy-reports-fourth-quarter-and-full-year-2025-results/"),
     ["funds generated", "comparable EBITDA", "payout", "dividend", "per common share"])
