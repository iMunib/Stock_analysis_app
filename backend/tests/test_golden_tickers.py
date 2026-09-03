"""Directive-named alias: the full mutating battery lives in test_zz_golden_tickers.py
(loaded last so its universe-mutating ingest fixtures cannot pollute earlier modules).
This module re-runs the golden paths with strict cleanup.
"""
import pytest

from app.models import Company, Score
from tests.test_zz_golden_tickers import (  # noqa: F401
    test_golden_msft_history_trust,
    test_golden_aapl_roic_low_confidence,
    test_golden_pypl_commercial_metrics,
    test_golden_ry_canadian_bank,
    test_golden_afl_insurer_path,
    test_golden_iip_un_insufficient_data,
    test_golden_penman_aapl_vs_ry,
    test_golden_schilit_msft_clean,
    test_golden_graham_msft_number,
    test_golden_ry_beneish_exclusion_cad,
    test_golden_amd_sbc_drag_dilution,
    test_golden_etf_constituent_missing_symbols_graceful,
)
from app.models import FinancialSnapshot


@pytest.fixture(scope="module")
def db(imported_db):
    return imported_db


def test_golden_kits_symbol_normalization(db):
    """CA:KITS:TSX normalization with cleanup to preserve 720 company count."""
    try:
        from tests.test_zz_golden_tickers import test_golden_kits_symbol_normalization as _test
        _test(db)
    finally:
        s = db.get(Score, "CA:KITS:TSX")
        if s:
            db.delete(s)
        c = db.get(Company, "CA:KITS:TSX")
        if c:
            db.delete(c)
        db.commit()


def test_golden_baba_adr_currency_rules(db):
    """US:BABA:US ADR rules with cleanup to preserve 720 company count."""
    try:
        from tests.test_zz_golden_tickers import test_golden_baba_adr_currency_rules as _test
        _test(db)
    finally:
        c = db.get(Company, "US:BABA:US")
        if c:
            db.delete(c)
        db.commit()


def test_golden_msft_beneish_and_etf_tags(db):
    """MSFT Beneish & ETF tags with cleanup to preserve zero invented years for Phase 1."""
    try:
        from tests.test_zz_golden_tickers import test_golden_msft_beneish_and_etf_tags as _test
        _test(db)
    finally:
        for s in db.query(FinancialSnapshot).filter(
            FinancialSnapshot.company_id == "US:MSFT:US",
            FinancialSnapshot.fiscal_year.isnot(None),
        ).all():
            db.delete(s)
        db.commit()


def test_golden_aapl_net_shareholder_yield(db):
    """AAPL True Shareholder Yield with cleanup to preserve zero invented years for Phase 1."""
    try:
        from tests.test_zz_golden_tickers import test_golden_aapl_net_shareholder_yield as _test
        _test(db)
    finally:
        for s in db.query(FinancialSnapshot).filter(
            FinancialSnapshot.company_id == "US:AAPL:US",
            FinancialSnapshot.fiscal_year.isnot(None),
        ).all():
            db.delete(s)
        db.commit()
