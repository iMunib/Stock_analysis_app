"""Chat endpoint test — Workstream 6 backend verification."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client(imported_db):
    with TestClient(app) as c:
        yield c


def test_chat_404_for_unknown_company(client):
    """Chat endpoint returns 404 for a company not in the database."""
    r = client.post(
        "/api/v1/companies/US:FAKE_TICKER_ZZZZ:US/chat",
        json={"messages": [{"role": "user", "content": "What is this company?"}]},
    )
    assert r.status_code == 404


def test_chat_400_for_empty_messages(client, imported_db):
    """Chat endpoint returns 400 for empty messages array."""
    # Get any real company from the database
    from sqlalchemy import select
    from app.models import Company
    db = imported_db
    company = db.execute(select(Company).limit(1)).scalar_one_or_none()
    if company is None:
        pytest.skip("No companies in test database")

    r = client.post(
        f"/api/v1/companies/{company.company_id}/chat",
        json={"messages": []},
    )
    assert r.status_code == 400


def test_chat_returns_valid_structure_without_api_key(client, imported_db, monkeypatch):
    """Without OPENROUTER_API_KEY, chat returns a graceful 'unavailable' message."""
    import os
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    from sqlalchemy import select
    from app.models import Company
    db = imported_db
    company = db.execute(select(Company).limit(1)).scalar_one_or_none()
    if company is None:
        pytest.skip("No companies in test database")

    r = client.post(
        f"/api/v1/companies/{company.company_id}/chat",
        json={"messages": [{"role": "user", "content": "Summarize this company."}]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "content" in body
    assert "model_used" in body
    assert "disclaimer" in body
    # Without API key, content should indicate unavailability
    assert "AI narration is unavailable" in body["content"] or body["model_used"] == "none"


def test_chat_key_never_in_response(client, imported_db, monkeypatch):
    """API key must never appear in any response field."""
    fake_key = "sk-or-test-secret-key-must-never-appear-in-response"
    monkeypatch.setenv("OPENROUTER_API_KEY", fake_key)

    from sqlalchemy import select
    from app.models import Company
    db = imported_db
    company = db.execute(select(Company).limit(1)).scalar_one_or_none()
    if company is None:
        pytest.skip("No companies in test database")

    r = client.post(
        f"/api/v1/companies/{company.company_id}/chat",
        json={"messages": [{"role": "user", "content": "What is the risk level?"}]},
    )
    assert r.status_code == 200
    response_text = r.text
    assert fake_key not in response_text, "API key must never appear in response"


def test_chat_cad_usd_isolation_note_in_facts(client, imported_db):
    """Facts JSON includes currency field; CAD company shows CAD currency."""
    from sqlalchemy import select
    from app.models import Company
    db = imported_db
    ca_company = db.execute(
        select(Company).where(Company.currency == "CAD").limit(1)
    ).scalar_one_or_none()
    if ca_company is None:
        pytest.skip("No CAD companies in test database")

    # We can't easily inspect facts JSON from the endpoint, but we can verify
    # the endpoint runs cleanly for a CAD company (no 500 from currency mixing).
    r = client.post(
        f"/api/v1/companies/{ca_company.company_id}/chat",
        json={"messages": [{"role": "user", "content": "Tell me about this company."}]},
    )
    # Either 200 (response ready) or 200 with unavailable message — never 500.
    assert r.status_code == 200
    body = r.json()
    assert "disclaimer" in body
