"""Facts builders + narration orchestration (facts -> cache -> OpenRouter)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK
from app.models import Company, FinancialSnapshot, HalalFlag, LlmCache, Score
from app.services import llm
from app.services.scoring import DISCLAIMER as _SCORE_DISCLAIMER  # noqa: F401 (parity)


def _to_float_optional(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric == numeric else None


_f = _to_float_optional


def _round(value: Any, digits: int = 2) -> Any:
    numeric = _to_float_optional(value)
    return None if numeric is None else round(numeric, digits)


def company_facts(db: Session, company_id: str) -> dict | None:
    from app.services.scoring_service import enrich_with_seed, load_universe

    company = db.get(Company, company_id)
    if company is None:
        return None
    entry = next((u for u in load_universe(db) if u["company_id"] == company_id), None)
    if entry is None:
        return None
    enriched = enrich_with_seed(entry["snapshot"], entry.get("seed_snapshot"))
    score = db.get(Score, company_id)
    halal = db.get(HalalFlag, company_id)
    history = sorted(
        (h for h in entry["history"] if h.get("fiscal_year") is not None),
        key=lambda h: h["fiscal_year"],
        reverse=True,
    )
    return {
        "kind": "company",
        "identity": {
            "company_id": company.company_id,
            "name": company.name,
            "currency": company.currency,
            "country": company.country,
            "gics_sector": company.gics_sector,
            "custom_industry_sheet": company.custom_industry_sheet,
        },
        "score": (
            {
                "composite": score.composite,
                "quality": score.quality,
                "value": score.value,
                "growth": score.growth,
                "risk": score.risk,
                "coverage": score.coverage,
                "signal": score.signal,
                "peer_rank": score.peer_rank,
                "peer_n": score.peer_n,
                "as_of_fy": score.as_of_fy,
            }
            if score
            else None
        ),
        "halal_status": halal.status if halal else None,
        "data_gaps": entry and _gaps_of(entry, enriched),
        "latest_snapshot": {
            "revenue": _round(enriched.get("revenue"), 0),
            "net_income": _round(enriched.get("net_income"), 0),
            "diluted_eps": _round(enriched.get("diluted_eps")),
            "fcf_calc": _round(enriched.get("fcf_calc"), 0),
            "roe_calc": _round(enriched.get("roe_calc"), 4),
            "roa_calc": _round(enriched.get("roa_calc"), 4),
            "fcfmargin_calc": _round(enriched.get("fcfmargin_calc"), 4),
            "grossmargin_calc": _round(enriched.get("grossmargin_calc"), 4),
            "pe_calc": _round(enriched.get("pe_calc")),
            "pb_calc": _round(enriched.get("pb_calc")),
            "ev_to_ebitda_calc": _round(enriched.get("ev_to_ebitda_calc")),
            "market_cap": _round(enriched.get("market_cap"), 0),
            "price": _round(enriched.get("price")),
        },
        "history_years_available": [h["fiscal_year"] for h in history],
        "disclaimer": "personal research software, not investment advice",
    }


def _gaps_of(entry: dict, enriched: dict) -> list[str]:
    from app.services.data_gaps import _data_gaps

    return _data_gaps(entry, enriched)


def sector_facts(db: Session, sheet: str, currency: str) -> dict | None:
    from app.services.scoring import build_peer_sets
    from app.services.scoring_service import load_universe

    universe = load_universe(db)
    sheet_l = sheet.lower()
    members = []
    for c in universe:
        m_sheet = (c.get("custom_industry_sheet") or "").lower() == sheet_l
        m_gics = sheet_l.startswith("gics_") and (c.get("gics_sector") or "").lower() == sheet_l.removeprefix("gics_").replace("_", " ")
        if m_sheet or m_gics:
            cur = (c.get("currency") or "").upper()
            if currency == "ALL" or cur == currency:
                score = db.get(Score, c["company_id"])
                members.append(
                    {
                        "company_id": c["company_id"],
                        "name": c.get("name"),
                        "currency": cur,
                        "composite": score.composite if score else None,
                        "signal": score.signal if score else None,
                        "peer_rank": score.peer_rank if score else None,
                    }
                )
    if not members:
        return None
    scored = [m for m in members if m["composite"] is not None]
    scored.sort(key=lambda m: m["composite"], reverse=True)
    currencies = sorted({m["currency"] for m in members if m["currency"]})
    hist: dict[str, int] = {}
    for m in members:
        key = m["signal"] or ("insufficient_data" if m["composite"] is None else "score_missing")
        hist[key] = hist.get(key, 0) + 1
    return {
        "kind": "sector",
        "sheet": sheet,
        "currency_view": currency,
        "companies": len(members),
        "scored": len(scored),
        "currencies": currencies,
        "signal_histogram": hist,
        "top5": [{k: m[k] for k in ("company_id", "name", "currency", "composite", "signal")} for m in scored[:5]],
        "bottom3": [{k: m[k] for k in ("company_id", "name", "currency", "composite", "signal")} for m in scored[-3:]],
        "note": "money amounts are never blended across currencies; this view carries scores/ratios only",
        "disclaimer": "personal research software, not investment advice",
    }


def cache_get(db: Session, kind: str, subject_id: str, score_computed_at: str, model: str) -> str | None:
    row = db.execute(
        select(LlmCache).where(
            LlmCache.kind == kind,
            LlmCache.subject_id == subject_id,
            LlmCache.method_version == "v1",
            LlmCache.score_computed_at == score_computed_at,
            LlmCache.model == model,
        )
    ).scalars().first()
    return row.narration if row else None


def cache_put(db: Session, kind: str, subject_id: str, score_computed_at: str, model: str, narration: str) -> None:
    db.add(
        LlmCache(
            kind=kind,
            subject_id=subject_id,
            method_version="v1",
            score_computed_at=score_computed_at,
            model=model,
            narration=narration,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    db.commit()


def narrate_company(db: Session, company_id: str) -> dict:
    facts = company_facts(db, company_id)
    if facts is None:
        return {"error": "unknown_company"}
    stamp = (db.get(Score, company_id).computed_at.isoformat() if db.get(Score, company_id) else "") or ""
    return _narrate_cached(db, "company", company_id, stamp, facts)


def narrate_sector(db: Session, sheet: str, currency: str) -> dict:
    facts = sector_facts(db, sheet, currency)
    if facts is None:
        return {"error": "unknown_sector"}
    stamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()[:19]
    return _narrate_cached(db, "sector", f"{sheet}:{currency}", stamp, facts)


def _narrate_cached(db: Session, kind: str, subject_id: str, stamp: str, facts: dict) -> dict:
    status = llm.llm_status(OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK)
    if not status["configured"]:
        return {
            "narration_unavailable": True,
            "reason": "OPENROUTER_API_KEY missing or model is not a :free id",
            "facts": facts,
            "banner": "Narration (not the score)",
            "disclaimer": "personal research software, not investment advice",
        }
    cached = cache_get(db, kind, subject_id, stamp, OPENROUTER_MODEL)
    if cached:
        return {"narration": cached, "model": OPENROUTER_MODEL, "cached": True, "facts": facts,
                "banner": "Narration (not the score)", "disclaimer": "personal research software, not investment advice"}
    try:
        out = llm.narrate(facts, OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK)
    except Exception as exc:  # noqa: BLE001 - total provider failure is a 503, not a crash
        return {
            "narration_unavailable": True,
            "reason": str(exc)[:300],
            "facts": facts,
            "banner": "Narration (not the score)",
            "disclaimer": "personal research software, not investment advice",
        }
    cache_put(db, kind, subject_id, stamp, out["model"], out["narration"])
    return {
        "narration": out["narration"],
        "model": out["model"],
        "elapsed_ms": out.get("elapsed_ms"),
        "facts": facts,
        "banner": "Narration (not the score)",
        "disclaimer": "personal research software, not investment advice",
    }


def research_company(db: Session, company_id: str) -> dict:
    """Draft Moat / SWOT from facts JSON. Refuses if model not :free. Caches result."""
    facts = company_facts(db, company_id)
    if facts is None:
        return {"error": "unknown_company"}
    score = db.get(Score, company_id)
    stamp = (score.computed_at.isoformat() if score and score.computed_at else "") or ""

    status = llm.llm_status(OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK)
    if not status["configured"]:
        return {
            "research_unavailable": True,
            "reason": "OPENROUTER_API_KEY missing or model is not a :free id",
            "facts": facts,
            "label": "LLM draft from our facts. Not a 10-K.",
            "disclaimer": "personal research software, not investment advice",
        }

    if not llm.free_latch(OPENROUTER_MODEL):
        return {
            "research_unavailable": True,
            "reason": f"Refusing non-free model: {OPENROUTER_MODEL}",
            "facts": facts,
            "label": "LLM draft from our facts. Not a 10-K.",
            "disclaimer": "personal research software, not investment advice",
        }

    cached = cache_get(db, "swot", company_id, stamp, OPENROUTER_MODEL)
    if cached:
        return {
            "company_id": company_id,
            "swot": cached,
            "model": OPENROUTER_MODEL,
            "cached": True,
            "facts": facts,
            "label": "LLM draft from our facts. Not a 10-K.",
            "disclaimer": "personal research software, not investment advice",
        }

    try:
        out = llm.draft_swot(facts, OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK)
    except Exception as exc:  # noqa: BLE001
        return {
            "research_unavailable": True,
            "reason": str(exc)[:300],
            "facts": facts,
            "label": "LLM draft from our facts. Not a 10-K.",
            "disclaimer": "personal research software, not investment advice",
        }

    cache_put(db, "swot", company_id, stamp, out["model"], out["swot"])
    return {
        "company_id": company_id,
        "swot": out["swot"],
        "model": out["model"],
        "cached": False,
        "elapsed_ms": out.get("elapsed_ms"),
        "facts": facts,
        "label": "LLM draft from our facts. Not a 10-K.",
        "disclaimer": "personal research software, not investment advice",
    }

