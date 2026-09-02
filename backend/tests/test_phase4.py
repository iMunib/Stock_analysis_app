"""Phase 4 tests: search, dossier, compare, similar, sector snapshot, meta. Network-free."""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def scores_computed(imported_db):
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    r = c.post("/api/v1/scores/recompute", json={"universe": "seed"})
    assert r.status_code == 200
    assert r.json()["companies_processed"] == 720
    return c


@pytest.fixture()
def computed(scores_computed):
    return scores_computed


def test_search_aapl(computed):
    r = computed.get("/api/v1/search?q=AAPL")
    assert r.status_code == 200
    body = r.json()
    ids = [i["company_id"] for i in body["items"]]
    assert "US:AAPL:US" in ids
    assert body["method_version"] == "v1"
    assert "not investment advice" in body["disclaimer"].lower()


def test_search_yahoo_symbol(computed):
    r = computed.get("/api/v1/search?q=RY.TO")
    assert r.status_code == 200
    ids = [i["company_id"] for i in r.json()["items"]]
    assert "CA:RY:TSX" in ids


def test_search_empty_q_400(computed):
    assert computed.get("/api/v1/search?q=").status_code == 400
    assert computed.get("/api/v1/search?q=%20%20").status_code == 400


def test_dossier_has_identity_score_disclaimer(computed):
    r = computed.get("/api/v1/companies/US:AAPL:US/dossier")
    assert r.status_code == 200
    body = r.json()
    assert body["identity"]["company_id"] == "US:AAPL:US"
    assert body["identity"]["currency"] == "USD"
    assert body["score"] is not None
    assert body["score"]["method_version"] == "v1"
    assert "not investment advice" in body["disclaimer"].lower()
    assert "latest_snapshot" in body
    assert isinstance(body["data_gaps"], list)


def test_dossier_404(computed):
    assert computed.get("/api/v1/companies/US:NOPE:US/dossier").status_code == 404


def test_compare_three_usd_ordered(computed):
    r = computed.get("/api/v1/compare?ids=US:AAPL:US,US:MSFT:US,US:GOOGL:US")
    assert r.status_code == 200
    body = r.json()
    assert body["currency_warning"] is False
    comps = [row["composite"] for row in body["rows"] if row["found"]]
    assert comps == sorted([c for c in comps if c is not None], reverse=True)


def test_compare_mixed_currency_warns(computed):
    r = computed.get("/api/v1/compare?ids=US:AAPL:US,CA:RY:TSX")
    assert r.status_code == 200
    body = r.json()
    assert body["currency_warning"] is True
    assert set(body["currencies"]) == {"USD", "CAD"}
    # money fields are per-row with that row's currency; no conversion
    for row in body["rows"]:
        if row["money"] is not None:
            assert row["money"]["currency"] in ("USD", "CAD")


def test_compare_bad_counts(computed):
    assert computed.get("/api/v1/compare?ids=US:AAPL:US").status_code == 400
    many = ",".join(f"US:T{i}:US" for i in range(9))
    assert computed.get(f"/api/v1/compare?ids={many}").status_code == 400


def test_similar_same_currency_only(computed):
    r = computed.get("/api/v1/companies/US:AAPL:US/similar?n=5")
    assert r.status_code == 200
    body = r.json()
    for item in body["items"]:
        assert item["currency"] == "USD"


def test_similar_null_score_409(computed):
    # CA:IIP.UN:TSX has insufficient_data (NULL composite)
    r = computed.get("/api/v1/companies/CA:IIP.UN:TSX/similar")
    assert r.status_code == 409


def test_sector_snapshot_requires_currency(computed):
    assert computed.get("/api/v1/sectors/Software/snapshot").status_code == 400


def test_sector_snapshot_dedup_and_shape(computed):
    r = computed.get("/api/v1/sectors/Software/snapshot?currency=USD")
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "USD"
    ids = [i["company_id"] for i in body["top"] + body["bottom"]]
    assert len(ids) == len(set(ids)), "no duplicate company rows"
    assert "median_composite" in body


def test_research_meta_shape(computed):
    r = computed.get("/api/v1/research/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["companies"] == 720
    assert body["scored"] >= 700
    assert "signal_histogram" in body
    assert body["method_version"] == "v1"
    assert "not investment advice" in body["disclaimer"].lower()


def test_no_scoring_formula_change_golden(computed):
    """Endpoints must not alter scores: dossier/compare mirror the Phase 3 stored value exactly."""
    s = computed.get("/api/v1/companies/US:AAPL:US/score").json()
    d = computed.get("/api/v1/companies/US:AAPL:US/dossier").json()
    assert d["score"]["composite"] == s["composite"]
    c = computed.get("/api/v1/compare?ids=US:AAPL:US,US:MSFT:US").json()
    aapl_row = next(r for r in c["rows"] if r["company_id"] == "US:AAPL:US")
    assert aapl_row["composite"] == s["composite"]


def test_empty_scores_table_does_not_crash(computed, imported_db):
    """If scores are wiped, search/dossier/compare still respond (scores null)."""
    from app.models import Score
    from sqlalchemy import delete

    imported_db.execute(delete(Score))
    imported_db.commit()
    try:
        assert computed.get("/api/v1/search?q=AAPL").status_code == 200
        d = computed.get("/api/v1/companies/US:AAPL:US/dossier")
        assert d.status_code == 200
        assert d.json()["score"] is None
        c = computed.get("/api/v1/compare?ids=US:AAPL:US,US:MSFT:US")
        assert c.status_code == 200
        assert all(r["composite"] is None for r in c.json()["rows"])
        assert computed.get("/api/v1/research/meta").json()["scored"] == 0
    finally:
        # restore scores deterministically
        computed.post("/api/v1/scores/recompute", json={"universe": "seed"})
