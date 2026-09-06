"""Schilit Forensic Shenanigans Engine (Master Directive WS3).

Detects earnings manipulation / cash-flow distortion across multi-year FY rows.

Available metrics given the stored schema (no AR/inventory breakdowns on
FinancialSnapshot): the engine computes every flag whose inputs exist and
returns `insufficient_data` markers for the rest - it never fabricates inputs.

Flags:
- RED_FLAG_CFO_EARNINGS_DECOUPLING: CFO < NI for 2 consecutive FY periods.
- RED_FLAG_DSO_SURGE: receivables-based; requires accounts_receivable column
  (absent today) -> reported as data-unavailable, never guessed.
- RED_FLAG_INVENTORY_BUILDUP: same for inventory.
- RED_FLAG_CAPITALIZED_EXPENSES: AQI needs current assets + PP&E (absent) ->
  data-unavailable today.

Earnings Quality Rating (EQR, 0-100): 100 base, -25 per confirmed flag,
floored at 0; `None` when no flag can be evaluated.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FinancialSnapshot

FLAG_CFO_DECOUPLING = "RED_FLAG_CFO_EARNINGS_DECOUPLING"
FLAG_DSO_SURGE = "RED_FLAG_DSO_SURGE"
FLAG_INVENTORY_BUILDUP = "RED_FLAG_INVENTORY_BUILDUP"
FLAG_CAPITALIZED_EXPENSES = "RED_FLAG_CAPITALIZED_EXPENSES"


def analyze_cfo_ni_decoupling(snaps: list[FinancialSnapshot]) -> dict[str, Any]:
    """CFO < NI for 2 consecutive fiscal years (ordered oldest -> newest)."""
    rows = sorted(
        (s for s in snaps if s.fiscal_year is not None and s.operating_cash_flow is not None and s.net_income is not None),
        key=lambda s: s.fiscal_year,
    )
    breaches: list[int] = []
    for a, b in zip(rows, rows[1:]):
        if b.fiscal_year and a.fiscal_year and b.fiscal_year - a.fiscal_year <= 2:
            if b.operating_cash_flow < b.net_income and a.operating_cash_flow < a.net_income:
                breaches.append(b.fiscal_year)
    return {
        "flag": FLAG_CFO_DECOUPLING,
        "triggered": bool(breaches),
        "years": breaches,
        "evidence": [
            {
                "fiscal_year": r.fiscal_year,
                "cfo": r.operating_cash_flow,
                "net_income": r.net_income,
            }
            for r in rows[-3:]
        ],
    }


def analyze_dso(snaps: list[FinancialSnapshot]) -> dict[str, Any]:
    """Detects accounts receivable growth outstripping revenue growth by > 15%."""
    rows = sorted(
        (s for s in snaps if s.fiscal_year is not None and getattr(s, "accounts_receivable", None) is not None and s.revenue is not None),
        key=lambda s: s.fiscal_year,
    )
    if len(rows) < 2:
        has_ar = any(getattr(s, "accounts_receivable", None) is not None for s in snaps)
        return {"flag": FLAG_DSO_SURGE, "triggered": False, "data_available": has_ar}

    breaches: list[int] = []
    for a, b in zip(rows, rows[1:]):
        ar_a = getattr(a, "accounts_receivable", 0.0) or 0.0
        ar_b = getattr(b, "accounts_receivable", 0.0) or 0.0
        rev_a = a.revenue or 0.0
        rev_b = b.revenue or 0.0
        if ar_a > 0 and rev_a > 0 and b.fiscal_year:
            ar_growth = (ar_b - ar_a) / ar_a
            rev_growth = (rev_b - rev_a) / rev_a
            if ar_growth > (rev_growth + 0.15):
                breaches.append(b.fiscal_year)

    return {
        "flag": FLAG_DSO_SURGE,
        "triggered": bool(breaches),
        "data_available": True,
        "years": breaches,
    }


def analyze_inventory(snaps: list[FinancialSnapshot]) -> dict[str, Any]:
    """Detects inventory growth outstripping revenue growth by > 15%."""
    rows = sorted(
        (s for s in snaps if s.fiscal_year is not None and getattr(s, "inventory", None) is not None and s.revenue is not None),
        key=lambda s: s.fiscal_year,
    )
    if len(rows) < 2:
        has_inv = any(getattr(s, "inventory", None) is not None for s in snaps)
        return {"flag": FLAG_INVENTORY_BUILDUP, "triggered": False, "data_available": has_inv}

    breaches: list[int] = []
    for a, b in zip(rows, rows[1:]):
        inv_a = getattr(a, "inventory", 0.0) or 0.0
        inv_b = getattr(b, "inventory", 0.0) or 0.0
        rev_a = a.revenue or 0.0
        rev_b = b.revenue or 0.0
        if inv_a > 0 and rev_a > 0 and b.fiscal_year:
            inv_growth = (inv_b - inv_a) / inv_a
            rev_growth = (rev_b - rev_a) / rev_a
            if inv_growth > (rev_growth + 0.15):
                breaches.append(b.fiscal_year)

    return {
        "flag": FLAG_INVENTORY_BUILDUP,
        "triggered": bool(breaches),
        "data_available": True,
        "years": breaches,
    }


def analyze_aqi(snaps: list[FinancialSnapshot]) -> dict[str, Any]:
    """Asset Quality Index check: Non-current non-PPE assets expanding as % of assets."""
    rows = sorted(
        (s for s in snaps if s.fiscal_year is not None and getattr(s, "current_assets", None) is not None and s.total_assets is not None),
        key=lambda s: s.fiscal_year,
    )
    if len(rows) < 2:
        has_ca = any(getattr(s, "current_assets", None) is not None for s in snaps)
        return {"flag": FLAG_CAPITALIZED_EXPENSES, "triggered": False, "data_available": has_ca}

    breaches: list[int] = []
    for a, b in zip(rows, rows[1:]):
        ta_a = a.total_assets or 1.0
        ta_b = b.total_assets or 1.0
        ca_a = getattr(a, "current_assets", None) or 0.0
        ca_b = getattr(b, "current_assets", None) or 0.0
        ppe_a = getattr(a, "ppe_net", None) or 0.0
        ppe_b = getattr(b, "ppe_net", None) or 0.0

        non_ca_a = 1.0 - ((ca_a + ppe_a) / ta_a)
        non_ca_b = 1.0 - ((ca_b + ppe_b) / ta_b)
        if non_ca_a > 0 and (non_ca_b / non_ca_a) > 1.25 and b.fiscal_year:
            breaches.append(b.fiscal_year)

    return {
        "flag": FLAG_CAPITALIZED_EXPENSES,
        "triggered": bool(breaches),
        "data_available": True,
        "years": breaches,
    }


def earnings_quality_rating(results: list[dict[str, Any]]) -> int | None:
    """0-100 EQR; None when nothing was evaluable (all inputs missing)."""
    evaluable = [r for r in results if r.get("data_available", True)]
    if not evaluable:
        return None
    score = 100
    for r in evaluable:
        if r.get("triggered"):
            score -= 25
    return max(0, score)


def analyze_company(db: Session, company_id: str) -> dict[str, Any]:
    """Full Schilit workup for one company from stored FY rows (read-only)."""
    snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
    ).scalars().all()

    cfo = analyze_cfo_ni_decoupling(list(snaps))
    dso = analyze_dso(list(snaps))
    inv = analyze_inventory(list(snaps))
    aqi = analyze_aqi(list(snaps))

    results = [cfo, dso, inv, aqi]
    return {
        "company_id": company_id,
        "flags": results,
        "triggered_flags": [r["flag"] for r in results if r.get("triggered")],
        "eqr": earnings_quality_rating(results),
        "periods_evaluated": len([s for s in snaps if s.fiscal_year is not None]),
    }


def synthesize_forensic_health(db: Session, company_id: str) -> dict[str, Any]:
    """Master Forensic Red Flag Synthesizer (Task 3.3).

    Synthesizes Schilit Shenanigans, Beneish M-Score, and Sloan Accruals into
    a unified Forensic Health Score (0-100) and risk tier.
    """
    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.sloan_engine import compute_sloan_accruals

    schilit = analyze_company(db, company_id)
    beneish = compute_beneish_m_score(db, company_id)
    sloan = compute_sloan_accruals(db, company_id)

    score = 100
    penalties = []

    # 1. Schilit flags
    for fl in schilit["flags"]:
        if fl.get("triggered"):
            name = fl.get("flag", "UNKNOWN")
            pts = 20 if name == FLAG_DSO_SURGE else (15 if name == FLAG_INVENTORY_BUILDUP else 25)
            score -= pts
            penalties.append(f"{name}: -{pts} pts")

    # 2. Beneish M-Score flag
    if beneish.get("is_manipulator"):
        score -= 25
        penalties.append(f"Beneish M-Score flagged ({beneish.get('m_score')}): -25 pts")

    # 3. Sloan Accruals flag
    if sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS":
        score -= 15
        penalties.append(f"Sloan High Accruals ({sloan.get('accrual_ratio')}): -15 pts")

    final_score = max(0, min(100, score))

    if final_score >= 80:
        tier = "Clean / Low Forensic Risk"
    elif final_score >= 50:
        tier = "Moderate Forensic Caution"
    else:
        tier = "High Forensic Risk / Red Flags"

    return {
        "company_id": company_id,
        "forensic_health_score": final_score,
        "forensic_risk_tier": tier,
        "penalties": penalties,
        "schilit": schilit,
        "beneish": beneish,
        "sloan": sloan,
    }


def compute_and_store_ttm_forensics(db: Session, company_id: str) -> dict[str, Any]:
    """Runs the Schilit workup and persists EQR/flags onto the TTM row (screener-facing)."""
    from app.models import FinancialSnapshotTTM

    result = analyze_company(db, company_id)
    ttm = db.get(FinancialSnapshotTTM, company_id)
    if ttm is None:
        ttm = compute_and_store_ttm(db, company_id)
    ttm.eqr = result["eqr"]
    ttm.forensic_flags_json = {
        "triggered": result["triggered_flags"],
        "flags": [
            {"flag": r["flag"], "triggered": r.get("triggered"), "years": r.get("years")}
            for r in result["flags"]
            if r.get("triggered") or r.get("data_available")
        ],
    }
    db.flush()
    return result


from app.services.ttm_engine import compute_and_store_ttm  # noqa: E402  (late import avoids a cycle)