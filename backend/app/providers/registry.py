"""Provider registry: routes a CompanyRef to its providers.

US listed -> EDGAR companyfacts (statements) + Yahoo (price, statements fallback).
CA listed -> Yahoo (statements + price). SEDAR+ is NOT scraped in v1.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.providers import yahoo as yahoo_provider
from app.providers.base import CompanyRef
from app.providers.edgar import EdgarClient, parse_companyfacts


class ProviderRegistry:
    def __init__(self, edgar_client: EdgarClient | None = None):
        self.edgar = edgar_client or EdgarClient()

    def fetch_annual_statements(self, ref: CompanyRef) -> list:
        rows: list = []
        if ref.country == "US" and ref.cik:
            try:
                data = self.edgar.get_companyfacts(ref.cik)
                rows = parse_companyfacts(data, expected_currency=ref.currency)
            except Exception as exc:  # noqa: BLE001 - provider failure degrades, never crashes ingest
                print(f"[edgar] companyfacts failed for {ref.company_id} (CIK {ref.cik}): {exc}", flush=True)
                rows = []
        if ref.yahoo_symbol and (ref.country == "CA" or not rows):
            try:
                rows.extend(yahoo_provider.fetch_annual_statements(ref.yahoo_symbol, ref.currency))
            except Exception as exc:  # noqa: BLE001
                print(f"[yahoo] statements failed for {ref.yahoo_symbol}: {exc}", flush=True)
        return rows

    def fetch_price(self, ref: CompanyRef):
        if not ref.yahoo_symbol:
            return None
        try:
            return yahoo_provider.fetch_price(ref.yahoo_symbol)
        except Exception as exc:  # noqa: BLE001
            print(f"[yahoo] price failed for {ref.yahoo_symbol}: {exc}", flush=True)
            return None

    def fetch_identity(self, ref: CompanyRef) -> dict | None:
        if ref.country == "US" and ref.cik:
            try:
                data = self.edgar.get_companyfacts(ref.cik)
                from app.providers.edgar import identity_from_companyfacts

                return identity_from_companyfacts(data)
            except Exception:
                return None
        return None
