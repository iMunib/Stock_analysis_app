"""Comprehensive unit tests for Phase 3: Forensic Accounting & Capital Allocation Suite."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.sloan_engine import compute_sloan_accruals
from app.services.practitioner_engine import analyze_fridson
from app.services.forensic_engine import synthesize_forensic_health
from app.services.capital_return_engine import compute_shareholder_yield
from app.services.bank_engine import compute_bank_metrics


def test_sloan_accrual_anomaly_classifications(imported_db):
    """Test Sloan accrual anomaly: Low Quality (>10%), High Quality (<-10%), Normal."""
    cid_low = "US:TEST_SLOAN_LOW:US"
    cid_high = "US:TEST_SLOAN_HIGH:US"
    try:
        # 1. Low quality: Net income 20M, CFO 5M, Assets 100M -> (20 - 5) / 100 = 15% (>10%)
        imported_db.add(Company(company_id=cid_low, ticker="SLOW", country="US", currency="USD", name="Low Quality Corp"))
        s_low = FinancialSnapshot(
            company_id=cid_low, fiscal_year=2024, period_type="FY", currency="USD",
            net_income=20_000_000.0, operating_cash_flow=5_000_000.0, total_assets=100_000_000.0,
        )
        # 2. High quality: Net income 10M, CFO 25M, Assets 100M -> (10 - 25) / 100 = -15% (<-10%)
        imported_db.add(Company(company_id=cid_high, ticker="SHIGH", country="US", currency="USD", name="High Quality Corp"))
        s_high = FinancialSnapshot(
            company_id=cid_high, fiscal_year=2024, period_type="FY", currency="USD",
            net_income=10_000_000.0, operating_cash_flow=25_000_000.0, total_assets=100_000_000.0,
        )
        imported_db.add_all([s_low, s_high])
        imported_db.commit()

        res_low = compute_sloan_accruals(imported_db, cid_low)
        assert res_low["quality_rating"] == "Low Quality / Paper Earnings"
        assert res_low["flag"] == "HIGH_ACCRUALS_PAPER_EARNINGS"
        assert res_low["accrual_ratio"] == 0.15

        res_high = compute_sloan_accruals(imported_db, cid_high)
        assert res_high["quality_rating"] == "High Quality / Cash Rich"
        assert res_high["flag"] == "CASH_RICH_QUALITY_EARNINGS"
        assert res_high["accrual_ratio"] == -0.15
    finally:
        imported_db.query(FinancialSnapshot).filter(FinancialSnapshot.company_id.in_([cid_low, cid_high])).delete()
        imported_db.query(Company).filter(Company.company_id.in_([cid_low, cid_high])).delete()
        imported_db.commit()


def test_fridson_reality_spread_and_cash_drain():
    """Test Fridson spread, fixed-charge coverage, and automated cash drain alert."""
    s1 = FinancialSnapshot(
        fiscal_year=2022, ebitda=50_000_000.0, operating_cash_flow=45_000_000.0,
        ebit=40_000_000.0, interest_expense=10_000_000.0,
    )
    s2 = FinancialSnapshot(
        fiscal_year=2023, ebitda=65_000_000.0, operating_cash_flow=40_000_000.0,  # EBITDA up, CFO down!
        ebit=50_000_000.0, interest_expense=10_000_000.0,
    )
    res = analyze_fridson([s1, s2])
    assert res["widening_spread_flag"] is True
    assert res["cash_drain_alert"] is True
    assert res["fixed_charge_coverage"] == 5.0
    assert "Cash drain detected" in res["cash_drain_warning"]


def test_master_forensic_synthesizer(imported_db):
    """Test unified forensic health synthesizer integrating Schilit, Beneish, and Sloan."""
    health = synthesize_forensic_health(imported_db, "US:MSFT:US")
    assert health["forensic_health_score"] >= 70
    assert health["forensic_risk_tier"] in ("Clean / Low Forensic Risk", "Moderate Forensic Caution")
    assert "schilit" in health
    assert "beneish" in health
    assert "sloan" in health


def test_float_shrink_and_capital_return(imported_db):
    """Test 3y/5y float shrink tracking and dividend safety ratings."""
    res = compute_shareholder_yield(imported_db, "US:AAPL:US")
    assert "float_shrink_3y_pct" in res
    assert "dividend_safety_rating" in res
    assert res["dividend_safety_rating"] in ("Very Safe", "Safe", "Borderline", "No Dividend Paid")


def test_bank_engine_rules_and_metrics(imported_db):
    """Test specialized bank model for CA:RY:TSX strictly enforcing NULL corporate debt/FCF/gross."""
    bank = compute_bank_metrics(imported_db, "CA:RY:TSX")
    assert bank["status"] == "computed"
    assert bank["currency"] == "CAD"
    assert bank["corporate_debt"] is None
    assert bank["free_cash_flow"] is None
    assert bank["gross_profit"] is None
    assert bank["roaa_pct"] is not None and bank["roaa_pct"] > 0
    assert bank["roae_pct"] is not None and bank["roae_pct"] > 0
    assert bank["capital_health"] in ("Well Capitalized", "Adequate")
