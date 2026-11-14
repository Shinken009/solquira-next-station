"""Isolated, same-origin NASA Field Shift bridge for the Next Station Vercel site.

This endpoint reuses the live Solquira Studio session and CSRF policy through
a bounded, metadata-only authorization request. It does not deploy new routes
or modify the existing Akamai backend. NASA computations use local Field Shift
Python rules and never invent weather data.
"""
from __future__ import annotations

from collections import OrderedDict, deque
from datetime import datetime, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from threading import Lock
from urllib import error as urlerror
from urllib import request as urlrequest
import json
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "artifacts" / "solquira" / "backend"))

from pydantic import ValidationError
from field_shift.schema import FieldShiftInput
from field_shift.adapter import evaluate_field_shift

# Only the same pinned Solquira backend verifies opaque bearer sessions.
VERIFY_ENDPOINT = "https://api-solquira.r4logic.lat/solquira-api/studio/evidence"
COOKIE = "solquira_studio_session"
CSRF = "X-Solquira-CSRF"
MAX_BODY = 8192
MAX_INFLIGHT = 2
MAX_PER_SESSION_MINUTE = 4
WINDOW_SECONDS = 60
_LOCK = Lock()
_ACTIVE = 0
_EVENTS = OrderedDict()
_TOKEN = re.compile(r"^[a-zA-Z0-9_-]{32,128}$")


class handler(BaseHTTPRequestHandler):
    def _json(self, code, value, extra_headers=None):
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, val in (extra_headers or {}).items():
            self.send_header(key, val)
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, code, reason, retry=None):
        headers = {"Retry-After": str(retry)} if retry is not None else {}
        self._json(code, {
            "status": "source_unavailable" if code >= 500 else "request_rejected",
            "message": reason,
            "historical_context": None,
            "pathways": [],
        }, headers)

    def _same_origin(self):
        host = self.headers.get("Host", "")
        if not host or len(host) > 253 or not re.fullmatch(r"[a-zA-Z0-9.-]+", host):
            return False
        origin = self.headers.get("Origin")
        if origin and origin != "https://" + host:
            return False
        if self.headers.get("Sec-Fetch-Site", "").lower() == "cross-site":
            return False
        return True

    def _auth_material(self):
        csrf = self.headers.get(CSRF, "")
        if not _TOKEN.fullmatch(csrf):
            return None, None
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None, None
        value = jar.get(COOKIE)
        token = value.value if value else ""
        if not _TOKEN.fullmatch(token):
            return None, None
        return token, csrf

    @staticmethod
    def _admit(token):
        global _ACTIVE
        now = time.monotonic()
        with _LOCK:
            if _ACTIVE >= MAX_INFLIGHT:
                return False, 3
            entry = _EVENTS.setdefault(token, deque())
            while entry and entry[0] <= now - WINDOW_SECONDS:
                entry.popleft()
            if len(entry) >= MAX_PER_SESSION_MINUTE:
                return False, max(1, int(WINDOW_SECONDS - (now - entry[0])))
            entry.append(now)
            _EVENTS.move_to_end(token)
            while len(_EVENTS) > 100:
                _EVENTS.popitem(last=False)
            _ACTIVE += 1
            return True, None

    @staticmethod
    def _release():
        global _ACTIVE
        with _LOCK:
            _ACTIVE = max(0, _ACTIVE - 1)

    @staticmethod
    def _verify_with_solquira(token, csrf, point):
        # This route uses existing session+CSRF+Host/Origin+admission; no AI
        # inference or NASA query is triggered by the evidence metadata endpoint.
        payload = json.dumps({
            "latitude": point.latitude, "longitude": point.longitude,
        }).encode("utf-8")
        req = urlrequest.Request(
            VERIFY_ENDPOINT,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Cookie": COOKIE + "=" + token,
                CSRF: csrf,
                "User-Agent": "Solquira-Next-Station/Vercel-FieldShift",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=8) as response:
                return response.status == 200, response.status
        except urlerror.HTTPError as err:
            return False, err.code
        except (urlerror.URLError, TimeoutError):
            return False, 503

    def do_GET(self):
        # A liveness check only; not an assertion of NASA or backend availability.
        self._json(200, {
            "status": "ready",
            "service": "next-station-field-shift-bridge",
            "backend_protection": "delegated_to_solquira_studio",
            "nasa": "not_queried",
        })

    def do_POST(self):
        if not self._same_origin():
            self._error(403, "Request origin is not permitted.")
            return
        token, csrf = self._auth_material()
        if not token or not csrf:
            self._error(401, "Start a Studio session before evaluating Field Shift.")
            return
        try:
            declared = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            declared = -1
        if declared < 0 or declared > MAX_BODY:
            self._error(413, "Request payload exceeds the allowed size.")
            return

        try:
            def unique_keys(pairs):
                output = {}
                for key, value in pairs:
                    if key in output:
                        raise ValueError("Duplicate JSON key")
                    output[key] = value
                return output

            parsed = json.loads(
                self.rfile.read(declared), object_pairs_hook=unique_keys,
                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("Non-finite number")),
            )
            field_input = FieldShiftInput.model_validate(parsed)
        except (ValueError, TypeError, ValidationError):
            self._error(422, "Check the Field Shift request fields.")
            return

        allowed, retry = self._admit(token)
        if not allowed:
            self._error(429, "NASA Field Shift is busy or over the per-session limit.", retry=retry)
            return
        try:
            verified, status = self._verify_with_solquira(token, csrf, field_input)
            if not verified:
                if status in (401, 403):
                    self._error(status, "Studio session or CSRF verification failed.")
                elif status == 429:
                    self._error(429, "Studio request limit reached.", retry=60)
                else:
                    self._error(503, "Studio authorization could not be verified.")
                return
            try:
                result = evaluate_field_shift(field_input, timeout_s=25)
            except Exception:
                self._error(503, "NASA POWER evaluation is unavailable; no data invented.")
                return
            self._json(200, result.model_dump(mode="json"))
        finally:
            self._release()
