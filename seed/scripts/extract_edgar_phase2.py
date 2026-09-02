# -*- coding: utf-8 -*-
"""
Phase 2 — SEC EDGAR XBRL (companyfacts) extraction for US pilot names.
Pulls 5 fiscal years of annual (10-K) raw values + latest-quarter TTM for flow metrics.
Outputs raw/edgar_annual.csv, raw/edgar_ttm.csv, caches raw JSON per CIK.
"""
import json, os, time, urllib.request
import pandas as pd

RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"
os.makedirs(RAW, exist_ok=True)
HEADERS = {"User-Agent": "OpenClaw Research contact@openclaw.local"}

US_TICKERS = ["JPM", "BAC", "WFC", "NEE", "DUK", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "UNP"]

# metric -> candidate us-gaap tags (tried in order)
FLOW = {
    "Revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "RegulatedAndUnregulatedOperatingRevenue", "RevenueFromContractWithCustomerIncludingAssessedTax", "RevenuesNetOfInterestExpense", "Revenues"],
    "CostOfRevenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "GrossProfit": ["GrossProfit"],
    "OperatingIncome": ["OperatingIncomeLoss"],
    "NetIncome": ["NetIncomeLoss"],
    "InterestExpense": ["InterestExpense", "InterestExpenseNonoperating"],
    "R&D": ["ResearchAndDevelopmentExpense"],
    "SG&A": ["SellingGeneralAndAdministrativeExpense"],
    "D&A": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet"],
    "OCF": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "Capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "PretaxIncome": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"],
    "TaxProvision": ["IncomeTaxExpenseBenefit"],
    "NI_Consolidated": ["ProfitLoss", "NetIncomeLoss"],
}
BS = {
    "Cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "STInvestments": ["ShortTermInvestments", "MarketableSecuritiesCurrent"],
    "Receivables": ["AccountsReceivableNetCurrent"],
    "Inventory": ["InventoryNet"],
    "Payables": ["AccountsPayableCurrent"],
    "CurrentAssets": ["AssetsCurrent"],
    "CurrentLiabilities": ["LiabilitiesCurrent"],
    "TotalAssets": ["Assets"],
    "TotalLiabilities": ["Liabilities"],
    "TotalEquity": ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "MinorityInterest": ["MinorityInterest"],
    "LongTermDebt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "ShortTermDebt": ["LongTermDebtCurrent", "DebtCurrent"],
    "Equity": ["StockholdersEquity"],
    "Goodwill": ["Goodwill"],
    "Intangibles": ["FiniteLivedIntangibleAssetsNet"],
}
EPS = {"EPS_diluted": ["EarningsPerShareDiluted"]}
SHARES = {"SharesDiluted": ["WeightedAverageNumberOfDilutedSharesOutstanding"]}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def cik_map():
    data = json.loads(get("https://www.sec.gov/files/company_tickers.json"))
    return {d["ticker"]: d["cik_str"] for d in data.values()}


def facts(cik):
    fp = os.path.join(RAW, f"edgar_cik{cik}.json")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    data = json.loads(get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"))
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    time.sleep(0.2)
    return data


def _unit_series(d, candidates, is_per_share):
    for tag in candidates:
        node = d.get(tag)
        if not node:
            continue
        units = node.get("units", {})
        keys = ["USD/shares", "USD"] if is_per_share else ["USD"]
        for k in keys:
            if k in units:
                return tag, k, units[k]
    return None, None, None


def annual_vals(d, candidates, is_per_share=False):
    """Return ({fy: val}, tag_name) for 10-K FY frames, choosing the candidate tag
    with the most recent data. For each fy, the annual figure is the fact with the
    latest 'end' (FY year-end)."""
    keys = ["USD/shares", "USD"] if is_per_share else ["USD"]
    best_series, best_max, best_tag = {}, -1, None
    for tag in candidates:
        node = d.get(tag)
        if not node:
            continue
        for k in keys:
            if k not in node.get("units", {}):
                continue
            by_fy = {}
            for it in node["units"][k]:
                if it.get("form") == "10-K" and it.get("fp") == "FY" and it.get("fy") is not None:
                    by_fy.setdefault(it["fy"], []).append(it)
            series = {}
            for fy, lst in by_fy.items():
                b = max(lst, key=lambda x: (x.get("end") or "", x.get("filed") or ""))
                series[fy] = b.get("val")
            if series and max(series) > best_max:
                best_max = max(series)
                best_series = series
                best_tag = tag
    return best_series, best_tag


def ttm_vals(d, candidates, is_per_share=False):
    """Sum latest 4 quarterly values; choose candidate tag with the most recent data."""
    keys = ["USD/shares", "USD"] if is_per_share else ["USD"]
    best_series, best_end = {}, ""
    for tag in candidates:
        node = d.get(tag)
        if not node:
            continue
        for k in keys:
            if k not in node.get("units", {}):
                continue
            best = {}
            for it in node["units"][k]:
                fp = it.get("fp"); end = it.get("end")
                if fp in ("Q1", "Q2", "Q3", "Q4") and end:
                    if end not in best or it.get("filed", "") > best[end]["filed"]:
                        best[end] = {"val": it.get("val"), "filed": it.get("filed", "")}
            ends = sorted(best)
            if len(ends) >= 4:
                last4 = ends[-4:]
                series = {"value": sum(best[e]["val"] for e in last4), "end": last4[-1], "n_quarters": 4}
                if last4[-1] > best_end:
                    best_end = last4[-1]
                    best_series = series
    return best_series


cmap = cik_map()
annual_rows = []
ttm_rows = []
for t in US_TICKERS:
    cik = cmap.get(t)
    if not cik:
        print(f"{t}: CIK not found")
        continue
    d = facts(cik)
    gaap = d["facts"].get("us-gaap", {})
    # flow metrics (annual 5y + TTM)
    for m, cands in {**FLOW, **EPS}.items():
        av, tag = annual_vals(gaap, cands, is_per_share=(m == "EPS_diluted"))
        for fy in sorted(av):
            annual_rows.append({"ticker": t, "metric": m, "fy": fy, "value": av[fy], "type": "annual", "tag": tag})
        tv = ttm_vals(gaap, cands, is_per_share=(m == "EPS_diluted"))
        if tv:
            ttm_rows.append({"ticker": t, "metric": m, "value": tv["value"], "end": tv["end"], "type": "ttm"})
    # balance sheet (annual only + latest point-in-time)
    for m, cands in {**BS, **SHARES}.items():
        av, tag = annual_vals(gaap, cands, is_per_share=False)
        for fy in sorted(av):
            annual_rows.append({"ticker": t, "metric": m, "fy": fy, "value": av[fy], "type": "annual", "tag": tag})
    print(f"{t}: done ({cik})")

pd.DataFrame(annual_rows).to_csv(os.path.join(RAW, "edgar_annual.csv"), index=False)
pd.DataFrame(ttm_rows).to_csv(os.path.join(RAW, "edgar_ttm.csv"), index=False)
print("\nannual rows:", len(annual_rows), "| ttm rows:", len(ttm_rows))
print("fiscal years present:", sorted({r["fy"] for r in annual_rows}))
