"""Comprehensive unit tests for the Field Shift domain.

Tests:
- Strict unit validation & UTC time-standard enforcement
- Discarding of incomplete seasonal windows (fail-closed, no zero-padding)
- Deterministic response to NASA signals (precipitation & drought exposure)
- Unassessed agronomic viability invariant
- FastAPI integration on /solquira-api/studio/field-shift
"""
from __future__ import annotations
import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from field_shift.schema import FieldShiftInput, FieldShiftEvaluation
from field_shift.seasonal import parse_power_daily, seasonal_summary, SourceUnavailable
from field_shift.tradeoffs import compare_pathways, PATHWAYS
from main import app


def synthetic_power_rows(heavy: bool = False, missing_day: str | None = None) -> list[dict]:
    """Generate deterministic synthetic daily rows for testing."""
    start = date(2021, 1, 1)
    end = date(2025, 12, 31)
    rows = []
    curr = start
    while curr <= end:
        iso = curr.isoformat()
        if missing_day and iso == missing_day:
            curr += timedelta(days=1)
            continue
        rain = 25.0 if heavy and curr.day in (3, 10, 17, 24) else (0.0 if not heavy else 2.0)
        rows.append({"date": iso, "rain_mm": rain, "temperature_c": 15.0})
        curr += timedelta(days=1)
    return rows


def synthetic_payload(rain_unit: str = "mm/day", temp_unit: str = "C", time_std: str = "UTC") -> dict:
    return {
        "header": {"start": "20250101", "end": "20250102", "time_standard": time_std},
        "parameters": {
            "PRECTOTCORR": {"units": rain_unit},
            "T2M": {"units": temp_unit},
        },
        "properties": {
            "parameter": {
                "PRECTOTCORR": {"20250101": 0.0, "20250102": 15.5},
                "T2M": {"20250101": 12.0, "20250102": 14.2},
            }
        },
    }


class FieldShiftTests(unittest.TestCase):

    def test_parse_power_daily_valid(self):
        payload = synthetic_payload()
        res = parse_power_daily(payload, date(2025, 1, 1), date(2025, 1, 2))
        self.assertEqual(res["available_days"], 2)
        self.assertEqual(res["requested_days"], 2)
        self.assertEqual(res["missing_days"], 0)
        self.assertEqual(res["rows"][1]["rain_mm"], 15.5)

    def test_parse_power_daily_rejects_wrong_units(self):
        payload = synthetic_payload(rain_unit="inches")
        with self.assertRaises(SourceUnavailable):
            parse_power_daily(payload, date(2025, 1, 1), date(2025, 1, 2))

    def test_parse_power_daily_rejects_non_utc(self):
        payload = synthetic_payload(time_std="LST")
        with self.assertRaises(SourceUnavailable):
            parse_power_daily(payload, date(2025, 1, 1), date(2025, 1, 2))

    def test_seasonal_summary_apr_sep_has_five_periods(self):
        rows = synthetic_power_rows(heavy=False)
        summary = seasonal_summary(rows, "apr_sep")
        self.assertEqual(summary["count"], 5)
        self.assertEqual(summary["sample_years"], [2021, 2022, 2023, 2024, 2025])
        self.assertEqual(summary["dry_day_fraction"], 1.0)
        self.assertEqual(summary["mean_rainfall_mm"], 0.0)

    def test_seasonal_summary_oct_mar_has_four_complete_periods(self):
        rows = synthetic_power_rows(heavy=False)
        summary = seasonal_summary(rows, "oct_mar")
        self.assertEqual(summary["count"], 4)
        self.assertEqual(summary["sample_years"], [2021, 2022, 2023, 2024])

    def test_incomplete_season_is_strictly_discarded(self):
        # Omit 2022-06-01
        rows = synthetic_power_rows(heavy=False, missing_day="2022-06-01")
        summary = seasonal_summary(rows, "apr_sep")
        # 2022 should be excluded, leaving 4 seasons
        self.assertEqual(summary["count"], 4)
        self.assertEqual(summary["sample_years"], [2021, 2023, 2024, 2025])

    def test_insufficient_seasons_raises_error(self):
        # Keep only 2021 and 2022
        rows = [r for r in synthetic_power_rows() if r["date"].startswith(("2021-", "2022-"))]
        with self.assertRaises(ValueError):
            seasonal_summary(rows, "apr_sep")

    def test_nasa_signal_changes_dry_exposure_deterministically(self):
        dry_summary = seasonal_summary(synthetic_power_rows(heavy=False), "apr_sep")
        wet_summary = seasonal_summary(synthetic_power_rows(heavy=True), "apr_sep")
        choice = FieldShiftInput(latitude=-30.04, longitude=-71.25, concern="dry")

        dry_res = compare_pathways(dry_summary, choice)
        wet_res = compare_pathways(wet_summary, choice)

        self.assertNotEqual(
            dry_res[0].dry_exposure_indicator,
            wet_res[0].dry_exposure_indicator,
        )

    def test_nasa_signal_changes_wet_exposure_deterministically(self):
        dry_summary = seasonal_summary(synthetic_power_rows(heavy=False), "apr_sep")
        wet_summary = seasonal_summary(synthetic_power_rows(heavy=True), "apr_sep")
        choice = FieldShiftInput(latitude=-42.48, longitude=-73.76, concern="wet", drainage="restricted")

        r_dry = compare_pathways(dry_summary, choice)
        r_wet = compare_pathways(wet_summary, choice)

        self.assertNotEqual(
            [p.wet_exposure_indicator for p in r_dry],
            [p.wet_exposure_indicator for p in r_wet],
        )

    def test_drainage_unknown_keeps_wet_exposure_none(self):
        wet_summary = seasonal_summary(synthetic_power_rows(heavy=True), "apr_sep")
        choice = FieldShiftInput(latitude=-42.48, longitude=-73.76, drainage="unknown")
        results = compare_pathways(wet_summary, choice)

        self.assertTrue(all(p.wet_exposure_indicator is None for p in results))
        self.assertTrue(all(p.agronomic_viability == "not_assessed" for p in results))

    def test_priority_sorting_does_not_mutate_indicators(self):
        summary = seasonal_summary(synthetic_power_rows(heavy=True), "apr_sep")
        water_first = compare_pathways(summary, FieldShiftInput(latitude=-35.43, longitude=-71.66, priority="water"))
        soil_first = compare_pathways(summary, FieldShiftInput(latitude=-35.43, longitude=-71.66, priority="soil"))

        self.assertNotEqual([p.id for p in water_first], [p.id for p in soil_first])
        water_map = {p.id: p.dry_exposure_indicator for p in water_first}
        soil_map = {p.id: p.dry_exposure_indicator for p in soil_first}
        self.assertEqual(water_map, soil_map)

    def test_fastapi_field_shift_healthz(self):
        client = TestClient(app)
        res = client.get("/solquira-api/studio/field-shift/healthz")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["domain"], "field_shift")

    def test_fastapi_field_shift_evaluate_endpoint(self):
        client = TestClient(app)
        # Point to Coquimbo, Chile
        body = {
            "latitude": -30.04,
            "longitude": -71.25,
            "season": "apr_sep",
            "drainage": "well_drained",
            "soil": "sandy",
            "priority": "water",
            "concern": "dry",
        }
        res = client.post("/solquira-api/studio/field-shift/evaluate", json=body)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["version"], "solquira.field-shift/2.0")
        self.assertIn(data["status"], ("historical_evidence_available", "source_unavailable"))
        self.assertIn("provenance", data)
        self.assertEqual(data["provenance"]["provider"], "NASA POWER")


if __name__ == "__main__":
    unittest.main()
