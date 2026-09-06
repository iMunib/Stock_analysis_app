"""Alerts API (Wave 5 Epic 6)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AlertRule, Company
from app.services.ids import normalize_company_id
from app.services.alerts_daemon import evaluate_rules, get_calendar, heartbeat

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


class AlertRuleCreateIn(BaseModel):
    company_id: str | None = None
    rule_type: str
    params: dict[str, Any] | None = None
    enabled: bool | None = True


@router.post("/rules")
def post_rule(body: AlertRuleCreateIn, db: Session = Depends(get_db)):
    cid = None
    if body.company_id:
        cid = normalize_company_id(body.company_id) or body.company_id
        if not db.get(Company, cid):
            raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    rule = AlertRule(
        id=str(uuid.uuid4()),
        company_id=cid,
        rule_type=body.rule_type,
        params_json=body.params or {},
        enabled=body.enabled if body.enabled is not None else True,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "company_id": rule.company_id, "rule_type": rule.rule_type, "params": rule.params_json, "enabled": rule.enabled}


@router.get("/rules")
def get_rules(company_id: str | None = None, db: Session = Depends(get_db)):
    q = select(AlertRule)
    if company_id:
        cid = normalize_company_id(company_id) or company_id
        q = q.where(AlertRule.company_id == cid)
    rows = db.execute(q.order_by(AlertRule.created_at.desc())).scalars().all()
    return {"count": len(rows), "rules": [{"id": r.id, "company_id": r.company_id, "rule_type": r.rule_type, "params": r.params_json, "enabled": r.enabled, "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None} for r in rows]}


@router.post("/evaluate")
def post_evaluate(company_ids: str | None = None, db: Session = Depends(get_db)):
    ids = [normalize_company_id(c.strip()) or c.strip() for c in company_ids.split(",") if c.strip()] if company_ids else None
    events = evaluate_rules(db, ids)
    return {"count": len(events), "events": events, "disclaimer": "Personal research software, not investment advice. Portfolio tracking and alerts run locally."}


@router.get("/evaluate")
def get_evaluate(company_ids: str | None = None, db: Session = Depends(get_db)):
    ids = [normalize_company_id(c.strip()) or c.strip() for c in company_ids.split(",") if c.strip()] if company_ids else None
    events = evaluate_rules(db, ids)
    return {"count": len(events), "events": events}


@router.get("/calendar")
def get_calendar_endpoint(days_ahead: int = 30, db: Session = Depends(get_db)):
    items = get_calendar(db, days_ahead)
    return {"count": len(items), "items": items}


@router.get("/heartbeat")
def get_heartbeat():
    return heartbeat()


@router.get("/events")
def get_events(limit: int = 20, db: Session = Depends(get_db)):
    # For MVP, events are ephemeral - we just re-evaluate and return last 20
    events = evaluate_rules(db)
    return {"count": len(events), "events": events[:limit]}