"""Loopback-only WSGI adapter for the fixed synthetic workspace API.

This is a local acceptance adapter, not an authenticated or deployable service.
The demo role is selected by the API path and is deliberately not an identity
boundary. Never bind this adapter to a non-loopback interface.
"""

from __future__ import annotations

import ipaddress
import json
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Iterable
from uuid import uuid4

from .workspace_api import MAX_BODY_BYTES, WorkspaceApi


_APP_ROOT = Path(__file__).resolve().parents[2]
_STATIC_ASSETS = {
    "/demo/teacher": ("teacher-web/index.html", "text/html; charset=utf-8"),
    "/demo/teacher/": ("teacher-web/index.html", "text/html; charset=utf-8"),
    "/demo/teacher/index.html": ("teacher-web/index.html", "text/html; charset=utf-8"),
    "/demo/teacher/app.js": ("teacher-web/app.js", "text/javascript; charset=utf-8"),
    "/demo/teacher/styles.css": ("teacher-web/styles.css", "text/css; charset=utf-8"),
    "/demo/student": ("student-web/index.html", "text/html; charset=utf-8"),
    "/demo/student/": ("student-web/index.html", "text/html; charset=utf-8"),
    "/demo/student/index.html": ("student-web/index.html", "text/html; charset=utf-8"),
    "/demo/student/app.js": ("student-web/app.js", "text/javascript; charset=utf-8"),
    "/demo/student/styles.css": ("student-web/styles.css", "text/css; charset=utf-8"),
    "/demo/workspace-client.mjs": ("workspace-client.mjs", "text/javascript; charset=utf-8"),
}


class WorkspaceWsgiApp:
    """Adapt WSGI calls to WorkspaceApi while enforcing local-demo boundaries."""

    def __init__(self, api: WorkspaceApi | None = None) -> None:
        self.api = api or WorkspaceApi()

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        remote_addr = environ.get("REMOTE_ADDR", "")
        try:
            if not ipaddress.ip_address(remote_addr).is_loopback:
                return self._respond(start_response, 403, self._error("loopback_only"))
        except (TypeError, ValueError):
            return self._respond(start_response, 403, self._error("loopback_only"))

        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        if method not in {"GET", "POST"}:
            return self._respond(start_response, 405, self._error("method_not_allowed"), [("Allow", "GET, POST")])

        path = str(environ.get("PATH_INFO", "/"))
        if path in _STATIC_ASSETS and method != "GET":
            return self._respond(start_response, 405, self._error("method_not_allowed"), [("Allow", "GET")])
        if method == "GET" and path in _STATIC_ASSETS:
            relative_path, content_type = _STATIC_ASSETS[path]
            try:
                body = (_APP_ROOT / relative_path).read_bytes()
            except OSError:
                return self._respond(start_response, 500, self._error("asset_unavailable"))
            return self._respond(start_response, 200, body, content_type=content_type)

        try:
            raw_length = environ.get("CONTENT_LENGTH", "0") or "0"
            length = int(raw_length)
            if length < 0:
                raise ValueError
        except (TypeError, ValueError):
            return self._respond(start_response, 400, self._error("invalid_content_length"))
        if length > MAX_BODY_BYTES:
            return self._respond(start_response, 413, self._error("payload_too_large"))

        if method == "POST":
            content_type = str(environ.get("CONTENT_TYPE", "")).split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                return self._respond(start_response, 415, self._error("json_required"))

        stream = environ.get("wsgi.input")
        try:
            body = stream.read(length) if method == "POST" and length else b""
            if not isinstance(body, bytes) or len(body) != length:
                return self._respond(start_response, 400, self._error("incomplete_body"))
            response = self.api.handle(
                method,
                path + (
                    "?" + str(environ["QUERY_STRING"]) if environ.get("QUERY_STRING") else ""
                ),
                body,
                idempotency_key=environ.get("HTTP_IDEMPOTENCY_KEY"),
                if_match=environ.get("HTTP_IF_MATCH"),
            )
            encoded = json.dumps(response.payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            return self._respond(start_response, response.status, encoded)
        except Exception:
            # Do not reflect exception text, paths, request fields, or stack data.
            return self._respond(start_response, 500, self._error("internal_error"))

    @staticmethod
    def _error(code: str, request_id: str | None = None) -> bytes:
        return json.dumps(
            {
                "schema_version": "skillshift-api/v1",
                "request_id": request_id or f"req-wsgi-{uuid4().hex}",
                "error": {"code": code, "message": "request could not be processed", "retryable": False},
            },
            separators=(",", ":"),
        ).encode("utf-8")

    @staticmethod
    def _respond(
        start_response: Callable,
        status: int,
        body: bytes,
        extra: list[tuple[str, str]] | None = None,
        *,
        content_type: str = "application/json; charset=utf-8",
    ) -> list[bytes]:
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ]
        headers.extend(extra or [])
        start_response(f"{status} {HTTPStatus(status).phrase}", headers)
        return [body]


def create_app(api: WorkspaceApi | None = None) -> WorkspaceWsgiApp:
    """Return a fresh test/local-demo WSGI application and in-memory store."""

    return WorkspaceWsgiApp(api)
