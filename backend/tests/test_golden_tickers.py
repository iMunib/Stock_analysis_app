"""Directive-named alias: the golden battery lives in test_zz_golden_tickers.py
(loaded last so its universe-mutating ingest fixtures cannot pollute earlier
modules). This module re-runs the pure, read-only golden paths in-process."""
import pytest

from tests.test_zz_golden_tickers import (  # noqa: F401
    test_golden_aapl_roic_low_confidence,
    test_golden_msft_history_trust,
)


@pytest.fixture(scope="module")
def db(imported_db):
    return imported_db
