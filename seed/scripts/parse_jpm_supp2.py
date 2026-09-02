import openpyxl
p = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\jpm_4q25_supp.xlsx"
wb = openpyxl.load_workbook(p, data_only=True)

def show(sn, cells):
    ws = wb[sn]
    for coord in cells:
        c = ws[coord]
        # also grab right neighbors (quarter columns)
        row = c.row; col = c.column
        neigh = [ws.cell(row=row, column=col+k).value for k in range(0, 5)]
        print(f"  {sn}!{coord} = {c.value!r}  -> {neigh}")

print("=== Page 2 (TBVPS, ROTCE, CET1) ===")
show("Page 2", ["B32", "B37", "B41"])
# print rows 30-46 full (label + values) to capture the table
ws = wb["Page 2"]
print("\nPage 2 rows 28-46 (label | col C..F):")
for r in range(28, 47):
    lab = ws.cell(row=r, column=1).value or ws.cell(row=r, column=2).value
    vals = [ws.cell(row=r, column=c).value for c in range(3, 8)]
    if lab or any(v is not None for v in vals):
        print(f"  r{r}: {lab!r} | {vals}")

print("\n=== Page 9 (CET1) rows 8-30 ===")
ws = wb["Page 9"]
for r in range(8, 31):
    lab = ws.cell(row=r, column=2).value or ws.cell(row=r, column=3).value
    vals = [ws.cell(row=r, column=c).value for c in range(4, 9)]
    if lab or any(v is not None for v in vals):
        print(f"  r{r}: {lab!r} | {vals}")
