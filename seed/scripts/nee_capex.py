import json, urllib.request, re, os
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"

def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

acc = "000075330826000015"
# main 10-K document (inline XBRL) — full statements
url = f"https://www.sec.gov/Archives/edgar/data/753308/{acc}/nee-20251231.htm"
html = get(url).decode("utf-8", "ignore")
print("doc bytes:", len(html))

# strip tags -> text
txt = re.sub(r"<[^>]+>", " ", html)
txt = re.sub(r"&nbsp;", " ", txt)
txt = re.sub(r"&amp;", "&", txt)
txt = re.sub(r"\s+", " ", txt)

# locate cash flow statement
i = txt.find("CONSOLIDATED STATEMENTS OF CASH FLOWS")
if i < 0:
    i = txt.find("STATEMENTS OF CASH FLOWS")
print("cashflow header idx:", i)
seg = txt[i:i+6000] if i >= 0 else ""
# find capital expenditure mentions
for m in re.finditer(r"[Cc]apital expenditure[^.]{0,120}", seg):
    print("  ...", m.group(0)[:130])
