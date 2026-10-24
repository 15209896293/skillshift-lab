"""Task 121: real loopback HTTP smoke for the current synthetic P3 WSGI API.

This runner binds an ephemeral port on 127.0.0.1 only, uses a fresh in-memory
WorkspaceApi and fixed synthetic fixture, then shuts down the server.
It does not call a model, external network, database, ECS, or execute fixture code.
"""

from __future__ import annotations

from hashlib import sha256
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
from wsgiref.simple_server import make_server


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))
from agent_first.workspace_api import WorkspaceApi  # noqa: E402
from agent_first.workspace_wsgi import WorkspaceWsgiApp  # noqa: E402

OUT = Path(__file__).resolve().parent / "loopback-http-smoke.json"
API = "/api/v1/demo"
VERSION = "skillshift-api/v1"


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


def main() -> None:
    api = WorkspaceApi()
    server = make_server("127.0.0.1", 0, WorkspaceWsgiApp(api), handler_class=QuietHandler)
    host, port = server.server_address[:2]
    assert host == "127.0.0.1", f"unexpected listener address: {host}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    exchanges: list[dict] = []

    def call(method: str, path: str, body: dict | None = None, *, key: str | None = None, revision: int | None = None):
        headers = {}
        data = None
        if body is not None:
            data = json.dumps({"schema_version": VERSION, **body}, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if key:
            headers["Idempotency-Key"] = key
        if revision is not None:
            headers["If-Match"] = str(revision)
        request = Request(base + path, data=data, headers=headers, method=method)
        response_headers = {}
        try:
            with urlopen(request, timeout=5) as response:
                status, raw = response.status, response.read()
                response_headers = dict(response.headers.items())
        except HTTPError as error:
            status, raw = error.code, error.read()
            response_headers = dict(error.headers.items())
        if response_headers.get("Content-Type", "").startswith("application/json"):
            payload = json.loads(raw.decode("utf-8"))
        else:
            payload = {"raw_bytes": len(raw), "content_type": response_headers.get("Content-Type", "")}
        exchanges.append({
            "method": method, "path": path, "status": status,
            "idempotency_key_sent": key is not None,
            "if_match_sent": revision is not None,
        })
        return status, payload

    checks: dict[str, bool] = {}
    try:
        status, health = call("GET", "/api/v1/health")
        checks["health_over_loopback_http"] = status == 200 and health["data"]["mode"] == "local-synthetic-demo"
        for page in ("/demo/teacher/", "/demo/student/"):
            page_status, _ = call("GET", page)
            checks[f"static_page_{page.rsplit('/', 2)[1]}_served"] = page_status == 200

        fixture_dir = ROOT / "fixtures" / "orders-audit-v1"
        manifest = json.loads((fixture_dir / "manifest.json").read_text(encoding="utf-8"))
        files = {entry["logical_name"]: (fixture_dir / entry["logical_name"]).read_text(encoding="utf-8") for entry in manifest["files"]}

        status_create, created = call("POST", f"{API}/teacher/assignments", {
            "title": "HTTP 合成闭环核验", "goal": "检查订单金额核对过程。",
            "student_responsibility": "说明检查依据及仍不确定的内容。",
            "submission_requirement": "提交固定 allowlist 快照和说明。",
            "starter_project_id": "orders-audit-v1", "collaboration_mode": "QA_ONLY",
        }, key="http-smoke-create")
        assignment = created["data"]
        assignment_id = assignment["id"]
        status_stale_publish, stale_publish = call(
            "POST", f"{API}/teacher/assignments/{assignment_id}/publish", {},
            key="http-smoke-stale-publish", revision=assignment["revision"] + 9,
        )
        status_draft_read, draft_read = call("GET", f"{API}/teacher/assignments/{assignment_id}")
        status_publish, published = call("POST", f"{API}/teacher/assignments/{assignment_id}/publish", {}, key="http-smoke-publish", revision=assignment["revision"])
        workspace_id = published["data"]["workspace"]["id"]
        status_catalog, catalog = call("GET", f"{API}/student/assignments")
        status_ws, ws = call("GET", f"{API}/student/workspaces/{workspace_id}")
        status_start, started = call("POST", f"{API}/student/workspaces/{workspace_id}/start", {}, key="http-smoke-start", revision=ws["data"]["revision"])
        submit_path = f"{API}/student/workspaces/{workspace_id}/submissions"
        first_submission_dto = {
            "artifact_refs": list(files), "artifact_contents": files,
            "student_explanation": "我已核对合成订单金额，并记录尚需确认的业务规则。",
        }
        submit_revision = started["data"]["workspace"]["revision"]
        status_submit, submitted = call("POST", submit_path, first_submission_dto, key="http-smoke-submit-v1", revision=submit_revision)
        status_submit_replay, replayed_submit = call("POST", submit_path, first_submission_dto, key="http-smoke-submit-v1", revision=submit_revision)
        submission_id = submitted["data"]["submission"]["id"]
        status_queue, queue = call("GET", f"{API}/teacher/assignments/{assignment_id}/review-queue")
        status_teacher_ws, teacher_ws = call("GET", f"{API}/teacher/workspaces/{workspace_id}")
        status_review, review = call("POST", f"{API}/teacher/submissions/{submission_id}/review-actions", {
            "kind": "REQUEST_REMEDIATION", "reason": "请补充订单金额核对依据并说明尚不确定的规则。",
        }, key="http-smoke-review", revision=teacher_ws["data"]["revision"])
        status_remediation, remediation = call("GET", f"{API}/student/workspaces/{workspace_id}/remediation")
        status_student_ws, student_ws = call("GET", f"{API}/student/workspaces/{workspace_id}")
        corrected_files = {**files, "README.md": files["README.md"] + "\n补充：逐项核对订单金额。\n"}
        status_resubmit, resubmitted = call("POST", submit_path, {
            "artifact_refs": list(corrected_files), "artifact_contents": corrected_files,
            "student_explanation": "我已补充核对依据，未确定的规则仍请教师确认。",
        }, key="http-smoke-submit-v2", revision=student_ws["data"]["revision"])
        latest_ws_status, latest_ws = call("GET", f"{API}/teacher/workspaces/{workspace_id}")
        status_ack, ack = call("POST", f"{API}/teacher/submissions/{resubmitted['data']['submission']['id']}/review-actions", {
            "kind": "ACKNOWLEDGE", "reason": "已复核合成补正快照及说明。",
        }, key="http-smoke-ack", revision=latest_ws["data"]["revision"])
        status_latest, latest = call("GET", f"{API}/student/workspaces/{workspace_id}/submissions/latest")
        status_events, events = call("GET", f"{API}/student/workspaces/{workspace_id}/events?after_sequence=0&limit=50")

        checks.update({
            "stale_publish_conflict_had_no_side_effect": status_stale_publish == 409 and stale_publish["error"]["code"] == "stale_revision" and status_draft_read == 200 and draft_read["data"]["state"] == "DRAFT" and draft_read["data"]["workspace"] is None,
            "teacher_created_and_published": status_create == 201 and status_publish == 200 and published["data"]["assignment"]["state"] == "PUBLISHED",
            "student_discovered_and_started": status_catalog == 200 and status_ws == 200 and status_start == 200 and catalog["data"]["assignments"][0]["id"] == assignment_id,
            "allowlist_submission_idempotency_replay_did_not_duplicate": status_submit == 201 and status_submit_replay == 201 and replayed_submit["data"]["submission"]["id"] == submission_id and status_queue == 200 and len(queue["data"]["submissions"]) == 1 and queue["data"]["submissions"][0]["id"] == submission_id,
            "teacher_remediation_readback": status_review == 201 and status_remediation == 200 and remediation["data"]["remediations"][0]["reason"] == review["data"]["review_action"]["reason"],
            "student_resubmitted_v2": status_student_ws == 200 and status_resubmit == 201 and resubmitted["data"]["submission"]["version"] == 2,
            "teacher_ack_and_student_readback": latest_ws_status == 200 and status_ack == 201 and status_latest == 200 and latest["data"]["submission"]["state"] == "ACCEPTED",
            "evidence_events_http_readback": status_events == 200 and len(events["data"]["events"]) >= 6,
            "execution_remained_disabled": published["data"]["workspace"]["execution_enabled"] is False,
        })
        mutations = [item for item in exchanges if item["method"] != "GET"]
        checks["all_mutations_sent_idempotency_and_revision"] = bool(mutations) and all(
            item["idempotency_key_sent"]
            and (item["if_match_sent"] or item["path"] == f"{API}/teacher/assignments")
            for item in mutations
        )
        result = {
            "task_id": "R0-P3-121-LOOPBACK-HTTP-SMOKE",
            "listener": {"host": host, "port": port, "actual_address": list(server.socket.getsockname()[:2])},
            "synthetic_only": True,
            "external_calls": 0,
            "fixture_python_executed": False,
            "checks": checks,
            "exchange_count": len(exchanges),
            "exchanges": exchanges,
        }
        result["pass"] = all(checks.values())
        raw_result = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        OUT.write_bytes(raw_result)
        if not result["pass"]:
            raise AssertionError(json.dumps(checks, ensure_ascii=False))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"artifact_sha256={sha256(raw_result).hexdigest().upper()}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive(), "loopback server thread did not stop"
        assert not server.socket.fileno() >= 0, "loopback listener socket remained open"


if __name__ == "__main__":
    main()
