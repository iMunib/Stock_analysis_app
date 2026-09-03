"""Koyfin-style Sector Percentile Matrix Engine (Master Directive WS5).

Computes 0-100 percentile ranks within same-currency sector peer groups across
8 core fundamental and valuation ratios:
1. P/E Ratio (lower is better -> inverted)
2. EV/EBITDA (lower is better -> inverted)
3. P/B Ratio (lower is better -> inverted)
4. ROE (higher is better)
5. ROIC / Penman RNOA (higher is better)
6. FCF Margin (higher is better)
7. Net Debt / EBITDA (lower is better -> inverted)
8. Total Shareholder Yield (higher is better)

Materializes ranks into `scores.percentiles_json` during universe scoring.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialPenmanAnalysis, FinancialSnapshot, Score
from app.services.capital_return_engine import compute_shareholder_yield
from app.services.scoring_service import enrich_with_seed, snapshot_dict


def compute_and_materialize_percentiles(db: Session) -> dict[str, dict[str, float | None]]:
    """Calculates and stores sector percentile matrix for all scored companies."""
    # 1. Load companies and their latest/seed snapshots
    companies = db.execute(select(Company).where(Company.is_deleted == False)).scalars().all()
    if not companies:
        return {}

    comp_map = {c.company_id: c for c in companies}
    all_snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.period_type == "FY")
    ).scalars().all()

    by_comp: dict[str, list[FinancialSnapshot]] = {}
    for sp in all_snaps:
        by_comp.setdefault(sp.company_id, []).append(sp)

    # Latest Penman analysis rows
    penman_rows = db.execute(select(FinancialPenmanAnalysis)).scalars().all()
    penman_by_comp: dict[str, FinancialPenmanAnalysis] = {}
    for pr in penman_rows:
        if pr.company_id not in penman_by_comp or (pr.fiscal_year is not None and (penman_by_comp[pr.company_id].fiscal_year is None or pr.fiscal_year > (penman_by_comp[pr.company_id].fiscal_year or 0))):
            penman_by_comp[pr.company_id] = pr

    # Build metric row per company
    company_metrics: dict[str, dict[str, Any]] = {}
    for c in companies:
        cid = c.company_id
        c_snaps = by_comp.get(cid, [])
        dated = sorted((r for r in c_snaps if r.fiscal_year is not None), key=lambda r: r.fiscal_year, reverse=True)
        seed_row = next((r for r in c_snaps if r.fiscal_year is None), None)
        cur_snap = dated[0] if dated else seed_row
        enriched = enrich_with_seed(snapshot_dict(cur_snap), snapshot_dict(seed_row))

        # 1. P/E
        pe = enriched.get("pe_calc")
        # 2. EV/EBITDA
        ev_ebitda = enriched.get("ev_to_ebitda_calc")
        # 3. P/B
        pb = enriched.get("pb_calc")
        # 4. ROE
        roe = enriched.get("roe_calc")
        # 5. ROIC / Penman RNOA
        p_row = penman_by_comp.get(cid)
        rnoa = p_row.rnoa if p_row and p_row.rnoa is not None else None
        roic = rnoa if rnoa is not None else enriched.get("roaa")
        # 6. FCF Margin
        fcf_m = enriched.get("fcfmargin_calc")
        # 7. Net Debt / EBITDA
        ebitda = enriched.get("ebitda")
        net_debt = enriched.get("netdebt_calc")
        nd_ebitda = None
        if net_debt is not None and ebitda is not None and ebitda > 0:
            nd_ebitda = round(net_debt / ebitda, 2)
        elif net_debt is not None and net_debt <= 0:
            nd_ebitda = 0.0  # net cash is safest
        # 8. Total Shareholder Yield
        try:
            tsy_res = compute_shareholder_yield(db, cid)
            tsy = tsy_res.get("total_shareholder_yield_pct")
        except Exception:  # noqa: BLE001
            tsy = None

        sheet = c.custom_industry_sheet or c.gics_sector or "General"
        peer_key = f"{sheet}_{c.currency.upper()}"

        company_metrics[cid] = {
            "peer_key": peer_key,
            "currency": c.currency.upper(),
            "pe_ratio": pe,
            "ev_to_ebitda": ev_ebitda,
            "pb_ratio": pb,
            "roe": roe,
            "roic_or_rnoa": roic,
            "fcf_margin": fcf_m,
            "net_debt_to_ebitda": nd_ebitda,
            "total_shareholder_yield": tsy,
        }

    # Group companies by peer_key
    peers_by_key: dict[str, list[str]] = {}
    for cid, m in company_metrics.items():
        peers_by_key.setdefault(m["peer_key"], []).append(cid)

    # Metrics configuration: key -> inverted (lower is better)
    METRICS_CONFIG = {
        "pe_ratio": True,
        "ev_to_ebitda": True,
        "pb_ratio": True,
        "roe": False,
        "roic_or_rnoa": False,
        "fcf_margin": False,
        "net_debt_to_ebitda": True,
        "total_shareholder_yield": False,
    }

    # Calculate percentile ranks
    out_percentiles: dict[str, dict[str, float | None]] = {}

    for peer_key, cids in peers_by_key.items():
        for metric_name, inverted in METRICS_CONFIG.items():
            valid_pairs = [
                (cid, company_metrics[cid][metric_name])
                for cid in cids
                if company_metrics[cid][metric_name] is not None
            ]
            total_valid = len(valid_pairs)

            for cid, val in valid_pairs:
                if total_valid <= 1:
                    pct = 50.0  # single-company peer baseline
                else:
                    if inverted:
                        # Lower is better: peers with higher values are "worse"
                        worse_count = sum(1 for _, pval in valid_pairs if pval > val)
                    else:
                        # Higher is better: peers with lower values are "worse"
                        worse_count = sum(1 for _, pval in valid_pairs if pval < val)
                    pct = round((worse_count / (total_valid - 1)) * 100.0, 1)

                out_percentiles.setdefault(cid, {})[metric_name] = pct

    # Materialize into Score rows
    for cid, pcts in out_percentiles.items():
        score = db.get(Score, cid)
        if score is not None:
            score.percentiles_json = pcts

    db.commit()
    return out_percentiles
