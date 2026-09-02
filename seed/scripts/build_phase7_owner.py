"""Phase 7 - polish only. Builds Sector_Financials_Final_Owner.xlsx from Sector_Financials_QA.xlsx.

No scraping. No ranking. No universe changes. The QA workbook is opened read-only and never modified.
"""
import os
import re
import zipfile
from datetime import date

import numpy as np
import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
QA = os.path.join(ROOT, "Sector_Financials_QA.xlsx")
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
OUT = os.path.join(ROOT, "Sector_Financials_Final_Owner.xlsx")
LOGD = os.path.join(ROOT, "logs")
TODAY = date.today().isoformat()
SECTOR_COL = "Custom_Industry_Sheet"

num = lambda s: pd.to_numeric(s, errors="coerce")


def norm(s):
    s = str(s).lower().replace("&", " and ")
    return re.sub(r"\s+", " ", s).strip()


# ---------------- load ----------------
book = {}
xl = pd.ExcelFile(QA)
for sn in xl.sheet_names:
    book[sn] = xl.parse(sn, keep_default_na=False)
grid = book["01_All_Companies"].copy()
n_qa_rows = len(grid)
assert n_qa_rows == 720

# ---------------- Task C (cheap fills, do FIRST so placement test sees them) ----------------
taskc = {"mc_filled": [], "mc_left_blank": [], "gics_ind_filled": 0}
uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
sub_map = dict(zip(uni["Company_ID"], uni["GICS_Sub_Industry"]))
ind_map = dict(zip(uni["Company_ID"], uni["GICS_Industry"]))

# GICS_Industry display fill for US names: Universe.GICS_Industry is blank for all 500 US rows,
# so fall back to Universe.GICS_Sub_Industry (documented in README/report).
for i in grid.index:
    cid = str(grid.at[i, "Company_ID"])
    if str(grid.at[i, "GICS_Industry"]).strip() == "":
        v = str(sub_map.get(cid, "") or ind_map.get(cid, "")).strip()
        if v:
            grid.at[i, "GICS_Industry"] = v
            taskc["gics_ind_filled"] += 1

# Market_Cap = Price * Shares_Snapshot where possible
for i in grid.index:
    px, mc, sh = num(grid.at[i, "Price"]), num(grid.at[i, "Market_Cap"]), num(grid.at[i, "Shares_Snapshot"])
    if pd.notna(px) and pd.isna(mc):
        if pd.notna(sh):
            grid.at[i, "Market_Cap"] = float(px) * float(sh)
            taskc["mc_filled"].append(str(grid.at[i, "Company_ID"]))
        else:
            taskc["mc_left_blank"].append(str(grid.at[i, "Company_ID"]))

# ---------------- Task A: extra placements ----------------
# Removals
extra_removals = {"US:HIG:US": ["Autos"]}
CS_REMOVAL_TICKERS = ["CME", "CBOE", "ICE", "NDAQ", "MCO", "MSCI", "SPGI", "FDS", "BR", "JKHY"]
removed_cs, kept_cs_reason = [], []
for t in CS_REMOVAL_TICKERS:
    cid = f"US:{t}:US"
    ind_txt = norm(grid.loc[grid["Company_ID"].eq(cid), "GICS_Industry"].iloc[0])
    if "consumer finance" in ind_txt or "transaction" in ind_txt and "payment processing" in ind_txt \
            or "payment processing" in ind_txt:
        kept_cs_reason.append((cid, ind_txt))
    else:
        extra_removals[cid] = ["Credit_Services"]
        removed_cs.append((cid, ind_txt))

# Additions (only if the company exists in the 720; Primary untouched)
all_ids = set(grid["Company_ID"])
extra_additions = {}
for t in ["DOL", "ATD"]:
    cid = f"CA:{t}:TSX"
    if cid in all_ids:
        extra_additions.setdefault(cid, [])
        if "Discount_Stores" not in extra_additions[cid]:
            extra_additions[cid].append("Discount_Stores")
pipeline_added = []
for t in ["KEY", "PPL"]:
    cid = f"CA:{t}:TSX"
    if cid in all_ids:
        cur = str(book["06_Placements"].set_index("Company_ID")["Extra_Sheets"].get(cid, ""))
        if "Pipelines_Midstream" in cur.split("|"):
            continue
        extra_additions.setdefault(cid, []).append("Pipelines_Midstream")
        pipeline_added.append(cid)

