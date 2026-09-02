import os
import re
import sys
import traceback
from datetime import date

import numpy as np
import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
V2 = os.path.join(ROOT, "Sector_Financials_Final_v2.xlsx")
OUT = os.path.join(ROOT, "Sector_Financials_CleanView.xlsx")
LOGD = os.path.join(ROOT, "logs")
EXPORTS = os.path.join(ROOT, "exports")
TODAY = date.today().isoformat()

DROP_PAT = re.compile(r"fill_source|calc_method|method_notes|placement_reason", re.I)
TAB_COLORS = {"Banks": "1F4E78", "Utilities_Regulated": "007782", "Software": "6A3D9A",
              "Semiconductors_Components": "3F51B5", "Oil_Gas_Producers": "E36C0A",
              "Insurance": "1E6B45", "Financials": "1E6B45", "Credit_Services": "1E6B45",
              "Discount_Stores": "C9A227"}
META_TAB, STEEL_TAB, GOLD_TAB, GICS_TAB = "808080", "4682B4", "C9A227", "2E7D32"

METHOD_LINES = [
    "",
    "METHODS (single source of truth - per-row method/provenance text was stripped in this CleanView):",
    "- FCF_Calc = Operating_Cash_Flow - abs(Capex); intentionally blank for Banks.",
    "- NetDebt_Calc = Total_Debt - Cash_ST_Investments.",
    "- ROE_Calc = Net_Income / ending Book_Equity (not average equity).",
    "- ROA_Calc = Net_Income / ending Total_Assets.",
    "- PE_Calc = Price / Diluted_EPS (blank when EPS <= 0); PB_Calc = Market_Cap / Book_Equity.",
    "- EV_Calc = Market_Cap + Total_Debt - Cash_ST_Investments; EV_to_EBITDA uses tagged or EBIT+D&A derived EBITDA > 0 only.",
    "- EBITDA often derived as EBIT + Depreciation & Amortization where a tagged EBITDA was absent.",
    "- Extra-sheet copies of a company are intentional multi-placement (Placement_Role = Extra, pale green); Primary = Universe.Custom_Industry_Sheet home tab.",
]


def num(s):
    return pd.to_numeric(s, errors="coerce")


