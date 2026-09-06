"""Watchlist 'What Changed' Digest & Morning Brief Engine (Wave 2 Epic 5).

Computes 1-page morning brief, historical pillar/score deltas, signal re-ratings,
post-earnings actuals vs prior year comparisons, and alert channel routing
(US-0084, US-0092, US-0351, US-0367, US-0377).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, DataQualityFlag, DerivedMetric, FinancialSnapshot, FinancialStatement, Score


def _sec_or_sedar_url(company: Company) -> str:
    """Generates authentic regulatory document URLs for US (EDGAR) or Canadian (SEDAR+)."""
    cur = (company.currency or "").upper()
    cid = company.company_id.upper()
    ticker = (company.ticker or "").upper()

    is_canadian = (
        cur == "CAD"
        or cid.startswith("CA:")
        or ":TSX" in cid
        or ticker.endswith(".TO")
        or (company.country or "").upper() == "CA"
    )
    if is_canadian:
        return "https://www.sedarplus.ca/csa-party/records/document.html"

    if company.cik:
        return f"https://www.sec.gov/edgar/browse/?CIK={company.cik:010d}"
    clean_ticker = ticker.split(":")[0].replace(".TO", "")
    return f"https://www.sec.gov/edgar/searchedgar/companysearch?search_text={clean_ticker}"


def compute_watchlist_digest(
    db: Session,
    company_ids: list[str] | None = None,
    client_alerts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generates complete morning brief digest over watched companies."""
    # Default representative golden universe names if none passed
    if not company_ids:
        company_ids = ["US:AAPL:US", "CA:SHOP:TSX", "US:MSFT:US", "US:NVDA:US", "CA:RY:TSX"]

    # Filter out blank strings
    clean_ids = [c.strip() for c in company_ids if c and c.strip()]
    if not clean_ids:
        clean_ids = ["US:AAPL:US", "CA:SHOP:TSX", "US:MSFT:US"]

    # Pre-fetch companies, scores, statements, and derived metrics
    companies = {c.company_id: c for c in db.execute(select(Company).where(Company.company_id.in_(clean_ids))).scalars().all()}
    scores = {s.company_id: s for s in db.execute(select(Score).where(Score.company_id.in_(clean_ids))).scalars().all()}

    # All statements for watched companies
    stmt_rows = db.execute(
        select(FinancialStatement)
        .where(FinancialStatement.company_id.in_(clean_ids), FinancialStatement.period_type == "FY")
        .order_by(FinancialStatement.company_id, FinancialStatement.fiscal_year.desc().nullslast())
    ).scalars().all()

    stmts_by_id: dict[str, list[FinancialStatement]] = {}
    for st in stmt_rows:
        stmts_by_id.setdefault(st.company_id, []).append(st)

    # Derived metrics for watched companies
    derived_rows = db.execute(
        select(DerivedMetric)
        .where(DerivedMetric.company_id.in_(clean_ids), DerivedMetric.period_type == "FY")
        .order_by(DerivedMetric.company_id, DerivedMetric.fiscal_year.desc().nullslast())
    ).scalars().all()

    derived_by_id: dict[str, list[DerivedMetric]] = {}
    for dm in derived_rows:
        derived_by_id.setdefault(dm.company_id, []).append(dm)

    # Flags for watched companies
    flag_rows = db.execute(
        select(DataQualityFlag).where(DataQualityFlag.company_id.in_(clean_ids))
    ).scalars().all()

    flags_by_id: dict[str, list[DataQualityFlag]] = {}
    for fl in flag_rows:
        flags_by_id.setdefault(fl.company_id or "", []).append(fl)

    # Snapshots fallback for watched companies
    snap_rows = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id.in_(clean_ids))
        .order_by(FinancialSnapshot.company_id, FinancialSnapshot.fiscal_year.desc().nullslast())
    ).scalars().all()

    snaps_by_id: dict[str, list[FinancialSnapshot]] = {}
    for sn in snap_rows:
        snaps_by_id.setdefault(sn.company_id, []).append(sn)

    items: list[dict[str, Any]] = []
    total_reratings = 0
    score_improvers = 0
    score_decliners = 0
    fresh_filings_count = 0
    critical_alerts_count = 0

    for cid in clean_ids:
        comp = companies.get(cid)
        if comp is None:
            continue

        sc = scores.get(cid)
        stmts = stmts_by_id.get(cid, [])
        dms = derived_by_id.get(cid, [])
        flags = flags_by_id.get(cid, [])
        snaps = snaps_by_id.get(cid, [])

        dated_stmts = [s for s in stmts if s.fiscal_year is not None]
        curr_stmt = dated_stmts[0] if dated_stmts else (stmts[0] if stmts else None)
        prior_stmt = dated_stmts[1] if len(dated_stmts) >= 2 else None

        dated_snaps = [s for s in snaps if s.fiscal_year is not None]
        snap_curr = dated_snaps[0] if dated_snaps else (snaps[0] if snaps else None)
        snap_prior = dated_snaps[1] if len(dated_snaps) >= 2 else None

        dated_dms = [d for d in dms if d.fiscal_year is not None]
        curr_dm = dated_dms[0] if dated_dms else (dms[0] if dms else None)
        prior_dm = dated_dms[1] if len(dated_dms) >= 2 else None

        # 1. Score and Pillar Deltas (US-0092)
        curr_comp = sc.composite if sc else None
        curr_q = sc.quality if sc else None
        curr_v = sc.value if sc else None
        curr_g = sc.growth if sc else None
        curr_r = sc.risk if sc else None
        curr_sig = (sc.signal or "neutral") if sc else "neutral"

        # Compute prior pillar estimates based on prior financial statement
        delta_q = 0.0
        delta_v = 0.0
        delta_g = 0.0
        delta_r = 0.0

        if curr_dm and prior_dm:
            # Quality delta (ROE change)
            if curr_dm.roe_calc is not None and prior_dm.roe_calc is not None:
                roe_diff = curr_dm.roe_calc - prior_dm.roe_calc
                delta_q = round(roe_diff * 2.0, 2)
            # Value delta (multiple change)
            if curr_dm.pe_calc is not None and prior_dm.pe_calc is not None and prior_dm.pe_calc > 0:
                pe_pct_diff = (curr_dm.pe_calc - prior_dm.pe_calc) / prior_dm.pe_calc
                delta_v = round(-pe_pct_diff * 1.5, 2)
            # Growth delta
            if curr_stmt and prior_stmt and curr_stmt.revenue is not None and prior_stmt.revenue is not None and prior_stmt.revenue > 0:
                rev_growth = (curr_stmt.revenue - prior_stmt.revenue) / prior_stmt.revenue
                delta_g = round((rev_growth - 0.05) * 4.0, 2)
            # Risk delta (Debt change)
            if curr_stmt and prior_stmt and curr_stmt.total_debt is not None and prior_stmt.total_debt is not None and prior_stmt.total_debt > 0:
                debt_pct_diff = (curr_stmt.total_debt - prior_stmt.total_debt) / prior_stmt.total_debt
                delta_r = round(-debt_pct_diff * 2.0, 2)

        # Composite delta: locked weights 0.30 Quality / 0.25 Value / 0.25 Growth / 0.20 Risk
        comp_delta = round(0.30 * delta_q + 0.25 * delta_v + 0.25 * delta_g + 0.20 * delta_r, 2)

        prior_comp = round(curr_comp - comp_delta, 2) if curr_comp is not None else None

        if comp_delta > 0:
            score_improvers += 1
        elif comp_delta < 0:
            score_decliners += 1

        prior_q = round(curr_q - delta_q, 2) if curr_q is not None else None
        prior_v = round(curr_v - delta_v, 2) if curr_v is not None else None
        prior_g = round(curr_g - delta_g, 2) if curr_g is not None else None
        prior_r = round(curr_r - delta_r, 2) if curr_r is not None else None

        # 2. Re-Rating & Signal Shift Detection (US-0084)
        signal_rerated = False
        prior_signal = curr_sig
        rerating_desc = None

        if prior_comp is not None and curr_comp is not None:
            if prior_comp < 6.0 <= curr_comp:
                signal_rerated = True
                prior_signal = "neutral"
                rerating_desc = f"Upgraded to {curr_sig} (+{comp_delta:.2f} composite score lift)"
            elif prior_comp >= 6.0 > curr_comp:
                signal_rerated = True
                prior_signal = "strong_candidate" if curr_sig != "strong_candidate" else "neutral"
                rerating_desc = f"Downgraded to {curr_sig} ({comp_delta:.2f} composite score decline)"
            elif abs(comp_delta) >= 0.4:
                signal_rerated = True
                rerating_desc = f"Material score shift ({comp_delta:+.2f}) in {curr_sig} band"

        if signal_rerated:
            total_reratings += 1

        # 3. Post-Earnings Comparison (US-0377)
        has_post_earnings = bool(curr_stmt is not None or snap_curr is not None)
        rev_curr = curr_stmt.revenue if (curr_stmt and curr_stmt.revenue is not None) else (snap_curr.revenue if snap_curr else None)
        rev_prior = prior_stmt.revenue if (prior_stmt and prior_stmt.revenue is not None) else (snap_prior.revenue if snap_prior else None)
        rev_growth_pct = None
        if rev_curr is not None and rev_prior is not None and rev_prior > 0:
            rev_growth_pct = round((rev_curr - rev_prior) / rev_prior * 100.0, 1)

        ni_curr = curr_stmt.net_income if (curr_stmt and curr_stmt.net_income is not None) else (snap_curr.net_income if snap_curr else None)
        ni_prior = prior_stmt.net_income if (prior_stmt and prior_stmt.net_income is not None) else (snap_prior.net_income if snap_prior else None)
        ni_growth_pct = None
        if ni_curr is not None and ni_prior is not None and abs(ni_prior) > 0:
            ni_growth_pct = round((ni_curr - ni_prior) / abs(ni_prior) * 100.0, 1)

        eps_curr = curr_stmt.diluted_eps if (curr_stmt and curr_stmt.diluted_eps is not None) else (snap_curr.diluted_eps if snap_curr else None)
        eps_prior = prior_stmt.diluted_eps if (prior_stmt and prior_stmt.diluted_eps is not None) else (snap_prior.diluted_eps if snap_prior else None)

        fcf_curr = (curr_stmt.free_cash_flow if curr_stmt else None) or (curr_dm.fcf_calc if curr_dm else None) or (snap_curr.free_cash_flow if snap_curr else None)
        fcf_prior = (prior_stmt.free_cash_flow if prior_stmt else None) or (prior_dm.fcf_calc if prior_dm else None) or (snap_prior.free_cash_flow if snap_prior else None)

        flag_messages = [f"{fl.code or 'FLAG'}: {fl.note or fl.field}" for fl in flags[:3]]
        fy = (curr_stmt.fiscal_year if curr_stmt else None) or (snap_curr.fiscal_year if snap_curr else None) or 2025
        period_str = str(curr_stmt.period_end or curr_stmt.as_of_date or "") if curr_stmt else str(snap_curr.as_of_date or "2025-12-31" if snap_curr else "2025-12-31")

        post_earnings = {
            "has_recent_earnings": has_post_earnings,
            "fiscal_year": fy,
            "period_end": period_str,
            "revenue": rev_curr,
            "prior_revenue": rev_prior,
            "revenue_growth_pct": rev_growth_pct,
            "net_income": ni_curr,
            "prior_net_income": ni_prior,
            "net_income_growth_pct": ni_growth_pct,
            "eps": eps_curr,
            "prior_eps": eps_prior,
            "fcf": fcf_curr,
            "prior_fcf": fcf_prior,
            "score_moved": comp_delta,
            "flags_changed": flag_messages,
        }

        # 4. Fresh Filings (US-0351, US-0453)
        filing_type = "Annual 10-K" if (comp.country or "").upper() == "US" else "SEDAR+ Annual Statement"
        if curr_stmt and curr_stmt.filing_type:
            filing_type = curr_stmt.filing_type

        period_date = str(curr_stmt.period_end or curr_stmt.as_of_date or "2025-12-31") if curr_stmt else "2025-12-31"
        fresh_filing = {
            "filing_type": filing_type,
            "period_end": period_date,
            "filing_url": _sec_or_sedar_url(comp),
            "is_fresh": True,
            "source": curr_stmt.source if curr_stmt else "Filing",
        }
        fresh_filings_count += 1

        # 5. Alert Rules & Channel Routing (US-0367)
        alerts: list[dict[str, Any]] = []
        altman_z = curr_dm.altman_z if curr_dm else None
        if altman_z is not None and altman_z < 1.81:
            alerts.append({
                "severity": "critical",
                "channel": "immediate",
                "title": "Distress Zone Warning",
                "message": f"Altman Z-Score dropped to {altman_z:.2f} (Distress Zone < 1.81)",
            })
            critical_alerts_count += 1
        elif altman_z is not None and altman_z < 2.99:
            alerts.append({
                "severity": "elevated",
                "channel": "digest",
                "title": "Altman Grey Zone",
                "message": f"Altman Z-Score in grey area ({altman_z:.2f})",
            })

        if signal_rerated:
            alerts.append({
                "severity": "elevated",
                "channel": "digest",
                "title": "Signal Re-Rating",
                "message": rerating_desc or "Company signal reassessed",
            })

        if rev_growth_pct is not None and rev_growth_pct > 15.0:
            alerts.append({
                "severity": "informational",
                "channel": "digest",
                "title": "Double-Digit Growth",
                "message": f"Revenue expanded {rev_growth_pct:+.1f}% YoY",
            })

        # Match custom client-side configured alerts (US-0367)
        if client_alerts:
            for ca in client_alerts:
                if ca.get("id") == cid:
                    pe_target = ca.get("pe_above")
                    pe_val = curr_dm.pe_calc if curr_dm else None
                    if pe_target is not None and pe_val is not None and pe_val > float(pe_target):
                        alerts.append({
                            "severity": ca.get("severity", "elevated"),
                            "channel": ca.get("channel", "immediate"),
                            "title": "P/E Ceiling Breach",
                            "message": f"P/E {pe_val:.1f} exceeds target threshold of {pe_target}",
                        })
                    comp_target = ca.get("composite_below")
                    if comp_target is not None and curr_comp is not None and curr_comp < float(comp_target):
                        alerts.append({
                            "severity": ca.get("severity", "critical"),
                            "channel": ca.get("channel", "immediate"),
                            "title": "Composite Floor Drop",
                            "message": f"Composite {curr_comp:.1f} dropped below target threshold of {comp_target}",
                        })

        items.append({
            "company_id": cid,
            "ticker": comp.ticker or cid,
            "name": comp.name or comp.ticker or cid,
            "currency": comp.currency or "USD",
            "gics_sector": comp.gics_sector or "Unknown",
            "custom_industry": comp.custom_industry_sheet,
            "current_composite": curr_comp,
            "prior_composite": prior_comp,
            "composite_delta": comp_delta,
            "current_signal": curr_sig,
            "prior_signal": prior_signal,
            "signal_rerated": signal_rerated,
            "rerating_description": rerating_desc,
            "pillar_deltas": {
                "quality": {"current": curr_q, "prior": prior_q, "delta": delta_q},
                "value": {"current": curr_v, "prior": prior_v, "delta": delta_v},
                "growth": {"current": curr_g, "prior": prior_g, "delta": delta_g},
                "risk": {"current": curr_r, "prior": prior_r, "delta": delta_r},
            },
            "post_earnings": post_earnings,
            "fresh_filing": fresh_filing,
            "alerts": alerts,
        })

    now_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    now_iso = datetime.now(timezone.utc).isoformat()

    cad_count = sum(1 for it in items if (it.get("currency") or "").upper() == "CAD")
    usd_count = sum(1 for it in items if (it.get("currency") or "").upper() == "USD")

    # Aggregate alerts across all watched items for the Morning Brief feed (US-0084, US-0351, US-0367)
    all_alerts: list[dict[str, Any]] = []
    for it in items:
        cid = it["company_id"]
        ticker = it["ticker"]
        name = it["name"]
        is_cad = (it.get("currency") or "").upper() == "CAD"
        filing_url = it.get("fresh_filing", {}).get("filing_url")
        for idx, al in enumerate(it.get("alerts", [])):
            sev_raw = (al.get("severity") or "informational").lower()
            if sev_raw in ("critical", "high"):
                sev_norm = "high"
            elif sev_raw in ("elevated", "medium"):
                sev_norm = "medium"
            else:
                sev_norm = "low"

            channel = al.get("channel", "digest")
            is_immediate = channel == "immediate"

            all_alerts.append({
                "id": f"{cid}_{idx}_{al.get('title', '').replace(' ', '_')}",
                "company_id": cid,
                "ticker": ticker,
                "name": name,
                "alert_type": al.get("alert_type") or al.get("title", "ALERT").upper().replace(" ", "_"),
                "title": al.get("title", ""),
                "detail": al.get("message", ""),
                "severity": sev_norm,
                "routing": {
                    "primary_channel": "Email + In-App Push" if is_immediate else "Morning Digest Feed",
                    "fallback_channel": "Daily Summary",
                    "urgency": "Immediate" if is_immediate else "Digest",
                },
                "metrics": al.get("metrics") or {},
                "sedar_url": filing_url if is_cad else None,
                "edgar_url": filing_url if not is_cad else None,
                "timestamp": now_iso,
            })

    high_sev_count = sum(1 for a in all_alerts if a["severity"] == "high")
    med_sev_count = sum(1 for a in all_alerts if a["severity"] == "medium")
    low_sev_count = sum(1 for a in all_alerts if a["severity"] == "low")

    stats = {
        "total_watched": len(items),
        "high_severity_count": high_sev_count,
        "medium_severity_count": med_sev_count,
        "low_severity_count": low_sev_count,
        "rerated_count": total_reratings,
        "earnings_count": sum(1 for it in items if it.get("post_earnings", {}).get("has_recent_earnings")),
    }

    summary = {
        "as_of_date": now_date,
        "total_watched": len(items),
        "reratings_count": total_reratings,
        "score_improvers_count": score_improvers,
        "score_decliners_count": score_decliners,
        "fresh_filings_count": fresh_filings_count,
        "critical_alerts_count": high_sev_count,
    }

    return {
        "brief_date": now_date,
        "market_session": "Pre-Market Opening Brief",
        "stats": stats,
        "alerts": all_alerts,
        "cad_companies_count": cad_count,
        "usd_companies_count": usd_count,
        "currency_segregation_note": "CAD and USD portfolios segregated. Cross-border comparisons use unitless ratios only.",
        "disclaimer": "Local morning digest for personal research. Not investment advice.",
        # Backward compatibility for tests:
        "summary": summary,
        "items": items,
    }
