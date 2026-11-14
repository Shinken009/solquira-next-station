import copy
import json
import queue
import threading
import time
import unittest
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock
import main
import power


class PowerTests(unittest.TestCase):
    def setUp(self):
        power._CACHE.clear()
        self.raw = json.loads(
            Path(__file__).with_name("power_sample.json").read_text(encoding="utf-8")
        )

    def query(self):
        return power.fetch_nasa_power(
            10.0, 20.0, date(2025, 1, 1), date(2025, 1, 7)
        )

    def mocked(self, data):
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps(data).encode()
        response.__enter__.return_value = response
        return patch.object(power.urllib.request, "urlopen", return_value=response)

    def test_valid_response_and_cache(self):
        with self.mocked(self.raw) as transport:
            a = self.query()
            b = self.query()
            self.assertEqual(a["status"], "ok")
            self.assertEqual(a["units"]["T2M"], "C")
            self.assertEqual(len(a["values"]["T2M"]), 7)
            self.assertTrue(b["cacheHit"])
            self.assertEqual(a["fetchedAt"], b["fetchedAt"])
            self.assertEqual(transport.call_count, 1)
            b["values"]["T2M"].clear()
            self.assertEqual(len(self.query()["values"]["T2M"]), 7)

    def test_fill_value_is_not_a_measurement(self):
        self.raw["properties"]["parameter"]["T2M"]["20250101"] = -999
        with self.mocked(self.raw):
            response = self.query()
            self.assertIsNone(response["values"]["T2M"]["20250101"])
            self.assertEqual(response["missingValueCount"], 1)

    def test_wrong_unit_period_location_and_incomplete_series(self):
        for case in ["unit", "period", "location", "coverage", "nan", "negative_rain"]:
            power._CACHE.clear()
            raw = copy.deepcopy(self.raw)
            if case == "unit":
                raw["parameters"]["T2M"]["units"] = "F"
            if case == "period":
                raw["header"]["start"] = "20240101"
            if case == "location":
                raw["geometry"]["coordinates"][0] = 0
            if case == "coverage":
                raw["properties"]["parameter"]["T2M"].pop("20250101")
            if case == "nan":
                raw["properties"]["parameter"]["T2M"]["20250101"] = float("nan")
            if case == "negative_rain":
                raw["properties"]["parameter"]["PRECTOTCORR"]["20250101"] = -1
            with self.subTest(case=case), self.mocked(raw):
                self.assertEqual(self.query()["status"], "invalid_response")

    def test_invalid_provider_geometry_is_never_cached(self):
        for coordinates in ([float("nan"), 10.0], [20.0, float("inf")], [True, 10.0],
                            [20.0, "10"], [20.0], [180.0001, 10.0]):
            with self.subTest(coordinates=coordinates):
                raw = copy.deepcopy(self.raw)
                raw["geometry"]["coordinates"] = coordinates
                with self.mocked(raw):
                    result = power.fetch_nasa_power(
                        10.0, 180.0 if coordinates[0] == 180.0001 else 20.0,
                        date(2025, 1, 1), date(2025, 1, 7),
                    )
                self.assertEqual(result["status"], "invalid_response")
                self.assertFalse(power._CACHE)

    def test_distinct_lookups_and_cached_series_do_not_wait_on_network_lock(self):
        with self.mocked(self.raw):
            self.assertEqual(self.query()["status"], "ok")
        entered = queue.Queue()
        release = threading.Event()

        def transport(*args, **kwargs):
            entered.put(True)
            if not release.wait(5):
                raise AssertionError("Test never released the mock transport")
            raise urllib.error.URLError("Declared offline fixture")

        def lookup(lon):
            return power.fetch_nasa_power(10.0, lon, date(2025, 1, 1), date(2025, 1, 7))

        with patch.object(power.urllib.request, "urlopen", side_effect=transport), ThreadPoolExecutor(3) as pool:
            try:
                first = pool.submit(lookup, 21.0)
                self.assertTrue(entered.get(timeout=2))
                second = pool.submit(lookup, 22.0)
                self.assertTrue(entered.get(timeout=2))
                self.assertTrue(pool.submit(self.query).result(timeout=2)["cacheHit"])
                with self.assertRaises(main.HTTPException) as caught:
                    lookup(21.0)
                self.assertEqual(caught.exception.status_code, 429)
                self.assertEqual(caught.exception.headers["Retry-After"], "3")
                with self.assertRaises(main.HTTPException) as busy:
                    lookup(23.0)
                self.assertEqual(busy.exception.status_code, 429)
                self.assertTrue(entered.empty(), "A saturated source must not queue more transport work")
            finally:
                release.set()
            self.assertEqual(first.result(timeout=2)["status"], "unavailable")
            self.assertEqual(second.result(timeout=2)["status"], "unavailable")
        self.assertFalse(power._INFLIGHT)

    def test_upstream_throttle_keeps_retry_after_and_does_not_cache(self):
        throttled = urllib.error.HTTPError(power.ENDPOINT, 429, "rate", {"Retry-After": "17"}, None)
        with patch.object(power.urllib.request, "urlopen", side_effect=throttled):
            with self.assertRaises(main.HTTPException) as caught:
                self.query()
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(caught.exception.headers["Retry-After"], "17")
        self.assertFalse(power._INFLIGHT)
        self.assertFalse(power._CACHE)

    def test_network_failure_never_becomes_synthetic_success(self):
        with patch.object(
            power.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ) as transport:
            for _ in range(2):
                response = self.query()
                self.assertEqual(response["status"], "unavailable")
                self.assertNotIn("values", response)
            self.assertEqual(transport.call_count, 2)

    def test_exactly_31_days_allowed_but_32_rejected(self):
        with patch.object(power.urllib.request, "urlopen", side_effect=TimeoutError):
            self.assertEqual(
                power.fetch_nasa_power(
                    10.0, 20.0, date(2025, 1, 1), date(2025, 1, 31)
                )["status"],
                "unavailable",
            )
            with self.assertRaises(main.HTTPException):
                power.fetch_nasa_power(
                    10.0, 20.0, date(2025, 1, 1), date(2025, 2, 1)
                )

    def test_global_points_are_accepted_when_provider_confirms_location(self):
        for latitude, longitude in ((45.0, -120.0), (-25.0, 135.0), (0.0, 0.0)):
            with self.subTest(latitude=latitude, longitude=longitude):
                power._CACHE.clear()
                raw = copy.deepcopy(self.raw)
                raw["geometry"]["coordinates"][:2] = [longitude, latitude]
                with self.mocked(raw) as transport:
                    result = power.fetch_nasa_power(
                        latitude, longitude, date(2025, 1, 1), date(2025, 1, 7)
                    )
                    self.assertEqual(result["status"], "ok")
                    self.assertEqual(
                        result["location"], {"latitude": latitude, "longitude": longitude}
                    )
                    self.assertEqual(transport.call_count, 1)

    def test_invalid_global_coordinates_are_rejected_before_network(self):
        invalid = (
            (90.001, 0), (-90.001, 0), (0, 180.001), (0, -180.001),
            (float("nan"), 0), (float("inf"), 0), (0, float("-inf")),
            (True, 0), (0, False),
        )
        with patch.object(power.urllib.request, "urlopen") as network:
            for latitude, longitude in invalid:
                with self.subTest(latitude=latitude, longitude=longitude):
                    with self.assertRaises(main.HTTPException):
                        power.fetch_nasa_power(
                            latitude, longitude, date(2025, 1, 1), date(2025, 1, 7)
                        )
            network.assert_not_called()

    def test_cache_expiry(self):
        with self.mocked(self.raw) as transport:
            self.query()
            for key, (_, result) in list(power._CACHE.items()):
                power._CACHE[key] = (time.monotonic() - power.CACHE_TTL - 1, result)
            self.query()
            self.assertEqual(transport.call_count, 2)


