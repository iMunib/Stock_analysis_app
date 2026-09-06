"""Automated Data Pulling & Calculation Pipeline.

Orchestrates:
1. Dynamic statement fetching via free APIs (SEC EDGAR for US, Yahoo Finance for CA & prices).
2. Statement ingestion into 3NF normalized schema (financial_statements, derived_metrics, financial_snapshots).
3. Live price, shares, and market cap extraction.
4. Comprehensive metric calculation:
   - ROIC and NOPAT (via ttm_engine)
   - Gross Margin, FCF Margin, Trailing P/E, P/B, EV/EBITDA, Net Debt (via fundamentals)
   - Multi-year Growth CAGRs (Revenue CAGR, EPS CAGR, 5Y FCF CAGR)
   - Altman Z-Score & Distress Zone (via distress_engine)
   - Beneish M-Score & Manipulation Risk (via beneish_engine)
   - Penman Reformulation & RNOA/FLEV Spread (via penman_engine)
   - Reverse DCF Market-Implied Growth & Expectations Gap (via valuation_engine)
   - Deterministic 4-Pillar Scoring & AAOIFI Halal Assessment (via scoring_service)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Company,
    DerivedMetric,
    FinancialSnapshot,
    FinancialSnapshotTTM,
    FinancialStatement,
    Score,
    ValuationReverseDCF,
)
from app.providers.registry import ProviderRegistry
from app.services.archetype_engine import _calc_cagr
from app.services.beneish_engine import compute_beneish_m_score
from app.services.distress_engine import compute_distress
from app.services.fundamentals import compute_snapshot_ratios, sync_snapshot_to_3nf
from app.services.ingest import get_or_create_company, ingest_price, ingest_statements
from app.services.mapping import MappingError, build_ref, resolve
from app.services.penman_engine import compute_and_store_penman
from app.services.scoring_service import recompute
from app.services.ttm_engine import compute_and_store_ttm
from app.services.valuation_engine import compute_and_store_reverse_dcf

logger = logging.getLogger("pipeline")


def run_company_pipeline(
    db: Session,
    query_or_company_id: str,
    refresh: bool = False,
    fetch_live: bool = True,
    recompute_score: bool = True,
) -> dict[str, Any]:
    """Execute complete data pull and calculation pipeline for a single company."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    registry = ProviderRegistry()

    # Step 1: Resolve company
    existing_company = db.get(Company, query_or_company_id)
    if existing_company is not None and not fetch_live:
        company = existing_company
        company_id = company.company_id
    else:
        try:
            res = resolve(query_or_company_id)
            ref = build_ref(res)
        except MappingError:
            if existing_company is None:
                raise
            ticker = existing_company.ticker or query_or_company_id.split(":")[1]
            t_query = ticker
            if (existing_company.country or "") == "CA" and not t_query.upper().endswith(".TO"):
                t_query = t_query + ".TO"
            res = resolve(t_query)
            ref = build_ref(res)

        company = get_or_create_company(
            db,
            ref.company_id,
            ref.ticker,
            ref.country,
            ref.currency,
            name=res.name,
        )
        if ref.cik and not company.cik:
            company.cik = ref.cik
        db.commit()
        company_id = ref.company_id

    statements_count = 0

    # Step 2: Fetch Live Statements & Price (if requested)
    if fetch_live:
        from app.services.mapping import yahoo_symbol_for
        from app.providers.base import CompanyRef
        query_sym = yahoo_symbol_for(company.ticker, company.country or "US")
        try:
            ref = build_ref(resolve(query_sym))
            if company.cik and not ref.cik:
                ref = CompanyRef(
                    company_id=ref.company_id,
                    ticker=ref.ticker,
                    country=ref.country,
                    currency=ref.currency,
                    yahoo_symbol=ref.yahoo_symbol,
                    cik=company.cik,
                )
            statements = registry.fetch_annual_statements(ref)
            ingest_statements(db, company, statements, refresh=refresh)
            statements_count = len(statements)
            db.commit()
        except Exception as exc:
            logger.warning("Statement fetch for %s: %s", company_id, exc)

        try:
            ref = build_ref(resolve(query_sym))
            if company.cik and not ref.cik:
                ref = CompanyRef(
                    company_id=ref.company_id,
                    ticker=ref.ticker,
                    country=ref.country,
                    currency=ref.currency,
                    yahoo_symbol=ref.yahoo_symbol,
                    cik=company.cik,
                )
            quote = registry.fetch_price(ref)
            ingest_price(db, company, quote)
            db.commit()
        except Exception as exc:
            logger.warning("Price fetch for %s: %s", company_id, exc)

    # Step 3: Synchronize snapshots and compute base ratios
    snaps = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id)
        .order_by(FinancialSnapshot.fiscal_year.desc().nullslast())
    ).scalars().all()

    for snap in snaps:
        compute_snapshot_ratios(snap, company)
        sync_snapshot_to_3nf(db, snap, company)
    db.commit()

    # Step 4: Multi-year Growth CAGRs calculation
    dated_snaps = sorted(
        [s for s in snaps if s.fiscal_year is not None],
        key=lambda s: s.fiscal_year,
    )
    rev_cagr_3y = None
    rev_cagr_5y = None
    eps_cagr_3y = None
    eps_cagr_5y = None

    if len(dated_snaps) >= 4:
        latest = dated_snaps[-1]
        t3 = dated_snaps[-4]
        rev_cagr_3y = _calc_cagr(t3.revenue, latest.revenue, 3)
        eps_cagr_3y = _calc_cagr(t3.diluted_eps, latest.diluted_eps, 3)

    if len(dated_snaps) >= 6:
        latest = dated_snaps[-1]
        t5 = dated_snaps[-6]
        rev_cagr_5y = _calc_cagr(t5.revenue, latest.revenue, 5)
        eps_cagr_5y = _calc_cagr(t5.diluted_eps, latest.diluted_eps, 5)

    # Step 5: TTM & ROIC
    ttm_row = None
    try:
        ttm_row = compute_and_store_ttm(db, company_id)
        db.commit()
    except Exception as exc:
        logger.warning("TTM computation failed for %s: %s", company_id, exc)

    # Step 6: Reverse DCF
    dcf_row = None
    try:
        dcf_row = compute_and_store_reverse_dcf(db, company_id)
        db.commit()
    except Exception as exc:
        logger.warning("Reverse DCF failed for %s: %s", company_id, exc)

    # Step 7: Penman Reformulation
    try:
        compute_and_store_penman(db, company_id)
        db.commit()
    except Exception as exc:
        logger.warning("Penman failed for %s: %s", company_id, exc)

    # Step 8: Altman Z-Score
    altman_val = None
    try:
        distress = compute_distress(db, company_id)
        altman_val = distress.get("active_z") or distress.get("z_score")
    except Exception as exc:
        logger.warning("Altman Z failed for %s: %s", company_id, exc)

    # Step 9: Beneish M-Score
    beneish_val = None
    try:
        beneish = compute_beneish_m_score(db, company_id)
        beneish_val = beneish.get("m_score")
    except Exception as exc:
        logger.warning("Beneish failed for %s: %s", company_id, exc)

    # Step 10: Update DerivedMetric records (both latest dated and seed) with all advanced metrics
    from app.services.exchange_resolver import get_exchange
    if company.ticker:
        resolved_ex = get_exchange(company.ticker, country=company.country or "US")
        if not company.exchange or company.exchange in ("US", "CA"):
            company.exchange = resolved_ex

    target_derived_rows = db.execute(
        select(DerivedMetric)
        .where(DerivedMetric.company_id == company_id)
        .order_by(DerivedMetric.fiscal_year.desc().nullslast(), DerivedMetric.id.desc())
    ).scalars().all()

    if not target_derived_rows:
        new_d = DerivedMetric(company_id=company_id)
        db.add(new_d)
        target_derived_rows = [new_d]

    latest_derived = target_derived_rows[0] if target_derived_rows else None
    seed_derived = next((r for r in target_derived_rows if r.fiscal_year is None), None)

    rows_to_update = set()
    if latest_derived is not None:
        rows_to_update.add(latest_derived)
    if seed_derived is not None:
        rows_to_update.add(seed_derived)

    for d_row in rows_to_update:
        if altman_val is not None:
            d_row.altman_z = float(altman_val)
        if beneish_val is not None:
            d_row.beneish_m_score = float(beneish_val)
        if ttm_row is not None:
            if ttm_row.roic is not None:
                d_row.roic_calc = ttm_row.roic
            if ttm_row.sloan_accrual_ratio is not None:
                d_row.sloan_accrual_ratio = ttm_row.sloan_accrual_ratio
        if dcf_row is not None and dcf_row.historical_5y_cagr is not None:
            d_row.fcf_cagr_5y = dcf_row.historical_5y_cagr
        if rev_cagr_3y is not None:
            d_row.revenue_cagr_3y = rev_cagr_3y
        if rev_cagr_5y is not None:
            d_row.revenue_cagr_5y = rev_cagr_5y
        if eps_cagr_3y is not None:
            d_row.eps_cagr_3y = eps_cagr_3y
        if eps_cagr_5y is not None:
            d_row.eps_cagr_5y = eps_cagr_5y
        d_row.computed_at = now

    db.commit()

    # Step 11: Recompute deterministic scoring & Halal flag (if single-company mode)
    score_res = None
    if recompute_score:
        score_res = recompute(db, company_id=company_id)
        db.commit()

    return {
        "company_id": company_id,
        "statements_fetched": statements_count,
        "altman_z": altman_val,
        "beneish_m_score": beneish_val,
        "roic": ttm_row.roic if ttm_row else None,
        "score": score_res,
        "status": "success",
    }


