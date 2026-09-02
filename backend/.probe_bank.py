import openpyxl
wb = openpyxl.load_workbook("../seed/Sector_Financials_Final_Owner.xlsx", read_only=True, data_only=True)
ws = wb["01_All_Companies"]
rows = list(ws.iter_rows(values_only=True))
hdr = [str(c).strip() if c else "" for c in rows[0]]
i_id, i_debt, i_gross = hdr.index("Company_ID"), hdr.index("Total_Debt"), hdr.index("Gross_Profit")
i_sector = hdr.index("GICS_Sector")
for r in rows[1:]:
    if r[i_id] == "CA:RY:TSX":
        print("RY Total_Debt:", r[i_debt], "| Gross_Profit:", r[i_gross])
banks_with_debt = [str(r[i_id]) for r in rows[1:] if r[i_sector] == "Financials" and r[i_debt] is not None]
print("financials WITH Total_Debt in seed:", len(banks_with_debt), banks_with_debt[:5])
wb.close()
