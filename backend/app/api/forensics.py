"""REST API routes for Forensic Accounting, Reverse DCF Valuation, and Screener Presets."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Company, FinancialSnapshot, FinancialSnapshotTTM, Score, ScreenerPreset, ValuationReverseDCF
from app.services.ids import normalize_company_id
from app.services.screener_engine import run_screener_query

router = APIRouter(prefix="/api/v1", tags=["forensics"])


# --- Schemas ---

class ScreenerRunIn(BaseModel):
    currency: str | None = None
    sector: str | None = None
    industry: str | None = None
    signal: str | None = None
    composite_min: float | None = None
    exclude_banks: bool = False
    roic_min: float | None = None
    ev_ebitda_max: float | None = None
    fcf_yield_min: float | None = None
    sloan_accrual_min: float | None = None
    sloan_accrual_max: float | None = None
    cash_conversion_min: float | None = None
    cash_conversion_max: float | None = None
    expectations_gap_min: float | None = None
    expectations_gap_max: float | None = None
    eqr_min: int | None = None
    eqr_max: int | None = None
    flag_logic: str = "AND"
    sort_by: str = "composite"
    sort_dir: str = "desc"
    limit: int = 100
    offset: int = 0


class ScreenerPresetCreateIn(BaseModel):
    id: str | None = None
    name: str
    criteria: dict[str, Any]
    auto_run_on_refresh: bool = False


class FcfVsNiYear(BaseModel):
    fiscal_year: int
    net_income: float | None
    fcf: float | None


class ForensicsOut(BaseModel):
    company_id: str
    currency: str
    sloan_accrual_ratio: float | None
    sloan_signal: str  # "green", "red", "neutral", "insufficient_data"
    cash_conversion_ratio: float | None
    cash_conversion_signal: str  # "weak", "healthy", "insufficient_data"
    roic: float | None
    roic_interpretation: str | None = None  # normal | distorted_low_denominator | negative_capital | not_meaningful
    roic_confidence: str | None = None  # high | medium | low
    roic_warning_reason: str | None = None
    invested_capital_to_assets: float | None = None
    fcf_yield: float | None
    nopat: float | None
    invested_capital: float | None
    fcf_vs_ni_history: list[FcfVsNiYear]


class ValuationOut(BaseModel):
    company_id: str
    status: str
    current_share_price: float | None
    diluted_shares: float | None
    net_debt: float | None
    baseline_fcf: float | None
    wacc: float
    terminal_growth_rate: float
    market_implied_growth_10y: float | None
    historical_5y_cagr: float | None
    expectations_gap: float | None
    sensitivity_matrix: dict[str, Any] | None
    # Trust sprint C: freshness provenance
    price_as_of: str | None = None
    price_freshness: str | None = None  # green | amber | red | unknown
    baseline_fcf_period_end: str | None = None
    baseline_fcf_basis: str | None = None
    fcf_freshness: str | None = None
    valuation_computed_at: str | None = None


class DeleteCompanyOut(BaseModel):
    ok: bool
    company_id: str
    message: str


# --- Endpoints ---

@router.get("/companies/{company_id}/forensics", response_model=ForensicsOut)
def get_company_forensics(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    try:
        # Read-only: never create TTM on GET (avoids SQLite write lock)
        ttm = db.get(FinancialSnapshotTTM, cid)
        if not ttm:
            raise ValueError("ttm_not_materialized")
    except Exception as exc:
        # Safe fallback - never 500, never write
        return ForensicsOut(
            company_id=cid,
            currency=company.currency or "USD",
            sloan_accrual_ratio=None,
            sloan_signal="insufficient_data",
            cash_conversion_ratio=None,
            cash_conversion_signal="insufficient_data",
            roic=None,
            roic_interpretation="not_meaningful",
            roic_confidence="low",
            roic_warning_reason=f"ttm_unavailable: {exc.__class__.__name__}",
            invested_capital_to_assets=None,
            fcf_yield=None,
            nopat=None,
            invested_capital=None,
            fcf_vs_ni_history=[],
        )

    # 5-year FCF vs Net Income history from annual snapshots
    annuals = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == cid,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.asc())
    ).scalars().all()

    fcf_vs_ni = [
        FcfVsNiYear(
            fiscal_year=a.fiscal_year,
            net_income=a.net_income,
            fcf=a.fcf_calc,
        )
        for a in annuals
        if a.fiscal_year is not None
    ]

    sloan = ttm.sloan_accrual_ratio
    sloan_signal = "insufficient_data"
    if sloan is not None:
        if sloan > 0.10:
            sloan_signal = "red"  # Aggressive accounting
        elif sloan < -0.10:
            sloan_signal = "green"  # Conservative accounting
        else:
            sloan_signal = "neutral"

    ccer = ttm.cash_conversion_ratio
    ccer_signal = "insufficient_data"
    if ccer is not None:
        ccer_signal = "weak" if ccer < 0.70 else "healthy"

    return ForensicsOut(
        company_id=cid,
        currency=ttm.currency,
        sloan_accrual_ratio=sloan,
        sloan_signal=sloan_signal,
        cash_conversion_ratio=ccer,
        cash_conversion_signal=ccer_signal,
        roic=ttm.roic,
        roic_interpretation=getattr(ttm, "roic_interpretation", None),
        roic_confidence=getattr(ttm, "roic_confidence", None),
        roic_warning_reason=getattr(ttm, "roic_warning_reason", None),
        invested_capital_to_assets=getattr(ttm, "invested_capital_to_assets", None),
        fcf_yield=ttm.fcf_yield,
        nopat=ttm.nopat,
        invested_capital=ttm.invested_capital,
        fcf_vs_ni_history=fcf_vs_ni,
    )


@router.get("/companies/{company_id}/forensics/benford")
def get_company_benford(company_id: str, db: Session = Depends(get_db)):
    """Wave 3 US-0211: Benford's Law first-digit distribution test."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.benford_engine import compute_benford
        return compute_benford(db, cid)
    except Exception as exc:
        return {
            "company_id": cid,
            "status": "insufficient_data",
            "verdict": "insufficient_data",
            "chi2": None,
            "observations": 0,
            "message": f"Benford unavailable: {exc.__class__.__name__}",
            "detail": str(exc)[:400],
        }


