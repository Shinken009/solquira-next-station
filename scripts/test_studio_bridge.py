"""Regression checks for the Next Station same-origin Studio bridge.

No outbound network access; the original Akamai server is not changed.
Run: python3 scripts/test_studio_bridge.py
"""
from __future__ import annotations

from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
import importlib.util
import json
import unittest


SOURCE = Path(__file__).resolve().parent.parent / "api" / "studio_bridge.py"
spec = importlib.util.spec_from_file_location("studio_bridge", SOURCE)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

BODY = b'{"latitude":-29.96,"longitude":-71.35}'
TOKEN = "t" * 40
CSRF = "c" * 40
HOST = "solquira-next-station.vercel.app"


class FakeResponse:
    status = 200
    headers = Message()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, amount):
        return b'{"schema_version":"solquira.location/1"}'


def make_handler(origin="https://" + HOST, host=HOST, route="location",
                 csrf=CSRF, cookie=TOKEN, body=BODY, content_type="application/json",
                 fetch_site="same-origin"):
    instance = object.__new__(bridge.handler)
    instance.path = "/api/studio_bridge?route=" + route
    instance.headers = {
        "Host": host,
        "Origin": origin,
        "Sec-Fetch-Site": fetch_site,
        "Content-Length": str(len(body)),
        "Content-Type": content_type,
        "X-Solquira-CSRF": csrf,
        "Cookie": "solquira_studio_session=" + cookie,
    }
    instance.rfile = BytesIO(body)
    instance.wfile = BytesIO()
    instance.response_code = None
    instance.response_headers = {}
    instance.send_response = lambda code: setattr(instance, "response_code", code)
    instance.send_header = lambda k, v: instance.response_headers.__setitem__(k, v)
    instance.end_headers = lambda: None
    return instance


class StudioBridgeTest(unittest.TestCase):
    def test_valid_location_passes_and_strips_browser_origin(self):
        h = make_handler()
        with patch.object(bridge._OPENER, "open", return_value=FakeResponse()) as request:
            h.do_POST()
            self.assertEqual(h.response_code, 200)
            sent = request.call_args.args[0]
            self.assertEqual(sent.full_url, bridge.UPSTREAM + "location")
            headers = dict(sent.header_items())
            self.assertNotIn("Origin", headers)
            self.assertEqual(headers.get("Cookie"), "solquira_studio_session=" + TOKEN)
            self.assertEqual(headers.get("X-solquira-csrf"), CSRF)
            self.assertEqual(json.loads(h.wfile.getvalue())["schema_version"], "solquira.location/1")

    def test_wrong_origin_rejected(self):
        h = make_handler(origin="https://untrusted.example")
        with patch.object(bridge._OPENER, "open") as request:
            h.do_POST()
            self.assertEqual(h.response_code, 403)
            request.assert_not_called()

    def test_no_origin_rejected(self):
        h = make_handler(origin="")
        h.do_POST()
        self.assertEqual(h.response_code, 403)

    def test_cross_site_flag_rejected(self):
        h = make_handler(fetch_site="cross-site")
        h.do_POST()
        self.assertEqual(h.response_code, 403)

    def test_random_host_rejected(self):
        h = make_handler(origin="https://wrong.vercel.app", host="wrong.vercel.app")
        h.do_POST()
        self.assertEqual(h.response_code, 403)

    def test_approved_preview_host_accepted(self):
        host = "solquira-next-station-example-shinken009s-projects.vercel.app"
        h = make_handler(origin="https://" + host, host=host)
        with patch.object(bridge._OPENER, "open", return_value=FakeResponse()):
            h.do_POST()
            self.assertEqual(h.response_code, 200)

    def test_requires_valid_session_cookie(self):
        h = make_handler(cookie="not-a-valid-session")
        h.do_POST()
        self.assertEqual(h.response_code, 401)

    def test_requires_csrf(self):
        h = make_handler(csrf="")
        h.do_POST()
        self.assertEqual(h.response_code, 401)

    def test_route_allowlist(self):
        h = make_handler(route="not-allowed")
        h.do_POST()
        self.assertEqual(h.response_code, 404)

    def test_disallows_get(self):
        h = make_handler()
        h.do_GET()
        self.assertEqual(h.response_code, 405)

    def test_disallows_non_json(self):
        h = make_handler(content_type="text/plain")
        h.do_POST()
        self.assertEqual(h.response_code, 415)

    def test_bounds_body(self):
        h = make_handler(body=b"x" * (bridge.MAX_BODY + 1))
        h.do_POST()
        self.assertEqual(h.response_code, 413)

    def test_explicit_route_list(self):
        self.assertEqual(bridge.ALLOWED_ROUTES, {
            "location", "history", "power", "evidence", "evaluate", "agent"
        })


if __name__ == "__main__":
    unittest.main()
