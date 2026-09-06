"""Benford's Law First-Digit Forensic Screening Engine (Wave 3 Epic 8 US-0211).

Evaluates the distribution of leading digits (1–9) across a company's
reported financial figures against the expected Benford logarithmic
distribution: P(d) = log10(1 + 1/d).

Method:
- Collects all positive absolute statement figures across 10-year FY rows
  (revenue, gross_profit, net_income, operating_cash_flow, total_assets,
  cash_st_investments, accounts_receivable, inventory, total_debt,
  book_equity, ebit, ebitda) from both financial_snapshots and
  financial_statements.
- Requires ≥ 15 observations; otherwise returns insufficient_data.
- Computes observed frequencies, expected frequencies, and Pearson χ²
  statistic with 8 degrees of freedom.
- Verdict thresholds (conservative, informational):
    χ² < 15.5  → conforms
    15.5 ≤ χ² < 20.1 → deviation_noted (amber, ~p~0.05–0.02)
    χ² ≥ 20.1  → strong_deviation (still a screen, never an accusation)

No data is invented; missing figures are omitted, never zero-filled.
"""
from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialSnapshot, FinancialStatement

# Benford expected probabilities for digits 1–9
BENFORD_EXPECTED: dict[int, float] = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
CHI2_CONFORMS = 15.507  # χ² critical value df=8, α=0.05
CHI2_STRONG = 20.09  # df=8, α=0.01
MIN_OBS = 15


def _first_digit(value: float) -> int | None:
    if value is None:
        return None
    try:
        v = abs(float(value))
    except Exception:
        return None
    if v == 0 or not math.isfinite(v):
        return None
    # Strip scientific notation, get first non-zero digit
    s = f"{v:.15g}".lstrip("0").lstrip(".").lstrip("0")
    # Handle scientific like 1.23e10 → first digit is 1
    if "e" in s or "E" in s:
        s = s.split("e")[0].split("E")[0]
    s = s.replace(".", "").replace("-", "").lstrip("0")
    if not s:
        return None
    ch = s[0]
    if ch.isdigit() and ch != "0":
        return int(ch)
    return None


def _collect_figures(
    snaps: list[FinancialSnapshot], stmts: list[FinancialStatement]
) -> list[float]:
    figures: list[float] = []
    fields_snapshot = [
        "revenue",
        "gross_profit",
        "net_income",
        "operating_cash_flow",
        "total_assets",
        "cash_st_investments",
        "accounts_receivable",
        "inventory",
        "total_debt",
        "book_equity",
        "ebit",
        "ebitda",
        "capex",
        "current_assets",
        "current_liabilities",
        "ppe_net",
    ]
    for s in snaps:
        for fld in fields_snapshot:
            v = getattr(s, fld, None)
            if v is not None:
                try:
                    fv = float(v)
                    if fv != 0 and math.isfinite(fv) and abs(fv) >= 1:
                        figures.append(abs(fv))
                except Exception:
                    continue
    fields_stmt = [
        "revenue",
        "gross_profit",
        "net_income",
        "operating_cash_flow",
        "total_assets",
        "cash_st_investments",
        "accounts_receivable",
        "inventory",
        "total_debt",
        "book_equity",
        "ebit",
        "ebitda",
        "free_cash_flow",
        "current_assets",
        "ppe_net",
    ]
    for st in stmts:
        for fld in fields_stmt:
            v = getattr(st, fld, None)
            if v is not None:
                try:
                    fv = float(v)
                    if fv != 0 and math.isfinite(fv) and abs(fv) >= 1:
                        figures.append(abs(fv))
                except Exception:
                    continue
    return figures


def compute_benford(db: Session, company_id: str) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if company is None:
        raise ValueError(f"Company {company_id} not found")

    snaps = db.execute(
        select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period_type == "FY",
        )
    ).scalars().all()

    stmts = db.execute(
        select(FinancialStatement).where(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_type == "FY",
        )
    ).scalars().all()

    figures = _collect_figures(list(snaps), list(stmts))

    if len(figures) < MIN_OBS:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "data_available": False,
            "observations": len(figures),
            "min_required": MIN_OBS,
            "observed_freq": None,
            "expected_freq": {str(k): round(v, 4) for k, v in BENFORD_EXPECTED.items()},
            "chi2": None,
            "degrees_of_freedom": 8,
            "verdict": "insufficient_data",
            "interpretation": f"Only {len(figures)} positive figures across statements - at least {MIN_OBS} required for a first-digit test. Benford screening is a probabilistic screen, not a fraud finding.",
            "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
        }

    # Count first digits
    counts: dict[int, int] = {d: 0 for d in range(1, 10)}
    for v in figures:
        d = _first_digit(v)
        if d is not None:
            counts[d] += 1

    total = sum(counts.values())
    if total < MIN_OBS:
        return {
            "company_id": company_id,
            "status": "insufficient_data",
            "data_available": False,
            "observations": total,
            "min_required": MIN_OBS,
            "observed_freq": {str(k): round(v / total, 4) if total else 0 for k, v in counts.items()},
            "expected_freq": {str(k): round(v, 4) for k, v in BENFORD_EXPECTED.items()},
            "chi2": None,
            "degrees_of_freedom": 8,
            "verdict": "insufficient_data",
            "interpretation": "Insufficient first-digit observations after filtering zeros and sub-unit figures.",
            "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
        }

    observed_freq = {str(k): round(v / total, 4) for k, v in counts.items()}
    expected_freq = {str(k): round(v, 4) for k, v in BENFORD_EXPECTED.items()}

    # Pearson chi-square
    chi2 = 0.0
    for d in range(1, 10):
        exp = BENFORD_EXPECTED[d] * total
        obs = counts[d]
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp
    chi2_r = round(chi2, 2)

    if chi2 < CHI2_CONFORMS:
        verdict = "conforms"
        interpretation = f"χ²={chi2_r} (df=8) - observed first-digit distribution conforms to Benford expectation (p>0.05). No statistical irregularity flagged."
    elif chi2 < CHI2_STRONG:
        verdict = "deviation_noted"
        interpretation = f"χ²={chi2_r} (df=8) - mild deviation from Benford curve (0.02<p<0.05). Treat as informational screen; many benign factors cause deviation."
    else:
        verdict = "strong_deviation"
        interpretation = f"χ²={chi2_r} (df=8) - strong deviation from Benford curve (p<0.01). Statistically unusual but NOT proof of manipulation - forensics are screens with 15–20% false-positive rates."

    return {
        "company_id": company_id,
        "status": "computed",
        "data_available": True,
        "observations": total,
        "min_required": MIN_OBS,
        "observed_freq": observed_freq,
        "expected_freq": expected_freq,
        "observed_counts": {str(k): v for k, v in counts.items()},
        "chi2": chi2_r,
        "degrees_of_freedom": 8,
        "critical_05": CHI2_CONFORMS,
        "critical_01": CHI2_STRONG,
        "verdict": verdict,
        "interpretation": interpretation,
        "disclaimer": "Personal research software, not investment advice. Forensic models are probabilistic screening tools, not legal findings.",
    }