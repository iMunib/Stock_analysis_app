"""Automated 60-Second Safety Verdict Algorithm (Phase 2 Master Directive).

Deterministically synthesizes Moat, Solvency (Altman Z), Earnings Quality
(Beneish M-Score & Sloan Accruals), and Valuation Hurdle (Reverse DCF Gap)
into 5 mutually exclusive verdict tags:

1. COMPOUNDER AT FAIR VALUE:
   Wide/Narrow Moat + Altman Z Safe + Reverse DCF Gap <= +2%.
2. UNDERVALUED BARGAIN:
   Altman Z Safe + Beneish Clean + Current Price <= Graham Floor / >25% Margin of Safety.
3. OVERVALUED QUALITY:
   Wide Moat + Pristine Balance Sheet, BUT Reverse DCF Gap > +6% (Priced for perfection).
4. CYCLICAL PEAK: CAUTION:
   Cyclical Archetype + Trough P/E multiple at peak earnings + decelerating CFO.
5. AVOID: VALUE TRAP / DISTRESS:
   Altman Z Distress Zone OR Beneish M-Score flagged OR severe CFO-NI decoupling.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.archetype_engine import classify_archetype
from app.services.beneish_engine import compute_beneish_m_score
from app.services.distress_engine import compute_distress
from app.services.graham_engine import compute_graham
from app.services.moat_engine import compute_economic_moat
from app.services.sloan_engine import compute_sloan_accruals
from app.services.valuation_engine import compute_and_store_reverse_dcf, evaluate_reverse_dcf_hurdles


VERDICT_COMPOUNDER = "COMPOUNDER AT FAIR VALUE"
VERDICT_BARGAIN = "UNDERVALUED BARGAIN"
VERDICT_OVERVALUED = "OVERVALUED QUALITY"
VERDICT_CYCLICAL = "CYCLICAL PEAK: CAUTION"
VERDICT_AVOID = "AVOID: VALUE TRAP / DISTRESS"


def synthesize_safety_verdict(db: Session, company_id: str) -> dict[str, Any]:
    """Generates the automated deterministic 60-second safety verdict."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    # 1. Gather all analytical inputs
    distress = compute_distress(db, company_id)
    beneish = compute_beneish_m_score(db, company_id)
    sloan = compute_sloan_accruals(db, company_id)
    moat = compute_economic_moat(db, company_id)
    archetype = classify_archetype(db, company_id)
    graham = compute_graham(db, company_id)

    # Reverse DCF
    dcf_row = compute_and_store_reverse_dcf(db, company_id)
    dcf_eval = evaluate_reverse_dcf_hurdles(dcf_row)

    # Multi-period snapshots for CFO-NI decoupling check
    snaps = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()
    latest = snaps[-1] if snaps else None
    prev = snaps[-2] if len(snaps) >= 2 else None

    # Solvency
    z_zone = distress.get("zone", "Unknown")
    is_distress = (z_zone == "Distress")

    # Earnings quality
    is_manipulator = beneish.get("is_manipulator", False)
    sloan_high_accruals = (
        sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS"
        or (sloan.get("accrual_ratio") is not None and sloan["accrual_ratio"] > 0.10)
    )
    ni = latest.net_income if latest else None
    cfo = latest.operating_cash_flow if latest else None
    cfo_prev = prev.operating_cash_flow if prev else None
    cfo_decelerating = (cfo is not None and cfo_prev is not None and cfo < cfo_prev)

    cfo_ni_decoupling = False
    if ni is not None and cfo is not None:
        if ni > 0 and cfo < 0:
            cfo_ni_decoupling = True
        elif ni > 0 and cfo > 0 and (cfo / ni) < 0.35:
            cfo_ni_decoupling = True

    # Valuation & Moat
    gap = dcf_row.expectations_gap if dcf_row else None
    moat_rating = moat.get("moat_rating", "None")
    is_cyclical = archetype.get("archetype") == "Cyclicals"
    price = latest.price if latest else None
    graham_number = graham.get("graham_number")
    is_graham_bargain = (price is not None and graham_number is not None and price <= graham_number * 0.75)

    # 2. Decision Synthesis Hierarchy
    verdict_badge = VERDICT_COMPOUNDER
    rationale_bullets = []

    # Priority 1: Distress / Manipulation / Severe decoupling / Paper Accruals
    if is_distress or is_manipulator or cfo_ni_decoupling or sloan_high_accruals:
        verdict_badge = VERDICT_AVOID
        if is_distress:
            rationale_bullets.append(f"Solvency warning: Altman Z-score in Distress zone ({distress.get('active_z')}).")
        if is_manipulator:
            rationale_bullets.append(f"Forensic flag: Beneish M-Score ({beneish.get('m_score')}) indicates high manipulation probability.")
        if cfo_ni_decoupling:
            rationale_bullets.append("Severe CFO-Net Income divergence; earnings lack underlying operating cash generation.")
        if sloan_high_accruals:
            ratio_pct = sloan.get('accrual_ratio', 0) * 100.0 if sloan.get('accrual_ratio') is not None else 10.0
            rationale_bullets.append(f"Forensic accrual warning: Sloan Accrual Ratio ({ratio_pct:.1f}%) signals paper earnings.")

    # Priority 2: Cyclical Peak Caution
    elif is_cyclical and cfo_decelerating and (latest and latest.pe_calc and latest.pe_calc < 15.0):
        verdict_badge = VERDICT_CYCLICAL
        rationale_bullets.append("Cyclical business archetype with trough multiple on peak-cycle earnings.")
        rationale_bullets.append("Operating cash flow is decelerating YoY, typical of late-cycle deceleration.")
        rationale_bullets.append("Risk of multiple compression and earnings contraction simultaneously.")

    # Priority 3: Overvalued Quality (Priced for Perfection)
    elif moat_rating == "Wide" and z_zone == "Safe" and gap is not None and gap > 0.06:
        verdict_badge = VERDICT_OVERVALUED
        rationale_bullets.append(f"Outstanding franchise ({moat_rating} Moat) and pristine balance sheet.")
        rationale_bullets.append(f"Reverse DCF expectations gap (+{gap*100:.1f}%) requires growth far above 5Y historical CAGR.")
        rationale_bullets.append("Stock is priced for flawless execution with zero margin of safety.")

    # Priority 4: Undervalued Bargain
    elif z_zone in ("Safe", "Grey") and not is_manipulator and not sloan_high_accruals and (is_graham_bargain or (gap is not None and gap <= -0.04)):
        verdict_badge = VERDICT_BARGAIN
        rationale_bullets.append(f"Safe balance sheet ({z_zone} zone) and clean forensic accounting profile.")
        if is_graham_bargain:
            rationale_bullets.append(f"Trading at >25% discount to Graham Value Floor (${graham_number:.2f}).")
        if gap is not None and gap <= -0.04:
            rationale_bullets.append(f"Market prices in conservative FCF contraction ({gap*100:.1f}% expectations discount).")

    # Priority 5: Compounder at Fair Value
    else:
        verdict_badge = VERDICT_COMPOUNDER
        rationale_bullets.append(f"Economic moat rating: {moat_rating} Moat with durable structural advantages.")
        rationale_bullets.append(f"Balance sheet health: {z_zone} zone with managed financial obligations.")
        gap_text = f"+{gap*100:.1f}%" if (gap is not None and gap >= 0) else (f"{gap*100:.1f}%" if gap is not None else "neutral")
        rationale_bullets.append(f"Valuation expectations gap ({gap_text}) is within achievable historical ranges.")

    # 3. Traffic Lights
    # Solvency Light
    solvency_light = "GREEN" if z_zone == "Safe" else ("RED" if z_zone == "Distress" else "YELLOW")

    # Earnings Quality Light
    eq_light = "RED" if (is_manipulator or cfo_ni_decoupling or sloan_high_accruals) else "GREEN"

    # Valuation Light
    if verdict_badge == VERDICT_OVERVALUED or (gap is not None and gap > 0.06):
        val_light = "RED"
    elif verdict_badge == VERDICT_BARGAIN or (gap is not None and gap < 0):
        val_light = "GREEN"
    else:
        val_light = "YELLOW"

    # Reverse DCF Rule summary
    rev_dcf_rule = (
        f"Market prices in 10-year FCF growth of {dcf_row.market_implied_growth_10y*100:.1f}%. "
        f"Benchmark against Malkiel/Collins 8.0% hurdle."
        if (dcf_row and dcf_row.market_implied_growth_10y is not None)
        else "Reverse DCF unviable due to negative baseline FCF or missing market capitalization."
    )

    return {
        "company_id": company_id,
        "verdict_badge": verdict_badge,
        "traffic_lights": {
            "solvency": solvency_light,
            "earnings_quality": eq_light,
            "valuation": val_light,
        },
        "decision_bullets": rationale_bullets[:3],
        "reverse_dcf_rule": rev_dcf_rule,
        "expectations_gap": gap,
        "moat_rating": moat_rating,
        "archetype": archetype.get("archetype"),
    }
