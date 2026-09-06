"""Ops & Backup API - Epic 22 (Wave 8)."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.backup_service import (
    create_backup,
    get_diagnostics,
    list_backups,
    restore_backup,
    run_integrity_check,
    run_vacuum,
    verify_seed_checksum,
)

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


@router.post("/backup")
def backup():
    return create_backup()


@router.get("/backups")
def backups():
    return list_backups()


@router.post("/restore/{filename}")
def restore(filename: str):
    return restore_backup(filename)


@router.get("/integrity")
def integrity():
    return run_integrity_check()


@router.get("/seed-checksum")
def seed_checksum():
    return verify_seed_checksum()


@router.get("/diagnostics")
def diagnostics():
    return get_diagnostics()


@router.post("/vacuum")
def vacuum():
    return run_vacuum()