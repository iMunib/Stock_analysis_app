"""Tests for search suggestions endpoint, exchange resolver, and TradingView symbol derivation."""
from __future__ import annotations

import pytest
from app.services.exchange_resolver import get_exchange, get_tradingview_symbol


def test_exchange_resolver_rules():
    """Verify authoritative exchange mapping for US and Canadian tickers."""
    # US NASDAQ names
    assert get_exchange("AAPL") == "NASDAQ"
    assert get_exchange("MSFT") == "NASDAQ"
    assert get_exchange("AMD") == "NASDAQ"
    assert get_exchange("KHC") == "NASDAQ"
    assert get_exchange("NVDA") == "NASDAQ"

    # US NYSE names
    assert get_exchange("JPM") == "NYSE"
    assert get_exchange("BABA") == "NYSE"
    assert get_exchange("BRK.B") == "NYSE"
    assert get_exchange("BRK-B") == "NYSE"
    assert get_exchange("XOM") == "NYSE"

    # Canadian TSX names
    assert get_exchange("RY", country="CA") == "TSX"
    assert get_exchange("SHOP.TO") == "TSX"
    assert get_exchange("KITS.TO") == "TSX"
    assert get_exchange("ABX.TO") == "TSX"


def test_tradingview_symbol_formatting():
    """Verify exact TradingView format required by the embed chart."""
    assert get_tradingview_symbol("US:AAPL:US", "AAPL") == "NASDAQ:AAPL"
    assert get_tradingview_symbol("US:BABA:US", "BABA") == "NYSE:BABA"
    assert get_tradingview_symbol("US:KHC:US", "KHC") == "NASDAQ:KHC"
    assert get_tradingview_symbol("US:JPM:US", "JPM") == "NYSE:JPM"
    assert get_tradingview_symbol("CA:RY:TSX", "RY") == "TSX:RY"
    assert get_tradingview_symbol("CA:SHOP:TSX", "SHOP.TO") == "TSX:SHOP"
    assert get_tradingview_symbol("CA:ABX:TSX", "ABX") == "TSX:ABX"
    assert get_tradingview_symbol("US:BRK.B:US", "BRK-B") == "NYSE:BRK.B"


def test_suggestions_endpoint_database_match(client, imported_db):
    """Verify GET /api/v1/search/suggestions returns rich disambiguated options for DB stocks."""
    resp = client.get("/api/v1/search/suggestions?q=aapl")
    assert resp.status_code == 200
    data = resp.json()
    assert data["q"] == "aapl"
    assert data["count"] >= 1

    first = data["items"][0]
    assert first["ticker"] == "AAPL"
    assert first["in_database"] is True
    assert first["exchange"] == "NASDAQ"
    assert first["tradingview_symbol"] == "NASDAQ:AAPL"
    assert first["country"] == "US"
    assert "Apple" in (first["name"] or "")


def test_suggestions_endpoint_sec_cache_fallback(client, imported_db):
    """Verify suggestions fall back to SEC cache for non-universe tickers with correct exchange."""
    # Look for a ticker in SEC cache that might not be in the 720 universe
    resp = client.get("/api/v1/search/suggestions?q=PLTR")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    pltr = next((it for it in data["items"] if it["ticker"] == "PLTR"), None)
    assert pltr is not None
    assert pltr["exchange"] in ("NASDAQ", "NYSE")
    assert pltr["tradingview_symbol"].startswith(pltr["exchange"] + ":")


def test_dossier_includes_exchange_and_tv_symbol(client, imported_db):
    """Verify company dossier payload returns authoritative exchange and tradingview_symbol."""
    resp = client.get("/api/v1/companies/US:AAPL:US/dossier")
    assert resp.status_code == 200
    ident = resp.json()["identity"]
    assert ident["exchange"] == "NASDAQ"
    assert ident["tradingview_symbol"] == "NASDAQ:AAPL"


def test_suggestions_canadian_ticker_priority(client, imported_db):
    """Verify typing 'RY' ranks in-database CA:RY:TSX above external unseeded US:RY:US."""
    resp = client.get("/api/v1/search/suggestions?q=RY")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert items[0]["company_id"] == "CA:RY:TSX"
    assert items[0]["in_database"] is True
    assert items[0]["exchange"] == "TSX"


def test_suggestions_dual_listed_priority(client, imported_db):
    """Verify typing 'SHOP' ranks in-database CA:SHOP:TSX above external unseeded US:SHOP:US."""
    resp = client.get("/api/v1/search/suggestions?q=SHOP")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert items[0]["company_id"] == "CA:SHOP:TSX"
    assert items[0]["in_database"] is True