class HardConstraintTests(unittest.TestCase):
    def evaluate(self, **updates):
        p = main.default_parcel().model_copy(update=updates)
        return main.evaluate(main.EvaluationInput(parcel=p, waterPercent=100))

    def test_immediate_repeat_is_excluded_even_with_high_water(self):
        result = self.evaluate(waterM3Ha=10000, previousCrops=["cubierta"])
        blocked = next(r for r in result["rotations"] if r["id"] == "rotation-a")
        self.assertFalse(blocked["eligibleUnderDemoRules"])
        self.assertFalse(blocked["rotationAllowed"])
        self.assertNotEqual(result["scenarioLeaderId"], "rotation-a")

    def test_no_eligible_leader_at_zero_water(self):
        result = self.evaluate(waterM3Ha=0)
        self.assertIsNone(result["scenarioLeaderId"])
        self.assertEqual(result["demoRuleMatches"], 0)
        self.assertTrue(
            all(not r["eligibleUnderDemoRules"] for r in result["rotations"])
        )

    def test_missing_priorities_or_unknown_crop_abstains(self):
        for updates in [{"priorities": []}, {"previousCrops": ["trigo"]}]:
            result = self.evaluate(**updates)
            self.assertEqual(result["status"], "insufficient_data")
            self.assertEqual(result["rotations"], [])

    def test_deterministic_and_no_agronomic_viability_claim(self):
        self.assertEqual(self.evaluate(), self.evaluate())
        for r in self.evaluate()["rotations"]:
            self.assertEqual(r["agronomicViability"], "not_assessed")
            self.assertAlmostEqual(sum(r["scoreWeights"].values()), 1, places=5)