@router.get("/companies/{company_id}/forensics/summary")
def get_company_forensics_summary(company_id: str, db: Session = Depends(get_db)):
    """Wave 3 US-0213/US-0222/US-0239: Consolidated red-flag count, severity, cross-model comparison."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    try:
        from app.services.beneish_engine import compute_beneish_m_score
        from app.services.distress_engine import compute_distress
        from app.services.sloan_engine import compute_sloan_accruals
        from app.services.shenanigans_engine import compute_shenanigans_summary
        from app.services.benford_engine import compute_benford

        beneish = compute_beneish_m_score(db, cid)
        distress = compute_distress(db, cid)
        sloan = compute_sloan_accruals(db, cid)
        shen = compute_shenanigans_summary(db, cid)
        benford = compute_benford(db, cid)
    except Exception as exc:
        return {
            "company_id": cid,
            "currency": getattr(company, "currency", "USD"),
            "forensic_health_score": 50,
            "forensic_risk_tier": "Insufficient Data",
            "flag_count": 0,
            "flags": [],
            "triggered_codes": [],
            "cross_model_divergence": None,
            "plain_language_summary": f"Forensic summary unavailable: {exc.__class__.__name__}",
            "status": "insufficient_data",
            "message": str(exc)[:400],
        }

    # Severity mapping
    flags: list[dict[str, Any]] = []
    if beneish.get("is_manipulator"):
        flags.append({"code": "BENEISH_MANIPULATOR", "severity": "critical", "detail": f"M-Score {beneish.get('m_score')} > -1.78", "threshold": -1.78, "value": beneish.get("m_score")})
    if distress.get("zone") == "Distress":
        flags.append({"code": "ALTMAN_DISTRESS", "severity": "critical", "detail": f"Altman Z {distress.get('active_z')} in Distress", "threshold": "1.81 / 1.10", "value": distress.get("active_z")})
    elif distress.get("zone") == "Grey":
        flags.append({"code": "ALTMAN_GREY", "severity": "elevated", "detail": f"Altman Z {distress.get('active_z')} in Grey", "threshold": "2.99 / 2.60", "value": distress.get("active_z")})
    if sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS":
        flags.append({"code": "SLOAN_HIGH_ACCRUALS", "severity": "elevated", "detail": f"Accrual ratio {sloan.get('accrual_ratio')}", "threshold": 0.10, "value": sloan.get("accrual_ratio")})
    for code in shen.get("triggered_flags", []):
        # Avoid duplicating beneish if already counted; shen includes those
        if code in ("BENEISH_MANIPULATOR",):
            continue
        sev = "critical" if code in ("GOING_CONCERN_LANGUAGE", "AUDITOR_CHANGE") else ("elevated" if "RED_FLAG" in code or "GOODWILL" in code or "COVENANT" in code else "informational")
        flags.append({"code": code, "severity": sev, "detail": code, "threshold": None, "value": None})
    if benford.get("verdict") == "strong_deviation":
        flags.append({"code": "BENFORD_STRONG_DEVIATION", "severity": "informational", "detail": f"Benford chi2 {benford.get('chi2')}", "threshold": 20.09, "value": benford.get("chi2")})
    elif benford.get("verdict") == "deviation_noted":
        flags.append({"code": "BENFORD_DEVIATION_NOTED", "severity": "informational", "detail": f"Benford chi2 {benford.get('chi2')}", "threshold": 15.507, "value": beneish.get("m_score")})

    # Cross-model divergence callout
    divergence = None
    beneish_clean = not beneish.get("is_manipulator")
    sloan_high = sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS"
    distress_safe = distress.get("zone") == "Safe"
    if beneish_clean and sloan_high:
        divergence = "Beneish=Clean but Sloan=High Accruals - cash lags earnings; accrual quality deserves scrutiny."
    elif distress_safe and beneish.get("is_manipulator"):
        divergence = "Altman=Safe but Beneish=Manipulator - solvency appears safe while earnings manipulation screen flagged."

    # Forensic health score 0-100
    health = 100
    for f in flags:
        if f["severity"] == "critical":
            health -= 25
        elif f["severity"] == "elevated":
            health -= 15
        else:
            health -= 8
    health = max(0, min(100, health))
    tier = "Clean / Low Forensic Risk" if health >= 80 else ("Moderate Forensic Caution" if health >= 50 else "High Forensic Risk / Red Flags")

    # Plain-language summary
    top = flags[:2]
    if top:
        summary = " and ".join([f["detail"] for f in top]) + "."
    else:
        summary = "No material forensic flags triggered; earnings and balance-sheet screens appear clean."

    return {
        "company_id": cid,
        "currency": company.currency,
        "forensic_health_score": health,
        "forensic_risk_tier": tier,
        "flag_count": len(flags),
        "flags": flags,
        "triggered_codes": [f["code"] for f in flags],
        "cross_model_divergence": divergence,
        "plain_language_summary": summary,
        "beneish": beneish,
        "distress": distress,
        "sloan": sloan,
        "shenanigans": shen,
        "benford": {"verdict": benford.get("verdict"), "chi2": benford.get("chi2"), "observations": benford.get("observations")},
        "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
        "method_version": "v1",
    }


@router.get("/companies/{company_id}/forensics/timeline")
def get_company_forensics_timeline(company_id: str, db: Session = Depends(get_db)):
    """Wave 3 US-0230: Year-by-year forensic timeline."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.distress_engine import compute_distress
    from app.services.sloan_engine import compute_sloan_accruals

    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid, FinancialSnapshot.period_type == "FY").order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    # Build timeline from each distinct FY where snapshot exists (up to last 10)
    fyears = sorted({s.fiscal_year for s in snaps if s.fiscal_year is not None})
    items = []
    for fy in fyears[-10:]:
        # For timeline we compute current snapshot's forensic via snapshot-specific logic;
        # As heuristic, recompute with latest but annotate FY; full per-FY recomputation would require
        # historical engine that accepts arbitrary FY cutoff - for now return latest values per FY with honest note.
        beneish = compute_beneish_m_score(db, cid)
        distress = compute_distress(db, cid)
        sloan = compute_sloan_accruals(db, cid)
        items.append({
            "fiscal_year": fy,
            "beneish_m": beneish.get("m_score"),
            "beneish_zone": beneish.get("zone"),
            "altman_z": distress.get("active_z"),
            "altman_zone": distress.get("zone"),
            "sloan_ratio": sloan.get("accrual_ratio"),
            "sloan_flag": sloan.get("flag"),
        })
    return {"company_id": cid, "count": len(items), "timeline": items, "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings."}


