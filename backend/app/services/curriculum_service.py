"""Curriculum Service - Epic 18 (Wave 8 Capstone).

Structured 6-module investment curriculum from balance-sheet basics to forensic
manipulation detection. Content is grounded in local universe numbers; no
external paid APIs. Quiz and flashcards are deterministic and self-contained.
Case studies map historic collapses/compounders to app metrics (Beneish, Altman,
Sloan, etc.). 10-K reader annotates where line items originate in SEC filings.
"""
from __future__ import annotations

from typing import Any

DISCLAIMER = "Personal research software, not investment advice."

CURRICULUM_MODULES: list[dict[str, Any]] = [
    {
        "id": "m01-balance-sheet",
        "title": "1. What Is a Balance Sheet?",
        "description": "Assets = Liabilities + Equity. Learn to read cash, receivables, inventory, debt and equity with a real company (RY, AAPL) example.",
        "lessons": [
            {"id": "l01", "title": "Assets: what the company owns", "body": "Cash + ST investments, receivables, inventory, PPE. Check Royal Bank (CA:RY:TSX) - cash is not free cash flow."},
            {"id": "l02", "title": "Liabilities & equity: who has claims", "body": "Total liabilities vs book equity. Bank vs non-bank treatment - banks report CET1, not corporate debt."},
            {"id": "l03", "title": "Common-size in one click", "body": "Every balance-sheet line as % of total assets. Spot a bloat >40% intangible (goodwill)."},
        ],
        "key_terms": ["Total Assets", "Book Equity", "Current Ratio", "Net Debt"],
        "quiz": [
            {"q": "What funds the assets? Liabilities + ?", "a": "Equity", "options": ["Equity", "Revenue", "Cash Flow"]},
            {"q": "Banks use which solvency ratio instead of Debt/Equity?", "a": "CET1", "options": ["CET1", "P/E", "PEG"]},
        ],
    },
    {
        "id": "m02-income-cashflow",
        "title": "2. Income & Cash Flow - From Revenue to FCF",
        "description": "Revenue → gross profit → operating income → net income → operating cash flow → FCF. Why cash matters more than accounting profit.",
        "lessons": [
            {"id": "l01", "title": "Revenue, gross and operating margin", "body": "Gross margin = gross profit / revenue. Watch deterioration >300 bps over 3y (margin contraction)."},
            {"id": "l02", "title": "The Ittelson bridge", "body": "NI → ±working capital → CFO → −CapEx → FCF → debt service → dividends → Δcash (CashFlowBridge SVG)."},
            {"id": "l03", "title": "Accruals (Sloan)", "body": "High accruals = NI far above CFO. High-accrual firms underperformed ~10%/yr in-sample (Sloan 1996) but edge decayed since."},
        ],
        "key_terms": ["Revenue", "Gross Margin", "FCF", "Sloan Accruals"],
        "quiz": [
            {"q": "FCF = ?", "a": "CFO − CapEx", "options": ["CFO − CapEx", "Revenue − COGS", "NI + Debt"]},
        ],
    },
    {
        "id": "m03-valuation",
        "title": "3. Valuation - DCF, EPV & Multiples Done Honestly",
        "description": "Guided DCF (Bear/Base/Bull, WACC, terminal >70% flag), EPV vs reproduction cost, Graham floors, reverse-DCF implied growth, and why PE across sectors is a trap.",
        "lessons": [
            {"id": "l01", "title": "Guided DCF with uncertainty", "body": "Explicit Rf + ERP×Beta WACC, 3 scenarios, P10–P90 range, terminal share warning."},
            {"id": "l02", "title": "EPV as a floor", "body": "Greenwald EPV vs market cap; reproduction cost proxied via assets - owned, not borrowed."},
            {"id": "l03", "title": "Multiples with context", "body": "PE/PB/EV-EBITDA percentiles vs same-currency peers only; current price mapped to DCF/Graham zones."},
        ],
        "key_terms": ["WACC", "Terminal Value", "EPV", "Reverse DCF"],
        "quiz": [
            {"q": "What share of DCF value from terminal is a fragile flag?", "a": ">70%", "options": [">70%", ">10%", ">95%"]},
        ],
    },
    {
        "id": "m04-pillars",
        "title": "4. The Four Pillars - Quality, Value, Growth, Risk",
        "description": "Locked weights 0.30/0.25/0.25/0.20. How each pillar is built, percentile-ranked, and penalized for missing data (NULL ≠ 0).",
        "lessons": [
            {"id": "l01", "title": "Quality = Piotroski + level quality", "body": "F-score 0–10 blended 70/30 with ROE/ROA/FCF margin/Novy-Marx GP/Assets."},
            {"id": "l02", "title": "Coverage penalty", "body": "4→×1.0, 3→×0.92, 2→×0.80, 1→×0.65, 0→NULL. Thin coverage is honest, not hidden."},
            {"id": "l03", "title": "Why scores skew low by design", "body": "713/718 lacking 3y history → growth NULL. Constructive 9 · mixed 136 · weak 345 · avoid 228 - explain, never hide."},
        ],
        "key_terms": ["Composite", "Coverage Penalty", "Peer Set", "Piotroski"],
        "quiz": [
            {"q": "Locked Quality weight?", "a": "0.30", "options": ["0.30", "0.40", "0.25"]},
        ],
    },
    {
        "id": "m05-forensics-intro",
        "title": "5. Forensics - Altman, Beneish & Sloan (Screens, Not Proof)",
        "description": "Altman Z/Z'' distress zones, Beneish M ≤ −1.78 manipulation screen, Sloan accruals, with false-positive disclosure.",
        "lessons": [
            {"id": "l01", "title": "Altman Z", "body": "Z > 2.99 Safe / 1.81–2.99 Grey / <1.81 Distress (manufacturing); Z'' variant for services. Banks excluded."},
            {"id": "l02", "title": "Beneish M", "body": "8-variable: DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA. M > −1.78 flags manipulation; ~14% false positives."},
            {"id": "l03", "title": "Benford χ²", "body": "First-digit distribution vs log10(1+1/d); n≥15, df=8; informational screen only."},
        ],
        "key_terms": ["Altman Z", "Beneish M", "Sloan", "Benford"],
        "quiz": [
            {"q": "Beneish threshold for flag?", "a": "-1.78", "options": ["-1.78", "-2.99", "1.81"]},
        ],
    },
    {
        "id": "m06-advanced-manipulation",
        "title": "6. Advanced Forensic Manipulation - Schilit, Sloan & Penman",
        "description": "Schilit shenanigans (DSO, inventory, covenant, goodwill), working-capital CCC (DSO/DIO/DPO), goodwill vs tangible strip, SBC dilution, Penman NOA/NFO/RNOA spread.",
        "lessons": [
            {"id": "l01", "title": "Schilit tactics", "body": "DSO spike, inventory buildup, covenant pressure, goodwill bloat ≥40%, serial-acquirer jumps >20%."},
            {"id": "l02", "title": "Penman reformulation", "body": "Separate operating (NOA, RNOA) from financing (NFO, FLEV); identity check within 5% of assets."},
            {"id": "l03", "title": "SBC dilution & shareholder yield", "body": "Buyback yield net of SBC drag = True Shareholder Yield. Organic float shrink >2% = ACCELERATED_BUYBACKS."},
        ],
        "key_terms": ["Schilit", "Penman RNOA", "CCC", "SBC Dilution"],
        "quiz": [
            {"q": "Goodwill bloat proxy threshold?", "a": "≥40% intangible", "options": ["≥40% intangible", "≥10% intangible", "≥80% intangible"]},
        ],
    },
]

