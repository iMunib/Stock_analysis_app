"""Wave 2 Router: Watchlist 'What Changed' Digest & Morning Brief Engine.

Provides REST endpoints for Wave 2 Epic 5:
- GET /api/v1/watchlist/digest (US-0084, US-0092, US-0351, US-0367, US-0377)
- POST /api/v1/watchlist/digest (accepts watched company IDs and client-configured alerts)
- GET /api/v1/watchlist/deltas (programmatic feed of historical pillar/score deltas)
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.services.watchlist_digest import compute_watchlist_digest

from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1", tags=["wave2_watchlist"])


def _cache(response: Response) -> None:
    response.headers["Cache-Control"] = "private, max-age=60"


class WatchlistDigestIn(BaseModel):
    ids: list[str] | None = None
    company_ids: list[str] | None = None
    alerts: list[dict[str, Any]] | None = None


@router.get(
    "/watchlist/digest",
    summary="1-page morning brief synthesizing watchlist score shifts, signal re-ratings, fresh filings, and post-earnings actuals (US-0351, US-0084, US-0092, US-0367, US-0377)",
)
def get_watchlist_digest_endpoint(
    response: Response,
    ids: str | None = Query(default=None, description="Comma-separated company IDs (e.g. US:AAPL:US,CA:SHOP:TSX)"),
    company_ids: str | None = Query(default=None, description="Comma-separated company IDs (alternative alias)"),
    db: Session = Depends(get_session),
) -> dict[str, Any]:
    _cache(response)
    raw_ids = company_ids or ids
    id_list = [x.strip() for x in raw_ids.split(",") if x.strip()] if raw_ids else None
    return compute_watchlist_digest(db, company_ids=id_list)


@router.post(
    "/watchlist/digest",
    summary="Post company IDs and custom alert rules to get personalized morning watchlist digest",
)
def post_watchlist_digest_endpoint(
    body: WatchlistDigestIn,
    response: Response,
    db: Session = Depends(get_session),
) -> dict[str, Any]:
    _cache(response)
    target_ids = body.company_ids if body.company_ids is not None else body.ids
    return compute_watchlist_digest(db, company_ids=target_ids, client_alerts=body.alerts)


@router.get(
    "/watchlist/deltas",
    summary="Historical pillar and score deltas feed for watched companies (US-0092)",
)
def get_watchlist_deltas_endpoint(
    response: Response,
    ids: str | None = Query(default=None, description="Comma-separated company IDs"),
    company_ids: str | None = Query(default=None, description="Comma-separated company IDs (alternative alias)"),
    db: Session = Depends(get_session),
) -> dict[str, Any]:
    _cache(response)
    raw_ids = company_ids or ids
    id_list = [x.strip() for x in raw_ids.split(",") if x.strip()] if raw_ids else None
    digest = compute_watchlist_digest(db, company_ids=id_list)
    deltas = []
    for it in digest.get("items", []):
        p_deltas = it.get("pillar_deltas", {})
        pe = it.get("post_earnings", {})
        is_cad = (it.get("currency") or "").upper() == "CAD"
        ff = it.get("fresh_filing", {})
        f_url = ff.get("filing_url")
        deltas.append({
            "company_id": it["company_id"],
            "ticker": it["ticker"],
            "name": it["name"],
            "currency": it["currency"],
            "current_composite": it["current_composite"],
            "prior_composite": it["prior_composite"],
            "composite_delta": it["composite_delta"],
            "delta_composite": it["composite_delta"],
            "current_signal": it["current_signal"],
            "prior_signal": it["prior_signal"],
            "signal_rerated": it["signal_rerated"],
            "is_rerated": it["signal_rerated"],
            "rerating_description": it["rerating_description"],
            "pillar_deltas": {
                "quality": p_deltas.get("quality", {}).get("delta") if isinstance(p_deltas.get("quality"), dict) else p_deltas.get("quality"),
                "value": p_deltas.get("value", {}).get("delta") if isinstance(p_deltas.get("value"), dict) else p_deltas.get("value"),
                "growth": p_deltas.get("growth", {}).get("delta") if isinstance(p_deltas.get("growth"), dict) else p_deltas.get("growth"),
                "risk": p_deltas.get("risk", {}).get("delta") if isinstance(p_deltas.get("risk"), dict) else p_deltas.get("risk"),
            },
            "earnings_post_actual": {
                "fiscal_year": pe.get("fiscal_year"),
                "revenue_actual": pe.get("revenue"),
                "prior_year_revenue": pe.get("prior_revenue"),
                "revenue_growth_pct": pe.get("revenue_growth_pct"),
                "net_income_actual": pe.get("net_income"),
                "prior_year_net_income": pe.get("prior_net_income"),
            } if pe.get("has_recent_earnings") else None,
            "filing_links": {
                "sedar_plus": f_url if is_cad else None,
                "edgar": f_url if not is_cad else None,
            },
            "as_of": digest.get("summary", {}).get("as_of_date", ""),
        })
    return {
        "as_of_date": digest.get("summary", {}).get("as_of_date"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(deltas),
        "total": len(deltas),
        "deltas": deltas,
    }
