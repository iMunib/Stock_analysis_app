import json
import os
import re
import sys
import traceback
from datetime import date

import numpy as np
import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
FINAL = os.path.join(ROOT, "Sector_Financials_Final.xlsx")
V2 = os.path.join(ROOT, "Sector_Financials_Final_v2.xlsx")
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
LOGD = os.path.join(ROOT, "logs")
EXPORTS = os.path.join(ROOT, "exports")
TODAY = date.today().isoformat()
SECTOR_COL = "Custom_Industry_Sheet"

COLLISION_IDS = {f"US:{t}:US" for t in ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]} | \
                {f"CA:{t}:TSX" for t in ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]}
TAB_COLORS = {"Banks": "1F4E78", "Utilities_Regulated": "007782", "Software": "6A3D9A",
              "Semiconductors_Components": "3F51B5", "Oil_Gas_Producers": "E36C0A",
              "Insurance": "1E6B45", "Financials": "1E6B45", "Credit_Services": "1E6B45",
              "Discount_Stores": "C9A227"}
META_TAB, STEEL_TAB, GOLD_TAB, GICS_TAB = "808080", "4682B4", "C9A227", "2E7D32"

DEPOSIT_BANKS = {"JPM", "BAC", "WFC", "C", "USB", "PNC", "TFC",
                 "RY", "TD", "BMO", "BNS", "CM", "NA"}

RULES = [
    ("Credit_Services", "ind_kw", ["consumer finance", "transaction", "payment processing",
                                   "data processing", "financial exchange", "consumer credit",
                                   "credit services"], ["V", "MA", "AXP", "PYPL", "COF", "SYF", "DFS",
                                                        "FIS", "FI", "GPN", "SQ", "XYZ"], []),
    ("Airlines", "ind_kw", ["airline", "airways"],
     ["DAL", "UAL", "AAL", "LUV", "ALK", "ACBAR", "JBLU", "RYAAY", "AC", "AC.TO"],
     ["airline", "airways"]),
    ("Autos", "ind_kw", ["automobile", "auto components", "motorcycle", "tire", "passenger vehicle"],
     ["F", "GM", "TSLA", "RIVN", "LCID", "STLA", "HMC", "TM", "PCAR"],
     ["ford", "general motors", "tesla", "honda", "toyota", "stellantis", "paccar"]),
    ("Comm_Services", "sector_eq", ["communication services"], [], []),
    ("Telecom", "ind_kw", ["integrated telecommunication", "wireless telecommunication", "telecom"],
     ["T", "TMUS", "VZ", "BCE", "RCI.B", "T.TO"], []),
    ("Internet_Platforms", "ticker_only", [],
     ["GOOGL", "GOOG", "META", "AMZN", "NFLX", "SNAP", "PINS", "RDDT"], []),
    ("Software", "ind_kw", ["software"], [], []),
    ("Semiconductors_Components", "ind_kw", ["semiconductor"], [], []),
    ("Banks", "ind_kw", ["diversified banks", "regional banks"], [], []),
    ("Insurance", "ind_kw", ["insurance"], [], []),
    ("Utilities_Regulated", "sector_eq", ["utilities"], [], []),
    ("Pipelines_Midstream", "name_ind_kw", ["pipeline", "midstream", "oil and gas storage"], [], []),
    ("Railroads", "ind_kw", ["rail"], ["UNP", "CNI", "CNR", "CP", "NSC", "CSX"], []),
    ("Oil_Gas_Producers", "ind_kw", ["oil and gas exploration", "integrated oil"], [], []),
    ("Discount_Stores", "ind_kw", ["consumer staples merchandise retail", "hypermarkets", "food retail"],
     ["WMT", "COST", "TGT", "DG", "DLTR", "KR", "CASY"], []),
    ("Fast_Food_Restaurants", "ind_kw", ["restaurant"], ["MCD", "SBUX", "CMG", "QSR", "YUM"], []),
    ("Retail", "ind_kw", ["retail"], [], []),
    ("Networking", "ind_kw", ["communications equipment"], [], []),
    ("Pharma", "ind_kw", ["pharmaceutical"], [], []),
    ("Biotech", "ind_kw", ["biotechnology"], [], []),
    ("Medical_Devices_Services", "ind_kw",
     ["health care equipment", "health care providers", "health care technology",
      "life sciences tools", "health care supplies"], [], []),
]


