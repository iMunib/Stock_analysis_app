"""Governance Service - Epic 23 (Wave 8 Capstone).

Model Risk Register (assumptions, false positives, blind spots per model),
canon literature cross-reference (Graham, Buffett, Lynch, Fisher, Greenwald),
and competitive diff matrix vs Seeking Alpha / Simply Wall St / TIKR / GuruFocus.
All governance is local, deterministic, and carries the standard disclaimer.
"""
from __future__ import annotations

from typing import Any

DISCLAIMER = "Personal research software, not investment advice."

MODEL_RISK_REGISTER: list[dict[str, Any]] = [
    {
        "model": "Composite 0.30Q/0.25V/0.25G/0.20R (Risk inverted) + coverage penalty",
        "assumption": "Weights are evidence-aligned (Quality/Value/Growth/Risk) and frozen; growth penalized when missing (713/718 have NULL growth).",
        "false_positive": "Scores skew low by design (mixed 136, weak 345, avoid 228) due to penalty, not poor quality - explain, never hide.",
        "blind_spot": "Single-year growth excluded; peer set widens to broad when custom <8; momentum (12-1) is context only, not a pillar.",
        "mitigation": "Drilldown shows exact inputs, percentiles, NULL reasons, thresholds; methodology version v1 pinned.",
    },
    {
        "model": "Piotroski F-Score (9 checks)",
        "assumption": "1976–96 sample; regime-dependent since. Impossible tests reduce denominator, not score 0.",
        "false_positive": "~15% false-positive territory in forensic literature; date-stamp 2000, decay disclosed.",
        "blind_spot": "Value-conditioned only; not standalone alpha.",
        "mitigation": "F-score shown with per-test pass/fail and accruals current-year logic.",
    },
    {
        "model": "Beneish M-Score (8-variable, M > −1.78)",
        "assumption": "Flags manipulators in/out-of-sample at −1.78; mixed cross-market validation.",
        "false_positive": "~14% false positives; screen, not proof.",
        "blind_spot": "Banks/insurers excluded (financial_institution_excluded) to avoid false alarms on regulated sheets.",
        "mitigation": "Component drilldown DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA; disclaimer on every flag.",
    },
    {
        "model": "Altman Z / Z''",
        "assumption": "~72% original accuracy; 80–90% one year prior; Z'' generalizes to non-manufacturers.",
        "false_positive": "Cutoffs 2.99/1.81 (manufacturing) and 2.60/1.10 (Z'') - grey zone is real, not binary.",
        "blind_spot": "Banks/insurers excluded; leverage-distorted ROIC handled separately.",
        "mitigation": "Gauge with Safe/Grey/Distress bands + bank exclusion banner.",
    },
    {
        "model": "Sloan Accruals",
        "assumption": "High accruals (NI >> CFO) underperform ~10%/yr in-sample, weakened since (M grade).",
        "false_positive": "Regime-dependent; never standalone.",
        "blind_spot": "Cash conversion complements Sloan; both shown.",
        "mitigation": "Accrual ratio + cash conversion ratio on forensics; flagged vs peer percentile.",
    },
    {
        "model": "12-1 Momentum (Jegadeesh & Titman 1993)",
        "assumption": "~1%/month decile spread, persists out-of-sample; crashes possible.",
        "false_positive": "Momentum crash risk acknowledged; not a scoring pillar.",
        "blind_spot": "Skips most recent month to avoid reversals; labeled market sentiment context only.",
        "mitigation": "Displayed as context on Technicals, never in composite.",
    },
    {
        "model": "Greenwald EPV & Graham Number",
        "assumption": "EPV vs reproduction cost anchors floors; Graham Number = sqrt(22.5*EPS*BPS).",
        "false_positive": "Reproduction cost proxied via assets; circular for asset-light firms.",
        "blind_spot": "Peak vs mid-cycle earnings; normalized path needed for cyclicals.",
        "mitigation": "Shown with replication cost disclosure and mid-cycle toggle.",
    },
    {
        "model": "Penman Reformulation (NOA/NFO/RNOA/FLEV)",
        "assumption": "Equity identity check within 5% of assets; minority-interest gaps flagged identity_ok=false.",
        "false_positive": "Leverage distortion when FLEV >3 or equity <10% assets (36 names flagged).",
        "blind_spot": "Forensic lens, not verdict.",
        "mitigation": "Leverage distortion badge; banks excluded.",
    },
]

