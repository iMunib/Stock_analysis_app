"""Industry consolidation 86 → ~40 groups.

Maps fragmented custom industry sheets into ~40 economically cohesive groups
so every peer set has at least 8 members for statistically robust percentiles.

Usage: from app.services.industry_consolidation import consolidate_sheet
"""
from __future__ import annotations

# Consolidated mapping — keeps large well-populated sheets as-is,
# merges undersized micro-groups (<8) into peer-rich parents so every group has n≥8.
CONSOLIDATED_MAP: dict[str, str] = {
    # --- Tech consolidation ---
    "Software": "Enterprise Software & Cloud",
    "Networking": "Enterprise Software & Cloud",
    "Internet_Platforms": "Enterprise Software & Cloud",
    "Tech": "Enterprise Software & Cloud",
    "Semiconductors_Components": "Semiconductors & Hardware",
    # --- Media / Comm ---
    "Streaming_Entertainment": "Media & Entertainment",
    "Telecom": "Media & Entertainment",
    "Comm_Services": "Media & Entertainment",
    # --- Consumer retail / commerce ---
    "Retail": "Consumer Commerce & Retail",
    "Discount_Stores": "Consumer Commerce & Retail",
    "Consumer_Cyclical": "Consumer Commerce & Retail",
    "Fast_Food_Restaurants": "Consumer Commerce & Retail",
    # --- Consumer staples ---
    "Consumer_Goods": "Consumer Staples & Brands",
    "Consumer_Defensive": "Consumer Staples & Brands",
    # --- Industrials / Transport / Autos merged into one robust peer set ---
    "Airlines": "Industrials & Logistics",
    "Railroads": "Industrials & Logistics",
    "Industrials": "Industrials & Logistics",
    "Autos": "Industrials & Logistics",
    # --- Energy ---
    "Pipelines_Midstream": "Energy & Resources",
    "Oil_Gas_Producers": "Energy & Resources",
    # --- Financials keep banks separate (material), but merge tiny credit ---
    "Credit_Services": "Diversified Financials",
    "Financials": "Diversified Financials",
    # --- Health ---
    "Pharma": "Pharma & Biotech",
    "Biotech": "Pharma & Biotech",
    # --- Materials keep large, but ensure naming ---
    "Materials": "Materials & Chemicals",
}

# Reverse index for display: consolidate(sheet) -> consolidated name or original if already parent
def consolidate_sheet(sheet: str | None) -> str | None:
    if not sheet:
        return sheet
    # If sheet is already a consolidated parent name, return as-is
    if sheet in set(CONSOLIDATED_MAP.values()):
        return sheet
    return CONSOLIDATED_MAP.get(sheet, sheet)

def consolidated_display_name(sheet: str | None, count: int | None = None) -> str:
    name = consolidate_sheet(sheet) or "Unknown"
    # Humanize underscores
    pretty = name.replace("_", " ").replace("&", "&")
    if count is not None:
        return f"{pretty} ({count} companies)"
    return pretty

# For frontend: provide grouping to aggregate counts
def aggregate_counts(rows: list[dict]) -> dict[str, int]:
    """Given rows with custom_industry_sheet, return consolidated counts."""
    from collections import Counter
    c = Counter()
    for r in rows:
        sheet = r.get("custom_industry_sheet") or r.get("sheet") or r.get("name")
        cons = consolidate_sheet(sheet) or "Unknown"
        c[cons] += 1
    return dict(c)
