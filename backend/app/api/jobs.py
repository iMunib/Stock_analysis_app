"""Phase 6A async job routes. Backfill becomes non-blocking (202 + poll).

BREAKING vs Phase 2: POST /api/v1/jobs/backfill now enqueues and returns 202
{job_id, status: "queued"} instead of running inline. Poll GET /api/v1/jobs/{id}.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session
from app.services import jobs as jobsvc
from app.services.scoring import DISCLAIMER, METHOD_VERSION

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class BackfillBody(BaseModel):
    mode: str = Field(default="sample", pattern="^(sample|all|company)$")
    limit: int = Field(default=5, ge=1, le=750)
    refresh: bool = False
    recompute: bool = False  # opt-in: scores recompute after a successful backfill
    company_id: str | None = None  # Trust sprint C: single-company "Refresh Price & Recompute"


@router.post("/backfill", status_code=202, description="Enqueue a backfill job (async, 202 + poll). Only one backfill may be queued/running at a time.")
def enqueue_backfill(body: BackfillBody, db: Session = Depends(get_session)):
    if jobsvc.has_active(db, "backfill"):
        raise HTTPException(status_code=409, detail="a backfill job is already queued or running — poll GET /api/v1/jobs")
    job = jobsvc.enqueue(
        db,
        "backfill",
        payload={
            "mode": body.mode,
            "limit": body.limit,
            "refresh": body.refresh,
            "recompute": body.recompute,
            "company_id": body.company_id,
        },
    )
    return {"job_id": job.id, "status": job.status, "kind": job.kind, "method_version": METHOD_VERSION, "disclaimer": DISCLAIMER}


@router.get("/{job_id}", description="Poll one job: status, progress, provider_stats, error.")
def get_job(job_id: str, db: Session = Depends(get_session)):
    job = jobsvc.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"unknown job_id: {job_id}")
    return jobsvc.job_to_dict(job) | {"method_version": METHOD_VERSION, "disclaimer": DISCLAIMER}


@router.get("", description="Recent jobs, newest first.")
def recent_jobs(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_session)):
    return {
        "count": 0,
        "items": [jobsvc.job_to_dict(j) for j in jobsvc.list_jobs(db, limit=limit)],
        "method_version": METHOD_VERSION,
        "disclaimer": DISCLAIMER,
    }
