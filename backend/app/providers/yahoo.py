"""Yahoo Finance adapter (yfinance) for CA names and prices.

yfinance is imported lazily so unit tests never require it. Calls are serialised
with a 0.2s delay. Accept sparse history - Yahoo usually exposes ~4 annual
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
    -> canonical AnnualStatement rows. No yfinance import needed - tests pass
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


def _clean_symbol(symbol: str) -> str:
    s = (symbol or "").strip()
    if s.upper().endswith(".TO"):
        base = s[:-3]
        return base.replace(".", "-") + ".TO"
    return s


def fetch_annual_statements(symbol: str, currency: str) -> list:
    """Annual statements via yfinance Ticker(symbol) financials/balance/cashflow."""
    yf = _import_yf()
    _polite_wait()
    tk = yf.Ticker(_clean_symbol(symbol))
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
    tk = yf.Ticker(_clean_symbol(symbol))
    hist = tk.history(period="5d", auto_adjust=False)
    if hist is None or hist.empty:
        return None
    last = hist.iloc[-1]
    price = float(last["Close"])
    idx = hist.index[-1]
    as_of = idx.date() if hasattr(idx, "date") else None
    trading_cur = "USD"
    fin_cur = None
    shares = None
    market_cap = None
    sector = None
    industry = None
    try:
        info = tk.info or {}
        trading_cur = info.get("currency") or "USD"
        fin_cur = info.get("financialCurrency") or trading_cur
        sh = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        if sh is not None:
            shares = float(sh)
        mc = info.get("marketCap")
        if mc is not None:
            market_cap = float(mc)
        sector = info.get("sector")
        industry = info.get("industry")
    except Exception:
        pass

    return PriceQuote(
        price=price,
        currency=trading_cur,
        as_of=as_of,
        source="yfinance",
        fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
        shares=shares,
        market_cap=market_cap,
        financial_currency=fin_cur,
        sector=sector,
        industry=industry,
    )


def fetch_profile_and_quarterly(symbol: str) -> dict:
    """Fetch company summary, dividend metrics, next earnings date, and quarterly income statement."""
    yf = _import_yf()
    _polite_wait()
    try:
        tk = yf.Ticker(_clean_symbol(symbol))
    except Exception:
        return {"summary": None, "dividend_yield": None, "dividend_rate": None, "next_earnings_date": None, "quarterly": None}

    summary = None
    dividend_yield = None
    dividend_rate = None
    next_earnings = None

    try:
        info = tk.info or {}
        raw_sum = info.get("longBusinessSummary")
        if raw_sum and isinstance(raw_sum, str) and raw_sum.strip():
            summary = raw_sum.strip()[:280]

        dy = info.get("dividendYield")
        if dy is not None:
            try:
                dividend_yield = float(dy)
            except (ValueError, TypeError):
                dividend_yield = None

        dr = info.get("dividendRate")
        if dr is not None:
            try:
                dividend_rate = float(dr)
            except (ValueError, TypeError):
                dividend_rate = None

        et = info.get("earningsTimestamp")
        if et is not None:
            try:
                next_earnings = datetime.fromtimestamp(float(et), tz=timezone.utc).strftime("%Y-%m-%d")
            except (ValueError, TypeError, OSError):
                next_earnings = None

        if not next_earnings:
            try:
                cal = getattr(tk, "calendar", None)
                if cal and isinstance(cal, dict):
                    e_dates = cal.get("Earnings Date")
                    if e_dates and isinstance(e_dates, (list, tuple)) and len(e_dates) > 0:
                        first = e_dates[0]
                        if hasattr(first, "strftime"):
                            next_earnings = first.strftime("%Y-%m-%d")
                        elif isinstance(first, str):
                            next_earnings = first[:10]
            except Exception:
                pass
    except Exception:
        pass

    # Quarterly income statement: last 4 quarters
    quarterly: list[dict] | None = None
    try:
        q_frame = getattr(tk, "quarterly_income_stmt", None)
        if q_frame is None or getattr(q_frame, "empty", True):
            q_frame = getattr(tk, "quarterly_financials", None)

        if q_frame is not None and not getattr(q_frame, "empty", True):
            quarters = []
            for col in list(q_frame.columns)[:4]:
                d = _col_to_date(col)
                date_str = d.isoformat() if d else str(col)[:10]
                row = q_frame[col]

                def _val(keys: list[str]) -> float | None:
                    for k in keys:
                        if k in row.index:
                            try:
                                v = float(row[k])
                                if not math.isnan(v):
                                    return v
                            except (ValueError, TypeError):
                                pass
                    return None

                rev = _val(["Total Revenue", "Operating Revenue", "Revenue"])
                ni = _val(["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operation Net Minority Interest"])
                eps = _val(["Diluted EPS", "Basic EPS"])

                quarters.append({
                    "date": date_str,
                    "revenue": rev,
                    "net_income": ni,
                    "diluted_eps": eps,
                })
            if quarters:
                quarterly = quarters
    except Exception:
        quarterly = None

    return {
        "summary": summary,
        "dividend_yield": dividend_yield,
        "dividend_rate": dividend_rate,
        "next_earnings_date": next_earnings,
        "quarterly": quarterly,
    }


def fetch_key_stats(symbol: str) -> dict:
    """Fetch extended key statistics from Yahoo Finance info dict.

    Returns a flat dict of {metric_name: {"value", "str_value", "currency", "as_of"}}.
    All values are optional - absent fields return None without raising.
    Never mixes currencies.
    """
    yf = _import_yf()
    _polite_wait()
    try:
        tk = yf.Ticker(_clean_symbol(symbol))
        info = tk.info or {}
    except Exception:
        return {}

    import math as _math
    from datetime import date as _date, datetime as _datetime

    today = _date.today().isoformat()
    trading_cur = (info.get("currency") or "").upper() or None

    def _float(key: str) -> float | None:
        v = info.get(key)
        try:
            f = float(v)
            return None if _math.isnan(f) else f
        except (TypeError, ValueError):
            return None

    def _date_str(key: str) -> str | None:
        ts = info.get(key)
        if ts is None:
            return None
        try:
            from datetime import timezone as _tz
            return _datetime.fromtimestamp(float(ts), tz=_tz.utc).strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError):
            return None

    metrics: dict = {}

    def _add(name: str, value: float | None, *, str_value: str | None = None, currency: str | None = None) -> None:
        metrics[name] = {"value": value, "str_value": str_value, "currency": currency, "as_of": today}

    _add("market_cap", _float("marketCap"), currency=trading_cur)
    _add("enterprise_value", _float("enterpriseValue"), currency=trading_cur)
    _add("shares_outstanding", _float("sharesOutstanding"))
    _add("float_shares", _float("floatShares"))
    _add("trailing_pe", _float("trailingPE"))
    _add("forward_pe", _float("forwardPE"))
    _add("peg_ratio", _float("pegRatio"))
    _add("price_to_sales", _float("priceToSalesTrailingTwelveMonths"))
    _add("price_to_book", _float("priceToBook"))
    _add("ev_to_revenue", _float("enterpriseToRevenue"))
    _add("ev_to_ebitda", _float("enterpriseToEbitda"))
    _add("beta", _float("beta"))
    _add("52w_high", _float("fiftyTwoWeekHigh"), currency=trading_cur)
    _add("52w_low", _float("fiftyTwoWeekLow"), currency=trading_cur)
    _add("52w_change_pct", _float("52WeekChange"))
    _add("50d_avg", _float("fiftyDayAverage"), currency=trading_cur)
    _add("200d_avg", _float("twoHundredDayAverage"), currency=trading_cur)
    _add("institutional_ownership_pct", _float("heldPercentInstitutions"))
    _add("insider_ownership_pct", _float("heldPercentInsiders"))
    _add("short_ratio", _float("shortRatio"))
    _add("short_pct_float", _float("shortPercentOfFloat"))
    _add("dividend_yield", _float("dividendYield"))
    _add("dividend_rate", _float("dividendRate"), currency=trading_cur)
    _add("payout_ratio", _float("payoutRatio"))
    _add("ex_dividend_date", None, str_value=_date_str("exDividendDate"))
    _add("current_ratio", _float("currentRatio"))
    _add("debt_to_equity", _float("debtToEquity"))
    _add("book_value_per_share", _float("bookValue"), currency=trading_cur)
    _add("profit_margin", _float("profitMargins"))
    _add("operating_margin", _float("operatingMargins"))
    _add("gross_margin", _float("grossMargins"))
    _add("revenue_growth_yoy", _float("revenueGrowth"))
    _add("earnings_growth_yoy", _float("earningsGrowth"))
    next_earnings = _date_str("earningsTimestamp") or _date_str("earningsTimestampStart")
    _add("next_earnings_date", None, str_value=next_earnings)
    return metrics