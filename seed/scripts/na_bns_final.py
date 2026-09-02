import re, urllib.request, time
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
t = open(D + r"\NA_news.txt", encoding="utf-8").read()
for kw in ["Net interest margin (3)", "Return on common shareholders"]:
    for m in re.finditer(re.escape(kw), t):
        seg = re.sub(r"\s+", " ", t[m.start():m.start()+90])
        print("NA", repr(seg))
print()
HEADERS = {"User-Agent": "Mozilla/5.0 (research)"}
def get(u):
    for a in range(2):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=HEADERS), timeout=40).read()
        except Exception:
            if a == 1:
                return None
            time.sleep(1)
for u in ["https://www.scotiabank.com/ca/en/about/investors-shareholders/quarterly-results.html"]:
    d = get(u)
    if not d:
        print("FAIL", u)
        continue
    h = d.decode("utf-8", "ignore")
    links = sorted(set(re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)))
    print("BNS page ->", len(links), "pdf links")
    for l in links:
        print("   ", l)
