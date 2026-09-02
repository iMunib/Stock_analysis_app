# -*- coding: utf-8 -*-
"""Canadian financials extraction — IR annual statement first, yfinance as fallback.
Refactored: tickers parametrized, yfinance maps kept local (aggregator-specific labels).
Writes raw/yfinance_ca.csv (long format) + raw/yfinance_ca_meta.csv, upserted.
NOTE: IR/SEDAR annual-statement extraction is primary; yfinance is the Medium fallback
and every such cell must carry Source_Aggregator = 'Yahoo Finance' in the workbook.
"""
import os, time
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import yfinance as yf

from common import RAW

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


def _pick(df, cands):
    for c in cands:
        if c in df.index:
            return c
    return None


def _get_stmt(t, name):
    try:
        return {"is": t.get_income_stmt(freq="yearly"),
                "bs": t.get_balance_sheet(freq="yearly"),
                "cf": t.get_cash_flow(freq="yearly")}[name]
    except Exception:
        return {"is": t.income_stmt, "bs": t.balance_sheet, "cf": t.cashflow}[name]


def _normalize_symbol(sym):
    """yfinance's quoteSummary endpoint wants hyphen for dual-class shares:
    'RCI.B.TO' -> 'RCI-B.TO'. The stored ticker key stays the original symbol."""
    parts = sym.split(".")
    if len(parts) == 3 and parts[-1].upper() == "TO" and len(parts[1]) == 1:
        return f"{parts[0]}-{parts[1]}.{parts[2]}"
    return sym


def extract(tickers):
    """tickers: list of Yahoo symbols (e.g. ['RY.TO', ...]). Returns (rows_df, meta_df)."""
    rows, meta = [], {}
    for sym in tickers:
        try:
            t = yf.Ticker(_normalize_symbol(sym))
            is_df = _get_stmt(t, "is"); bs_df = _get_stmt(t, "bs"); cf_df = _get_stmt(t, "cf")
            info = t.info or {}
            meta[sym] = {"currency": info.get("financialCurrency") or info.get("currency"),
                         "shares": info.get("sharesOutstanding"), "mktcap": info.get("marketCap"),
                         "price": info.get("currentPrice") or info.get("previousClose")}

            def emit(df, mmap):
                for m, cands in mmap.items():
                    lab = _pick(df, cands)
                    if lab is None:
                        continue
                    for col in df.columns:
                        v = df.loc[lab, col]
                        if pd.notna(v):
                            rows.append({"ticker": sym, "metric": m, "period": str(col)[:10], "value": float(v), "type": "annual"})
            emit(is_df, IS_MAP); emit(bs_df, BS_MAP); emit(cf_df, CF_MAP)
        except Exception as e:
            print(f"{sym}: ERROR {type(e).__name__}: {e}")
        time.sleep(0.4)
    df = pd.DataFrame(rows, columns=["ticker", "metric", "period", "value", "type"])
    mdf = pd.DataFrame(meta).T.reset_index().rename(columns={"index": "ticker"})
    return df, mdf


def upsert(df, mdf):
    fp = os.path.join(RAW, "yfinance_ca.csv")
    if os.path.exists(fp) and len(df):
        old = pd.read_csv(fp, keep_default_na=False)
        df = pd.concat([old, df]).drop_duplicates(subset=["ticker", "metric", "period"], keep="last")
    df.to_csv(fp, index=False)
    mfp = os.path.join(RAW, "yfinance_ca_meta.csv")
    if os.path.exists(mfp) and len(mdf):
        oldm = pd.read_csv(mfp, keep_default_na=False)
        mdf = pd.concat([oldm, mdf]).drop_duplicates(subset=["ticker"], keep="last")
    mdf.to_csv(mfp, index=False)
    return len(df)


if __name__ == "__main__":
    import sys
    tk = sys.argv[1:] or ["RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "CM.TO", "NA.TO"]
    d, m = extract(tk)
    n = upsert(d, m)
    print(f"CA yfinance rows total: {n}")
