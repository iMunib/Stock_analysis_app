"""Phase 3 scoring service: load rows, compute, persist (idempotent).

Two passes: (1) compute score results for every company, (2) rank inside peer
sets by composite (NULL composites excluded from ranking, rank 1 = best).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot, HalalFlag, Score
from app.services.halal import evaluate_halal
from app.services.scoring import (
    METHOD_VERSION,
    build_peer_sets,
    peer_values_for,
    score_company,
)


def snapshot_dict(snap: FinancialSnapshot | None) -> dict:
    """FinancialSnapshot ORM row -> plain dict of scoring/research fields."""
    if snap is None:
        return {}
    return {
        "revenue": snap.revenue,
        "net_income": snap.net_income,
        "diluted_eps": snap.diluted_eps,
        "gross_profit": snap.gross_profit,
        "operating_cash_flow": snap.operating_cash_flow,
        "capex": snap.capex,
        "fcf_calc": snap.fcf_calc,
        "netdebt_calc": snap.netdebt_calc,
        "total_debt": snap.total_debt,
        "book_equity": snap.book_equity,
        "cash_st_investments": snap.cash_st_investments,
        "total_assets": snap.total_assets,
        "total_liabilities": snap.total_liabilities,
        "ebit": snap.ebit,
        "ebitda": snap.ebitda,
        "interest_expense": snap.interest_expense,
        "roe_calc": snap.roe_calc,
        "roa_calc": snap.roa_calc,
        "fcfmargin_calc": snap.fcfmargin_calc,
        "grossmargin_calc": snap.grossmargin_calc,
        "pe_calc": snap.pe_calc,
        "pb_calc": snap.pb_calc,
        "ev_to_ebitda_calc": snap.ev_to_ebitda_calc,
        "price": snap.price,
        "market_cap": snap.market_cap,
        "shares_snapshot": snap.shares_snapshot,
        "price_asof": snap.price_asof,
        "accounts_receivable": getattr(snap, "accounts_receivable", None),
        "inventory": getattr(snap, "inventory", None),
        "current_assets": getattr(snap, "current_assets", None),
        "current_liabilities": getattr(snap, "current_liabilities", None),
        "ppe_net": getattr(snap, "ppe_net", None),
        "retained_earnings": getattr(snap, "retained_earnings", None),
        "stock_based_compensation": getattr(snap, "stock_based_compensation", None),
        "interest_income": getattr(snap, "interest_income", None),
        "cet1_ratio": snap.cet1_ratio,
        "total_capital_ratio": snap.total_capital_ratio,
        "leverage_ratio": snap.leverage_ratio,
        "nim_fy2025": snap.nim_fy2025,
        "nim_q4_2025": snap.nim_q4_2025,
        "efficiency_ratio": snap.efficiency_ratio,
        "roaa": snap.roaa,
        "as_of_date": snap.as_of_date.isoformat() if snap.as_of_date else None,
        "source": snap.source,
    }


def load_universe(db: Session, company_id: str | None = None, include_deleted: bool = False) -> list[dict]:
    comp_stmt = select(Company)
    if not include_deleted:
        comp_stmt = comp_stmt.where(Company.is_deleted == False)
    if company_id:
        comp_stmt = comp_stmt.where(Company.company_id == company_id)
    companies = db.execute(comp_stmt).scalars().all()

    snaps = db.execute(
        select(FinancialSnapshot).where(FinancialSnapshot.period_type == "FY")
    ).scalars().all()
    by_company: dict[str, list[FinancialSnapshot]] = {}
    for s in snaps:
        by_company.setdefault(s.company_id, []).append(s)

    out = []
    for c in companies:
        rows = by_company.get(c.company_id, [])
        dated = sorted((r for r in rows if r.fiscal_year is not None), key=lambda r: r.fiscal_year, reverse=True)
        seed_rows = [r for r in rows if r.fiscal_year is None]
        current = dated[0] if dated else (seed_rows[0] if seed_rows else None)
        prior = dated[1] if len(dated) > 1 else None
        out.append({
            "company_id": c.company_id,
            "name": c.name,
            "gics_sector": c.gics_sector,
            "custom_industry_sheet": c.custom_industry_sheet,
            "currency": c.currency,
            "snapshot": snapshot_dict(current),
            "prior": snapshot_dict(prior),
            "history": [{**snapshot_dict(r), "fiscal_year": r.fiscal_year} for r in rows],
            "seed_snapshot": snapshot_dict(seed_rows[0] if seed_rows else None),
        })
    return out


def enrich_with_seed(cur: dict, seed: dict | None) -> dict:
    """NULL-fill a (provider) current snapshot from the owner seed row.

    Owner values always win: only fields that are NULL in `cur` and non-NULL in
    `seed` are copied. Used at score time so provider history rows keep the
    workbook's derived ratio/price coverage. Storage is never modified.
    """
    out = dict(cur)
    for k, v in (seed or {}).items():
        if out.get(k) is None and v is not None:
            out[k] = v
    return out


def recompute(db: Session, company_id: str | None = None) -> dict:
    full_universe = load_universe(db)
    members, meta = build_peer_sets(full_universe)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    target_universe = [c for c in full_universe if c["company_id"] == company_id] if company_id else full_universe

    results: dict[str, dict] = {}
    errors: list[str] = []

    # Also load existing scores for fast peer rank calculation if running single company
    existing_scores: dict[str, float | None] = {}
    if company_id:
        for r_cid, r_comp in db.execute(select(Score.company_id, Score.composite)).all():
            existing_scores[r_cid] = r_comp

    for company in target_universe:
        cid = company["company_id"]
        try:
            # Peer value lists EXCLUDE the company itself: percentile of the
            # cheapest/best maps to the full 0..10 range (spec: cheapest = 10).
            peers = [m for m in (members.get(cid) or []) if m["company_id"] != cid]
            peer_vals = peer_values_for(peers)
            # Read-time enrichment: provider history rows lack the derived ratio /
            # price columns that only the owner seed row carries. NULL-fill the
            # current snapshot from the seed row (never the reverse, owner values
            # always win) so scored companies keep full coverage.
            cur_row = enrich_with_seed(company["snapshot"], company.get("seed_snapshot"))
            # Phase 10 A: growth uses only sanitized FY years (suspect scale rows excluded).
            from app.services.history_sanity import sanitize_history

            _sani = sanitize_history(company["history"])
            results[cid] = score_company(cur_row, company["prior"], _sani["rows_for_growth"], peer_vals)
        except Exception as exc:  # noqa: BLE001 - one bad company must not kill the run
            errors.append(f"{cid}: {exc.__class__.__name__}: {exc}")

    # Peer ranks: best composite = 1; NULL composites excluded.
    ranks: dict[str, int | None] = {}
    for cid, result in results.items():
        if result["composite"] is None:
            ranks[cid] = None
            continue
        peers = members.get(cid) or []
        better = 0
        for p in peers:
            pid = p["company_id"]
            pc = results.get(pid, {}).get("composite") if not company_id else existing_scores.get(pid)
            if pc is not None and pc > result["composite"]:
                better += 1
        ranks[cid] = better + 1

    scored = insufficient = 0
    for company in target_universe:
        cid = company["company_id"]
        result = results.get(cid)
        if result is None:
            continue
        ptype, pn = meta.get(cid, ("broad_peer_set", 1))

        row = db.get(Score, cid)
        if row is None:
            row = Score(company_id=cid)
            db.add(row)
        row.as_of_fy = max(
            (h["fiscal_year"] for h in company["history"] if h.get("fiscal_year") is not None),
            default=None,
        )
        row.composite = result["composite"]
        row.quality = result["pillars"]["quality"]
        row.value = result["pillars"]["value"]
        row.growth = result["pillars"]["growth"]
        row.risk = result["pillars"]["risk"]
        row.coverage = result["coverage"]
        row.signal = result["signal"]
        row.peer_set_type = ptype
        row.peer_n = pn
        row.peer_rank = ranks.get(cid)
        row.method_version = METHOD_VERSION
        row.computed_at = now
        row.inputs_json = {
            "pillars": result["pillars"],
            "penalty": result["penalty"],
            "details": result["details"],
            "disclaimer": result["disclaimer"],
        }

        halal = evaluate_halal(company, company["snapshot"])
        hf = db.get(HalalFlag, cid)
        if hf is None:
            hf = HalalFlag(company_id=cid)
            db.add(hf)
        hf.status = halal["status"]
        hf.tests_json = halal["tests"]
        hf.method = halal["method"]
        hf.computed_at = halal["computed_at"]

        if result["composite"] is None:
            insufficient += 1
        else:
            scored += 1

    db.commit()

    # Workstream 2: Materialize sector summary cache when full universe is recomputed
    if company_id is None:
        from app.services.sector_cache import materialize_sector_cache
        try:
            materialize_sector_cache(db)
        except Exception:  # noqa: BLE001
            pass

        # Workstream 5: Materialize sector percentile matrix
        from app.services.percentile_engine import compute_and_materialize_percentiles
        try:
            compute_and_materialize_percentiles(db)
        except Exception:  # noqa: BLE001
            pass

    return {
        "companies_processed": len(target_universe),
        "scored": scored,
        "insufficient_data": insufficient,
        "errors": errors[:20],
        "method_version": METHOD_VERSION,
        "computed_at": now.isoformat(),
    }


def recompute_universe(db: Session | None = None) -> dict:
    """Full universe scoring recompute entry point (Master Directive WS1/WS2)."""
    if db is None:
        from app.db import SessionLocal
        with SessionLocal() as session:
            return recompute(session, company_id=None)
    return recompute(db, company_id=None)

