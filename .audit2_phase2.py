import openpyxl, json, csv
wb = openpyxl.load_workbook("seed/Sector_Financials_Final_Owner.xlsx", read_only=True, data_only=True)
ws = wb["03_Data_Quality"]
rows = list(ws.iter_rows(values_only=True))
hdr = [str(x).strip() if x else "" for x in rows[0]]
print("hdr:", hdr)
shown = 0
for r in rows[1:]:
    if r and r[0] and str(r[0]).strip() == "(workbook)":
        print("ROW:", [str(v)[:60] if v is not None else "" for v in r])
        shown += 1
        if shown >= 11: break
wb.close()
print("---- seed/raw files ----")
with open("seed/raw/sec_ticker_exchange.json", encoding="utf-8") as f:
    data = json.load(f)
print("sec_ticker_exchange.json type:", type(data).__name__)
if isinstance(data, dict):
    k = list(data)[:2]
    print("sample keys:", k, "->", [data[x] for x in k])
elif isinstance(data, list):
    print("sample:", data[:2])
with open("seed/raw/universe_master.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    h = next(rd)
    print("universe_master.csv header:", h)
    for i, row in enumerate(rd):
        if i >= 2: break
        print("  row:", row[:8])
with open("seed/config/universe.yaml", encoding="utf-8") as f:
    print("universe.yaml head:")
    print("".join([next(f) for _ in range(12)]))
