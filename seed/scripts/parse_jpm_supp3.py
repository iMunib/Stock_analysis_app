import openpyxl
p = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw\docs\jpm_4q25_supp.xlsx"
wb = openpyxl.load_workbook(p, data_only=True)
keys = ["overhead ratio", "net yield", "net interest margin", "nonperforming", "nonaccrual",
        "net charge-off", "charge-off", "allowance", "efficiency", "net interest margin on interest-earning assets"]
for sn in wb.sheetnames:
    ws = wb[sn]
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and any(k in c.value.lower() for k in keys):
                # print label + row values (columns C..G)
                vals = [ws.cell(row=c.row, column=cc).value for cc in range(c.column, c.column+6)]
                print(f"{sn}!{c.coordinate}: {c.value[:60]!r} -> {vals}")
