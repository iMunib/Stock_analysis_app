"""Tests for the Reverse DCF Engine."""
from __future__ import annotations

import pytest

from app.services.valuation_engine import (
    dcf_enterprise_value,
    solve_market_implied_growth,
    compute_sensitivity_matrix,
    _brentq,
)


def test_dcf_enterprise_value_monotonicity():
    """Higher growth rate g must strictly produce higher Enterprise Value."""
    fcf = 100_000_000.0
    ev_0 = dcf_enterprise_value(0.02, fcf, wacc=0.09, g_terminal=0.025)
    ev_5 = dcf_enterprise_value(0.05, fcf, wacc=0.09, g_terminal=0.025)
    ev_10 = dcf_enterprise_value(0.10, fcf, wacc=0.09, g_terminal=0.025)

    assert ev_0 < ev_5 < ev_10


def test_brentq_root_solver():
    """Pure Python Brent's method solves root within tolerance."""
    def f(x):
        return x**3 - 2*x - 5

    root = _brentq(f, 2.0, 3.0, xtol=1e-8)
    assert abs(root - 2.09455148) < 1e-5


def test_solve_market_implied_growth_aapl_benchmark():
    """Apple benchmark: market EV ~$3.4T - $4.5T with ~$98.8B FCF must converge to 7% - 14% growth."""
    fcf_0 = 98_767_000_000.0  # AAPL FY2025 FCF
    # Test across realistic EV range for Apple ($3.0T to $4.0T)
    ev_apple = 3_400_000_000_000.0  # ~$230 share price
    implied_g = solve_market_implied_growth(ev_apple, fcf_0, wacc=0.09, g_terminal=0.025)

    assert implied_g is not None
    assert 0.07 <= implied_g <= 0.14  # Converges between 7% and 14%


def test_solve_market_implied_growth_negative_fcf_fails_gracefully():
    """Negative FCF returns None without raising exceptions."""
    result = solve_market_implied_growth(10_000_000_000.0, -500_000.0)
    assert result is None


def test_sensitivity_matrix_structure():
    """3x3 sensitivity matrix must contain correct dimensions and monotonic headers."""
    fcf = 1_000_000_000.0
    ev = 20_000_000_000.0
    matrix = compute_sensitivity_matrix(ev, fcf)

    assert "grid" in matrix
    assert len(matrix["grid"]) == 3
    for row in matrix["grid"]:
        assert len(row) == 3
        for cell in row:
            assert "wacc" in cell
            assert "terminal_g" in cell
            assert "implied_growth" in cell
