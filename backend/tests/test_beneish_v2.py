"""Dedicated unit tests for upgraded Beneish M-Score Engine (Phase 1)."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.beneish_engine import compute_beneish_m_score


def test_beneish_genuine_dsri_and_aqi(imported_db):
    """Test genuine DSRI and AQI calculation using expanded statement columns."""
    cid = "US:TEST_BEN_V2:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="TEST_BEN", country="US", currency="USD",
            name="Test Beneish Clean Corp", gics_sector="Information Technology",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2023, period_type="FY", currency="USD",
            revenue=100_000_000.0, gross_profit=60_000_000.0, ebit=25_000_000.0,
            net_income=20_000_000.0, total_assets=150_000_000.0, total_liabilities=50_000_000.0,
            operating_cash_flow=22_000_000.0, book_equity=100_000_000.0,
            accounts_receivable=15_000_000.0, current_assets=50_000_000.0, ppe_net=40_000_000.0,
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=120_000_000.0, gross_profit=72_000_000.0, ebit=30_000_000.0,
            net_income=25_000_000.0, total_assets=180_000_000.0, total_liabilities=55_000_000.0,
            operating_cash_flow=28_000_000.0, book_equity=125_000_000.0,
            accounts_receivable=18_000_000.0, current_assets=60_000_000.0, ppe_net=48_000_000.0,
        )
        imported_db.add_all([s1, s2])
        imported_db.commit()

        res = compute_beneish_m_score(imported_db, cid)
        assert res["status"] == "computed"
        assert res["data_available"] is True
        assert res["beneish_score"] is not None
        assert res["m_score"] is not None
        assert res["variables"]["dsri"] == pytest.approx(1.0, abs=0.05)
        assert res["variables"]["gmi"] == pytest.approx(1.0, abs=0.05)
        assert res["is_manipulator"] is False
        assert res["zone"] == "Non-manipulator"
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()


def test_beneish_missing_historical_lines_strict(imported_db):
    """When required historical lines are absent, strict mode returns data_available: false and beneish_score: None."""
    cid = "US:TEST_BEN_MISSING:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="TEST_BEN_MISS", country="US", currency="USD",
            name="Missing Lines Corp", gics_sector="Industrials",
        ))
        s1 = FinancialSnapshot(
            company_id=cid, fiscal_year=2023, period_type="FY", currency="USD",
            revenue=100_000_000.0, gross_profit=40_000_000.0, total_assets=100_000_000.0,
        )
        s2 = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=110_000_000.0, gross_profit=44_000_000.0, total_assets=110_000_000.0,
        )
        imported_db.add_all([s1, s2])
        imported_db.commit()

        res = compute_beneish_m_score(imported_db, cid, strict=True)
        assert res["status"] == "insufficient_data"
        assert res["data_available"] is False
        assert res["beneish_score"] is None
        assert res["m_score"] is None
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()
