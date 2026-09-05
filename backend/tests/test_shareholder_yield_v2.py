"""Dedicated unit tests for upgraded Capital Return & Shareholder Yield Engine (Phase 1)."""
import pytest
from app.models import Company, CompanyProfile, FinancialSnapshot
from app.services.capital_return_engine import compute_shareholder_yield


def test_shareholder_yield_genuine_sbc_dilution(imported_db):
    """Test actual SBC extraction from filings and net buyback yield calculation."""
    cid = "US:TEST_SBC_YIELD:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="TEST_SBC", country="US", currency="USD",
            name="Test SBC Corp", gics_sector="Information Technology",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2023, period_type="FY", currency="USD",
            revenue=1_000_000_000.0, shares_snapshot=100_000_000.0,
            market_cap=10_000_000_000.0, price=100.0,
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=1_200_000_000.0, shares_snapshot=96_000_000.0,  # 4% gross share contraction
            market_cap=10_000_000_000.0, price=104.17,
            stock_based_compensation=100_000_000.0,  # $100M actual SBC (1.0% of market cap)
        )
        imported_db.add_all([s1, s2])
        imported_db.add(CompanyProfile(company_id=cid, dividend_yield=0.02))  # 2.0% dividend yield
        imported_db.commit()

        res = compute_shareholder_yield(imported_db, cid)
        assert res["company_id"] == cid
        assert res["sbc_drag_pct"] == pytest.approx(8.33, abs=0.1)  # 100M / 1200M = 8.33%
        assert res["sbc_dilution_offset_pct"] == pytest.approx(1.0, abs=0.1)  # 100M / 10B = 1.0%
        # Gross buyback yield = 4.0%, SBC offset = 1.0% => Net buyback yield = 3.0%
        assert res["net_buyback_yield_pct"] == pytest.approx(3.0, abs=0.2)
        assert res["dividend_yield_pct"] == 2.0
        # True Shareholder Yield = Net Buyback Yield + Dividend Yield = 5.0%
        assert res["true_shareholder_yield_pct"] == pytest.approx(5.0, abs=0.2)
        assert res["total_shareholder_yield_pct"] == res["true_shareholder_yield_pct"]
    finally:
        imported_db.query(CompanyProfile).filter_by(company_id=cid).delete()
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()


def test_zero_hardcoded_sbc_when_missing(imported_db):
    """When SBC is not filed, do not invent numbers (sbc remains None, no hardcoded sector %)."""
    cid = "US:TEST_NO_SBC:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="TEST_NO_SBC", country="US", currency="USD",
            name="Test No SBC Corp", gics_sector="Information Technology",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2023, period_type="FY", currency="USD",
            revenue=500_000_000.0, shares_snapshot=50_000_000.0, market_cap=1_000_000_000.0,
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=600_000_000.0, shares_snapshot=48_000_000.0, market_cap=1_200_000_000.0,
            stock_based_compensation=None,  # Not reported
        )
        imported_db.add_all([s1, s2])
        imported_db.commit()

        res = compute_shareholder_yield(imported_db, cid)
        assert res["sbc_drag_pct"] is None
        assert res["sbc_dilution_offset_pct"] is None
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()
