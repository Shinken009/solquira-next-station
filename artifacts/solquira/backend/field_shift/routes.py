"""Admitted FastAPI routes for NASA Field Shift.

Reuses Studio's opaque session, CSRF, Host/Origin checks, bounded request parsing,
and dedicated NASA POWER rate/concurrency budget. The blocking historical
connector runs in a worker thread whose admission lease survives cancellations.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from .schema import FieldShiftInput, FieldShiftEvaluation
from .adapter import evaluate_field_shift

# studio_api loads this router after defining its security primitives. Using
# those primitives is required: a standalone Pydantic endpoint bypassed CSRF.
from studio_api import _admitted, _body, _json, _require_mode, _run_service, _validate

field_shift_router = APIRouter(prefix="/field-shift", tags=["field-shift"])


@field_shift_router.post("/evaluate", response_model=FieldShiftEvaluation)
async def evaluate_endpoint(request: Request):
    """Evaluate verified historical NASA POWER data within Studio admission."""
    async with _admitted(request, power=True) as lease:
        payload = _validate(FieldShiftInput, await _body(request))
        try:
            result = await asyncio.wait_for(
                _run_service(lease, evaluate_field_shift, payload),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            # _run_service keeps the slot until the worker really finishes.
            raise HTTPException(
                504, "NASA POWER lookup timed out. No seasonal estimate was invented."
            ) from None
        except Exception:
            # Never echo provider response, coordinates, or internal exception.
            raise HTTPException(
                503, "NASA POWER evaluation is unavailable. No estimate was invented."
            ) from None

        return _json(result.model_dump())


@field_shift_router.get("/healthz")
async def healthz():
    """Harmless metadata only; not a data/compute capability."""
    _require_mode()
    return {
        "status": "healthy",
        "domain": "field_shift",
        "source": "NASA POWER Daily Point AG",
        "rules": "Fail-closed, 100% complete seasonal windows",
    }
