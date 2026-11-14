"""Seasonal aggregation logic for NASA POWER daily time series.

Enforces strict temporal completeness. Incomplete seasons are excluded
rather than falsifying metrics with zero-padding.
"""
from __future__ import annotations
import math
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean, median


class SourceUnavailable(RuntimeError):
    """Raised when external data cannot be validated or has insufficient coverage."""
    pass


def season_label(season: str) -> str:
    return "April–September (Austral Autumn/Winter)" if season == "apr_sep" else "October–March (Austral Spring/Summer)"


def parse_power_daily(payload: dict, start: date, end: date) -> dict:
    """Validate and parse raw NASA POWER Daily Point API response.

    Fail-closed: requires time_standard=UTC and verified units.
    Sentinels (<= -900) are flagged as absent.
    """
    try:
        header = payload["header"]
        units = payload["parameters"]
        parameters = payload["properties"]["parameter"]
        rainfall = parameters["PRECTOTCORR"]
        temperature = parameters["T2M"]

        if (
            header.get("start") != start.strftime("%Y%m%d")
            or header.get("end") != end.strftime("%Y%m%d")
            or header.get("time_standard") != "UTC"
        ):
            raise SourceUnavailable("NASA time range or time standard does not match request (UTC required)")

        if units["PRECTOTCORR"]["units"] != "mm/day" or units["T2M"]["units"] != "C":
            raise SourceUnavailable("NASA returned unexpected or unsupported measurement units")
    except (TypeError, KeyError, ValueError) as err:
        raise SourceUnavailable("NASA response lacks validated metadata or variable parameters") from err

    days = (end - start).days + 1
    rows = []
    absent = 0

    for offset in range(days):
        current_date = start + timedelta(days=offset)
        stamp = current_date.strftime("%Y%m%d")
        if stamp not in rainfall or stamp not in temperature:
            raise SourceUnavailable("NASA payload does not cover the complete requested date range")

        rain = rainfall[stamp]
        temp = temperature[stamp]

        is_missing = (
            rain is None
            or temp is None
            or isinstance(rain, bool)
            or isinstance(temp, bool)
            or not isinstance(rain, (int, float))
            or not isinstance(temp, (int, float))
            or not math.isfinite(rain)
            or not math.isfinite(temp)
            or rain <= -900
            or temp <= -900
        )

        if is_missing:
            absent += 1
            continue

        if not (0.0 <= rain <= 1500.0 and -90.0 <= temp <= 75.0):
            raise SourceUnavailable("NASA payload contains out-of-physical-range values")

        rows.append({
            "date": current_date.isoformat(),
            "rain_mm": round(float(rain), 4),
            "temperature_c": round(float(temp), 4),
        })

    if len(rows) < 0.85 * days:
        raise SourceUnavailable("NASA data completeness is below required quality threshold")

    return {
        "rows": rows,
        "requested_days": days,
        "available_days": len(rows),
        "missing_days": absent,
    }


def seasonal_summary(rows: list[dict], season: str) -> dict:
    """Group daily records into discrete multi-year seasonal windows.

    apr_sep: Months 4 to 9 within the same calendar year.
    oct_mar: Months 10 to 12 of year Y, and months 1 to 3 of year Y+1 (indexed by start year Y).
    Requires at least 3 fully observed seasons.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        d = date.fromisoformat(row["date"])
        if season == "apr_sep" and 4 <= d.month <= 9:
            groups[str(d.year)].append(row)
        elif season == "oct_mar" and (d.month >= 10 or d.month <= 3):
            start_year = d.year if d.month >= 10 else d.year - 1
            groups[str(start_year)].append(row)

    samples = []
    for start_year_str, chosen in sorted(groups.items()):
        sy = int(start_year_str)
        first = date(sy, 4, 1) if season == "apr_sep" else date(sy, 10, 1)
        last = date(sy, 9, 30) if season == "apr_sep" else date(sy + 1, 3, 31)
        expected_days = (last - first).days + 1

        # Incomplete seasons are strictly discarded to avoid distorted seasonal aggregates
        if len(chosen) != expected_days:
            continue

        precip_sum = round(sum(r["rain_mm"] for r in chosen), 2)
        dry_frac = sum(1 for r in chosen if r["rain_mm"] < 1.0) / len(chosen)
        heavy_days = sum(1 for r in chosen if r["rain_mm"] >= 20.0)
        temp_mean = round(mean(r["temperature_c"] for r in chosen), 2)

        samples.append({
            "season_year": sy,
            "days": len(chosen),
            "precipitation_mm": precip_sum,
            "dry_day_fraction": round(dry_frac, 4),
            "heavy_rain_days": heavy_days,
            "temperature_mean_c": temp_mean,
        })

    if len(samples) < 3:
        raise ValueError(
            "At least three fully observed equivalent seasons are required for multi-year summary; "
            f"only {len(samples)} complete seasons found."
        )

    return {
        "label": season_label(season),
        "count": len(samples),
        "sample_years": [s["season_year"] for s in samples],
        "mean_rainfall_mm": round(mean(s["precipitation_mm"] for s in samples), 1),
        "median_rainfall_mm": round(median(s["precipitation_mm"] for s in samples), 1),
        "dry_day_fraction": round(mean(s["dry_day_fraction"] for s in samples), 4),
        "mean_heavy_rain_days": round(mean(s["heavy_rain_days"] for s in samples), 2),
        "mean_temperature_c": round(mean(s["temperature_mean_c"] for s in samples), 1),
        "sample": samples,
        "completeness_rule": "Only seasons with 100% daily observations are included; incomplete periods are excluded.",
    }
