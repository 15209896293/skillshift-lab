"""Loopback-only synthetic acceptance server for pause receipt/readback recovery.

This test harness mutates only an in-memory WorkspaceApi. It commits the first
pause, drops its response as HTTP 503, then fails the first exact-workspace GET
readback as HTTP 503. No external services, identities, data, or code execution.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.workspace_api import WorkspaceApi  # noqa: E402
from agent_first.workspace_wsgi import WorkspaceWsgiApp  # noqa: E402


HOST = "127.0.0.1"
PORT = 8766
SYNTHETIC_503 = json.dumps(
    {
        "schema_version": "skillshift-api/v1",
        "request_id": "req-fault-injected",
        "error": {"code": "service_unavailable", "message": "本机合成故障注入。", "retryable": True},
    },
    ensure_ascii=False,
    separators=(",", ":"),
).encode("utf-8")


class PauseReadbackFault:
    def __init__(self) -> None:
        self.app = WorkspaceWsgiApp(WorkspaceApi())
        self.pause_response_dropped = False
        self.readback_failed = False
        self.commit_pause_before_dropping_response = os.environ.get("SKILLSHIFT_FAULT_COMMIT_PAUSE", "1") != "0"

    def __call__(self, environ: dict, start_response):
        method = environ.get("REQUEST_METHOD")
        path = environ.get("PATH_INFO", "")
        if method == "POST" and path.endswith("/pause") and not self.pause_response_dropped:
            if self.commit_pause_before_dropping_response:
                captured = []
                list(self.app(environ, lambda status, headers: captured.append((status, headers))))
            self.pause_response_dropped = True
            start_response("503 Service Unavailable", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(SYNTHETIC_503))),
                ("Cache-Control", "no-store"),
            ])
            return [SYNTHETIC_503]

        if (
            self.pause_response_dropped
            and not self.readback_failed
            and method == "GET"
            and path.startswith("/api/v1/demo/student/workspaces/")
            and "/" not in path.split("/workspaces/", 1)[1]
        ):
            self.readback_failed = True
            start_response("503 Service Unavailable", [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(SYNTHETIC_503))),
                ("Cache-Control", "no-store"),
            ])
            return [SYNTHETIC_503]

        return self.app(environ, start_response)


if __name__ == "__main__":
    fault = PauseReadbackFault()
    with make_server(HOST, PORT, fault) as server:
        print(f"Synthetic pause/readback fault test: http://{HOST}:{PORT}/demo/student/")
        print(f"Loopback only. Commit-before-drop={fault.commit_pause_before_dropping_response}; first readback returns 503.")
        server.serve_forever()
