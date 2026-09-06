"""Tests for Piotroski F-Score, DuPont ROE Decomposition, and Peer Percentile Matrix."""
from __future__ import annotations

from app.services.dupont_engine import compute_dupont_analysis
from app.services.peer_engine import compute_peer_comparison_matrix
from app.services.piotroski_engine import compute_piotroski_f_score


def test_piotroski_f_score_engine(imported_db):
    db = imported_db
    res = compute_piotroski_f_score(db, "US:AAPL:US")
    assert res["company_id"] == "US:AAPL:US"
    assert 0 <= res["f_score"] <= 9
    assert res["f_possible"] >= 1
    assert res["signal"] in ("Strong", "Moderate", "Weak")
    assert "profitability" in res["categories"]
    assert "leverage_liquidity" in res["categories"]
    assert "efficiency" in res["categories"]

    # Invariant check: bank handling (Rule #8)
    bank_res = compute_piotroski_f_score(db, "US:JPM:US")
    if bank_res.get("f_possible"):
        assert bank_res["is_bank"] is True
        # Rule #8: debt/margin tests must be None for banks
        assert bank_res["tests"]["leverage_down"]["passed"] is None
        assert bank_res["tests"]["gross_margin_up"]["passed"] is None


def test_dupont_decomposition_engine(imported_db):
    db = imported_db
    res = compute_dupont_analysis(db, "US:AAPL:US")
    assert res["company_id"] == "US:AAPL:US"
    assert "latest" in res
    assert "history" in res
    assert len(res["history"]) >= 1
    lat = res["latest"]
    if lat and lat.get("roe_3stage") is not None:
        # Check 3-stage identity: ROE ~ Net Margin * Asset Turnover * Equity Multiplier
        expected = lat["net_profit_margin"] * lat["asset_turnover"] * lat["equity_multiplier"]
        assert abs(lat["roe_3stage"] - expected) < 1e-3


def test_peer_comparison_matrix_currency_isolation(imported_db):
    db = imported_db
    us_res = compute_peer_comparison_matrix(db, "US:AAPL:US")
    assert "USD" in us_res["peer_group"]
    assert us_res["peer_count"] >= 1
    assert "valuation" in us_res["pillars"]
    assert "quality" in us_res["pillars"]

    ca_res = compute_peer_comparison_matrix(db, "CA:SHOP:TSX")
    assert "CAD" in ca_res["peer_group"]
    assert "USD" not in ca_res["peer_group"]


def test_api_endpoints_return_200(client):
    r1 = client.get("/api/v1/companies/US:AAPL:US/piotroski")
    assert r1.status_code == 200
    p_data = r1.json()
    assert "f_score" in p_data

    r2 = client.get("/api/v1/companies/US:AAPL:US/dupont")
    assert r2.status_code == 200
    d_data = r2.json()
    assert "history" in d_data

    r3 = client.get("/api/v1/companies/US:AAPL:US/peer-matrix")
    assert r3.status_code == 200
    pm_data = r3.json()
    assert "pillars" in pm_data
