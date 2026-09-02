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
def clean(d):
    t = d.decode("utf-8", "ignore")
    t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"&nbsp;", " ", t); t = re.sub(r"&amp;", "&", t); t = re.sub(r"&#149;", "-", t)
    return re.sub(r"\s+", " ", t)
def show(name, t, kws, ctx=260):
    print(f"\n===== {name} =====")
    for kw in kws:
        hits = [m.start() for m in re.finditer(re.escape(kw), t, re.I)]
        if hits:
            for i in hits[:2]:
                print(f"[{kw}]: {t[max(0,i-80):i+ctx].encode('ascii','replace').decode()}")
        else:
            print(f"[{kw}] NOT FOUND")

enb = get("https://www.prnewswire.com/news-releases/enbridge-reports-record-2025-financial-results-reaffirms-2026-financial-guidance-and-grows-secured-backlog-to-39-billion-302687600.html")
if enb:
    t = clean(enb)
    open(r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\enb_q4.txt", "w", encoding="utf-8").write(t)
    show("ENB", t, ["DCF per share of $", "per share of $5", "contracted", "payout", "coverage", "dividend"])

trp = get("https://www.tcenergy.com/announcements/2026/2026-02-13-tc-energy-reports-fourth-quarter-and-full-year-2025-results/")
if trp:
    t = clean(trp)
    open(r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\trp_q4.txt", "w", encoding="utf-8").write(t)
    show("TRP", t, ["payout", "contracted", "coverage", "dividend", "leverage", "comparable EBITDA of"])
