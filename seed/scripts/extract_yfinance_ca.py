# -*- coding: utf-8 -*-
"""
Phase 2 — Canadian pilot financials via yfinance (aggregator fallback; native CAD).
Corrected CamelCase labels. Banks lack GrossProfit/CostOfRevenue/CurrentAssets -> NA.
"""
import os, time
import pandas as pd
import yfinance as yf

RAW = r"C:\Users\RehmanPC\.openclaw-autoclaw\workspace\na_financials_research\raw"
CA = ["RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "CM.TO", "NA.TO",
      "H.TO", "FTS.TO", "EMA.TO", "ENB.TO", "TRP.TO",
      "CNR.TO", "CP.TO", "BCE.TO", "T.TO", "RCI-B.TO"]

IS_MAP = {
    "Revenue": ["TotalRevenue", "OperatingRevenue"],
    "CostOfRevenue": ["CostOfRevenue", "ReconciledCostOfRevenue"],
    "GrossProfit": ["GrossProfit"],
    "OperatingIncome": ["OperatingIncome", "TotalOperatingIncomeAsReported"],
    "NetIncome": ["NetIncome"],
    "EPS_diluted": ["DilutedEPS"],
    "InterestExpense": ["InterestExpense"],
    "R&D": ["ResearchAndDevelopment", "ResearchAndDevelopmentExpense"],
    "SG&A": ["SellingGeneralAndAdministration"],
    "D&A": ["ReconciledDepreciation", "DepreciationAmortizationDepletionIncomeStatement", "DepreciationAndAmortizationInIncomeStatement"],
    "EBITDA": ["EBITDA", "NormalizedEBITDA"],
    "PretaxIncome": ["PretaxIncome"],
    "TaxProvision": ["TaxProvision"],
}
BS_MAP = {
    "Cash": ["CashAndCashEquivalents", "CashCashEquivalentsAndFederalFundsSold", "CashFinancial"],
    "STInvestments": ["ShortTermInvestments", "OtherShortTermInvestments"],
    "Receivables": ["Receivables", "AccountsReceivable"],
    "Inventory": ["Inventory"],
    "Payables": ["Payables", "AccountsPayable"],
    "CurrentAssets": ["CurrentAssets"],
    "CurrentLiabilities": ["CurrentLiabilities"],
    "TotalAssets": ["TotalAssets"],
    "TotalLiabilities": ["TotalLiabilitiesNetMinorityInterest"],
    "TotalEquity": ["TotalEquityGrossMinorityInterest"],
    "LongTermDebt": ["LongTermDebt"],
    "TotalDebt": ["TotalDebt"],
    "Equity": ["StockholdersEquity"],
    "Goodwill": ["Goodwill"],
    "Intangibles": ["OtherIntangibleAssets"],
}
CF_MAP = {"OCF": ["OperatingCashFlow"], "Capex": ["CapitalExpenditure"]}


def pick(df, cands):
    for c in cands:
        if c in df.index:
            return c
    return None


def get_stmt(t, name):
    try:
        return {"is": t.get_income_stmt(freq="yearly"),
                "bs": t.get_balance_sheet(freq="yearly"),
                "cf": t.get_cash_flow(freq="yearly")}[name]
    except Exception:
        return {"is": t.income_stmt, "bs": t.balance_sheet, "cf": t.cashflow}[name]


rows = []
meta = {}
for sym in CA:
    try:
        t = yf.Ticker(sym)
        is_df = get_stmt(t, "is")
        bs_df = get_stmt(t, "bs")
        cf_df = get_stmt(t, "cf")
        info = t.info or {}
        meta[sym] = {"currency": info.get("financialCurrency") or info.get("currency"),
                     "shares": info.get("sharesOutstanding"), "mktcap": info.get("marketCap"),
                     "price": info.get("currentPrice") or info.get("previousClose")}
        def emit(df, mmap):
            for m, cands in mmap.items():
                lab = pick(df, cands)
                if lab is None:
                    continue
                for col in df.columns:
                    v = df.loc[lab, col]
                    if pd.notna(v):
                        rows.append({"ticker": sym, "metric": m, "period": str(col)[:10], "value": float(v), "type": "annual"})
        emit(is_df, IS_MAP)
        emit(bs_df, BS_MAP)
        emit(cf_df, CF_MAP)
        print(f"{sym}: OK | currency={meta[sym]['currency']} | n_is={len(is_df)} n_bs={len(bs_df)}")
    except Exception as e:
        print(f"{sym}: ERROR {type(e).__name__}: {e}")
    time.sleep(0.4)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(RAW, "yfinance_ca.csv"), index=False)
pd.DataFrame(meta).T.to_csv(os.path.join(RAW, "yfinance_ca_meta.csv"))
print("\nCA rows:", len(df), "| metrics:", sorted(df["metric"].unique()))
print("periods:", sorted(df["period"].unique()))
