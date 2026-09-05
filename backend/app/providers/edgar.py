"""EDGAR provider: SEC companyfacts JSON -> canonical annual rows.

Free, one call per CIK (https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json).
User-Agent from SEC_USER_AGENT. Token bucket 8 req/s; back off on 403/429.
"""
from __future__ import annotations

import json
import time
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from urllib import error, request

from app.config import SEC_USER_AGENT

BASE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


def _mark_rate_limited() -> None:
    global _rate_limited
    with _lock:
        _rate_limited += 1

# --- rate limiting (token bucket, 8/s, process-wide) ---
_lock = threading.Lock()
_tokens = 8.0
_last = time.monotonic()
_last_wait_ms = 0.0
_rate_limited = 0
RATE = 8.0


def bucket_state() -> dict:
    """Expose limiter state for job provider_stats (8/s cap unchanged)."""
    with _lock:
        return {
            "tokens_remaining": round(_tokens, 3),
            "last_token_wait_ms": int(_last_wait_ms),
            "rate_limited": _rate_limited,
        }


def _throttle() -> None:
    global _tokens, _last, _last_wait_ms
    with _lock:
        now = time.monotonic()
        _tokens = min(RATE, _tokens + (now - _last) * RATE)
        _last = now
        if _tokens < 1:
            sleep = (1 - _tokens) / RATE
            _last_wait_ms = sleep * 1000.0
            time.sleep(sleep)
            _tokens = 0.0
        else:
            _tokens -= 1.0


class EdgarClient:
    """Thin companyfacts fetcher. `fetcher` injectable for tests/stubs."""

    def __init__(self, user_agent: str | None = None, fetcher=None):
        self.user_agent = user_agent or SEC_USER_AGENT
        self._fetcher = fetcher  # callable(url) -> dict

    def _http_get_json(self, url: str) -> dict:
        req = request.Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        try:
            with request.urlopen(req, timeout=30) as resp:
                if resp.status in (403, 429):
                    _mark_rate_limited()
                    raise RuntimeError(f"SEC back-off: HTTP {resp.status}")
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            if exc.code in (403, 429):
                _mark_rate_limited()
                # conservative fixed back-off; caller decides whether to retry once
                time.sleep(2.0)
            raise

    def get_companyfacts(self, cik: int) -> dict:
        url = BASE.format(cik=cik)
        if self._fetcher is not None:
            return self._fetcher(url)
        _throttle()
        return self._http_get_json(url)


# --- XBRL tag preferences (US-GAAP and IFRS), first match wins per concept ---
_TAG_PREFS: dict[str, list[str]] = {
    "Revenue": [
        "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueGoodsNet",
        "SalesRevenueServicesNet", "SalesRevenueNet", "RevenueFromContractWithCustomer",
        "OperatingRevenue", "TotalRevenuesAndOtherIncome", "Revenue", "GrossRevenue"
    ],
    "Net_Income": ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "IncomeLossFromContinuingOperations"],
    "Diluted_EPS": ["EarningsPerShareDiluted", "DilutedEarningsLossPerShare"],
    "Gross_Profit": ["GrossProfit", "GrossMargin"],
    "Operating_Cash_Flow": ["NetCashProvidedByUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "Capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PurchaseOfPropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets", "PaymentsToAcquireProductiveAssetsNet"],
    "EBIT": ["OperatingIncomeLoss", "ProfitLossFromOperatingActivities", "OperatingIncome"],
    "Interest_Expense": ["InterestExpense", "InterestExpenseNonoperating", "FinanceCosts"],
    "Cash_ST_Investments": ["CashAndCashEquivalentsAtCarryingValue", "CashAndCashEquivalents"],
    "Book_Equity": ["StockholdersEquity", "Equity", "EquityAttributableToOwnersOfParent"],
    "Total_Assets": ["Assets"],
    "Total_Liabilities": ["Liabilities"],
    "Total_Debt": [
        "LongTermDebtAndCapitalLeaseObligations", "LongTermDebtNoncurrent",
        "LongTermDebt", "DebtAndCapitalLeaseObligations", "DebtCurrent"
    ],
    "Common_Shares": [
        "CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingDiluted",
        "CommonStockSharesIssued"
    ],
    "Accounts_Receivable": ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"],
    "Inventory": ["InventoryNet"],
    "Current_Assets": ["AssetsCurrent"],
    "Current_Liabilities": ["LiabilitiesCurrent"],
    "PPE_Net": ["PropertyPlantAndEquipmentNet"],
    "Retained_Earnings": ["RetainedEarningsAccumulatedDeficit"],
    "Stock_Based_Compensation": ["AllocatedShareBasedCompensationExpense", "ShareBasedCompensation"],
    "Interest_Income": ["InvestmentIncomeInterest", "InterestAndDividendIncomeOperating"],
    "Cost_Of_Revenue": [
        "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfServices"
    ],
    "Depreciation_Amortization": [
        "DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation", "AmortizationOfIntangibleAssets"
    ],
    "EBITDA": ["OperatingIncomeLossBeforeDepreciationAndAmortization"],
}

