import json
import os
import sys
import time
import traceback
import urllib.request
import urllib.error

import pandas as pd

ROOT = r"C:\Users\RehmanPC\Documents\NA_Financials_ClaudeCode_Handoff\na_financials_research"
P1 = os.path.join(ROOT, "Sector_Financials_Phase1.xlsx")
CANON = os.path.join(ROOT, "NA_Company_Financials.xlsx")
LOGD = os.path.join(ROOT, "logs")
CACHE = r"C:\Users\RehmanPC\AppData\Local\Temp\opencode\p2cache"
UA = {"User-Agent": "Rehman Individual Investor Research rehman.research@proton.me"}
ATTEMPTS = os.path.join(LOGD, "phase2_attempts.csv")
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"

TAG_MAP = {
    "Revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"],
    "Net_Income": ["NetIncomeLoss", "ProfitLoss"],
    "Diluted_EPS": ["EarningsPerShareDiluted"],
    "Gross_Profit": ["GrossProfit"],
    "EBIT": ["OperatingIncomeLoss"],
    "OCF": ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "Capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "Cash_ST_Investments": ["CashAndCashEquivalentsAtCarryingValue",
                            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "Book_Equity": ["StockholdersEquity",
                    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "Total_Assets": ["Assets"],
    "Total_Liabilities": ["Liabilities"],
    "Interest_Expense": ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
                         "InterestIncomeExpenseNet"],
}
CONFLICT_REL_TOL = 0.10
SUCCESSOR_ALTS = {"US:XOM:US": ["0000034088"]}
DEBT_LT_TOTAL = ["DebtLongtermAndShorttermCombinedAmount", "LongTermDebt"]
DEBT_LT_NC = ["LongTermDebtNoncurrent"]
DEBT_ST = ["DebtCurrent", "ShortTermBorrowings", "LongTermDebtCurrent", "OtherShortTermBorrowings"]
STALE_DAYS = 370
STOP_STATUSES = {402, 403, 429}


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def log_attempt(row):
    df = pd.DataFrame([row])
    hdr = not os.path.exists(ATTEMPTS)
    df.to_csv(ATTEMPTS, mode="a", header=hdr, index=False, encoding="utf-8")


def load_attempts_ok():
    if not os.path.exists(ATTEMPTS):
        return {}
    a = pd.read_csv(ATTEMPTS, keep_default_na=False)
    a = a[(a["kind"] == "companyfacts") & (a["status"].astype(str) == "200")]
    return dict(zip(a["cik"].astype(str), a["company_id"]))


def token_overlap(a, b):
    ta = {t.strip(".,&'").lower() for t in str(a).replace("/", " ").split() if len(t) > 2}
    tb = {t.strip(".,&'").lower() for t in str(b).replace("/", " ").split() if len(t) > 2}
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


def pick_latest(tag_node):
    units = tag_node.get("units", {})
    for unit_name, entries in units.items():
        if not (unit_name.upper().startswith("USD") or unit_name == "shares"):
            continue
        annual = [e for e in entries
                  if str(e.get("form", "")).startswith("10-K") or e.get("fp") == "FY"]
        if not annual:
            continue
        dedup = {}
        for e in annual:
            k = e.get("end", "")
            if k not in dedup or str(e.get("filed", "")) > str(dedup[k].get("filed", "")):
                dedup[k] = e
        best = sorted(dedup.items(), key=lambda kv: kv[0])[-1][1]
        return {"val": float(best["val"]), "end": best.get("end"), "fy": best.get("fy"),
                "fp": best.get("fp"), "form": best.get("form"), "accn": best.get("accn"),
                "unit": unit_name}
    return None


def close(a, b, tol=CONFLICT_REL_TOL):
    m = max(abs(a), abs(b))
    return abs(a - b) <= tol * m


