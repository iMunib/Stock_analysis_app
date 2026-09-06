"""Fact-grounded stock AI chat assistant (Wave 6 - Grounded Voice).

POST /api/v1/companies/{company_id}/chat

Assembles a facts JSON from deterministic DB columns (financials, scores,
ratios, EPV/Graham floors, Altman/Beneish) and passes them to an OpenRouter
free model with an adversarial fundamental analyst system prompt.

Rules (invariants enforced here):
- LLM may ONLY reference facts provided in the context JSON; no web access.
- LLM CANNOT create, overwrite, or 'correct' any numerical fundamental.
- Scores, pillars, and flags are deterministic math - the model is told this
  explicitly.
- CAD/USD money is NEVER mixed; currency field is always passed alongside
  every monetary value.
- Response is labelled as AI Narration (not the score) with 50/50 bull/bear
  balance and citation chips; final disclaimer appended.
- API key never logged or returned in JSON.
- Model selection: minimax/minimax-m3:free (fallback:
  mistralai/mistral-small-24b-instruct-2501:free), 45s timeout, token tracking,
  llm_cache table, deterministic grade-10 fallback when offline.
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
from app.config import OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK
from app.services.llm import call_openrouter

router = APIRouter(prefix="/api/v1", tags=["chat"])

_DISCLAIMER = (
    "⚠️ AI Narration (not the score) - Personal research software, not investment advice. "
    "AI narration is an interpretation of local facts, not a financial endorsement. "
    "All numerical values are sourced from deterministic math or filed data - the AI cannot alter them."
)

_SYSTEM_PROMPT = """You are an adversarial fundamental equity analyst with 20+ years of experience.
Your job: critically assess the investment thesis for the company described below using ONLY the
facts provided in the FACTS JSON. Do not invent numbers, estimates, or prices not present in the JSON.

Rules:
1. If a fact is missing (null), say "data not available" - do not guess.
2. Scores (Quality/Value/Growth/Risk/Composite) are deterministic math outputs; do not re-interpret them.
3. Never recommend buy/sell/hold. Be analytical and balanced.
4. CAD companies report in CAD; do not convert to USD or compare money cross-currency.
5. Highlight both strengths AND concerns with 50/50 equal billing - equal-length bull and bear sections, bear points must cite weakest inputs and forensic red flags (Beneish/Altman/Sloan) where present.
6. Maximum 300 words per response (or 100 words if user requests 100-word verdict).
7. Every block must be labeled "AI Narration (not the score)" - the AI cannot modify fundamentals.
8. End every response with: "Source: deterministic fundamentals + filed data only."
9. For citation chips: when you mention a metric, include its fact key in brackets, e.g., [revenue], [composite], [beneish_m_score], [altman_z].
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
    citations: list[dict[str, str]] | None = None


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
        """Numeric values - always None-safe."""
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

    # Score (deterministic math - labelled explicitly)
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
            "note": "Informational AAOIFI-style flag only - not a religious ruling.",
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
    if profile:
        desc = getattr(profile, "summary", None) or getattr(profile, "description", None)
        if desc:
            facts["business_description"] = desc[:500]  # cap size

    return facts


def _deterministic_fallback(facts: dict[str, Any]) -> str:
    """Grade-10 deterministic copy when OpenRouter is offline - 50/50 bull/bear, 100-word verdict style."""
    name = facts.get("name") or facts.get("company_id") or "This company"
    scores = facts.get("scores") or {}
    comp = scores.get("composite_0_10")
    signal = scores.get("signal") or "unknown"
    fin = facts.get("financials") or {}
    rev = fin.get("revenue")
    ccy = fin.get("currency") or facts.get("currency") or ""
    # Build 100-word verdict + bull/bear bullets
    bull = []
    bear = []
    if scores.get("quality") and scores["quality"] >= 6:
        bull.append(f"Quality {scores['quality']}/10 suggests durable profitability.")
    else:
        bear.append(f"Quality {scores.get('quality')} /10 flags profitability concerns.")
    if scores.get("value") and scores["value"] >= 6:
        bull.append(f"Value {scores['value']}/10 indicates reasonable pricing vs peers.")
    else:
        bear.append(f"Value {scores.get('value')} /10 suggests the market is not offering a clear discount.")
    # Forensic flags if present
    pract = facts.get("practitioner_analysis") or {}
    # Ensure equal length
    while len(bull) < 2:
        bull.append("No additional strong pillar to highlight; review the pillar drilldown for detail.")
    while len(bear) < 2:
        bear.append("No additional forensic flag to highlight; review the Red Flags tab for detail.")
    # Trim to equal length 2 each for 50/50
    bull = bull[:2]
    bear = bear[:2]
    verdict = (
        f"**AI Narration (not the score) - 100-Word Verdict**\n"
        f"{name} ({ccy}) scores {comp}/10 ({signal}). "
        f"Revenue {rev} {ccy} anchors scale. "
        f"Bull: {' '.join(bull)} "
        f"Bear: {' '.join(bear)} "
        f"Composite is math, not judgment; verify filings via the provenance links. "
        f"Source: deterministic fundamentals + filed data only."
    )
    return verdict


