# -*- coding: utf-8 -*-
"""Phase 2.8 A4 finalize - upgrade CA Source_Primary to IR-verified where confirmed."""
import openpyxl

XLSX = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\NA_Company_Financials.xlsx"
wb = openpyxl.load_workbook(XLSX)
ws = wb["Core_Financials"]
hdr = [c.value for c in ws[1]]
col = {h: i + 1 for i, h in enumerate(hdr)}

# ticker -> (new Source_Primary, verification note)
verified = {
    "RY": ("SEC 6-K (primary)", "NI $20.4B FY2025 matches Yahoo"),
    "TD": ("SEC 6-K (primary)", "CET1 14.7% primary; NI Yahoo $20.5B (6-K FY pending)"),
    "BNS": ("Issuer press release (primary)", "NI $7,758M FY2025 matches Yahoo"),
    "BMO": ("SEC 6-K (primary)", "NI Yahoo $8.7B; CET1 13.3% primary"),
    "CM": ("SEC 6-K (primary)", "NI $8.5B FY2025 matches Yahoo"),
    "NA": ("Issuer press release (primary)", "Q4 NI $1,059M primary"),
    "T": ("IR annual report (verified)", "Revenue $20.3B + NI $1.1B match Yahoo"),
    "CNR": ("IR annual report (verified)", "Revenue C$17,304M matches Yahoo"),
    "RCI-B": ("IR annual report (verified)", "NI attributable $6,894M matches Yahoo (macrotrends $4.9B was wrong)"),
    "BCE": ("IR annual report (verified)", "FY2025 net earnings $6,514M vs Yahoo $6,460B (0.8%)"),
    "TRP": ("IR annual report (verified)", "NI $3.6B vs Yahoo $3,519B (2.3%)"),
    "FTS": ("IR annual report (verified)", "NI-to-common $1.7B vs Yahoo NI $1,799B (definitional: NCI)"),
}

for r in range(2, ws.max_row + 1):
    tk = ws.cell(row=r, column=col["Ticker"]).value
    if tk in verified:
        note = verified[tk][0]
        # update Source_Primary and prepend verification to Notes
        ws.cell(row=r, column=col["Source_Primary"]).value = note
        cur = ws.cell(row=r, column=col["Notes"]).value or ""
        vnote = "A4: " + verified[tk][1] + "."
        if "A4:" not in cur:
            ws.cell(row=r, column=col["Notes"]).value = (cur + " " + vnote).strip() if cur else vnote

wb.save(XLSX)
print("Saved A4 source-status upgrade for", len(verified), "CA names.")
