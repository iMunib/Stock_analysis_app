"""Exchange & TradingView Symbol Resolver and Suggestion Service.

Maps tickers and company IDs to their authoritative exchange (NASDAQ, NYSE, TSX, etc.)
and generates authoritative TradingView symbol strings (e.g. 'NASDAQ:AAPL', 'NYSE:BABA', 'TSX:RY').
Also powers the interactive typeahead suggestions endpoint.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Score
from app.services.ids import normalize_company_id

logger = logging.getLogger("exchange_resolver")

_EXCHANGE_MAP: dict[str, str] | None = None


def _load_exchange_map() -> dict[str, str]:
    """Load pre-indexed SEC ticker -> exchange mapping."""
    global _EXCHANGE_MAP
    if _EXCHANGE_MAP is not None:
        return _EXCHANGE_MAP

    candidates = [
        Path("seed/raw/sec_ticker_exchange.json"),
        Path("/seed/raw/sec_ticker_exchange.json"),
        Path("../seed/raw/sec_ticker_exchange.json"),
        Path("data/sec_ticker_exchange.json"),
        Path(__file__).resolve().parents[2] / "seed" / "raw" / "sec_ticker_exchange.json",
        Path(__file__).resolve().parents[1] / "seed" / "raw" / "sec_ticker_exchange.json",
    ]
    path = next((p for p in candidates if p.is_file()), None)
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                _EXCHANGE_MAP = json.load(f)
                return _EXCHANGE_MAP
        except Exception as exc:
            logger.warning("Failed reading exchange map from %s: %s", path, exc)

    _EXCHANGE_MAP = {}
    return _EXCHANGE_MAP


def get_exchange(ticker: str, country: str = "US") -> str:
    """Resolve authoritative exchange name ('NASDAQ', 'NYSE', 'TSX', etc.)."""
    tk = (ticker or "").strip().upper()
    if not tk:
        return "NASDAQ" if country == "US" else "TSX"

    if country == "CA" or tk.endswith(".TO") or tk.endswith(".TSX") or tk.endswith(".V"):
        if tk.endswith(".V"):
            return "TSXV"
        return "TSX"

    clean_tk = tk
    if clean_tk.endswith(".US"):
        clean_tk = clean_tk[:-3]
    clean_tk = clean_tk.replace(".", "-")

    ex_map = _load_exchange_map()
    if clean_tk in ex_map:
        return ex_map[clean_tk]
    if tk in ex_map:
        return ex_map[tk]

    # Well-known NYSE listings fallback if not in json
    known_nyse = {
        "BRK.A", "BRK.B", "BRK-A", "BRK-B", "JPM", "BAC", "WFC", "C", "GS", "MS",
        "JNJ", "PG", "XOM", "CVX", "KO", "MCD", "WMT", "HD", "DIS", "IBM", "GE",
        "GM", "F", "T", "VZ", "RTX", "MMM", "CAT", "BA", "UNH", "ABBV", "MRK",
        "PFE", "ABT", "BMY", "LLY", "CRM", "ACN", "SLB", "HAL", "COP", "EOG",
        "PSX", "MPC", "VLO", "MA", "V", "AXP", "BK", "USB", "PNC", "TFC", "COF",
        "SCHW", "CB", "MET", "PRU", "AFL", "AIG", "BLK", "ICE", "MCO", "SPGI",
        "BABA", "NVO", "TSM", "SAP", "BHP", "RIO", "AZN", "SHEL", "TTE", "SAN",
    }
    if tk in known_nyse or clean_tk in known_nyse:
        return "NYSE"

    return "NASDAQ"


def get_tradingview_symbol(
    company_id: str,
    ticker: str | None = None,
    exchange: str | None = None,
    country: str | None = None,
) -> str:
    """Compute exact TradingView symbol string (e.g. 'NASDAQ:AAPL', 'NYSE:BABA', 'TSX:RY')."""
    parts = company_id.split(":")
    c_country = (country or (parts[0] if len(parts) >= 1 else "US")).upper()
    tk = (ticker or (parts[1] if len(parts) >= 2 else company_id)).strip().upper()

    # Canadian listings
    if c_country == "CA" or tk.endswith(".TO") or tk.endswith(".TSX"):
        clean = tk
        if clean.endswith(".TO"):
            clean = clean[:-3]
        elif clean.endswith(".TSX"):
            clean = clean[:-4]
        return f"TSX:{clean}"

    clean = tk
    if clean.endswith(".US"):
        clean = clean[:-3]

    resolved_ex = exchange if (exchange and exchange not in ("US", "CA")) else get_exchange(clean, country=c_country)
    # Format share classes with dot for TV (e.g. BRK.B)
    tv_tk = clean.replace("-", ".")
    return f"{resolved_ex.upper()}:{tv_tk}"


def get_suggestions(db: Session, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search companies across DB, universe master, and SEC tickers cache with rich metadata."""
    from app.services.mapping import _sec_tickers, _universe_rows

    q = (query or "").strip()
    if not q:
        return []

    q_up = q.upper()
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_tickers: set[str] = set()

    # 1. Search database companies (highest priority - full data already available)
    like = f"%{q}%"
    db_rows = db.execute(
        select(Company, Score)
        .outerjoin(Score, Score.company_id == Company.company_id)
        .where(Company.is_deleted == False)
        .where(
            (Company.ticker.ilike(like))
            | (Company.name.ilike(like))
            | (Company.company_id.ilike(like))
        )
        .limit(limit * 2)
    ).all()

    for comp, score in db_rows:
        cid = comp.company_id
        tk = (comp.ticker or "").upper()
        seen_ids.add(cid)
        seen_tickers.add(tk)
        ex = get_exchange(tk, country=comp.country or "US")
        tv_sym = get_tradingview_symbol(cid, tk, exchange=ex, country=comp.country)
        results.append({
            "company_id": cid,
            "ticker": tk,
            "name": comp.name,
            "exchange": ex,
            "country": comp.country or "US",
            "sector": comp.gics_sector,
            "in_database": True,
            "tradingview_symbol": tv_sym,
            "composite": score.composite if score else None,
            "signal": score.signal if score else None,
            "universe_tags": comp.universe_tags or [],
        })

    # 2. Search universe_master.csv (for known universe entries not yet visited)
    by_id, by_primary = _universe_rows()
    for cid, rec in by_id.items():
        if cid in seen_ids:
            continue
        tk = rec["ticker"].upper()
        name = rec.get("name") or ""
        if q_up in tk or q.lower() in name.lower():
            seen_ids.add(cid)
            seen_tickers.add(tk)
            country = rec["country"]
            ex = get_exchange(tk, country=country)
            tv_sym = get_tradingview_symbol(cid, tk, exchange=ex, country=country)
            u_tags = ["TSX"] if country == "CA" else ["SP500", "RUSSELL1000"]
            results.append({
                "company_id": cid,
                "ticker": tk,
                "name": rec.get("name"),
                "exchange": ex,
                "country": country,
                "sector": rec.get("sector") or rec.get("gics_sector"),
                "in_database": False,
                "tradingview_symbol": tv_sym,
                "composite": None,
                "signal": None,
                "universe_tags": u_tags,
            })
            if len(results) >= limit * 3:
                break

    # 3. Search SEC tickers cache (for any other US stock)
    try:
        sec_data = _sec_tickers()
        for entry in sec_data.values():
            tk = str(entry.get("ticker", "")).upper()
            title = str(entry.get("title", ""))
            if not tk:
                continue
            if tk in seen_tickers:
                continue
            if q_up in tk or q.lower() in title.lower():
                cid = f"US:{tk}:US"
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
                seen_tickers.add(tk)
                ex = get_exchange(tk, country="US")
                tv_sym = get_tradingview_symbol(cid, tk, exchange=ex, country="US")
                results.append({
                    "company_id": cid,
                    "ticker": tk,
                    "name": title.title(),
                    "exchange": ex,
                    "country": "US",
                    "sector": None,
                    "in_database": False,
                    "tradingview_symbol": tv_sym,
                    "composite": None,
                    "signal": None,
                    "universe_tags": [],
                })
                if len(results) >= limit * 4:
                    break
    except Exception as exc:
        logger.debug("SEC cache suggestion search: %s", exc)

    # Ranking logic:
    # 1. Exact ticker match (accounting for .TO / .TSX suffix for Canadian stocks)
    # 2. In database over not in database
    # 3. Ticker starts with query
    # 4. Name starts with query
    # 5. Composite score desc
    def _rank_key(item: dict[str, Any]) -> tuple:
        tk = item["ticker"].upper()
        clean_tk = tk
        for sfx in (".TO", ".TSX", ".US", "-TO"):
            if clean_tk.endswith(sfx):
                clean_tk = clean_tk[:-len(sfx)]
                break
        nm = (item["name"] or "").upper()
        is_exact_tk = (tk == q_up or clean_tk == q_up)
        is_starts_tk = (tk.startswith(q_up) or clean_tk.startswith(q_up))
        is_starts_nm = nm.startswith(q_up)
        in_db = item["in_database"]
        score = item["composite"] or 0.0

        return (
            not is_exact_tk,
            not in_db,
            not is_starts_tk,
            not is_starts_nm,
            -score,
            len(clean_tk),
            clean_tk,
        )

    results.sort(key=_rank_key)
    return results[:limit]
