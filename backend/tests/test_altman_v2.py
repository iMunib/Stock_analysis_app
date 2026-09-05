"""Dedicated unit tests for upgraded Altman Z-Score Distress Engine (Phase 1)."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.distress_engine import compute_distress


def test_altman_z_genuine_working_capital_and_retained_earnings(imported_db):
    """Test genuine working capital and retained earnings calculation without proxies."""
    cid = "US:TEST_ALT_V2:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="TEST_ALT", country="US", currency="USD",
            name="Test Altman Mfg Corp", gics_sector="Materials",
        ))
        snap = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=200_000_000.0, ebit=40_000_000.0, total_assets=250_000_000.0,
            total_liabilities=100_000_000.0, book_equity=150_000_000.0, market_cap=300_000_000.0,
            current_assets=120_000_000.0, current_liabilities=50_000_000.0,
            retained_earnings=90_000_000.0, ppe_net=100_000_000.0, inventory=25_000_000.0,
        )
        imported_db.add(snap)
        imported_db.commit()

        res = compute_distress(imported_db, cid)
        assert res["status"] == "computed"
        assert res["model_used"] == "manufacturing"
        # Working Capital = 120M - 50M = 70M; X1 = 70M / 250M = 0.28
        assert res["factors"]["x1_working_capital_to_ta"] == pytest.approx(0.28, abs=0.001)
        # Retained Earnings = 90M; X2 = 90M / 250M = 0.36
        assert res["factors"]["x2_retained_earnings_to_ta"] == pytest.approx(0.36, abs=0.001)
        # Z-Score should be calculated
        assert res["z_score"] is not None
        assert res["zone"] in ("Safe", "Grey", "Distress")
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()


def test_altman_z_fallback_when_ppe_inventory_inapplicable(imported_db):
    """When manufacturing capital assets are inapplicable (0), engine safely falls back to Z''."""
    cid = "US:TEST_ALT_FALLBACK:US"
    try:
        imported_db.add(Company(
            company_id=cid, ticker="TEST_FALLBACK", country="US", currency="USD",
            name="Inapplicable Capital Corp", gics_sector="Materials",
        ))
        snap = FinancialSnapshot(
            company_id=cid, fiscal_year=2024, period_type="FY", currency="USD",
            revenue=100_000_000.0, ebit=20_000_000.0, total_assets=100_000_000.0,
            total_liabilities=40_000_000.0, book_equity=60_000_000.0, market_cap=120_000_000.0,
            current_assets=80_000_000.0, current_liabilities=30_000_000.0,
            retained_earnings=30_000_000.0, ppe_net=0.0, inventory=0.0,
        )
        imported_db.add(snap)
        imported_db.commit()

        res = compute_distress(imported_db, cid)
        assert res["status"] == "computed"
        assert res["model_used"] == "non_manufacturing"
        assert "FALLBACK_Z_DOUBLE_PRIME_INAPPLICABLE_CAPITAL_ITEMS" in res["data_quality_flags"]
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()
