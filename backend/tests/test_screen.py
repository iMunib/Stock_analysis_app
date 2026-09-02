"""Tests for GET /api/v1/screen.

Requirements:
- USD+ROE min returns only USD
- CAD money not in All money columns (money columns hidden in ALL view)
- PE max excludes blanks / nulls
- Coverage min filters by number of pillars
- Exclude banks toggle removes financials
- Growth history filter works
"""
from __future__ import annotations

import pytest


def test_screen_all_default_hides_money_columns(client):
    """ALL view must never blend money; money dict must be None for all rows."""
    res = client.get("/api/v1/screen?currency=ALL")
    assert res.status_code == 200
    data = res.json()
    assert data["currency_view"] == "ALL"
    assert data["count"] > 0
    # Crucial test: money columns must be None/hidden in ALL view
    for it in data["items"]:
        assert it["money"] is None, "money columns must not appear in ALL currency view"
        assert "company_id" in it


def test_screen_usd_plus_roe_min_returns_only_usd(client):
    """USD + ROE min returns only USD rows, all matching the ROE threshold."""
    res = client.get("/api/v1/screen?currency=USD&roe_min=0.10")
    assert res.status_code == 200
    data = res.json()
    assert data["currency_view"] == "USD"
    assert data["count"] > 0
    for it in data["items"]:
        assert it["currency"] == "USD", f"expected only USD but got {it['currency']} for {it['company_id']}"
        assert it["roe_calc"] is not None and it["roe_calc"] >= 0.10
        # In single-currency USD mode, money dictionary is native
        assert it["money"] is not None


def test_cad_money_not_in_all_money_columns(client):
    """Verify CAD rows in ALL view do not carry CAD money amounts into money columns."""
    res = client.get("/api/v1/screen?currency=ALL")
    assert res.status_code == 200
    data = res.json()
    cad_items = [it for it in data["items"] if it["currency"] == "CAD"]
    assert len(cad_items) > 0, "expected CAD companies in ALL view"
    for it in cad_items:
        assert it["money"] is None


def test_screen_pe_max_excludes_blanks(client):
    """PE max must exclude any rows where PE is null, zero, or negative."""
    res = client.get("/api/v1/screen?pe_max=25.0")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    for it in data["items"]:
        assert it["pe_calc"] is not None, "PE max must exclude blank/null PE"
        assert 0 < it["pe_calc"] <= 25.0


def test_screen_coverage_min(client):
    """Coverage min filters by number of scored pillars (1 to 4)."""
    res = client.get("/api/v1/screen?coverage_min=4")
    assert res.status_code == 200
    data = res.json()
    for it in data["items"]:
        assert it["coverage"] == 4


def test_screen_exclude_banks(client):
    """Exclude banks toggle removes financials and banks."""
    res_all = client.get("/api/v1/screen?limit=1000")
    banks_in_all = [it for it in res_all.json()["items"] if it["is_bank"]]
    assert len(banks_in_all) > 0, "banks exist in the universe"

    res_no_banks = client.get("/api/v1/screen?exclude_banks=true&limit=1000")
    assert res_no_banks.status_code == 200
    for it in res_no_banks.json()["items"]:
        assert it["is_bank"] is False
        assert (it["gics_sector"] or "").lower() != "financials"


def test_screen_has_growth_history(client):
    """has_growth_history filter requires growth pillar or >= 3 years history."""
    res = client.get("/api/v1/screen?has_growth_history=true")
    assert res.status_code == 200
    for it in res.json()["items"]:
        assert it["has_growth_history"] is True


def test_screen_empty_filter_combination(client):
    """Impossible filters return count=0 cleanly."""
    res = client.get("/api/v1/screen?composite_min=9.99&pe_max=1.0")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["count"] == 0
    assert len(data["items"]) == 0
