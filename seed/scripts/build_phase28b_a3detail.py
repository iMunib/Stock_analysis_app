# -*- coding: utf-8 -*-
"""Phase 2.8 A3 detail - ENB/TRP payout, comparable EBITDA, mix."""
import openpyxl

XLSX = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\NA_Company_Financials.xlsx"
wb = openpyxl.load_workbook(XLSX)
ws = wb["Utility_Pipeline"]
hdr = [c.value for c in ws[1]]
col = {h: i + 1 for i, h in enumerate(hdr)}
ticker_rows = {ws.cell(row=r, column=col["Ticker"]).value: r for r in range(2, ws.max_row + 1)}

def setv(tk, field, val):
    if tk in ticker_rows and field in col:
        ws.cell(row=ticker_rows[tk], column=col[field], value=val)

def append_note(tk, text):
    if tk not in ticker_rows:
        return
    r = ticker_rows[tk]
    cur = ws.cell(row=r, column=col["Notes"]).value or ""
    ws.cell(row=r, column=col["Notes"], value=(cur + " " + text).strip())

# ENB - Enbridge
setv("ENB", "Dividend_Payout", "60-70% of DCF (stated payout target)")
setv("ENB", "Commodity_vs_Contracted_Mix", "Predominantly contracted/cost-of-service (Mainline tolls, gas utility, renewables PPAs) - exact % in MD&A")
append_note("ENB", "FY2025 DCF $12.5B (up 4%). 2026 dividend $0.97/qtr ($3.88 annualized), 31st consecutive annual increase. DCF/share = record, exact figure in MD&A (not headline release) - left N/A. Debt-to-EBITDA 2.31x (XBRL).")

# TRP - TC Energy
setv("TRP", "Dividend_Payout", "~90%+ of comparable earnings (26th yr of growth)")
setv("TRP", "Commodity_vs_Contracted_Mix", "Predominantly rate-regulated/long-term contracted gas pipelines - exact % in MD&A")
append_note("TRP", "FY2025 comparable EBITDA $11.0B (vs $10.0B 2024); CFGO $7,996M. Dividend $0.8775/qtr ($3.51 annualized), 26th consecutive annual increase. Debt-to-EBITDA 2.38x (XBRL). Coverage ratio in MD&A - left N/A.")

wb.save(XLSX)
print("Saved A3 detail for ENB/TRP.")
