"""Same-origin, CSRF-preserving bridge to the original Solquira Studio.

Vercel's external rewrite forwards the browser Origin unchanged to Akamai.
The original Studio correctly rejects that Origin as foreign to its own host.
This isolated Next Station function checks the caller's Origin and Studio
session/CSRF material before making a bounded server-to-server request.

The upstream API, session verification, scenario validation and quotas remain
unchanged. Only explicitly listed Studio endpoints are forwarded.
"""

from __future__ import annotations

from http import cookies
from http.server import BaseHTTPRequestHandler
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import parse_qs, urlsplit
import json
import re

UPSTREAM = "https://api-solquira.r4logic.lat/solquira-api/studio/"
ALLOWED_ROUTES = frozenset({
    "location", "history", "power", "evidence", "evaluate", "agent",
})
HOST = re.compile(r"^solquira-next-station(?:-[a-z0-9-]+)?\.vercel\.app$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
COOKIE = "solquira_studio_session"
CSRF = "X-Solquira-CSRF"
MAX_BODY = 65536
MAX_RESPONSE = 2_000_000


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urlrequest.build_opener(_NoRedirect)


class handler(BaseHTTPRequestHandler):
    def _reply(self, status: int, body: bytes, retry_after: str | None = None):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if retry_after and re.fullmatch(r"[0-9]{1,5}", retry_after):
            self.send_header("Retry-After", retry_after)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str):
        self._reply(status, json.dumps(
            {"detail": message}, separators=(",", ":")
        ).encode("utf-8"))

    def _same_origin(self) -> bool:
        host = self.headers.get("Host", "").lower()
        origin = self.headers.get("Origin", "")
        fetch_site = self.headers.get("Sec-Fetch-Site", "").lower()
        # An Origin is required for all JSON POSTs from the public web app.
        # Do not allow a browser from another site to use the Studio session.
        return bool(
            HOST.fullmatch(host)
            and origin == f"https://{host}"
            and fetch_site != "cross-site"
        )

    def _route(self) -> str | None:
        location = urlsplit(self.path)
        values = parse_qs(location.query, keep_blank_values=True).get("route", [])
        if len(values) != 1:
            return None
        return values[0] if values[0] in ALLOWED_ROUTES else None

    def _auth(self) -> tuple[str, str] | None:
        csrf = self.headers.get(CSRF, "")
        if not TOKEN.fullmatch(csrf):
            return None
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        entry = jar.get(COOKIE)
        token = entry.value if entry else ""
        if not TOKEN.fullmatch(token):
            return None
        return token, csrf

    def do_GET(self):
        self._error(405, "Method not allowed.")

    def do_POST(self):
        route = self._route()
        if route is None:
            self._error(404, "Unknown Studio route.")
            return
        if not self._same_origin():
            self._error(403, "Request origin is not allowed.")
            return
        auth = self._auth()
        if auth is None:
            self._error(401, "Reconnect the Studio session.")
            return
        media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            self._error(415, "JSON body required.")
            return
        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            size = -1
        if size < 2 or size > MAX_BODY:
            self._error(413, "Request body is too large or missing.")
            return
        body = self.rfile.read(size)
        if len(body) != size:
            self._error(400, "Incomplete request.")
            return

        token, csrf = auth
        req = urlrequest.Request(
            UPSTREAM + route,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Cookie": COOKIE + "=" + token,
                CSRF: csrf,
                "User-Agent": "Solquira-Next-Station/Studio-Bridge",
            },
            method="POST",
        )
        try:
            # The browser's Origin was validated above. Do not forward that
            # unrelated Next Station Origin to the Akamai host: it is not its
            # own origin and the original backend must continue rejecting it.
            with _OPENER.open(req, timeout=22) as upstream:
                payload = upstream.read(MAX_RESPONSE + 1)
                if len(payload) > MAX_RESPONSE:
                    self._error(502, "Upstream response too large.")
                    return
                self._reply(upstream.status, payload, upstream.headers.get("Retry-After"))
        except urlerror.HTTPError as error:
            payload = error.read(MAX_RESPONSE + 1)
            if len(payload) > MAX_RESPONSE:
                self._error(502, "Upstream response too large.")
                return
            self._reply(error.code, payload, error.headers.get("Retry-After"))
        except (urlerror.URLError, TimeoutError, OSError):
            self._error(503, "The original Studio service is temporarily unavailable.")
