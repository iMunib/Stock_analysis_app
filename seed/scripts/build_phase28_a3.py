# -*- coding: utf-8 -*-
"""Phase 2.8 A3 - utility/pipeline non-GAAP MD&A metrics (ENB/TRP/FTS/DUK)."""
import openpyxl

XLSX = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\NA_Company_Financials.xlsx"
wb = openpyxl.load_workbook(XLSX)
ws = wb["Utility_Pipeline"]

# column names
hdr = [c.value for c in ws[1]]
col = {h: i + 1 for i, h in enumerate(hdr)}

# ticker -> row
ticker_rows = {}
for r in range(2, ws.max_row + 1):
    tk = ws.cell(row=r, column=col["Ticker"]).value
    if tk:
        ticker_rows[tk] = r

def setv(tk, field, val):
    if tk in ticker_rows and field in col:
        ws.cell(row=ticker_rows[tk], column=col[field], value=val)

def append_note(tk, text):
    if tk not in ticker_rows:
        return
    r = ticker_rows[tk]
    cur = ws.cell(row=r, column=col["Notes"]).value or ""
    ws.cell(row=r, column=col["Notes"], value=(cur + " " + text).strip())

# ENB - Enbridge (pipeline): DCF
setv("ENB", "DCF_or_Comparable", 12500000000)
setv("ENB", "Issuer_Term", "Distributable Cash Flow (DCF)")
setv("ENB", "Source_URL", "https://www.prnewswire.com/news-releases/enbridge-reports-record-2025-financial-results-reaffirms-2026-financial-guidance-and-grows-secured-backlog-to-39-billion-302687600.html")
setv("ENB", "Confidence", "High (issuer press release)")
append_note("ENB", "FY2025 DCF $12.5B (up 4% from $12.0B 2024); record EBITDA + DCF per share. DCF/share + coverage ratio in MD&A (not headline release) - left NA.")

# TRP - TC Energy (pipeline): comparable funds generated from operations
setv("TRP", "DCF_or_Comparable", 7996000000)
setv("TRP", "Issuer_Term", "Comparable funds generated from operations (CFGO)")
setv("TRP", "Source_URL", "https://www.tcenergy.com/announcements/2026/2026-02-13-tc-energy-reports-fourth-quarter-and-full-year-2025-results/")
setv("TRP", "Confidence", "High (issuer press release)")
append_note("TRP", "FY2025 CFGO $7,996M (vs $7,890M 2024). TC Energy does not headline 'DCF'; uses CFGO + dividend payout. Q4 comparable EBITDA +13% YoY; Q4 comparable EPS $0.98.")

# FTS - Fortis (utility): rate base
setv("FTS", "Rate_Base", 42400000000)
setv("FTS", "Rate_Base_Growth", 0.07)
setv("FTS", "Source_URL", "https://www.fortisinc.com/news/news-releases/detail?id=9776")
setv("FTS", "Confidence", "High (issuer press release)")
append_note("FTS", "2025 midyear rate base $42.4B; 7% annual rate base growth; net earnings $1.7B ($3.40/sh); $28.8B 5-yr capital plan (to $57.9B rate base by 2030).")

# DUK - Duke Energy (utility): FFO to debt
setv("DUK", "FFO_to_Debt", 0.148)
setv("DUK", "Source_URL", "https://www.sec.gov/Archives/edgar/data/1326160/000132616026000007/er-20251231xearningsreleas.htm")
setv("DUK", "Confidence", "Medium (earnings call transcript; 14.8% FFO-to-debt)")
append_note("DUK", "FFO-to-debt 14.8% (2025). 2025 adjusted EPS $6.31 (up 7% YoY); Q4 2025 reported EPS $1.50 vs $1.54.")

wb.save(XLSX)
print("Saved. Utility_Pipeline updated for ENB/TRP/FTS/DUK.")
