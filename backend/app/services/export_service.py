"""Export Service - Structured research memos, batch CSV, JSON dumps, journal exports (Wave 6 Epic 13).

All exports are local, deterministic, currency-tagged, and carry disclaimers.
No external calls, no invented numbers.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot, Score


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _disclaimer() -> str:
    return "Personal research software, not investment advice. AI narration is an interpretation of local facts, not a financial endorsement."


def generate_research_memo(db: Session, company_id: str) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")
    # Latest snapshot
    snap = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == company_id).order_by(FinancialSnapshot.fiscal_year.desc().nullslast())
    ).scalars().first()
    score = db.get(Score, company_id)
    # Valuation floors
    try:
        from app.services.epv_engine import compute_epv
        epv = compute_epv(db, company_id)
    except Exception:
        epv = {"status": "insufficient_data"}
    try:
        from app.services.graham_engine import compute_graham
        graham = compute_graham(db, company_id)
    except Exception:
        graham = {}
    # Forensic
    try:
        from app.services.beneish_engine import compute_beneish_m_score
        from app.services.distress_engine import compute_distress
        beneish = compute_beneish_m_score(db, company_id)
        distress = compute_distress(db, company_id)
    except Exception:
        beneish = {}
        distress = {}

    # Build Markdown
    md_lines = [
        f"# Research Memo - {company.name or company.ticker or company_id} ({company_id})",
        f"Generated: {_now_iso()}",
        f"Currency: {company.currency or snap.currency if snap else 'Not reported in filing'} (native, never converted)",
        "",
        "## Snapshot (Current Metrics, Provenance)",
        f"- Price: {snap.price if snap and snap.price else 'Not reported in filing'} {snap.price_currency if snap and snap.price_currency else company.currency}",
        f"- Revenue: {snap.revenue if snap and snap.revenue else 'Not reported in filing'} ({company.currency}) - source: {snap.source if snap else 'Not reported in filing'} as_of {snap.as_of_date if snap and snap.as_of_date else 'Not reported in filing'}",
        f"- Net Income: {snap.net_income if snap and snap.net_income else 'Not reported in filing'}",
        f"- Total Assets: {snap.total_assets if snap and snap.total_assets else 'Not reported in filing'}",
        f"- Market Cap: {snap.market_cap if snap and snap.market_cap else 'Not reported in filing'}",
        "",
        "## Valuation Floors",
        f"- EPV: {epv.get('epv', 'Not reported in filing')} (reproduction cost proxy {epv.get('reproduction_cost', 'Not reported in filing')}) - {epv.get('status', '')}",
        f"- Graham Floor: {graham.get('graham_number', 'Not reported in filing')} (NCAV {graham.get('ncav_per_share', 'Not reported in filing')})",
        "",
        "## Forensic Flags",
        f"- Beneish M-Score: {beneish.get('m_score', 'Not reported in filing')} zone {beneish.get('zone', 'Not reported in filing')}",
        f"- Altman Z: {distress.get('active_z', 'Not reported in filing')} zone {distress.get('zone', 'Not reported in filing')}",
        "",
        "## Scores (Deterministic v1 - Quality 30% / Value 25% / Growth 25% / Risk 20%)",
        f"- Composite: {score.composite if score else 'Not reported in filing'} ({score.signal if score else 'Not reported in filing'})",
        f"- Quality: {score.quality if score else 'Not reported in filing'}, Value: {score.value if score else 'Not reported in filing'}, Growth: {score.growth if score else 'Not reported in filing'}, Risk: {score.risk if score else 'Not reported in filing'}",
        "",
        f"> {_disclaimer()}",
        "> AI Narration (not the score) - this memo is a structured draft for editing.",
    ]
    markdown = "\n".join(md_lines)
    return {
        "company_id": company_id,
        "markdown": markdown,
        "generated_at": _now_iso(),
        "currency": company.currency,
        "disclaimer": _disclaimer(),
        "method_version": "v1",
    }


def generate_raw_dump(db: Session, company_id: str) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")
    snaps = db.execute(select(FinancialSnapshot).where(FinancialSnapshot.company_id == company_id).order_by(FinancialSnapshot.fiscal_year.desc().nullslast())).scalars().all()
    score = db.get(Score, company_id)
    return {
        "company_id": company_id,
        "company": {"ticker": company.ticker, "name": company.name, "currency": company.currency, "country": company.country, "sector": company.gics_sector},
        "snapshots": [
            {
                "fiscal_year": s.fiscal_year,
                "currency": s.currency,
                "revenue": s.revenue,
                "net_income": s.net_income,
                "total_assets": s.total_assets,
                "price": s.price,
                "source": s.source,
                "as_of_date": s.as_of_date.isoformat() if s.as_of_date else None,
            }
            for s in snaps[:10]
        ],
        "score": {"composite": score.composite if score else None, "signal": score.signal if score else None, "method_version": score.method_version if score else "v1"} if score else None,
        "generated_at": _now_iso(),
        "currency_note": "All money retains native ISO currency per row; no averaging across currencies.",
        "disclaimer": _disclaimer(),
    }


def generate_batch_csv(db: Session, company_ids: list[str]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["company_id", "ticker", "name", "currency", "price", "market_cap", "revenue", "composite", "signal", "source", "disclaimer"])
    for cid in company_ids:
        company = db.get(Company, cid)
        if not company:
            continue
        snap = db.execute(select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid).order_by(FinancialSnapshot.fiscal_year.desc().nullslast())).scalars().first()
        score = db.get(Score, cid)
        w.writerow([
            cid,
            company.ticker or "",
            (company.name or "").replace(",", " "),
            company.currency or (snap.currency if snap else ""),
            snap.price if snap and snap.price else "",
            snap.market_cap if snap and snap.market_cap else "",
            snap.revenue if snap and snap.revenue else "",
            score.composite if score else "",
            score.signal if score else "",
            snap.source if snap and snap.source else "",
            _disclaimer(),
        ])
    # Prepend provenance header comment (for screen CSV compatibility, we use # comments)
    csv_content = out.getvalue()
    header = f"# Batch Export - {len(company_ids)} companies - {_now_iso()}\n# Currency: native ISO per row, never averaged\n# {_disclaimer()}\n"
    return header + csv_content


def generate_journal_export(db: Session, company_id: str | None = None) -> dict[str, Any]:
    from app.models import DecisionJournal
    q = select(DecisionJournal)
    if company_id:
        q = q.where(DecisionJournal.company_id == company_id)
    rows = db.execute(q.order_by(DecisionJournal.created_at.desc())).scalars().all()
    # Calibration stats
    confidences = [r.confidence for r in rows if r.confidence]
    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else None
    return {
        "count": len(rows),
        "avg_confidence": avg_conf,
        "entries": [
            {
                "company_id": r.company_id,
                "confidence": r.confidence,
                "strategy_tag": r.strategy_tag,
                "thesis": r.thesis,
                "kill_conditions": r.kill_conditions,
                "purchase_date": r.purchase_date.isoformat() if r.purchase_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "generated_at": _now_iso(),
        "disclaimer": _disclaimer(),
    }