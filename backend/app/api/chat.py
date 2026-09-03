"""Fact-grounded stock AI chat assistant (Workstream 6).

POST /api/v1/companies/{company_id}/chat

Assembles a facts JSON from deterministic DB columns (financials, scores,
ratios, flags) and passes them to an OpenRouter free model with an adversarial
fundamental analyst system prompt.

Rules (invariants enforced here):
- LLM may ONLY reference facts provided in the context JSON; no web access.
- LLM CANNOT create, overwrite, or 'correct' any numerical fundamental.
- Scores, pillars, and flags are deterministic math — the model is told this
  explicitly.
- CAD/USD money is NEVER mixed; currency field is always passed alongside
  every monetary value.
- Response is labelled as AI-generated narration; final disclaimer appended.
- API key never logged or returned in JSON.
- Model selection: meta-llama/llama-3.3-70b-instruct:free (fallback:
  mistralai/mistral-small-24b-instruct-2501:free).
"""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import (
    Company,
    CompanyProfile,
    FinancialSnapshot,
    FinancialSnapshotTTM,
    HalalFlag,
    Score,
)
from app.services.llm import call_openrouter

router = APIRouter(prefix="/api/v1", tags=["chat"])

_DISCLAIMER = (
    "⚠️ AI narration generated from stored facts. "
    "This is NOT investment advice. All numerical values are sourced from "
    "deterministic math or filed data — the AI cannot alter them."
)

_SYSTEM_PROMPT = """You are an adversarial fundamental equity analyst with 20+ years of experience.
Your job: critically assess the investment thesis for the company described below using ONLY the
facts provided in the FACTS JSON. Do not invent numbers, estimates, or prices not present in the JSON.

Rules:
1. If a fact is missing (null), say "data not available" — do not guess.
2. Scores (Quality/Value/Growth/Risk/Composite) are deterministic math outputs; do not re-interpret them.
3. Never recommend buy/sell/hold. Be analytical and balanced.
4. CAD companies report in CAD; do not convert to USD or compare money cross-currency.
5. Highlight both strengths AND concerns. Be constructive, not promotional.
6. Maximum 300 words per response.
7. End every response with: "Source: deterministic fundamentals + filed data only."
"""


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    model_used: str
    facts_version: str = "deterministic_v1"
    disclaimer: str = _DISCLAIMER


