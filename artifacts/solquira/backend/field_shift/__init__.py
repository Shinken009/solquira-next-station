"""Field Shift domain for Solquira Next Station.

Integrates multi-season NASA POWER historical gridded observations with
deterministic exploratory rotation tradeoffs. Fail-closed, no synthetic data.
"""
from .schema import FieldShiftInput, FieldShiftEvaluation
from .seasonal import seasonal_summary, parse_power_daily
from .tradeoffs import compare_pathways, PATHWAYS

__all__ = [
    "FieldShiftInput",
    "FieldShiftEvaluation",
    "seasonal_summary",
    "parse_power_daily",
    "compare_pathways",
    "PATHWAYS",
]
