"""Yahoo Finance adapter (yfinance) for CA names and prices.

yfinance is imported lazily so unit tests never require it. Calls are serialised
with a 0.2s delay. Accept sparse history — Yahoo usually exposes ~4 annual
columns. Never pads missing years.
"""
from __future__ import annotations

import math
import threading
import time
from datetime import date, datetime, timezone

_yf_lock = threading.Lock()
_last_call = 0.0
_DELAY = 0.2

# yfinance annual-frame column names -> canonical fields
COLUMN_MAP = {
    "Total Revenue": "Revenue",
    "Net Income": "Net_Income",
    "Diluted EPS": "Diluted_EPS",
    "Basic EPS": "Diluted_EPS",  # fallback only
    "Gross Profit": "Gross_Profit",
    "Operating Cash Flow": "Operating_Cash_Flow",
    "Capital Expenditure": "Capex",
    "Free Cash Flow": "Free_Cash_Flow",
    "Total Debt": "Total_Debt",
    "Cash And Cash Equivalents": "Cash_ST_Investments",
    "Cash Cash Equivalents And Short Term Investments": "Cash_ST_Investments",
    "Stockholders Equity": "Book_Equity",
    "Total Assets": "Total_Assets",
    "Total Liabilities Net Minority Interest": "Total_Liabilities",
    "Operating Income": "EBIT",
    "EBITDA": "EBITDA",
    "Interest Expense": "Interest_Expense",
    "Net Interest Income": "TopLine_Alt",
}


def _polite_wait() -> None:
    global _last_call
    with _yf_lock:
        now = time.monotonic()
        wait = _DELAY - (now - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()


def _import_yf():
    import yfinance  # lazy: only live paths

    return yfinance


def _col_to_date(col) -> date | None:
    if isinstance(col, datetime):
        return col.date()
    if isinstance(col, str):
        try:
            return date.fromisoformat(col[:10])
        except ValueError:
            return None
    if hasattr(col, "year") and hasattr(col, "month"):
        return date(col.year, col.month, getattr(col, "day", 1))
    return None


def parse_frames(frames: list, currency: str) -> list:
    """Pure: list of pandas-like DataFrames (index=column labels, columns=dates)
    -> canonical AnnualStatement rows. No yfinance import needed — tests pass
    simple objects with .columns / .empty / __getitem__ / index access."""
    from app.providers.base import AnnualStatement

    per_year: dict[int, dict] = {}
    ends: dict[int, date] = {}

    for frame in frames:
        if frame is None:
            continue
        try:
            if frame.empty:
                continue
        except AttributeError:
            continue
        for col in frame.columns:
            d = _col_to_date(col)
            if d is None:
                continue
            year = d.year
            row = frame[col]
            bucket = per_year.setdefault(year, {})
            if year not in ends or d > ends[year]:
                ends[year] = d
            for ycol, target in COLUMN_MAP.items():
                try:
                    if ycol not in row.index:
                        continue
                    val = row[ycol]
                except (KeyError, TypeError, IndexError):
                    continue
                try:
                    fv = float(val)
                except (TypeError, ValueError):
                    continue
                if math.isnan(fv):
                    continue
                bucket.setdefault(target, fv)

    rows = []
    for year, bucket in per_year.items():
        rows.append(
            AnnualStatement(
                fiscal_year=year,
                period_end=ends.get(year),
                currency=currency,
                source="yfinance",
                fields=bucket,
            )
        )
    rows.sort(key=lambda r: r.fiscal_year or 0, reverse=True)
    return rows


def fetch_annual_statements(symbol: str, currency: str) -> list:
    """Annual statements via yfinance Ticker(symbol) financials/balance/cashflow."""
    yf = _import_yf()
    _polite_wait()
    tk = yf.Ticker(symbol)
    frames = []
    for getter in ("financials", "balance_sheet", "cashflow"):
        try:
            frames.append(getattr(tk, getter, None))
        except Exception:
            frames.append(None)
    return parse_frames(frames, currency)


def fetch_price(symbol: str):
    from app.providers.base import PriceQuote

    yf = _import_yf()
    _polite_wait()
    tk = yf.Ticker(symbol)
    hist = tk.history(period="5d", auto_adjust=False)
    if hist is None or hist.empty:
        return None
    last = hist.iloc[-1]
    price = float(last["Close"])
    idx = hist.index[-1]
    as_of = idx.date() if hasattr(idx, "date") else None
    info_cur = None
    try:
        info_cur = tk.info.get("financialCurrency") or tk.info.get("currency")
    except Exception:
        info_cur = None
    return PriceQuote(
        price=price,
        currency=info_cur or "USD",
        as_of=as_of,
        source="yfinance",
        fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
