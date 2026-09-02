"""Company_ID helpers. Frozen format: US:TICKER:US | CA:TICKER:TSX (dots kept)."""
from __future__ import annotations

import re
from dataclasses import dataclass

_ID_RE = re.compile(r"^(?:US:([A-Za-z0-9.\-^]+):US|CA:([A-Za-z0-9.\-^]+):TSX)$")
# STRICT frozen format: US ids end in :US, CA ids end in :TSX. Loose variants
# (US:AES:NYSE, CA:NA:TO) are handled by normalize_company_id, not here.


@dataclass(frozen=True)
class CompanyId:
    country: str  # "US" | "CA"
    ticker: str
    exchange: str  # canonical suffix: "US" | "TSX"

    def format(self) -> str:
        return f"{self.country}:{self.ticker}:{self.exchange}"


def parse_company_id(raw: str) -> CompanyId | None:
    """Parse a STRICT frozen-format ID (US:...:US | CA:...:TSX). None otherwise."""
    if not raw:
        return None
    m = _ID_RE.match(str(raw).strip())
    if not m:
        return None
    country = "US" if m.group(1) is not None else "CA"
    ticker = (m.group(1) if country == "US" else m.group(2)).upper()
    return CompanyId(country=country, ticker=ticker, exchange="US" if country == "US" else "TSX")


def format_company_id(country: str, ticker: str) -> str:
    """Format from country + ticker. US -> US:TICKER:US, CA -> CA:TICKER:TSX."""
    country = country.strip().upper()
    ticker = ticker.strip().upper()
    if country == "US":
        return f"US:{ticker}:US"
    if country == "CA":
        return f"CA:{ticker}:TSX"
    raise ValueError(f"unsupported country: {country!r}")


def normalize_company_id(raw: str) -> str | None:
    """Normalize loose IDs into the frozen format (US:<TICKER>:US | CA:<TICKER>:TSX).

    Supports:
    - US:AES:NYSE -> US:AES:US
    - CA:NA:TO -> CA:NA:TSX
    - TSE:KITS / TSX:KITS / TO:KITS -> CA:KITS:TSX
    - NYSE:IBM / NASDAQ:AAPL -> US:IBM:US / US:AAPL:US
    - KITS:TSX -> CA:KITS:TSX
    """
    if raw is None:
        return None
    s = re.sub(r"\s*:\s*", ":", str(raw).strip())
    parts = s.split(":")
    if len(parts) == 2:
        prefix, ticker = parts[0].upper(), parts[1].strip().upper()
        if not ticker:
            return None
        if prefix in ("TSE", "TSX", "TOR", "TO", "V", "NEO", "CSE", "CA"):
            return f"CA:{ticker}:TSX"
        if prefix in ("NYSE", "NASDAQ", "AMEX", "US"):
            return f"US:{ticker}:US"
        if ticker in ("TSX", "TSE", "TO", "V"):
            return f"CA:{prefix}:TSX"
        if ticker in ("US", "NYSE", "NASDAQ"):
            return f"US:{prefix}:US"
        return None

    if len(parts) != 3:
        return None
    country, ticker, suffix = parts[0].upper(), parts[1].strip().upper(), parts[2].upper()
    if not ticker or not suffix:
        return None
    if country in ("US", "NYSE", "NASDAQ", "AMEX"):
        return f"US:{ticker}:US"
    if country in ("CA", "TSE", "TSX", "TOR", "TO"):
        return f"CA:{ticker}:TSX"
    return None


def is_valid_company_id(raw: str) -> bool:
    cid = parse_company_id(raw)
    return cid is not None
