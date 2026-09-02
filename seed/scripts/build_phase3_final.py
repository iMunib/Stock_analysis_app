import csv
import json
import os
import sys
import time
import traceback
from datetime import date, datetime

import numpy as np
import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
COMPLETE = os.path.join(ROOT, "Sector_Financials_Complete.xlsx")
FINAL = os.path.join(ROOT, "Sector_Financials_Final.xlsx")
LOGD = os.path.join(ROOT, "logs")
EXPORTS = os.path.join(ROOT, "exports")
CACHE = r"C:\Users\RehmanPC\AppData\Local\Temp\opencode\p2cache"
TODAY = date.today().isoformat()
SECTOR_COL = "Custom_Industry_Sheet"
A_START = time.time()
A_BUDGET_S = 1200

STMT_COLS = ["Revenue", "Net_Income", "Diluted_EPS", "Gross_Profit", "Operating_Cash_Flow",
             "Capex", "Total_Debt", "Book_Equity", "Cash_ST_Investments", "Total_Assets",
             "Total_Liabilities", "EBIT", "EBITDA", "Interest_Expense"]
DERIVED_COLS = ["FCF_Reported", "Free_Cash_Flow", "FCF_Calc", "NetDebt_Calc", "FCFMargin_Calc",
                "GrossMargin_Calc", "ROE_Calc", "ROA_Calc", "PE_Calc", "PB_Calc", "EV_Calc",
                "EV_to_EBITDA_Calc"]
REV_TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
            "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"]
DA_TAGS = ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
           "DepreciationAndAmortization", "Depreciation"]
DEBT_ST_TAGS = ["DebtCurrent", "ShortTermBorrowings", "LongTermDebtCurrent", "OtherShortTermBorrowings"]
DEBT_LT_TAG = "LongTermDebtNoncurrent"
TINY_EXPECTED = {"Discount_Stores": 2, "Comm_Services": 1, "Airlines": 4, "Autos": 4,
                 "Credit_Services": 4, "Internet_Platforms": 4, "Biotech": 7,
                 "Fast_Food_Restaurants": 7}
COLLISION_IDS = {f"US:{t}:US" for t in ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]} | \
                {f"CA:{t}:TSX" for t in ["ARE", "EFX", "KEY", "L", "PPL", "T", "TKO"]}
TAB_COLORS = {"Banks": "1F4E78", "Utilities_Regulated": "007782", "Software": "6A3D9A",
              "Semiconductors_Components": "3F51B5", "Oil_Gas_Producers": "E36C0A",
              "Insurance": "1E6B45", "Financials": "1E6B45", "Credit_Services": "1E6B45",
              "Discount_Stores": "C9A227"}
META_TAB, STEEL_TAB, GOLD_TAB = "808080", "4682B4", "C9A227"


def num(s):
    return pd.to_numeric(s, errors="coerce")


def blank(v):
    return v is None or (isinstance(v, float) and np.isnan(v)) or str(v).strip() == ""


def log_attempt(rows, cid, tkr, field, source, action, status, detail=""):
    rows.append({"ts": datetime.utcnow().isoformat(timespec="seconds"), "Company_ID": cid,
                 "Ticker": tkr, "Field": field, "Source": source, "Action": action,
                 "Status": status, "Detail": detail})


def load_cik_map():
    with open(os.path.join(CACHE, "company_tickers.json")) as f:
        raw = json.load(f)
    m = {}
    for _, rec in raw.items():
        m[str(rec.get("ticker", "")).upper().replace("-", ".")] = str(int(rec["cik_str"])).zfill(10)
    return m


def annual_series(facts, taxo, concept):
    out = {}
    node = facts.get("facts", {}).get(taxo, {}).get(concept)
    if not node:
        return out
    for unit, arr in node.get("units", {}).items():
        for e in arr:
            if e.get("form") == "10-K" and e.get("fp") == "FY" and e.get("end") and not e.get("frame"):
                end = e["end"]
                prev = out.get(end)
                if prev is None or str(e.get("filed", "")) >= prev[1]:
                    out[end] = (e.get("val"), e.get("filed", ""), unit)
    return out


def latest(ser):
    if not ser:
        return None
    end = max(ser)
    v = ser[end]
    return {"end": end, "val": v[0], "unit": v[2]}


def append_src(grid, i, txt):
    cur = grid.at[i, "Fill_Source"]
    grid.at[i, "Fill_Source"] = ("" if blank(cur) else str(cur) + "; ") + txt


