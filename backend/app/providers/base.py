"""Provider protocol + shared models. Phase 2 data layer.

A provider turns a CompanyRef into canonical annual statement rows and/or a
price quote. Implementations must be network-free in unit tests (stubs).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class CompanyRef:
    """Everything a provider needs to locate a company."""
    company_id: str            # frozen format US:TICKER:US | CA:TICKER:TSX
    ticker: str                # primary ticker without suffix (AAPL, RY, IIP.UN)
    country: str               # US | CA
    currency: str              # USD | CAD (native reporting currency)
    yahoo_symbol: str | None = None   # e.g. AAPL, RY.TO, IIP-UN.TO
    cik: int | None = None     # SEC CIK (US only)


@dataclass
class AnnualStatement:
    """One canonical FY row mapped onto financial_snapshots columns."""
    fiscal_year: int | None
    period_end: date | None                    # provider period end -> provider_as_of / as_of_date
    currency: str                              # USD | CAD, verbatim from provider
    source: str                                # sec_companyfacts | yfinance
    fields: dict[str, float | str | None] = field(default_factory=dict)
    raw_facts: dict | None = None              # optional provider payload reference (kept small)


@dataclass
class PriceQuote:
    price: float
    currency: str
    as_of: date | None
    source: str                                # yfinance
    fetched_at: datetime | None = None


class FundamentalProvider(Protocol):
    def fetch_annual_statements(self, ref: CompanyRef) -> list[AnnualStatement]:
        ...


class PriceProvider(Protocol):
    def fetch_price(self, ref: CompanyRef) -> PriceQuote | None:
        ...


class IdentityProvider(Protocol):
    def fetch_identity(self, ref: CompanyRef) -> dict | None:
        """Return optional identity enrichment (e.g. SIC, name) or None."""
        ...