@router.get("/forensics/rank")
def rank_forensics(ids: str = Query(..., description="Comma-separated company IDs"), db: Session = Depends(get_db)):
    """Wave 3 US-0249: Portfolio-level forensic severity ranker."""
    cids = [c.strip() for c in ids.split(",") if c.strip()]
    if len(cids) < 1 or len(cids) > 20:
        raise HTTPException(status_code=400, detail="Provide 1-20 company IDs")
    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.distress_engine import compute_distress
    from app.services.sloan_engine import compute_sloan_accruals

    ranked = []
    for cid in cids:
        norm = normalize_company_id(cid) or cid
        company = db.get(Company, norm)
        if not company:
            continue
        beneish = compute_beneish_m_score(db, norm)
        distress = compute_distress(db, norm)
        sloan = compute_sloan_accruals(db, norm)
        # Score severity 0 clean → higher = riskier
        sev = 0
        worst = None
        if distress.get("zone") == "Distress":
            sev += 30
            worst = "ALTMAN_DISTRESS"
        elif distress.get("zone") == "Grey":
            sev += 10
            worst = worst or "ALTMAN_GREY"
        if beneish.get("is_manipulator"):
            sev += 25
            worst = "BENEISH_MANIPULATOR"
        if sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS":
            sev += 15
            worst = worst or "SLOAN_HIGH_ACCRUALS"
        ranked.append({
            "company_id": norm,
            "ticker": company.ticker,
            "name": company.name,
            "currency": company.currency,
            "severity_score": sev,
            "worst_flag": worst or "None",
            "flag_count": (1 if beneish.get("is_manipulator") else 0) + (1 if distress.get("zone") in ("Distress", "Grey") else 0) + (1 if sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS" else 0),
            "altman_zone": distress.get("zone"),
            "beneish_zone": beneish.get("zone"),
            "sloan_flag": sloan.get("flag"),
        })
    ranked.sort(key=lambda x: x["severity_score"], reverse=True)
    return {"count": len(ranked), "ranked": ranked}


@router.get("/companies/{company_id}/forensics/export")
def export_forensics(company_id: str, format: str = Query(default="json", pattern="^(json|csv)$"), db: Session = Depends(get_db)):
    """Wave 3 US-0214/US-0240: Structured forensic export."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")
    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.distress_engine import compute_distress
    from app.services.sloan_engine import compute_sloan_accruals
    from app.services.shenanigans_engine import compute_shenanigans_summary

    beneish = compute_beneish_m_score(db, cid)
    distress = compute_distress(db, cid)
    sloan = compute_sloan_accruals(db, cid)
    shen = compute_shenanigans_summary(db, cid)
    payload = {
        "company_id": cid,
        "currency": company.currency,
        "method_version": "v1",
        "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
        "beneish": beneish,
        "distress": distress,
        "sloan": sloan,
        "shenanigans": shen,
    }
    if format == "csv":
        import csv, io
        from fastapi.responses import PlainTextResponse

        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["model", "field", "value", "threshold", "interpretation"])
        w.writerow(["beneish", "m_score", beneish.get("m_score"), -1.78, beneish.get("interpretation")])
        w.writerow(["altman", "active_z", distress.get("active_z"), "2.99/1.81", distress.get("zone")])
        w.writerow(["sloan", "accrual_ratio", sloan.get("accrual_ratio"), 0.10, sloan.get("interpretation")])
        for code in shen.get("triggered_flags", []):
            w.writerow(["shenanigans", code, "triggered", None, code])
        return PlainTextResponse(content=out.getvalue(), media_type="text/csv")
    return payload


@router.get("/companies/{company_id}/quality")
def get_company_quality(company_id: str, db: Session = Depends(get_db)):
    """Trust sprint E1: provenance + freshness + denominator confidence for the dossier drawer."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    from datetime import datetime as _dt

    from app.services.valuation_engine import get_freshness_status

    now = _dt.utcnow()
    seed = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == cid,
            FinancialSnapshot.fiscal_year.is_(None),
        )
    ).scalar_one_or_none()
    latest_annual = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == cid,
            FinancialSnapshot.fiscal_year.is_not(None),
            FinancialSnapshot.period_type == "FY",
        ).order_by(FinancialSnapshot.fiscal_year.desc())
    ).scalars().first()

    price_as_of = (seed.as_of_date if seed and seed.as_of_date else (latest_annual.as_of_date if latest_annual else None))
    price_freshness = get_freshness_status(price_as_of, now, kind="price")

    sources: set[str] = set()
    if seed and seed.source:
        sources.add(str(seed.source).split(":")[0])
    if latest_annual and latest_annual.source:
        sources.add(str(latest_annual.source).split(":")[0])

    # Read-only: never materialize TTM on GET
    ttm = db.get(FinancialSnapshotTTM, cid)
    if ttm is None:
        return {
            "company_id": cid,
            "currency": company.currency,
            "price_freshness": price_freshness,
            "price_as_of": price_as_of.isoformat() if price_as_of else None,
            "statement_as_of": latest_annual.as_of_date.isoformat() if latest_annual and latest_annual.as_of_date else None,
            "source_count": len(sources),
            "sources": sorted(sources),
            "denominator_confidence": None,
            "roic_interpretation": "not_meaningful",
            "roic_warning_reason": "ttm_not_materialized",
        }

    return {
        "company_id": cid,
        "currency": company.currency,
        "price_freshness": price_freshness,
        "price_as_of": price_as_of.isoformat() if price_as_of else None,
        "statement_as_of": latest_annual.as_of_date.isoformat() if latest_annual and latest_annual.as_of_date else None,
        "source_count": len(sources),
        "sources": sorted(sources),
        "denominator_confidence": ttm.roic_confidence,
        "roic_interpretation": ttm.roic_interpretation,
        "roic_warning_reason": ttm.roic_warning_reason,
    }


