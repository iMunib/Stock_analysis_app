"""Curriculum API - Epic 18 (Wave 8)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.curriculum_service import (
    DISCLAIMER,
    get_10k_reader,
    get_case_studies,
    get_flashcards,
    get_module,
    get_modules,
    get_quiz,
)

router = APIRouter(prefix="/api/v1/curriculum", tags=["curriculum"])


@router.get("/modules")
def modules():
    return {"count": len(get_modules()), "items": get_modules(), "disclaimer": DISCLAIMER}


@router.get("/modules/{module_id}")
def module_detail(module_id: str):
    m = get_module(module_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Module {module_id} not found")
    return {**m, "disclaimer": DISCLAIMER}


@router.get("/flashcards")
def flashcards(module_id: str | None = None):
    cards = get_flashcards(module_id)
    return {"count": len(cards), "items": cards, "disclaimer": DISCLAIMER}


@router.get("/quiz/{module_id}")
def quiz(module_id: str):
    q = get_quiz(module_id)
    if not q:
        raise HTTPException(status_code=404, detail=f"Module {module_id} not found")
    return {**q, "disclaimer": DISCLAIMER}


@router.get("/case-studies")
def case_studies():
    return {"count": len(get_case_studies()), "items": get_case_studies(), "disclaimer": DISCLAIMER}


@router.get("/10k-reader/{company_id}")
def reader(company_id: str):
    return get_10k_reader(company_id)