"""Ingest rules: upsert provider data into financial_snapshots.

Overwrite policy (frozen):
- Seed FY rows (fiscal_year NULL, source 'Sector_Financials_Final_Owner.xlsx')
  are NEVER overwritten by providers on that pseudo-year. Providers FILL NULLS
  on that row only for fields that are NULL, and never touch non-NULL owner values.
- Provider statements INSERT their own (company_id, fiscal_year, period_type='FY',
  source) rows. Unique constraint is (company_id, fiscal_year, period_type), so a
  second provider for the same fiscal_year updates columns only where the
  existing value is NULL (first provider wins on conflicts).
- Same-source re-ingest refreshes that source's rows in place.
- Cache: if a row for (company_id, fiscal_year, source) exists, no network re-hit
  unless refresh=True.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot
from app.providers.base import AnnualStatement
from app.services.fundamentals import apply_statement_to_snapshot

SEED_SOURCE = "Sector_Financials_Final_Owner.xlsx"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_or_create_company(db: Session, company_id: str, ticker: str, country: str, currency: str, name: str | None = None, exchange: str | None = None) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        company = Company(
            company_id=company_id,
            ticker=ticker,
            exchange=exchange or ("US" if country == "US" else "TSX"),
            country=country,
            name=name,
            currency=currency,
            indexes=[],
            in_sp500=False,
            in_tsx_composite=False,
            imported_at=_utcnow(),
        )
        db.add(company)
        db.flush()
    return company


def has_snapshot_for(db: Session, company_id: str, fiscal_year: int, source: str) -> bool:
    stmt = select(FinancialSnapshot.id).where(
        FinancialSnapshot.company_id == company_id,
        FinancialSnapshot.fiscal_year == fiscal_year,
        FinancialSnapshot.period_type == "FY",
    )
    row = db.execute(stmt).scalars().first()
    if row is None:
        return False
    snap = db.get(FinancialSnapshot, row)
    return (snap.source or "") == source


def seed_row(db: Session, company_id: str) -> FinancialSnapshot | None:
    return db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.fiscal_year.is_(None),
            FinancialSnapshot.period_type == "FY",
        )
    ).scalar_one_or_none()


def ingest_statements(
    db: Session,
    company: Company,
    statements: list[AnnualStatement],
    refresh: bool = False,
) -> dict:
    """Apply provider statements under the frozen overwrite policy."""
    now = _utcnow()
    created, updated, filled, skipped_cached = 0, 0, 0, 0
    seed = seed_row(db, company.company_id)

    for stmt in statements:
        year = stmt.fiscal_year
        if year is None:
            continue
        existing = db.execute(
            select(FinancialSnapshot).where(
                FinancialSnapshot.company_id == company.company_id,
                FinancialSnapshot.fiscal_year == year,
                FinancialSnapshot.period_type == "FY",
            )
        ).scalar_one_or_none()

        if existing is not None and existing.source == stmt.source and not refresh:
            skipped_cached += 1
            continue

        if existing is None:
            snap = FinancialSnapshot(
                company_id=company.company_id,
                fiscal_year=year,
                period_type="FY",
                source=stmt.source,
                currency=stmt.currency,
                as_of_date=stmt.period_end,
                provider_as_of=stmt.period_end,
                fetched_at=now,
            )
            db.add(snap)
            db.flush()
            apply_statement_to_snapshot(snap, stmt)
            snap.fetched_at = now
            created += 1
        else:
            # Another source already has this fiscal year: FILL NULLS ONLY.
            before = {c: getattr(existing, c) for c in (
                "revenue", "net_income", "diluted_eps", "gross_profit", "operating_cash_flow",
                "capex", "total_debt", "cash_st_investments", "book_equity", "total_assets",
                "total_liabilities", "ebit", "ebitda", "interest_expense", "fcf_calc", "netdebt_calc",
            )}
            changed = apply_statement_to_snapshot(existing, stmt)
            touched_fill = 0
            for attr in changed:
                if before.get(attr) is None and getattr(existing, attr) is not None:
                    touched_fill += 1
                elif before.get(attr) is not None:
                    # owner/first-provider value: revert any overwrite attempt
                    setattr(existing, attr, before[attr])
            if existing.source == SEED_SOURCE:
                # seed row keeps its identity; provider only filled NULLs
                filled += touched_fill
            else:
                updated += touched_fill

    # FILL-NULLS pass on the seed row itself (never overwrite non-NULL owner values).
    # Bank/insurer carve-out (AGENTS.md): corporate debt / gross stay blank for
    # Financials-sector companies even when a provider reports them.
    if seed is not None and statements:
        financials_sector = (company.gics_sector or "").strip().lower() == "financials"
        bank_skip = {"Total_Debt", "Gross_Profit"} if financials_sector else set()
        provider_fields: dict[str, float] = {}
        for stmt in statements:
            for k, v in stmt.fields.items():
                if v is not None and float(v) == float(v):
                    provider_fields.setdefault(k, float(v))
        attr_map = {
            "Revenue": "revenue", "TopLine_Alt": "topline_alt", "Net_Income": "net_income",
            "Diluted_EPS": "diluted_eps", "Gross_Profit": "gross_profit",
            "Operating_Cash_Flow": "operating_cash_flow", "Capex": "capex",
            "Total_Debt": "total_debt", "Cash_ST_Investments": "cash_st_investments",
            "Book_Equity": "book_equity", "Total_Assets": "total_assets",
            "Total_Liabilities": "total_liabilities", "EBIT": "ebit", "EBITDA": "ebitda",
            "Interest_Expense": "interest_expense",
        }
        for field, attr in attr_map.items():
            if field in bank_skip:
                continue
            val = provider_fields.get(field)
            if val is None:
                continue
            if getattr(seed, attr) is None:
                setattr(seed, attr, val)
                filled += 1
        # never alter seed provenance
        seed.source = SEED_SOURCE

    return {"created": created, "filled_seed_nulls": filled, "updated": updated, "skipped_cached": skipped_cached}


def ingest_price(db: Session, company: Company, quote) -> bool:
    """Write price into the seed row's price columns (fills NULLs only)."""
    if quote is None:
        return False
    snap = seed_row(db, company.company_id) or db.execute(
        select(FinancialSnapshot)
        .where(FinancialSnapshot.company_id == company.company_id, FinancialSnapshot.period_type == "FY")
        .order_by(FinancialSnapshot.fiscal_year.desc().nullslast(), FinancialSnapshot.id.desc())
        .limit(1)
    ).scalars().first()
    if snap is None:
        return False
    changed = False
    if snap.price is None and quote.price:
        snap.price = float(quote.price)
        snap.price_currency = quote.currency
        snap.price_asof = quote.as_of.isoformat() if quote.as_of else None
        changed = True
    return changed
