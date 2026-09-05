"""Dedicated unit tests for upgraded AAOIFI Halal Engine (Phase 1)."""
import pytest
from app.services.halal import evaluate_halal


def test_halal_genuine_interest_income_passes():
    """When interest income is reported and <= 5% of revenue, company passes as halal_candidate."""
    company = {"gics_sector": "Information Technology", "custom_industry_sheet": "Software", "name": "Pure Tech Inc"}
    snap = {
        "market_cap": 1_000_000_000.0,
        "total_debt": 100_000_000.0,         # 10% debt / mcap (< 30%)
        "cash_st_investments": 150_000_000.0, # 15% cash / mcap (< 30%)
        "revenue": 500_000_000.0,
        "interest_income": 5_000_000.0,       # 1% impure income (<= 5%)
    }
    res = evaluate_halal(company, snap)
    assert res["status"] == "halal_candidate"
    assert res["halal_candidate"] is True
    assert res["tests"]["financial_ratios"]["result"] == "pass"
    assert res["tests"]["financial_ratios"]["ratios"]["impure_income"]["result"] == "pass"
    assert res["tests"]["financial_ratios"]["ratios"]["impure_income"]["ratio"] == 0.01


def test_halal_genuine_interest_income_fails_excess():
    """When interest income > 5% of revenue, company is not_halal."""
    company = {"gics_sector": "Information Technology", "custom_industry_sheet": "Software", "name": "High Interest Inc"}
    snap = {
        "market_cap": 1_000_000_000.0,
        "total_debt": 50_000_000.0,
        "cash_st_investments": 50_000_000.0,
        "revenue": 100_000_000.0,
        "interest_income": 8_000_000.0,       # 8% impure income (> 5%)
    }
    res = evaluate_halal(company, snap)
    assert res["status"] == "not_halal"
    assert res["halal_candidate"] is False
    assert res["tests"]["financial_ratios"]["ratios"]["impure_income"]["result"] == "fail"


def test_halal_missing_interest_income_preserves_honest_unknown():
    """When interest income is not filed, status remains honestly unknown, never halal by default."""
    company = {"gics_sector": "Information Technology", "custom_industry_sheet": "Software", "name": "No Interest Reported"}
    snap = {
        "market_cap": 1_000_000_000.0,
        "total_debt": 50_000_000.0,
        "cash_st_investments": 50_000_000.0,
        "revenue": 100_000_000.0,
        "interest_income": None,
    }
    res = evaluate_halal(company, snap)
    assert res["status"] == "unknown"
    assert res["halal_candidate"] is False
    assert res["tests"]["financial_ratios"]["ratios"]["impure_income"]["result"] == "unknown"
