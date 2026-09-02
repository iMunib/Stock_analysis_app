import re, os
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
na = open(os.path.join(D, "NA_news.txt"), encoding="utf-8").read()
# Find balance-sheet "Loans" and "Total assets" figures
for kw in ["Loans", "Total assets", "Total loans", "loans and acceptances", "Personal lending", "gross loans"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), na, re.I)]
    print(f"\n[{kw}] x{len(hits)}")
    for i in hits[:4]:
        seg = re.sub(r"\s+", " ", na[max(0, i-40):i+140]).encode("ascii", "replace").decode()
        print("  ", seg)
