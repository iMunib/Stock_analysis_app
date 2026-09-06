"""Wave 8 Governance tests (Epic 23)."""
def test_model_risk_register(client):
    r = client.get("/api/v1/governance/model-risk")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 6
    assert any("Composite" in i["model"] for i in data["items"])
    assert any("Beneish" in i["model"] for i in data["items"])
    assert "disclaimer" in data
    # Check false_positive spelled correctly
    assert any("false" in str(i).lower() for i in data["items"])

def test_canon_map(client):
    r = client.get("/api/v1/governance/canon-map")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 8
    assert any("Graham" in i["book"] for i in data["items"])
    assert any("Buffett" in i["book"] for i in data["items"])
    assert any("Greenblatt" in i["book"] for i in data["items"])

def test_diff_matrix(client):
    r = client.get("/api/v1/governance/diff-matrix")
    assert r.status_code == 200
    data = r.json()
    assert "columns" in data
    assert "Simply Wall St" in str(data["columns"])
    assert "GuruFocus" in str(data["columns"])
    assert "TIKR" in str(data["columns"])
    assert len(data["rows"]) >= 5
    # First row should be forensic suite
    assert any("Forensic" in str(row) for row in data["rows"])
