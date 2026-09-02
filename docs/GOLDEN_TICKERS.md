# Golden Ticker Validation Battery

Deterministic trust paths (Trust sprint D). Executed by `backend/tests/test_golden_tickers.py`;
run with `pytest backend/tests/test_golden_tickers.py -v` from the repo root, or
`python -m pytest tests/test_golden_tickers.py -v` from `backend/`.

| # | Golden path | Trust rule verified | Result |
|---|---|---|---|
| 1 | `US:MSFT:US` | EDGAR duration filter rejects quarterly facts; suspect FY rows are chipped `SCALE_OR_TAG_SUSPECT` + excluded from growth, never deleted; FY2017–2019 trusted revenue must be > $60B | PASS |
| 2 | `US:AAPL:US` | Buyback-shrunken invested capital: any ROIC > 100% or IC/assets < 5% forces `roic_confidence="low"` + `distorted_low_denominator`; UI never shows an unqualified green MOAT badge | PASS |
| 3 | `US:PYPL:US` | Payments/fintech: commercial fields (revenue/FCF/debt) stay populated; corporate ROIC suppressed as `not_meaningful` where classification applies — never CET1 | PASS |
| 4 | `CA:RY:TSX` | Canadian bank: company currency CAD (0 USD conversions); seed CET1/efficiency preserved via enrichment; TTM ROIC `not_meaningful` / `bank_excluded` | PASS |
| 5 | `CA:KITS:TSX` | Symbol normalization: `KITS.TO` → `CA:KITS:TSX`; frozen-id resolution; on-demand names enter the universe with the same trust rules | PASS |
| 6 | `US:BABA:US` | ADR: `reporting_currency=CNY` + trading USD → `currency_aligned=False`, price multiples suppressed with an explicit reason; SEC 20-F filing type supported | PASS |
| 7 | `US:AFL:US` | Insurer: corporate debt / gross profit never force-filled; ROIC `not_meaningful` / `bank_excluded` | PASS |
| 8 | `CA:IIP.UN:TSX` | Sparse-data path: `load_universe` tolerates NULL-heavy rows; composite `None` + `insufficient_data` signal; no division errors | PASS |
| 9 | `US:AMD:US` | On-demand ingest: `POST /api/v1/tickers/ingest` → 202 → state machine (`resolve → filings → prices_shares → sector_peers → score → done`) reaches a terminal state; score exists on success | PASS |
| 10 | `INVALID_TICKER_XYZ` | Graceful failure: job `failed` with `error_code=SYMBOL_NOT_FOUND` and actionable copy ("Try AMD, BABA, SHOP.TO, or KITS.TO.") | PASS |

Notes:

- Tests run against the ephemeral pytest database (imported once from the real owner
  workbook). On-demand names (KITS, BABA) are seeded as fixtures inside their tests —
  the deterministic part is the *rule*, not the provider payload.
- Every path is network-free except the ingest pipeline (local registry), which
  accepts either terminal state by design.
- The battery is the executable form of the trust contract; extend it whenever a new
  currency/asset-class rule lands.
