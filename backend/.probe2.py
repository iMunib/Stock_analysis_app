# probe: does process_one claim anything, and is the DB the same file the client sees?
import os
os.environ["DATABASE_URL"] = "sqlite:///./.probe2.db"
if os.path.exists(".probe2.db"): os.remove(".probe2.db")
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)  # lifespan: worker disabled via env? check
print("worker disabled env:", os.environ.get("JOBS_WORKER_DISABLED"))
r1 = c.post("/api/v1/jobs/backfill", json={"mode":"sample","limit":1})
print("r1:", r1.status_code)
from app.db import SessionLocal
from app.services import jobs as jobsvc
from app.services.job_worker import JobWorker
db = SessionLocal()
row = jobsvc.get_job(db, r1.json()["job_id"])
print("as seen by SessionLocal:", row.status if row else "MISSING")
db.close()
w = JobWorker()
got = w.process_one()
print("process_one returned:", got)
db = SessionLocal()
row = jobsvc.get_job(db, r1.json()["job_id"])
print("after process_one:", row.status if row else "MISSING")
db.close()
engine.dispose() if False else None
