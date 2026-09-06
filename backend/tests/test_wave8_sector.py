"""Wave 8 Sector rotation tests (Epic 20)."""
def test_sector_rotation(client):
    r = client.get("/api/v1/sectors/rotation?currency=ALL")
    assert r.status_code == 200
    data = r.json()
    assert "sectors" in data
    assert len(data["sectors"]) >= 5
    assert data["currency"] == "ALL"
    assert "disclaimer" in data
    # CAD split
    r2 = client.get("/api/v1/sectors/rotation?currency=CAD")
    assert r2.status_code == 200
    assert r2.json()["currency"] == "CAD"

def test_cycle_tag_and_barrier(client):
    r = client.get("/api/v1/sectors/Information Technology/cycle-tag")
    assert r.status_code == 200
    assert "Early" in r.json()["cycle_tag"]
    r2 = client.get("/api/v1/sectors/Utilities/cycle-tag")
    assert "Defensive" in r2.json()["cycle_tag"]
    b = client.get("/api/v1/sectors/Information Technology/barrier?currency=USD")
    assert b.status_code == 200
    assert "barrier_assessment" in b.json() or "median_margin_stdev" in b.json()

def test_histogram_pure_svg(client):
    r = client.get("/api/v1/sectors/Information Technology/histogram?currency=USD&metric=composite")
    assert r.status_code == 200
    data = r.json()
    assert data["metric"] == "composite"
    assert len(data["bins"]) == 5
    assert len(data["bin_edges"]) == 5
    assert data["sheet"] == "Information Technology"