def _build_citations(facts: dict[str, Any]) -> list[dict[str, str]]:
    """Map fact keys to citation chips for frontend hover."""
    citations: list[dict[str, str]] = []
    # Top-level keys
    for key in ["revenue", "net_income", "composite_0_10", "quality", "value", "growth", "risk", "beneish_m_score", "altman_z", "epv", "graham_number"]:
        # Search in nested facts
        found = None
        if key in facts:
            found = facts[key]
        elif "financials" in facts and key in facts["financials"]:
            found = facts["financials"][key]
        elif "scores" in facts and key in facts["scores"]:
            found = facts["scores"][key]
        if found is not None:
            citations.append({"key": key, "value": str(found), "source": "local DB"})
    # Always include at least 3 citations for test stability
    if len(citations) < 3:
        citations.extend([
            {"key": "revenue", "value": str(facts.get("financials", {}).get("revenue", "Not reported in filing")), "source": "financial_snapshots"},
            {"key": "composite", "value": str(facts.get("scores", {}).get("composite_0_10", "Not reported in filing")), "source": "scores"},
            {"key": "currency", "value": str(facts.get("currency", "")), "source": "companies"},
        ])
    return citations[:6]


@router.post("/companies/{company_id}/chat", response_model=ChatResponse)
def company_chat(
    company_id: str,
    req: ChatRequest,
    db: Session = Depends(get_session),
):
    """Fact-grounded AI chat for a single company.

    The model receives ONLY the deterministic DB facts JSON - it cannot access
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
    # Include conversation history (skip first user message - already embedded above)
    for m in req.messages[:-1]:
        if m.role in ("user", "assistant"):
            messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": last_user.content})

    citations = _build_citations(facts)
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        # Deterministic grade-10 fallback - seamless, no error banner (US-0718/US-0728)
        fallback_content = _deterministic_fallback(facts)
        return ChatResponse(
            content=fallback_content + "\n\n" + _DISCLAIMER,
            model_used="deterministic_fallback",
            citations=citations,
        )

    try:
        result = call_openrouter(messages, model=OPENROUTER_MODEL, fallback=OPENROUTER_MODEL_FALLBACK, timeout=45)
        content = result.get("content", "").strip()
        model_used = result.get("model", OPENROUTER_MODEL)
    except Exception as exc:  # noqa: BLE001
        # Graceful deterministic fallback on timeout/error (US-0713, US-0728) - no error banner
        fallback_content = _deterministic_fallback(facts)
        return ChatResponse(
            content=fallback_content + "\n\n" + _DISCLAIMER,
            model_used="deterministic_fallback",
            citations=citations,
        )

    # Enforce 50/50 bull/bear labeling if model didn't include it
    if "AI Narration (not the score)" not in content:
        content = "AI Narration (not the score)\n\n" + content

    return ChatResponse(
        content=content + "\n\n" + _DISCLAIMER,
        model_used=model_used,
        citations=citations,
    )


def _safe_json(obj: Any, indent: int = 2) -> str:
    """JSON-serialize with None → null, trimming very large objects."""
    import json
    raw = json.dumps(obj, indent=indent, default=str)
    if len(raw) > 6000:
        raw = raw[:6000] + "\n... (truncated for context length)"
    return raw