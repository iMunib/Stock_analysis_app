# AGENTS.md
Personal equity-research app. Local Docker. Not investment advice. Not a product.

Stack: FastAPI, SQLAlchemy2, SQLite, React+Vite+TS+Tailwind, Compose.
IDs: US:TICKER:US | CA:TICKER:TSX. Never mix CAD and USD money. Ratios only for cross-border.
Do not run refresh.py --mode all. Do not invent numbers. NULL + flag if missing.
Banks/insurers: leave corporate debt/FCF/gross blank when the seed left them blank.
Halal is a flag (AAOIFI-style), never a filter.
LLM: OpenRouter only, cache outputs, never let the model overwrite fundamentals.
Work the current PHASE prompt only. On EXIT CHECK pass, stop and write the phase report.
No questions to the user. Conservative default + log it.
Secrets in .env. No paid APIs in v1.
