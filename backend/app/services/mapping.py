"""Ticker/exchange/CIK mapping: raw input -> CompanyRef.

Lookup order for known names: seed/raw/universe_master.csv (has Yahoo_Ticker +
CIK_SEDAR for all 720). Fallback for unknown US tickers: SEC company_tickers.json
(https://www.sec.gov/files/company_tickers.json, User-Agent required) cached at
data/sec_tickers_cache.json.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.providers.base import CompanyRef
from app.services.ids import normalize_company_id, parse_company_id


@dataclass(frozen=True)
class ResolveResult:
    company_id: str
    ticker: str
    country: str
    currency: str
    yahoo_symbol: str | None
    cik: int | None
    in_universe: bool
    name: str | None = None


class MappingError(ValueError):
    pass


_UNIVERSE_CACHE: dict[str, dict] | None = None
_BY_PRIMARY: dict[str, dict] | None = None


def _universe_rows() -> tuple[dict[str, dict], dict[str, dict]]:
    """Load universe_master.csv if present; index by frozen company_id and primary ticker."""
    global _UNIVERSE_CACHE, _BY_PRIMARY
    if _UNIVERSE_CACHE is not None:
        return _UNIVERSE_CACHE, _BY_PRIMARY
    by_id: dict[str, dict] = {}
    by_primary: dict[str, dict] = {}
    candidates = [Path("/seed/raw/universe_master.csv"), Path("seed/raw/universe_master.csv"),
                  Path("../seed/raw/universe_master.csv"), Path.cwd() / "seed/raw/universe_master.csv"]
    path = next((p for p in candidates if p.is_file()), None)
    if path:
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                # NOTE: for CA rows Ticker is bare ('RY') while Primary_Ticker is
                # Yahoo-style ('RY.TO'); company IDs need the bare form.
                ticker = (row.get("Ticker") or row.get("Primary_Ticker") or "").strip()
                country = (row.get("Country_of_Listing") or "").strip().upper()
                if not ticker or country not in ("US", "CA"):
                    continue
                cid = normalize_company_id(f"{country}:{ticker}:X") or f"US:{ticker}:US"
                cid = f"US:{ticker.upper()}:US" if country == "US" else f"CA:{ticker.upper()}:TSX"
                rec = {
                    "company_id": cid,
                    "ticker": ticker.upper(),
                    "country": country,
                    "currency": (row.get("Primary_Currency") or ("USD" if country == "US" else "CAD")).strip().upper(),
                    "yahoo": (row.get("Yahoo_Ticker") or "").strip() or None,
                    "cik": int(row["CIK_SEDAR"]) if (row.get("CIK_SEDAR") or "").strip().isdigit() else None,
                    "name": (row.get("Company_Name") or "").strip() or None,
                }
                by_id[cid] = rec
                by_primary.setdefault(rec["ticker"], rec)
    _UNIVERSE_CACHE, _BY_PRIMARY = by_id, by_primary
    return by_id, by_primary


def yahoo_symbol_for(ticker: str, country: str) -> str:
    """Frozen Yahoo symbol rules: US plain, CA suffix .TO, dots preserved.
    Yahoo uses '-' for share-class dots (IIP.UN -> IIP-UN.TO); universe_master
    carries the authoritative symbol and wins when present."""
    by_id, by_primary = _universe_rows()
    rec = by_primary.get(ticker.upper())
    if rec and rec.get("yahoo"):
        return rec["yahoo"]
    t = ticker.upper()
    if country == "US":
        return t
    return t.replace(".", "-") + ".TO"


# ---- free-text resolver ----
_PATTERNS = [
    # CA:RY:TSX / US:MMM:US
    re.compile(r"^(US|CA):([A-Za-z0-9.\-^]+):(US|TSX|NYSE|NASDAQ|AMEX|TO|V|NEO|CSE)$", re.I),
    # RY.TO / AAPL.US / IIP-UN.TO
    re.compile(r"^([A-Za-z0-9.\-^]+)\.(TO|US|TSX|V|NEO|CN)$", re.I),
]

# Exchange-prefix normalisers: convert "NASDAQ:AMD" / "TSE:KITS" / "NYSE:IBM" → bare ticker + inferred country
_EXCHANGE_CA = re.compile(r"^(?:TSE|TSX|TSV|NEO|CSE)\s*:\s*([A-Za-z0-9.\-^]{1,16})$", re.I)
_EXCHANGE_US = re.compile(r"^(?:NASDAQ|NYSE|AMEX|NYSEARCA|CBOE)\s*:\s*([A-Za-z0-9.\-^]{1,16})$", re.I)

# Tickers that are definitively Canadian (CA universe) — avoid defaulting to US
_CA_BARE_TICKERS: set[str] | None = None


def _ca_bare_tickers() -> set[str]:
    global _CA_BARE_TICKERS
    if _CA_BARE_TICKERS is not None:
        return _CA_BARE_TICKERS
    by_id, by_primary = _universe_rows()
    _CA_BARE_TICKERS = {rec["ticker"].upper() for rec in by_id.values() if rec.get("country") == "CA"}
    return _CA_BARE_TICKERS


def resolve(query: str) -> ResolveResult:
    """Resolve 'AAPL', 'AAPL.US', 'RY.TO', 'CA:RY:TSX', 'US:MMM:US',
    'NASDAQ:AMD', 'NYSE:IBM', 'TSE:KITS', 'TSX:KITS'.
    Conservative default: unknown plain ticker → check CA universe first, then US."""
    q = (query or "").strip()
    if not q:
        raise MappingError("empty query")
    by_id, by_primary = _universe_rows()

    # Early check for ambiguous or unsupported foreign exchange listings (e.g. 9988.HK)
    if q.upper().endswith(".HK") or re.search(r"^\d{4}(\.HK)?$", q):
        raise MappingError("LISTING_AMBIGUOUS: Multiple listings. Pick US ADR or HK/TSX (show choices).")

    # Exchange-prefix normalization: TSE:KITS / NASDAQ:AMD / NYSE:IBM / TSX:KITS
    m_ca = _EXCHANGE_CA.match(q)
    if m_ca:
        return resolve(m_ca.group(1).upper() + ".TO")

    m_us = _EXCHANGE_US.match(q)
    if m_us:
        return resolve(m_us.group(1).upper())

    cid = normalize_company_id(q)
    if cid and ":" in q:
        rec = by_id.get(cid)
        if rec:
            return ResolveResult(cid, rec["ticker"], rec["country"], rec["currency"], rec["yahoo"], rec["cik"], True, rec["name"])
        cid_parts = cid.split(":")
        country, ticker = cid_parts[0], cid_parts[1]
        sec_info = cik_for_unknown_us(ticker) if country == "US" else (None, None)
        cik, name = (sec_info[0], sec_info[1]) if isinstance(sec_info, tuple) else (sec_info, None)
        return ResolveResult(cid, ticker, country, "USD" if country == "US" else "CAD", yahoo_symbol_for(ticker, country), cik, False, name)

    m = _PATTERNS[1].match(q)
    if m:
        raw_ticker, suffix = m.group(1).upper(), m.group(2).lower()
        if suffix == "us":
            cid = f"US:{raw_ticker}:US"
            rec = by_id.get(cid) or by_primary.get(raw_ticker)
            if rec:
                return ResolveResult(rec["company_id"], rec["ticker"], "US", rec["currency"], rec["yahoo"], rec["cik"], True, rec["name"])
            sec_info = cik_for_unknown_us(raw_ticker)
            cik, name = (sec_info[0], sec_info[1]) if isinstance(sec_info, tuple) else (sec_info, None)
            return ResolveResult(cid, raw_ticker, "US", "USD", raw_ticker, cik, False, name)
        # .TO / .TSX -> CA
        ticker = raw_ticker.replace("-", ".")
        cid = f"CA:{ticker}:TSX"
        rec = by_id.get(cid) or by_primary.get(ticker)
        if rec:
            return ResolveResult(rec["company_id"], rec["ticker"], "CA", rec["currency"], rec["yahoo"], rec["cik"], True, rec["name"])
        return ResolveResult(cid, ticker, "CA", "CAD", yahoo_symbol_for(ticker, "CA"), None, False)

    # plain ticker
    t = q.upper()
    if not re.match(r"^[A-Z0-9.\-^]{1,12}$", t):
        raise MappingError("SYMBOL_NOT_FOUND: We could not find that ticker. Try AMD, BABA, SHOP.TO, or KITS.TO.")
    rec = by_primary.get(t)
    if rec:
        return ResolveResult(rec["company_id"], rec["ticker"], rec["country"], rec["currency"], rec["yahoo"], rec["cik"], True, rec["name"])
    if t.endswith(".TO"):
        return resolve(t)  # unreachable, kept for safety

    # Unknown plain ticker: check if it's a known CA ticker first (e.g. KITS is only on TSX)
    if t in _ca_bare_tickers():
        return resolve(t + ".TO")

    # Unknown plain ticker: default US (conservative default, logged by callers)
    cid = f"US:{t}:US"
    sec_info = cik_for_unknown_us(t)
    cik, name = (sec_info[0], sec_info[1]) if isinstance(sec_info, tuple) else (sec_info, None)
    return ResolveResult(cid, t, "US", "USD", t, cik, False, name)


# ---- SEC ticker -> CIK fallback for unknown US tickers ----
_SEC_CACHE: dict | None = None


def _sec_tickers() -> dict:
    global _SEC_CACHE
    if _SEC_CACHE is not None:
        return _SEC_CACHE
    cache_path = Path("data/sec_tickers_cache.json")
    candidates = [Path("/app/data/sec_tickers_cache.json"), cache_path, Path("../data/sec_tickers_cache.json")]
    path = next((p for p in candidates if p.is_file()), None)
    if path:
        with open(path, encoding="utf-8") as f:
            _SEC_CACHE = json.load(f)
            return _SEC_CACHE
    import os
    from urllib import request as urlrequest
    from app.config import SEC_USER_AGENT

    req = urlrequest.Request(
        "https://www.sec.gov/files/company_tickers.json",
        headers={"User-Agent": os.environ.get("SEC_USER_AGENT", SEC_USER_AGENT)},
    )
    with urlrequest.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    _SEC_CACHE = data
    return _SEC_CACHE


def cik_for_unknown_us(ticker: str) -> tuple[int | None, str | None]:
    """SEC company_tickers.json lookup for tickers outside the 720 universe."""
    try:
        data = _sec_tickers()
    except Exception:
        return None, None
    t = ticker.upper()
    for entry in data.values():
        if str(entry.get("ticker", "")).upper() == t:
            cik = entry.get("cik_str")
            name = entry.get("title")
            return (int(cik) if cik is not None else None, str(name) if name else None)
    return None, None


def build_ref(result: ResolveResult) -> CompanyRef:
    cik = result.cik
    if cik is None and result.country == "US":
        cik_val, _ = cik_for_unknown_us(result.ticker)
        cik = cik_val
    return CompanyRef(
        company_id=result.company_id,
        ticker=result.ticker,
        country=result.country,
        currency=result.currency,
        yahoo_symbol=result.yahoo_symbol or yahoo_symbol_for(result.ticker, result.country),
        cik=cik,
    )