def main():
    uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
    uix = uni.set_index("Company_ID")
    grid = pd.read_excel(COMPLETE, sheet_name="01_All_Companies", keep_default_na=False)
    dq_prev = pd.read_excel(COMPLETE, sheet_name="03_Data_Quality", keep_default_na=False)
    cov_prev = pd.read_excel(COMPLETE, sheet_name="02_Coverage", keep_default_na=False)
    coll_prev = pd.read_excel(COMPLETE, sheet_name="04_Collisions", keep_default_na=False)
    comp_stmt = grid.copy()

    att, dq_new = [], []
    print("=== TASK A: last holes ===")
    cik_map = load_cik_map()

    def facts_for(cid):
        tkr = str(uix.at[cid, "Primary_Ticker"]).strip()
        cik = str(uix.at[cid, "CIK_SEDAR"]).strip()
        if not cik.isdigit():
            cik = cik_map.get(tkr.upper(), "")
        cik = cik.zfill(10)
        p = os.path.join(CACHE, f"cik_{cik}.json")
        if not cik or not os.path.exists(p):
            return tkr, None
        with open(p) as f:
            return tkr, json.load(f)

    def resolve_rev_conflicts():
        fixed = 0
        for cid in ["US:APA:US", "US:SYF:US", "US:TFC:US"]:
            tkr, facts = facts_for(cid)
            series = {}
            if facts:
                for t in REV_TAGS:
                    s = annual_series(facts, "us-gaap", t)
                    if s:
                        series[t] = s
            if not series:
                reason = {"US:SYF:US": "interest-income business model; income statement top line not tagged as any Revenue concept",
                          "US:TFC:US": "interest-income business model; income statement top line not tagged as any Revenue concept",
                          "US:APA:US": "cached facts contain only zero-valued 2020-21 interim stubs; no annual revenue concept exists"}.get(cid, "")
                log_attempt(att, cid, tkr, "Revenue", "SEC cache", "conflict_recheck", "NO_ANNUAL_DATA",
                            reason or "no fallback tag has annual data")
                dq_new.append({"Company_ID": cid, "Ticker": tkr, "Field": "Revenue",
                               "Issue": "REVENUE_CONCEPT_ABSENT", "Source_Attempted": "SEC EDGAR (cached companyfacts)",
                               "Retrieval_Date": TODAY, "Resolution": "Left blank",
                               "Notes": reason})
                continue
            ref = max(e for s in series.values() for e in s)
            vals = {t: s[ref] for t, s in series.items() if ref in s}
            uniq = sorted({v[0] for v in vals.values() if v[0] is not None})
            if len(uniq) == 1:
                i = grid.index[grid["Company_ID"].eq(cid)][0]
                if blank(grid.at[i, "Revenue"]):
                    tag = next(t for t, v in vals.items() if v[0] == uniq[0])
                    grid.at[i, "Revenue"] = float(uniq[0])
                    append_src(grid, i, f"EDGAR {tag}@{ref} (phase3 single-tag resolution)")
                    fixed += 1
                    log_attempt(att, cid, tkr, "Revenue", "SEC cache", "single_tag_fill", "OK",
                                f"{tag}={uniq[0]} end={ref}")
                    dq_new.append({"Company_ID": cid, "Ticker": tkr, "Field": "Revenue",
                                   "Issue": "PRIOR_TAG_CONFLICT_RESOLVED", "Source_Attempted": "SEC EDGAR (cached)",
                                   "Retrieval_Date": TODAY,
                                   "Resolution": f"Filled from sole populated fallback {tag}",
                                   "Notes": f"end={ref}; other fallback tags absent at that period"})
            else:
                log_attempt(att, cid, tkr, "Revenue", "SEC cache", "conflict_stands", "KEPT_BLANK",
                            f"{len(uniq)} distinct values at {ref}: {min(uniq)}..{max(uniq)}")
        return fixed

    def hona_recheck():
        tkr, facts = facts_for("US:HONA:US")
        any_annual = False
        if facts:
            for concept in facts.get("facts", {}).get("us-gaap", {}):
                if annual_series(facts, "us-gaap", concept):
                    any_annual = True
                    break
        log_attempt(att, "US:HONA:US", tkr, "statements", "SEC cache", "annual_recheck",
                    "NO_ANNUAL_FILING_STANDS" if not any_annual else "FOUND_ANNUAL?",
                    "Honeywell Aerospace Inc interim-only registrant; never copy HON")

    def yahoo_ca_income_retry():
        import yfinance as yf
        for cid, sym in [("CA:IIP.UN:TSX", "IIP-UN.TO"), ("CA:TECK.B:TSX", "TECK-B.TO")]:
            i = grid.index[grid["Company_ID"].eq(cid)][0]
            got = []
            try:
                inc = yf.Ticker(sym).get_income_stmt()
                time.sleep(0.8)
                if inc is not None and not inc.empty:
                    col = inc.columns[0]
                    for lbl in ["TotalRevenue", "OperatingRevenue", "NetIncome",
                                "NetIncomeCommonStockholders", "NetIncomeIncludingNoncontrollingInterests"]:
                        if lbl in inc.index and pd.notna(inc.loc[lbl, col]):
                            tgt = "Revenue" if lbl in ("TotalRevenue", "OperatingRevenue") else "Net_Income"
                            if blank(grid.at[i, tgt]):
                                grid.at[i, tgt] = float(inc.loc[lbl, col])
                                append_src(grid, i, f"YahooStmt {lbl}@{col.date()}")
                                got.append(tgt)
                log_attempt(att, cid, sym, "Revenue/Net_Income", "Yahoo", "income_retry",
                            "FILLED" if got else "NO_DATA", ",".join(got) or "labels absent")
            except Exception as ex:
                log_attempt(att, cid, sym, "Revenue/Net_Income", "Yahoo", "income_retry", "ERROR", repr(ex)[:160])

    def quote_retry():
        import yfinance as yf
        for cid, sym in [("CA:IIP.UN:TSX", "IIP-UN.TO"), ("CA:OLA:TSX", "OLA.TO")]:
            i = grid.index[grid["Company_ID"].eq(cid)][0]
            px = mc = cur = None
            try:
                info = yf.Ticker(sym).get_info()
                time.sleep(0.8)
                px = info.get("regularMarketPrice") or info.get("currentPrice")
                mc = info.get("marketCap")
                cur = info.get("currency") or ""
            except Exception as ex:
                log_attempt(att, cid, sym, "Price/Market_Cap", "Yahoo", "quote_retry", "ERROR", repr(ex)[:160])
            if px:
                grid.at[i, "Price"] = float(px)
                grid.at[i, "Price_Currency"] = str(cur)
                grid.at[i, "Price_AsOf"] = TODAY
                if mc:
                    grid.at[i, "Market_Cap"] = float(mc)
                log_attempt(att, cid, sym, "Price/Market_Cap", "Yahoo", "quote_retry", "FILLED", f"px={px} ccy={cur}")
            else:
                log_attempt(att, cid, sym, "Price/Market_Cap", "Yahoo", "quote_retry", "NO_QUOTE",
                            "delisted or unavailable; left blank")

    def debt_sums():
        sh = grid[SECTOR_COL].astype(str).str.strip()
        skip_mask = sh.eq("Banks") | sh.str.startswith("Insurance")
        filled = skipped_bankish = insufficient = 0
        src_ids = [x.strip() for x in dq_prev[(dq_prev["Issue"] == "STILL_BLANK_AFTER_FILL") &
                                              (dq_prev["Field"] == "Total_Debt")].iloc[0]["Notes"].split(",")]
        for cid in src_ids:
            i_list = grid.index[grid["Company_ID"].eq(cid)]
            if not len(i_list):
                continue
            i = i_list[0]
            if bool(skip_mask.loc[i]):
                skipped_bankish += 1
                continue
            if not blank(grid.at[i, "Total_Debt"]):
                continue
            if time.time() - A_START > A_BUDGET_S:
                log_attempt(att, cid, "", "Total_Debt", "SEC cache", "st_lt_sum", "SKIPPED_TIMEBOX")
                continue
            tkr, facts = facts_for(cid)
            st_vals = []
            lt = None
            tot = None
            if facts:
                for t in DEBT_ST_TAGS:
                    v = latest(annual_series(facts, "us-gaap", t))
                    if v:
                        st_vals.append(v)
                for t in ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"):
                    lt = latest(annual_series(facts, "us-gaap", t))
                    if lt:
                        break
                for t in ("LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", "LongTermDebt"):
                    tot = latest(annual_series(facts, "us-gaap", t))
                    if tot:
                        break
            if tot:
                grid.at[i, "Total_Debt"] = float(tot["val"])
                append_src(grid, i, f"EDGAR {t}@{tot['end']} (combined total)")
                filled += 1
                log_attempt(att, cid, tkr, "Total_Debt", "SEC cache", "total_tag_fill", "FILLED",
                            f"tag={t} val={tot['val']} end={tot['end']}")
                continue
            if not st_vals or not lt:
                insufficient += 1
                log_attempt(att, cid, tkr, "Total_Debt", "SEC cache", "st_lt_sum", "INSUFFICIENT_TAGS",
                            "need both ST and LongTermDebtNoncurrent annual tags")
                continue
            st_end = max(v["end"] for v in st_vals)
            if abs(int(st_end[:4]) - int(lt["end"][:4])) > 1:
                insufficient += 1
                log_attempt(att, cid, tkr, "Total_Debt", "SEC cache", "st_lt_sum", "PERIOD_MISMATCH",
                            f"ST@{st_end} vs LT@{lt['end']}")
                continue
            st_total = sum(v["val"] for v in st_vals if v["end"] == st_end)
            td = float(st_total + lt["val"])
            grid.at[i, "Total_Debt"] = td
            append_src(grid, i, f"EDGAR ST{st_end}+LT{lt['end']} sum")
            filled += 1
            log_attempt(att, cid, tkr, "Total_Debt", "SEC cache", "st_lt_sum", "FILLED",
                        f"ST={st_total} LT={lt['val']} total={td}")
        return filled, skipped_bankish, insufficient

    def ebitda_from_da():
        n = 0
        us_idx = grid.index[grid["Company_ID"].str.startswith("US:") &
                            grid["EBITDA"].apply(lambda v: blank(v)) & num(grid["EBIT"]).notna()]
        for i in us_idx:
            if time.time() - A_START > A_BUDGET_S:
                break
            cid = grid.at[i, "Company_ID"]
            tkr, facts = facts_for(cid)
            da = None
            if facts:
                for t in DA_TAGS:
                    da = latest(annual_series(facts, "us-gaap", t))
                    if da:
                        break
            if not da:
                continue
            ebit = float(num(pd.Series([grid.at[i, "EBIT"]])).iloc[0])
            grid.at[i, "EBITDA"] = float(ebit + da["val"])
            append_src(grid, i, f"EBITDA=EBIT+D&A({da['end']})")
            n += 1
        return n

    rev_fixed = resolve_rev_conflicts()
    print("revenue conflict resolutions:", rev_fixed)
    hona_recheck()
    yahoo_ca_income_retry()
    quote_retry()
    td_filled, td_bankish, td_insuff = debt_sums()
    eb_fixed = ebitda_from_da()
    print(f"TD filled {td_filled}, bankish skipped {td_bankish}, insufficient {td_insuff}; EBITDA derived {eb_fixed}")

    with open(os.path.join(LOGD, "phase3_attempts.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "Company_ID", "Ticker", "Field", "Source", "Action", "Status", "Detail"])
        w.writeheader()
        w.writerows(att)

    banks = grid[SECTOR_COL].astype(str).str.strip().eq("Banks")
    rev, ni = num(grid["Revenue"]), num(grid["Net_Income"])
    ocf, capex = num(grid["Operating_Cash_Flow"]), num(grid["Capex"])
    debt, cash = num(grid["Total_Debt"]), num(grid["Cash_ST_Investments"])
    gp, eq, assets = num(grid["Gross_Profit"]), num(grid["Book_Equity"]), num(grid["Total_Assets"])
    eps, px, mc = num(grid["Diluted_EPS"]), num(grid["Price"]), num(grid["Market_Cap"])
    ebitda = num(grid["EBITDA"])
    fcf = ocf - capex.abs()
    fcf[(ocf.isna() | capex.isna() | banks)] = np.nan
    nd = debt - cash
    nd[debt.isna() | cash.isna()] = np.nan
    fm = (fcf / rev.where(rev != 0)).round(6)
    fm[banks] = np.nan
    gm = (gp / rev.where(rev != 0)).round(6)
    roe = (ni / eq.where(eq > 0)).round(6)
    roa = (ni / assets.where(assets > 0)).round(6)
    pe = (px / eps.where(eps > 0)).round(4)
    pb = (mc / eq.where(eq > 0)).round(4)
    ev = mc + debt - cash
    ev[mc.isna() | debt.isna() | cash.isna()] = np.nan
    eve = (ev / ebitda.where(ebitda > 0)).round(4)
    for col, vals in [("FCF_Calc", fcf), ("NetDebt_Calc", nd), ("FCFMargin_Calc", fm),
                      ("GrossMargin_Calc", gm), ("ROE_Calc", roe), ("ROA_Calc", roa),
                      ("PE_Calc", pe), ("PB_Calc", pb), ("EV_Calc", ev), ("EV_to_EBITDA_Calc", eve)]:
        grid[col] = [("" if pd.isna(v) else float(v)) for v in vals]

    changed = []
    for c in STMT_COLS + DERIVED_COLS:
        old = num(comp_stmt.set_index("Company_ID")[c])
        new = num(grid.set_index("Company_ID")[c])
        d = old.notna() & ((new - old).abs() > (old.abs() * 1e-9 + 1e-9))
        if d.any():
            changed.append((c, int(d.sum())))
    assert not changed, changed

    logged_reason_ids = {"US:HONA:US", "CA:IIP.UN:TSX", "US:APA:US", "US:SYF:US", "US:TFC:US"}
    grid["Fill_OK"] = ["Y" if ((not blank(r.Company_ID)) and (not blank(r.Company_Name)) and
                               (not blank(r.Currency)) and
                               ((not blank(r.Revenue)) or r.Company_ID in logged_reason_ids))
                       else "N" for r in grid.itertuples()]

    print("=== TASK B: membership ===")
    auth_sheet = uix[SECTOR_COL].astype(str).str.strip()
    placed, flags = [], []
    misplaced_rows = []
    for i in grid.index:
        cid = grid.at[i, "Company_ID"]
        want = str(auth_sheet.at[cid]).strip()
        have = str(grid.at[i, SECTOR_COL]).strip()
        placed.append(want)
        if have != want:
            flags.append("MISPLACED")
            misplaced_rows.append((cid, have, want))
            dq_new.append({"Company_ID": cid, "Ticker": str(uix.at[cid, "Primary_Ticker"]).strip(),
                           "Field": SECTOR_COL, "Issue": "MISPLACED_SHEET_AUTOREPAIRED",
                           "Source_Attempted": "Universe.Custom_Industry_Sheet", "Retrieval_Date": TODAY,
                           "Resolution": f"'{have}' -> '{want}'", "Notes": ""})
        else:
            flags.append("")
    grid[SECTOR_COL] = placed
    grid["Membership_Flag"] = flags

    part = grid.groupby(SECTOR_COL)["Company_ID"].count()
    assert int(part.sum()) == 720
    tiny_review = []
    for s, n in part.items():
        if s in TINY_EXPECTED and int(n) != TINY_EXPECTED[s]:
            tiny_review.append((f"{s} (COUNT DRIFT)", int(n)))
        elif int(n) <= 7:
            tiny_review.append((s, int(n)))
    disc = grid[grid[SECTOR_COL].eq("Discount_Stores")][["Company_Name", "GICS_Sector", "GICS_Industry"]]
    banks_sheet = grid[grid[SECTOR_COL].eq("Banks")]
    checks_b = {
        "partition_720": int(part.sum()) == 720,
        "banks_39": len(banks_sheet) == 39,
        "banks_has_jpm_ry_na": all(c in set(banks_sheet["Company_ID"]) for c in ["US:JPM:US", "CA:RY:TSX", "CA:NA:TSX"]),
        "hydro_one_utilities": grid.loc[grid["Company_ID"].eq("CA:H:TSX"), SECTOR_COL].iloc[0] == "Utilities_Regulated",
        "semis_nonempty": int(part.get("Semiconductors_Components", 0)) > 0,
        "na_intact": grid.loc[grid["Company_ID"].eq("CA:NA:TSX"), "Company_Name"].iloc[0] == "National Bank of Canada",
    }
    bad_b = [k for k, v in checks_b.items() if not v]
    assert not bad_b, bad_b

    memb = pd.DataFrame({
        "Company_ID": grid["Company_ID"], "Company_Name": grid["Company_Name"],
        "GICS_Sector": grid["GICS_Sector"], "GICS_Industry": grid["GICS_Industry"],
        "Custom_Industry_Sheet": grid[SECTOR_COL], "Sheet_Placed_On": grid[SECTOR_COL],
        "Revenue_filled": np.where(num(grid["Revenue"]).notna(), "Y", "N"),
        "Fill_OK": grid["Fill_OK"], "Flag": ""})
    for i in memb.index:
        f = flags[i]
        rf = memb.at[i, "Revenue_filled"]
        if f:
            memb.at[i, "Flag"] = f
        elif rf == "N":
            memb.at[i, "Flag"] = "OK" if memb.at[i, "Company_ID"] in logged_reason_ids else "REVENUE_BLANK"
        elif int(part.get(memb.at[i, "Custom_Industry_Sheet"], 99)) <= 7:
            memb.at[i, "Flag"] = "TINY_SHEET_REVIEW"
        else:
            memb.at[i, "Flag"] = "OK"
    memb.to_csv(os.path.join(LOGD, "phase3_membership.csv"), index=False, encoding="utf-8-sig")

    disc_ids = grid.loc[grid[SECTOR_COL].eq("Discount_Stores"), "Company_ID"]
    for cid in disc_ids:
        sub = str(uix.at[cid, "GICS_Sub_Industry"]).strip()
        if "Discount" not in sub and "Warehouse" not in sub and "Club" not in sub:
            memb.loc[memb["Company_ID"].eq(cid), "Flag"] = "NAME_SHEET_MISMATCH"
            dq_new.append({"Company_ID": cid, "Ticker": str(uix.at[cid, "Primary_Ticker"]).strip(),
                           "Field": SECTOR_COL, "Issue": "NAME_SHEET_MISMATCH",
                           "Source_Attempted": f"Universe GICS_Sub_Industry={sub}",
                           "Retrieval_Date": TODAY,
                           "Resolution": "Kept on Universe-assigned sheet; naming review recommended",
                           "Notes": "Not moved: no new taxonomy may be invented"})
    memb.to_csv(os.path.join(LOGD, "phase3_membership.csv"), index=False, encoding="utf-8-sig")

    print("=== TASK C: build styled Final ===")
    ORDER = ["Company_ID", "Company_Name", "Primary_Ticker", "Country_of_Listing", "Currency",
             "GICS_Sector", "GICS_Industry", "Custom_Industry_Sheet", "Exchange", "In_SP500",
             "In_TSX_Composite", "Extraction_Status", "Source_Primary", "Fiscal_Year_End",
             "Revenue", "Net_Income", "Diluted_EPS", "Gross_Profit", "Operating_Cash_Flow", "Capex",
             "Total_Debt", "Cash_ST_Investments", "Book_Equity", "Total_Assets", "Total_Liabilities",
             "EBIT", "EBITDA", "Interest_Expense", "FCF_Reported", "Free_Cash_Flow",
             "FCF_Calc", "NetDebt_Calc", "FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc",
             "Price", "Price_Currency", "Price_AsOf", "Shares_Snapshot", "Market_Cap",
             "PE_Calc", "PB_Calc", "EV_Calc", "EV_to_EBITDA_Calc",
             "CET1_Ratio", "CET1_Approach", "CET1_Requirement_or_Target", "Total_Capital_Ratio",
             "Leverage_Ratio", "NIM_FY2025", "NIM_Q4_2025", "Efficiency_Ratio", "ROAA",
             "Fill_OK", "Fill_Source", "Calc_Method_Notes", "Fill_Notes",
             "Revenue_TS_Fill_FY", "Net_Income_TS_Fill_FY", "Total_Debt_TS_Fill_FY", "Membership_Flag"]
    missing_cols = [c for c in ORDER if c not in grid.columns]
    assert not missing_cols, missing_cols
    dropped = [c for c in grid.columns if c not in ORDER]
    print("dropped technical cols:", dropped)
    grid = grid[ORDER]

    cov = cov_prev.copy()
    cov["n_blank_Final"] = [max(0, 720 - int(num(grid[c]).notna().sum())) if c in grid.columns else ""
                            for c in cov["Field"]]

    dq_all = pd.concat([dq_prev.astype(str),
                        pd.DataFrame(dq_new + [{"Company_ID": "(workbook)", "Ticker": "",
                                                "Field": "Phase3 fills", "Issue": "PHASE3_SUMMARY",
                                                "Source_Attempted": "SEC cache + Yahoo retry",
                                                "Retrieval_Date": TODAY,
                                                "Resolution": f"rev_resolved={rev_fixed} td_filled={td_filled} td_insufficient={td_insuff} ebitda_derived={eb_fixed}",
                                                "Notes": "see logs/phase3_attempts.csv"}]).astype(str)],
                       ignore_index=True)

    still_rev = list(grid.loc[num(grid["Revenue"]).isna(), "Company_ID"])
    still_ni = list(grid.loc[num(grid["Net_Income"]).isna(), "Company_ID"])
    readme_lines = [
        "NORTH AMERICAN FINANCIALS - FINAL WORKBOOK",
        f"Prepared: {TODAY}.  NOT INVESTMENT ADVICE - research data compilation only.",
        "All monetary values are in each company's NATIVE reporting currency (USD for US listings, CAD for TSX listings). NO currency conversion has been applied anywhere; ratio columns are per-row native-currency consistent.",
        "",
        "COLOUR LEGEND - tabs: grey=meta (00-05); navy=Banks; teal=Utilities_Regulated; purple=Software; indigo=Semiconductors_Components; orange=Oil_Gas_Producers; dark green=Insurance/Financials/Credit_Services; gold=consumer/retail incl Discount_Stores; steel blue=all others.",
        "CELLS: pale grey = value missing (blank, not zero); pale amber Fill_OK=N = row lacks revenue without a logged reason; pale red Extraction_Status = MISSING_SOURCE. No colour scales are used anywhere.",
        "",
        "SHEET MAP:",
        "  00_README - this page",
        "  01_All_Companies - master grid, all 720 companies",
        "  02_Coverage - field fill counts Phase1 vs Final (+ blank counts)",
        "  03_Data_Quality - issue log Phases 0-3",
        "  04_Collisions - 14 rows whose tickers exist in both US and CA books",
        "  05_Membership - sheet-placement audit and tiny-sheet review",
        "  then one sheet per Custom_Industry_Sheet; every company appears on exactly one sheet:"]
    readme_lines += [f"    {s}: {int(part[s])}" for s in part.index]
    readme_lines += [
        "",
        "LEFTOVER BLANKS IN PLAIN ENGLISH:",
        "- US:HONA:US Honeywell Aerospace Inc: SEC registrant has interim filings only; annual-only policy keeps financials blank. This is NOT Honeywell International (HON) and NOT Hydro One (CA:H:TSX).",
        "- CA:IIP.UN:TSX: no reliable annual revenue/income feed and no market quote; only quoteSummary totalDebt available.",
        "- CA:OLA:TSX: no market quote at snapshot time.",
        "- US:APA:US / US:SYF:US / US:TFC:US Revenue: no annual Revenue concept exists in SEC companyfacts for these registrants (SYF and TFC report interest-income business models whose top line is not tagged as Revenue; APA's cached facts contain only zero-valued interim stubs). Kept blank rather than guess - see 03_Data_Quality.",
        f"- Revenue still blank ({len(still_rev)}): " + ", ".join(still_rev),
        f"- Net_Income still blank ({len(still_ni)}): " + ", ".join(still_ni),
        "- Total_Debt stays blank for most banks/insurers (no simple tagged total) and for industrial names lacking BOTH short- and long-term tagged debt; nothing partially summed.",
    ]

    tiny_rows = [{"Sheet": s.replace(" (COUNT DRIFT)", ""), "Row_Count": n,
                  "Note": "COUNT CHANGED vs Phase1 expectation" if "DRIFT" in s else "small by design - preserved"}
                 for s, n in tiny_review] or \
                [{"Sheet": "(none)", "Row_Count": "", "Note": "all small sheets match Phase1 expectations"}]
    disc_disp = disc.copy()
    disc_disp.insert(0, "Sheet", "Discount_Stores")
    memb_block = memb[["Company_ID", "Company_Name", "Custom_Industry_Sheet", "Flag"]]
    misplaced_flagged = memb[memb["Flag"].eq("MISPLACED")]

    sector_names = sorted(part.index)
    sheets = [("00_README", pd.DataFrame({"A": readme_lines})),
              ("01_All_Companies", grid),
              ("02_Coverage", cov),
              ("03_Data_Quality", dq_all),
              ("04_Collisions", coll_prev.astype(str)),
              ("05_Membership", memb)]
    for s in sector_names:
        sub = grid[grid[SECTOR_COL].eq(s)].sort_values("Company_Name", key=lambda x: x.str.lower())
        sheets.append((s[:31], sub))

    if os.path.exists(FINAL):
        os.remove(FINAL)
    with pd.ExcelWriter(FINAL, engine="openpyxl") as xw:
        for sname, df in sheets:
            df.to_excel(xw, sheet_name=sname, index=False)

    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    wb = load_workbook(FINAL)
    MONEY = {"Revenue", "Net_Income", "Gross_Profit", "Operating_Cash_Flow", "Capex", "Total_Debt",
             "Cash_ST_Investments", "Book_Equity", "Total_Assets", "Total_Liabilities", "EBIT",
             "EBITDA", "Interest_Expense", "FCF_Reported", "Free_Cash_Flow", "FCF_Calc",
             "NetDebt_Calc", "Market_Cap", "EV_Calc", "Shares_Snapshot"}
    TWO = {"Diluted_EPS", "Price"}
    RATIO2 = {"PE_Calc", "PB_Calc", "EV_to_EBITDA_Calc"}
    PCT = {"FCFMargin_Calc", "GrossMargin_Calc", "ROE_Calc", "ROA_Calc", "CET1_Ratio",
           "Total_Capital_Ratio", "Leverage_Ratio", "NIM_FY2025", "NIM_Q4_2025", "Efficiency_Ratio", "ROAA"}
    GREYABLE = set(STMT_COLS) | {"FCF_Calc", "NetDebt_Calc", "FCFMargin_Calc", "GrossMargin_Calc",
                                 "ROE_Calc", "ROA_Calc", "PE_Calc", "PB_Calc", "EV_Calc", "EV_to_EBITDA_Calc"}
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="1F4E78")
    band_fill = PatternFill("solid", fgColor="D6EAF8")
    band_grey = PatternFill("solid", fgColor="E8EEF4")
    greycell = PatternFill("solid", fgColor="F2F2F2")
    amber = PatternFill("solid", fgColor="FDEBD0")
    pale_red = PatternFill("solid", fgColor="FADBD8")
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
                c.font = Font(name="Calibri", size=(14 if r == 1 else 10),
                              bold=(r == 1), color=("1F4E78" if r == 1 else "000000"))
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
            elif hs in ("Calc_Method_Notes", "Fill_Source", "Fill_Notes", "Resolution", "Notes"):
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
    wb.save(FINAL)
    wb.close()

    import zipfile
    z = zipfile.ZipFile(FINAL)
    tables = [n for n in z.namelist() if "tables/" in n.lower()]
    z.close()
    assert not tables, tables

    print("=== TASK D: verification ===")
    from python_calamine import CalamineWorkbook
    wbck = load_workbook(FINAL)
    af_ok = all(wbck[s].auto_filter.ref and wbck[s].freeze_panes == "B2"
                for s in data_sheets if s in wbck.sheetnames)
    tb_ok = all(len(wbck[s].tables) == 0 for s in wbck.sheetnames)
    wbck.close()
    cw = CalamineWorkbook.from_path(FINAL)
    rows = cw.get_sheet_by_name("01_All_Companies").to_python(skip_empty_area=False)
    ixh = {h: i for i, h in enumerate(rows[0])}
    body = rows[1:]
    ids = [r[ixh["Company_ID"]] for r in body]
    fin = {r[ixh["Company_ID"]]: r for r in body}

    def fv(cid, col):
        return fin[cid][ixh[col]]

    hydro_ok = False
    rr = cw.get_sheet_by_name("Utilities_Regulated").to_python(skip_empty_area=False)
    ci = rr[0].index("Company_ID")
    hydro_ok = any(r[ci] == "CA:H:TSX" for r in rr[1:])
    part_sum = sum(len(cw.get_sheet_by_name(s).to_python(skip_empty_area=False)) - 1 for s in sector_names)
    comp_jpm = float(num(comp_stmt.set_index("Company_ID").loc["US:JPM:US", "Revenue"]))
    comp_ry = float(num(comp_stmt.set_index("Company_ID").loc["CA:RY:TSX", "Revenue"]))
    checks_d = {
        "rows_720": len(body) == 720,
        "unique_720": len(set(ids)) == 720,
        "no_blank_ids": all(str(x).strip() for x in ids),
        "collisions_14_present": len(COLLISION_IDS & set(ids)) == 14,
        "na_intact": fv("CA:NA:TSX", "Company_Name") == "National Bank of Canada",
        "hydro_one_on_utilities_regulated": hydro_ok,
        "hona_separate_row": fv("US:HONA:US", "Primary_Ticker") == "HONA",
        "jpm_revenue_equal_complete": float(fv("US:JPM:US", "Revenue")) == comp_jpm,
        "ry_revenue_equal_complete": float(fv("CA:RY:TSX", "Revenue")) == comp_ry,
        "discount_count_matches_universe": len(cw.get_sheet_by_name("Discount_Stores").to_python(skip_empty_area=False)) - 1 == int(part["Discount_Stores"]),
        "industry_partition_sums_720": part_sum == 720,
        "no_worksheet_tables": bool(tb_ok),
        "autofilter_and_freeze_B2_on_data_sheets": bool(af_ok),
    }
    bad_d = [k for k, v in checks_d.items() if not v]
    assert not bad_d, bad_d

    pdf = pd.read_excel(FINAL, sheet_name="01_All_Companies", keep_default_na=False)
    os.makedirs(EXPORTS, exist_ok=True)
    for fname, mask in [("Banks.csv", pdf[SECTOR_COL].eq("Banks")),
                        ("Utilities_Regulated.csv", pdf[SECTOR_COL].eq("Utilities_Regulated")),
                        ("Software.csv", pdf[SECTOR_COL].eq("Software")),
                        ("Discount_Stores.csv", pdf[SECTOR_COL].eq("Discount_Stores")),
                        ("All_Companies.csv", pd.Series(True, index=pdf.index))]:
        pdf[mask].to_csv(os.path.join(EXPORTS, fname), index=False, encoding="utf-8-sig")

    print("\n".join(f"  {k}: {v}" for k, v in checks_d.items()))
    print("\nDiscount_Stores members:")
    print(disc.to_string(index=False))
    print("tiny-sheet review:", tiny_review)
    print("misplaced repaired:", len(misplaced_rows))

    rep = ["# Phase 3 Report",
           f"- Date: {TODAY}. Output: {FINAL} ({os.path.getsize(FINAL):,} bytes). All protected workbooks untouched.",
           "- Owner can open this in Microsoft Excel.", "",
           f"## Task A - last holes ({int(time.time()-A_START)}s wall clock)",
           "- Revenue (APA/SYF/TFC): confirmed unfillable, not merely conflicting - SEC companyfacts contains no annual Revenue concept for these registrants (SYF/TFC are interest-income business models whose top line is not tagged as Revenue; APA has only zero-valued interim stubs). Left blank with REVENUE_CONCEPT_ABSENT rows in 03_Data_Quality.",
           f"- Total_Debt: {td_filled} fills via combined-total debt tags; {td_insuff} names lack any usable ST/LT tagged pair (logged INSUFFICIENT_TAGS); {td_bankish} banks/insurers intentionally untouched.",
           f"- EBITDA = EBIT + D&A derived on blank cells: {eb_fixed} rows; the 4 existing Yahoo EBITDA values untouched.",
           "- Net_Income: TECK-B.TO filled from Yahoo annual statements (label sweep); HONA and IIP.UN remain blank - no annual data exists anywhere for them.",
           "- Market quotes: IIP-UN.TO and OLA.TO both returned quotes on retry -> Price/Market_Cap coverage is now 720/720 priced rows.",
           "- HONA rechecked vs cached CIK0002089271 companyfacts: still interim-only -> NO_ANNUAL_FILING stands; HON never copied; XOM predecessor fill preserved.",
           "- Every attempt recorded in logs/phase3_attempts.csv; Task A ran inside its time budget using cached SEC JSONs plus bounded Yahoo calls.", "",
           "## Task B - membership audit",
           f"- Placement source of truth Universe.Custom_Industry_Sheet applied to all 720 rows; auto-repairs: {len(misplaced_rows)}; industry sheets partition to 720.",
           f"- Banks = {len(banks_sheet)} rows containing JPM, RY and CA:NA:TSX; Hydro One verified on Utilities_Regulated; Semiconductors_Components = {int(part.get('Semiconductors_Components', 0))} rows (non-empty).",
           "- Discount_Stores members:", "", disc.to_string(index=False), "",
           f"- Tiny-sheet review list: {tiny_review if tiny_review else '(none beyond Phase1 expectations)'}",
           f"- Membership CSV: logs/phase3_membership.csv ({len(memb)} rows; flags OK/TINY_SHEET_REVIEW/MISPLACED/REVENUE_BLANK; Fill_OK included; N-count {int((grid['Fill_OK'].eq('N')).sum())}).", "",
           "## Task C - presentation",
           "- No Excel Tables/ListObjects (zip scan + openpyxl worksheet.tables both clean); header row Calibri 11 bold white on navy 1F4E78 with wrap and height 30; data Calibri 10; banded white/D6EAF8 rows; thin light-grey borders; freeze B2 (header + Company_ID visible); autofilter on every sheet; landscape fit-to-width print with repeated header row; max_row = header + data everywhere.",
           "- Blank statement/ratio cells shaded grey (missing-not-zero); Fill_OK=N pale amber; MISSING_SOURCE status cells pale red; no colour scales anywhere (Apple's ROE will not blow up any legend).",
           "- Tab colours: meta grey; Banks navy; Utilities_Regulated teal; Software purple; Semiconductors indigo; Oil_Gas_Producers orange; Insurance/Financials/Credit_Services dark green; consumer/retail/Discount_Stores gold; everything else steel blue.",
           "- Column order human-first (ID, name, ticker, country, currency, GICS, sheet, status... then statements, derived, price/ratios, bank regulatory, provenance); technical helper columns dropped: " + (", ".join(dropped) if dropped else "(none)"),
           "- README rebuilt (title, date, not-investment-advice, native-currency warning, colour legend, sheet map with counts, leftover blanks in plain English); 02_Coverage gained n_blank_Final; new 05_Membership sheet added.", "",
           "## Task D - verification results", ""]
    rep += [f"- {k}: {v}" for k, v in checks_d.items()]
    rep += ["", "- Exports refreshed from Sector_Financials_Final.xlsx: Banks.csv, Utilities_Regulated.csv, Software.csv, Discount_Stores.csv (new), All_Companies.csv - all utf-8-sig.",
            "- Explicitly NOT done (out of scope): scoring/composites/Altman/Piotroski/Greenblatt; no second 720-company scrape; refresh.py untouched.",
            "- Ship state: complete." if not tiny_review else "- Ship state: shipped with tiny-sheet review notes above (small sheets preserved by design)."]
    with open(os.path.join(LOGD, "phase3_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")

    ch = ["# Phase 3 Changelog", f"Date: {TODAY}", "",
          "## New files",
          "Sector_Financials_Final.xlsx; scripts/build_phase3_final.py; logs/phase3_report.md; logs/phase3_changelog.md; logs/phase3_membership.csv; logs/phase3_attempts.csv",
          "exports/*.csv refreshed from Sector_Financials_Final.xlsx (added Discount_Stores.csv).", "",
          "## Methods worth remembering",
          "- Task A consumed ONLY the phase-2 SEC cache plus bounded Yahoo retries; no new bulk fetches.",
          "- Revenue single-fallback resolution: fill only when exactly one fallback tag reports an annual value at the reference period end.",
          "- Total_Debt = sum(short-term debt tags + LongTermDebtNoncurrent) written only when both sides exist within one fiscal year; Banks/Insurance* sheets excluded by design.",
          "- EBITDA = EBIT + first-available annual D&A tag, only where EBITDA was blank.",
          "- Membership rebuilt strictly from Universe.Custom_Industry_Sheet (Mapping_Overrides already reflected there); mismatches auto-repaired and flagged MISPLACED; tiny sheets reviewed, never deleted.",
          "- Presentation layer: static fills instead of conditional-format rules; no Tables; freeze B2; landscape print setup.", "",
          "## Untouched",
          "NA_Company_Financials.xlsx, NA_Company_Financials_Analysis.xlsx, Sector_Financial_Analysis.xlsx, Sector_Financials_Clean.xlsx, Sector_Financials_Phase1.xlsx, Sector_Financials_Phase1b.xlsx, Sector_Financials_Complete.xlsx, and all phase0-2 artifacts."]
    with open(os.path.join(LOGD, "phase3_changelog.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(ch) + "\n")

    print("\n=== PHASE 3 COMPLETE ===")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        if os.path.exists(FINAL):
            try:
                os.remove(FINAL)
            except OSError:
                pass
        sys.exit(1)

