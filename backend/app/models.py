"""SQLAlchemy 2 models. Phase 1 schema: companies, financial_snapshots,
data_quality_flags, placements, import_runs.

Designed so future annual rows (5-10 years of history) need no rewrite:
financial_snapshots is keyed by (company_id, fiscal_year, period_type) with
fiscal_year nullable until the seed provides real fiscal years.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Company(Base):
    __tablename__ = "companies"

    company_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ticker: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    exchange: Mapped[str | None] = mapped_column(String(16), nullable=True)
    country: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    gics_sector: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    gics_industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    custom_industry_sheet: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    indexes: Mapped[str | None] = mapped_column(JSON, nullable=True)  # ["SP500","TSX_Composite"]
    in_sp500: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    in_tsx_composite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fiscal_year_end: Mapped[str | None] = mapped_column(String(32), nullable=True)
    extraction_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_primary: Mapped[str | None] = mapped_column(String(64), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cik: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reporting_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    filing_type: Mapped[str | None] = mapped_column(String(16), nullable=True)

    snapshots: Mapped[list["FinancialSnapshot"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    flags: Mapped[list["DataQualityFlag"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    placements: Mapped[list["Placement"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"
    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", "period_type", name="uq_snapshot_company_year_period"),
        Index("ix_snapshots_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(String(32), ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    fiscal_year: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL in Phase 1: seed has no FY column
    period_type: Mapped[str] = mapped_column(String(8), nullable=False, default="FY")
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # = Price_AsOf when present
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # -- money / statement columns (native currency, verbatim) --
    revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    diluted_eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_cash_flow: Mapped[float | None] = mapped_column(Float, nullable=True)
    capex: Mapped[float | None] = mapped_column(Float, nullable=True)
    fcf_reported: Mapped[float | None] = mapped_column(Float, nullable=True)
    free_cash_flow: Mapped[float | None] = mapped_column(Float, nullable=True)
    fcf_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    netdebt_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_debt: Mapped[float | None] = mapped_column(Float, nullable=True)
    book_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    cash_st_investments: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_assets: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_liabilities: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebit: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda: Mapped[float | None] = mapped_column(Float, nullable=True)
    interest_expense: Mapped[float | None] = mapped_column(Float, nullable=True)
    topline_alt: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -- ratios (unitless) --
    fcfmargin_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    grossmargin_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    roe_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    roa_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    pe_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    pb_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_calc: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_to_ebitda_calc: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -- price / snapshot --
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    price_asof: Mapped[str | None] = mapped_column(String(32), nullable=True)  # raw workbook text
    shares_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -- bank / insurer regulatory fields --
    cet1_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    cet1_approach: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cet1_requirement_or_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_capital_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    leverage_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    nim_fy2025: Mapped[float | None] = mapped_column(Float, nullable=True)
    nim_q4_2025: Mapped[float | None] = mapped_column(Float, nullable=True)
    efficiency_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    roaa: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -- provenance / QC passthrough --
    extraction_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_primary: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fill_ok: Mapped[str | None] = mapped_column(String(8), nullable=True)
    membership_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # -- Phase 2 provider provenance --
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # when the provider row was pulled
    provider_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)      # provider-reported period end for statements

    company: Mapped["Company"] = relationship(back_populates="snapshots")


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flags"
    __table_args__ = (Index("ix_flags_company", "company_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # NULL company_id = workbook-level note (e.g. the owner sheet's '(workbook)' pseudo-ID rows)
    company_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=True)
    field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. MISSING_FIELD
    note: Mapped[str | None] = mapped_column(Text, nullable=True)        # raw note text preserved

    company: Mapped["Company"] = relationship(back_populates="flags")


class Placement(Base):
    __tablename__ = "placements"
    __table_args__ = (
        UniqueConstraint("company_id", "sheet_name", "placement_role", name="uq_placement"),
        Index("ix_placements_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(String(32), ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    sheet_name: Mapped[str] = mapped_column(String(64), nullable=False)
    placement_role: Mapped[str] = mapped_column(String(8), nullable=False)  # Primary | Extra | GICS

    company: Mapped["Company"] = relationship(back_populates="placements")


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_filename: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_mtime: Mapped[float | None] = mapped_column(Float, nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    companies_imported: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fixture: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Score(Base):
    """Deterministic Phase 3 research score (method_version=v1)."""

    __tablename__ = "scores"

    company_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    as_of_fy: Mapped[int | None] = mapped_column(Integer, nullable=True)  # latest FY year used (NULL for seed-only)
    composite: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage: Mapped[int | None] = mapped_column(Integer, nullable=True)  # pillars computed 0-4
    signal: Mapped[str | None] = mapped_column(String(24), nullable=True)  # insufficient_data | strong_candidate | ...
    peer_set_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # custom_industry_currency | gics_currency
    peer_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    peer_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    method_version: Mapped[str] = mapped_column(String(8), nullable=False, default="v1")
    computed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inputs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # which fields were used


class HalalFlag(Base):
    """AAOIFI-style informational flag. NEVER a filter by default."""

    __tablename__ = "halal_flags"

    company_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # halal_candidate | not_halal | unknown
    tests_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # per-test explanation
    method: Mapped[str] = mapped_column(String(24), nullable=False, default="aaoifi_style_v1")
    computed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Job(Base):
    """Async job row (Phase 6A). Worker thread claims oldest queued, one at a time."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # uuid4
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # backfill | ingest | recompute
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="queued", index=True)  # queued|running|succeeded|failed|cancelled
    step: Mapped[str | None] = mapped_column(String(32), nullable=True)  # resolve | filings | prices_shares | sector_peers | score | done | failed
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_done: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_stats_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LlmCache(Base):
    """Cached LLM narration. Keyed so a recompute invalidates old text."""

    __tablename__ = "llm_cache"
    __table_args__ = (
        UniqueConstraint("kind", "subject_id", "method_version", "score_computed_at", "model", name="uq_llm_cache"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # company | sector | swot
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    method_version: Mapped[str] = mapped_column(String(8), nullable=False, default="v1")
    score_computed_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CompanyProfile(Base):
    """Company research pack: Yahoo business summary, dividends, next earnings, quarterly."""

    __tablename__ = "company_profiles"

    company_id: Mapped[str] = mapped_column(String(32), ForeignKey("companies.company_id", ondelete="CASCADE"), primary_key=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # truncated 280 chars
    dividend_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    dividend_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # DPS
    next_earnings_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quarterly_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # last 4 quarters
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

