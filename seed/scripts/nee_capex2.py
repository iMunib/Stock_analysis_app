import urllib.request, re
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()
acc = "000075330826000015"
html = get(f"https://www.sec.gov/Archives/edgar/data/753308/{acc}/nee-20251231.htm").decode("utf-8", "ignore")
txt = re.sub(r"<[^>]+>", " ", html)
txt = re.sub(r"&nbsp;", " ", txt); txt = re.sub(r"&amp;", "&", txt); txt = re.sub(r"&#8212;", "--", txt)
txt = re.sub(r"\s+", " ", txt)
i = txt.find("CONSOLIDATED STATEMENTS OF CASH FLOWS")
seg = txt[i:i+4500]
# print the investing activities region
j = seg.find("CASH FLOWS FROM INVESTING ACTIVITIES")
print("=== INVESTING ACTIVITIES (raw) ===")
print(seg[j:j+2200])
