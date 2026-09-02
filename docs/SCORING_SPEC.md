# SCORING_SPEC.md — Scoring Design (implemented in Phase 3; method_version=v1)

Status: locked design, implemented in Phase 3 (`app/services/scoring.py`, deterministic,
no LLM). This document remains the reference; deviations are documented in PHASE3_REPORT.md.

## Research framing

The output is a **research signal for a personal equity-research workflow, not a
trade order and not investment advice**. A score ranks candidates for further
manual research; it never instructs a buy/sell.

## Composite score (0–10)

    Composite = 0.30*Quality + 0.25*Value + 0.25*Growth + 0.20*Risk_inverted

Each pillar is normalized to 0–10 before weighting. **Risk is inverted** (low
risk → high contribution). Weights sum to 1.00.

### Quality (weight 0.30)

- Piotroski (2000)-style binary fundamentals tests (FScore components adapted to
  annual data availability): positive net income, positive operating cash flow,
  rising ROA, OCF > net income (accruals check), stable/growing margins.
- ROE and ROA levels, sector-aware (a bank and a software firm are not graded on
  the same ROE scale).
- FCF margin (FCF_Calc / Revenue) where FCF is meaningful — blank for
  banks/insurers by design, substituted with their alternate-quality metrics.
- Margin stability: dispersion of GrossMargin_Calc/FCFMargin_Calc across
  available history.

### Value (weight 0.25)

- Earnings yield (Diluted_EPS / Price) as the anchor.
- PE_Calc, PB_Calc, EV_to_EBITDA_Calc each compared **vs the median of the
  company's peer set**, never vs the other currency's dollars.
- Missing valuation inputs reduce the pillar's confidence, never get invented.

### Growth (weight 0.25)

- 5-year and 10-year CAGR of Revenue, Diluted_EPS, and FCF where history exists.
- Missing history is **penalized (scored conservatively), never guessed or
  extrapolated** from fewer points.

### Risk (weight 0.20, inverted)

- Net debt / EBITDA (NetDebt_Calc vs EBITDA) for corporates.
- Interest coverage (EBIT / Interest_Expense).
- Earnings volatility across available history.
- For banks: regulatory capital (CET1_Ratio vs CET1_Requirement_or_Target)
  replaces leverage metrics; NIM and Efficiency_Ratio inform quality/health.

## Alternate metric sets

- **Banks/insurers:** CET1_Ratio, Total_Capital_Ratio, Leverage_Ratio, NIM
  (FY and Q4), Efficiency_Ratio, ROAA, TopLine_Alt (net interest income as the
  revenue concept). Corporate Total_Debt / FCF / Gross_Profit are meaningless
  for them and stay NULL — the scorer must branch on metric set, not backfill.
- **REITs:** FFO/AFFO-based payout and valuation rather than EPS/PE (fields to
  be added in a later phase if sourced).

## Peer set

1. Same `custom_industry_sheet` first (the owner's 30 home tabs).
2. Else same GICS industry.
3. **Money fields are always split by currency** within a peer set: USD peers
   are only compared to USD peers, CAD to CAD. Cross-border comparisons use
   unitless ratios only (ROE_Calc, ROA_Calc, FCFMargin_Calc, GrossMargin_Calc,
   PE_Calc, PB_Calc, EV_to_EBITDA_Calc).

## Research signal map (not an order)

| Composite | Signal |
|-----------|--------|
| 8–10 | Strong candidate |
| 6.5–7.9 | Constructive |
| 5–6.4 | Mixed |
| 3.5–4.9 | Weak |
| 0–3.4 | Avoid |

The signal describes research priority. It is never an instruction to trade.

## Halal flag (a FLAG, never a filter)

Screens applied independently; the flag is informational metadata for the user.

- **Business-activity screen:** keyword screen over company name/industry for
  prohibited activities (conventional finance, alcohol, tobacco, gambling,
  adult entertainment, weapons, pork production).
- **Financial ratios (AAOIFI-style thresholds):**
  - Interest-bearing debt / Market_Cap ≤ 30%
  - Interest-bearing assets / Market_Cap ≤ 30%
  - Impure (non-compliant) income / Revenue ≤ 5%
- If any input is missing (e.g. interest-bearing assets not sourced in Phase 1),
  the flag is **unknown — never halal by default**.

## Methodology notes (cited ideas, not endorsements)

- Piotroski (2000), "Value Investing: The Use of Historical Financial Statement
  Information to Separate Winners from Losers" — binary FScore tests.
- Greenblatt, "The Little Book That Beats the Market" — Magic Formula: cheapness
  (earnings yield) combined with quality (return on capital).
- AAOIFI-style Shariah screens — the 30%/30%/5% ratio thresholds above.

## Limitations

- Latest-FY snapshot only in Phase 1; growth and stability need history (Phase 2+).
- No FX conversion means scale metrics (Revenue, Market_Cap) are not comparable
  across borders; only ratios are.
- Owner-workbook values are vendor/file-derived and contain intentional blanks;
  coverage gaps translate directly into scoring gaps.
- Binary tests degrade gracefully but silently when data is sparse — the scorer
  must expose a per-company coverage/confidence note alongside any score.
- This is not investment advice; thresholds are heuristic.