# Balance-sheet instant concepts (balance_sheet facts keyed by "end")
_INSTANT = {
    "Cash_ST_Investments", "Book_Equity", "Total_Assets", "Total_Liabilities", "Total_Debt", "Common_Shares",
    "Accounts_Receivable", "Inventory", "Current_Assets", "Current_Liabilities", "PPE_Net", "Retained_Earnings"
}


def parse_companyfacts(data: dict, expected_currency: str = "USD") -> list:
    """Convert a companyfacts payload into canonical AnnualStatement rows.

    Network-free; pure function over the payload. Supports US-GAAP (10-K) and
    foreign private issuers (20-F, IFRS, CNY/other native currency).
    """
    from collections import Counter
    from app.providers.base import AnnualStatement

    facts = data.get("facts", {})
    gaap = facts.get("us-gaap") or facts.get("ifrs-full") or {}
    if not gaap:
        return []

    out: dict[int, dict] = {}  # fiscal_year -> {field: value}
    ends: dict[int, str] = {}
    currencies_by_year: dict[int, list[str]] = {}
    detected_forms_by_year: dict[int, list[str]] = {}

    for concept, entries in gaap.items():
        field_name = None
        for target, prefs in _TAG_PREFS.items():
            if concept in prefs:
                field_name = target
                break
        if field_name is None:
            continue
        units = entries.get("units", {})
        for unit_key, items in units.items():
            raw_cur = unit_key.strip()
            unit_cur = raw_cur.split("/")[0].upper() if "/" in raw_cur else raw_cur.upper()

            for it in items:
                form = it.get("form")
                if form not in ("10-K", "10-K/A", "20-F", "20-F/A"):
                    continue
                fp = it.get("fp")
                frame = it.get("frame")
                end = it.get("end")
                start = it.get("start")
                if not end or len(end) < 4 or not end[:4].isdigit():
                    continue

                # Duration gate: income-statement annual facts span ~300-400 days.
                days = None
                if start:
                    try:
                        days = (date.fromisoformat(end) - date.fromisoformat(start)).days
                    except ValueError:
                        days = None
                if days is not None and not (300 <= days <= 400):
                    continue  # quarterly / stub period
                if frame and "Q" in frame:
                    continue  # explicit quarterly frame

                year = None
                is_annual = False
                if frame and len(frame) >= 6 and frame.startswith("CY") and frame[2:6].isdigit():
                    year = int(frame[2:6])
                    is_annual = True
                elif "start" not in it:
                    # instant fact (balance sheet): use period-end year
                    year = int(end[:4])
                    is_annual = True
                elif days is not None and 300 <= days <= 400:
                    # annual duration fact without a frame
                    if fp == "FY" or end[5:7] in ("12", "03", "06", "09"):
                        year = int(end[:4])
                        is_annual = True
                if year is None or not is_annual:
                    continue
                val = it.get("val")
                if val is None:
                    continue

                bucket = out.setdefault(year, {})
                existing = bucket.get(field_name)
                if existing is None:
                    bucket[field_name] = float(val)
                    bucket.setdefault("_pref", {})[field_name] = days
                else:
                    prev_days = bucket.get("_pref", {}).get(field_name)
                    if prev_days is None or (days is not None and abs(days - 365) < abs(prev_days - 365)):
                        bucket[field_name] = float(val)
                        bucket.setdefault("_pref", {})[field_name] = days

                if unit_cur not in ("SHARES", "PURE"):
                    currencies_by_year.setdefault(year, []).append(unit_cur)
                if form:
                    detected_forms_by_year.setdefault(year, []).append("20-F" if "20-F" in form else "10-K")

                if year not in ends or end > ends[year]:
                    ends[year] = end

    rows = []
    for year, bucket in out.items():
        pref = bucket.pop("_pref", None)
        cur_list = currencies_by_year.get(year, [])
        cur = Counter(cur_list).most_common(1)[0][0] if cur_list else expected_currency
        forms_list = detected_forms_by_year.get(year, [])
        primary_form = Counter(forms_list).most_common(1)[0][0] if forms_list else "10-K"

        # Accounting derivation: Gross Profit = Revenue - Cost of Revenue if not directly reported
        if bucket.get("Gross_Profit") is None and bucket.get("Revenue") is not None and bucket.get("Cost_Of_Revenue") is not None:
            bucket["Gross_Profit"] = bucket["Revenue"] - bucket["Cost_Of_Revenue"]

        # Accounting derivation: EBITDA = EBIT + Depreciation & Amortization if not directly reported
        if bucket.get("EBITDA") is None and bucket.get("EBIT") is not None and bucket.get("Depreciation_Amortization") is not None:
            bucket["EBITDA"] = bucket["EBIT"] + bucket["Depreciation_Amortization"]

        stmt = AnnualStatement(
            fiscal_year=year,
            period_end=date.fromisoformat(ends[year]) if ends.get(year) else None,
            currency=cur,
            source="sec_companyfacts",
            fields=bucket,
        )
        setattr(stmt, "filing_type", primary_form)
        rows.append(stmt)

    rows.sort(key=lambda r: r.fiscal_year or 0, reverse=True)
    return rows


def identity_from_companyfacts(data: dict) -> dict | None:
    """Optional identity enrichment from companyfacts entityName."""
    name = data.get("entityName")
    if not name:
        return None
    return {"name": name}

