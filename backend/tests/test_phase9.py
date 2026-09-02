"""Phase 9 backend tests: currency=ALL rankings never blend money."""
from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def scored():
    with TestClient(app) as c:
        r = c.post("/api/v1/scores/recompute", json={"universe": "seed"})
        assert r.status_code == 200
        yield c


def test_sector_rankings_all_returns_both_currencies(scored):
    r = scored.get("/api/v1/sectors/Banks/rankings?currency=ALL&limit=500")
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "ALL"
    currencies = {i["currency"] for i in body["items"]}
    assert currencies == {"USD", "CAD"}, "ALL must include both currencies"
    comps = [i["composite"] for i in body["items"] if i["composite"] is not None]
    assert comps == sorted(comps, reverse=True)


def test_sector_rankings_all_never_blends_money(scored):
    """The ALL response carries per-row money fields from each company's own
    snapshot and NO money medians at all — nothing to average."""
    r = scored.get("/api/v1/sectors/Banks/rankings?currency=ALL&limit=500")
    body = r.json()
    assert "median_pe" not in body and "median_pb" not in body and "median_roe" not in body
    for item in body["items"]:
        assert item["currency"] in ("USD", "CAD")
        assert "ticker" in item and "pe_calc" in item and "pb_calc" in item and "roe_calc" in item
    # a USD bank's pe_calc equals its USD-mode value (no cross-currency fill)
    usd = scored.get("/api/v1/sectors/Banks/rankings?currency=USD&limit=500").json()
    usd_pe = {i["company_id"]: i.get("pe_calc") for i in usd["items"]}
    for item in body["items"]:
        if item["currency"] == "USD" and item["company_id"] in usd_pe:
            assert item["pe_calc"] == usd_pe[item["company_id"]]


def test_sector_rankings_usd_still_single_currency(scored):
    r = scored.get("/api/v1/sectors/Banks/rankings?currency=USD&limit=500")
    body = r.json()
    assert all(i["currency"] == "USD" for i in body["items"])
