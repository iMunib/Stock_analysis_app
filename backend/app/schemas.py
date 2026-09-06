"""Pydantic v2 response schemas. Phase 1 is read-only."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DisclaimerOut(BaseModel):
    disclaimer: str
    phase: str = "Phase 1"


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: str
    ticker: str | None = None
    exchange: str | None = None
    country: str | None = None
    name: str | None = None
    gics_sector: str | None = None
    gics_industry: str | None = None
    custom_industry_sheet: str | None = None
    currency: str | None = None
    indexes: Any = None
    universe_tags: list[str] | None = None
    in_sp500: bool = False
    in_tsx_composite: bool = False
    cik: int | None = None
    reporting_currency: str | None = None
    filing_type: str | None = None


class CompanyListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CompanyOut]


class FlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field: str | None = None
    code: str | None = None
    note: str | None = None


class PlacementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sheet_name: str
    placement_role: str


class SnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fiscal_year: int | None = None
    period_type: str = "FY"
    as_of_date: date | None = None
    source: str | None = None
    currency: str | None = None
    # money
    revenue: float | None = None
    net_income: float | None = None
    diluted_eps: float | None = None
    gross_profit: float | None = None
    operating_cash_flow: float | None = None
    capex: float | None = None
    fcf_reported: float | None = None
    free_cash_flow: float | None = None
    fcf_calc: float | None = None
    netdebt_calc: float | None = None
    total_debt: float | None = None
    book_equity: float | None = None
    cash_st_investments: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    ebit: float | None = None
    ebitda: float | None = None
    interest_expense: float | None = None
    topline_alt: float | None = None
    # expanded GAAP/IFRS line items (Phase 1)
    accounts_receivable: float | None = None
    inventory: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    ppe_net: float | None = None
    retained_earnings: float | None = None
    stock_based_compensation: float | None = None
    interest_income: float | None = None
    # ratios
    fcfmargin_calc: float | None = None
    grossmargin_calc: float | None = None
    roe_calc: float | None = None
    roa_calc: float | None = None
    pe_calc: float | None = None
    pb_calc: float | None = None
    ev_calc: float | None = None
    ev_to_ebitda_calc: float | None = None
    # price
    price: float | None = None
    price_currency: str | None = None
    price_asof: str | None = None
    shares_snapshot: float | None = None
    market_cap: float | None = None
    # bank fields
    cet1_ratio: float | None = None
    cet1_approach: str | None = None
    cet1_requirement_or_target: float | None = None
    total_capital_ratio: float | None = None
    leverage_ratio: float | None = None
    nim_fy2025: float | None = None
    nim_q4_2025: float | None = None
    efficiency_ratio: float | None = None
    roaa: float | None = None


class CompanyDetailOut(CompanyOut):
    flags: list[FlagOut] = []
    placements: list[PlacementOut] = []
    latest_snapshot: SnapshotOut | None = None
    fiscal_year_note: str = (
        "Fiscal year is not present in the Phase 1 source workbook; "
        "the snapshot is the owner workbook's latest-FY compilation."
    )


class SectorCountOut(BaseModel):
    name: str
    count: int
    usd: int = 0
    cad: int = 0
    median_composite_usd: float | None = None
    median_composite_cad: float | None = None
    median_composite_all: float | None = None


class SectorsOut(BaseModel):
    custom_industries: list[SectorCountOut]
    gics_sectors: list[SectorCountOut]


class ImportInfoOut(BaseModel):
    last_import_at: datetime | None = None
    source_filename: str | None = None
    source_mtime: float | None = None
    fixture: bool | None = None


class StatsOut(BaseModel):
    companies: int
    financial_snapshots: int
    data_quality_flags: int
    placements: int
    import_runs: int
    by_currency: dict[str, int]
    coverage: dict[str, int]
    last_import: ImportInfoOut | None = None
