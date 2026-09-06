"""Restatements & Trajectory API (Wave 3 Epic 9).

Endpoints:
- GET /api/v1/companies/{id}/restatements  - as-filed vs as-restated per FY (US-0245/US-0161)
- GET /api/v1/companies/{id}/trajectory   - 10-year synchronized Revenue/Margin/FCF trajectory (US-0152/US-0156)
- GET /api/v1/companies/{id}/working-capital - DSO/DIO/DPO + CCC series (US-0157/US-0228)
- GET /api/v1/companies/{id}/goodwill-risk - goodwill vs tangible strip (US-0168/US-0027)
- GET /api/v1/companies/{id}/dilution     - share count history with SBC separation (US-0158)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company, FinancialSnapshot, FinancialStatement

router = APIRouter(prefix="/api/v1", tags=["restatements"])


def _snap_source(s):
    return s.source or ""


@router.get("/companies/{company_id}/restatements")
def get_restatements(company_id: str, db: Session = Depends(get_db)):
    from app.services.ids import normalize_company_id

    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid, FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    stmts = db.execute(
        select(FinancialStatement).where(FinancialStatement.company_id == cid, FinancialStatement.period_type == "FY").order_by(FinancialStatement.fiscal_year.asc().nullslast())
    ).scalars().all()
    stmt_by_fy = {st.fiscal_year: st for st in stmts if st.fiscal_year is not None}

    items = []
    for snap in snaps:
        fy = snap.fiscal_year
        if fy is None:
            continue
        stmt = stmt_by_fy.get(fy)
        # as_filed = earliest snapshot (snapshot table) ; as_restated = statement table or latest snapshot if differs
        as_filed = {
            "revenue": snap.revenue,
            "net_income": snap.net_income,
            "gross_profit": snap.gross_profit,
            "total_assets": snap.total_assets,
            "source": _snap_source(snap),
        }
        as_restated = None
        delta = {}
        if stmt is not None:
            as_restated = {
                "revenue": stmt.revenue,
                "net_income": stmt.net_income,
                "gross_profit": stmt.gross_profit,
                "total_assets": stmt.total_assets,
                "source": stmt.source or "",
            }
            # compute deltas where both present
            for k in ("revenue", "net_income", "gross_profit", "total_assets"):
                fv = as_filed.get(k)
                rv = as_restated.get(k)
                if fv is not None and rv is not None and fv != 0:
                    delta[k] = round((rv - fv) / abs(fv) * 100.0, 2) if fv != 0 else None
                else:
                    delta[k] = None
            has_restatement = any(fv != rv for fv, rv in zip(as_filed.values(), as_restated.values()) if isinstance(fv, (int, float)) and isinstance(rv, (int, float)))
        else:
            has_restatement = False

        items.append({
            "fiscal_year": fy,
            "as_filed": as_filed,
            "as_restated": as_restated,
            "delta_pct": delta,
            "has_restatement": has_restatement,
            "provenance": {"filed_source": _snap_source(snap), "restated_source": stmt.source if stmt else None},
        })

    return {
        "company_id": cid,
        "count": len(items),
        "items": items[-10:],
        "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
    }


@router.get("/companies/{company_id}/trajectory")
def get_trajectory(company_id: str, db: Session = Depends(get_db)):
    from app.services.ids import normalize_company_id

    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid, FinancialSnapshot.fiscal_year.is_not(None), FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    fyears = [s for s in snaps if s.fiscal_year is not None][-10:]
    points = []
    prev_rev = None
    prev_gm = None
    prev_om = None
    prev_fcf = None
    for s in fyears:
        rev = s.revenue
        gp = s.gross_profit
        ebit = s.ebit
        fcf = s.fcf_calc
        gm = (gp / rev) if (gp is not None and rev not in (None, 0)) else None
        om = (ebit / rev) if (ebit is not None and rev not in (None, 0)) else None
        # Inflection where YoY delta >15% for revenue/FCF or >5pp for margins
        inflections = []
        if prev_rev is not None and rev is not None and prev_rev != 0:
            d = (rev - prev_rev) / abs(prev_rev)
            if abs(d) > 0.15:
                inflections.append(f"revenue_{'surge' if d>0 else 'contraction'}")
        if prev_gm is not None and gm is not None:
            if abs(gm - prev_gm) > 0.05:
                inflections.append("gross_margin_inflection")
        if prev_om is not None and om is not None:
            if abs(om - prev_om) > 0.05:
                inflections.append("operating_margin_inflection")
        if prev_fcf is not None and fcf is not None and prev_fcf not in (None, 0):
            if abs((fcf - prev_fcf) / abs(prev_fcf)) > 0.15:
                inflections.append("fcf_inflection")
        points.append({
            "fiscal_year": s.fiscal_year,
            "revenue": rev,
            "gross_margin": round(gm, 4) if gm is not None else None,
            "operating_margin": round(om, 4) if om is not None else None,
            "fcf": fcf,
            "inflections": inflections,
            "currency": s.currency or company.currency,
        })
        prev_rev, prev_gm, prev_om, prev_fcf = rev, gm, om, fcf

    return {"company_id": cid, "count": len(points), "points": points, "currency": company.currency}


@router.get("/companies/{company_id}/working-capital")
def get_working_capital(company_id: str, db: Session = Depends(get_db)):
    from app.services.ids import normalize_company_id
    from app.services.shenanigans_engine import compute_ccc_series

    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid, FinancialSnapshot.period_type == "FY")
    ).scalars().all()
    stmts = db.execute(
        select(FinancialStatement).where(FinancialStatement.company_id == cid, FinancialStatement.period_type == "FY")
    ).scalars().all()
    result = compute_ccc_series(list(snaps), list(stmts))
    result["company_id"] = cid
    result["disclaimer"] = "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings."
    return result


@router.get("/companies/{company_id}/goodwill-risk")
def get_goodwill_risk(company_id: str, db: Session = Depends(get_db)):
    from app.services.ids import normalize_company_id
    from app.services.shenanigans_engine import analyze_goodwill, analyze_serial_acquirer

    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid, FinancialSnapshot.period_type == "FY")
    ).scalars().all()
    gw = analyze_goodwill(list(snaps))
    serial = analyze_serial_acquirer(list(snaps))
    # Build trend strip last 5 FY
    rows = sorted([s for s in snaps if s.fiscal_year is not None and s.total_assets is not None], key=lambda s: s.fiscal_year)
    strip = []
    for s in rows[-5:]:
        ta = float(s.total_assets or 0)
        proxy = max(0.0, ta - float(s.book_equity or 0) - float(s.cash_st_investments or 0) - float(getattr(s, "accounts_receivable", 0) or 0) - float(getattr(s, "inventory", 0) or 0) - float(getattr(s, "ppe_net", 0) or 0))
        ratio = proxy / ta if ta else None
        strip.append({"fiscal_year": s.fiscal_year, "proxy_intangible_ratio": round(ratio, 3) if ratio is not None else None, "total_assets": s.total_assets})
    return {
        "company_id": cid,
        "goodwill": gw,
        "serial_acquirer": serial,
        "strip": strip,
        "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
    }


@router.get("/companies/{company_id}/dilution")
def get_dilution(company_id: str, db: Session = Depends(get_db)):
    from app.services.ids import normalize_company_id

    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid, FinancialSnapshot.fiscal_year.is_not(None), FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    series = []
    prev_shares = None
    for s in snaps[-10:]:
        shares = s.shares_snapshot
        sbc = getattr(s, "stock_based_compensation", None)
        if shares is None:
            continue
        entry = {"fiscal_year": s.fiscal_year, "shares": shares, "sbc": sbc}
        if prev_shares is not None:
            delta = shares - prev_shares
            delta_pct = delta / prev_shares * 100.0 if prev_shares else None
            # Annotate buyback vs issuance
            if delta < 0:
                entry["annotation"] = "net_buyback"
            elif delta > 0:
                entry["annotation"] = "issuance"
            else:
                entry["annotation"] = "flat"
            entry["delta"] = delta
            entry["delta_pct"] = round(delta_pct, 2) if delta_pct is not None else None
            # SBC separation
            if sbc is not None and delta_pct is not None:
                # SBC dilution proxied as sbc / market_cap if available else not computed
                entry["sbc_dilution_note"] = "SBC field present - separate from organic buyback where buyback net of SBC is tracked via ShareholderYieldBar."
        series.append(entry)
        prev_shares = shares
    return {"company_id": cid, "count": len(series), "series": series, "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings."}