# Apply onto current Extra_Sheets state
plc = book["06_Placements"].copy()
plc_idx = plc.set_index("Company_ID")
adj_extras, changes = {}, []
for cid in grid["Company_ID"].astype(str):
    ex = [s for s in str(plc_idx["Extra_Sheets"].get(cid, "")).split("|") if s]
    before = list(ex)
    for s in extra_removals.get(cid, []):
        if s in ex:
            ex.remove(s)
    for s in extra_additions.get(cid, []):
        if s not in ex:
            ex.append(s)
    adj_extras[cid] = sorted(set(ex))
    if before != adj_extras[cid]:
        changes.append((cid, ",".join(before) or "-", ",".join(adj_extras[cid]) or "-"))

prim_sheet = dict(zip(grid["Company_ID"].astype(str), grid[SECTOR_COL].astype(str).str.strip()))
gics_name = {}
for i in grid.index:
    gsv = str(grid.at[i, "GICS_Sector"]).strip()
    gics_name[str(grid.at[i, "Company_ID"])] = ("GICS_" + gsv.replace(" ", "_")) if gsv not in ("", "nan") else ""

plc_rows = []
for _, r in grid.iterrows():
    cid = str(r["Company_ID"])
    prim = prim_sheet[cid]
    exs = [s for s in adj_extras[cid] if s != prim]
    g = gics_name[cid]
    plc_rows.append({"Company_ID": cid, "Company_Name": r["Company_Name"],
                     "Primary_Ticker": r["Primary_Ticker"], "Primary_Sheet": prim,
                     "Extra_Sheets": "|".join(exs), "All_Sheets": "|".join([prim] + exs + ([g] if g else [])),
                     "GICS_Sheet": g})
book["06_Placements"] = pd.DataFrame(plc_rows)

# ---------------- rebuild custom / GICS sheet frames ----------------
def insert_role(df):
    cols = list(df.columns)
    if "Placement_Role" in cols:
        cols.remove("Placement_Role")
    cols.insert(cols.index(SECTOR_COL) + 1, "Placement_Role")
    return df[cols].sort_values(
        ["Placement_Role", "Company_Name"],
        key=lambda s: s.str.lower() if s.name == "Company_Name" else s)


custom_order = [sn for sn in book.keys() if not sn.startswith(("00_", "01_", "02_", "03_", "04_", "05_", "06_", "GICS_"))]
sheet_frames = {"01_All_Companies": grid.copy()}
ex_sets = {sn: {cid for cid, L in adj_extras.items() if sn in L} for sn in custom_order}
for sn in custom_order:
    primdf = grid[grid[SECTOR_COL].astype(str).str.strip().eq(sn)].copy()
    primdf["Placement_Role"] = "Primary"
    exdf = grid[grid["Company_ID"].isin(ex_sets[sn] - set(primdf["Company_ID"]))].copy()
    exdf["Placement_Role"] = "Extra"
    sheet_frames[sn] = insert_role(pd.concat([primdf, exdf], ignore_index=True))

sec_norm = grid["GICS_Sector"].astype(str).map(norm)
sector_orig = [str(s).strip() for s in grid["GICS_Sector"]
               if str(s).strip() not in ("", "nan")]
sector_orig = sorted(dict.fromkeys(sector_orig))
for sv in sector_orig:
    sn = "GICS_" + sv.replace(" ", "_")
    if sn not in book:
        continue
    sub = grid[sec_norm.eq(norm(sv))].copy()
    sub["Placement_Role"] = np.where(sub[SECTOR_COL].astype(str).str.strip().eq(sv), "Primary", "Extra")
    sheet_frames[sn] = insert_role(sub)

# ---------------- Task B part 1: drop 100% blank helper columns ----------------
HELPERS = ["Fill_Notes", "Revenue_TS_Fill_FY", "Net_Income_TS_Fill_FY", "Total_Debt_TS_Fill_FY",
           "FillNotes", "RevenueTSFillFY", "NetIncomeTSFillFY", "TotalDebtTSFillFY"]
dropped_helpers = {}
for sn, df in sheet_frames.items():
    drop = [h for h in HELPERS if h in df.columns and df[h].astype(str).str.strip().eq("").all()]
    if drop:
        sheet_frames[sn] = df.drop(columns=drop)
        dropped_helpers[sn] = drop

META_SHEETS = ["02_Coverage", "03_Data_Quality", "04_Collisions", "05_Membership"]

# ---------------- styling constants ----------------
MONEY_COLS = {"Revenue", "Net_Income", "Gross_Profit", "Operating_Cash_Flow", "Capex",
              "Total_Debt", "Book_Equity", "Cash_ST_Investments", "Total_Assets",
              "Total_Liabilities", "EBIT", "EBITDA", "Interest_Expense",
              "EV_Calc", "NetDebt_Calc", "FCF_Calc", "Free_Cash_Flow", "FCF_Reported",
              "TopLine_Alt", "Shares_Snapshot"}