def populate_missing_metrics(
    db: Session,
    limit: int | None = None,
    fetch_live: bool = False,
    recompute_score: bool = True,
    force: bool = False,
) -> dict[str, int]:
    """Scans existing companies and computes any missing metrics in the DB."""
    from app.services.peer_engine import populate_peer_benchmarks

    cids = db.execute(select(Company.company_id)).scalars().all()
    populated = 0
    errors = 0

    # Collect companies that need population:
    candidates: list[str] = []
    for cid in cids:
        if force:
            candidates.append(cid)
            continue
        derived = db.execute(
            select(DerivedMetric)
            .where(DerivedMetric.company_id == cid)
            .order_by(DerivedMetric.fiscal_year.desc().nullslast(), DerivedMetric.id.desc())
            .limit(1)
        ).scalars().first()
        score = db.get(Score, cid)

        needs_calc = (
            derived is None
            or score is None
            or derived.computed_at is None
            or (derived.revenue_cagr_3y is None and derived.altman_z is None and derived.roic_calc is None)
        )
        if needs_calc:
            candidates.append(cid)

    target_cids = candidates if limit is None else candidates[:limit]

    for cid in target_cids:
        try:
            run_company_pipeline(db, cid, refresh=False, fetch_live=fetch_live, recompute_score=False)
            populated += 1
        except Exception as exc:
            logger.warning("Populate missing metrics for %s: %s", cid, exc)
            errors += 1

    # If any company was populated, recompute global scores and percentiles
    if populated > 0 and recompute_score:
        try:
            recompute(db)
        except Exception as exc:
            logger.warning("Global score recompute failed: %s", exc)

    # Populate 3NF peer benchmarks
    bm_count = 0
    try:
        bm_count = populate_peer_benchmarks(db)
    except Exception as exc:
        logger.warning("Peer benchmarks population failed: %s", exc)

    return {
        "populated": populated,
        "errors": errors,
        "scanned": len(target_cids),
        "total_unpopulated": len(candidates),
        "benchmarks": bm_count,
    }
