"""Wave 8 Backtesting tests (Epic 21)."""
def test_factor_decay(client):
    r = client.get("/api/v1/backtesting/factor-decay")
    assert r.status_code == 200
    data = r.json()
    assert "factors" in data
    assert any("Piotroski" in f["factor"] for f in data["factors"])
    assert any("58%" in f["decay"] or "58%" in data.get("headline","") for f in data["factors"])
    # McLean & Pontiff headline
    assert "58%" in data["headline"] or any("58%" in f["decay"] for f in data["factors"])

def test_survivorship_and_follow_through(client):
    r = client.get("/api/v1/backtesting/survivorship")
    assert r.status_code == 200
    data = r.json()
    assert "survivorship" in str(data).lower() or "universe_construction" in data
    assert "lookahead" in str(data).lower()
    assert "disclaimer" in data
    r2 = client.get("/api/v1/backtesting/signal-follow-through")
    assert r2.status_code == 200
    assert "bias_note" in r2.json() or "method" in r2.json()

def test_overfitting_warning(client):
    # >5 constraints -> warning
    heavy = {"roic_min": 0.15, "ev_ebitda_max": 10, "gross_profitability_min": 0.3, "sbc_dilution_max": 0.03, "peg_max": 1.5, "composite_min": 6, "custom": 1}
    r = client.post("/api/v1/backtesting/overfitting-check", json=heavy)
    assert r.status_code == 200
    data = r.json()
    assert data["constraints"] > 5
    assert data["warning"] is not None
    assert "overfitting" in data["warning"].lower()
    # <=5 no warning
    light = {"roic_min": 0.15, "ev_ebitda_max": 10}
    r2 = client.post("/api/v1/backtesting/overfitting-check", json=light)
    assert r2.status_code == 200
    assert r2.json()["warning"] is None
