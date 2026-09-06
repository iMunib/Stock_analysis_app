"""Backtest Engine - Epic 21 (Wave 8 Capstone).

Factor decay transparency (Piotroski post-2000, McLean & Pontiff -58%),
survivorship & lookahead bias auditor, historical signal follow-through,
parameter overfitting warnings. Backtests here are research replay, not
promises. All composites remain locked 0.30/0.25/0.25/0.20 - backtests never
alter scoring.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

DISCLAIMER = "Personal research software, not investment advice."

FACTOR_DECAY: list[dict[str, Any]] = [
    {
        "factor": "Piotroski F-Score",
        "discovery": "Piotroski 2000 - 1976–1996 sample",
        "original_claim": "~23%/yr long-short within cheap stocks (1976–96)",
        "decay": "Weakened post-publication; regime-dependent. Alpha decay ~58% lower after publication (McLean & Pontiff 2016), ~32% publication-attributable.",
        "citation": "McLean & Pontiff 2016 (Wiley/SSRN); Piotroski 2000 UCLA Anderson PDF; Harvey-Liu-Zhu 2016 t>3.0",
    },
    {
        "factor": "Greenblatt Magic Formula (~33% claim)",
        "discovery": "The Little Book That Beats the Market (2005)",
        "original_claim": "~33% independent backtest (contested)",
        "decay": "Independent backtests weaker; present as preset screen, not promise. Survivorship and lookahead biases matter.",
        "citation": "Greenblatt 2005; Cakici et al. 2024 review",
    },
    {
        "factor": "Size Premium",
        "discovery": "Banz 1981",
        "original_claim": "Small caps beat large (1981)",
        "decay": "≈ zero since discovery - only credible when conditioned on quality (Novy-Marx/Asness). Treat as dead until quality-conditioned.",
        "citation": "Banz 1981; Asness-Frazzini-Pedersen QMJ 2019",
    },
    {
        "factor": "Composite Q+V+M",
        "discovery": "Fama-French + Novy-Marx + Jegadeesh-Titman",
        "original_claim": "Blends raise information ratio vs single factors",
        "decay": "Decay per McLean-Pontiff; still (M) grade but never promised as forward alpha.",
        "citation": "McLean & Pontiff 2016; Jacobs & Müller 2020",
    },
]

SURVIVORSHIP_DOC: dict[str, Any] = {
    "universe_construction": "720 companies: 500 S&P 500 + 220 S&P/TSX Composite names as of owner workbook date (2026-08-22). Current members only; delisted names are not backfilled (survivorship bias). Study is point-in-time replay, not continuous history.",
    "delisted_treatment": "Delisted outcomes not included where data unavailable; backtests here are screens over the live universe snapshot, not CRSP-style survival. Treat as descriptive, not predictive.",
    "lookahead_bias": "All signals use only data available at fiscal year end / provider_as_of; no future knowledge leaks. Hindsight replay uses price_as_of dating. Score history respects filing lag.",
    "limitations": "Factor returns shown are historical empirical averages with confidence intervals; historical does not imply future. Overfitting risk rises with >5 interdependent constraints (see overfitting warnings).",
    "disclaimer": DISCLAIMER,
}


def get_factor_decay() -> dict[str, Any]:
    return {
        "as_of": "2026-09-05",
        "factors": FACTOR_DECAY,
        "headline": "McLean & Pontiff 2016: returns ~58% lower post-publication (~32% publication-attributable); Harvey-Liu-Zhu: demand t > 3.0",
        "disclaimer": DISCLAIMER,
    }


def get_survivorship_doc() -> dict[str, Any]:
    return SURVIVORSHIP_DOC


def get_signal_follow_through(db: Session | None = None) -> dict[str, Any]:
    # Historical signal follow-through: what happened after score band shifts
    # For MVP, provide methodology and honesty wrapper; with more history this would compute actual price reactions.
    return {
        "method": "Signal follow-through compares score band (Strong candidate → Avoid) changes to subsequent 12-1 context (not prediction). Uses available annual periods only; missing years = NULL+flag.",
        "finding": "With limited history (seed is FY-null), most names have insufficient multi-year score deltas for a full panel. Earlier waves note 713/718 lacked 3y growth history. Follow-through is therefore descriptive.",
        "bias_note": "Survivorship: current 720 members; Lookahead: point-in-time; Sample: small where scored history thin - confidence labels respect actual sample sizes.",
        "disclaimer": DISCLAIMER,
    }


def check_overfitting(criteria: dict[str, Any] | None) -> dict[str, Any]:
    if not criteria:
        return {"constraints": 0, "warning": None, "disclaimer": DISCLAIMER}
    # Count active constraints (non-null, non-default)
    active = 0
    for k, v in criteria.items():
        if v is None or v == "" or v is False:
            continue
        if k in {"currency", "signal", "sector", "industry", "preset"} and v:
            active += 1
        elif k not in {"currency", "signal", "sector", "industry", "preset", "sort_by", "sort_dir", "limit", "offset", "criteria_logic"}:
            if isinstance(v, (int, float)) and v != 0:
                active += 1
            elif isinstance(v, bool):
                active += 1
            elif isinstance(v, str) and v:
                active += 1
    warning = None
    if active > 5:
        warning = f"Parameter overfitting risk: {active} interdependent constraints. Fewer constraints (≤5) reduce curve-fitting; prefer economically distinct checks (quality + value + distress) over many correlated bounds. Results may be in-sample artifacts."
    return {
        "constraints": active,
        "threshold": 5,
        "warning": warning,
        "guidance": "Favor 2–4 economically distinct constraints; document thesis before screening; validate out-of-sample.",
        "disclaimer": DISCLAIMER,
    }