"""Wave 8 Curriculum tests (Epic 18)."""
def test_curriculum_modules(client):
    r = client.get("/api/v1/curriculum/modules")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 6
    assert len(data["items"]) == 6
    ids = {m["id"] for m in data["items"]}
    assert "m01-balance-sheet" in ids
    assert "m06-advanced-manipulation" in ids
    assert "disclaimer" in data

def test_curriculum_module_detail_and_quiz(client):
    r = client.get("/api/v1/curriculum/modules/m01-balance-sheet")
    assert r.status_code == 200
    assert r.json()["id"] == "m01-balance-sheet"
    q = client.get("/api/v1/curriculum/quiz/m01-balance-sheet")
    assert q.status_code == 200
    assert len(q.json()["questions"]) >= 1
    # 404 for unknown
    r2 = client.get("/api/v1/curriculum/modules/unknown")
    assert r2.status_code == 404

def test_flashcards_and_case_studies(client):
    r = client.get("/api/v1/curriculum/flashcards")
    assert r.status_code == 200
    assert r.json()["count"] >= 6
    r2 = client.get("/api/v1/curriculum/case-studies")
    assert r2.status_code == 200
    assert any("Enron" in c["title"] for c in r2.json()["items"])
    assert any("Berkshire" in c["title"] for c in r2.json()["items"])

def test_10k_reader(client):
    r = client.get("/api/v1/curriculum/10k-reader/US:AAPL:US")
    assert r.status_code == 200
    data = r.json()
    assert data["company_id"] == "US:AAPL:US"
    assert len(data["annotations"]) >= 3
    assert any("Revenue" in a["line_item"] for a in data["annotations"])