def _build_facts(db: Session, company_id: str) -> dict[str, Any]:
    """Assemble a fact-grounded JSON from deterministic DB data only."""
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {company_id!r} not found")

    facts: dict[str, Any] = {
        "company_id": company_id,
        "name": company.name,
        "ticker": company.ticker,
        "country": company.country,
        "currency": company.currency,  # always pass currency alongside money
        "reporting_currency": company.reporting_currency,
        "gics_sector": company.gics_sector,
        "industry": company.custom_industry_sheet,
        "fiscal_year_end": company.fiscal_year_end,
    }

    # Latest annual snapshot
    snaps = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.desc().nullsfirst())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    seed = next((s for s in snaps if s.fiscal_year is None), None)
    current = dated[0] if dated else seed

    def _s(v: Any, label: str = "") -> Any:
        """Numeric values — always None-safe."""
        return round(v, 4) if isinstance(v, float) else v

    if current:
        cur_currency = current.currency or company.currency
        facts["financials"] = {
            "fiscal_year": current.fiscal_year,
            "currency": cur_currency,
            "revenue": _s(current.revenue),
            "gross_profit": _s(current.gross_profit),
            "ebit": _s(current.ebit),
            "ebitda": _s(current.ebitda),
            "net_income": _s(current.net_income),
            "diluted_eps": _s(current.diluted_eps),
            "operating_cash_flow": _s(current.operating_cash_flow),
            "capex": _s(current.capex),
            "fcf_calc": _s(current.fcf_calc),
            "total_debt": _s(current.total_debt),
            "net_debt": _s(current.netdebt_calc),
            "book_equity": _s(current.book_equity),
            "total_assets": _s(current.total_assets),
            "market_cap": _s(current.market_cap),
            "price": _s(current.price),
            "gross_margin_pct": _s(current.grossmargin_calc),
            "fcf_margin_pct": _s(current.fcfmargin_calc),
            "roe_pct": _s(current.roe_calc),
            "roa_pct": _s(current.roa_calc),
            "pe_ratio": _s(current.pe_calc),
            "pb_ratio": _s(current.pb_calc),
            "ev_ebitda": _s(current.ev_to_ebitda_calc),
            # Bank metrics (null for non-banks)
            "cet1_ratio": _s(current.cet1_ratio),
            "efficiency_ratio": _s(current.efficiency_ratio),
        }
        facts["financials_currency_note"] = (
            "All monetary values above are in the currency field. "
            "Do NOT convert to another currency."
        )

    # YoY history (up to 5 years, fiscal_year + revenue only for context)
    if len(dated) >= 2:
        facts["revenue_history_ccy"] = cur_currency if current else company.currency
        facts["revenue_history"] = [
            {"fiscal_year": s.fiscal_year, "revenue": _s(s.revenue)}
            for s in dated[:5]
        ]

    # Score (deterministic math — labelled explicitly)
    score = db.get(Score, company_id)
    if score:
        facts["scores_note"] = (
            "These scores are deterministic math (Quality 30%, Value 25%, "
            "Growth 25%, Risk 20%, inverted so higher = safer). The AI did not "
            "compute them."
        )
        facts["scores"] = {
            "composite_0_10": _s(score.composite),
            "quality": _s(score.quality),
            "value": _s(score.value),
            "growth": _s(score.growth),
            "risk": _s(score.risk),
            "signal": score.signal,
            "peer_rank": score.peer_rank,
            "peer_set_type": score.peer_set_type,
        }

    # Halal flag (informational)
    halal = db.get(HalalFlag, company_id)
    if halal:
        facts["halal_flag"] = {
            "status": halal.status,
            "note": "Informational AAOIFI-style flag only — not a religious ruling.",
        }

    # TTM
    ttm = db.query(FinancialSnapshotTTM).filter_by(company_id=company_id).first()
    if ttm:
        facts["ttm"] = {
            "roic_pct": _s(ttm.roic),
            "roic_confidence": ttm.roic_confidence,
            "roic_interpretation": ttm.roic_interpretation,
        }

    # Practitioner analytical engines (Master Directive WS3)
    try:
        from app.services.practitioner_engine import get_practitioner_analytics
        practitioner = get_practitioner_analytics(db, company_id)
        if practitioner:
            facts["practitioner_analysis"] = practitioner
    except Exception:  # noqa: BLE001
        pass

    # Profile / description
    profile = db.query(CompanyProfile).filter_by(company_id=company_id).first()
    if profile and profile.description:
        facts["business_description"] = profile.description[:500]  # cap size

    return facts


@router.post("/companies/{company_id}/chat", response_model=ChatResponse)
def company_chat(
    company_id: str,
    req: ChatRequest,
    db: Session = Depends(get_session),
):
    """Fact-grounded AI chat for a single company.

    The model receives ONLY the deterministic DB facts JSON — it cannot access
    the internet, invent numbers, or alter fundamentals.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    last_user = next(
        (m for m in reversed(req.messages) if m.role == "user"), None
    )
    if last_user is None:
        raise HTTPException(status_code=400, detail="No user message found")

    facts = _build_facts(db, company_id)

    # Build conversation for OpenRouter
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"FACTS JSON for {facts.get('name', company_id)}:\n"
                f"```json\n{_safe_json(facts)}\n```\n\n"
                "Please analyse this company given the facts above."
            ),
        },
    ]
    # Include conversation history (skip first user message — already embedded above)
    for m in req.messages[:-1]:
        if m.role in ("user", "assistant"):
            messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": last_user.content})

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return ChatResponse(
            content=(
                "AI narration is unavailable: OPENROUTER_API_KEY is not set. "
                "All financial data above is deterministic and reliable."
            ),
            model_used="none",
        )

    try:
        result = call_openrouter(messages, timeout=45)
        content = result.get("content", "").strip()
        model_used = result.get("model", "unknown")
    except Exception as exc:  # noqa: BLE001
        content = (
            f"AI narration timed out or errored ({exc.__class__.__name__}). "
            "All deterministic financial data remains valid."
        )
        model_used = "error"

    return ChatResponse(
        content=content + "\n\n" + _DISCLAIMER,
        model_used=model_used,
    )


def _safe_json(obj: Any, indent: int = 2) -> str:
    """JSON-serialize with None → null, trimming very large objects."""
    import json
    raw = json.dumps(obj, indent=indent, default=str)
    if len(raw) > 6000:
        raw = raw[:6000] + "\n... (truncated for context length)"
    return raw
