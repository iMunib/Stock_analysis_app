"""Tests for Moat/SWOT research draft endpoint and company profile data.

Requirements:
- POST /api/v1/companies/{id}/research drafts SWOT with mock LLM
- Caches output on second call
- Refuses if model is not :free
- Unknown company returns 404
- Dossier exposes profile summary, dividends, next earnings, and quarterly statement
"""
from __future__ import annotations

import pytest
from app.models import CompanyProfile


def test_swot_draft_with_mock_llm(client, monkeypatch):
    """POST /api/v1/companies/{id}/research returns structured SWOT and caches."""
    mock_swot_text = (
        "Strengths:\n- High return on equity above peers.\n- Strong positive cash flow.\n\n"
        "Weaknesses:\n- High valuation multiples.\n- Revenue growth moderate.\n\n"
        "Opportunities:\n- Expansion into cloud and services.\n\n"
        "Threats:\n- Regulatory scrutiny in core markets.\n\n"
        "Competitive advantage: Strong ecosystem lock-in and pricing power.\n\n"
        "LLM draft from our facts. Not a 10-K. Research notes, not investment advice."
    )

    monkeypatch.setattr(
        "app.services.llm.draft_swot",
        lambda facts, model, fallback, timeout=45.0: {
            "swot": mock_swot_text,
            "model": "minimax/minimax-m3:free",
            "elapsed_ms": 120,
        },
    )
    monkeypatch.setattr(
        "app.services.llm.llm_status",
        lambda model, fallback: {
            "configured": True,
            "model": "minimax/minimax-m3:free",
            "fallback": "mistralai/mistral-small-24b-instruct-2501:free",
            "free_latch": True,
        },
    )
    # Ensure clean cache for this company/model
    from app.db import SessionLocal as _SessionLocal
    from app.models import LlmCache as _LlmCache
    try:
        with _SessionLocal() as _s:
            _s.query(_LlmCache).filter(_LlmCache.subject_id == "US:MSFT:US", _LlmCache.kind == "swot").delete()
            _s.commit()
    except Exception:
        pass

    # First call: not cached
    res = client.post("/api/v1/companies/US:MSFT:US/research")
    assert res.status_code == 200
    data = res.json()
    assert "Strengths" in data["swot"]
    assert "Weaknesses" in data["swot"]
    assert "Competitive advantage" in data["swot"]
    assert data["label"] == "LLM draft from our facts. Not a 10-K."
    assert data["company_id"] == "US:MSFT:US"
    assert data["cached"] is False

    # Second call: must be cached
    res2 = client.post("/api/v1/companies/US:MSFT:US/research")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["cached"] is True
    assert data2["swot"] == data["swot"]


def test_swot_refuses_non_free_model(client, monkeypatch):
    """Refuses if model is paid / not a :free model."""
    monkeypatch.setattr("app.services.narration.OPENROUTER_MODEL", "openai/gpt-4o")
    monkeypatch.setattr(
        "app.services.llm.llm_status",
        lambda model, fallback: {
            "configured": True,
            "model": "openai/gpt-4o",
            "fallback": "openai/gpt-4o-mini",
            "free_latch": False,
        },
    )

    res = client.post("/api/v1/companies/US:MSFT:US/research")
    assert res.status_code in (503, 400)


def test_swot_unknown_company_returns_404(client):
    res = client.post("/api/v1/companies/US:DOESNOTEXIST:US/research")
    assert res.status_code == 404


def test_dossier_includes_profile_and_quarterly(client, imported_db):
    """Dossier payload exposes profile summary, dividend metrics, next earnings, and quarterly rows."""
    # Seed a CompanyProfile in the test database
    prof = CompanyProfile(
        company_id="US:MSFT:US",
        summary="Microsoft Corporation develops software, devices, and solutions worldwide.",
        dividend_yield=0.0075,
        dividend_rate=3.00,
        next_earnings_date="2026-10-25",
        quarterly_json=[
            {"date": "2026-06-30", "revenue": 64700000000.0, "net_income": 22000000000.0, "diluted_eps": 2.95},
            {"date": "2026-03-31", "revenue": 61800000000.0, "net_income": 21900000000.0, "diluted_eps": 2.94},
        ],
    )
    imported_db.merge(prof)
    imported_db.commit()

    res = client.get("/api/v1/companies/US:MSFT:US/dossier")
    assert res.status_code == 200
    d = res.json()
    assert "profile" in d
    assert d["profile"] is not None
    assert "Microsoft Corporation develops" in (d["profile"]["summary"] or "")
    assert d["profile"]["dividend_rate"] == 3.00
    assert d["profile"]["next_earnings_date"] == "2026-10-25"
    assert "quarterly" in d
    assert len(d["quarterly"]) == 2
    assert d["quarterly"][0]["diluted_eps"] == 2.95
