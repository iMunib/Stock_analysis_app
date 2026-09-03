"""Tests for Common-Size Financial Statement Engine (Master Directive WS2)."""
import pytest
from app.models import Company, FinancialSnapshot
from app.services.common_size_engine import compute_common_size


def test_common_size_percentage_calculations(imported_db):
    """Test common size percentages for revenue and asset line items."""
    res = compute_common_size(imported_db, "US:MSFT:US", years=5)
    assert res["company_id"] == "US:MSFT:US"
    assert res["currency"] == "USD"
    assert res["years_delivered"] >= 1

    # Check Income Statement
    is_rows = res["income_statement_common_size"]
    assert len(is_rows) >= 1
    latest_is = is_rows[-1]
    assert latest_is["revenue"]["pct"] == 100.0
    if latest_is["gross_profit"]["raw"] is not None and latest_is["revenue"]["raw"]:
        expected_gp_pct = round((latest_is["gross_profit"]["raw"] / latest_is["revenue"]["raw"]) * 100.0, 2)
        assert latest_is["gross_profit"]["pct"] == expected_gp_pct

    # Check Balance Sheet
    bs_rows = res["balance_sheet_common_size"]
    assert len(bs_rows) >= 1
    latest_bs = bs_rows[-1]
    assert latest_bs["total_assets"]["pct"] == 100.0
    if latest_bs["total_debt"]["raw"] is not None and latest_bs["total_assets"]["raw"]:
        expected_debt_pct = round((latest_bs["total_debt"]["raw"] / latest_bs["total_assets"]["raw"]) * 100.0, 2)
        assert latest_bs["total_debt"]["pct"] == expected_debt_pct


def test_common_size_margin_drift_detection(imported_db):
    """Test margin contraction and cost creep flag detection on synthetic history."""
    cid = "US:TEST_DRIFT:US"
    imported_db.add(Company(company_id=cid, ticker="TEST_DRIFT", country="US", currency="USD", name="Test Drift Inc"))
    # Year 1: High margin, low cost
    imported_db.add(FinancialSnapshot(
        company_id=cid, fiscal_year=2021, period_type="FY",
        revenue=1000.0, gross_profit=600.0, ebit=300.0, total_assets=2000.0, total_liabilities=1000.0, book_equity=1000.0,
    ))
    # Year 2: Declining margin
    imported_db.add(FinancialSnapshot(
        company_id=cid, fiscal_year=2022, period_type="FY",
        revenue=1000.0, gross_profit=550.0, ebit=200.0, total_assets=2000.0, total_liabilities=1000.0, book_equity=1000.0,
    ))
    # Year 3: Severe contraction (OM 30% -> 10% = -2000 bps) and cost creep (OpEx/Rev 30% -> 35% = +500 bps)
    imported_db.add(FinancialSnapshot(
        company_id=cid, fiscal_year=2023, period_type="FY",
        revenue=1000.0, gross_profit=450.0, ebit=100.0, total_assets=2000.0, total_liabilities=1000.0, book_equity=1000.0,
    ))
    imported_db.commit()

    try:
        res = compute_common_size(imported_db, cid, years=5)
        flag_codes = [f["code"] for f in res["margin_drift_flags"]]
        assert "MARGIN_CONTRACTION" in flag_codes
        assert "COST_CREEP" in flag_codes
    finally:
        imported_db.query(FinancialSnapshot).filter_by(company_id=cid).delete()
        imported_db.query(Company).filter_by(company_id=cid).delete()
        imported_db.commit()
