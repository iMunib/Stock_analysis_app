"""Portfolio & Journal API (Wave 5 Epic 11 + 12)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company, DecisionJournal, PortfolioAccount
from app.services.ids import normalize_company_id
from app.services.portfolio_engine import (
    add_transaction,
    create_account,
    dividend_schedule,
    forensic_heatmap,
    get_holdings,
    list_accounts,
    portfolio_summary,
    rebalance_analysis,
    tax_lots,
)

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


class AccountCreateIn(BaseModel):
    name: str
    account_type: str
    currency: str


class TransactionCreateIn(BaseModel):
    account_id: str
    company_id: str
    txn_type: str
    quantity: float
    price_per_share: float
    txn_date: date
    currency: str | None = None
    fees: float | None = 0
    notes: str | None = None


class JournalCreateIn(BaseModel):
    company_id: str
    account_id: str | None = None
    purchase_date: date | None = None
    confidence: int | None = None
    strategy_tag: str | None = None
    thesis: str | None = None
    kill_conditions: str | None = None


@router.post("/accounts")
def post_account(body: AccountCreateIn, db: Session = Depends(get_db)):
    try:
        acct = create_account(db, body.name, body.account_type, body.currency)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": acct.id, "name": acct.name, "account_type": acct.account_type, "currency": acct.currency, "created_at": acct.created_at.isoformat() if acct.created_at else None}


@router.get("/accounts")
def get_accounts(db: Session = Depends(get_db)):
    accts = list_accounts(db)
    return {"count": len(accts), "accounts": [{"id": a.id, "name": a.name, "account_type": a.account_type, "currency": a.currency} for a in accts]}


@router.post("/transactions")
def post_transaction(body: TransactionCreateIn, db: Session = Depends(get_db)):
    cid = normalize_company_id(body.company_id) or body.company_id
    # Validate account exists etc in engine
    try:
        txn = add_transaction(db, body.account_id, cid, body.txn_type, body.quantity, body.price_per_share, body.txn_date, body.currency, body.fees or 0, body.notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": txn.id, "account_id": txn.account_id, "company_id": txn.company_id, "txn_type": txn.txn_type, "quantity": txn.quantity, "price_per_share": txn.price_per_share, "currency": txn.currency, "txn_date": txn.txn_date.isoformat()}


@router.get("/holdings")
def get_holdings_endpoint(account_id: str | None = None, db: Session = Depends(get_db)):
    holdings = get_holdings(db, account_id)
    return {"count": len(holdings), "holdings": holdings, "disclaimer": "Personal research software, not investment advice. Portfolio tracking and alerts run locally."}


@router.get("/summary")
def get_summary(account_id: str | None = None, db: Session = Depends(get_db)):
    return portfolio_summary(db, account_id)


@router.get("/dividends")
def get_dividends(account_id: str | None = None, db: Session = Depends(get_db)):
    return dividend_schedule(db, account_id)


@router.get("/rebalance")
def get_rebalance(account_id: str | None = None, db: Session = Depends(get_db)):
    return rebalance_analysis(db, account_id)


@router.get("/tax-lots")
def get_tax_lots(account_id: str | None = None, db: Session = Depends(get_db)):
    return tax_lots(db, account_id)


@router.get("/forensic-heatmap")
def get_heatmap(account_id: str | None = None, db: Session = Depends(get_db)):
    return forensic_heatmap(db, account_id)


# Journal endpoints
@router.post("/journal")
def post_journal(body: JournalCreateIn, db: Session = Depends(get_db)):
    cid = normalize_company_id(body.company_id) or body.company_id
    if not db.get(Company, cid):
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    if body.confidence is not None and not (1 <= body.confidence <= 5):
        raise HTTPException(status_code=400, detail="confidence must be 1-5")
    j = DecisionJournal(
        id=str(uuid.uuid4()),
        company_id=cid,
        account_id=body.account_id,
        purchase_date=body.purchase_date,
        confidence=body.confidence,
        strategy_tag=body.strategy_tag,
        thesis=body.thesis,
        kill_conditions=body.kill_conditions,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return {"id": j.id, "company_id": j.company_id, "confidence": j.confidence, "strategy_tag": j.strategy_tag, "created_at": j.created_at.isoformat() if j.created_at else None}


@router.get("/journal")
def get_journal(company_id: str | None = None, db: Session = Depends(get_db)):
    q = select(DecisionJournal)
    if company_id:
        cid = normalize_company_id(company_id) or company_id
        q = q.where(DecisionJournal.company_id == cid)
    rows = db.execute(q.order_by(DecisionJournal.created_at.desc())).scalars().all()
    return {"count": len(rows), "entries": [{"id": r.id, "company_id": r.company_id, "confidence": r.confidence, "strategy_tag": r.strategy_tag, "thesis": r.thesis, "kill_conditions": r.kill_conditions, "purchase_date": r.purchase_date.isoformat() if r.purchase_date else None, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]}


@router.get("/journal/calibration")
def get_calibration(db: Session = Depends(get_db)):
    # Annual reflection & calibration: link confidence to outcomes (simplified)
    rows = db.execute(select(DecisionJournal).order_by(DecisionJournal.created_at.desc())).scalars().all()
    # For each journal, check current composite vs purchase confidence
    items = []
    for r in rows:
        from app.models import Score
        score = db.get(Score, r.company_id)
        items.append({
            "company_id": r.company_id,
            "confidence": r.confidence,
            "strategy_tag": r.strategy_tag,
            "thesis": (r.thesis or "")[:80],
            "current_composite": score.composite if score else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    # Calibration stats: avg confidence vs avg composite
    avg_conf = round(sum(x["confidence"] for x in items if x["confidence"]) / len([x for x in items if x["confidence"]]) , 2) if items and any(x["confidence"] for x in items) else None
    return {"count": len(items), "avg_confidence": avg_conf, "entries": items, "disclaimer": "Personal research software, not investment advice."}
