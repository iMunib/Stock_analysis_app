"""Job queue service (SQLite-backed). enqueue / get / list / claim.

Claim pattern: UPDATE jobs SET status='running' WHERE id = (oldest queued) —
one at a time, safe under WAL with busy_timeout. No Redis, no Celery.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Job

VALID_KINDS = {"backfill", "ingest", "recompute", "refresh_universe"}
ACTIVE_STATUSES = {"queued", "running"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def enqueue(
    db: Session,
    kind: str,
    payload: dict[str, Any] | None = None,
    progress_total: int = 0,
    company_id: str | None = None,
) -> Job:
    if kind not in VALID_KINDS:
        raise ValueError(f"unsupported job kind: {kind}")
    job = Job(
        id=uuid.uuid4().hex,
        kind=kind,
        status="queued",
        step="queued",
        message="Job queued",
        company_id=company_id,
        payload_json=json.dumps(payload or {}),
        progress_total=max(0, int(progress_total)),
        created_at=_utcnow(),
    )
    db.add(job)
    db.commit()
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    return db.get(Job, job_id)


def list_jobs(db: Session, limit: int = 20) -> list[Job]:
    stmt = select(Job).order_by(Job.created_at.desc(), Job.id).limit(max(1, min(100, limit)))
    return list(db.execute(stmt).scalars().all())


def has_active(db: Session, kind: str) -> bool:
    stmt = select(Job.id).where(Job.kind == kind, Job.status.in_(ACTIVE_STATUSES)).limit(1)
    return db.execute(stmt).scalar_one_or_none() is not None


def claim_oldest_queued(db: Session) -> Job | None:
    """Atomically claim the oldest queued job (queued -> running)."""
    job_id = db.execute(
        select(Job.id)
        .where(Job.status == "queued")
        .order_by(Job.created_at.asc(), Job.id.asc())
        .limit(1)
    ).scalar_one_or_none()
    if job_id is None:
        return None
    claimed = db.execute(
        update(Job)
        .where(Job.id == job_id, Job.status == "queued")
        .values(status="running", started_at=_utcnow())
    )
    if claimed.rowcount == 0:
        db.rollback()
        return None
    db.commit()
    return db.get(Job, job_id)


def set_step(
    db: Session,
    job_id: str,
    step: str,
    message: str | None = None,
    company_id: str | None = None,
    error_code: str | None = None,
) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.step = step
    if message is not None:
        job.message = message
    if company_id is not None:
        job.company_id = company_id
    if error_code is not None:
        job.error_code = error_code
    db.commit()


def fail_job(
    db: Session,
    job_id: str,
    error_code: str,
    message: str,
    step: str = "failed",
    company_id: str | None = None,
) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.status = "failed"
    job.step = step
    job.error_code = error_code
    job.message = message
    job.error = f"{error_code}: {message}"
    if company_id is not None:
        job.company_id = company_id
    job.finished_at = _utcnow()
    db.commit()


def set_progress(db: Session, job_id: str, done: int, total: int | None = None) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.progress_done = max(0, int(done))
    if total is not None:
        job.progress_total = max(0, int(total))
    db.commit()


def finish(
    db: Session,
    job_id: str,
    ok: bool,
    error: str | None = None,
    provider_stats: dict | None = None,
    message: str | None = None,
    error_code: str | None = None,
) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.status = "succeeded" if ok else "failed"
    if ok and job.step != "failed":
        job.step = "done"
    elif not ok:
        job.step = "failed"
    if message is not None:
        job.message = message
    if error_code is not None:
        job.error_code = error_code
    job.error = error
    if provider_stats is not None:
        job.provider_stats_json = json.dumps(provider_stats)
    job.finished_at = _utcnow()
    db.commit()


def payload_of(job: Job) -> dict[str, Any]:
    try:
        return json.loads(job.payload_json or "{}")
    except json.JSONDecodeError:
        return {}


def provider_stats_of(job: Job) -> dict[str, Any]:
    try:
        return json.loads(job.provider_stats_json or "{}")
    except json.JSONDecodeError:
        return {}


def job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "step": job.step,
        "message": job.message,
        "company_id": job.company_id,
        "error_code": job.error_code,
        "payload": payload_of(job),
        "progress_done": job.progress_done,
        "progress_total": job.progress_total,
        "error": job.error,
        "provider_stats": provider_stats_of(job),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