def extract_concepts(facts):
    from datetime import datetime
    gaap = facts.get("facts", {}).get("us-gaap", {})
    raw = {}
    interim_skipped = []
    for field, tags in TAG_MAP.items():
        picks = []
        had_any_tag = False
        for t in tags:
            node = gaap.get(t)
            if not node:
                continue
            had_any_tag = True
            p = pick_latest(node)
            if p:
                p["tag"] = t
                picks.append(p)
        if picks:
            raw[field] = picks
        elif had_any_tag:
            interim_skipped.append(field)

    debt_parts = {}
    for role, tags in [("lt_total", DEBT_LT_TOTAL), ("lt_nc", DEBT_LT_NC), ("st", DEBT_ST)]:
        for t in tags:
            node = gaap.get(t)
            if not node:
                continue
            p = pick_latest(node)
            if p:
                p["tag"] = t
                debt_parts[role] = p
                break

    all_ends = [p["end"] for ps in raw.values() for p in ps if p.get("end")]
    all_ends += [p["end"] for p in debt_parts.values() if p.get("end")]
    ref_end = max(all_ends) if all_ends else ""

    def to_d(s):
        try:
            return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

    ref_d = to_d(ref_end)
    stale = []

    def fresh(p):
        d = to_d(p.get("end", ""))
        if ref_d is None or d is None:
            return True
        return (ref_d - d).days <= STALE_DAYS

    for role in list(debt_parts.keys()):
        if not fresh(debt_parts[role]):
            stale.append(f"Total_Debt:{debt_parts[role]['tag']}@{debt_parts[role]['end']}")
            del debt_parts[role]

    out, statuses = {}, {}

    def resolve(field):
        kept = [dict(p) for p in raw.get(field, []) if fresh(p)]
        for p in raw.get(field, []):
            if not fresh(p):
                stale.append(f"{field}:{p['tag']}@{p['end']}")
        if not kept:
            statuses[field] = "no_fresh"
            return
        primary_tag = TAG_MAP[field][0]
        prim = next((p for p in kept if p["tag"] == primary_tag), None)
        if prim:
            diffs = [f"{p['tag']}:{p['val']:,.0f}" for p in kept if p["tag"] != primary_tag
                     and not close(prim["val"], p["val"])]
            prim["resolve"] = "primary" + ("|alt_differs:" + ";".join(diffs) if diffs else "")
            out[field] = prim
            statuses[field] = "primary"
            return
        base = kept[0]["val"]
        hard = [p["tag"] for p in kept[1:] if not close(base, p["val"])]
        if hard:
            statuses[field] = f"conflict:{kept[0]['tag']}vs{','.join(hard)}"
            return
        kept[0]["resolve"] = "fallback"
        out[field] = kept[0]
        statuses[field] = "fallback"

    for field in TAG_MAP:
        if field in raw:
            resolve(field)

    lt_total = debt_parts.get("lt_total")
    lt_nc = debt_parts.get("lt_nc")
    st_pick = debt_parts.get("st")
    if lt_total:
        debt = dict(lt_total)
        debt["formula"] = f"{lt_total['tag']}(total)"
        out["Total_Debt"] = debt
        statuses["Total_Debt"] = "primary"
    elif lt_nc:
        parts_val = lt_nc["val"] + (st_pick["val"] if st_pick else 0.0)
        out["Total_Debt"] = {"val": parts_val, "end": lt_nc["end"], "fy": lt_nc["fy"],
                             "fp": lt_nc["fp"], "form": lt_nc["form"], "accn": lt_nc["accn"],
                             "unit": lt_nc["unit"],
                             "tag": f"{lt_nc['tag']}+{st_pick['tag']}" if st_pick else lt_nc["tag"],
                             "formula": f"{lt_nc['tag']}+{st_pick['tag']}" if st_pick else lt_nc["tag"],
                             "resolve": "composite"}
        statuses["Total_Debt"] = "composite"
    return out, statuses, stale, interim_skipped


