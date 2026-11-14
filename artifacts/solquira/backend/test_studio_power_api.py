"""Studio POWER admission tests: no source network or inference."""
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
import studio_api


def test_power_is_explicit_admitted_and_geodata_gated():
    path = "/solquira-api/studio/power"
    payload = {"latitude": 1.23456, "longitude": 2.34567, "start": "2020-01-01", "end": "2020-01-02"}
    studio_api.ADMISSION.reset()
    try:
        with patch.dict("os.environ", {"SOLQUIRA_STUDIO_MODE": "1"}, clear=True), \
            patch.object(studio_api, "POWER_SESSION_REQUESTS", 8), \
            patch("power.fetch_nasa_power", return_value={"status": "unavailable"}) as source, \
            patch.object(studio_api, "current_provider", side_effect=AssertionError("Inference forbidden")), \
            TestClient(main.app, base_url="http://127.0.0.1") as client:
            assert client.post(path, json=payload).status_code == 401
            csrf = client.get("/solquira-api/studio/bootstrap").json()["csrf_token"]
            assert client.post(path, json=payload).status_code == 403
            headers = {studio_api.CSRF_HEADER: csrf}
            assert client.post(path, json=payload, headers=headers | {"Origin": "https://untrusted.invalid"}).status_code == 403
            assert client.post(path, json=payload, headers=headers).json() == {"status": "disabled"}
            with patch.dict("os.environ", {"SOLQUIRA_STUDIO_GEODATA": "1"}):
                for invalid in ({"end": "2020-02-01"}, {"start": "2020-02-31"}, {"latitude": 91}, {"url": "https://untrusted.invalid"}):
                    assert client.post(path, json=payload | invalid, headers=headers).status_code == 422
                source.assert_not_called()
                response = client.post(path, json=payload, headers=headers)
                assert response.status_code == 200 and response.json()["status"] == "unavailable"
                assert "no-store" in response.headers["cache-control"]
                source.assert_called_once_with(1.235, 2.346, date(2020, 1, 1), date(2020, 1, 2))
                assert client.get("/api/fuentes/power", params=payload).status_code == 404
    finally:
        studio_api.ADMISSION.reset()


def test_legacy_soil_weight_is_rotation_history_not_soil_suitability():
    fixtures = Path(__file__).resolve().parents[1] / "src/studio/fixtures.json"
    parcel = json.loads(fixtures.read_text(encoding="utf-8"))["parcels"]["valle"]
    def run(soil):
        return main.evaluate(main.EvaluationInput(
            parcel=main.Parcel.model_validate(parcel | {"soil": soil}), waterPercent=100
        ))["rotations"]
    a, b = run("franco"), run("arcilloso")
    assert [r["score"] for r in a] == [r["score"] for r in b]
    assert all(r["scoreWeightSemantics"] == {"suelo": "rotation_history", "soilSuitability": "not_assessed"} for r in a)


def test_slow_power_worker_does_not_take_core_studio_slot():
    path = "/solquira-api/studio/power"
    payload = {"latitude": 1.0, "longitude": 2.0, "start": "2020-01-01", "end": "2020-01-02"}
    entered, release = threading.Event(), threading.Event()

    def slow_source(*args):
        entered.set()
        assert release.wait(5)
        return {"status": "unavailable"}

    studio_api.ADMISSION.reset()
    try:
        with patch.dict("os.environ", {"SOLQUIRA_STUDIO_MODE": "1", "SOLQUIRA_STUDIO_GEODATA": "1"}, clear=True), \
            patch.object(studio_api, "MAX_POWER_ACTIVE", 1), patch.object(studio_api, "MAX_ACTIVE", 1), \
            patch("power.fetch_nasa_power", side_effect=slow_source) as source, \
            TestClient(main.app, base_url="http://127.0.0.1") as client, ThreadPoolExecutor(1) as pool:
            headers = {studio_api.CSRF_HEADER: client.get("/solquira-api/studio/bootstrap").json()["csrf_token"]}
            pending = pool.submit(client.post, path, json=payload, headers=headers)
            try:
                assert entered.wait(2)
                limited = client.post(path, json=payload | {"longitude": 3.0}, headers=headers)
                assert limited.status_code == 429 and limited.headers["Retry-After"] == "3"
                assert studio_api.ADMISSION.active == 0
                assert studio_api.ADMISSION.power_active == 1
                core = client.post("/solquira-api/studio/evaluate", headers=headers, json={
                    "profile_id": "valle", "water_percent": 100, "previous_crop": "cereal",
                })
                assert core.status_code == 200
                assert source.call_count == 1
            finally:
                release.set()
            assert pending.result(timeout=2).status_code == 200
            assert studio_api.ADMISSION.power_active == studio_api.ADMISSION.active == 0
    finally:
        studio_api.ADMISSION.reset()


def test_power_request_window_is_independent_of_core_studio():
    admission = studio_api.Admission()
    token, session, _ = admission.bootstrap(None, "local")
    for _ in range(studio_api.POWER_SESSION_REQUESTS):
        admission.acquire(token, session["csrf"], power=True)
        admission.release(power=True)
    try:
        admission.acquire(token, session["csrf"], power=True)
    except HTTPException as error:
        assert error.status_code == 429 and error.headers["Retry-After"] == "60"
    else:
        raise AssertionError("POWER session quota did not reject the request")
    # The core lane remains independent even with the POWER window exhausted.
    admission.acquire(token, session["csrf"])
    assert admission.active == 1 and admission.power_active == 0
    admission.release()
