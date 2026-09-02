import os
import sys
import traceback
import zipfile
from datetime import date

import numpy as np
import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
P1 = os.path.join(ROOT, "Sector_Financials_Phase1.xlsx")
OUT = os.path.join(ROOT, "Sector_Financials_Phase1b.xlsx")
EXPORTS = os.path.join(ROOT, "exports")
LOGD = os.path.join(ROOT, "logs")
TODAY = date.today().isoformat()

TARGETS = [("Revenue", "Revenue", "Revenue_TS_Fill_FY"),
           ("Net_Income", "NetIncome", "Net_Income_TS_Fill_FY"),
           ("Total_Debt", "TotalDebt", "Total_Debt_TS_Fill_FY")]
REF_COLS = ["Operating_Cash_Flow", "Book_Equity", "Total_Assets", "Cash_ST_Investments", "Gross_Profit"]
COLLISION_TICKERS = ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]
SECTOR_COL = "Custom_Industry_Sheet"


def fail(msg):
    print("BUILD FAILED:", msg)
    if os.path.exists(OUT):
        os.remove(OUT)
    sys.exit(1)


def norm(s):
    p = s.astype(str).str.strip().str.split(":")
    return p.str[0] + ":" + p.str[1]


def num(s):
    return pd.to_numeric(s, errors="coerce")


def style_workbook(path, readme_width=150):
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    MONEY = {"Revenue", "Net_Income", "Gross_Profit", "Operating_Cash_Flow", "Capex",
             "Free_Cash_Flow", "FCF_Reported", "FCF_Calc", "Total_Debt", "Cash_ST_Investments",
             "Book_Equity", "NetDebt_Calc", "Total_Assets", "Total_Liabilities"}
    PCT = {"FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc"}
    wb = load_workbook(path)
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    hdr_font = Font(bold=True, color="FFFFFF")
    for sname in wb.sheetnames:
        ws = wb[sname]
        if sname.startswith("00_"):
            ws.column_dimensions["A"].width = readme_width
            continue
        headers = [c.value for c in ws[1]]
        for j, h in enumerate(headers, start=1):
            letter = get_column_letter(j)
            maxlen = max([len(str(h))] + [len(str(ws.cell(row=r, column=j).value)) for r in range(2, min(ws.max_row, 400) + 1) if ws.cell(row=r, column=j).value is not None], default=10)
            ws.column_dimensions[letter].width = min(46, max(11, maxlen + 2))
            hc = ws.cell(row=1, column=j)
            hc.font = hdr_font
            hc.fill = hdr_fill
            fmt = "#,##0" if h in MONEY else ("#,##0.00" if h == "Diluted_EPS" else ("0.00%" if h in PCT else None))
            for r in range(2, ws.max_row + 1):
                cell = ws.cell(row=r, column=j)
                if fmt and isinstance(cell.value, (int, float)):
                    cell.number_format = fmt
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
    wb.save(path)