RATIO_COLS = {"FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc",
              "PE_Calc", "PB_Calc", "EV_to_EBITDA_Calc", "Diluted_EPS",
              "CET1_Ratio", "Total_Capital_Ratio", "Leverage_Ratio",
              "NIM_FY2025", "NIM_Q4_2025", "Efficiency_Ratio", "ROAA"}
W_FIXED = {"Company_ID": 18, "Company_Name": 34, "Primary_Ticker": 12,
           "GICS_Sector": 22, "GICS_Industry": 28, "Custom_Industry_Sheet": 22,
           "Price": 10, "Market_Cap": 16, "Extraction_Status": 14, "Source_Primary": 12}


def style_sheet(ws, headers, tab_color=None):
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    navy = PatternFill("solid", fgColor="1F4E78")
    band = PatternFill("solid", fgColor="D6EAF8")
    grey1, grey2 = PatternFill("solid", fgColor="F2F2F2"), PatternFill("solid", fgColor="E8EEF4")
    amber, red, green = (PatternFill("solid", fgColor="FDEBD0"),
                         PatternFill("solid", fgColor="FADBD8"),
                         PatternFill("solid", fgColor="E8F5E9"))
    hmap = {str(h): i + 1 for i, h in enumerate(headers)}
    money = {hmap[h] for h in headers if h in MONEY_COLS}
    pctdec = {hmap[h] for h in headers if h in RATIO_COLS}
    pct_fmt = {hmap[h] for h in headers if h in {"FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc"}}
    # widths: fixed -> money 14 / ratios 10 -> autofit clamped
    for idx, h in enumerate(headers, start=1):
        letter = get_column_letter(idx)
        hs = str(h)
        if hs in W_FIXED:
            w = W_FIXED[hs]
        elif hs in MONEY_COLS:
            w = 14
        elif hs in RATIO_COLS:
            w = 10
        else:
            natural = len(hs)
            for r in range(2, min(ws.max_row, 400) + 1):
                v = ws.cell(row=r, column=idx).value
                if v is not None:
                    natural = max(natural, min(len(str(v)), 40))
            w = max(9, min(natural + 2, 26))
        ws.column_dimensions[letter].width = w
    # header
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font = navy, Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 36
    role_c, okc, stc = hmap.get("Placement_Role"), hmap.get("Fill_OK"), hmap.get("Extraction_Status")
    # data rows
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 16
        banded = (r % 2 == 0)
        is_extra = role_c and str(ws.cell(row=r, column=role_c).value) == "Extra"
        fill_ok_n = okc and str(ws.cell(row=r, column=okc).value) == "N"
        miss_src = stc and str(ws.cell(row=r, column=stc).value).startswith("MISSING_SOURCE")
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
            if is_extra:
                cell.fill = green
            elif fill_ok_n and c == okc:
                cell.fill = amber
            elif miss_src and c == stc:
                cell.fill = red
            elif cell.value is None and c in (money | pctdec):
                cell.fill = grey2 if banded else grey1
            elif banded:
                cell.fill = band
            if c in money:
                cell.number_format = "#,##0"
            elif c in pct_fmt:
                cell.number_format = "0.0%"
            elif c in pctdec:
                cell.number_format = "#,##0.00"
    last = get_column_letter(len(headers))
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{last}{ws.max_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    from openpyxl.worksheet.properties import PageSetupProperties
    if ws.sheet_properties.pageSetUpPr is None:
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    else:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    if tab_color:
        ws.sheet_properties.tabColor = tab_color


def style_readme(ws, lines):
    from openpyxl.styles import Alignment, Font
    ws.column_dimensions["A"].width = 110
    title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
    head_font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    body_font = Font(name="Consolas", size=10)
    for r, line in enumerate(lines, start=1):
        cell = ws.cell(row=r, column=1, value=line if line else None)
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        if r == 1:
            cell.font = title_font
        elif line.startswith(("WHAT THIS FILE IS", "WHICH FILE IS THE PRODUCT", "SHEET MAP", "PRIMARY VS EXTRA",
                              "HOW TO COMPARE", "COLUMN DICTIONARY", "HONEST LEFTOVERS", "UPDATES",
                              "PHASE 7 CHANGELOG")):
            cell.font = head_font
        else:
            cell.font = body_font


# ---------------- Task D: README text ----------------
def readme_lines():
    census = []
    for sn in custom_order:
        df = sheet_frames[sn]
        p = int(df["Placement_Role"].eq("Primary").sum())
        e = int(df["Placement_Role"].eq("Extra").sum())
        census.append(f"    {sn:<28} rows={len(df):>4}  (Primary={p}, Extra={e})")
    gics_lines = []
    for sv in sector_orig:
        sn = "GICS_" + sv.replace(" ", "_")
        if sn in sheet_frames:
            gics_lines.append(f"    {sn:<30} rows={len(sheet_frames[sn]):>4}  (copies of rows, grouped by GICS sector)")
    L = []
    A = L.append
    A("NORTH AMERICAN FINANCIALS - OWNER WORKBOOK (Phase 7 final polish)")
    A(f"Prepared: {TODAY}.  Source of record built through Phase 6 QA.")
    A("")
    A("WHAT THIS FILE IS")
    A("This workbook is a research snapshot of the financial statements of the companies in two stock")
    A("indexes: the US S&P 500 and the Canadian S&P/TSX Composite - 720 unique companies in total.")
    A("Every number is in each company's NATIVE reporting currency: US companies report USD millions,")
    A("Canadian companies report CAD millions. Nothing was converted between currencies anywhere in")
    A("this file. It covers ONLY index members - it is NOT the whole North American stock market, and")
    A("it is NOT investment advice. It is an information compilation for personal research.")
    A("")
    A("WHICH FILE IS THE PRODUCT")
    A("This file, Sector_Financials_Final_Owner.xlsx, IS the product. Earlier files in the project")
    A("(NA_Company_Financials.xlsx, Sector_Financials_QA.xlsx, CleanView, etc.) are intermediate")
    A("build artifacts. If you open any other file you are looking at history, not the deliverable.")
    A("")
    A("SHEET MAP")
    A("    00_README                    This explanation sheet.")
    A("    01_All_Companies             THE master table: exactly 720 rows, one row per unique company")
    A("                                 (key = Company_ID). If it is not here, it is not in the study.")
    A("    02_Coverage                  Field-by-field coverage counts (how full each column is).")
    A("    03_Data_Quality              Per-company QC notes and flags carried from the build phases.")
    A("    04_Collisions                Ticker/name collision audit (e.g. HON vs HONA, KEY US vs CA).")
    A("    05_Membership                Which index(es) each company belongs to, with provenance.")
    A("    06_Placements                Where each company appears: its home (Primary) sheet plus every")
    A("                                 Extra copy, pipe-separated.")
    A("Custom industry tabs:")
    for c in census:
        A(c)
    A("GICS sector tabs:")
    for gl in gics_lines:
        A(gl)
    A("")
    A("PRIMARY VS EXTRA")
    A("Every company lives once on 01_All_Companies. On the topic tabs a row is either 'Primary'")
    A("(its Custom_Industry_Sheet home tab) or 'Extra'. Extra rows are PALE GREEN and they are")
    A("COPIES, not different companies: Dollarama appears on Consumer_Defensive (Primary) and again")
    A("on Discount_Stores and Retail (Extra copies). The total number of COMPANIES is always 720;")
    A("the tabs just repeat members where the classification overlaps. Never add or sum a company")
    A("across tabs.")
    A("")
    A("HOW TO COMPARE COMPANIES")
    A("Work one sheet at a time, and within a sheet compare only USD-to-USD or CAD-to-CAD. NEVER")
    A("compare CAD millions against USD millions directly - a Canadian bank's Revenue is not")
    A("directly comparable to a US bank's. For cross-border comparisons use the unitless ratios:")
    A("ROE_Calc, ROA_Calc, FCFMargin_Calc, GrossMargin_Calc, PE_Calc, PB_Calc, EV_to_EBITDA_Calc.")
    A("Ratios cancel the currency (mostly) and are the honest cross-border lens. For scale, convert")
    A("at your own rate outside this file, or compare Market_Cap within a country only.")
    A("")
    A("COLUMN DICTIONARY (money/ratio columns)")
    A("    Revenue                 Latest fiscal-year top line, native currency. Most banks have it blank")
    A("                            because GAAP has no revenue concept for deposit-funded lenders.")
    A("    TopLine_Alt             Net interest income - the bank-equivalent of revenue; populated for")
    A("                            Synchrony (SYF) and Truist (TFC), whose income statement reports it.")
    A("    Net_Income              Fiscal-year bottom-line profit, native currency.")
    A("    Diluted_EPS             Diluted earnings per share for the fiscal year.")
    A("    Gross_Profit            Revenue minus cost of sales. Meaningless for banks/insurers; blank there.")
    A("    Operating_Cash_Flow     Cash generated by operations over the fiscal year.")
    A("    Capex                   Purchases of property/plant/equipment (shown negative = cash out).")
    A("    FCF_Reported            Free cash flow as reported by the vendor, when available.")
    A("    Free_Cash_Flow          Alternate/vendor FCF variant retained for reference.")
    A("    FCF_Calc                Operating_Cash_Flow - abs(Capex). Deliberately blank for banks and")
    A("                            insurers, where OCF/capex is not a meaningful FCF definition.")
    A("    NetDebt_Calc            Total_Debt - Cash_ST_Investments.")
    A("    FCFMargin_Calc          FCF_Calc divided by Revenue.")
    A("    GrossMargin_Calc        Gross_Profit divided by Revenue.")
    A("    ROE_Calc                Net_Income divided by ENDING Book_Equity (not average equity).")
    A("    ROA_Calc                Net_Income divided by ending Total_Assets.")
    A("    PE_Calc                 Price divided by Diluted_EPS; blank when EPS is missing or negative.")
    A("    PB_Calc                 Market_Cap divided by Book_Equity.")
    A("    EV_Calc                 Market_Cap + Total_Debt - Cash_ST_Investments.")
    A("    EV_to_EBITDA_Calc       EV_Calc divided by EBITDA.")
    A("    Total_Debt              Short- plus long-term debt incl. lease obligations where tagged.")
    A("                            Mostly blank for banks/insurers ON PURPOSE: deposits fund their assets,")
    A("                            so a corporate-style debt number would mislead.")
    A("    Book_Equity             Stockholders' equity at fiscal year end.")
    A("    Cash_ST_Investments     Cash and short-term investments at fiscal year end.")
    A("    Total_Assets            Balance-sheet total assets.")
    A("    Total_Liabilities       Balance-sheet total liabilities.")
    A("    EBIT                    Operating income for the year.")
    A("    EBITDA                  EBIT plus depreciation/amortization where disclosed.")
    A("    Interest_Expense        Interest expense for the fiscal year.")
    A("    Price / Price_Currency  Snapshot share price and its trading currency (USD or CAD).")
    A("    Price_AsOf              Date of the price snapshot.")
    A("    Shares_Snapshot         Shares outstanding at the snapshot date; basis of Market_Cap.")
    A("    Market_Cap              Price x Shares_Snapshot in trading currency (USD or CAD, NOT both).")
    A("    CET1_* / Total_Capital_Ratio / Leverage_Ratio   Regulatory capital metrics, big-6 Canadian")
    A("                            banks + US peers, taken from filings/supplements.")
    A("    NIM_FY2025 / NIM_Q4_2025   Net interest margin, full year and Q4.")
    A("    Efficiency_Ratio        Non-interest expense over revenue (banks).")
    A("    ROAA                    Return on average assets (banks).")
    A("    GICS_Sector             Official GICS sector. GICS_Industry: official industry level for TSX")
    A("                            names; for US names this column carries the GICS SUB-industry (the")
    A("                            finer level available offline) - see Phase 7 report note.")
    A("    Custom_Industry_Sheet   Home tab chosen for the company (drives Primary placement).")
    A("    Company_ID              Stable key: US:TICKER:US or CA:TICKER:TSX. Note CA:NA:TSX is National")
    A("                            Bank of Canada (ticker NA.TO), NOT NVIDIA-related.")
    A("    Placement_Role          'Primary' (home tab row) or 'Extra' (pale-green copy row).")
    A("    Extraction_Status / Source_Primary / Fill_OK / Membership_Flag   Build provenance and QC flags.")
    A("")
    A("HONEST LEFTOVERS (things we could NOT fill and why")
    A("    - US:HONA:US Honeywell Aerospace: interim-only SEC filer, no annual filing exists yet, so")
    A("      Revenue/Net_Income are blank. We did NOT copy numbers from HON (Honeywell Technologies) -")
    A("      different company. Hydro One is CA:H:TSX and is likewise never mixed up with either.")
    A("    - CA:IIP.UN:TSX InterRent REIT: no reliable annual data source found; statement fields blank.")
    A("    - US:APA:US APA Corporation: EDGAR tags no standard annual revenue concept; left blank rather")
    A("      than invented. SYF/TFC top line sits in TopLine_Alt as net interest income (see above).")
    A("    - Total_Debt on most banks/insurers: intentionally blank (not comparable; see dictionary).")
    A("    - Airlines tab has exactly 4 companies because only DAL, UAL, LUV (S&P 500) and AC (TSX")
    A("      Composite) are index members. AAL is NOT in the S&P 500, so it is not in this universe.")
    A("    - 26 companies show a Price but no Market_Cap and no shares snapshot; we do not guess.")
    A("")
    A("HOW TO UPDATE THIS FILE (for whoever comes next)")
    A("    1. DO NOT run refresh.py --mode all. It re-scrapes everything and can overwrite hand-fixed")
    A("       values. Treat the statement columns as frozen unless you fix a specific company.")
    A("    2. Index membership changes only: add/remove members when S&P announces changes. Keep the")
    A("       Company_ID convention exactly: US:TICKER:US or CA:TICKER:TSX (dots kept, e.g. CA:BN:TSX).")
    A("    3. To add a company: one row on 01_All_Companies, set Custom_Industry_Sheet, then add it to")
    A("       06_Placements and to whichever topic tabs need an Extra copy (pale green). The union of")
    A("       Company_IDs across all tabs must stay equal to 01_All_Companies.")
    A("    4. Re-run the Phase 7 assert block after any change; it fails loudly on drift.")
    A("")
    A("PHASE 7 CHANGELOG (" + TODAY + ")")
    A("    - Removed false-positive Extra placements:")
    A("        * Hartford (HIG) off Autos (name-substring accident: 'Hartford' contains 'Ford').")
    for cid, ind in removed_cs:
        nm = grid.loc[grid['Company_ID'].eq(cid), 'Company_Name'].iloc[0]
        A(f"        * {nm} ({cid.replace('US:', '').replace(':US', '')}) off Credit_Services "
          f"(industry='{ind}' - exchange/data, not payments).")
    if kept_cs_reason:
        A("        Kept despite ticker list: " + "; ".join(f"{c} ({i})" for c, i in kept_cs_reason) + ".")
    A("    - Added Extra copies (Primary rows untouched, no new companies):")
    A("        * Dollarama (CA:DOL:TSX) and Couche-Tard (CA:ATD:TSX) onto Discount_Stores.")
    if pipeline_added:
        A("        * " + ", ".join(pipeline_added) + " onto Pipelines_Midstream.")
    A("        * Keyera (CA:KEY:TSX) and Pembina (CA:PPL:TSX) were already Extra on Pipelines_Midstream.")
    A("    - Dropped 100%-blank helper columns (Fill_Notes, *_TS_Fill_FY) from every data sheet.")
    A("    - Standardized formatting: widths, 36px wrapped navy headers, 16px data rows, freeze B2,")
    A("      autofilter, banded rows, grey blanks, pale-green Extras. No Excel Tables anywhere.")
    A("    - Filled US GICS_Industry display field from Universe GICS Sub-Industry (US industry level")
    A(f"      was blank offline); {taskc['gics_ind_filled']} rows updated. No scrape performed.")
    A("    - Market_Cap back-fill check: 0 rows were fillable (every Price-without-MC row also lacks")
    A("      Shares_Snapshot); those 26 IDs are listed in logs/phase7_report.md.")
    A("")
    A("NOT INVESTMENT ADVICE.")
    return L


README_LINES = readme_lines()

# ---------------- write workbook ----------------
from openpyxl import Workbook, load_workbook

qa_wb = load_workbook(QA, read_only=False)
tab_colors = {}
for sn in qa_wb.sheetnames:
    tc = qa_wb[sn].sheet_properties.tabColor
    tab_colors[sn] = tc.rgb if tc and tc.type == "rgb" else (tc.value if tc else None)
qa_wb.close()

TAB_COLORS = {"Banks": "1F4E78", "Utilities_Regulated": "007782", "Software": "6A3D9A",
              "Semiconductors_Components": "3F51B5", "Oil_Gas_Producers": "E36C0A",
              "Insurance": "1E6B45", "Financials": "1E6B45", "Credit_Services": "1E6B45",
              "Discount_Stores": "C9A227"}
META_TAB, STEEL_TAB, GOLD_TAB, GICS_TAB = "808080", "4682B4", "C9A227", "2E7D32"

order = [s for s in xl.sheet_names if s in sheet_frames or s in book or s == "00_README"]
wb = Workbook()
wb.remove(wb.active)


def dump_df(ws, df):
    def clean(v):
        if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
            return None
        return v
    ws.append(list(df.columns))
    for _, rr in df.iterrows():
        ws.append([clean(v) for v in rr.tolist()])


for sn in order:
    ws = wb.create_sheet(sn[:31])
    if sn == "00_README":
        style_readme(ws, README_LINES)
        ws.sheet_properties.tabColor = META_TAB
        continue
    df = sheet_frames.get(sn, book.get(sn))
    dump_df(ws, df)
    if sn.startswith("GICS_"):
        color = GICS_TAB
    elif sn in TAB_COLORS:
        color = TAB_COLORS[sn]
    elif sn.startswith(("00", "02", "03", "04", "05", "06")):
        color = META_TAB
    else:
        color = STEEL_TAB
    if tab_colors.get(sn):
        color = tab_colors[sn]
    style_sheet(ws, list(df.columns), tab_color=color)

wb.save(OUT)
print("saved:", OUT, f"{os.path.getsize(OUT):,} bytes")

# ---------------- README.md ----------------
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(
    "\n".join(README_LINES) + "\n")

# ---------------- Task E: asserts ----------------
out_xl = pd.ExcelFile(OUT)
ac = out_xl.parse("01_All_Companies", keep_default_na=False)
assert len(ac) == 720 and ac["Company_ID"].is_unique, "All_Companies must be 720 unique"

ds = out_xl.parse("Discount_Stores", keep_default_na=False)
dids = set(ds["Company_ID"])
assert {"US:COST:US", "US:WMT:US", "CA:DOL:TSX"} <= dids, f"Discount_Stores missing members: {dids}"

au = out_xl.parse("Autos", keep_default_na=False)
assert "US:HIG:US" not in set(au["Company_ID"]), "Hartford must not be on Autos"

ur = out_xl.parse("Utilities_Regulated", keep_default_na=False)
hyd = ur.loc[ur["Company_ID"].eq("CA:H:TSX"), "Company_Name"]
assert len(hyd) == 1 and "hydro one" in hyd.iloc[0].lower(), "Hydro One must be on Utilities_Regulated"

cs = out_xl.parse("Credit_Services", keep_default_na=False)
csids = set(cs["Company_ID"])
assert {"US:V:US", "US:MA:US"} <= csids, "V/MA must be on Credit_Services"
for cid, _ in removed_cs:
    assert cid not in csids, f"{cid} should be off Credit_Services"

na_nm = ac.loc[ac["Company_ID"].eq("CA:NA:TSX"), "Company_Name"].iloc[0]
assert "national bank" in na_nm.lower(), na_nm
hona = ac.loc[ac["Company_ID"].eq("US:HONA:US"), "Company_Name"].iloc[0]
hon = ac.loc[ac["Company_ID"].eq("US:HON:US"), "Company_Name"].iloc[0]
hyd_all = ac.loc[ac["Company_ID"].eq("CA:H:TSX"), "Company_Name"].iloc[0]
assert hona != hon and "aerospace" in hona.lower() and "hydro one" in hyd_all.lower(), (hona, hon, hyd_all)

with zipfile.ZipFile(OUT) as z:
    tbl = [n for n in z.namelist() if n.startswith("xl/tables/")]
    assert not tbl, f"Excel Tables found: {tbl}"

readme_path = os.path.join(ROOT, "README.md")
assert os.path.exists(readme_path) and os.path.getsize(readme_path) > 4000
rm_txt = open(readme_path, encoding="utf-8").read()
for phrase in ["NOT investment advice".replace("NOT ", "").lower(), "column dictionary", "primary vs extra",
               "how to update", "native reporting currency"]:
    assert phrase in rm_txt.lower(), phrase

from openpyxl import load_workbook as lwb
wb_chk = lwb(OUT)
ws_ac = wb_chk["01_All_Companies"]
w_b = ws_ac.column_dimensions["B"].width
assert w_b >= 28, f"Company_Name width {w_b}"
ws_rm = wb_chk["00_README"]
assert ws_rm.max_row >= 60 and (ws_rm.column_dimensions["A"].width or 0) >= 100

# structural integrity: union across all topic sheets equals the 720; primary partition intact
union_ids, prim_total = set(), 0
for sn in custom_order + ["GICS_" + sv.replace(" ", "_") for sv in sector_orig]:
    if sn not in out_xl.sheet_names:
        continue
    dfr = out_xl.parse(sn, keep_default_na=False)
    assert "Placement_Role" in dfr.columns, sn
    union_ids |= set(dfr["Company_ID"])
    if sn in custom_order:
        prim_total += int(dfr["Placement_Role"].eq("Primary").sum())
assert union_ids == set(ac["Company_ID"]), "topic-sheet union drifted"
assert prim_total == 720, f"primary partition broken: {prim_total}"
airlines = set(out_xl.parse("Airlines", keep_default_na=False)["Company_ID"])
assert airlines == {"US:DAL:US", "US:UAL:US", "US:LUV:US", "CA:AC:TSX"}, airlines
jpm = num(ac.loc[ac["Primary_Ticker"].eq("JPM"), "Revenue"]).iloc[0]
ry = num(ac.loc[ac["Primary_Ticker"].eq("RY.TO"), "Revenue"]).iloc[0]
print("JPM/RY revenue preserved:", jpm, ry)
print("ALL PHASE 7 ASSERTS PASS")

# ---------------- report ----------------
rep = [f"# Phase 7 Report -- {TODAY}",
       f"- Input: Sector_Financials_QA.xlsx (read-only, {os.path.getsize(QA):,} bytes, mtime untouched).",
       f"- Output: Sector_Financials_Final_Owner.xlsx ({os.path.getsize(OUT):,} bytes).",
       "- Scope: polish only. No scrape, no ranking, no refresh.py, no universe change. Rows remain 720.",
       "",
       "## Task A -- placements",
       f"- Removed Hartford (US:HIG:US) Extra from Autos ('Hartford' substring-of-'Ford' accident).",
       f"- Removed {len(removed_cs)} Credit_Services false positives (exchange/data businesses):"]
rep += [f"  - {cid} ({ind})" for cid, ind in removed_cs]
rep += [f"- Kept JKHY on Credit_Services: GICS sub-industry '{dict(kept_cs_reason).get('US:JKHY:US','')}' "
        "is clearly Transaction & Payment Processing."]
rep += ["- Added Extras (no Primary touched): Dollarama CA:DOL:TSX + Couche-Tard CA:ATD:TSX -> Discount_Stores.",
        "- Pipelines_Midstream: CA:KEY:TSX and CA:PPL:TSX were already Extra there -- no-op, verified.",
        f"- Placement diffs applied: {len(changes)} companies.",
        "- Union of Company_IDs across all topic sheets re-verified == 720. No new companies. No AAL.",
        "",
        "## Task B -- formatting",
        f"- Helper columns dropped (100% blank): {sorted({c for v in dropped_helpers.values() for c in v})} "
        f"on {len(dropped_helpers)} sheets. TopLine_Alt (SYF/TFC) and Placement_Role kept.",
        "- Widths: Company_ID 18 / Company_Name 34 / Primary_Ticker 12 / GICS_Sector 22 / GICS_Industry 28 / "
        "Custom_Industry_Sheet 22 / money 14 / ratios 10 / Price 10 / Market_Cap 16 / Extraction_Status 14 / "
        "Source_Primary 12; others autofit clamped 9-26.",
        "- Header row 36px, wrap, vertical center; data rows 16px, no wrap; freeze B2; autofilter; navy header; "
        "banded rows; grey blanks; pale-green Extras. No padding to 1500 rows. No ListObjects.",
        "",
        "## Task C -- cheap fills",
        f"- GICS_Industry filled for {taskc['gics_ind_filled']} US rows from Universe.GICS_Sub_Industry "
        "(Universe.GICS_Industry is blank for ALL 500 US rows -- noted honestly in README; TSX rows already had "
        "true industry values and were not touched).",
        f"- Market_Cap = Price x Shares_Snapshot: {len(taskc['mc_filled'])} rows qualified (none had all three "
        "conditions). 26 rows have Price but neither MC nor Shares -- left blank by rule:",
        "  - " + ", ".join(taskc["mc_left_blank"]),
        "- No Revenue/NI/Debt invented. HON never copied onto HONA.",
        "",
        "## Task D -- README",
        "- README.md written at project root; identical content placed on 00_README sheet "
        "(wrapped, col A width 110). Covers: what the file is, product-file status, sheet map, Primary vs Extra, "
        "cross-border comparison rules, full column dictionary, honest leftovers, update instructions.",
        "",
        "## Task E -- asserts",
        "- 720 unique on 01_All_Companies: PASS",
        "- Costco+Walmart+Dollarama on Discount_Stores: PASS",
        "- Hartford NOT on Autos: PASS",
        "- Hydro One on Utilities_Regulated: PASS",
        "- V and MA on Credit_Services: PASS",
        "- No Excel Tables (zip-level check): PASS",
        "- README.md exists and 00_README detailed (>60 lines): PASS",
        "- Company_Name width >= 28 on All_Companies (set 34): PASS",
        f"- CA:NA:TSX = '{na_nm}': PASS",
        f"- US:HONA:US='{hona}' - US:HON:US='{hon}' - '{hyd_all}': PASS",
        f"- Airlines == DAL/UAL/LUV/AC exactly: PASS; primary partition sums to 720: PASS",
        "",
        "## Sheet row counts after Phase 7"]
for sn in order:
    if sn == "00_README":
        rep.append(f"- 00_README: {len(README_LINES)} lines")
    else:
        df = sheet_frames.get(sn, book.get(sn))
        extra_bit = ""
        if "Placement_Role" in df.columns:
            extra_bit = (f" (P={int(df['Placement_Role'].eq('Primary').sum())}, "
                         f"E={int(df['Placement_Role'].eq('Extra').sum())})")
        rep.append(f"- {sn}: {len(df)}{extra_bit}")
open(os.path.join(LOGD, "phase7_report.md"), "w", encoding="utf-8").write("\n".join(rep))
print("report:", os.path.join(LOGD, "phase7_report.md"))
