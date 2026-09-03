"""Tests for Simply Wall St-Style Dilution & Total Shareholder Yield (Master Directive WS4)."""
import pytest
from app.models import Company, CompanyProfile, FinancialSnapshot
from app.services.capital_return_engine import compute_shareholder_yield


def test_capital_return_dilution_and_buybacks(imported_db):
    """Test dilution CAGR and accelerated buyback flags on synthetic share series."""
    cid = "US:TEST_CAP:US"
    imported_db.add(Company(company_id=cid, ticker="TEST_CAP", country="US", currency="USD", name="Test Capital Return Inc"))
    # 4 years of share count contraction: 100M -> 95M -> 90M -> 85M (~-5% per year)
    for fy, shares in [(2021, 100_000_000.0), (2022, 95_000_000.0), (2023, 90_000_000.0), (2024, 85_000_000.0)]:
        imported_db.add(FinancialSnapshot(
            company_id=cid, fiscal_year=fy, period_type="FY",
            shares_snapshot=shares, revenue=500_000_000.0, net_income=50_000_000.0,
        ))
    imported_db.add(CompanyProfile(company_id=cid, dividend_yield=0.03))  # 3% dividend yield
    imported_db.commit()

    try:
        res = compute_shareholder_yield(imported_db, cid)
        assert res["company_id"] == cid
        assert res["share_count_delta_1y_pct"] is not None
        # 85 vs 90 = -5.56%
        assert res["share_count_delta_1y_pct"] < -2.0
        assert "ACCELERATED_BUYBACKS" in res["flags"]
        assert res["net_buyback_yield_pct"] > 2.0
        assert res["dividend_yield_pct"] == 3.0
        # Total Shareholder Yield = Net Buyback Yield + Dividend Yield
        expected_tsy = round(res["net_buyback_yield_pct"] + res["dividend_yield_pct"], 2)
        assert res["total_shareholder_yield_pct"] == expected_tsy
    finally:
        imported_db.query(CompanyProfile).filter_by(company_id=cid).delete()
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()