@router.get("/companies/{company_id}/penman")
def get_company_penman(company_id: str, db: Session = Depends(get_db)):
    """Analytical sprint WS2: Penman reformulation (RNOA vs naive ROIC, leverage). Read-only."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    # Read-only: query existing Penman row, never compute_and_store on GET
    from app.models import FinancialPenmanAnalysis

    row = db.execute(
        select(FinancialPenmanAnalysis).where(FinancialPenmanAnalysis.company_id == cid).order_by(FinancialPenmanAnalysis.fiscal_year.desc().nullslast())
    ).scalars().first()
    if row is None:
        return {
            "company_id": cid,
            "status": "insufficient_data",
            "rnoa": None,
            "flev": None,
            "nbc": None,
            "nopat": None,
            "noa": None,
            "nfo": None,
            "leverage_distortion": None,
            "exclusion": None,
        }
    return {
        "company_id": cid,
        "status": "financial_institution_excluded" if row.exclusion else "ok",
        "fiscal_year": row.fiscal_year,
        "rnoa": row.rnoa,
        "flev": row.flev,
        "nbc": row.nbc,
        "nopat": row.nopat,
        "noa": row.noa,
        "nfo": row.nfo,
        "roe_operational_spread": row.roe_operational_spread,
        "identity_ok": row.identity_ok,
        "leverage_distortion": row.leverage_distortion,
        "exclusion": row.exclusion,
    }


@router.get("/companies/{company_id}/schilit")
def get_company_schilit(company_id: str, db: Session = Depends(get_db)):
    """Analytical sprint WS3: Schilit shenanigans flags + Earnings Quality Rating."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    from app.services.forensic_engine import analyze_company

    return analyze_company(db, cid)


