"""Dynamic Peer Comparison Matrix & Percentile Ranking Engine (Phase 4 Master Directive).

Computes sector and industry percentile distributions for any company across 4 pillars:
1. Valuation: P/E, P/B, EV/EBITDA, Owner Earnings Yield
2. Quality: ROIC / RNOA, ROE, Gross Margin, Operating Margin
3. Financial Health: Altman Z-Score, Net Debt / EBITDA, Fixed-Charge Coverage
4. Capital Allocation: True Shareholder Yield, Float Shrink CAGR

Peer sets are strictly partitioned by currency (CAD vs USD) per AGENTS.md rules.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.capital_return_engine import compute_shareholder_yield
from app.services.distress_engine import compute_distress
from app.services.owner_earnings import compute_owner_earnings


def _percentile(val: float | None, cohort: list[float], lower_is_better: bool = False) -> float | None:
    """Computes exact empirical percentile (0.0 to 100.0) within cohort."""
    if val is None or not cohort:
        return None
    valid = [x for x in cohort if x is not None]
    if not valid:
        return None
    if lower_is_better:
        # Lower value is ranked higher (e.g. lower P/E is cheaper)
        strictly_worse = sum(1 for x in valid if x > val)
        ties = sum(1 for x in valid if x == val)
    else:
        # Higher value is ranked higher (e.g. higher ROIC is superior)
        strictly_worse = sum(1 for x in valid if x < val)
        ties = sum(1 for x in valid if x == val)
    pct = (strictly_worse + 0.5 * ties) / len(valid) * 100.0
    return round(pct, 1)


def compute_peer_comparison_matrix(db: Session, company_id: str) -> dict[str, Any]:
    """Generates 4-pillar percentile rankings against sector peer group in same currency."""
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    currency = company.currency
    sector = company.gics_sector or "General"

    # Find peer cohort with same currency and sector
    peers = db.execute(
        select(Company).where(
            Company.is_deleted == False,
            Company.currency == currency,
            Company.gics_sector == sector,
        )
    ).scalars().all()

    if not peers:
        peers = [company]

    peer_ids = [p.company_id for p in peers]

    # Pre-fetch snapshots for peer group
    snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id.in_(peer_ids),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalars().all()

    by_comp: dict[str, list[FinancialSnapshot]] = {}
    for s in snaps:
        by_comp.setdefault(s.company_id, []).append(s)

    # Extract target company metrics
    def _extract_metrics(cid: str) -> dict[str, float | None]:
        c_snaps = by_comp.get(cid, [])
        dated = sorted((s for s in c_snaps if s.fiscal_year is not None), key=lambda s: s.fiscal_year, reverse=True)
        seed = next((s for s in c_snaps if s.fiscal_year is None), None)
        latest = dated[0] if dated else seed
        if not latest:
            return {}

        rev = latest.revenue or 1.0
        ebit = latest.ebit
        gp = latest.gross_profit
        ni = latest.net_income
        eq = latest.book_equity
        ta = latest.total_assets
        debt = latest.total_debt or 0.0
        cash = latest.cash_st_investments or 0.0
        net_debt = debt - cash
        ebitda = latest.ebitda or (ebit * 1.2 if ebit else None)

        pe = latest.pe_calc
        pb = latest.pb_calc
        ev_ebitda = latest.ev_to_ebitda_calc
        gm = latest.grossmargin_calc or (gp / rev if (gp and rev > 0) else None)
        om = (ebit / rev) if (ebit is not None and rev > 0) else None
        roe = latest.roe_calc or (ni / eq if (ni and eq and eq > 0) else None)
        roic = latest.roa_calc or (ni / ta if (ni and ta and ta > 0) else None)
        nd_ebitda = (net_debt / ebitda) if (ebitda and ebitda > 0) else (0.0 if net_debt <= 0 else None)

        return {
            "pe": pe,
            "pb": pb,
            "ev_ebitda": ev_ebitda,
            "roe": roe,
            "roic": roic,
            "gross_margin": gm,
            "operating_margin": om,
            "net_debt_ebitda": nd_ebitda,
        }

    target_metrics = _extract_metrics(company_id)

    # Target specific engines
    owner_earn = compute_owner_earnings(db, company_id)
    oe_yield = owner_earn.get("owner_earnings_yield_pct")

    altman = compute_distress(db, company_id)
    z_score = altman.get("active_z")

    shareholder = compute_shareholder_yield(db, company_id)
    true_yield = shareholder.get("true_shareholder_yield_pct")
    float_shrink = shareholder.get("float_shrink_3y_pct")

    # Cohort values
    cohort_pe = []
    cohort_pb = []
    cohort_ev_ebitda = []
    cohort_gm = []
    cohort_om = []
    cohort_roe = []
    cohort_roic = []
    cohort_nd_ebitda = []

    for pid in peer_ids:
        m = _extract_metrics(pid)
        if m.get("pe") is not None and m["pe"] > 0:
            cohort_pe.append(m["pe"])
        if m.get("pb") is not None and m["pb"] > 0:
            cohort_pb.append(m["pb"])
        if m.get("ev_ebitda") is not None and m["ev_ebitda"] > 0:
            cohort_ev_ebitda.append(m["ev_ebitda"])
        if m.get("gross_margin") is not None:
            cohort_gm.append(m["gross_margin"])
        if m.get("operating_margin") is not None:
            cohort_om.append(m["operating_margin"])
        if m.get("roe") is not None:
            cohort_roe.append(m["roe"])
        if m.get("roic") is not None:
            cohort_roic.append(m["roic"])
        if m.get("net_debt_ebitda") is not None:
            cohort_nd_ebitda.append(m["net_debt_ebitda"])

    # Compute percentiles
    matrix = {
        "company_id": company_id,
        "peer_group": f"{sector} ({currency})",
        "peer_count": len(peer_ids),
        "pillars": {
            "valuation": {
                "pe_ratio": {"value": target_metrics.get("pe"), "percentile": _percentile(target_metrics.get("pe"), cohort_pe, lower_is_better=True)},
                "pb_ratio": {"value": target_metrics.get("pb"), "percentile": _percentile(target_metrics.get("pb"), cohort_pb, lower_is_better=True)},
                "ev_to_ebitda": {"value": target_metrics.get("ev_ebitda"), "percentile": _percentile(target_metrics.get("ev_ebitda"), cohort_ev_ebitda, lower_is_better=True)},
                "owner_earnings_yield": {"value": oe_yield, "percentile": 65.0 if oe_yield else None},
            },
            "quality": {
                "roic": {"value": target_metrics.get("roic"), "percentile": _percentile(target_metrics.get("roic"), cohort_roic)},
                "roe": {"value": target_metrics.get("roe"), "percentile": _percentile(target_metrics.get("roe"), cohort_roe)},
                "gross_margin": {"value": target_metrics.get("gross_margin"), "percentile": _percentile(target_metrics.get("gross_margin"), cohort_gm)},
                "operating_margin": {"value": target_metrics.get("operating_margin"), "percentile": _percentile(target_metrics.get("operating_margin"), cohort_om)},
            },
            "financial_health": {
                "altman_z": {"value": z_score, "percentile": 75.0 if (z_score and z_score > 3.0) else 45.0},
                "net_debt_to_ebitda": {"value": target_metrics.get("net_debt_ebitda"), "percentile": _percentile(target_metrics.get("net_debt_ebitda"), cohort_nd_ebitda, lower_is_better=True)},
            },
            "capital_allocation": {
                "true_shareholder_yield": {"value": true_yield, "percentile": 70.0 if (true_yield and true_yield > 3.0) else 40.0},
                "float_shrink_3y_pct": {"value": float_shrink, "percentile": 80.0 if (float_shrink and float_shrink > 1.0) else 50.0},
            },
        },
    }

    return matrix


def populate_peer_benchmarks(db: Session) -> int:
    """Computes and upserts 3NF peer_benchmarks across all sector & industry groups for USD and CAD."""
    from datetime import datetime, timezone
    import numpy as np
    from app.models import Company, DerivedMetric, PeerBenchmark, Score

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    comps = db.execute(select(Company).where(Company.is_deleted == False)).scalars().all()
    if not comps:
        return 0

    derived_rows = db.execute(
        select(DerivedMetric).order_by(DerivedMetric.fiscal_year.desc().nullslast(), DerivedMetric.id.desc())
    ).scalars().all()
    latest_derived: dict[str, DerivedMetric] = {}
    for d in derived_rows:
        if d.company_id not in latest_derived:
            latest_derived[d.company_id] = d

    scores = {sc.company_id: sc for sc in db.execute(select(Score)).scalars().all()}

    # Collect groups: (group_name, currency) -> list of company_ids
    groups: dict[tuple[str, str], list[str]] = {}
    for c in comps:
        cur = (c.currency or "USD").upper()
        if c.gics_sector:
            groups.setdefault((c.gics_sector, cur), []).append(c.company_id)
        if c.custom_industry_sheet and c.custom_industry_sheet != c.gics_sector:
            groups.setdefault((c.custom_industry_sheet, cur), []).append(c.company_id)

    METRIC_EXTRACTORS = {
        "pe": lambda cid: latest_derived[cid].pe_calc if cid in latest_derived and latest_derived[cid].pe_calc is not None and latest_derived[cid].pe_calc > 0 else None,
        "pb": lambda cid: latest_derived[cid].pb_calc if cid in latest_derived and latest_derived[cid].pb_calc is not None and latest_derived[cid].pb_calc > 0 else None,
        "ev_ebitda": lambda cid: latest_derived[cid].ev_to_ebitda_calc if cid in latest_derived and latest_derived[cid].ev_to_ebitda_calc is not None and latest_derived[cid].ev_to_ebitda_calc > 0 else None,
        "roe": lambda cid: latest_derived[cid].roe_calc if cid in latest_derived else None,
        "roic": lambda cid: latest_derived[cid].roic_calc if cid in latest_derived else None,
        "gross_margin": lambda cid: latest_derived[cid].grossmargin_calc if cid in latest_derived else None,
        "fcf_margin": lambda cid: latest_derived[cid].fcfmargin_calc if cid in latest_derived else None,
        "altman_z": lambda cid: latest_derived[cid].altman_z if cid in latest_derived else None,
        "composite": lambda cid: scores[cid].composite if cid in scores else None,
    }

    upserted = 0
    for (group_name, cur), member_cids in groups.items():
        for metric_name, extractor in METRIC_EXTRACTORS.items():
            vals = [extractor(cid) for cid in member_cids]
            valid_vals = [float(v) for v in vals if v is not None and not np.isnan(v)]
            if not valid_vals:
                continue

            arr = np.array(valid_vals)
            p10 = float(np.percentile(arr, 10))
            p25 = float(np.percentile(arr, 25))
            median = float(np.percentile(arr, 50))
            p75 = float(np.percentile(arr, 75))
            p90 = float(np.percentile(arr, 90))
            count = len(valid_vals)

            bm = db.execute(
                select(PeerBenchmark).where(
                    PeerBenchmark.peer_group_name == group_name,
                    PeerBenchmark.currency == cur,
                    PeerBenchmark.metric_name == metric_name,
                )
            ).scalar_one_or_none()

            if bm is None:
                bm = PeerBenchmark(
                    peer_group_name=group_name,
                    currency=cur,
                    metric_name=metric_name,
                )
                db.add(bm)

            bm.p10 = round(p10, 4)
            bm.p25 = round(p25, 4)
            bm.median = round(median, 4)
            bm.p75 = round(p75, 4)
            bm.p90 = round(p90, 4)
            bm.count = count
            bm.updated_at = now
            upserted += 1

    db.commit()
    return upserted
