import urllib.request, os
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
os.makedirs(D, exist_ok=True)

def dl(url, fn):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        with open(os.path.join(D, fn), "wb") as f:
            f.write(data)
        print(f"OK  {fn}  {len(data)//1024} KB")
        return True
    except Exception as e:
        print(f"ERR {fn}: {e}")
        return False

dl("https://www.wellsfargo.com/assets/pdf/about/investor-relations/earnings/fourth-quarter-2025-financial-results.pdf", "wfc_4q25.pdf")
dl("https://investor.bankofamerica.com/regulatory-and-other-filings/select-sec-filings/content/0000070858-26-000020/0000070858-26-000020.pdf", "bac_4q25.pdf")
dl("https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/4th-quarter/3f2030e7-c144-4ad8-92b8-57b36851ffb6.pdf", "jpm_4q25_pres.pdf")
dl("https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/4th-quarter/4q25-earnings-supplement.xlsx", "jpm_4q25_supp.xlsx")
