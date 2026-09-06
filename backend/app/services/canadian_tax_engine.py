"""Canadian Tax & Market Engine (Wave 7 Epic 15).

Informational, not tax advice. All rules are proxy explanations for display.
Handles TFSA/RRSP/FHSA/Non-Registered placement, US withholding, eligible
dividend gross-up, REIT FFO/AFFO, and TSX industry medians in pure CAD.
"""
from __future__ import annotations

from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Score


def get_account_placement_guide(company: Company) -> dict[str, Any]:
    is_us = (company.country or "").upper() == "US" or company.currency == "USD"
    is_canadian_eligible = (company.country or "").upper() == "CA" and company.currency == "CAD"
    # Simple heuristics: if company is US, US dividend withholding applies
    # If Canadian eligible dividend payer, gross-up applies
    guides = {
        "TFSA": {
            "eligible": True,
            "withholding": "15% US withholding applies and is NOT recoverable in TFSA (treaty does not exempt TFSA).",
            "note": "US dividends face 15% withholding in TFSA; Canadian eligible dividends have no withholding." if is_us else "Canadian eligible dividends: no withholding, gross-up/tax credit in Non-Registered, tax-free in TFSA.",
            "best_for": "Canadian growth (no US dividends) or Canadian eligible dividends.",
        },
        "RRSP": {
            "eligible": True,
            "withholding": "0% US withholding via Canada-US treaty - RRSP is exempt (US-listed securities held directly).",
            "note": "US dividends in RRSP are exempt from 15% withholding if held directly (not via Canadian wrapper).",
            "best_for": "US dividend payers - RRSP maximizes after-tax yield.",
        },
        "FHSA": {
            "eligible": True,
            "withholding": "15% US withholding applies (like TFSA, not exempt).",
            "note": "FHSA follows TFSA withholding rules; Canadian eligible dividends are tax-free while held.",
            "best_for": "First-home savings; prefers Canadian or growth assets over US dividends.",
        },
        "NonRegistered": {
            "eligible": True,
            "withholding": "15% US withholding is recoverable as foreign tax credit; Canadian eligible dividends get gross-up (38% for 2024) + federal tax credit (~15% of grossed-up) + provincial credit.",
            "note": "Canadian eligible dividends: gross-up and tax credit make them tax-efficient in Non-Registered; US dividends: foreign tax credit mitigates withholding.",
            "best_for": "Canadian eligible dividends (Aristocrats) for tax-efficient income.",
        },
    }
    return {
        "company_id": company.company_id,
        "is_us_dividend_payer": is_us,
        "is_canadian_eligible": is_canadian_eligible,
        "guides": guides,
        "disclaimer": "Informational, not tax advice. Consult a Canadian tax professional.",
    }


def get_canadian_industry_medians(db: Session, industry: str, currency: str = "CAD") -> dict[str, Any]:
    # Pure CAD medians for custom industry
    scores = db.execute(
        select(Score).join(Company, Score.company_id == Company.company_id).where(
            Company.custom_industry_sheet == industry,
            Company.currency == currency,
            Score.composite.isnot(None),
        )
    ).scalars().all()
    if not scores:
        return {"industry": industry, "currency": currency, "count": 0, "median_composite": None, "median_pe": None, "median_pb": None, "median_roe": None, "note": "No pure CAD peers in this custom industry."}
    comps = sorted([s.composite for s in scores if s.composite is not None])
    # Need to fetch PE/PB/ROE via scores percentiles or via financial snapshot? Use scores for composite only for MVP
    median_comp = median(comps) if comps else None
    return {
        "industry": industry,
        "currency": currency,
        "count": len(scores),
        "median_composite": round(float(median_comp), 2) if median_comp is not None else None,
        "note": "Pure CAD medians - never blended with USD.",
    }


def get_dual_listed_identity(company: Company) -> dict[str, Any]:
    # Heuristic: dual-listed if company has interlisted flag or known dual-listed tickers
    dual_tickers = {"RY", "SHOP", "ENB", "CNQ", "SU", "TD", "BNS", "BMO", "CM", "TRP", "BCE", "CNR", "CP"}
    ticker = (company.ticker or "").upper().replace(".TO", "").replace(".UN", "")
    is_dual = ticker in dual_tickers
    # For dual-listed, show native CAD TSX metrics alongside US NYSE ratio parity
    return {
        "company_id": company.company_id,
        "ticker": company.ticker,
        "is_dual_listed": is_dual,
        "cad_ticker": f"{ticker}.TO" if is_dual else None,
        "us_ticker": ticker if is_dual else None,
        "note": "Dual-listed: native CAD TSX metrics alongside US NYSE ratio parity without blending currencies (unitless ratios only)." if is_dual else "Single-listed.",
        "currency": company.currency,
    }


def get_canadian_metrics(company: Company, snap: Any | None = None) -> dict[str, Any]:
    gics = (company.gics_sector or "").upper()
    custom = (company.custom_industry_sheet or "").upper()
    is_reit = "REIT" in custom or "REIT" in gics
    is_energy = "ENERGY" in gics or "ENERGY" in custom
    is_materials = "MATERIALS" in gics or "MINING" in custom
    is_utility = "UTILITIES" in gics
    # FFO/AFFO proxies: FFO ≈ OCF, AFFO ≈ OCF - capex (where available)
    ffo = None
    affo = None
    if snap:
        ocf = getattr(snap, "operating_cash_flow", None)
        capex = getattr(snap, "capex", None)
        if ocf is not None:
            ffo = float(ocf)
            if capex is not None:
                affo = float(ocf) - float(abs(capex))
    return {
        "company_id": company.company_id,
        "is_reit": is_reit,
        "ffo_proxy": round(ffo, 2) if ffo is not None else None,
        "affo_proxy": round(affo, 2) if affo is not None else None,
        "ffo_note": "FFO proxied via operating cash flow; AFFO proxied via OCF - capex (honest proxy, not filed FFO)." if is_reit else None,
        "is_energy_mining": is_energy or is_materials,
        "resource_note": "Energy/Mining: resource economics - reserve life, FCF ex-growth capex context (informational)." if (is_energy or is_materials) else None,
        "is_utility": is_utility,
        "utility_note": "Utility: rate-regulated capital structure - high leverage is structural, not distress." if is_utility else None,
        "is_canadian": company.currency == "CAD",
        "currency": company.currency,
    }