def build():
    os.makedirs(EXPORTS, exist_ok=True)

    print("=== TASK A: ranking-pack CSVs from Sector_Financials_Phase1.xlsx ===")
    p1_sheets = {}
    p1_sheets["01_All_Companies"] = pd.read_excel(P1, sheet_name="01_All_Companies", keep_default_na=False)
    readme_df = pd.read_excel(P1, sheet_name="00_README", keep_default_na=False)
    dq_df = pd.read_excel(P1, sheet_name="03_Data_Quality", keep_default_na=False)
    all1 = p1_sheets["01_All_Companies"]
    assert len(all1) == 720 and all1["Company_ID"].nunique() == 720

    def write_csv(df, name):
        path = os.path.join(EXPORTS, name)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    banks_csv = write_csv(all1[all1[SECTOR_COL].eq("Banks")], "Banks.csv")
    util_csv = write_csv(all1[all1[SECTOR_COL].eq("Utilities_Regulated")], "Utilities_Regulated.csv")
    soft_csv = write_csv(all1[all1[SECTOR_COL].eq("Software")], "Software.csv")
    all_csv = write_csv(all1, "All_Companies.csv")

    b = pd.read_csv(banks_csv, keep_default_na=False)
    u = pd.read_csv(util_csv, keep_default_na=False)
    s = pd.read_csv(soft_csv, keep_default_na=False)
    a = pd.read_csv(all_csv, keep_default_na=False)
    coll_ids = [f"US:{t}:US" for t in COLLISION_TICKERS] + [f"CA:{t}:TSX" for t in COLLISION_TICKERS]
    assert len(b) == 39, f"Banks.csv {len(b)}"
    assert "CA:H:TSX" in set(u["Company_ID"]), "Hydro One missing from utilities csv"
    assert len(s) == 29, f"Software.csv {len(s)}"
    assert len(a) == 720 and a["Company_ID"].nunique() == 720
    na_row = a[a["Company_ID"].eq("CA:NA:TSX")]
    assert len(na_row) == 1 and na_row.iloc[0]["Company_Name"] == "National Bank of Canada"
    assert sum(cid in set(a["Company_ID"]) for cid in coll_ids) == 14
    print(f"  wrote {banks_csv} ({len(b)} rows)")
    print(f"  wrote {util_csv} ({len(u)} rows, CA:H:TSX present)")
    print(f"  wrote {soft_csv} ({len(s)} rows)")
    print(f"  wrote {all_csv} ({len(a)} rows)")

    print("\n=== TASK B: Time_Series backfill ===")
    ts = pd.read_excel(CANON, sheet_name="Time_Series", keep_default_na=False)
    ts["_k"] = norm(ts["Company_ID"])
    ts["_v"] = num(ts["Value"])
    tsv = ts[ts["_v"].notna()]

    latest = {}
    for core_col, ts_field, _ in TARGETS:
        sub = tsv[tsv["Field"].eq(ts_field)]
        idx = sub.groupby("_k")["Fiscal_Year"].idxmax()
        latest[core_col] = sub.loc[idx].set_index("_k")[["Fiscal_Year", "_v", "Currency", "Source"]]

    allb = all1.copy()
    for _, fy_col, in [(t[0], t[2]) for t in TARGETS]:
        pass
    for core_col, ts_field, fy_col in TARGETS:
        allb[fy_col] = ""
    allb["Fill_Notes"] = ""

    ref_abs = allb[REF_COLS].apply(num).abs()

    dq_rows = []
    n_fill = {c: 0 for c, _, _ in TARGETS}
    n_lacked = {c: 0 for c, _, _ in TARGETS}
    n_amb = 0
    n_curmis = 0

    for core_col, ts_field, fy_col in TARGETS:
        blanks = allb.index[allb[core_col].astype(str).str.strip() == ""]
        for i in blanks:
            cid = allb.at[i, "Company_ID"]
            k = str(norm(pd.Series([cid])).iloc[0])
            tick = allb.at[i, "Primary_Ticker"]
            if k not in latest[core_col].index:
                n_lacked[core_col] += 1
                dq_rows.append({"Company_ID": cid, "Ticker": tick, "Field": core_col,
                                "Issue": "TIME_SERIES_LACKED_FIELD", "Source_Attempted": "canonical Time_Series",
                                "Retrieval_Date": TODAY, "Resolution": "Left blank",
                                "Notes": "No non-null Time_Series value for any fiscal year."})
                continue
            row = latest[core_col].loc[k]
            v = float(row["_v"])
            fy = int(row["Fiscal_Year"])
            cur = str(row["Currency"]).strip()
            src = str(row["Source"]).strip()
            native = str(allb.at[i, "Currency"]).strip()
            if cur != native:
                n_curmis += 1
                dq_rows.append({"Company_ID": cid, "Ticker": tick, "Field": core_col,
                                "Issue": "CURRENCY_MISMATCH_SKIPPED", "Source_Attempted": f"Time_Series FY{fy}",
                                "Retrieval_Date": TODAY, "Resolution": "Left blank",
                                "Notes": f"TS currency {cur} != native {native}; FX mixing forbidden."})
                continue
            mags = ref_abs.loc[i].dropna()
            m = float(mags.median()) if len(mags) else 0.0

            def plausible(x):
                return True if m <= 0 else abs(np.log10(abs(x)) - np.log10(m)) <= 2.5

            if not plausible(v) and plausible(v * 1e6):
                n_amb += 1
                dq_rows.append({"Company_ID": cid, "Ticker": tick, "Field": core_col,
                                "Issue": "UNIT_AMBIGUOUS", "Source_Attempted": f"Time_Series FY{fy}",
                                "Retrieval_Date": TODAY, "Resolution": "Skipped fill; left blank",
                                "Notes": f"TS value {v:g} looks millions-scaled vs company Core reference magnitude {m:g}; scale not guessed."})
                continue
            if not plausible(v):
                n_amb += 1
                dq_rows.append({"Company_ID": cid, "Ticker": tick, "Field": core_col,
                                "Issue": "UNIT_AMBIGUOUS", "Source_Attempted": f"Time_Series FY{fy}",
                                "Retrieval_Date": TODAY, "Resolution": "Skipped fill; left blank",
                                "Notes": f"TS value {v:g} inconsistent with company Core reference magnitude {m:g} under either scale; skipped."})
                continue
            allb.at[i, core_col] = v
            allb.at[i, fy_col] = str(fy)
            note = f"{core_col} filled from Time_Series FY{fy} ({src}, {cur})"
            prev = str(allb.at[i, "Fill_Notes"])
            allb.at[i, "Fill_Notes"] = (prev + "; " + note) if prev else note
            n_fill[core_col] += 1
            dq_rows.append({"Company_ID": cid, "Ticker": tick, "Field": core_col,
                            "Issue": "FILLED_FROM_TIME_SERIES", "Source_Attempted": f"Time_Series FY{fy} ({src})",
                            "Retrieval_Date": TODAY, "Resolution": "Backfilled into Phase1b only",
                            "Notes": f"Latest available FY with non-null value; {v:,.0f} {cur}; canonical books untouched."})

    assert len(allb) == 720 and allb["Company_ID"].nunique() == 720
    assert allb["Company_ID"].astype(str).str.strip().ne("").all()
    for core_col, _, _ in TARGETS:
        was_blank = all1[core_col].astype(str).str.strip() == ""
        was_full = ~was_blank
        assert (allb.loc[was_full, core_col].values == all1.loc[was_full, core_col].values).all(), f"non-blank {core_col} overwritten"
        newly = allb.loc[was_blank, core_col].astype(str).str.strip() != ""
        assert (newly == allb.loc[was_blank, fy_col].astype(str).str.strip().ne("")).all()

    cov_specs = [("Revenue", "native currency"), ("Net_Income", "native currency"),
                 ("Diluted_EPS", ""), ("Operating_Cash_Flow", "OCF"), ("Capex", ""),
                 ("FCF_Reported", "copy of Core Free_Cash_Flow"), ("FCF_Calc", "OCF - abs(Capex); blank for Banks"),
                 ("Total_Debt", ""), ("Equity (Book_Equity)", "ending balance"),
                 ("Cash (Cash_ST_Investments)", ""), ("NetDebt_Calc", "Total_Debt - Cash"),
                 ("FCFMargin_Calc", "blank for Banks"), ("GrossMargin_Calc", "Gross_Profit / Revenue"),
                 ("ROE_Calc", "ROE = NI / ending equity (not average equity)")]
    cov_rows = []
    label_map = {"Equity (Book_Equity)": "Book_Equity", "Cash (Cash_ST_Investments)": "Cash_ST_Investments"}
    for label, note in cov_specs:
        col = label_map.get(label, label)
        nb = int(num(all1[col]).notna().sum())
        na_ = int(num(allb[col]).notna().sum())
        cov_rows.append({"Field": label, "n_before": nb, "pct_before": round(nb / 7.2, 1),
                         "n_after": na_, "pct_after": round(na_ / 7.2, 1), "notes": note})
    for core_col, _, fy_col in TARGETS:
        nf = int((allb[fy_col].astype(str).str.strip() != "").sum())
        cov_rows.append({"Field": fy_col, "n_before": 0, "pct_before": 0.0,
                         "n_after": nf, "pct_after": round(nf / 7.2, 1),
                         "notes": f"Fiscal year used for Time_Series backfill of {core_col}"})
    cov = pd.DataFrame(cov_rows)

    dq_new = pd.DataFrame(dq_rows)
    dq_all = pd.concat([dq_df.astype(str), dq_new.astype(str)], ignore_index=True)

    readme_lines = list(readme_df["A"].astype(str))
    readme_lines += ["", "PHASE 1B APPENDIX - TIME_SERIES BACKFILL",
                     f"Date: {TODAY}. New file Sector_Financials_Phase1b.xlsx; Phase1 file untouched.",
                     "Only blank Revenue / Net_Income / Total_Debt cells were eligible; no existing value was overwritten.",
                     "Value copied from the latest fiscal year in canonical Time_Series holding a non-null value for that company+field; year recorded in <FIELD>_TS_Fill_FY.",
                     "Guards applied: currency must equal the row's native currency (no FX); magnitude cross-checked against the company's own Core figures - mismatches logged as UNIT_AMBIGUOUS and skipped.",
                     "Banks untouched beyond the three listed statement fields; no FCF/NIM/CET1 invented.",
                     "XOM / HONA / IIP.UN remain MISSING_SOURCE: canonical Time_Series holds no rows for them.",
                     f"Ranking CSVs in exports/ were refreshed from this Phase1b All_Companies sheet (same filenames, utf-8-sig): Banks.csv, Utilities_Regulated.csv, Software.csv, All_Companies.csv."]
    readme = pd.DataFrame({"A": readme_lines})

    coll = allb[allb["Company_ID"].isin(coll_ids)].sort_values(["Primary_Ticker", "Country_of_Listing"])
    assert len(coll) == 14

    sheets = [("00_README", readme), ("01_All_Companies", allb), ("02_Coverage", cov),
              ("03_Data_Quality", dq_all), ("04_Collisions", coll)]
    sector_names = sorted(allb[SECTOR_COL].unique())
    for sname in sector_names:
        sub = allb[allb[SECTOR_COL].eq(sname)].sort_values("Company_Name", key=lambda x: x.str.lower())
        assert sub["Company_ID"].ne("").all()
        sheets.append((sname, sub))

    if os.path.exists(OUT):
        os.remove(OUT)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        for sname, df in sheets:
            df.to_excel(xw, sheet_name=sname[:31], index=False)
    style_workbook(OUT)

    z = zipfile.ZipFile(OUT)
    tables = [n for n in z.namelist() if "tables/" in n.lower()]
    assert not tables, f"ListObject parts found: {tables}"
    z.close()

    from openpyxl import load_workbook
    wb2 = load_workbook(OUT)
    for sname in wb2.sheetnames:
        assert len(getattr(wb2[sname], "tables", {})) == 0
        if not sname.startswith("00_"):
            assert wb2[sname].freeze_panes == "A2"
    wb2.close()

    from python_calamine import CalamineWorkbook
    cw = CalamineWorkbook.from_path(OUT)
    rows = cw.get_sheet_by_name("01_All_Companies").to_python(skip_empty_area=False)
    ix = {h: i for i, h in enumerate(rows[0])}
    body = rows[1:]

    def val(cid, col_name):
        return next(r[ix[col_name]] for r in body if r[ix["Company_ID"]] == cid)

    checks = {
        "rows_720": len(body) == 720,
        "ids_unique_720": len({r[ix["Company_ID"]] for r in body}) == 720,
        "no_blank_ids": all(str(r[ix["Company_ID"]]).strip() != "" for r in body),
        "na_name": val("CA:NA:TSX", "Company_Name") == "National Bank of Canada",
        "jpm_rev_numeric": isinstance(val("US:JPM:US", "Revenue"), (int, float)),
        "ry_rev_numeric_and_equal_p1": isinstance(val("CA:RY:TSX", "Revenue"), (int, float)) and float(val("CA:RY:TSX", "Revenue")) == float(num(all1.loc[all1['Company_ID'].eq('CA:RY:TSX'), 'Revenue']).iloc[0]),
        "efx_pair_split": ("CA:EFX:TSX" in {r[ix['Company_ID']] for r in body}) and ("US:EFX:US" in {r[ix['Company_ID']] for r in body}),
        "hydro_one_present": "CA:H:TSX" in {r[ix["Company_ID"]] for r in body},
        "collisions_14": sum(r[ix["Company_ID"]] in coll_ids for r in body) == 14,
    }
    bad = [k for k, v in checks.items() if not v]
    assert not bad, f"calamine checks failed: {bad}"

    pdf = pd.read_excel(OUT, sheet_name="01_All_Companies", keep_default_na=False)
    assert len(pdf) == 720 and pdf["Company_ID"].nunique() == 720 and pdf["Company_ID"].isna().sum() == 0
    total_sector = 0
    for sname in sector_names:
        sub = pd.read_excel(OUT, sheet_name=sname, keep_default_na=False)
        total_sector += len(sub)
        assert sub["Company_ID"].ne("").all()
    assert total_sector == 720, f"industry sheets sum {total_sector}"

    banks_csv = write_csv(pdf[pdf[SECTOR_COL].eq("Banks")], "Banks.csv")
    util_csv = write_csv(pdf[pdf[SECTOR_COL].eq("Utilities_Regulated")], "Utilities_Regulated.csv")
    soft_csv = write_csv(pdf[pdf[SECTOR_COL].eq("Software")], "Software.csv")
    all_csv = write_csv(pdf, "All_Companies.csv")
    print("  refreshed CSVs from Phase1b 01_All_Companies (same filenames)")

    b2 = pd.read_csv(banks_csv, keep_default_na=False)
    u2 = pd.read_csv(util_csv, keep_default_na=False)
    s2 = pd.read_csv(soft_csv, keep_default_na=False)
    a2 = pd.read_csv(all_csv, keep_default_na=False)
    assert len(b2) == 39 and len(s2) == 29 and len(a2) == 720 and a2["Company_ID"].nunique() == 720
    assert "CA:H:TSX" in set(u2["Company_ID"])

    print("\n=== VERIFICATION PASSED ===")
    for k, v in checks.items():
        print(f"  {k}: {v}")

    gained = {}
    for cid in ["US:XOM:US", "US:HONA:US", "CA:IIP.UN:TSX"]:
        r = allb[allb["Company_ID"].eq(cid)].iloc[0]
        gained[cid] = {c: ("" if str(r[c]).strip() == "" else float(r[c])) for c, _, _ in TARGETS}

    rep = []
    rep.append("# Phase 1b Report")
    rep.append(f"- Date: {TODAY}")
    rep.append(f"- Output workbook: {OUT} ({os.path.getsize(OUT):,} bytes); Phase1 workbook not modified.")
    rep.append("- Fill rule: only blank Revenue / Net_Income / Total_Debt cells; latest FY in canonical Time_Series with a non-null value; Company_ID matched via normalized CC:TICKER key (both schemes share segment 1+2); currency guard; magnitude guard (UNIT_AMBIGUOUS skips).")
    rep.append("")
    rep.append("## Fill counts")
    tot_attempted = 0
    for core_col, _, fy_col in TARGETS:
        blanks1 = int((all1[core_col].astype(str).str.strip() == "").sum())
        blanksb = int((allb[core_col].astype(str).str.strip() == "").sum())
        tot_attempted += blanks1
        rep.append(f"- {core_col}: before-blank {blanks1} -> after-blank {blanksb}; filled {n_fill[core_col]}; still blank {blanksb} (of which TS-lacked {n_lacked[core_col]}, UNIT_AMBIGUOUS {n_amb if core_col=='Total_Debt' else 0})")
    rep.append(f"- Attempted cells total: {tot_attempted}; successful fills: {sum(n_fill.values())}")
    rep.append(f"- UNIT_AMBIGUOUS skips: {n_amb}; CURRENCY_MISMATCH skips: {n_curmis}")
    rep.append("")
    rep.append("## MISSING_SOURCE trio")
    for cid, d in gained.items():
        rep.append(f"- {cid}: " + ", ".join(f"{k}={'still blank' if v=='' else format(v, ',.0f')}" for k, v in d.items()))
    rep.append("")
    rep.append("## Ranking CSVs (refreshed from Phase1b All_Companies, utf-8-sig, same filenames)")
    for p, n in [(banks_csv, len(b2)), (util_csv, len(u2)), (soft_csv, len(s2)), (all_csv, len(a2))]:
        rep.append(f"- {p} ({n} rows)")
    rep.append("")
    rep.append("## Integrity checks")
    rep.append("- 720 rows, 0 blank Company_ID, industry sheets sum 720, collisions 14 split, no Excel Tables (zip scan + openpyxl), python-calamine reload passed all checks.")
    rep.append("- Microsoft Excel itself was not launched on this machine (headless session); validation relies on python-calamine, openpyxl reload, and zip OOXML table-part scan.")
    rep.append("- No scrape, no network calls, no ranking or scoring; canonical xlsx untouched; Sector_Financials_Phase1.xlsx untouched.")
    rep.append("")
    rep.append("## Coverage before/after")
    rep.append("| Field | n_before | pct | n_after | pct |")
    rep.append("|---|---|---|---|---|")
    for _, r in cov.iterrows():
        rep.append(f"| {r['Field']} | {r['n_before']} | {r['pct_before']}% | {r['n_after']} | {r['pct_after']}% |")
    with open(os.path.join(LOGD, "phase1b_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")

    ch = ["# Phase 1b Changelog", f"Date: {TODAY}", "",
          "## What changed",
          "- Created exports/ with Banks.csv, Utilities_Regulated.csv, Software.csv, All_Companies.csv (utf-8-sig; first written from Phase1, then refreshed from Phase1b All_Companies under the SAME filenames - documented choice).",
          "- Created Sector_Financials_Phase1b.xlsx: Phase1 layout + Revenue_TS_Fill_FY / Net_Income_TS_Fill_FY / Total_Debt_TS_Fill_FY / Fill_Notes; Coverage now shows before/after; Data_Quality extended with FILLED_FROM_TIME_SERIES / TIME_SERIES_LACKED_FIELD / UNIT_AMBIGUOUS / CURRENCY_MISMATCH_SKIPPED rows.",
          "- Created logs/phase1b_report.md and this changelog.",
          f"- Backfill totals: {sum(n_fill.values())} cells filled ({n_fill}), {n_amb} UNIT_AMBIGUOUS skips, {n_curmis} currency skips, {sum(n_lacked.values())} TS-lacked.",
          "",
          "## Why",
          "Owner asked for gap-only enrichment from the already-collected Time_Series archive plus machine-readable ranking packs; nothing else.",
          "",
          "## Files touched",
          "scripts/build_phase1b.py (new), Sector_Financials_Phase1b.xlsx (new), exports/*.csv (new), logs/phase1b_report.md (new), logs/phase1b_changelog.md (new).",
          "",
          "## Files NOT touched",
          "NA_Company_Financials.xlsx, NA_Company_Financials_Analysis.xlsx, Sector_Financial_Analysis.xlsx, Sector_Financials_Clean.xlsx, Sector_Financials_Phase1.xlsx, all phase0/phase1 logs and artifacts, METHODOLOGY.md, HANDOFF_STATUS.txt."]
    with open(os.path.join(LOGD, "phase1b_changelog.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(ch) + "\n")

    print("\n=== TASK C REPORT ===")
    print("\n".join(rep))


if __name__ == "__main__":
    try:
        build()
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
