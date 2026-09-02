"""Phase 10 Stage A/B: LLM status, narration, refresh job. Free models only."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK
from app.db import get_session
from app.services import jobs as jobsvc
from app.services import narration as narrsvc
from app.services.llm import llm_status
from app.services.scoring import DISCLAIMER, METHOD_VERSION

router = APIRouter(prefix="/api/v1", tags=["phase10"])


@router.get("/llm/status", description="Narration availability. Never returns the API key.")
def get_llm_status():
    return llm_status(OPENROUTER_MODEL, OPENROUTER_MODEL_FALLBACK) | {
        "method_version": METHOD_VERSION,
        "disclaimer": DISCLAIMER,
    }


@router.post("/companies/{company_id}/narrate")
def company_narrate(company_id: str, db: Session = Depends(get_session)):
    out = narrsvc.narrate_company(db, company_id)
    if out.get("error") == "unknown_company":
        raise HTTPException(status_code=404, detail=f"unknown company_id: {company_id}")
    if out.get("narration_unavailable"):
        raise HTTPException(status_code=503, detail=out)
    return out


@router.post("/sectors/{sheet}/narrate")
def sector_narrate(
    sheet: str,
    currency: str = Query(default="ALL", pattern="^(ALL|USD|CAD)$"),
    db: Session = Depends(get_session),
):
    out = narrsvc.narrate_sector(db, sheet, currency)
    if out.get("error") == "unknown_sector":
        raise HTTPException(status_code=404, detail=f"unknown sector sheet: {sheet}")
    if out.get("narration_unavailable"):
        raise HTTPException(status_code=503, detail=out)
    return out


class RefreshBody(BaseModel):
    mode: str = Field(default="sample", pattern="^(sample|all)$")
    limit: int = Field(default=5, ge=1, le=750)


@router.post("/jobs/refresh", status_code=202, description="Enqueue refresh_universe: backfill then recompute scores. 409 if one is active.")
def enqueue_refresh(body: RefreshBody, db: Session = Depends(get_session)):
    if jobsvc.has_active(db, "refresh_universe"):
        raise HTTPException(status_code=409, detail="a refresh_universe job is already queued or running")
    job = jobsvc.enqueue(db, "refresh_universe", payload={"mode": body.mode, "limit": body.limit, "recompute": True})
    return {"job_id": job.id, "status": job.status, "kind": job.kind, "method_version": METHOD_VERSION, "disclaimer": DISCLAIMER}
