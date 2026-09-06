"""Data gap detection service for company financials and dossiers."""
from __future__ import annotations


def compute_data_gaps(company: dict, enriched: dict) -> list[str]:
    """Identify data coverage gaps in company fundamentals."""
    gaps: list[str] = []
    dated = [h for h in company.get("history", []) if h.get("fiscal_year") is not None]
    if len(dated) < 3:
        gaps.append("growth_history")
    if enriched.get("pe_calc") is None and enriched.get("pb_calc") is None:
        gaps.append("valuation_multiples")
    if (company.get("gics_sector") or "").lower() == "financials":
        if enriched.get("cet1_ratio") is None and enriched.get("leverage_ratio") is None:
            gaps.append("bank_capital")
    if enriched.get("gross_profit") is None:
        gaps.append("gross_profit")
    if enriched.get("total_debt") is None:
        gaps.append("total_debt")
    if enriched.get("market_cap") is None:
        gaps.append("market_cap")
    if enriched.get("fcf_calc") is None:
        gaps.append("fcf")
    return gaps


# Alias for backward compatibility
_data_gaps = compute_data_gaps
