import urllib.request, re, os, time
HEADERS = {"User-Agent": "Mozilla/5.0 (research) contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=50) as r:
                return r.read()
        except Exception as e:
            if a == tries - 1:
                return None
            time.sleep(1.5)
    return None

# 1) TD quarterly results page -> extract PDF links
html = get("https://www.td.com/ca/en/about-td/for-investors/investor-relations/financial-information/financial-reports/quarterly-results")
links = []
if html:
    h = html.decode("utf-8", "ignore")
    links = re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)
    print("TD results page PDF links (%d):" % len(links))
    for l in links:
        print("  ", l)
    # candidates mentioning q4/2025 + supp
    cand = [l for l in links if re.search(r'(q4|2025-q4|supp)', l, re.I)]
    for l in cand:
        full = l if l.startswith("http") else ("https://www.td.com" + l if l.startswith("/") else "https://www.td.com/" + l)
        d = get(full)
        if d and d[:4] == b"%PDF" and len(d) < 8*1024*1024:
            open(os.path.join(D, "td_supp.pdf"), "wb").write(d)
            print("SAVED td_supp.pdf", len(d)//1024, "KB  <-", full)
            break
