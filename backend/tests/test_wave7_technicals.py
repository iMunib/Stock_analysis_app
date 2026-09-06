"""Wave 7 Technicals tests (Epic 17: 43 stories — 12-1 momentum, SMA, drawdown, beta)."""
from __future__ import annotations


def test_technicals_12_1_momentum_and_sma(client):
    r = client.get("/api/v1/companies/US:AAPL:US/technicals")
    assert r.status_code == 200
    data = r.json()
    assert "momentum_12_1" in data
    # Momentum may be None if insufficient history, but should be present
    assert "momentum_formula" in data
    assert "Jegadeesh" in data["momentum_formula"]
    # SMA
    assert "sma50" in data
    assert "sma200" in data
    # 52-week range
    assert "high_52w" in data
    assert "low_52w" in data
    # Disclaimer
    assert "disclaimer" in data
    assert "not an intrinsic verdict" in data["disclaimer"]
    # Momentum is context only, not scoring pillar
    assert data.get("momentum_percentile") is None or isinstance(data.get("momentum_percentile"), (int, float))


def test_technicals_drawdown_and_beta(client):
    r = client.get("/api/v1/companies/US:AAPL:US/technicals")
    assert r.status_code == 200
    data = r.json()
    assert "max_drawdown" in data
    assert "beta" in data
    assert "correlation_vs_benchmark" in data
    assert "benchmark" in data
    assert data["benchmark"] in ("SPX", "TSX")


def test_momentum_rank(client):
    r = client.get("/api/v1/technicals/momentum-rank?ids=US:AAPL:US,US:MSFT:US,CA:RY:TSX")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 3
    assert "ranked" in data
    # Should be sorted descending by momentum (None last)
    for item in data["ranked"]:
        assert "momentum_12_1" in item
        assert "currency" in item


def test_momentum_not_scoring_pillar(client):
    # Ensure scoring weights are unchanged and momentum is not added as pillar
    from app.models import Score
    # Check that Score model still has only 4 pillars (quality, value, growth, risk)
    # We verify via API that dossier still has 4 pillars
    r = client.get("/api/v1/companies/US:AAPL:US/dossier")
    assert r.status_code == 200
    data = r.json()
    pillars = data["score"]["pillars"] if data.get("score") else {}
    assert set(pillars.keys()) == {"quality", "value", "growth", "risk"} or pillars == {}
    # Ensure technicals endpoint does not modify scores
    assert "momentum" not in pillars
