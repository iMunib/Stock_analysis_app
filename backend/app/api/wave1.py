"""Wave 1 Router: Pillar Drilldown, Ratio Inspector, Coverage Health & Factor Evidence.

Provides REST endpoints for Wave 1 Epics 1-4:
- GET /api/v1/companies/{company_id}/pillar-drilldown (US-0051, US-0052, US-0056, US-0064, US-0067, US-0080, US-0083, US-0100)
- GET /api/v1/companies/{company_id}/ratios/{ratio_name}/inspect (US-0460, US-0453, US-0481)
- GET /api/v1/companies/{company_id}/bear-case (US-0074, US-0705, US-0725)
- GET /api/v1/coverage/health (US-0466)
- GET /api/v1/factors/evidence (US-0060, US-0063, US-0676, US-0905, US-0919, US-0947)
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Company
from app.services.pillar_drilldown import get_pillar_drilldown
from app.services.ratio_inspector import inspect_ratio
from app.services.coverage_health import compute_universe_health
from app.services.bear_case_engine import generate_bear_case
from app.services.factor_evidence import get_factor_evidence_catalog

router = APIRouter(prefix="/api/v1", tags=["wave1"])


def _cache(response: Response) -> None:
    response.headers["Cache-Control"] = "private, max-age=60"


@router.get(
    "/companies/{company_id}/pillar-drilldown",
    summary="Exact inputs, formula, weight breakdown, and peer medians for 4 pillars (US-0051, US-0056, US-0067, US-0080, US-0100)",
)
def pillar_drilldown_endpoint(company_id: str, response: Response, db: Session = Depends(get_session)) -> dict[str, Any]:
    _cache(response)
    try:
        return get_pillar_drilldown(db, company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as exc:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "message": f"Pillar drilldown unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:400],
        }


@router.get(
    "/companies/{company_id}/ratios/{ratio_name}/inspect",
    summary="Inspect ratio calculation with numerator, denominator, as-of dates, and SEC link (US-0460, US-0453)",
)
def ratio_inspect_endpoint(company_id: str, ratio_name: str, response: Response, db: Session = Depends(get_session)) -> dict[str, Any]:
    _cache(response)
    try:
        return inspect_ratio(db, company_id, ratio_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as exc:
        return {
            "company_id": company_id,
            "ratio_name": ratio_name,
            "status": "insufficient_data",
            "message": f"Ratio inspection unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:400],
        }


@router.get(
    "/companies/{company_id}/bear-case",
    summary="Auto-synthesized bear case, pre-mortem prompt, and bottom percentiles (US-0074, US-0705, US-0725)",
)
def bear_case_endpoint(company_id: str, response: Response, db: Session = Depends(get_session)) -> dict[str, Any]:
    _cache(response)
    try:
        return generate_bear_case(db, company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as exc:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "message": f"Bear case unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:400],
        }


@router.get(
    "/coverage/health",
    summary="Universe data coverage & health audit matrix across 720 constituents (US-0466)",
)
def coverage_health_endpoint(response: Response, db: Session = Depends(get_session)) -> dict[str, Any]:
    _cache(response)
    try:
        return compute_universe_health(db)
    except Exception as exc:
        return {
            "status": "insufficient_data",
            "message": f"Coverage health unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:400],
        }


@router.get(
    "/factors/evidence",
    summary="Factor historical behavior, decay dates, regime notes, and Bessembinder base rates (US-0060, US-0063, US-0676, US-0905, US-0919, US-0947)",
)
def factor_evidence_endpoint(response: Response) -> dict[str, Any]:
    _cache(response)
    return get_factor_evidence_catalog()
