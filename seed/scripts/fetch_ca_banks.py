import urllib.request, re, os, time
HEADERS = {"User-Agent": "Mozilla/5.0 (research) contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"

def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            if a == tries - 1:
                return None
            time.sleep(1)
    return None

def dl(url, fn):
    data = get(url)
    if data and len(data) < 8*1024*1024 and data[:4] == b"%PDF":
        open(os.path.join(D, fn), "wb").write(data)
        print(f"OK  {fn}  {len(data)//1024} KB  <- {url}")
        return True
    print(f"FAIL {fn} ({len(data)//1024 if data else 'none'} KB, pdf={data[:4]==b'%PDF' if data else False})  <- {url}")
    return False

# TD Q4 2025
dl("https://www.td.com/content/dam/tdcom/canada/about-td/pdf/quarterly-results/2025/q4/2025-q4-financial-supppack-en.pdf", "td_q4_25.pdf")

# BMO Q4 2025 (try patterns)
for u in ["https://www.bmo.com/ir/qtrinfo/1/2025-q4/Suppq425.pdf",
          "https://www.bmo.com/ir/qtrinfo/1/2025-q4/Suppq425_Dec4.pdf",
          "https://www.bmo.com/ir/qtrinfo/1/2025-q4/Suppq425_final.pdf"]:
    if dl(u, "bmo_q4_25.pdf"):
        break

# RY: fetch IR page, find supplementary PDF link
html = get("https://www.rbc.com/investor-relations/financial-information.html")
if html:
    h = html.decode("utf-8", "ignore")
    links = re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)
    print("\nRBC IR page PDF links:")
    for l in links[:30]:
        print("  ", l)
    # try to find Q4 2025 supplementary
    cand = [l for l in links if re.search(r'(q4|fourth|2025).*(supp|sup|sfi|financial)', l, re.I)]
    for l in cand[:5]:
        full = l if l.startswith("http") else ("https://www.rbc.com" + l if l.startswith("/") else l)
        if dl(full, "ry_q4_25.pdf"):
            break
