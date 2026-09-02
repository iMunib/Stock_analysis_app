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


# --- XBRL tag preferences (US-GAAP), first match wins per concept ---
_TAG_PREFS: dict[str, list[str]] = {
    "Revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
    "Net_Income": ["NetIncomeLoss"],
    "Diluted_EPS": ["EarningsPerShareDiluted"],
    "Gross_Profit": ["GrossProfit"],
    "Operating_Cash_Flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "Capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "EBIT": ["OperatingIncomeLoss"],
    "Interest_Expense": ["InterestExpense", "InterestExpenseNonoperating"],
    "Cash_ST_Investments": ["CashAndCashEquivalentsAtCarryingValue"],
    "Book_Equity": ["StockholdersEquity"],
    "Total_Assets": ["Assets"],
    "Total_Liabilities": ["Liabilities"],
}

# Balance-sheet instant concepts (balance_sheet facts keyed by "end")
_INSTANT = {"Cash_ST_Investments", "Book_Equity", "Total_Assets", "Total_Liabilities"}


def parse_companyfacts(data: dict, expected_currency: str = "USD") -> list:
    """Convert a companyfacts payload into canonical AnnualStatement rows.

    Network-free; pure function over the payload. Fiscal year inferred from the
    FY frame's period end (frame='CY{year}' entries only, form 10-K).
    """
    from app.providers.base import AnnualStatement

    facts = data.get("facts", {})
    gaap = facts.get("us-gaap", {})
    if not gaap:
        return []

    entity_currency = (facts.get("dei", {}) or {}).get("EntityCommonStockSharesOutstanding", {})
    # Prefer explicitly reported currency on each fact; fall back to expected.
    out: dict[int, dict] = {}  # fiscal_year -> {field: value}
    ends: dict[int, str] = {}

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
            cur = unit_key.upper()
            if cur not in ("USD", "CAD", "USD/shares", "shares", "pure"):
                continue
            for it in items:
                form = it.get("form")
                if form not in ("10-K", "10-K/A"):
                    continue
                fp = it.get("fp")
                frame = it.get("frame")
                end = it.get("end")
                start = it.get("start")
                if not end or len(end) < 4 or not end[:4].isdigit():
                    continue

                # Duration gate (Phase 10 A): income-statement annual facts must span
                # ~360-370 days. Quarterly facts (frame "CY2017Q1", 90-day spans) were
                # slipping through the frame check and stealing FY years (MSFT $23-31B).
                days = None
                if start:
                    try:
                        days = (date.fromisoformat(end) - date.fromisoformat(start)).days
                    except ValueError:
                        days = None
                if days is not None and not (300 <= days <= 400):
                    continue  # quarterly / stub period: never a FY row
                if frame and "Q" in frame:
                    continue  # explicit quarterly frame (belt and braces)

                year = None
                is_annual = False
                if frame and len(frame) >= 6 and frame.startswith("CY") and frame[2:6].isdigit():
                    # exact annual frame CY{year} (no Q suffix survived the gate above)
                    year = int(frame[2:6])
                    is_annual = True
                elif "start" not in it:
                    # instant fact (balance sheet): use the period-end year
                    year = int(end[:4])
                    is_annual = True
                elif days is not None and 300 <= days <= 400:
                    # annual duration fact without a frame: require fp=FY December end
                    if fp == "FY" and end[5:7] == "12":
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
                    # prefer the fact closest to a full year (365d) on duplicates
                    prev_days = bucket.get("_pref", {}).get(field_name)
                    if prev_days is None or (days is not None and abs(days - 365) < abs(prev_days - 365)):
                        bucket[field_name] = float(val)
                        bucket.setdefault("_pref", {})[field_name] = days
                if year not in ends or end > ends[year]:
                    ends[year] = end

    rows = []
    for year, bucket in out.items():
        rows.append(
            AnnualStatement(
                fiscal_year=year,
                period_end=date.fromisoformat(ends[year]) if ends.get(year) else None,
                currency=expected_currency,
                source="sec_companyfacts",
                fields=bucket,
            )
        )
    rows.sort(key=lambda r: r.fiscal_year or 0, reverse=True)
    return rows


def identity_from_companyfacts(data: dict) -> dict | None:
    """Optional identity enrichment from companyfacts entityName."""
    name = data.get("entityName")
    if not name:
        return None
    return {"name": name}