def main():
    os.makedirs(CACHE, exist_ok=True)
    uni = pd.read_excel(CANON, sheet_name="Universe", keep_default_na=False)
    p1 = pd.read_excel(P1, sheet_name="01_All_Companies", keep_default_na=False)
    uix = uni.set_index("Company_ID")

    holes = p1[(p1["Revenue"].astype(str).str.strip() == "") |
               (p1["Net_Income"].astype(str).str.strip() == "") |
               (p1["Total_Debt"].astype(str).str.strip() == "")]
    queue = sorted(holes["Company_ID"].tolist())
    print(f"B1 allowlist ({len(queue)} companies):")
    for q in queue:
        print("  ", q)
    assert len(queue) <= 90, f"allowlist too large: {len(queue)}"

    us_ids = sorted(p1.loc[p1["Company_ID"].str.startswith("US:"), "Company_ID"])
    print(f"\nB3 target US names: {len(us_ids)}")

    tm_path = os.path.join(CACHE, "company_tickers.json")
    if os.path.exists(tm_path):
        tmap_raw = json.load(open(tm_path))
    else:
        st, body = http_get(TICKER_MAP_URL)
        assert st == 200
        open(tm_path, "wb").write(body)
        tmap_raw = json.loads(body)
    tmap = {v["ticker"].upper(): (str(v["cik_str"]).zfill(10), v["title"]) for v in tmap_raw.values()}
    print("SEC ticker map size:", len(tmap))

    done = load_attempts_ok()
    todo = []
    overrides = 0
    for cid in us_ids:
        sym = str(uix.at[cid, "Primary_Ticker"]).strip().upper()
        ucik = str(uix.at[cid, "CIK_SEDAR"]).strip()
        ucik = ucik.zfill(10) if ucik else ""
        mcik = tmap.get(sym, ("", ""))[0]
        cik = mcik or ucik
        if mcik and ucik and mcik != ucik:
            overrides += 1
        todo.append((cid, sym, cik))
    print("CIK corrections (Universe -> SEC map):", overrides)

    results = {}
    stop = None
    n_new = 0
    for i, (cid, sym, cik) in enumerate(todo):
        if stop:
            break
        if not cik:
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid, "kind": "companyfacts",
                         "cik": "", "symbol": sym, "status": "NO_CIK", "fields_filled": 0, "note": "no CIK from map or universe"})
            continue
        cpath = os.path.join(CACHE, f"cik_{cik}.json")
        if cik in done:
            try:
                facts = json.load(open(cpath))
                results[cid] = facts
                continue
            except Exception:
                pass
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        try:
            st, body = http_get(url)
            open(cpath, "wb").write(body)
            facts = json.loads(body)
            results[cid] = facts
            done[cik] = cid
            n_new += 1
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid, "kind": "companyfacts",
                         "cik": cik, "symbol": sym, "status": str(st), "fields_filled": "", "note": "cached"})
            time.sleep(0.12)
        except urllib.error.HTTPError as e:
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid, "kind": "companyfacts",
                         "cik": cik, "symbol": sym, "status": str(e.code), "fields_filled": 0,
                         "note": str(e.reason)})
            if e.code in STOP_STATUSES:
                stop = f"HTTP {e.code} at {cid} ({sym}); stopping per rules"
                break
        except Exception as e:
            log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid, "kind": "companyfacts",
                         "cik": cik, "symbol": sym, "status": "ERR", "fields_filled": 0, "note": repr(e)[:120]})
        if i % 50 == 0:
            print(f"  ...{i}/{len(todo)} fetched={len(results)}")

    if stop:
        print("\nSTOP CONDITION:", stop)

    fills = {}
    meta_rows = []
    n_conflict_companies = 0
    for cid, facts in results.items():
        ent = str(facts.get("facts", {}).get("dei", {}).get("entityName", "") or facts.get("entityName", ""))
        sym = str(uix.at[cid, "Primary_Ticker"]).strip().upper()
        sec_title = tmap.get(sym, ("", ""))[1]
        concepts, statuses, stale, interim_skipped = extract_concepts(facts)
        had_conflict = False
        for field, st in statuses.items():
            if str(st).startswith("conflict"):
                had_conflict = True
                meta_rows.append({"Company_ID": cid, "status": "TAG_CONFLICT",
                                  "entityName": f"{field}:{st}", "sec_title": ""})
        for s in stale:
            meta_rows.append({"Company_ID": cid, "status": "STALE_TAG_SKIPPED",
                              "entityName": s, "sec_title": ""})
        if had_conflict:
            n_conflict_companies += 1
        if concepts:
            fills[cid] = concepts
        note = f"interim_only_skipped={','.join(interim_skipped)}" if interim_skipped else ""
        meta_rows.append({"Company_ID": cid, "status": "OK", "entityName": ent[:80],
                          "sec_title": (note if not sec_title else f"{sec_title[:60]}|{note}")})

    alt_meta = []
    for cid, alt_ciks in SUCCESSOR_ALTS.items():
        sym = str(uix.at[cid, "Primary_Ticker"]).strip().upper()
        primary_end = max((v.get("end", "") for v in fills.get(cid, {}).values()), default="")
        best_alt, best_ent, best_end = None, "", ""
        for acik in alt_ciks:
            cpath = os.path.join(CACHE, f"cik_{acik}.json")
            try:
                if os.path.exists(cpath):
                    afacts = json.load(open(cpath))
                else:
                    st, body = http_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{acik}.json")
                    open(cpath, "wb").write(body)
                    afacts = json.loads(body)
                    log_attempt({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "company_id": cid,
                                 "kind": "companyfacts_successor", "cik": acik, "symbol": sym,
                                 "status": str(st), "fields_filled": "", "note": "successor-alt cached"})
            except Exception as e:
                alt_meta.append({"Company_ID": cid, "status": "SUCCESSOR_ALT_ERROR",
                                 "entityName": acik, "sec_title": repr(e)[:80]})
                continue
            aent = str(afacts.get("facts", {}).get("dei", {}).get("entityName", ""))
            aconcepts, _, _, _ = extract_concepts(afacts)
            aend = max((v.get("end", "") for v in aconcepts.values()), default="")
            alt_meta.append({"Company_ID": cid, "status": "SUCCESSOR_ALT_SEEN",
                             "entityName": f"{aent} latest_annual_end={aend}",
                             "sec_title": f"{len(aconcepts)} concepts"})
            if aend > best_end:
                best_alt, best_ent, best_end = aconcepts, aent, aend
        p_ent = ""
        if cid in results:
            p_ent = str(results[cid].get("facts", {}).get("dei", {}).get("entityName", ""))
        alt_meta.append({"Company_ID": cid, "status": "SUCCESSOR_DECISION",
                         "entityName": f"primary={p_ent} end={primary_end} | alt={best_ent} end={best_end}",
                         "sec_title": "alt used" if best_end > primary_end else "primary kept"})
        if best_alt and best_end > primary_end:
            fills[cid] = best_alt
    meta_rows.extend(alt_meta)

    hona_cid = "US:HONA:US"
    print("\nSummary:")
    print("  companies with concept fills:", len(fills))
    print("  TAG_CONFLICT events:", sum(1 for m in meta_rows if m['status'] == 'TAG_CONFLICT'),
          "across", n_conflict_companies, "companies")
    print("  HONA fetched:", hona_cid in results,
          "| HONA annual concepts:", sorted(fills.get(hona_cid, {}).keys()))
    xom = fills.get("US:XOM:US", {})
    print("  XOM chosen entity end:", max((v.get('end', '') for v in xom.values()), default='NONE'),
          "| XOM Revenue:", xom.get('Revenue', {}).get('val'))

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "fills": fills, "meta": meta_rows, "stop_condition": stop or "",
           "allowlist_queue": queue}
    path = os.path.join(LOGD, "phase2_edgar_fills.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("wrote", path, "| companies with concept fills:", len(fills))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
