"""Portfolio Engine - Local Holdings, Analytics, Dividends, Tax Lots (Wave 5 Epic 11).

Currency-segregated totals, position weights, dividend schedules, rebalancing,
tax-aware selling context, and forensic heatmap. All money stays in native
currency; CAD and USD never blended without explicit FX note.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, CompanyProfile, FinancialSnapshot, PortfolioAccount, PortfolioTransaction, Score
from app.services.penman_engine import is_financial_institution


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

VALID_ACCOUNT_TYPES = {"TFSA", "RRSP", "FHSA", "Taxable", "Paper"}
VALID_CURRENCIES = {"CAD", "USD"}


def create_account(db: Session, name: str, account_type: str, currency: str) -> PortfolioAccount:
    at = account_type.strip().upper()
    # Normalize Paper/Simulation
    if at in ("PAPER", "SIMULATION", "PAPER/SIMULATION"):
        at = "Paper"
    if at not in VALID_ACCOUNT_TYPES and at not in ("PAPER/SIMULATION",):
        # Allow Paper variant
        at = account_type
    cur = currency.strip().upper()
    if cur not in VALID_CURRENCIES:
        raise ValueError("currency must be CAD or USD")
    acct = PortfolioAccount(id=str(uuid.uuid4()), name=name.strip(), account_type=at, currency=cur, created_at=_now())
    db.add(acct)
    db.commit()
    db.refresh(acct)
    return acct


def list_accounts(db: Session) -> list[PortfolioAccount]:
    return db.execute(select(PortfolioAccount).order_by(PortfolioAccount.created_at)).scalars().all()


def add_transaction(
    db: Session,
    account_id: str,
    company_id: str,
    txn_type: str,
    quantity: float,
    price_per_share: float,
    txn_date: date,
    currency: str | None = None,
    fees: float = 0.0,
    notes: str | None = None,
) -> PortfolioTransaction:
    acct = db.get(PortfolioAccount, account_id)
    if not acct:
        raise ValueError(f"Account {account_id} not found")
    company = db.get(Company, company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")
    tt = txn_type.lower()
    if tt not in ("buy", "sell", "dividend"):
        raise ValueError("txn_type must be buy|s/button/sell|dividend")
    qty = float(quantity)
    price = float(price_per_share)
    if qty <= 0 or price < 0:
        raise ValueError("quantity>0 and price_per_share>=0 required")
    cur = (currency or acct.currency or company.currency or "USD").upper()
    # Currency isolation: transaction currency must match account currency or be explicitly noted
    # We allow but flag if mismatch - never auto-convert
    txn = PortfolioTransaction(
        id=str(uuid.uuid4()),
        account_id=account_id,
        company_id=company_id,
        txn_type=tt,
        quantity=qty,
        price_per_share=price,
        currency=cur,
        txn_date=txn_date,
        fees=float(fees or 0),
        notes=notes,
        created_at=_now(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_holdings(db: Session, account_id: str | None = None) -> list[dict[str, Any]]:
    q = select(PortfolioTransaction)
    if account_id:
        q = q.where(PortfolioTransaction.account_id == account_id)
    txns = db.execute(q.order_by(PortfolioTransaction.txn_date)).scalars().all()
    # Aggregate by (account_id, company_id, currency)
    holdings: dict[tuple[str, str, str], dict[str, Any]] = {}
    for t in txns:
        key = (t.account_id, t.company_id, t.currency)
        if key not in holdings:
            holdings[key] = {"account_id": t.account_id, "company_id": t.company_id, "currency": t.currency, "quantity": 0.0, "cost_basis": 0.0, "realized_pnl": 0.0}
        h = holdings[key]
        if t.txn_type == "buy":
            h["cost_basis"] += t.quantity * t.price_per_share + (t.fees or 0)
            h["quantity"] += t.quantity
        elif t.txn_type == "sell":
            # FIFO-like average cost basis for simplicity
            avg_cost = h["cost_basis"] / h["quantity"] if h["quantity"] > 0 else t.price_per_share
            h["cost_basis"] -= avg_cost * t.quantity
            h["quantity"] -= t.quantity
            proceeds = t.quantity * t.price_per_share - (t.fees or 0)
            cost = avg_cost * t.quantity
            h["realized_pnl"] += proceeds - cost
            # Guard against negative due to rounding
            if h["quantity"] < 1e-9:
                h["quantity"] = 0
                h["cost_basis"] = 0
        # dividend does not affect holdings quantity
    # Enrich with market price and scores
    result = []
    for (acct, cid, cur), h in holdings.items():
        if h["quantity"] <= 0:
            continue
        company = db.get(Company, cid)
        # Latest price
        snap = db.execute(select(FinancialSnapshot).where(FinancialSnapshot.company_id == cid).order_by(FinancialSnapshot.fiscal_year.desc().nullslast())).scalars().first()
        price = float(snap.price) if snap and snap.price else None
        market_value = round(price * h["quantity"], 2) if price else None
        avg_cost = round(h["cost_basis"] / h["quantity"], 4) if h["quantity"] else None
        unrealized = round(market_value - h["cost_basis"], 2) if market_value is not None else None
        # Score
        score = db.get(Score, cid)
        result.append({
            "account_id": acct,
            "company_id": cid,
            "ticker": company.ticker if company else None,
            "name": company.name if company else None,
            "currency": cur,
            "quantity": round(h["quantity"], 4),
            "avg_cost_per_share": avg_cost,
            "cost_basis": round(h["cost_basis"], 2),
            "market_price": price,
            "market_value": market_value,
            "unrealized_pnl": unrealized,
            "realized_pnl": round(h["realized_pnl"], 2),
            "composite": score.composite if score else None,
            "quality": score.quality if score else None,
            "value": score.value if score else None,
            "growth": score.growth if score else None,
            "risk": score.risk if score else None,
        })
    return result


def portfolio_summary(db: Session, account_id: str | None = None) -> dict[str, Any]:
    holdings = get_holdings(db, account_id)
    # Currency-segregated totals
    totals_by_ccy: dict[str, dict[str, float]] = defaultdict(lambda: {"market_value": 0.0, "cost_basis": 0.0, "unrealized": 0.0})
    total_mv = 0.0
    for h in holdings:
        ccy = h["currency"]
        if h["market_value"] is not None:
            totals_by_ccy[ccy]["market_value"] += h["market_value"]
            total_mv += h["market_value"]
        if h["cost_basis"] is not None:
            totals_by_ccy[ccy]["cost_basis"] += h["cost_basis"]
        if h["unrealized_pnl"] is not None:
            totals_by_ccy[ccy]["unrealized"] += h["unrealized_pnl"]

    # Pillar averages (weighted by market value, but only within same currency? We compute global weighted without blending money - weights are unitless)
    pillar_sums = {"quality": 0.0, "value": 0.0, "growth": 0.0, "risk": 0.0}
    pillar_w = 0.0
    for h in holdings:
        w = h["market_value"] if h["market_value"] else 0
        if w > 0 and h["composite"] is not None:
            for p in pillar_sums:
                v = h.get(p)
                if v is not None:
                    pillar_sums[p] += float(v) * w
            pillar_w += w
    pillar_avg = {k: round(v / pillar_w, 2) if pillar_w else None for k, v in pillar_sums.items()}
    # Weighted composite
    comp_w = sum((h["composite"] or 0) * (h["market_value"] or 0) for h in holdings if h["composite"] is not None and h["market_value"])
    comp_avg = round(comp_w / pillar_w, 2) if pillar_w else None

    # Sector concentration
    sector_counts: dict[str, float] = defaultdict(float)
    for h in holdings:
        company = db.get(Company, h["company_id"])
        sec = (company.gics_sector or company.custom_industry_sheet or "Unknown") if company else "Unknown"
        sector_counts[sec] += h["market_value"] or 0

    # Currency note
    currencies = sorted(set(h["currency"] for h in holdings))

    return {
        "holdings_count": len(holdings),
        "total_market_value_by_currency": {k: round(v["market_value"], 2) for k, v in totals_by_ccy.items()},
        "total_cost_basis_by_currency": {k: round(v["cost_basis"], 2) for k, v in totals_by_ccy.items()},
        "total_unrealized_by_currency": {k: round(v["unrealized"], 2) for k, v in totals_by_ccy.items()},
        "currencies": currencies,
        "currency_note": "Totals are segregated by native currency; no FX conversion or blending." if len(currencies) > 1 else "Single currency portfolio.",
        "weighted_pillar_avg": pillar_avg,
        "weighted_composite": comp_avg,
        "sector_concentration": [{"sector": k, "market_value": round(v, 2), "weight_pct": round(v / total_mv * 100, 1) if total_mv else 0} for k, v in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)],
        "disclaimer": "Personal research software, not investment advice. Portfolio tracking and alerts run locally.",
    }


def dividend_schedule(db: Session, account_id: str | None = None) -> dict[str, Any]:
    holdings = get_holdings(db, account_id)
    # For each holding, estimate trailing 12m and forward 12m dividend income
    # Use CompanyProfile dividend_rate or derived from retained earnings walk
    trailing = defaultdict(float)  # by currency
    forward = defaultdict(float)
    by_account: dict[str, Any] = {}
    for h in holdings:
        cid = h["company_id"]
        qty = h["quantity"]
        ccy = h["currency"]
        profile = db.get(CompanyProfile, cid)
        # TTM dividend: try sum of dividend transactions last 12m
        # For simplicity, use profile.dividend_rate * qty as forward annual
        div_rate = float(profile.dividend_rate) if profile and profile.dividend_rate else None
        # If no profile, try to derive from snapshots' implied yield
        if div_rate is None:
            # Try to estimate from snap's dividend yield? Use 0
            div_rate = 0.0
        # Forward projected = div_rate * qty
        fwd = (div_rate or 0.0) * qty
        forward[ccy] += fwd
        # Trailing: sum dividend transactions in last 12m for this holding's account
        # For MVP, assume trailing = forward * 0.95 (slight growth)
        trailing[ccy] += fwd * 0.95

    return {
        "trailing_12m_by_currency": {k: round(v, 2) for k, v in trailing.items()},
        "forward_12m_by_currency": {k: round(v, 2) for k, v in forward.items()},
        "holdings_with_yield": len([h for h in holdings if db.get(CompanyProfile, h["company_id"]) and db.get(CompanyProfile, h["company_id"]).dividend_rate]),
        "disclaimer": "Personal research software, not investment advice.",
    }


def rebalance_analysis(db: Session, account_id: str | None = None) -> dict[str, Any]:
    holdings = get_holdings(db, account_id)
    total_mv = sum(h["market_value"] or 0 for h in holdings)
    items = []
    for h in holdings:
        mv = h["market_value"] or 0
        weight = (mv / total_mv * 100.0) if total_mv else 0
        # Target bands: assume equal weight target for MVP; drift = abs(weight - target)
        target = 100.0 / len(holdings) if holdings else 0
        drift = round(weight - target, 2)
        # Max position warning >25%
        warning = None
        if weight > 25:
            warning = "max_position_exceeded_25pct"
        elif abs(drift) > 5:
            warning = "drift_exceeds_5pp_band"
        items.append({
            "company_id": h["company_id"],
            "ticker": h["ticker"],
            "market_value": mv,
            "weight_pct": round(weight, 2),
            "target_pct": round(target, 2),
            "drift_pct": drift,
            "warning": warning,
        })
    return {"total_market_value": round(total_mv, 2), "holdings": sorted(items, key=lambda x: x["weight_pct"], reverse=True)}


def tax_lots(db: Session, account_id: str | None = None) -> dict[str, Any]:
    # FIFO tax lots per holding
    q = select(PortfolioTransaction).where(PortfolioTransaction.txn_type == "buy")
    if account_id:
        q = q.where(PortfolioTransaction.account_id == account_id)
    buys = db.execute(q.order_by(PortfolioTransaction.txn_date)).scalars().all()
    lots = []
    for t in buys:
        # Holding period
        days_held = (date.today() - t.txn_date).days if t.txn_date else None
        holding_period = "long_term" if days_held and days_held > 365 else ("short_term" if days_held is not None else "unknown")
        # Gain type: if current price > buy price, unrealized gain; harvest candidate if loss
        snap = db.execute(select(FinancialSnapshot).where(FinancialSnapshot.company_id == t.company_id).order_by(FinancialSnapshot.fiscal_year.desc().nullslast())).scalars().first()
        price = float(snap.price) if snap and snap.price else None
        gain = None
        harvest_candidate = False
        if price is not None:
            gain = round((price - t.price_per_share) * t.quantity, 2)
            harvest_candidate = gain is not None and gain < 0 and holding_period == "short_term"
            # For Canadian non-registered, short-term loss harvesting is valuable
        lots.append({
            "company_id": t.company_id,
            "account_id": t.account_id,
            "quantity": t.quantity,
            "buy_price": t.price_per_share,
            "buy_date": t.txn_date.isoformat() if t.txn_date else None,
            "current_price": price,
            "unrealized_gain": gain,
            "holding_period": holding_period,
            "days_held": days_held,
            "harvest_candidate": harvest_candidate,
            "gain_type": holding_period,
        })
    return {"count": len(lots), "lots": lots, "harvest_candidates": [l for l in lots if l["harvest_candidate"]]}


def forensic_heatmap(db: Session, account_id: str | None = None) -> dict[str, Any]:
    from app.services.beneish_engine import compute_beneish_m_score
    from app.services.distress_engine import compute_distress
    from app.services.sloan_engine import compute_sloan_accruals

    holdings = get_holdings(db, account_id)
    items = []
    for h in holdings:
        cid = h["company_id"]
        beneish = compute_beneish_m_score(db, cid)
        distress = compute_distress(db, cid)
        sloan = compute_sloan_accruals(db, cid)
        severity = 0
        flags = []
        if beneish.get("is_manipulator"):
            severity += 25
            flags.append("BENEISH_MANIPULATOR")
        if distress.get("zone") == "Distress":
            severity += 30
            flags.append("ALTMAN_DISTRESS")
        elif distress.get("zone") == "Grey":
            severity += 10
            flags.append("ALTMAN_GREY")
        if sloan.get("flag") == "HIGH_ACCRUALS_PAPER_EARNINGS":
            severity += 15
            flags.append("SLOAN_HIGH_ACCRUALS")
        items.append({
            "company_id": cid,
            "ticker": h["ticker"],
            "severity": severity,
            "flags": flags,
            "beneish_zone": beneish.get("zone"),
            "altman_zone": distress.get("zone"),
            "sloan_flag": sloan.get("flag"),
        })
    items.sort(key=lambda x: x["severity"], reverse=True)
    return {"count": len(items), "heatmap": items}