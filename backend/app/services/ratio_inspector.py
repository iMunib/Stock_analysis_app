"""Ratio Calculation Inspector Engine (Wave 1: US-0460, US-0453, US-0481).

Provides step-by-step arithmetic transparency for computed financial ratios:
- Exact formula definition
- Numerator value, units, currency, and as-of fiscal date
- Denominator value, units, currency, and as-of fiscal date
- Step-by-step arithmetic resolution
- Direct SEC EDGAR filing viewer link and accession provenance.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.services.pillar_drilldown import _format_money, _sec_url

CANONICAL_US_TAX_RATE = 0.21
FINANCIAL_SHEETS = {"Banks", "Insurance", "Credit_Services"}
FINANCIAL_SECTOR = "Financials"

RatioBuilder = Callable[["InspectionContext"], dict[str, Any]]


@dataclass(frozen=True)
class InspectionContext:
    company: Company
    company_id: str
    currency: str
    edgar_url: str
    primary_snapshot: FinancialSnapshot
    seed_snapshot: FinancialSnapshot | None
    fiscal_year_label: str
    as_of_label: str
    vintage_label: str
    provenance: str

    def resolve_field(self, field_name: str) -> Any:
        primary = getattr(self.primary_snapshot, field_name, None)
        if primary is not None:
            return primary
        if self.seed_snapshot is not None:
            return getattr(self.seed_snapshot, field_name, None)
        return None


def _is_financial_company(company: Company) -> bool:
    return company.custom_industry_sheet in FINANCIAL_SHEETS or company.gics_sector == FINANCIAL_SECTOR


def _load_context(db: Session, company_id: str) -> InspectionContext:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    currency = (company.currency or "USD").strip().upper()
    edgar_url = _sec_url(company.cik, company.ticker, currency, company_id)

    snaps = db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company_id, FinancialSnapshot.period_type == "FY")
        .order_by(FinancialSnapshot.fiscal_year.desc().nullslast())
    ).scalars().all()

    dated = [s for s in snaps if s.fiscal_year is not None]
    seed_snapshot = next((s for s in snaps if s.fiscal_year is None), None)
    primary = dated[0] if dated else seed_snapshot
    if primary is None:
        raise ValueError(f"No financial data available for company {company_id}")

    fiscal_year_label = f"FY{primary.fiscal_year}" if primary.fiscal_year else "Seed Baseline"
    as_of_label = primary.as_of_date.isoformat() if primary.as_of_date else (f"{primary.fiscal_year}-12-31" if primary.fiscal_year else "Current Baseline")
    vintage_label = f"{fiscal_year_label} filed {as_of_label} | Currency: {currency} (audited)"
    provenance = primary.source or (seed_snapshot.source if seed_snapshot and seed_snapshot.source else ("Audited SEDAR+ Filing" if currency == "CAD" else "SEC EDGAR 10-K Filing"))

    return InspectionContext(
        company=company,
        company_id=company_id,
        currency=currency,
        edgar_url=edgar_url,
        primary_snapshot=primary,
        seed_snapshot=seed_snapshot,
        fiscal_year_label=fiscal_year_label,
        as_of_label=as_of_label,
        vintage_label=vintage_label,
        provenance=provenance,
    )


def _build_side(
    ctx: InspectionContext,
    label: str,
    raw_value: Any,
    statement_location: str,
    as_of_override: str | None = None,
) -> dict[str, Any]:
    return {
        "label": label,
        "raw_value": raw_value,
        "formatted": _format_money(raw_value, ctx.currency),
        "units": "Base currency units",
        "currency": ctx.currency,
        "as_of_date": as_of_override or ctx.as_of_label,
        "statement_location": statement_location,
        "source": ctx.provenance,
        "sec_edgar_url": ctx.edgar_url,
    }


def _build_response(
    ctx: InspectionContext,
    ratio_id: str,
    label: str,
    formula: str,
    result: Any,
    result_formatted: str,
    numerator: dict[str, Any],
    denominator: dict[str, Any],
    arithmetic: list[str],
) -> dict[str, Any]:
    return {
        "company_id": ctx.company_id,
        "ratio_id": ratio_id,
        "label": label,
        "formula_string": formula,
        "result": result,
        "result_formatted": result_formatted,
        "vintage": ctx.vintage_label,
        "numerator": numerator,
        "denominator": denominator,
        "arithmetic_resolution": arithmetic,
    }


# ---------------------------------------------------------------------------
# Per-ratio builders (G30: each function does one thing, G23: polymorphism)
# ---------------------------------------------------------------------------


def _inspect_roe(ctx: InspectionContext) -> dict[str, Any]:
    net_income = ctx.resolve_field("net_income")
    book_equity = ctx.resolve_field("book_equity")
    ratio_val = ctx.resolve_field("roe_calc")
    if ratio_val is None and net_income is not None and book_equity and book_equity > 0:
        ratio_val = net_income / book_equity
    return _build_response(
        ctx, "roe", "Return on Equity (ROE)", "Net Income / Stockholders' Equity (Book Equity)", ratio_val,
        f"{ratio_val * 100:.2f}%" if ratio_val is not None else "0.0%",
        _build_side(ctx, "Net Income", net_income, "Consolidated Statement of Operations (Income Statement)"),
        _build_side(ctx, "Total Stockholders' Equity", book_equity, "Consolidated Balance Sheet (Stockholders' Equity)"),
        [
            f"Numerator (Net Income) = {_format_money(net_income, ctx.currency)}",
            f"Denominator (Book Equity) = {_format_money(book_equity, ctx.currency)}",
            f"Calculation: {net_income} / {book_equity} = {ratio_val:.6f}" if net_income is not None and book_equity else "Cannot compute: missing or zero denominator",
            f"Final Resolution: {ratio_val * 100:.2f}%" if ratio_val is not None else "Result: NULL",
        ],
    )


def _inspect_roa(ctx: InspectionContext) -> dict[str, Any]:
    net_income = ctx.resolve_field("net_income")
    total_assets = ctx.resolve_field("total_assets")
    ratio_val = ctx.resolve_field("roa_calc")
    if ratio_val is None and net_income is not None and total_assets and total_assets > 0:
        ratio_val = net_income / total_assets
    return _build_response(
        ctx, "roa", "Return on Assets (ROA)", "Net Income / Total Assets", ratio_val,
        f"{ratio_val * 100:.2f}%" if ratio_val is not None else "0.0%",
        _build_side(ctx, "Net Income", net_income, "Income Statement"),
        _build_side(ctx, "Total Assets", total_assets, "Consolidated Balance Sheet"),
        [
            f"Numerator (Net Income) = {_format_money(net_income, ctx.currency)}",
            f"Denominator (Total Assets) = {_format_money(total_assets, ctx.currency)}",
            f"Calculation: {net_income} / {total_assets} = {ratio_val:.6f}" if net_income is not None and total_assets else "Cannot compute",
            f"Final Resolution: {ratio_val * 100:.2f}%" if ratio_val is not None else "Result: NULL",
        ],
    )


def _inspect_fcf_margin(ctx: InspectionContext) -> dict[str, Any]:
    fcf = ctx.resolve_field("fcf_calc")
    revenue = ctx.resolve_field("revenue")
    ratio_val = ctx.resolve_field("fcfmargin_calc")
    if ratio_val is None and fcf is not None and revenue and revenue > 0:
        ratio_val = fcf / revenue
    cfo = ctx.resolve_field("operating_cash_flow")
    capex = ctx.resolve_field("capex")
    return _build_response(
        ctx, "fcf_margin", "Free Cash Flow Margin", "(Operating Cash Flow - Capital Expenditures) / Total Revenue", ratio_val,
        f"{ratio_val * 100:.2f}%" if ratio_val is not None else "0.0%",
        {
            "label": "Free Cash Flow (CFO - Capex)",
            "raw_value": fcf,
            "formatted": _format_money(fcf, ctx.currency),
            "units": "Base currency units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": f"Cash Flow Statement: CFO ({_format_money(cfo, ctx.currency)}) - Capex ({_format_money(capex, ctx.currency)})",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        _build_side(ctx, "Total Revenue", revenue, "Income Statement (Topline Revenue)"),
        [
            f"Operating Cash Flow = {_format_money(cfo, ctx.currency)}",
            f"Capital Expenditures = {_format_money(capex, ctx.currency)}",
            f"FCF = CFO - Capex = {_format_money(fcf, ctx.currency)}",
            f"Revenue = {_format_money(revenue, ctx.currency)}",
            f"Calculation: {fcf} / {revenue} = {ratio_val:.6f}" if fcf is not None and revenue else "Cannot compute",
            f"Final Resolution: {ratio_val * 100:.2f}%" if ratio_val is not None else "Result: NULL",
        ],
    )


def _inspect_pe(ctx: InspectionContext) -> dict[str, Any]:
    price = ctx.resolve_field("price")
    eps = ctx.resolve_field("diluted_eps")
    pe_val = ctx.resolve_field("pe_calc")
    if pe_val is None and price and eps and eps > 0:
        pe_val = price / eps
    return _build_response(
        ctx, "pe", "Price to Earnings (P/E)", "Current Share Price / Diluted Earnings Per Share (or Market Cap / Net Income)", pe_val,
        f"{pe_val:.2f}x" if pe_val and pe_val > 0 else ("Loss / Deficit" if eps and eps < 0 else "Not reported in filing"),
        {
            "label": "Current Market Price",
            "raw_value": price,
            "formatted": f"{ctx.currency} {price:.2f}" if price is not None else "Not reported in filing",
            "units": "Currency per share",
            "currency": ctx.currency,
            "as_of_date": ctx.primary_snapshot.price_asof or ctx.as_of_label,
            "statement_location": "Market Trading Quote",
            "source": "Market Trading Provider (Yahoo/Owner)",
            "sec_edgar_url": ctx.edgar_url,
        },
        {
            "label": "Diluted EPS (Trailing FY)",
            "raw_value": eps,
            "formatted": f"{ctx.currency} {eps:.2f}" if eps is not None else "Not reported in filing",
            "units": "Currency per share",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": "Income Statement (Diluted EPS)",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        [
            f"Share Price = {ctx.currency} {price:.2f}" if price is not None else "Price: NULL",
            f"Diluted EPS = {ctx.currency} {eps:.2f}" if eps is not None else "EPS: NULL",
            f"Calculation: {price} / {eps} = {pe_val:.4f}" if price and eps and eps > 0 else (f"Negative EPS ({eps}): P/E is undefined / Loss" if eps and eps < 0 else "Cannot compute"),
            f"Final Resolution: {pe_val:.2f}x" if pe_val and pe_val > 0 else "Status: Loss / Deficit",
        ],
    )


def _inspect_net_debt_ebitda(ctx: InspectionContext) -> dict[str, Any]:
    net_debt = ctx.resolve_field("netdebt_calc")
    ebitda = ctx.resolve_field("ebitda")
    total_debt = ctx.resolve_field("total_debt")
    cash = ctx.resolve_field("cash_st_investments")
    if net_debt is None and (total_debt is not None or cash is not None):
        net_debt = (total_debt or 0.0) - (cash or 0.0)
    ratio_val = (net_debt / ebitda) if (net_debt is not None and ebitda and ebitda > 0) else None
    total_debt_raw = getattr(ctx.primary_snapshot, "total_debt", None)
    cash_raw = getattr(ctx.primary_snapshot, "cash_st_investments", None)
    return _build_response(
        ctx, "net_debt_ebitda", "Net Debt / EBITDA", "(Total Debt - Cash & Equivalents) / EBITDA", ratio_val,
        f"{ratio_val:.2f}x" if ratio_val is not None else ("Net Cash (Negative Net Debt)" if net_debt is not None and net_debt <= 0 else "Not reported in filing"),
        {
            "label": "Net Debt (Total Debt - Cash)",
            "raw_value": net_debt,
            "formatted": _format_money(net_debt, ctx.currency),
            "units": "Base currency units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": f"Balance Sheet: Debt ({_format_money(total_debt_raw, ctx.currency)}) - Cash ({_format_money(cash_raw, ctx.currency)})",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        _build_side(ctx, "EBITDA", ebitda, "Operating Performance Metric"),
        [
            f"Total Debt = {_format_money(total_debt_raw, ctx.currency)}",
            f"Cash & Equivalents = {_format_money(cash_raw, ctx.currency)}",
            f"Net Debt = Total Debt - Cash = {_format_money(net_debt, ctx.currency)}",
            f"EBITDA = {_format_money(ebitda, ctx.currency)}",
            f"Calculation: {net_debt} / {ebitda} = {ratio_val:.4f}" if net_debt is not None and ebitda and ebitda > 0 else "Cannot compute",
            f"Final Resolution: {ratio_val:.2f}x" if ratio_val is not None else "Result: Net Cash / Bank Model",
        ],
    )


def _inspect_roic(ctx: InspectionContext) -> dict[str, Any]:
    is_fin = _is_financial_company(ctx.company)
    ebit = getattr(ctx.primary_snapshot, "ebit", None)
    total_debt = getattr(ctx.primary_snapshot, "total_debt", None) or 0.0
    equity = getattr(ctx.primary_snapshot, "book_equity", None) or 0.0
    cash = getattr(ctx.primary_snapshot, "cash_st_investments", None) or 0.0
    nopat = (ebit * (1.0 - CANONICAL_US_TAX_RATE)) if ebit is not None else None
    invested_capital = (total_debt + equity - cash) if (total_debt or equity) else None
    ratio_val = (nopat / invested_capital) if (nopat is not None and invested_capital and invested_capital > 0 and not is_fin) else None
    return _build_response(
        ctx, "roic", "Return on Invested Capital (ROIC)", "NOPAT (EBIT × [1 - 21% Tax]) / Invested Capital (Total Debt + Equity - Cash)", ratio_val,
        f"{ratio_val * 100:.2f}%" if ratio_val is not None else ("N/A (Bank Model)" if is_fin else "0.0%"),
        {
            "label": "Net Operating Profit After Tax (NOPAT)",
            "raw_value": nopat,
            "formatted": _format_money(nopat, ctx.currency),
            "units": "Base currency units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": f"Income Statement: EBIT ({_format_money(ebit, ctx.currency)}) × (1 - {CANONICAL_US_TAX_RATE:.2f})",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        {
            "label": "Invested Capital (Total Debt + Book Equity - Cash)",
            "raw_value": invested_capital,
            "formatted": _format_money(invested_capital, ctx.currency),
            "units": "Base currency units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": f"Balance Sheet: Debt ({_format_money(total_debt, ctx.currency)}) + Equity ({_format_money(equity, ctx.currency)}) - Cash ({_format_money(cash, ctx.currency)})",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        [
            f"EBIT = {_format_money(ebit, ctx.currency)}",
            f"NOPAT = EBIT × (1 - {CANONICAL_US_TAX_RATE:.2f}) = {_format_money(nopat, ctx.currency)}" if nopat is not None else "NOPAT: NULL",
            f"Invested Capital = Debt + Equity - Cash = {_format_money(invested_capital, ctx.currency)}" if invested_capital is not None else "Invested Capital: NULL",
            f"Calculation: {nopat} / {invested_capital} = {ratio_val:.4f}" if ratio_val is not None else ("Bank Model: ROIC omitted per regulatory standard" if is_fin else "Cannot compute: non-positive invested capital or missing inputs"),
            f"Final Resolution: {ratio_val * 100:.2f}%" if ratio_val is not None else "Status: N/A",
        ],
    )


def _inspect_pb(ctx: InspectionContext) -> dict[str, Any]:
    mcap = ctx.resolve_field("market_cap")
    equity = ctx.resolve_field("book_equity")
    pb_val = ctx.resolve_field("pb_calc")
    if pb_val is None and mcap and equity and equity > 0:
        pb_val = mcap / equity
    return _build_response(
        ctx, "pb", "Price to Book (P/B)", "Market Capitalization / Total Stockholders' Equity (Book Value)", pb_val,
        f"{pb_val:.2f}x" if pb_val and pb_val > 0 else ("Deficit (Negative Equity)" if equity and equity < 0 else "Not reported in filing"),
        {
            "label": "Market Capitalization",
            "raw_value": mcap,
            "formatted": _format_money(mcap, ctx.currency),
            "units": "Base currency units",
            "currency": ctx.currency,
            "as_of_date": ctx.primary_snapshot.price_asof or ctx.as_of_label,
            "statement_location": "Market Trading Quote",
            "source": "Market Trading Provider",
            "sec_edgar_url": ctx.edgar_url,
        },
        _build_side(ctx, "Total Stockholders' Equity", equity, "Consolidated Balance Sheet"),
        [
            f"Market Capitalization = {_format_money(mcap, ctx.currency)}",
            f"Stockholders' Equity = {_format_money(equity, ctx.currency)}",
            f"Calculation: {mcap} / {equity} = {pb_val:.4f}" if mcap and equity and equity > 0 else (f"Negative Equity ({_format_money(equity, ctx.currency)}): P/B is undefined due to share buybacks" if equity and equity < 0 else "Cannot compute"),
            f"Final Resolution: {pb_val:.2f}x" if pb_val and pb_val > 0 else "Status: Deficit / Buyback Distortion",
        ],
    )


def _inspect_ev_ebitda(ctx: InspectionContext) -> dict[str, Any]:
    is_fin = _is_financial_company(ctx.company)
    ev_val = ctx.resolve_field("ev_calc")
    ebitda_val = ctx.resolve_field("ebitda")
    mcap = ctx.resolve_field("market_cap") or 0.0
    total_debt = ctx.resolve_field("total_debt") or 0.0
    cash = ctx.resolve_field("cash_st_investments") or 0.0
    if ev_val is None and (mcap or total_debt):
        ev_val = mcap + total_debt - cash
    ratio_val = ctx.resolve_field("ev_to_ebitda_calc")
    if ratio_val is None and ev_val and ebitda_val and ebitda_val > 0 and not is_fin:
        ratio_val = ev_val / ebitda_val
    return _build_response(
        ctx, "ev_ebitda", "Enterprise Value to EBITDA (EV/EBITDA)", "(Market Cap + Total Debt - Cash & Equivalents) / EBITDA", ratio_val,
        f"{ratio_val:.2f}x" if ratio_val and ratio_val > 0 else ("N/A (Bank Model)" if is_fin else "Not applicable: Bank model"),
        {
            "label": "Enterprise Value (EV)",
            "raw_value": ev_val,
            "formatted": _format_money(ev_val, ctx.currency),
            "units": "Base currency units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": f"Market Cap ({_format_money(mcap, ctx.currency)}) + Debt ({_format_money(total_debt, ctx.currency)}) - Cash ({_format_money(cash, ctx.currency)})",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        _build_side(ctx, "EBITDA", ebitda_val, "Operating Performance Metric"),
        [
            f"Enterprise Value = {_format_money(ev_val, ctx.currency)}" if ev_val is not None else "EV: NULL",
            f"EBITDA = {_format_money(ebitda_val, ctx.currency)}" if ebitda_val is not None else "EBITDA: NULL",
            f"Calculation: {ev_val} / {ebitda_val} = {ratio_val:.4f}" if ev_val and ebitda_val and ebitda_val > 0 else ("Bank Model: EV/EBITDA omitted" if is_fin else "Cannot compute"),
            f"Final Resolution: {ratio_val:.2f}x" if ratio_val and ratio_val > 0 else "Status: N/A",
        ],
    )


def _inspect_current_ratio(ctx: InspectionContext) -> dict[str, Any]:
    current_assets = ctx.resolve_field("current_assets")
    current_liabilities = ctx.resolve_field("current_liabilities")
    ratio_val = (current_assets / current_liabilities) if (current_assets is not None and current_liabilities and current_liabilities > 0) else None
    return _build_response(
        ctx, "current_ratio", "Current Ratio (Working Capital Liquidity)", "Total Current Assets / Total Current Liabilities", ratio_val,
        f"{ratio_val:.2f}x" if ratio_val is not None else "Not reported in filing",
        _build_side(ctx, "Total Current Assets", current_assets, "Consolidated Balance Sheet (Current Assets)"),
        _build_side(ctx, "Total Current Liabilities", current_liabilities, "Consolidated Balance Sheet (Current Liabilities)"),
        [
            f"Current Assets = {_format_money(current_assets, ctx.currency)}",
            f"Current Liabilities = {_format_money(current_liabilities, ctx.currency)}",
            f"Calculation: {current_assets} / {current_liabilities} = {ratio_val:.4f}" if current_assets is not None and current_liabilities and current_liabilities > 0 else "Cannot compute: missing balance sheet line items",
            f"Final Resolution: {ratio_val:.2f}x" if ratio_val is not None else "Result: NULL",
        ],
    )


def _inspect_interest_coverage(ctx: InspectionContext) -> dict[str, Any]:
    ebit = ctx.resolve_field("ebit")
    interest_expense = ctx.resolve_field("interest_expense")
    ratio_val = (ebit / interest_expense) if (ebit is not None and interest_expense and interest_expense > 0) else None
    return _build_response(
        ctx, "interest_coverage", "Interest Coverage Ratio", "Operating Income (EBIT) / Interest Expense", ratio_val,
        f"{ratio_val:.2f}x" if ratio_val is not None else ("Negligible Interest" if interest_expense is not None and interest_expense <= 0 else "Not reported in filing"),
        _build_side(ctx, "Operating Income (EBIT)", ebit, "Consolidated Statement of Operations (Operating Income)"),
        _build_side(ctx, "Interest Expense", interest_expense, "Income Statement (Interest / Debt Service Expense)"),
        [
            f"Operating Income (EBIT) = {_format_money(ebit, ctx.currency)}",
            f"Interest Expense = {_format_money(interest_expense, ctx.currency)}",
            f"Calculation: {ebit} / {interest_expense} = {ratio_val:.4f}" if ebit is not None and interest_expense and interest_expense > 0 else "Cannot compute: zero or negative interest expense",
            f"Final Resolution: {ratio_val:.2f}x" if ratio_val is not None else "Result: Clean / Negligible Debt Service",
        ],
    )


def _inspect_gross_margin(ctx: InspectionContext) -> dict[str, Any]:
    gross_profit = ctx.resolve_field("gross_profit")
    revenue = ctx.resolve_field("revenue")
    ratio_val = ctx.resolve_field("grossmargin_calc")
    if ratio_val is None and gross_profit is not None and revenue and revenue > 0:
        ratio_val = gross_profit / revenue
    return _build_response(
        ctx, "gross_margin", "Gross Margin", "Gross Profit / Total Revenue", ratio_val,
        f"{ratio_val * 100:.2f}%" if ratio_val is not None else "0.0%",
        _build_side(ctx, "Gross Profit", gross_profit, "Consolidated Statement of Operations (Gross Profit)"),
        _build_side(ctx, "Total Revenue", revenue, "Income Statement (Topline Revenue)"),
        [
            f"Gross Profit = {_format_money(gross_profit, ctx.currency)}",
            f"Total Revenue = {_format_money(revenue, ctx.currency)}",
            f"Calculation: {gross_profit} / {revenue} = {ratio_val:.4f}" if gross_profit is not None and revenue and revenue > 0 else "Cannot compute",
            f"Final Resolution: {ratio_val * 100:.2f}%" if ratio_val is not None else "Result: NULL",
        ],
    )


def _inspect_net_debt_fcf(ctx: InspectionContext) -> dict[str, Any]:
    net_debt = ctx.resolve_field("netdebt_calc")
    fcf = ctx.resolve_field("fcf_calc")
    total_debt = ctx.resolve_field("total_debt")
    cash = ctx.resolve_field("cash_st_investments")
    if net_debt is None and (total_debt is not None or cash is not None):
        net_debt = (total_debt or 0.0) - (cash or 0.0)
    ratio_val = (net_debt / fcf) if (net_debt is not None and fcf and fcf > 0) else None
    return _build_response(
        ctx, "net_debt_fcf", "Net Debt to Free Cash Flow (Payback Horizon)", "(Total Debt - Cash & Equivalents) / Free Cash Flow", ratio_val,
        f"{ratio_val:.2f} years" if ratio_val is not None and ratio_val > 0 else ("Net Cash (0.0 years)" if net_debt is not None and net_debt <= 0 else "Not reported in filing"),
        _build_side(ctx, "Net Debt (Total Debt - Cash)", net_debt, "Consolidated Balance Sheet"),
        _build_side(ctx, "Free Cash Flow (CFO - Capex)", fcf, "Cash Flow Statement"),
        [
            f"Net Debt = {_format_money(net_debt, ctx.currency)}",
            f"Free Cash Flow = {_format_money(fcf, ctx.currency)}",
            f"Calculation: {net_debt} / {fcf} = {ratio_val:.4f}" if net_debt is not None and fcf and fcf > 0 else "Cannot compute",
            f"Final Resolution: {ratio_val:.2f} years to pay off debt via FCF" if ratio_val is not None else "Result: Net Cash / Bank Model",
        ],
    )


def _inspect_unknown(ctx: InspectionContext, normalized_name: str) -> dict[str, Any]:
    return {
        "company_id": ctx.company_id,
        "ratio_id": normalized_name,
        "label": f"{normalized_name.upper()} Ratio",
        "formula_string": f"Calculated metric {normalized_name}",
        "result": None,
        "result_formatted": "Not reported in filing",
        "vintage": ctx.vintage_label,
        "numerator": {
            "label": "Metric Primary Component",
            "raw_value": None,
            "formatted": "Not reported in filing",
            "units": "Native units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": "Audited Filings",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        "denominator": {
            "label": "Metric Baseline Component",
            "raw_value": None,
            "formatted": "Not reported in filing",
            "units": "Native units",
            "currency": ctx.currency,
            "as_of_date": ctx.as_of_label,
            "statement_location": "Audited Filings",
            "source": ctx.provenance,
            "sec_edgar_url": ctx.edgar_url,
        },
        "arithmetic_resolution": [f"Ratio {normalized_name} definition inspected.", "Resolution complete."],
    }


_RATIO_DISPATCH: dict[str, RatioBuilder] = {
    "roe": _inspect_roe,
    "roe_calc": _inspect_roe,
    "return_on_equity": _inspect_roe,
    "roa": _inspect_roa,
    "roa_calc": _inspect_roa,
    "return_on_assets": _inspect_roa,
    "fcf_margin": _inspect_fcf_margin,
    "fcfmargin": _inspect_fcf_margin,
    "fcfmargin_calc": _inspect_fcf_margin,
    "pe": _inspect_pe,
    "pe_calc": _inspect_pe,
    "pe_ratio": _inspect_pe,
    "price_to_earnings": _inspect_pe,
    "net_debt_ebitda": _inspect_net_debt_ebitda,
    "net_debt_to_ebitda": _inspect_net_debt_ebitda,
    "leverage": _inspect_net_debt_ebitda,
    "roic": _inspect_roic,
    "roic_calc": _inspect_roic,
    "return_on_invested_capital": _inspect_roic,
    "pb": _inspect_pb,
    "pb_calc": _inspect_pb,
    "pb_ratio": _inspect_pb,
    "price_to_book": _inspect_pb,
    "ev_ebitda": _inspect_ev_ebitda,
    "ev_to_ebitda": _inspect_ev_ebitda,
    "ev_to_ebitda_calc": _inspect_ev_ebitda,
    "current_ratio": _inspect_current_ratio,
    "current_ratio_calc": _inspect_current_ratio,
    "liquidity": _inspect_current_ratio,
    "interest_coverage": _inspect_interest_coverage,
    "interest_coverage_calc": _inspect_interest_coverage,
    "coverage": _inspect_interest_coverage,
    "gross_margin": _inspect_gross_margin,
    "grossmargin": _inspect_gross_margin,
    "grossmargin_calc": _inspect_gross_margin,
    "net_debt_fcf": _inspect_net_debt_fcf,
    "net_debt_to_fcf": _inspect_net_debt_fcf,
}


def inspect_ratio(db: Session, company_id: str, ratio_name: str) -> dict[str, Any]:
    """Inspect calculation of a specific financial ratio for a company."""
    ctx = _load_context(db, company_id)
    normalized = ratio_name.lower().replace("-", "_").strip()
    builder = _RATIO_DISPATCH.get(normalized)
    if builder:
        return builder(ctx)
    return _inspect_unknown(ctx, normalized)
