"""Governance API - Epic 23 (Wave 8)."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.governance_service import get_canon_map, get_diff_matrix, get_model_risk_register

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


@router.get("/model-risk")
def model_risk():
    return get_model_risk_register()


@router.get("/canon-map")
def canon_map():
    return get_canon_map()


@router.get("/diff-matrix")
def diff_matrix():
    return get_diff_matrix()