"""Wave 6 Export Suite tests (Epic 13: 48 stories)."""
from __future__ import annotations


def test_research_memo_markdown_and_json(client):
    res = client.get("/api/v1/companies/US:AAPL:US/export/memo?format=json")
    assert res.status_code == 200
    data = res.json()
    assert "markdown" in data
    assert "Personal research software" in data["markdown"] or "Personal research software" in data["disclaimer"]
    # Markdown download
    md = client.get("/api/v1/companies/US:AAPL:US/export/memo?format=markdown")
    assert md.status_code == 200
    assert "text/markdown" in md.headers["content-type"]
    assert "Research Memo" in md.text
    assert "Personal research software" in md.text


def test_raw_dump_and_factsheet(client):
    raw = client.get("/api/v1/companies/US:AAPL:US/export/raw")
    assert raw.status_code == 200
    assert "snapshots" in raw.json()
    assert "currency_note" in raw.json()
    fact = client.get("/api/v1/companies/US:AAPL:US/export/factsheet")
    assert fact.status_code == 200
    assert "factsheet" in fact.json()
    assert "print_note" in fact.json()


def test_batch_export_currency_tagged(client):
    res = client.get("/api/v1/export/batch?ids=US:AAPL:US,US:MSFT:US&format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    text = res.text
    assert "US:AAPL:US" in text
    assert "US:MSFT:US" in text
    # Currency per row
    assert "USD" in text or "CAD" in text
    # No averaging note
    assert "never averaged" in text.lower() or "native" in text.lower()

    j = client.get("/api/v1/export/batch?ids=US:AAPL:US&format=json")
    assert j.status_code == 200
    assert j.json()["count"] == 1


def test_journal_export_and_portfolio_review(client):
    # Ensure at least one journal exists (from wave5)
    client.post("/api/v1/portfolio/journal", json={"company_id": "US:AAPL:US", "confidence": 4, "strategy_tag": "quality", "thesis": "Test thesis"})
    j = client.get("/api/v1/export/journal")
    assert j.status_code == 200
    assert "entries" in j.json()
    assert "avg_confidence" in j.json()

    review = client.get("/api/v1/portfolio/export/review")
    assert review.status_code == 200
    assert "portfolio_summary" in review.json()
    assert "journal" in review.json()