CASE_STUDIES: list[dict[str, Any]] = [
    {
        "id": "enron-2001",
        "title": "Enron (2001) - The Collapse Before the Filing",
        "summary": "Inflated revenue via mark-to-market, hidden debt in SPEs, CFO decoupling (NI >> CFO), Beneish M well above −1.78, Sloan accruals high, Altman distress flag months before bankruptcy.",
        "metrics_mapped": ["Beneish M > −1.78", "Sloan high", "Altman Distress", "CFO vs NI divergence"],
        "lesson": "Forensics are screens, not prophecy - but they clustered here.",
    },
    {
        "id": "worldcom-2002",
        "title": "WorldCom (2002) - Capitalized Expenses",
        "summary": "Line costs capitalized as assets, not expenses. AQI spike, SGAI distortion, Penman leverage distortion, DSO anomaly.",
        "metrics_mapped": ["AQI", "DEPI", "SGAI", "Leverage distortion"],
        "lesson": "When expenses become assets, quality collapses first.",
    },
    {
        "id": "berkshire-compounder",
        "title": "Berkshire Compounders - The Boring Great Business",
        "summary": "Durable high ROIC, stable gross margin, low Sloan accruals, Fortress Altman Safe, True Shareholder Yield via buybacks net of SBC.",
        "metrics_mapped": ["ROIC persistence", "Gross margin stability", "Low accruals", "TSY"],
        "lesson": "Quality + Value + patience; moat proxies matter.",
    },
]

