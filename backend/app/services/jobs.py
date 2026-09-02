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

VALID_KINDS = {"backfill", "ingest", "recompute"}
ACTIVE_STATUSES = {"queued", "running"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def enqueue(db: Session, kind: str, payload: dict[str, Any] | None = None, progress_total: int = 0) -> Job:
    if kind not in VALID_KINDS:
        raise ValueError(f"unsupported job kind: {kind}")
    job = Job(
        id=uuid.uuid4().hex,
        kind=kind,
        status="queued",
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


def set_progress(db: Session, job_id: str, done: int, total: int | None = None) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.progress_done = max(0, int(done))
    if total is not None:
        job.progress_total = max(0, int(total))
    db.commit()


def finish(db: Session, job_id: str, ok: bool, error: str | None = None, provider_stats: dict | None = None) -> None:
    job = db.get(Job, job_id)
    if job is None:
        return
    job.status = "succeeded" if ok else "failed"
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
        "payload": payload_of(job),
        "progress_done": job.progress_done,
        "progress_total": job.progress_total,
        "error": job.error,
        "provider_stats": provider_stats_of(job),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
