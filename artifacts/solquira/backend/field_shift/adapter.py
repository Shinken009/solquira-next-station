"""NASA POWER historical adapter for Field Shift.

Executes bounded multi-year requests with in-memory caching and fail-closed handling.
Never produces synthetic observations.
"""
from __future__ import annotations
import copy
import json
import logging
import math
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import date, datetime, timezone
from typing import Optional

from .schema import (
    FieldShiftInput,
    FieldShiftEvaluation,
    SeasonalContext,
    SeasonSample,
    SourceProvenance,
)
from .seasonal import parse_power_daily, seasonal_summary, SourceUnavailable
from .tradeoffs import compare_pathways

logger = logging.getLogger(__name__)

ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ("PRECTOTCORR", "T2M")
DEFAULT_START = date(2021, 1, 1)
DEFAULT_END = date(2025, 12, 31)

CACHE_TTL_SECONDS = 21600  # 6 hours
CACHE_MAX_ENTRIES = 32
_CACHE: OrderedDict[tuple, tuple[float, dict]] = OrderedDict()
_LOCK = threading.Lock()


def query_historical_power(
    latitude: float,
    longitude: float,
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    timeout_s: float = 25.0,
) -> dict:
    """Fetch and cache multi-year daily NASA POWER observations."""
    grid_lat = round(latitude, 2)
    grid_lon = round(longitude, 2)
    cache_key = (grid_lat, grid_lon, start.isoformat(), end.isoformat())

    now = time.monotonic()
    with _LOCK:
        if cache_key in _CACHE:
            cached_time, cached_val = _CACHE[cache_key]
            if now - cached_time < CACHE_TTL_SECONDS:
                _CACHE.move_to_end(cache_key)
                return copy.deepcopy(cached_val)

    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": str(grid_lon),
        "latitude": str(grid_lat),
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC",
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Solquira-Next-Station/2.0 (NASA Space Apps 2026; https://github.com/Shinken009/solquira-next-station)",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            if resp.status != 200:
                raise SourceUnavailable(f"NASA POWER returned HTTP status {resp.status}")
            raw_bytes = resp.read()
            if len(raw_bytes) > 4_000_000:
                raise SourceUnavailable("NASA payload exceeded maximum allowable size limit")
            payload = json.loads(raw_bytes.decode("utf-8"))

        normalized = parse_power_daily(payload, start, end)
        normalized["source_url"] = url
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        logger.warning(f"NASA POWER request failed: {exc}")
        raise SourceUnavailable(f"NASA POWER is currently unavailable or returned an unreadable payload: {exc}") from exc

    with _LOCK:
        _CACHE[cache_key] = (time.monotonic(), copy.deepcopy(normalized))
        _CACHE.move_to_end(cache_key)
        while len(_CACHE) > CACHE_MAX_ENTRIES:
            _CACHE.popitem(last=False)

    return normalized


def evaluate_field_shift(field_input: FieldShiftInput, timeout_s: float = 25.0) -> FieldShiftEvaluation:
    """End-to-end evaluation connecting verified NASA data with rotation alternatives."""
    try:
        raw_data = query_historical_power(
            field_input.latitude,
            field_input.longitude,
            DEFAULT_START,
            DEFAULT_END,
            timeout_s=timeout_s,
        )
        context_dict = seasonal_summary(raw_data["rows"], field_input.season)
        pathways = compare_pathways(context_dict, field_input)

        provenance = SourceProvenance(
            requested_latitude=round(field_input.latitude, 2),
            requested_longitude=round(field_input.longitude, 2),
            original_latitude=field_input.latitude,
            original_longitude=field_input.longitude,
            period_start=DEFAULT_START.isoformat(),
            period_end=DEFAULT_END.isoformat(),
            source_url=raw_data.get("source_url", ENDPOINT),
        )

        seasonal_context = SeasonalContext(
            label=context_dict["label"],
            count=context_dict["count"],
            sample_years=context_dict["sample_years"],
            mean_rainfall_mm=context_dict["mean_rainfall_mm"],
            median_rainfall_mm=context_dict["median_rainfall_mm"],
            dry_day_fraction=context_dict["dry_day_fraction"],
            mean_heavy_rain_days=context_dict["mean_heavy_rain_days"],
            mean_temperature_c=context_dict["mean_temperature_c"],
            sample=[SeasonSample(**s) for s in context_dict["sample"]],
            completeness_rule=context_dict["completeness_rule"],
        )

        return FieldShiftEvaluation(
            version="solquira.field-shift/2.0",
            status="historical_evidence_available",
            input=field_input,
            historical_context=seasonal_context,
            pathways=pathways,
            provenance=provenance,
            quality={
                "requested_days": raw_data["requested_days"],
                "available_days": raw_data["available_days"],
                "missing_days": raw_data["missing_days"],
            },
            assumptions={
                "dry_day_threshold": "< 1.0 mm/day (descriptive frequency)",
                "heavy_rain_threshold": ">= 20.0 mm/day (descriptive count)",
                "seasonal_inclusion": "100% complete daily observation required for each included season",
                "tradeoff_nature": "Comparative exploratory indicators, not agronomic crop suitability prescriptions",
            },
            disclaimers=[
                "NASA POWER data are model-assimilated historical grid estimates, not on-site parcel measurements.",
                "Past multi-season observations are not a seasonal weather forecast for 2026/2027.",
                "Soil and drainage characteristics are self-reported by the operator and require field verification.",
                "Agronomic feasibility remains unassessed; obtain local agronomic extension counsel before implementation.",
            ],
        )

    except SourceUnavailable as e:
        logger.error(f"Field shift source unavailable: {e}")
        # Return structured unavailable object without inventing numbers
        return FieldShiftEvaluation(
            version="solquira.field-shift/2.0",
            status="source_unavailable",
            input=field_input,
            historical_context=None,
            pathways=[],
            provenance=SourceProvenance(
                requested_latitude=round(field_input.latitude, 2),
                requested_longitude=round(field_input.longitude, 2),
                original_latitude=field_input.latitude,
                original_longitude=field_input.longitude,
                period_start=DEFAULT_START.isoformat(),
                period_end=DEFAULT_END.isoformat(),
                source_url=ENDPOINT,
            ),
            quality={"requested_days": 0, "available_days": 0, "missing_days": 0},
            assumptions={"status": "external_source_temporarily_unreachable"},
            disclaimers=[str(e), "Fail-closed safety policy active: synthetic observations are strictly prohibited."],
        )