FLASHCARDS: list[dict[str, Any]] = [
    {"front": "What is the locked Quality weight?", "back": "0.30 (Value 0.25, Growth 0.25, Risk 0.20 inverted)."},
    {"front": "What does Beneish M > −1.78 mean?", "back": "High probability of earnings manipulation (screen, ~14% false positives, not proof)."},
    {"front": "Altman Z Distress threshold (manufacturing)?", "back": "Z < 1.81 (Safe > 2.99). Z'' for services: Safe > 2.60."},
    {"front": "Why is Growth NULL on most names?", "back": "Needs ≥3 positive FY points; owner workbook is FY-null seed (713/718) until backfill."},
    {"front": "CAD and USD money - can you average them?", "back": "Never. Cross-border = unitless ratios only (ROE, PE, PB, FCF margin). Money per currency segregated."},
    {"front": "PE across sectors - misuse example?", "back": "A low PE bank vs high PE software is not cheap vs expensive; sector-currency peers only."},
    {"front": "What is Sloan accrual ratio?", "back": "(NI − OCF)/assets; high accruals precede underperformance (Sloan 1996, weakened since)."},
    {"front": "True Shareholder Yield = ?", "back": "Dividend yield + net buyback yield (buybacks net of SBC dilution)."},
]


def get_modules() -> list[dict[str, Any]]:
    return CURRICULUM_MODULES


def get_module(module_id: str) -> dict[str, Any] | None:
    for m in CURRICULUM_MODULES:
        if m["id"] == module_id:
            return m
    return None


def get_flashcards(module_id: str | None = None) -> list[dict[str, Any]]:
    if module_id is None:
        return FLASHCARDS
    # Filter by module key terms if desired - for now return all with module context
    mod = get_module(module_id)
    if not mod:
        return []
    return FLASHCARDS


def get_quiz(module_id: str) -> dict[str, Any] | None:
    mod = get_module(module_id)
    if not mod:
        return None
    return {"module_id": module_id, "questions": mod.get("quiz", [])}


def get_case_studies() -> list[dict[str, Any]]:
    return CASE_STUDIES


def get_10k_reader(company_id: str) -> dict[str, Any]:
    # Guided annotation: where each snapshot line originates in the 10-K
    return {
        "company_id": company_id,
        "annotations": [
            {"line_item": "Revenue", "section": "Item 8 - Financial Statements, Income Statement", "note": "Top line; cross-check with revenue in FinancialSnapshot (source = owner xlsx | sec_companyfacts | yfinance)."},
            {"line_item": "Gross Profit", "section": "Item 8 - Income Statement", "note": "Not meaningful for banks/insurers (intentionally blank)."},
            {"line_item": "Operating Cash Flow", "section": "Item 8 - Cash Flow Statement", "note": "CFO vs NI divergence flags accrual concerns (Sloan)."},
            {"line_item": "Total Assets / Liabilities", "section": "Item 8 - Balance Sheet", "note": "Used for Altman Z, Penman NOA, goodwill vs tangible."},
            {"line_item": "Risk Factors", "section": "Item 1A - Risk Factors", "note": "Qualitative; not yet parsed numerically but informs bear-case prompts."},
        ],
        "source_hint": "EDGAR filing URL is on dossier Filings & Sources tab (CIK link) and SEDAR+ for CA names.",
        "disclaimer": DISCLAIMER,
    }