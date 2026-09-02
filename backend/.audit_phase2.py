import os
os.environ["DATABASE_URL"] = "sqlite:///../data/app.db"
from sqlalchemy import create_engine, text
e = create_engine(os.environ["DATABASE_URL"])
with e.connect() as c:
    print("placements by role:", c.execute(text("SELECT placement_role, COUNT(*) FROM placements GROUP BY placement_role")).all())
    # quality flag coverage vs sheet: find raw IDs in 03_Data_Quality that did not match
    import openpyxl
    wb = openpyxl.load_workbook("../seed/Sector_Financials_Final_Owner.xlsx", read_only=True, data_only=True)
    ws = wb["03_Data_Quality"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(x).strip() if x else "" for x in rows[0]]
    i_id = hdr.index("Company_ID")
    ids_sheet = [str(r[i_id]).strip() for r in rows[1:] if r and r[i_id]]
    wb.close()
    master = {x[0] for x in c.execute(text("SELECT company_id FROM companies")).all()}
    stored = {x[0] for x in c.execute(text("SELECT DISTINCT company_id FROM data_quality_flags")).all()}
    def norm(raw):
        parts = raw.split(":")
        if len(parts) != 3: return None
        c_, t_, s_ = parts[0].upper(), parts[1].strip().upper(), parts[2].upper()
        if c_ == "US": return f"US:{t_}:US"
        if c_ == "CA": return f"CA:{t_}:TSX"
        return None
    unresolved = {}
    for raw in set(ids_sheet):
        n = norm(raw)
        if n is None or n not in master:
            unresolved[raw] = n
    print("distinct raw sheet ids:", len(set(ids_sheet)))
    print("unresolved raw ids:", len(unresolved))
    for k, v in sorted(unresolved.items()):
        print("  RAW:", k, "-> norm:", v, "| in master as-is:", k in master)
    print("stored distinct companies with flags:", len(stored))
e.dispose()
