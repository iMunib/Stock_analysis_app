"""Tests for TTM Normalization and Forensic Ratios."""
from __future__ import annotations

import pytest

from app.models import Company, FinancialSnapshot
from app.services.ttm_engine import compute_and_store_ttm


def test_ttm_forensics_computation(imported_db):
    """Verify Sloan Accrual, ROIC, and Cash Conversion calculation on a company."""
    c = Company(
        company_id="US:TESTCO:US",
        ticker="TESTCO",
        country="US",
        currency="USD",
        name="Test Corp",
        is_deleted=False,
    )
    imported_db.merge(c)
    imported_db.flush()

    # Annual snapshot: Net income 100M, Operating Cash Flow 80M, Total Assets 1000M, Total Debt 200M, Book Equity 400M, Cash 100M
    snap = FinancialSnapshot(
        company_id="US:TESTCO:US",
        fiscal_year=2024,
        period_type="FY",
        revenue=500_000_000.0,
        ebit=120_000_000.0,
        net_income=100_000_000.0,
        operating_cash_flow=80_000_000.0,
        fcf_calc=60_000_000.0,
        total_assets=1_000_000_000.0,
        total_debt=200_000_000.0,
        book_equity=400_000_000.0,
        cash_st_investments=100_000_000.0,
        shares_snapshot=10_000_000.0,
        price=50.0,
    )
    imported_db.merge(snap)
    imported_db.commit()

    ttm = compute_and_store_ttm(imported_db, "US:TESTCO:US")

    # Sloan Accrual: (Net Income - Operating Cash Flow) / Total Assets = (100 - 80) / 1000 = 0.02
    assert ttm.sloan_accrual_ratio == pytest.approx(0.02, abs=1e-4)

    # Cash Conversion: FCF / Net Income = 60 / 100 = 0.60
    assert ttm.cash_conversion_ratio == pytest.approx(0.60, abs=1e-4)

    # Invested Capital: Debt (200) + Equity (400) - Cash (100) = 500M
    assert ttm.invested_capital == pytest.approx(500_000_000.0)

    # NOPAT: 120M * (1 - 0.21) = 94.8M
    assert ttm.nopat == pytest.approx(94_800_000.0)

    # ROIC: NOPAT / Invested Capital = 94.8M / 500M = 0.1896 (18.96%)
    assert ttm.roic == pytest.approx(0.1896, abs=1e-4)
