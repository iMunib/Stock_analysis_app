import re, os
D = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs"
txt = open(os.path.join(D, "td_mda.txt"), encoding="utf-8").read()
def show(kw, before=60, after=300, n=3):
    hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)]
    print(f"\n[{kw}] x{len(hits)}")
    for i in hits[:n]:
        print("   ", txt[max(0, i-before):i+after].encode("ascii", "replace").decode())
        print("   ---")
show("gross impaired loans")
show("Gross impaired loans")
show("loans and acceptances", n=2)
show("net impaired loans")
