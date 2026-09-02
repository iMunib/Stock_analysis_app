# reproduce the 202/409 flow: is the real (202) route registered at all, and what does the worker do to queued jobs?
from fastapi.testclient import TestClient
import os
os.environ["DATABASE_URL"] = "sqlite:///./.probe_jobs.db"
if os.path.exists(".probe_jobs.db"): os.remove(".probe_jobs.db")
from app.db import Base, engine
import app.models
Base.metadata.create_all(bind=engine)
from app.main import app
c = TestClient(app)
r1 = c.post("/api/v1/jobs/backfill", json={"mode":"sample","limit":1})
print("r1:", r1.status_code, r1.json())
r2 = c.post("/api/v1/jobs/backfill", json={"mode":"sample","limit":1})
print("r2:", r2.status_code)
import time; time.sleep(4)  # give the live lifespan worker time to run the sample job
g = c.get(f"/api/v1/jobs/{r1.json()['job_id']}")
print("after sleep:", g.json()["status"], g.json()["progress_done"], "/", g.json()["progress_total"])
r3 = c.post("/api/v1/jobs/backfill", json={"mode":"sample","limit":1})
print("r3 (after first finished):", r3.status_code)
engine.dispose()
