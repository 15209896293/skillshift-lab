from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.workspace_api import WorkspaceApi
from agent_first.workspace_wsgi import WorkspaceWsgiApp


class WorkspaceWsgiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = WorkspaceWsgiApp(WorkspaceApi())

    def call(self, *, method="GET", path="/api/v1/health", query="", remote="127.0.0.1", body=b"", content_type="", extra=None, raw=False):
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "REMOTE_ADDR": remote,
            "CONTENT_LENGTH": str(len(body)),
            "CONTENT_TYPE": content_type,
            "wsgi.input": BytesIO(body),
        }
        environ.update(extra or {})
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        result = b"".join(self.app(environ, start_response))
        return captured, result if raw else json.loads(result.decode("utf-8"))

    def test_fixed_demo_pages_and_assets_are_loopback_allowlisted(self):
        for role in ("teacher", "student"):
            page_body = b""
            script_body = b""
            for suffix, expected_type in (
                ("", "text/html"), ("/app.js", "text/javascript"), ("/styles.css", "text/css"),
            ):
                path = f"/demo/{role}{suffix}"
                response, body = self.call(path=path, raw=True)
                self.assertEqual("200 OK", response["status"])
                self.assertTrue(response["headers"]["Content-Type"].startswith(expected_type))
                self.assertEqual("no-store", response["headers"]["Cache-Control"])
                self.assertEqual("nosniff", response["headers"]["X-Content-Type-Options"])
                self.assertGreater(len(body), 0)
                if suffix == "":
                    page_body = body
                elif suffix == "/app.js":
                    script_body = body
            self.assertIn(b'href="./styles.css"', page_body)
            self.assertIn(b'src="./app.js"', page_body)
            self.assertIn(f'<base href="/demo/{role}/">'.encode(), page_body)
            self.assertIn(b'from "../workspace-client.mjs"', script_body)
        response, client = self.call(path="/demo/workspace-client.mjs", raw=True)
        self.assertEqual("200 OK", response["status"])
        self.assertTrue(response["headers"]["Content-Type"].startswith("text/javascript"))
        self.assertIn(b"/api/v1/demo", client)

        denied, denied_body = self.call(path="/demo/teacher/", remote="192.0.2.5", raw=True)
        self.assertEqual("403 Forbidden", denied["status"])
        self.assertEqual("loopback_only", json.loads(denied_body.decode("utf-8"))["error"]["code"])
        rejected, rejected_body = self.call(method="POST", path="/demo/student/", raw=True)
        self.assertEqual("405 Method Not Allowed", rejected["status"])
        self.assertEqual("GET", rejected["headers"]["Allow"])
        self.assertEqual("method_not_allowed", json.loads(rejected_body.decode("utf-8"))["error"]["code"])

        _, missing = self.call(path="/demo/teacher/../../README.md")
        self.assertEqual("not_found", missing["error"]["code"])

    def test_loopback_health_has_no_store_headers(self):
        response, payload = self.call()
        self.assertEqual("200 OK", response["status"])
        self.assertEqual("no-store", response["headers"]["Cache-Control"])
        self.assertEqual("local-synthetic-demo", payload["data"]["mode"])

    def test_non_loopback_and_missing_peer_are_denied(self):
        for remote in ("192.0.2.5", ""):
            _, payload = self.call(remote=remote)
            self.assertEqual("loopback_only", payload["error"]["code"])

    def test_preflight_errors_use_distinct_request_ids(self):
        ids = []
        for remote in ("192.0.2.5", ""):
            _, payload = self.call(remote=remote)
            ids.append(payload["request_id"])
        self.assertEqual(2, len(set(ids)))
        self.assertTrue(all(value.startswith("req-wsgi-") for value in ids))

        for remote in (None, 123):
            response, payload = self.call(remote=remote)
            self.assertEqual("403 Forbidden", response["status"])
            self.assertEqual("no-store", response["headers"]["Cache-Control"])
            self.assertEqual("loopback_only", payload["error"]["code"])

    def test_ipv6_peer_policy_does_not_trust_forwarded_for_headers(self):
        # This exercises the WSGI callable only; it does not verify proxy
        # configuration, network binding, or deployment security.
        loopback, payload = self.call(remote="::1")
        self.assertEqual("200 OK", loopback["status"])
        self.assertEqual("local-synthetic-demo", payload["data"]["mode"])

        for remote, forwarded in (("2001:db8::1", None), ("192.0.2.5", "::1")):
            extra = {"HTTP_X_FORWARDED_FOR": forwarded} if forwarded is not None else None
            response, denied = self.call(remote=remote, extra=extra)
            self.assertEqual("403 Forbidden", response["status"])
            self.assertEqual("no-store", response["headers"]["Cache-Control"])
            self.assertEqual("loopback_only", denied["error"]["code"])

    def test_post_requires_json_and_idempotency_revision_headers_reach_api(self):
        body = json.dumps({
            "schema_version": "skillshift-api/v1",
            "title": "检查合成订单",
            "goal": "核对订单字段关系并说明验证方法。",
            "student_responsibility": "解释异常和验证步骤。",
            "submission_requirement": "提交结果及说明。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
        }, ensure_ascii=False).encode("utf-8")
        _, rejected = self.call(method="POST", path="/api/v1/demo/teacher/assignments", body=body)
        self.assertEqual("json_required", rejected["error"]["code"])
        _, created = self.call(
            method="POST", path="/api/v1/demo/teacher/assignments", body=body,
            content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "create-wsgi-1"},
        )
        self.assertEqual("assignment-1", created["data"]["id"])

    def test_post_rejects_missing_or_unsupported_schema_version(self):
        request_body = {
            "title": "核对合成订单",
            "goal": "核对订单数量、单价与金额是否一致。",
            "student_responsibility": "说明异常记录和验证步骤。",
            "submission_requirement": "提交结果及验证说明。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
        }
        for version in (None, "skillshift-api/v0"):
            body = dict(request_body)
            if version is not None:
                body["schema_version"] = version
            _, payload = self.call(
                method="POST", path="/api/v1/demo/teacher/assignments",
                body=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "schema-version-wsgi"},
            )
            self.assertEqual("invalid_schema_version", payload["error"]["code"])

    def test_publish_conflict_is_explicit_and_draft_can_be_read_back_through_wsgi(self):
        request_body = {
            "schema_version": "skillshift-api/v1",
            "title": "核对合成订单",
            "goal": "核对订单数量、单价与金额是否一致。",
            "student_responsibility": "说明异常记录和验证步骤。",
            "submission_requirement": "提交 allowlist 文件快照和验证说明。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
        }
        _, created = self.call(
            method="POST",
            path="/api/v1/demo/teacher/assignments",
            body=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-conflict-create"},
        )
        assignment_id = created["data"]["id"]
        publish_path = f"/api/v1/demo/teacher/assignments/{assignment_id}/publish"
        stale_response, stale = self.call(
            method="POST",
            path=publish_path,
            body=json.dumps({"schema_version": "skillshift-api/v1"}).encode("utf-8"),
            content_type="application/json",
            extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-conflict-publish", "HTTP_IF_MATCH": "999"},
        )
        self.assertEqual("409 Conflict", stale_response["status"])
        self.assertEqual("no-store", stale_response["headers"]["Cache-Control"])
        self.assertEqual("stale_revision", stale["error"]["code"])
        self.assertNotIn("999", stale["error"]["message"])

        read_response, readback = self.call(path=f"/api/v1/demo/teacher/assignments/{assignment_id}")
        self.assertEqual("200 OK", read_response["status"])
        self.assertEqual("DRAFT", readback["data"]["state"])
        self.assertIsNone(readback["data"]["workspace"])

        published_response, published = self.call(
            method="POST",
            path=publish_path,
            body=json.dumps({"schema_version": "skillshift-api/v1"}).encode("utf-8"),
            content_type="application/json",
            extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-conflict-publish-retry", "HTTP_IF_MATCH": str(created["data"]["revision"])},
        )
        self.assertEqual("200 OK", published_response["status"])
        self.assertEqual("PUBLISHED", published["data"]["assignment"]["state"])
        self.assertEqual(assignment_id, published["data"]["workspace"]["assignment_id"])

    def test_size_method_and_malformed_length_are_bounded(self):
        too_large, _ = self.call(method="POST", body=b" " * 20_000, content_type="application/json")
        self.assertTrue(too_large["status"].startswith("413 "))
        unsupported, _ = self.call(method="DELETE")
        self.assertEqual("405 Method Not Allowed", unsupported["status"])
        malformed, payload = self.call(extra={"CONTENT_LENGTH": "not-a-number"})
        self.assertEqual("400 Bad Request", malformed["status"])
        self.assertEqual("invalid_content_length", payload["error"]["code"])

    def test_api_exception_is_not_reflected(self):
        class ExplodingApi:
            def handle(self, *args, **kwargs):
                raise RuntimeError("private path C:\\secret\\token.txt")

        self.app.api = ExplodingApi()
        _, payload = self.call()
        self.assertEqual("internal_error", payload["error"]["code"])
        self.assertNotIn("secret", json.dumps(payload))

    def test_synthetic_teacher_student_snapshot_remediation_round_trip_through_wsgi_calls(self):
        teacher_page, teacher_html = self.call(path="/demo/teacher/", raw=True)
        student_page, student_html = self.call(path="/demo/student/", raw=True)
        shared_module, client_source = self.call(path="/demo/workspace-client.mjs", raw=True)
        self.assertEqual("200 OK", teacher_page["status"])
        self.assertEqual("200 OK", student_page["status"])
        self.assertEqual("200 OK", shared_module["status"])
        self.assertIn(b'src="./app.js"', teacher_html)
        self.assertIn(b'src="./app.js"', student_html)
        self.assertIn(b'const API_ROOT = "/api/v1/demo"', client_source)

        create_body = {
            "schema_version": "skillshift-api/v1",
            "title": "核对合成订单",
            "goal": "核对订单数量、单价与金额是否一致。",
            "student_responsibility": "说明异常记录和验证步骤。",
            "submission_requirement": "提交 allowlist 文件快照和验证说明。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
        }
        _, created = self.call(method="POST", path="/api/v1/demo/teacher/assignments", body=json.dumps(create_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-create"})
        assignment_id = created["data"]["id"]
        _, published = self.call(method="POST", path=f"/api/v1/demo/teacher/assignments/{assignment_id}/publish", body=json.dumps({"schema_version": "skillshift-api/v1"}).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-publish", "HTTP_IF_MATCH": str(created["data"]["revision"])})
        workspace_id = published["data"]["workspace"]["id"]

        _, catalog = self.call(path="/api/v1/demo/student/assignments")
        self.assertEqual(assignment_id, catalog["data"]["assignments"][0]["id"])
        _, workspace = self.call(path=f"/api/v1/demo/student/workspaces/{workspace_id}")
        _, started = self.call(method="POST", path=f"/api/v1/demo/student/workspaces/{workspace_id}/start", body=json.dumps({"schema_version": "skillshift-api/v1"}).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-start", "HTTP_IF_MATCH": str(workspace["data"]["revision"])})
        turn_response, turn = self.call(
            method="POST",
            path=f"/api/v1/demo/student/workspaces/{workspace_id}/agent-turns",
            body=json.dumps({"schema_version": "skillshift-api/v1", "question": "请说明如何核对订单金额，不运行项目。"}, ensure_ascii=False).encode(),
            content_type="application/json",
            extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-agent-turn", "HTTP_IF_MATCH": str(started["revision"])},
        )
        self.assertEqual("200 OK", turn_response["status"])
        self.assertEqual("scripted-demo", turn["data"]["turn"]["provider_mode"])
        self.assertIn("如何验证", turn["data"]["turn"]["response_text"])
        proposal_id = turn["data"]["proposed_action"]["id"]
        decision_response, decision = self.call(
            method="POST",
            path=f"/api/v1/demo/student/workspaces/{workspace_id}/proposed-actions/{proposal_id}/decision",
            body=json.dumps({"schema_version": "skillshift-api/v1", "decision": "REJECTED"}).encode(),
            content_type="application/json",
            extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-agent-proposal-reject", "HTTP_IF_MATCH": str(turn["revision"])},
        )
        self.assertEqual("200 OK", decision_response["status"])
        self.assertEqual("REJECTED", decision["data"]["proposed_action"]["status"])
        _, workspace_after_collaboration = self.call(path=f"/api/v1/demo/student/workspaces/{workspace_id}")
        latest_path = f"/api/v1/demo/student/workspaces/{workspace_id}/submissions/latest"
        latest_response, empty_latest = self.call(path=latest_path)
        self.assertEqual("200 OK", latest_response["status"])
        self.assertEqual("no-store", latest_response["headers"]["Cache-Control"])
        self.assertIsNone(empty_latest["data"]["submission"])
        fixture_dir = ROOT / "fixtures" / "orders-audit-v1"
        fixture_manifest = json.loads((fixture_dir / "manifest.json").read_text(encoding="utf-8"))
        fixture_contents = {
            entry["logical_name"]: (fixture_dir / entry["logical_name"]).read_text(encoding="utf-8")
            for entry in fixture_manifest["files"]
        }
        submission_body = {
            "schema_version": "skillshift-api/v1",
            "artifact_refs": list(fixture_contents),
            "artifact_contents": fixture_contents,
            "student_explanation": "我逐行核对了订单关系，并记录了仍需确认的规则。",
        }
        _, submitted = self.call(method="POST", path=f"/api/v1/demo/student/workspaces/{workspace_id}/submissions", body=json.dumps(submission_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-submit-1", "HTTP_IF_MATCH": str(workspace_after_collaboration["data"]["revision"])})
        submission_path = f"/api/v1/demo/student/workspaces/{workspace_id}/submissions"
        replay_status, replayed_submission = self.call(method="POST", path=submission_path, body=json.dumps(submission_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-submit-1", "HTTP_IF_MATCH": str(workspace_after_collaboration["data"]["revision"])})
        self.assertEqual("201 Created", replay_status["status"])
        self.assertEqual(submitted["data"], replayed_submission["data"])
        changed_match_status, changed_match = self.call(method="POST", path=submission_path, body=json.dumps(submission_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-submit-1", "HTTP_IF_MATCH": str(workspace_after_collaboration["data"]["revision"] + 1)})
        self.assertEqual("409 Conflict", changed_match_status["status"])
        self.assertEqual("idempotency_conflict", changed_match["error"]["code"])
        latest_response, latest_first = self.call(path=latest_path)
        self.assertEqual("200 OK", latest_response["status"])
        self.assertEqual("no-store", latest_response["headers"]["Cache-Control"])
        self.assertEqual(submitted["data"]["submission"], latest_first["data"]["submission"])
        first_submission_snapshots = submitted["data"]["submission"]["artifact_snapshots"]
        self.assertEqual(set(fixture_contents), {snapshot["logical_name"] for snapshot in first_submission_snapshots})
        for snapshot in first_submission_snapshots:
            entry = next(item for item in fixture_manifest["files"] if item["logical_name"] == snapshot["logical_name"])
            self.assertEqual(fixture_contents[snapshot["logical_name"]], snapshot["content"])
            self.assertEqual(entry["size_bytes"], snapshot["size_bytes"])
            self.assertEqual(entry["sha256"], snapshot["sha256"])
        _, queue = self.call(path=f"/api/v1/demo/teacher/assignments/{assignment_id}/review-queue")
        self.assertEqual(submitted["data"]["submission"]["id"], queue["data"]["submissions"][0]["id"])
        self.assertEqual(first_submission_snapshots, queue["data"]["submissions"][0]["artifact_snapshots"])

        _, live_workspace = self.call(path=f"/api/v1/demo/teacher/workspaces/{workspace_id}")
        review_body = {"schema_version": "skillshift-api/v1", "kind": "REQUEST_REMEDIATION", "reason": "请补充金额核对依据并说明仍不确定的规则。"}
        _, reviewed = self.call(method="POST", path=f"/api/v1/demo/teacher/submissions/{submitted['data']['submission']['id']}/review-actions", body=json.dumps(review_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-review-1", "HTTP_IF_MATCH": str(live_workspace["data"]["revision"])})
        _, remediation = self.call(path=f"/api/v1/demo/student/workspaces/{workspace_id}/remediation")
        self.assertEqual(reviewed["data"]["review_action"]["reason"], remediation["data"]["remediations"][0]["reason"])

        _, after_feedback = self.call(path=f"/api/v1/demo/student/workspaces/{workspace_id}")
        corrected_body = {
            "schema_version": "skillshift-api/v1",
            "artifact_refs": list(fixture_contents),
            "artifact_contents": {
                **fixture_contents,
                "main.py": fixture_contents["main.py"] + "# 学生补正后的合成版本\n",
            },
            "student_explanation": "我补充了金额核对依据，并说明了仍需教师确认的业务规则。",
        }
        _, resubmitted = self.call(method="POST", path=f"/api/v1/demo/student/workspaces/{workspace_id}/submissions", body=json.dumps(corrected_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-submit-2", "HTTP_IF_MATCH": str(after_feedback["data"]["revision"])})
        self.assertEqual(2, resubmitted["data"]["submission"]["version"])
        latest_response, latest_second = self.call(path=latest_path)
        self.assertEqual("200 OK", latest_response["status"])
        self.assertEqual("no-store", latest_response["headers"]["Cache-Control"])
        self.assertEqual(resubmitted["data"]["submission"], latest_second["data"]["submission"])
        _, responded = self.call(path=f"/api/v1/demo/student/workspaces/{workspace_id}/remediation")
        self.assertEqual("RESPONDED", responded["data"]["remediations"][0]["state"])
        _, latest_workspace = self.call(path=f"/api/v1/demo/teacher/workspaces/{workspace_id}")
        close_body = {"schema_version": "skillshift-api/v1", "kind": "ACKNOWLEDGE", "reason": "已复核补正提交，验证说明满足任务要求。"}
        _, closed = self.call(method="POST", path=f"/api/v1/demo/teacher/submissions/{resubmitted['data']['submission']['id']}/review-actions", body=json.dumps(close_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-review-2", "HTTP_IF_MATCH": str(latest_workspace["data"]["revision"])})
        self.assertEqual("ACKNOWLEDGE", closed["data"]["review_action"]["kind"])
        latest_response, latest_accepted = self.call(path=latest_path)
        self.assertEqual("200 OK", latest_response["status"])
        self.assertEqual("no-store", latest_response["headers"]["Cache-Control"])
        self.assertEqual("ACCEPTED", latest_accepted["data"]["submission"]["state"])
        self.assertEqual(resubmitted["data"]["submission"]["id"], latest_accepted["data"]["submission"]["id"])
        _, closed_remediation = self.call(path=f"/api/v1/demo/student/workspaces/{workspace_id}/remediation")
        self.assertEqual("CLOSED", closed_remediation["data"]["remediations"][0]["state"])
        self.assertEqual(
            resubmitted["data"]["submission"]["id"],
            closed_remediation["data"]["remediations"][0]["response_submission_id"],
        )

        history_path = f"/api/v1/demo/teacher/assignments/{assignment_id}/review-history"
        first_history_response, first_history = self.call(path=history_path, query="after_sequence=0&limit=1")
        self.assertEqual("200 OK", first_history_response["status"])
        self.assertEqual("no-store", first_history_response["headers"]["Cache-Control"])
        self.assertTrue(first_history["data"]["has_more"])
        self.assertEqual("REQUEST_REMEDIATION", first_history["data"]["review_actions"][0]["kind"])
        self.assertEqual(
            {"id", "submission_id", "submission_version", "kind", "reason", "created_event_sequence"},
            set(first_history["data"]["review_actions"][0]),
        )
        next_sequence = first_history["data"]["next_sequence"]
        second_history_response, second_history = self.call(path=history_path, query=f"after_sequence={next_sequence}&limit=1")
        self.assertEqual("200 OK", second_history_response["status"])
        self.assertEqual("no-store", second_history_response["headers"]["Cache-Control"])
        self.assertFalse(second_history["data"]["has_more"])
        self.assertEqual("ACKNOWLEDGE", second_history["data"]["review_actions"][0]["kind"])
        self.assertNotIn("artifact_snapshots", second_history["data"]["review_actions"][0])
        self.assertNotIn("student_explanation", second_history["data"]["review_actions"][0])

        teacher_latest_status, teacher_latest = self.call(path=latest_path.replace("/student/", "/teacher/"))
        self.assertEqual("404 Not Found", teacher_latest_status["status"])
        self.assertEqual("no-store", teacher_latest_status["headers"]["Cache-Control"])
        self.assertEqual("not_found", teacher_latest["error"]["code"])
        student_history_status, student_history = self.call(path=history_path.replace("/teacher/", "/student/"))
        self.assertEqual("404 Not Found", student_history_status["status"])
        self.assertEqual("no-store", student_history_status["headers"]["Cache-Control"])
        self.assertEqual("not_found", student_history["error"]["code"])
        bad_cursor_status, bad_cursor = self.call(path=history_path, query="after_sequence=invalid")
        self.assertEqual("400 Bad Request", bad_cursor_status["status"])
        self.assertEqual("no-store", bad_cursor_status["headers"]["Cache-Control"])
        self.assertEqual("invalid_cursor", bad_cursor["error"]["code"])

        events_response, events_payload = self.call(
            path=f"/api/v1/demo/student/workspaces/{workspace_id}/events",
            query="after_sequence=0&limit=50",
        )
        self.assertEqual("200 OK", events_response["status"])
        self.assertEqual("no-store", events_response["headers"]["Cache-Control"])
        events = events_payload["data"]["events"]
        expected_events = [
            (published["data"]["event"]["sequence"], "assignment.published", assignment_id),
            (started["data"]["event"]["sequence"], "student.work_started", workspace_id),
            (turn["data"]["turn"]["event_sequence"], "agent.turn_created", turn["data"]["turn"]["id"]),
            (decision["data"]["proposed_action"]["decision_event_sequence"], "agent.proposed_action_decided", proposal_id),
            (submitted["data"]["submission"]["created_event_sequence"], "submission.created", submitted["data"]["submission"]["id"]),
            (reviewed["data"]["review_action"]["created_event_sequence"], "review.action_recorded", reviewed["data"]["review_action"]["id"]),
            (resubmitted["data"]["submission"]["created_event_sequence"], "submission.created", resubmitted["data"]["submission"]["id"]),
            (closed["data"]["review_action"]["created_event_sequence"], "review.action_recorded", closed["data"]["review_action"]["id"]),
        ]
        sequences = [event["sequence"] for event in events]
        self.assertEqual([item[0] for item in expected_events], sequences)
        self.assertEqual(sorted(set(sequences)), sequences)
        self.assertEqual(
            [(event_type, resource_ref) for _, event_type, resource_ref in expected_events],
            [(event["event_type"], event["resource_ref"]) for event in events],
        )
        event_by_sequence = {event["sequence"]: event for event in events}
        for sequence, event_type, resource_ref in expected_events:
            self.assertEqual(event_type, event_by_sequence[sequence]["event_type"])
            self.assertEqual(resource_ref, event_by_sequence[sequence]["resource_ref"])

        stale_status, stale = self.call(method="POST", path=f"/api/v1/demo/student/workspaces/{workspace_id}/submissions", body=json.dumps(submission_body, ensure_ascii=False).encode(), content_type="application/json", extra={"HTTP_IDEMPOTENCY_KEY": "wsgi-stale-submit", "HTTP_IF_MATCH": str(started["revision"])})
        self.assertTrue(stale_status["status"].startswith("409 "))
        self.assertEqual("stale_revision", stale["error"]["code"])


if __name__ == "__main__":
    unittest.main()
