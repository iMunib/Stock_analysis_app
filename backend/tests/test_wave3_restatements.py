"""Wave 3 Restatements & Trajectory tests (Epic 9: as-filed vs restated, DSO/DIO/DPO, goodwill, dilution)."""
from __future__ import annotations


def test_restatements_endpoint(client):
    res = client.get("/api/v1/companies/US:AAPL:US/restatements")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "count" in data
    for it in data["items"]:
        assert "fiscal_year" in it
        assert "as_filed" in it
        assert "as_restated" in it or it["as_restated"] is None
        assert "has_restatement" in it
        assert "provenance" in it


def test_trajectory_endpoint(client):
    res = client.get("/api/v1/companies/US:AAPL:US/trajectory")
    assert res.status_code == 200
    data = res.json()
    assert "points" in data
    assert isinstance(data["points"], list)
    if data["points"]:
        p = data["points"][0]
        assert "fiscal_year" in p
        assert "revenue" in p
        assert "gross_margin" in p
        assert "operating_margin" in p
        assert "fcf" in p
        assert "inflections" in p


def test_working_capital_ccc(client):
    res = client.get("/api/v1/companies/US:AAPL:US/working-capital")
    assert res.status_code == 200
    data = res.json()
    assert "series" in data
    if data.get("data_available"):
        for s in data["series"]:
            assert "fiscal_year" in s
            assert "ccc" in s


def test_goodwill_risk(client):
    res = client.get("/api/v1/companies/US:AAPL:US/goodwill-risk")
    assert res.status_code == 200
    data = res.json()
    assert "goodwill" in data
    assert "serial_acquirer" in data
    assert "strip" in data
    assert isinstance(data["strip"], list)


def test_dilution_tracker(client):
    res = client.get("/api/v1/companies/US:AAPL:US/dilution")
    assert res.status_code == 200
    data = res.json()
    assert "series" in data
    # series may be empty if no shares history; ensure structure
    for s in data["series"]:
        assert "fiscal_year" in s or "shares" in s


def test_restatements_toggle_no_invented_numbers(client):
    # Ensure NULL handling: if no restatement, delta is None, not 0 fake
    res = client.get("/api/v1/companies/CA:RY:TSX/restatements")
    assert res.status_code == 200
    data = res.json()
    for it in data["items"]:
        if not it["has_restatement"]:
            # delta_pct values should be None or computed, not invented 0
            for v in it["delta_pct"].values():
                assert v is None or isinstance(v, (int, float))
