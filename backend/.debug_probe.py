import os
os.environ["DATABASE_URL"] = "sqlite:///./.debug_import.db"
if os.path.exists(".debug_import.db"): os.remove(".debug_import.db")
from app.db import Base, SessionLocal, engine
import app.models
from app.config import find_seed_workbook
from app.services.importer import _import_companies, _import_placements, _import_quality, _sheet_rows
import openpyxl
from sqlalchemy import select, func
from app.models import Company, Placement

Base.metadata.create_all(bind=engine)
db = SessionLocal()
wb = openpyxl.load_workbook(find_seed_workbook(), read_only=True, data_only=True)
n = _import_companies(db, wb, "Sector_Financials_Final_Owner.xlsx")
print("companies imported:", n)
print("pending in session.new:", len(db.new))
# Probe: does db.get find a pending company?
print("db.get pending US:MMM:US:", db.get(Company, "US:MMM:US") is not None)
print("db.get pending CA:RY:TSX:", db.get(Company, "CA:RY:TSX") is not None)
p = _import_placements(db, wb)
print("placements imported:", p)
q = _import_quality(db, wb)
print("flags imported:", q)
db.commit()
print("DB placement rows:", db.execute(select(func.count()).select_from(Placement)).scalar_one())
print("DB company rows:", db.execute(select(func.count()).select_from(Company)).scalar_one())
db.close(); engine.dispose()
os.remove(".debug_import.db")