CANON_MAP: list[dict[str, Any]] = [
    {"book": "Benjamin Graham - The Intelligent Investor", "app_feature": "Defensive 7 via Screener presets; current ratio ≥2; PE×PB ≤22.5; margin of safety gauge on GrahamCard", "check": "Graham Deep Bargains, NCAV, NNWC"},
    {"book": "Warren Buffett - Berkshire Letters", "app_feature": "Owner earnings (Buffett-style) in waterfall; DuPont ROE decomposition; moat trend via gross-margin stability", "check": "Owner earnings calc; retained-dollar test prompt"},
    {"book": "Philip Fisher - Common Stocks… (15 points)", "app_feature": "Qualitative checklist in curriculum + scuttlebutt question bank; R&D effectiveness via margin trend", "check": "Fisher checklist module"},
    {"book": "Peter Lynch - One Up on Wall Street", "app_feature": "PEG/dividend-adjusted PEG <1.0; six categories classifier; inventory/receivables divergence flags", "check": "Lynch Stalwarts / Growers presets"},
    {"book": "Howard Marks - The Most Important Thing", "app_feature": "Cycle-position context via sector cycle tags (Early/Late/Defensive/Recessional)", "check": "Sector cycle tag on rotation"},
    {"book": "Bruce Greenwald - Value Investing", "app_feature": "EPV vs reproduction cost as floor estimate in EPVCard", "check": "Greenwald EPV"},
    {"book": "Joel Greenblatt - The Little Book", "app_feature": "EV/EBIT + ROIC dual ranking magic formula preset", "check": "Greenblatt Formula preset"},
    {"book": "Pat Dorsey - Five Rules", "app_feature": "Moat-type tags (intangibles, switching costs, network) via observable proxies", "check": "Moat durability verdict"},
    {"book": "Seth Klarman - Margin of Safety", "app_feature": "DCF intrinsic range vs price margin-of-safety; bear case equal billing", "check": "Valuation margin gauge"},
    {"book": "Aswath Damodaran - Valuation", "app_feature": "Assumption-explicit Guided DCF + sensitivity tables (Bear/Base/Bull)", "check": "Guided DCF modal"},
]

DIFF_MATRIX: dict[str, Any] = {
    "columns": ["Feature", "This App (verified)", "Seeking Alpha", "Simply Wall St", "TIKR", "GuruFocus"],
    "rows": [
        ["Forensic suite (Beneish/Altman/Sloan/Penman/Benford/Schilit)", "✅ Full suite, component drilldown, false-positive disclosure", "❌", "❌", "limited", "⚠️ warning signs only"],
        ["Canadian TSX + CAD/USD segregation", "✅ 220 TSX, native CAD, TFSA/RRSP/FHSA context, dual-listed RY/SHOP/ENB", "thin TSX", "global but black-box", "global", "US-heavy"],
        ["Deterministic 0–10 composite + drilldown", "✅ Locked 0.30/0.25/0.25/0.20, coverage penalty, NULL honesty, percentile matrix", "Quant grades (opaque)", "Snowflake (black-box)", "no rating", "opaque scores"],
        ["12-1 Momentum as context only", "✅ Jegadeesh 1993, never a pillar", "Not reported in filing", "Not reported in filing", "Not reported in filing", "Not reported in filing"],
        ["Reproducible provenance (source, as-of, lag)", "✅ Every metric carries source/fetched_at/provider_as_of; Form 4 lag label", "limited", "limited", "terminal", "limited"],
        ["Local-first, free core, no cloud", "✅ Docker + SQLite WAL, offline months, one-click backup", "cloud", "cloud", "cloud", "cloud"],
        ["Price", "Free local core (gap under ~$150/yr)", "$239–299/yr", "~$10.95/mo", "Free–$119.95", "$499–2448/yr"],
    ],
    "disclaimer": DISCLAIMER,
}


def get_model_risk_register() -> dict[str, Any]:
    return {"count": len(MODEL_RISK_REGISTER), "items": MODEL_RISK_REGISTER, "disclaimer": DISCLAIMER}


def get_canon_map() -> dict[str, Any]:
    return {"count": len(CANON_MAP), "items": CANON_MAP, "disclaimer": DISCLAIMER}


def get_diff_matrix() -> dict[str, Any]:
    return DIFF_MATRIX