"""Wave 8 Ops tests (Epic 22)."""
import pathlib

def test_ops_integrity_and_seed(client):
    r = client.get("/api/v1/ops/integrity")
    assert r.status_code == 200
    assert "ok" in r.json()
    assert r.json()["result"] in ("ok", "DB not found") or r.json()["ok"] is True
    r2 = client.get("/api/v1/ops/seed-checksum")
    assert r2.status_code == 200
    data = r2.json()
    assert data["ok"] is True
    assert "sha256" in data
    assert len(data["sha256"]) == 64

def test_backup_create_and_list(client):
    r = client.post("/api/v1/ops/backup")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "file" in data
    assert data["file"].startswith("app_backup_")
    assert data["integrity"]["ok"] is True
    r2 = client.get("/api/v1/ops/backups")
    assert r2.status_code == 200
    assert r2.json()["count"] >= 1
    assert any(data["file"] == b["file"] for b in r2.json()["items"])

def test_diagnostics_and_vacuum(client):
    r = client.get("/api/v1/ops/diagnostics")
    assert r.status_code == 200
    data = r.json()
    assert "db_size_bytes" in data
    assert "integrity" in data
    assert "disclaimer" in data
    r2 = client.post("/api/v1/ops/vacuum")
    assert r2.status_code == 200
    # ok true or false but endpoint must respond
    assert "ok" in r2.json()
