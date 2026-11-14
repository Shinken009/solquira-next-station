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
import os
from unittest.mock import Mock, patch

import studio_api
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

    def _client_with_session(self):
        env = patch.dict(os.environ, {
            "SOLQUIRA_STUDIO_MODE": "1",
            "SOLQUIRA_STUDIO_ALLOWED_HOSTS": "testserver",
        })
        env.start()
        self.addCleanup(env.stop)
        studio_api.ADMISSION.reset()
        self.addCleanup(studio_api.ADMISSION.reset)
        client = TestClient(app)
        self.addCleanup(client.close)
        with patch.object(studio_api, "_service") as service:
            service.return_value.studio_status.return_value = {
                "available": False, "mode": "local_fallback", "model": None,
            }
            bootstrap = client.get("/solquira-api/studio/bootstrap")
        self.assertEqual(bootstrap.status_code, 200)
        return client, bootstrap.json()["csrf_token"]

    def _field_request(self):
        return {
            "latitude": -30.04, "longitude": -71.25,
            "season": "apr_sep", "drainage": "well_drained",
            "soil": "sandy", "priority": "water", "concern": "dry",
        }

    def test_fastapi_field_shift_healthz(self):
        with patch.dict(os.environ, {"SOLQUIRA_STUDIO_MODE": "1"}):
            client = TestClient(app, base_url="http://127.0.0.1")
            with client:
                res = client.get("/solquira-api/studio/field-shift/healthz")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["domain"], "field_shift")

    def test_fastapi_field_shift_evaluate_requires_session(self):
        with patch.dict(os.environ, {
            "SOLQUIRA_STUDIO_MODE": "1",
            "SOLQUIRA_STUDIO_ALLOWED_HOSTS": "testserver",
        }):
            studio_api.ADMISSION.reset()
            with TestClient(app) as client:
                with patch("field_shift.routes.evaluate_field_shift") as worker:
                    res = client.post(
                        "/solquira-api/studio/field-shift/evaluate",
                        json=self._field_request(),
                    )
                    self.assertEqual(res.status_code, 401)
                    worker.assert_not_called()

    def test_fastapi_field_shift_rejects_missing_or_forged_csrf(self):
        client, csrf = self._client_with_session()
        for headers in ({}, {studio_api.CSRF_HEADER: "forged"}):
            with self.subTest(headers=headers):
                with patch("field_shift.routes.evaluate_field_shift") as worker:
                    res = client.post(
                        "/solquira-api/studio/field-shift/evaluate",
                        json=self._field_request(), headers=headers,
                    )
                    self.assertEqual(res.status_code, 403)
                    worker.assert_not_called()

    def test_fastapi_field_shift_rejects_untrusted_origin(self):
        client, csrf = self._client_with_session()
        with patch("field_shift.routes.evaluate_field_shift") as worker:
            res = client.post(
                "/solquira-api/studio/field-shift/evaluate",
                json=self._field_request(),
                headers={studio_api.CSRF_HEADER: csrf, "Origin": "https://attacker.invalid"},
            )
            self.assertEqual(res.status_code, 403)
            worker.assert_not_called()

    def test_fastapi_field_shift_evaluate_endpoint(self):
        client, csrf = self._client_with_session()
        with patch("field_shift.routes.evaluate_field_shift") as worker:
            result = Mock()
            result.model_dump.return_value = {
                "version": "solquira.field-shift/2.0",
                "status": "source_unavailable",
                "pathways": [],
                "provenance": {"provider": "NASA POWER"},
            }
            worker.return_value = result
            res = client.post(
                "/solquira-api/studio/field-shift/evaluate",
                json=self._field_request(),
                headers={studio_api.CSRF_HEADER: csrf},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["version"], "solquira.field-shift/2.0")
        worker.assert_called_once()
        self.assertEqual(res.headers["cache-control"], "no-store")

    def test_fastapi_field_shift_enforces_power_budget(self):
        client, csrf = self._client_with_session()
        with patch("field_shift.routes.evaluate_field_shift") as worker:
            result = Mock()
            result.model_dump.return_value = {"status": "source_unavailable", "pathways": []}
            worker.return_value = result
            statuses = [
                client.post(
                    "/solquira-api/studio/field-shift/evaluate",
                    json=self._field_request(), headers={studio_api.CSRF_HEADER: csrf},
                ).status_code for _ in range(studio_api.POWER_SESSION_REQUESTS + 1)
            ]
        self.assertEqual(statuses[:-1], [200] * studio_api.POWER_SESSION_REQUESTS)
        self.assertEqual(statuses[-1], 429)

    def test_fastapi_field_shift_rejects_oversized_body(self):
        client, csrf = self._client_with_session()
        with patch("field_shift.routes.evaluate_field_shift") as worker:
            res = client.post(
                "/solquira-api/studio/field-shift/evaluate",
                content=b" " * (studio_api.MAX_BODY_BYTES + 1),
                headers={"Content-Type": "application/json", studio_api.CSRF_HEADER: csrf},
            )
            self.assertEqual(res.status_code, 413)
            worker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
