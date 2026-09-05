"""Pat Dorsey 4-Moat Heuristic Engine (Phase 2 Master Directive).

Evaluates the 4 structural sources of economic moats:
1. High Switching Costs (Sustained Gross Margin > 60%, sticky customer relationships)
2. Network Effects (Accelerating revenue growth with SG&A operational leverage)
3. Cost Advantage (Low SG&A-to-gross-profit ratio < 35%, scalable low-cost production)
4. Intangible Assets (Pricing power: gross margin expansion or sustained > 50% with high ROE/ROIC)

Classifies overall moat into:
- Wide Moat (3-4 structural pillars + superior returns on capital)
- Narrow Moat (1-2 structural pillars)
- None (Commoditized / lacking durable competitive advantages)
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot


def compute_economic_moat(db: Session, company_id: str) -> dict[str, Any]:
    """Evaluates the 4 Dorsey economic moat sources and classifies Wide/Narrow/None."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    snaps = db.execute(
        select(FinancialSnapshot)
        .where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
        .order_by(FinancialSnapshot.fiscal_year.asc().nullslast())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    seed = [s for s in snaps if s.fiscal_year is None]
    snaps_to_use = dated if len(dated) >= 2 else (dated + seed if dated else seed)

    if not snaps_to_use:
        return {
            "company_id": company_id,
            "moat_rating": "None",
            "score": 0,
            "sources": {},
            "rationale": "Insufficient financial statements to evaluate economic moat.",
        }

    latest = snaps_to_use[-1]
    earliest = snaps_to_use[0]

    rev = latest.revenue or 1.0
    gp = latest.gross_profit or (latest.revenue * 0.4 if latest.revenue else 0.0)
    ebit = latest.ebit or 0.0
    gm = latest.grossmargin_calc or (gp / rev if rev > 0 else 0.0)
    op_margin = (ebit / rev) if rev > 0 else 0.0
    roe = latest.roe_calc or 0.0

    # SG&A to Gross Profit ratio
    sga = getattr(latest, "sga_expense", None) or max(0.0, gp - ebit)
    sga_to_gp = (sga / gp) if gp > 0 else 1.0

    # Margin trajectory over available horizon
    gm_earliest = earliest.grossmargin_calc or ((earliest.gross_profit or 0.0) / earliest.revenue if earliest.revenue else gm)
    pricing_power = (gm >= gm_earliest - 0.02) and (gm > 0.40)

    # 1. High Switching Costs
    has_switching_costs = gm >= 0.55 and op_margin >= 0.15
    switching_costs_rationale = (
        f"High gross margin ({gm*100:.1f}%) and operating margin ({op_margin*100:.1f}%) indicate substantial customer switching friction."
        if has_switching_costs
        else "Gross margin below 55% threshold; commoditized or price-sensitive switching profile."
    )

    # 2. Network Effects
    years = max(1, (latest.fiscal_year or 0) - (earliest.fiscal_year or 0)) if (latest.fiscal_year and earliest.fiscal_year) else 1
    rev_cagr = ((latest.revenue / earliest.revenue) ** (1.0 / years) - 1.0) * 100.0 if (latest.revenue and earliest.revenue and latest.revenue > 0 and earliest.revenue > 0 and years > 0) else 0.0
    has_network_effects = rev_cagr >= 12.0 and sga_to_gp < 0.65
    network_effects_rationale = (
        f"Double-digit expansion ({rev_cagr:.1f}% CAGR) with operational leverage indicates self-reinforcing network dynamics."
        if has_network_effects
        else "Lacks viral top-line acceleration or demonstrates high customer acquisition drag."
    )

    # 3. Cost Advantage
    has_cost_advantage = sga_to_gp <= 0.40 and roe >= 0.15
    cost_advantage_rationale = (
        f"Low overhead-to-gross-profit ratio ({sga_to_gp*100:.1f}%) and high ROE ({roe*100:.1f}%) signify durable cost leadership."
        if has_cost_advantage
        else "Cost structure in line with or higher than median industrial competitors."
    )

    # 4. Intangible Assets (Brand, Patents, Regulatory licenses)
    has_intangibles = pricing_power and (roe >= 0.18 or gm >= 0.50)
    intangibles_rationale = (
        f"Sustained pricing power ({gm*100:.1f}% gross margin) and superior capital return ({roe*100:.1f}% ROE) reflect strong intangibles/brand."
        if has_intangibles
        else "Lacks distinct brand premium or patented pricing power."
    )

    sources = {
        "switching_costs": {"present": has_switching_costs, "rationale": switching_costs_rationale},
        "network_effects": {"present": has_network_effects, "rationale": network_effects_rationale},
        "cost_advantage": {"present": has_cost_advantage, "rationale": cost_advantage_rationale},
        "intangible_assets": {"present": has_intangibles, "rationale": intangibles_rationale},
    }

    moat_score = sum(1 for s in sources.values() if s["present"])

    if moat_score >= 3 and roe >= 0.12:
        moat_rating = "Wide"
        summary_rationale = "Exceptional structural protection across multiple economic moat dimensions."
    elif moat_score >= 1:
        moat_rating = "Narrow"
        summary_rationale = "Moderate structural competitive advantage in specific operating areas."
    else:
        moat_rating = "None"
        summary_rationale = "No durable economic moat detected; competitive pressures erode excess returns."

    return {
        "company_id": company_id,
        "moat_rating": moat_rating,
        "moat_score": moat_score,
        "sources": sources,
        "rationale": summary_rationale,
    }