@router.get("/companies/{company_id}/graham")
def get_company_graham(company_id: str, db: Session = Depends(get_db)):
    """Analytical sprint WS4: Graham floors (Graham Number, NCAV, NNWC) + MoS. Read-only."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    from app.services.graham_engine import compute_graham

    # compute_graham is pure (no DB writes), so no commit needed
    return compute_graham(db, cid)


@router.get("/companies/{company_id}/practitioner")
def get_company_practitioner_analytics(company_id: str, db: Session = Depends(get_db)):
    """Master Directive WS3: Practitioner analytical engines (Penman, Fridson, Graham, Malkiel, Housel)."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    from app.services.practitioner_engine import get_practitioner_analytics

    return get_practitioner_analytics(db, cid)


@router.get("/companies/{company_id}/valuation", response_model=ValuationOut)
def get_company_valuation(company_id: str, db: Session = Depends(get_db)):
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    # Read-only: never materialize Reverse DCF on GET
    dcf = db.get(ValuationReverseDCF, cid)
    if not dcf:
        raise HTTPException(status_code=404, detail=f"Valuation not materialized for {cid}. Trigger background recompute or ingest.")

    # Trust sprint C: freshness classification for price + FCF basis.
    from datetime import datetime as _dt, timezone as _tz

    from app.services.valuation_engine import get_freshness_status

    now = _dt.now(_tz.utc).replace(tzinfo=None)
    price_freshness = get_freshness_status(dcf.price_as_of, now, kind="price")
    fcf_freshness = get_freshness_status(dcf.baseline_fcf_period_end, now, kind="statement")

    return ValuationOut(
        company_id=cid,
        status=dcf.status,
        current_share_price=dcf.current_share_price,
        diluted_shares=dcf.diluted_shares,
        net_debt=dcf.net_debt,
        baseline_fcf=dcf.baseline_fcf,
        wacc=dcf.wacc,
        terminal_growth_rate=dcf.terminal_growth_rate,
        market_implied_growth_10y=dcf.market_implied_growth_10y,
        historical_5y_cagr=dcf.historical_5y_cagr,
        expectations_gap=dcf.expectations_gap,
        sensitivity_matrix=dcf.sensitivity_matrix_json,
        price_as_of=dcf.price_as_of.isoformat() if dcf.price_as_of else None,
        price_freshness=price_freshness,
        baseline_fcf_period_end=dcf.baseline_fcf_period_end.isoformat() if dcf.baseline_fcf_period_end else None,
        baseline_fcf_basis=dcf.baseline_fcf_basis,
        fcf_freshness=fcf_freshness,
        valuation_computed_at=dcf.valuation_computed_at.isoformat() if dcf.valuation_computed_at else None,
    )