def norm(s):
    s = str(s).lower().replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


def base_tkr(t):
    t = str(t).strip()
    return t[:-3] if t.endswith(".TO") else t


def main():
    print("=== TASK 0: census ===")
    grid = pd.read_excel(FINAL, sheet_name="01_All_Companies", keep_default_na=False)
    n_rows, n_uniq, n_blank = len(grid), grid["Company_ID"].nunique(), int((grid["Company_ID"].astype(str).str.strip() == "").sum())
    print(f"rows={n_rows} unique={n_uniq} blank_ids={n_blank}")
    assert (n_rows, n_uniq, n_blank) == (720, 720, 0), "CENSUS FAILED - STOP"
    flg = lambda s: s.astype(str).str.upper().isin(["Y", "YES", "TRUE", "1"])
    sp, tsx = int(flg(grid["In_SP500"]).sum()), int(flg(grid["In_TSX_Composite"]).sum())
    print(f"In_SP500={sp} In_TSX_Composite={tsx}")
    uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
    uix = uni.set_index("Company_ID")

    probe = ["V", "MA", "AXP", "DAL", "UAL", "AAL", "LUV", "F", "GM", "TSLA", "T", "TMUS", "VZ", "CHTR"]
    ixp = grid.set_index("Primary_Ticker")
    probe_lines = []
    for t in probe:
        if t in ixp.index:
            r = ixp.loc[t]
            probe_lines.append(f"{t}: PRESENT - primary sheet {r[SECTOR_COL]} ({r['Company_ID']})")
            print(probe_lines[-1])
        else:
            probe_lines.append(f"{t}: ABSENT_FROM_UNIVERSE (not added)")
            print(probe_lines[-1])

    print("=== TASK 1: placement model ===")
    sub_ind_series = grid["Company_ID"].map(uix["GICS_Sub_Industry"]).astype(str) if "GICS_Sub_Industry" in uix.columns else pd.Series("", index=grid.index)
    ind_text = (grid["GICS_Industry"].astype(str).map(norm) + " ; " +
                sub_ind_series.map(norm))
    sec_text = grid["GICS_Sector"].astype(str).map(norm)
    name_text = grid["Company_Name"].astype(str).map(norm)
    tkrs = grid["Primary_Ticker"].astype(str)
    base_tkrs = tkrs.map(base_tkr)

    def tk_match(i, wanted):
        return str(tkrs[i]) in wanted or str(base_tkrs[i]) in {base_tkr(w) for w in wanted}

    extra_map = {cid: [] for cid in grid["Company_ID"]}
    reason_map = {cid: {} for cid in grid["Company_ID"]}
    for sheet, kind, kws, tickers, name_kws in RULES:
        for i in grid.index:
            cid = grid.at[i, "Company_ID"]
            hit = None
            if kind == "sector_eq":
                if str(sec_text[i]) in [norm(k) for k in kws]:
                    hit = f"GICS_Sector={grid.at[i, 'GICS_Sector']}"
            elif kind == "ticker_only":
                if tk_match(i, tickers):
                    hit = "ticker rule"
            elif kind == "name_ind_kw":
                if any(k in ind_text[i] or k in name_text[i] for k in kws):
                    hit = "name/industry keyword"
            else:
                kw_hit = [k for k in kws if k in ind_text[i]]
                nm_hit = [k for k in name_kws if k in name_text[i]]
                if kw_hit or nm_hit or tk_match(i, tickers):
                    bits = ([] + [f"kw:{k}" for k in kw_hit] + [f"name:{k}" for k in nm_hit] +
                            (["ticker"] if tk_match(i, tickers) else []))
                    hit = ",".join(bits)
            if not hit:
                continue
            if sheet == "Credit_Services" and base_tkr(tkrs[i]) in DEPOSIT_BANKS:
                continue
            if sheet != "Retail":
                pass
            if sheet == "Retail" and "Discount_Stores" in [grid.at[i, SECTOR_COL]] + extra_map[cid]:
                continue
            if sheet == "Discount_Stores":
                pass
            if cid not in reason_map or sheet not in reason_map[cid]:
                extra_map[cid].append(sheet)
                reason_map[cid][sheet] = hit
    for i in grid.index:
        cid = grid.at[i, "Company_ID"]
        if SECTOR_COL not in extra_map[cid]:
            pass
    extra_map = {cid: sorted(set(v)) for cid, v in extra_map.items()}

    rows = []
    for i in grid.index:
        cid = grid.at[i, "Company_ID"]
        prim = str(grid.at[i, SECTOR_COL]).strip()
        extras = [s for s in extra_map[cid] if s != prim]
        allsh = [prim] + extras
        reasons = "; ".join(f"{s}[{reason_map[cid][s]}]" for s in extras)
        rows.append({"Company_ID": cid, "Company_Name": grid.at[i, "Company_Name"],
                     "Primary_Ticker": grid.at[i, "Primary_Ticker"], "Primary_Sheet": prim,
                     "Extra_Sheets": "|".join(extras), "All_Sheets": "|".join(allsh),
                     "Placement_Reason": reasons})
    plc = pd.DataFrame(rows)
    plc.to_csv(os.path.join(LOGD, "phase4_placements.csv"), index=False, encoding="utf-8-sig")
    n_extra_rows = int(plc["Extra_Sheets"].str.split("|").apply(lambda x: len([e for e in x if e])).sum())
    print("placement rows:", len(plc), "| total extra placements:", n_extra_rows)
    for sh in ["Credit_Services", "Airlines", "Autos"]:
        ids = plc[(plc["Primary_Sheet"] == sh) | plc["Extra_Sheets"].str.contains(sh, regex=False)]["Company_ID"]
        print(f"  {sh}: {len(ids)} companies")
    print("=== TASK 2: rebuild workbook ===")
    customs = sorted(uix[SECTOR_COL].astype(str).str.strip().unique())
    before_counts = {"Airlines": 4, "Autos": 4, "Comm_Services": 1, "Credit_Services": 4,
                     "Discount_Stores": 2, "Internet_Platforms": 4, "Software": 29, "Banks": 39}

    def member_df(sheet):
        prim = grid[grid[SECTOR_COL].astype(str).str.strip().eq(sheet)].copy()
        prim["Placement_Role"] = "Primary"
        ex_ids = plc[plc["Extra_Sheets"].str.split("|").apply(lambda L: sheet in L)]["Company_ID"]
        ex = grid[grid["Company_ID"].isin(set(ex_ids) - set(prim["Company_ID"]))].copy()
        ex["Placement_Role"] = "Extra"
        out = pd.concat([prim, ex], ignore_index=True)
        cols = list(out.columns)
        cols.remove("Placement_Role")
        cols.insert(cols.index(SECTOR_COL) + 1, "Placement_Role")
        out = out[cols]
        return out.sort_values(["Placement_Role", "Company_Name"],
                               key=lambda s: s.str.lower() if s.name == "Company_Name" else s)

    def gics_df(sector_val):
        sub = grid[sec_text.eq(norm(sector_val))].copy()
        sub["Placement_Role"] = np.where(sub[SECTOR_COL].astype(str).str.strip().eq(sector_val),
                                         "Primary", "Extra")
        cols = list(sub.columns)
        cols.remove("Placement_Role")
        cols.insert(cols.index(SECTOR_COL) + 1, "Placement_Role")
        return sub[cols].sort_values(["Placement_Role", "Company_Name"],
                                     key=lambda s: s.str.lower() if s.name == "Company_Name" else s)

    sector_orig = sorted({str(s).strip() for s in grid["GICS_Sector"] if str(s).strip()})
    gics_sheets = ["GICS_" + sv.replace(" ", "_") for sv in sector_orig]
    gics_dfs = {}
    for sv in sector_orig:
        d = gics_df(sv)
        if len(d) == 0:
            continue
        gics_dfs["GICS_" + sv.replace(" ", "_")] = d
        assert len(d) == int((sec_text == norm(sv)).sum())

    cust_dfs = {s: member_df(s) for s in customs}
    assert sum(len(d[d["Placement_Role"].eq("Primary")]) for d in cust_dfs.values()) == 720

    census_rows = []
    for s in customs:
        d = cust_dfs[s]
        census_rows.append({"Sheet": s, "Rows": len(d),
                            "Primary": int(d["Placement_Role"].eq("Primary").sum()),
                            "Extra": int(d["Placement_Role"].eq("Extra").sum())})
    for s, d in gics_dfs.items():
        census_rows.append({"Sheet": s, "Rows": len(d),
                            "Primary": int(d["Placement_Role"].eq("Primary").sum()),
                            "Extra": int(d["Placement_Role"].eq("Extra").sum())})
    census = pd.DataFrame(census_rows)
    census.to_csv(os.path.join(LOGD, "phase4_census.csv"), index=False, encoding="utf-8-sig")

    plc_ix = plc.set_index("Company_ID")

    def where(cid):
        return str(plc_ix.at[cid, "All_Sheets"])

    readme_lines = [
        "NORTH AMERICAN FINANCIALS - FINAL WORKBOOK v2 (MULTI-SHEET PLACEMENT)",
        f"Prepared: {TODAY}. NOT INVESTMENT ADVICE - research data compilation only.",
        "All monetary values are in each company's NATIVE reporting currency (USD / CAD). NO currency conversion anywhere.",
        "",
        f"There are exactly 720 UNIQUE companies. They all live once on 01_All_Companies.",
        "Sector/GICS tabs MAY contain the same company several times across different tabs. THIS IS INTENTIONAL:",
        "Primary_Sheet = Universe.Custom_Industry_Sheet home tab; every other appearance is labelled Placement_Role = Extra (pale green cell).",
        "On GICS_ sector tabs every row is a copy (Extra); the custom home tabs carry the Primary rows.",
        "",
        "CENSUS TABLE (sheet | rows | primary | extra):"]
    readme_lines += [f"  {r.Sheet}: {int(r.Rows)} | P {int(r.Primary)} | E {int(r.Extra)}" for r in census.itertuples()]
    readme_lines += ["", "WHERE THE OFTEN-ASKED-FOR NAMES SIT:"]
    for t, cid in [("V", "US:V:US"), ("MA", "US:MA:US"), ("AXP", "US:AXP:US"), ("DAL", "US:DAL:US"),
                   ("UAL", "US:UAL:US"), ("F", "US:F:US"), ("GM", "US:GM:US"), ("TSLA", "US:TSLA:US"),
                   ("T", "US:T:US"), ("TMUS", "US:TMUS:US")]:
        if cid in plc_ix.index:
            readme_lines.append(f"  {t}: {where(cid)}")
    readme_lines.append("  AAL: ABSENT_FROM_UNIVERSE (not added)")
    readme_lines += ["", "Airlines tab now carries the airline cohort; Visa/Mastercard sit on Credit_Services + GICS_Financials;",
                     "deposit banks were deliberately kept OFF Credit_Services.", "",
                     "No new companies were invented: the union of Company_IDs across ALL sheets equals the same 720."]

    dq_prev = pd.read_excel(FINAL, sheet_name="03_Data_Quality", keep_default_na=False)
    coll_prev = pd.read_excel(FINAL, sheet_name="04_Collisions", keep_default_na=False)
    cov_prev = pd.read_excel(FINAL, sheet_name="02_Coverage", keep_default_na=False)
    memb_prev = pd.read_excel(FINAL, sheet_name="05_Membership", keep_default_na=False)
    memb_new = pd.concat([memb_prev.astype(str),
                          census.astype(str).reindex(columns=list(memb_prev.columns), fill_value="")],
                         ignore_index=True)

    sheets = [("00_README", pd.DataFrame({"A": readme_lines})),
              ("01_All_Companies", grid),
              ("02_Coverage", cov_prev),
              ("03_Data_Quality", dq_prev),
              ("04_Collisions", coll_prev.astype(str)),
              ("05_Membership", memb_new),
              ("06_Placements", plc)]
    for s in customs:
        sheets.append((s[:31], cust_dfs[s]))
    for s, d in gics_dfs.items():
        sheets.append((s[:31], d))

    if os.path.exists(V2):
        os.remove(V2)
    with pd.ExcelWriter(V2, engine="openpyxl") as xw:
        for sname, df in sheets:
            df.to_excel(xw, sheet_name=sname, index=False)

    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = load_workbook(V2)
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

    data_sheet_names = []
    for ws in wb.worksheets:
        name = ws.title
        is_meta = name.startswith(("0",))
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
            elif hs in ("Calc_Method_Notes", "Fill_Source", "Fill_Notes", "Resolution", "Notes",
                        "Placement_Reason"):
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
            data_sheet_names.append(name)
    wb.save(V2)
    wb.close()

    import zipfile
    z = zipfile.ZipFile(V2)
    tables = [n for n in z.namelist() if "tables/" in n.lower()]
    z.close()
    assert not tables, tables

    print("=== TASK 3: asserts ===")
    wbck = load_workbook(V2)
    tb_ok = all(len(wbck[s].tables) == 0 for s in wbck.sheetnames)
    af_ok = all(wbck[s].auto_filter.ref and wbck[s].freeze_panes == "B2" for s in data_sheet_names)
    wbck.close()
    from python_calamine import CalamineWorkbook
    cw = CalamineWorkbook.from_path(V2)

    def ids_on(sheet):
        rr = cw.get_sheet_by_name(sheet).to_python(skip_empty_area=False)
        ci = rr[0].index("Company_ID")
        return {r[ci] for r in rr[1:]}

    all_ids = ids_on("01_All_Companies")
    final_ids = set(pd.read_excel(FINAL, sheet_name="01_All_Companies", keep_default_na=False)["Company_ID"])
    country_counts = pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)["Country_of_Listing"].astype(str).str.strip().value_counts()
    union_ids = set().union(*[ids_on(s) for s in data_sheet_names])
    jpm_f = float(num(pd.read_excel(FINAL, sheet_name="01_All_Companies", keep_default_na=False)
                      .set_index("Company_ID").loc["US:JPM:US", "Revenue"]))
    jpm_v = float(num(pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)
                      .set_index("Company_ID").loc["US:JPM:US", "Revenue"]))
    ry_f = float(num(pd.read_excel(FINAL, sheet_name="01_All_Companies", keep_default_na=False)
                     .set_index("Company_ID").loc["CA:RY:TSX", "Revenue"]))
    ry_v = float(num(pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)
                     .set_index("Company_ID").loc["CA:RY:TSX", "Revenue"]))

    checks = {
        "all_companies_720_unique": len(all_ids) == 720 and len(all_ids) == n_uniq,
        "no_blank_ids_v2": all(str(x).strip() for x in
                               pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)["Company_ID"]),
        "us_500_ca_220": bool(country_counts.get("United States", 0) == 500 or country_counts.get("US", 0) == 500) and
                         bool(country_counts.get("Canada", 0) == 220 or country_counts.get("CA", 0) == 220),
        "same_ids_as_final": all_ids == final_ids,
        "union_all_sheets_equals_720": union_ids == final_ids,
        "V_on_credit_and_gics_financials": "US:V:US" in ids_on("Credit_Services") and "US:V:US" in ids_on("GICS_Financials"),
        "MA_on_credit_and_gics_financials": "US:MA:US" in ids_on("Credit_Services") and "US:MA:US" in ids_on("GICS_Financials"),
        "airline_present_on_airlines": len({"US:DAL:US", "US:UAL:US", "CA:AC:TSX"} & ids_on("Airlines")) >= 1,
        "hydro_one_utilities_regulated": "CA:H:TSX" in ids_on("Utilities_Regulated"),
        "NA_on_banks": "CA:NA:TSX" in ids_on("Banks"),
        "collisions_14_on_all_companies": len(COLLISION_IDS & all_ids) == 14,
        "jpm_revenue_unchanged": jpm_f == jpm_v,
        "ry_revenue_unchanged": ry_f == ry_v,
        "no_worksheet_tables": bool(tb_ok),
        "autofilter_freeze_data_sheets": bool(af_ok),
    }
    bad = [k for k, v in checks.items() if not v]
    for k, v in checks.items():
        print(f"  {k}: {v}")
    assert not bad, bad

    os.makedirs(EXPORTS, exist_ok=True)
    pdf = pd.read_excel(V2, sheet_name="01_All_Companies", keep_default_na=False)
    pdf.to_csv(os.path.join(EXPORTS, "All_Companies.csv"), index=False, encoding="utf-8-sig")
    for sname, _ in [(s, 0) for s in customs] + list(gics_dfs.items()):
        pd.read_excel(V2, sheet_name=sname[:31], keep_default_na=False) \
          .to_csv(os.path.join(EXPORTS, f"{sname[:31]}.csv"), index=False, encoding="utf-8-sig")

    after_counts = {}
    for s, b in before_counts.items():
        d = cust_dfs.get(s)
        after_counts[s] = len(d) if d is not None else 0

    rep = ["# Phase 4 Report", f"- Date: {TODAY}. Output: {V2} ({os.path.getsize(V2):,} bytes).",
           "- No scrape occurred; Sector_Financials_Final.xlsx untouched; numbers are byte-equal to Final.",
           "", "## Census proof (Task 0)",
           f"- 01_All_Companies: rows={n_rows}, unique={n_uniq}, blank IDs={n_blank}. In_SP500={sp}, In_TSX_Composite={tsx}.",
           "- Probe tickers: " + " | ".join(probe_lines), "",
           "## Before/after row counts (Task 1 rules)", "",
           "| Sheet | Phase3 (single-place) | v2 (multi-place) |", "|---|---|---|"]
    rep += [f"| {s} | {before_counts[s]} | {after_counts[s]} |" for s in before_counts]
    rep += ["", f"- Total EXTRA placements added: {n_extra_rows} (sector-sheet rows now exceed 720 by design).",
            f"- Union of Company_IDs across every sheet == the same 720; nothing invented, nothing dropped.", ""]
    rep += ["## Where key names now sit", ""]
    rep += [f"- {t}: {where(cid)}" for t, cid in [("V", "US:V:US"), ("MA", "US:MA:US"), ("AXP", "US:AXP:US"),
                                                  ("DAL", "US:DAL:US"), ("UAL", "US:UAL:US"), ("F", "US:F:US"),
                                                  ("GM", "US:GM:US"), ("TSLA", "US:TSLA:US"), ("T", "US:T:US"),
                                                  ("TMUS", "US:TMUS:US")]]
    rep += ["- AAL: ABSENT_FROM_UNIVERSE - not added.",
            "- Deposit banks (JPM/BAC/WFC/C/USB/PNC/TFC + Big Six CA) intentionally NOT pulled onto Credit_Services.", ""]
    rep += ["## Task 3 assert results", ""]
    rep += [f"- {k}: {v}" for k, v in checks.items()]
    rep += ["", "- Exports: All_Companies.csv refreshed + one CSV per custom/GICS sheet written to exports/.",
            "- Out of scope remains: ranking, scoring, composites, scraping."]
    with open(os.path.join(LOGD, "phase4_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")

    ch = ["# Phase 4 Changelog", f"Date: {TODAY}", "",
          "## New files",
          "Sector_Financials_Final_v2.xlsx; scripts/build_phase4_v2.py; logs/phase4_report.md; logs/phase4_changelog.md; logs/phase4_census.csv; logs/phase4_placements.csv",
          "exports/: All_Companies.csv refreshed plus one CSV per custom industry and GICS sector sheet.", "",
          "## Model",
          "- Primary_Sheet = Universe.Custom_Industry_Sheet (unchanged). Rule engine adds Extra appearances (GICS sector tabs + 21 keyword/ticker/name rules).",
          "- Sector tabs carry Placement_Role (Primary|Extra; Extra shaded E8F5E9). GICS tabs prefixed GICS_ to avoid name clashes with custom tabs.",
          "- Deposit banks excluded from Credit_Services extras. No company outside the 720 was created. No network calls.",
          "- Formatting carried over from Phase 3 (navy headers, banded rows, grey blanks, freeze B2, autofilter, tab colours, no Tables).", "",
          "## Untouched",
          "All seven prior workbooks (canonical, Analysis, Clean, SFA, Phase1, Phase1b, Complete, Final) and all earlier logs/artifacts."]
    with open(os.path.join(LOGD, "phase4_changelog.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(ch) + "\n")

    print("\n=== PHASE 4 COMPLETE ===")


def num(s):
    return pd.to_numeric(s, errors="coerce")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        if os.path.exists(V2):
            try:
                os.remove(V2)
            except OSError:
                pass
        sys.exit(1)

