"""FastAPI router for Field Shift operations.

Additive routes mounted under /solquira-api/studio/field-shift.
Preserves existing Studio session contracts and rate limits.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from .schema import FieldShiftInput, FieldShiftEvaluation
from .adapter import evaluate_field_shift

field_shift_router = APIRouter(prefix="/field-shift", tags=["field-shift"])


@field_shift_router.post("/evaluate", response_model=FieldShiftEvaluation)
async def evaluate_endpoint(payload: FieldShiftInput):
    """Evaluate multi-season NASA POWER indicators and rotation tradeoffs."""
    return evaluate_field_shift(payload)


@field_shift_router.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "domain": "field_shift",
        "source": "NASA POWER Daily Point AG",
        "rules": "Fail-closed, 100% complete seasonal windows",
    }