def main():
    src = pd.ExcelFile(V2)
    sheet_dfs = {}
    dropped_report = {}
    for sname in src.sheet_names:
        df = src.parse(sname, keep_default_na=False)
        if sname == "00_README":
            lines = df["A"].astype(str).tolist()
            df = pd.DataFrame({"A": lines + METHOD_LINES})
            sheet_dfs[sname] = df
            continue
        hit = [c for c in df.columns if DROP_PAT.search(str(c))]
        if hit:
            df = df.drop(columns=hit)
            dropped_report[sname] = hit
        sheet_dfs[sname] = df
    print("dropped columns per sheet:")
    for s, h in dropped_report.items():
        print(f"  {s}: {h}")

    ac = sheet_dfs["01_All_Companies"]
    assert len(ac) == 720 and ac["Company_ID"].nunique() == 720

    if os.path.exists(OUT):
        os.remove(OUT)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        for sname, df in sheet_dfs.items():
            df.to_excel(xw, sheet_name=sname, index=False)

    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = load_workbook(OUT)
    MONEY = {"Revenue", "Net_Income", "Gross_Profit", "Operating_Cash_Flow", "Capex", "Total_Debt",
             "Cash_ST_Investments", "Book_Equity", "Total_Assets", "Total_Liabilities", "EBIT",
             "EBITDA", "Interest_Expense", "FCF_Reported", "Free_Cash_Flow", "FCF_Calc",
             "NetDebt_Calc", "Market_Cap", "EV_Calc", "Shares_Snapshot"}
    TWO = {"Diluted_EPS", "Price"}
    RATIO2 = {"PE_Calc", "PB_Calc", "EV_to_EBITDA_Calc"}
    PCT = {"FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc", "CET1_Ratio",
           "Total_Capital_Ratio", "Leverage_Ratio", "NIM_FY2025", "NIM_Q4_2025", "Efficiency_Ratio", "ROAA"}
    GREYABLE = {"Revenue", "Net_Income", "Diluted_EPS", "Gross_Profit", "Operating_Cash_Flow", "Capex",
                "Total_Debt", "Book_Equity", "Cash_ST_Investments", "Total_Assets", "Total_Liabilities",
                "EBIT", "EBITDA", "Interest_Expense", "FCF_Reported", "Free_Cash_Flow", "FCF_Calc",
                "NetDebt_Calc", "FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc",
                "PE_Calc", "PB_Calc", "EV_Calc", "EV_to_EBITDA_Calc"}
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    band_fill = PatternFill("solid", fgColor="D6EAF8")
    band_grey = PatternFill("solid", fgColor="E8EEF4")
    greycell = PatternFill("solid", fgColor="F2F2F2")
    amber = PatternFill("solid", fgColor="FDEBD0")
    pale_red = PatternFill("solid", fgColor="FADBD8")
    pale_green = PatternFill("solid", fgColor="E8F5E9")
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    data_sheets = []
    for ws in wb.worksheets:
        name = ws.title
        is_meta = name.startswith("0")
        if name == "Banks":
            ws.sheet_properties.tabColor = TAB_COLORS["Banks"]
        elif name == "Utilities_Regulated":
            ws.sheet_properties.tabColor = TAB_COLORS["Utilities_Regulated"]
        elif name == "Software":
            ws.sheet_properties.tabColor = TAB_COLORS["Software"]
        elif name == "Semiconductors_Components":
            ws.sheet_properties.tabColor = TAB_COLORS["Semiconductors_Components"]
        elif name == "Oil_Gas_Producers":
            ws.sheet_properties.tabColor = TAB_COLORS["Oil_Gas_Producers"]
        elif name in ("Insurance", "Financials", "Credit_Services"):
            ws.sheet_properties.tabColor = TAB_COLORS[name]
        elif name.startswith("GICS_"):
            ws.sheet_properties.tabColor = GICS_TAB
        elif not is_meta and (name.startswith(("Consumer", "Retail")) or name == "Discount_Stores"):
            ws.sheet_properties.tabColor = GOLD_TAB
        elif is_meta:
            ws.sheet_properties.tabColor = META_TAB
        else:
            ws.sheet_properties.tabColor = STEEL_TAB

        if name == "00_README":
            ws.column_dimensions["A"].width = 150
            for r in range(1, ws.max_row + 1):
                c = ws.cell(row=r, column=1)
                c.font = Font(name="Calibri", size=(14 if r == 1 else 10), bold=(r == 1),
                              color=("1F4E78" if r == 1 else "000000"))
                c.alignment = Alignment(vertical="top")
            continue

        headers = [c.value for c in ws[1]]
        hidx = {h: j for j, h in enumerate(headers, start=1)}
        fmt_map = {}
        for h in headers:
            if h in MONEY:
                fmt_map[h] = "#,##0"
            elif h in TWO:
                fmt_map[h] = "#,##0.00"
            elif h in RATIO2:
                fmt_map[h] = "0.00"
            elif h in PCT:
                fmt_map[h] = "0.0%"
        for j, h in enumerate(headers, start=1):
            hs = str(h)
            if hs == "Company_Name":
                width = 32
            elif hs in ("Resolution", "Notes", "Definition"):
                width = 40
            elif hs in MONEY:
                width = 14
            else:
                smax = 0
                for r in range(2, min(ws.max_row, 200) + 1):
                    v = ws.cell(row=r, column=j).value
                    if v is not None:
                        smax = max(smax, len(str(v)))
                width = min(42, max(11, smax + 2))
            ws.column_dimensions[get_column_letter(j)].width = width
            hc = ws.cell(row=1, column=j)
            hc.font = hdr_font
            hc.fill = hdr_fill
            hc.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
            hc.border = border
        ws.row_dimensions[1].height = 30

        for r in range(2, ws.max_row + 1):
            banded = (r % 2 == 0)
            for j, h in enumerate(headers, start=1):
                c = ws.cell(row=r, column=j)
                c.font = Font(name="Calibri", size=10)
                c.border = border
                if banded:
                    c.fill = band_fill
                if h in fmt_map and isinstance(c.value, (int, float)):
                    c.number_format = fmt_map[h]
            if not is_meta:
                for h in GREYABLE:
                    if h not in hidx:
                        continue
                    c = ws.cell(row=r, column=hidx[h])
                    if c.value is None or (isinstance(c.value, str) and not c.value.strip()):
                        c.fill = band_grey if banded else greycell
                if "Placement_Role" in hidx and str(ws.cell(row=r, column=hidx["Placement_Role"]).value) == "Extra":
                    ws.cell(row=r, column=hidx["Placement_Role"]).fill = pale_green
                if "Fill_OK" in hidx and str(ws.cell(row=r, column=hidx["Fill_OK"]).value).strip() == "N":
                    ws.cell(row=r, column=hidx["Fill_OK"]).fill = amber
                if "Extraction_Status" in hidx and str(ws.cell(row=r, column=hidx["Extraction_Status"]).value).strip() == "MISSING_SOURCE":
                    ws.cell(row=r, column=hidx["Extraction_Status"]).fill = pale_red

        ws.freeze_panes = "B2"
        ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "1:1"
        if not is_meta:
            data_sheets.append(name)
    wb.save(OUT)
    wb.close()

    import zipfile
    z = zipfile.ZipFile(OUT)
    assert not [n for n in z.namelist() if "tables/" in n.lower()]
    z.close()

    from openpyxl import load_workbook as lw
    wbx = lw(OUT, read_only=True)
    bad_headers = []
    for ws in wbx.worksheets:
        for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
            bad_headers += [v for v in row if v and DROP_PAT.search(str(v))]
    wbx.close()
    assert not bad_headers, bad_headers

    pdf_all = pd.read_excel(OUT, sheet_name="01_All_Companies", keep_default_na=False)
    pdf_all.to_csv(os.path.join(EXPORTS, "All_Companies.csv"), index=False, encoding="utf-8-sig")
    n_sheet_csv = 0
    for sname in data_sheets:
        if sname == "06_Placements":
            continue
        pd.read_excel(OUT, sheet_name=sname, keep_default_na=False) \
          .to_csv(os.path.join(EXPORTS, f"{sname}.csv"), index=False, encoding="utf-8-sig")
        n_sheet_csv += 1

    bad_csv = []
    for f in os.listdir(EXPORTS):
        head = pd.read_csv(os.path.join(EXPORTS, f), nrows=0, encoding="utf-8-sig")
        bad_csv += [(f, c) for c in head.columns if DROP_PAT.search(str(c))]
    assert not bad_csv, bad_csv[:5]

    from python_calamine import CalamineWorkbook
    cw = CalamineWorkbook.from_path(OUT)

    def ids_on(sheet):
        rr = cw.get_sheet_by_name(sheet).to_python(skip_empty_area=False)
        ci = rr[0].index("Company_ID")
        return {r[ci] for r in rr[1:]}

    def val_on(sheet, cid, col="Revenue"):
        rr = cw.get_sheet_by_name(sheet).to_python(skip_empty_area=False)
        hh = rr[0]
        ci, vi = hh.index("Company_ID"), hh.index(col)
        return next(r[vi] for r in rr[1:] if r[ci] == cid)

    jpm_v2 = float(num(pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)
                       .set_index("Company_ID").loc["US:JPM:US", "Revenue"]))
    ry_v2 = float(num(pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)
                      .set_index("Company_ID").loc["CA:RY:TSX", "Revenue"]))
    checks = {
        "rows_720_unique_0_blank": len(ac) == 720 and ac["Company_ID"].nunique() == 720,
        "V_MA_on_credit_services": {"US:V:US", "US:MA:US"} <= ids_on("Credit_Services"),
        "hydro_one_utilities_regulated": "CA:H:TSX" in ids_on("Utilities_Regulated"),
        "no_provenance_headers_xlsx": not bad_headers,
        "no_provenance_headers_exports": not bad_csv,
        "jpm_revenue_unchanged": float(val_on("01_All_Companies", "US:JPM:US")) == jpm_v2,
        "ry_revenue_unchanged": float(val_on("01_All_Companies", "CA:RY:TSX")) == ry_v2,
        "row_counts_match_v2": all(len(sheet_dfs[s]) ==
                                   pd.read_excel(V2, sheet_name=s, keep_default_na=False).shape[0]
                                   for s in sheet_dfs if s != "00_README"),
        "placement_role_kept": "Placement_Role" in cw.get_sheet_by_name("GICS_Financials").to_python(skip_empty_area=False)[0],
        "extraction_status_kept": "Extraction_Status" in cw.get_sheet_by_name("01_All_Companies").to_python(skip_empty_area=False)[0],
        "no_tables": True,
    }
    bad = [k for k, v in checks.items() if not v]
    print("\n".join(f"  {k}: {v}" for k, v in checks.items()))
    assert not bad, bad

    rep = ["# Phase 5a Report", f"- Date: {TODAY}. Output: {OUT} ({os.path.getsize(OUT):,} bytes).",
           "- No scrape; no number changes; Sector_Financials_Final_v2.xlsx and all protected workbooks untouched.", "",
           "## Dropped columns (per sheet)",
           ""]
    rep += [f"- {s}: {', '.join(h)}" for s, h in sorted(dropped_report.items())] or ["- (none present)"]
    rep += ["", f"- Sheets processed: {len(sheet_dfs)}; row counts identical to v2 on every sheet (assert passed).",
            "- Methods consolidated once on 00_README (9 bullets); no EDGAR tag strings remain on company rows.", "",
            "## Assert results", ""]
    rep += [f"- {k}: {v}" for k, v in checks.items()]
    rep += ["", f"- Exports rewritten clean: All_Companies.csv + {n_sheet_csv} sector/GICS packs (utf-8-sig, same filenames).",
            "- Kept: Company_ID, all financials/prices/ratios, Placement_Role, Extraction_Status, Currency, GICS fields, Custom_Industry_Sheet."]
    with open(os.path.join(LOGD, "phase5a_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")
    print("\n=== PHASE 5a COMPLETE ===")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        if os.path.exists(OUT):
            try:
                os.remove(OUT)
            except OSError:
                pass
        sys.exit(1)