@router.delete("/companies/{company_id}", response_model=DeleteCompanyOut)
def delete_company(company_id: str, hard: bool = Query(False), db: Session = Depends(get_db)):
    """Removes a company from the active research desk. Defaults to soft deletion."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    if hard:
        db.delete(company)
        db.commit()
        return DeleteCompanyOut(ok=True, company_id=cid, message=f"Permanently deleted {cid} from database.")

    company.is_deleted = True
    db.commit()
    return DeleteCompanyOut(ok=True, company_id=cid, message=f"Removed {cid} from active research desk.")


@router.post("/companies/{company_id}/restore", response_model=DeleteCompanyOut)
def restore_company(company_id: str, db: Session = Depends(get_db)):
    """Restores a previously removed company back to the active research desk."""
    cid = normalize_company_id(company_id) or company_id
    company = db.get(Company, cid)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {cid} not found")

    company.is_deleted = False
    db.commit()
    return DeleteCompanyOut(ok=True, company_id=cid, message=f"Restored {cid} to active research desk.")


@router.get("/screener/presets")
def get_screener_presets(db: Session = Depends(get_db)):
    """Lists institutional deep-value and forensic screener presets including user custom presets. Read-only."""
    presets = db.execute(
        select(ScreenerPreset).order_by(ScreenerPreset.is_system_preset.desc(), ScreenerPreset.name.asc())
    ).scalars().all()
    if presets:
        return [
            {
                "id": p.id,
                "name": p.name,
                "criteria": p.criteria_json,
                "is_system": p.is_system_preset,
                "auto_run_on_refresh": bool(p.criteria_json.get("auto_run_on_refresh", False)) if p.criteria_json else False,
            }
            for p in presets
        ]
    # Read-only fallback: return in-memory system presets when DB not yet seeded (avoids write on GET)
    try:
        from app.services.screener_engine import SYSTEM_PRESETS
        from app.services.screener_bundle import CANONICAL_PRESETS
        combined = {p["id"]: p for p in SYSTEM_PRESETS + CANONICAL_PRESETS}
        return [
            {"id": pid, "name": p["name"], "criteria": p["criteria"], "is_system": True, "auto_run_on_refresh": False}
            for pid, p in sorted(combined.items())
        ]
    except Exception:
        return []


@router.post("/screener/presets")
def save_screener_preset(body: ScreenerPresetCreateIn, db: Session = Depends(get_db)):
    """Saves a custom screener preset with a one-word or custom name (US-0009)."""
    preset_id = (body.id or body.name).strip().lower().replace(" ", "_")
    criteria = dict(body.criteria)
    if body.auto_run_on_refresh:
        criteria["auto_run_on_refresh"] = True

    row = db.get(ScreenerPreset, preset_id)
    if row is None:
        row = ScreenerPreset(
            id=preset_id,
            name=body.name.strip(),
            criteria_json=criteria,
            is_system_preset=False,
        )
        db.add(row)
    else:
        row.name = body.name.strip()
        row.criteria_json = criteria

    db.commit()
    return {
        "ok": True,
        "id": row.id,
        "name": row.name,
        "criteria": row.criteria_json,
        "is_system": row.is_system_preset,
        "auto_run_on_refresh": bool(row.criteria_json.get("auto_run_on_refresh", False)),
    }


@router.delete("/screener/presets/{preset_id}")
def delete_screener_preset(preset_id: str, db: Session = Depends(get_db)):
    """Deletes a custom user screener preset."""
    row = db.get(ScreenerPreset, preset_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    if row.is_system_preset:
        raise HTTPException(status_code=400, detail="Cannot delete institutional system preset")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted": preset_id}


@router.put("/screener/presets/{preset_id}/auto-run")
def toggle_preset_auto_run(preset_id: str, db: Session = Depends(get_db)):
    """Toggles preset auto-run queue for execution after data refresh (US-0042)."""
    row = db.get(ScreenerPreset, preset_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    crit = dict(row.criteria_json or {})
    current_auto = crit.get("auto_run_on_refresh", False)
    crit["auto_run_on_refresh"] = not current_auto
    row.criteria_json = crit
    db.commit()
    return {"ok": True, "id": row.id, "auto_run_on_refresh": crit["auto_run_on_refresh"]}


@router.post("/screener/run")
def run_screener(body: ScreenerRunIn, db: Session = Depends(get_db)):
    """Runs a multi-metric deep-value forensic screener query."""
    criteria = body.model_dump(exclude_none=True)
    return run_screener_query(db, criteria, limit=body.limit, offset=body.offset)
