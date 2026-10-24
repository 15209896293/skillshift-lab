from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys
from threading import Event, Lock, Thread
import unittest
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.workspace_api import WorkspaceApi


TASK = {
    "title": "检查合成订单",
    "goal": "检查数量、单价与金额关系，并解释如何验证判断。",
    "student_responsibility": "说明异常记录、验证步骤和不确定处。",
    "submission_requirement": "提交项目结果及验证说明。",
    "starter_project_id": "orders-audit-v1",
    "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
}
EXPLANATION = "我逐行比较了金额和数量乘单价。O-105 的预期值是 178，但文件中是 160；我还需要确认折扣规则。"
ARTIFACT_CONTENTS = {
    "main.py": "# 合成提交：增加逐项校验逻辑\nprint('不执行')\n",
    "orders.csv": "order_id,quantity,unit_price,amount\nO-105,2,89.00,160.00\n",
}


def request(api: WorkspaceApi, method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
    headers = {"idempotency_key": key, "if_match": str(revision) if revision is not None else None}
    if method.upper() in {"POST", "PUT", "PATCH"}:
        payload = {"schema_version": "skillshift-api/v1", **(payload or {})}
    body = json.dumps(payload or {}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
    return api.handle(method, path, body, **headers)


class WorkspaceApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = WorkspaceApi()

    def create_assignment(self) -> dict:
        response = request(self.api, "POST", "/api/v1/demo/teacher/assignments", TASK, key="create-1")
        self.assertEqual(201, response.status)
        return response.payload["data"]

    def publish(self) -> tuple[dict, dict]:
        assignment = self.create_assignment()
        response = request(
            self.api, "POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish",
            key="publish-1", revision=assignment["revision"],
        )
        self.assertEqual(200, response.status)
        return response.payload["data"]["assignment"], response.payload["data"]["workspace"]

    def start(self) -> tuple[dict, dict]:
        assignment, workspace = self.publish()
        response = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start",
            key="start-1", revision=workspace["revision"],
        )
        self.assertEqual(200, response.status)
        return assignment, response.payload["data"]["workspace"]

    def submit(self, workspace: dict, *, key: str = "submit-1") -> dict:
        response = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION},
            key=key, revision=workspace["revision"],
        )
        self.assertEqual(201, response.status)
        return response.payload["data"]["submission"]

    def review(self, submission: dict, revision: int, *, kind: str = "REQUEST_EXPLANATION", reason: str = "请解释你如何核验金额规则。", key: str = "review-1"):
        return request(
            self.api, "POST", f"/api/v1/demo/teacher/submissions/{submission['id']}/review-actions",
            {"kind": kind, "reason": reason}, key=key, revision=revision,
        )

    def test_health_is_explicitly_local_synthetic(self) -> None:
        response = request(self.api, "GET", "/api/v1/health")
        second = request(self.api, "GET", "/api/v1/health")
        self.assertEqual(200, response.status)
        self.assertEqual("local-synthetic-demo", response.payload["data"]["mode"])
        self.assertTrue(response.payload["request_id"].startswith("req-demo-"))
        self.assertNotEqual(response.payload["request_id"], second.payload["request_id"])

    def test_create_requires_declared_fields_and_fixed_project(self) -> None:
        extra = {**TASK, "actor_id": "student-demo"}
        response = request(self.api, "POST", "/api/v1/demo/teacher/assignments", extra, key="bad-fields")
        self.assertEqual(400, response.status)
        self.assertEqual("invalid_fields", response.payload["error"]["code"])
        other = {**TASK, "starter_project_id": "arbitrary-path"}
        response = request(self.api, "POST", "/api/v1/demo/teacher/assignments", other, key="bad-project")
        self.assertEqual(422, response.status)

    def test_write_requests_require_the_supported_schema_version(self) -> None:
        for payload in (TASK, {"schema_version": "skillshift-api/v0", **TASK}):
            response = self.api.handle(
                "POST", "/api/v1/demo/teacher/assignments",
                json.dumps(payload, ensure_ascii=False), idempotency_key="schema-version-required",
            )
            self.assertEqual(400, response.status)
            self.assertEqual("invalid_schema_version", response.payload["error"]["code"])
        self.assertEqual({}, self.api.store.assignments)

    def test_task_text_limit_is_measured_in_utf8_bytes(self) -> None:
        exact = {**TASK, "title": "中" * 42 + "ab"}
        accepted = request(self.api, "POST", "/api/v1/demo/teacher/assignments", exact, key="utf8-exact")
        self.assertEqual(201, accepted.status)
        over = {**TASK, "title": "中" * 43}
        rejected = request(self.api, "POST", "/api/v1/demo/teacher/assignments", over, key="utf8-over")
        self.assertEqual(413, rejected.status)
        self.assertEqual("text_too_large", rejected.payload["error"]["code"])

    def test_create_idempotency_replays_and_rejects_key_reuse(self) -> None:
        first = request(self.api, "POST", "/api/v1/demo/teacher/assignments", TASK, key="create-1")
        replay = request(self.api, "POST", "/api/v1/demo/teacher/assignments", TASK, key="create-1")
        conflict = request(self.api, "POST", "/api/v1/demo/teacher/assignments", {**TASK, "title": "不同任务"}, key="create-1")
        self.assertEqual(first.payload["data"], replay.payload["data"])
        self.assertNotEqual(first.payload["request_id"], replay.payload["request_id"])
        self.assertEqual(first.payload["data"]["id"], replay.payload["data"]["id"])
        self.assertEqual(409, conflict.status)
        self.assertEqual("idempotency_conflict", conflict.payload["error"]["code"])

    def test_submission_and_review_replays_do_not_duplicate_work_after_state_advances(self) -> None:
        _, workspace = self.start()
        workspace_path = f"/api/v1/demo/student/workspaces/{workspace['id']}"
        payload = {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION}
        submitted = request(self.api, "POST", f"{workspace_path}/submissions", payload, key="submission-replay", revision=workspace["revision"])
        self.assertEqual(201, submitted.status)
        live = self.api._workspace(workspace["id"])
        event_count_after_submit = len(live.events)
        submission_replay = request(self.api, "POST", f"{workspace_path}/submissions", payload, key="submission-replay", revision=workspace["revision"])
        self.assertEqual(201, submission_replay.status)
        self.assertEqual(submitted.payload["data"], submission_replay.payload["data"])
        self.assertNotEqual(submitted.payload["request_id"], submission_replay.payload["request_id"])
        self.assertEqual(1, len(live.submissions))
        self.assertEqual(event_count_after_submit, len(live.events))
        changed_precondition = request(self.api, "POST", f"{workspace_path}/submissions", payload, key="submission-replay", revision=workspace["revision"] + 1)
        self.assertEqual(409, changed_precondition.status)
        self.assertEqual("idempotency_conflict", changed_precondition.payload["error"]["code"])
        missing_precondition = request(self.api, "POST", f"{workspace_path}/submissions", payload, key="submission-replay")
        self.assertEqual(409, missing_precondition.status)
        self.assertEqual("idempotency_conflict", missing_precondition.payload["error"]["code"])
        self.assertEqual(1, len(live.submissions))
        self.assertEqual(event_count_after_submit, len(live.events))

        submission = submitted.payload["data"]["submission"]
        review_payload = {"kind": "REQUEST_REMEDIATION", "reason": "请补充逐项核对与业务规则说明。"}
        revision = live.revision
        review_path = f"/api/v1/demo/teacher/submissions/{submission['id']}/review-actions"
        reviewed = request(self.api, "POST", review_path, review_payload, key="review-replay", revision=revision)
        self.assertEqual(201, reviewed.status)
        event_count_after_review = len(live.events)
        review_replay = request(self.api, "POST", review_path, review_payload, key="review-replay", revision=revision)
        self.assertEqual(201, review_replay.status)
        self.assertEqual(reviewed.payload["data"], review_replay.payload["data"])
        self.assertNotEqual(reviewed.payload["request_id"], review_replay.payload["request_id"])
        self.assertEqual(1, len(live.reviews))
        self.assertEqual(1, len(live.remediations))
        self.assertEqual(event_count_after_review, len(live.events))

    def test_student_cannot_create_assignments_or_use_teacher_role_routes(self) -> None:
        response = request(self.api, "POST", "/api/v1/demo/student/assignments", TASK, key="student-create")
        self.assertEqual(404, response.status)
        self.assertEqual({}, self.api.store.assignments)

    def test_publish_requires_revision_and_student_cannot_see_draft(self) -> None:
        assignment = self.create_assignment()
        hidden = request(self.api, "GET", f"/api/v1/demo/student/assignments/{assignment['id']}")
        missing_revision = request(self.api, "POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="pub-no-rev")
        self.assertEqual(404, hidden.status)
        self.assertEqual(428, missing_revision.status)

    def test_assignment_catalog_shows_drafts_to_teacher_and_only_published_tasks_to_student(self) -> None:
        draft = self.create_assignment()
        teacher_catalog = request(self.api, "GET", "/api/v1/demo/teacher/assignments")
        student_catalog = request(self.api, "GET", "/api/v1/demo/student/assignments")
        self.assertEqual([draft["id"]], [item["id"] for item in teacher_catalog.payload["data"]["assignments"]])
        self.assertEqual([], student_catalog.payload["data"]["assignments"])

        published_response = request(
            self.api, "POST", f"/api/v1/demo/teacher/assignments/{draft['id']}/publish",
            key="catalog-publish", revision=draft["revision"],
        )
        self.assertEqual(200, published_response.status)
        student_catalog = request(self.api, "GET", "/api/v1/demo/student/assignments")
        self.assertEqual([draft["id"]], [item["id"] for item in student_catalog.payload["data"]["assignments"]])
        self.assertEqual("PUBLISHED", student_catalog.payload["data"]["assignments"][0]["state"])

    def test_student_can_only_have_one_active_workspace_and_pause_switch_resume_isolated(self) -> None:
        _, workspace_a = self.publish()
        created_b = request(self.api, "POST", "/api/v1/demo/teacher/assignments", {**TASK, "title": "第二个合成任务"}, key="create-second")
        assignment_b = created_b.payload["data"]
        published_b = request(self.api, "POST", f"/api/v1/demo/teacher/assignments/{assignment_b['id']}/publish", key="publish-second", revision=assignment_b["revision"])
        workspace_b = published_b.payload["data"]["workspace"]
        started_a = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/start", key="start-a", revision=workspace_a["revision"])
        self.assertEqual(200, started_a.status)
        events_a_before_b_start = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/events?after_sequence=0").payload["data"]["events"]
        events_b_before_start = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/events?after_sequence=0").payload["data"]["events"]
        blocked_b = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/start", key="start-b-retry", revision=workspace_b["revision"])
        self.assertEqual(409, blocked_b.status)
        self.assertEqual("active_task_exists", blocked_b.payload["error"]["code"])
        unchanged_a = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_a['id']}").payload["data"]
        unchanged_b = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_b['id']}").payload["data"]
        self.assertEqual(("IN_PROGRESS", started_a.payload["revision"]), (unchanged_a["state"], unchanged_a["revision"]))
        self.assertEqual(("ASSIGNED", workspace_b["revision"]), (unchanged_b["state"], unchanged_b["revision"]))
        self.assertEqual(events_a_before_b_start, request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/events?after_sequence=0").payload["data"]["events"])
        self.assertEqual(events_b_before_start, request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/events?after_sequence=0").payload["data"]["events"])
        paused_a = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/pause", key="pause-a", revision=started_a.payload["revision"])
        self.assertEqual("PAUSED", paused_a.payload["data"]["workspace"]["state"])
        started_b = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/start", key="start-b-retry", revision=workspace_b["revision"])
        self.assertEqual(200, started_b.status)
        blocked_resume = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/start", key="resume-a-blocked", revision=paused_a.payload["revision"])
        self.assertEqual(409, blocked_resume.status)
        submission_b = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/submissions", {
            "artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS,
            "student_explanation": "第二任务单独核对了 O-105 的数量、单价和金额，并保留规则待确认。",
        }, key="submit-b", revision=started_b.payload["revision"])
        self.assertEqual(201, submission_b.status)
        workspace_b_after_submit = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_b['id']}").payload["data"]
        reviewed_b = self.review(submission_b.payload["data"]["submission"], workspace_b_after_submit["revision"], kind="REQUEST_REMEDIATION", reason="请单独补充第二任务的验证步骤。", key="review-b")
        self.assertEqual(201, reviewed_b.status)
        remediations_a = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/remediation")
        remediations_b = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/remediation")
        self.assertEqual([], remediations_a.payload["data"]["remediations"])
        self.assertEqual(submission_b.payload["data"]["submission"]["id"], remediations_b.payload["data"]["remediations"][0]["submission_id"])
        resumed_a = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/start", key="resume-a", revision=paused_a.payload["revision"])
        self.assertEqual(200, resumed_a.status)
        self.assertEqual("IN_PROGRESS", resumed_a.payload["data"]["workspace"]["state"])
        submission_a = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/submissions", {
            "artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS,
            "student_explanation": "第一任务单独核对了 O-105 的数量、单价和金额，并保留规则待确认。",
        }, key="submit-a", revision=resumed_a.payload["revision"])
        self.assertEqual(201, submission_a.status)
        latest_a = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/submissions/latest")
        latest_b = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace_b['id']}/submissions/latest")
        self.assertEqual(workspace_a["id"], latest_a.payload["data"]["submission"]["workspace_id"])
        self.assertEqual(workspace_b["id"], latest_b.payload["data"]["submission"]["workspace_id"])
        self.assertIn("第一任务", latest_a.payload["data"]["submission"]["student_explanation"])
        self.assertIn("第二任务", latest_b.payload["data"]["submission"]["student_explanation"])

    def test_parallel_start_requests_cannot_create_two_active_workspaces(self) -> None:
        _, workspace_a = self.publish()
        assignment_b = request(self.api, "POST", "/api/v1/demo/teacher/assignments", {**TASK, "title": "并发启动任务 B"}, key="parallel-start-create-b").payload["data"]
        workspace_b = request(self.api, "POST", f"/api/v1/demo/teacher/assignments/{assignment_b['id']}/publish", key="parallel-start-publish-b", revision=assignment_b["revision"]).payload["data"]["workspace"]
        start_gate = Event()

        def start(workspace: dict, key: str):
            start_gate.wait(timeout=2)
            return request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key=key, revision=workspace["revision"])

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(start, workspace_a, "parallel-start-a"), pool.submit(start, workspace_b, "parallel-start-b")]
            start_gate.set()
            responses = [future.result(timeout=3) for future in futures]

        self.assertEqual([200, 409], sorted(response.status for response in responses))
        conflict = next(response for response in responses if response.status == 409)
        self.assertEqual("active_task_exists", conflict.payload["error"]["code"])
        active = [item.workspace for item in self.api.store.assignments.values() if item.workspace and item.workspace.state == "IN_PROGRESS"]
        self.assertEqual(1, len(active))
        start_events = [event for event in active[0].events if event["event_type"] == "student.work_started"]
        self.assertEqual(1, len(start_events))

    def test_parallel_same_idempotency_key_creates_one_assignment(self) -> None:
        start_gate = Event()

        def create():
            start_gate.wait(timeout=2)
            return request(self.api, "POST", "/api/v1/demo/teacher/assignments", TASK, key="parallel-create-once")

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(create), pool.submit(create)]
            start_gate.set()
            responses = [future.result(timeout=3) for future in futures]

        self.assertEqual([201, 201], sorted(response.status for response in responses))
        assignment_ids = {response.payload["data"]["id"] for response in responses}
        self.assertEqual(1, len(assignment_ids))
        self.assertEqual(1, len(self.api.store.assignments))

    def test_api_serializes_overlapping_dispatches_on_shared_store(self) -> None:
        first_entered = Event()
        release_first = Event()
        second_entered = Event()
        state_lock = Lock()
        call_number = 0
        original_dispatch = self.api._handle_request

        def controlled_dispatch(method, path, body, *, idempotency_key=None, if_match=None):
            nonlocal call_number
            with state_lock:
                call_number += 1
                current_call = call_number
            if current_call == 1:
                first_entered.set()
                if not release_first.wait(timeout=2):
                    raise TimeoutError("test did not release first API dispatch")
            else:
                second_entered.set()
            return original_dispatch(method, path, body, idempotency_key=idempotency_key, if_match=if_match)

        self.api._handle_request = controlled_dispatch
        failures: list[BaseException] = []

        def health_request() -> None:
            try:
                response = self.api.handle("GET", "/api/v1/health")
                self.assertEqual(200, response.status)
            except BaseException as error:
                failures.append(error)

        first = Thread(target=health_request)
        second = Thread(target=health_request)
        first.start()
        self.assertTrue(first_entered.wait(timeout=1))
        second.start()
        try:
            self.assertFalse(second_entered.wait(timeout=0.05))
        finally:
            release_first.set()
        first.join(timeout=2)
        second.join(timeout=2)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertTrue(second_entered.is_set())
        self.assertEqual([], failures)

    def test_stale_revision_cannot_publish_or_start(self) -> None:
        assignment = self.create_assignment()
        stale = request(self.api, "POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="pub-stale", revision=99)
        self.assertEqual(409, stale.status)
        published, workspace = self.publish()
        stale_start = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="start-stale", revision=99)
        self.assertEqual(409, stale_start.status)

    def test_every_workspace_write_advances_revision_and_rejects_stale_followup(self) -> None:
        _, workspace = self.publish()
        path = f"/api/v1/demo/student/workspaces/{workspace['id']}"
        revision = workspace["revision"]

        started = request(self.api, "POST", f"{path}/start", key="revision-start", revision=revision)
        self.assertEqual(200, started.status)
        self.assertEqual(revision + 1, started.payload["revision"])
        stale_start = request(self.api, "POST", f"{path}/start", key="revision-start-stale", revision=revision)
        self.assertEqual("stale_revision", stale_start.payload["error"]["code"])
        revision = started.payload["revision"]

        turn = request(self.api, "POST", f"{path}/agent-turns", {"question": "如何验证？"}, key="revision-agent", revision=revision)
        self.assertEqual(200, turn.status)
        self.assertEqual(revision + 1, turn.payload["revision"])
        stale_turn = request(self.api, "POST", f"{path}/agent-turns", {"question": "如何验证？"}, key="revision-agent-stale", revision=revision)
        self.assertEqual("stale_revision", stale_turn.payload["error"]["code"])
        revision = turn.payload["revision"]

        proposal_id = turn.payload["data"]["proposed_action"]["id"]
        decision_path = f"{path}/proposed-actions/{proposal_id}/decision"
        decision = request(self.api, "POST", decision_path, {"decision": "STUDENT_TAKEOVER"}, key="revision-decision", revision=revision)
        self.assertEqual(200, decision.status)
        self.assertEqual(revision + 1, decision.payload["revision"])
        stale_decision = request(self.api, "POST", decision_path, {"decision": "STUDENT_TAKEOVER"}, key="revision-decision-stale", revision=revision)
        self.assertEqual("stale_revision", stale_decision.payload["error"]["code"])
        revision = decision.payload["revision"]

        submission_response = request(
            self.api, "POST", f"{path}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION},
            key="revision-submit", revision=revision,
        )
        self.assertEqual(201, submission_response.status)
        self.assertEqual(revision + 1, submission_response.payload["revision"])
        submission = submission_response.payload["data"]["submission"]
        stale_submission = request(
            self.api, "POST", f"{path}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION},
            key="revision-submit-stale", revision=revision,
        )
        self.assertEqual("stale_revision", stale_submission.payload["error"]["code"])
        revision = submission_response.payload["revision"]

        review = self.review(submission, revision, key="revision-review")
        self.assertEqual(201, review.status)
        self.assertEqual(revision + 1, review.payload["revision"])
        stale_review = self.review(submission, revision, key="revision-review-stale")
        self.assertEqual("stale_revision", stale_review.payload["error"]["code"])

    def test_complete_teacher_student_remediation_and_close_path(self) -> None:
        assignment, workspace = self.publish()
        started = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="start-1", revision=workspace["revision"])
        workspace = started.payload["data"]["workspace"]
        submission = self.submit(workspace)
        review = self.review(submission, self.api._workspace(workspace["id"]).revision)
        self.assertEqual(201, review.status)
        self.assertEqual("FEEDBACK_REQUIRED", self.api._workspace(workspace["id"]).state)
        remediation = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/remediation")
        self.assertEqual("OPEN", remediation.payload["data"]["remediations"][0]["state"])
        self.assertEqual("请解释你如何核验金额规则。", remediation.payload["data"]["remediations"][0]["reason"])

        live_workspace = self.api._workspace(workspace["id"])
        retry = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions", {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION}, key="submit-2", revision=live_workspace.revision)
        self.assertEqual(201, retry.status)
        self.assertEqual("RESPONDED", remediation.payload["data"]["remediations"][0]["state"])
        latest = retry.payload["data"]["submission"]
        close = self.review(latest, self.api._workspace(workspace["id"]).revision, kind="ACKNOWLEDGE", reason="验证说明与任务要求相符。", key="review-2")
        self.assertEqual(201, close.status)
        self.assertEqual("CLOSED", self.api._workspace(workspace["id"]).state)
        self.assertEqual("ACCEPTED", self.api._submission(latest["id"])[2]["state"])

    def test_teacher_demo_remediation_read_returns_open_and_responded_submission_link(self) -> None:
        _, workspace = self.publish()
        started = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start",
            key="teacher-remediation-start", revision=workspace["revision"],
        )
        submission = self.submit(started.payload["data"]["workspace"], key="teacher-remediation-submit-1")
        reviewed = self.review(
            submission, self.api._workspace(workspace["id"]).revision,
            kind="REQUEST_EVIDENCE", reason="请补充可复核的验证依据。", key="teacher-remediation-review",
        )
        self.assertEqual(201, reviewed.status)

        teacher_path = f"/api/v1/demo/teacher/workspaces/{workspace['id']}/remediation"
        opened = request(self.api, "GET", teacher_path)
        self.assertEqual(200, opened.status)
        open_remediation = opened.payload["data"]["remediations"][0]
        self.assertEqual("OPEN", open_remediation["state"])
        self.assertEqual(submission["id"], open_remediation["submission_id"])
        self.assertNotIn("response_submission_id", open_remediation)

        live_workspace = self.api._workspace(workspace["id"])
        resubmitted = self.submit(
            {"id": workspace["id"], "revision": live_workspace.revision},
            key="teacher-remediation-submit-2",
        )
        responded = request(self.api, "GET", teacher_path)
        self.assertEqual(200, responded.status)
        responded_remediation = responded.payload["data"]["remediations"][0]
        self.assertEqual("RESPONDED", responded_remediation["state"])
        self.assertEqual(submission["id"], responded_remediation["submission_id"])
        self.assertEqual(resubmitted["id"], responded_remediation["response_submission_id"])

        # The student demo role still reads its own published workspace via its existing route.
        student_read = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/remediation")
        self.assertEqual(200, student_read.status)
        self.assertEqual("RESPONDED", student_read.payload["data"]["remediations"][0]["state"])

    def test_teacher_review_queue_tracks_only_current_pending_submission(self) -> None:
        assignment, workspace = self.publish()
        student_queue = request(self.api, "GET", f"/api/v1/demo/student/assignments/{assignment['id']}/review-queue")
        self.assertEqual(404, student_queue.status)

        started = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="queue-start", revision=workspace["revision"])
        self.assertEqual(200, started.status)
        workspace = started.payload["data"]["workspace"]
        first_submission = self.submit(workspace, key="queue-submit-1")
        queue_path = f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-queue"
        queue = request(self.api, "GET", queue_path)
        self.assertEqual([first_submission["id"]], [item["id"] for item in queue.payload["data"]["submissions"]])

        first_review = self.review(
            first_submission, self.api._workspace(workspace["id"]).revision,
            kind="REQUEST_REMEDIATION", reason="请补充逐项核对与业务规则说明。", key="queue-review-1",
        )
        self.assertEqual(201, first_review.status)
        self.assertEqual([], request(self.api, "GET", queue_path).payload["data"]["submissions"])

        live = self.api._workspace(workspace["id"])
        second_submission = self.submit({**workspace, "revision": live.revision}, key="queue-submit-2")
        queue_after_resubmission = request(self.api, "GET", queue_path)
        self.assertEqual([second_submission["id"]], [item["id"] for item in queue_after_resubmission.payload["data"]["submissions"]])

        closing_review = self.review(
            second_submission, self.api._workspace(workspace["id"]).revision,
            kind="ACKNOWLEDGE", reason="已核验补正说明与提交结果一致。", key="queue-review-2",
        )
        self.assertEqual(201, closing_review.status)
        self.assertEqual([], request(self.api, "GET", queue_path).payload["data"]["submissions"])

    def test_all_review_actions_require_reason_including_acknowledge(self) -> None:
        _, workspace = self.start()
        submission = self.submit(workspace)
        response = self.review(submission, self.api._workspace(workspace["id"]).revision, kind="ACKNOWLEDGE", reason="同意")
        self.assertEqual(422, response.status)
        self.assertEqual("reason_too_short", response.payload["error"]["code"])

    def test_teacher_review_history_pages_ack_and_other_actions_without_mutating(self) -> None:
        assignment, workspace = self.publish()
        base = f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-history"
        empty = request(self.api, "GET", base)
        self.assertEqual(200, empty.status)
        self.assertEqual({"review_actions": [], "next_sequence": 0, "has_more": False}, empty.payload["data"])

        workspace_state = self.api._workspace(workspace["id"])
        started = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="history-start", revision=workspace_state.revision)
        submission1 = self.submit(started.payload["data"]["workspace"], key="history-submit-1")
        live = self.api._workspace(workspace["id"])
        first_review = self.review(submission1, live.revision, kind="REQUEST_EXPLANATION", key="history-review-1")
        self.assertEqual(201, first_review.status)

        live = self.api._workspace(workspace["id"])
        submission2_response = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION + " 补充复核过程。"},
            key="history-submit-2", revision=live.revision,
        )
        self.assertEqual(201, submission2_response.status)
        live = self.api._workspace(workspace["id"])
        second_review = self.review(submission2_response.payload["data"]["submission"], live.revision, kind="ACKNOWLEDGE", reason="已完成复核，说明清楚。", key="history-review-2")
        self.assertEqual(201, second_review.status)

        live = self.api._workspace(workspace["id"])
        revision_before = live.revision
        events_before = len(live.events)
        all_history = request(self.api, "GET", f"{base}?after_sequence=0&limit=50")
        records = all_history.payload["data"]["review_actions"]
        self.assertEqual(["REQUEST_EXPLANATION", "ACKNOWLEDGE"], [item["kind"] for item in records])
        sequences = [item["created_event_sequence"] for item in records]
        self.assertEqual(sorted(sequences), sequences)
        self.assertEqual(first_review.payload["data"]["review_action"]["id"], records[0]["id"])
        self.assertEqual(second_review.payload["data"]["review_action"]["id"], records[1]["id"])
        self.assertTrue(all(set(item) == {"id", "submission_id", "submission_version", "kind", "reason", "created_event_sequence"} for item in records))
        self.assertNotIn("student_explanation", all_history.payload["data"])
        self.assertNotIn("artifact_snapshots", all_history.payload["data"])
        self.assertEqual(revision_before, live.revision)
        self.assertEqual(events_before, len(live.events))

        first_page = request(self.api, "GET", f"{base}?after_sequence=0&limit=1").payload["data"]
        self.assertEqual(1, len(first_page["review_actions"]))
        self.assertTrue(first_page["has_more"])
        second_page = request(self.api, "GET", f"{base}?after_sequence={first_page['next_sequence']}&limit=1").payload["data"]
        self.assertEqual([records[1]["id"]], [item["id"] for item in second_page["review_actions"]])
        self.assertFalse(second_page["has_more"])
        self.assertEqual(sequences, [first_page["review_actions"][0]["created_event_sequence"], second_page["review_actions"][0]["created_event_sequence"]])

    def test_review_history_role_and_resource_denial_are_uniform_404(self) -> None:
        draft = self.create_assignment()
        published, _ = self.publish()
        self.api._assignment(published["id"]).workspace = None
        active, _ = self.publish()
        responses = [
            request(self.api, "GET", f"/api/v1/demo/teacher/assignments/{draft['id']}/review-history"),
            request(self.api, "GET", "/api/v1/demo/teacher/assignments/missing/review-history"),
            request(self.api, "GET", f"/api/v1/demo/teacher/assignments/{published['id']}/review-history"),
            request(self.api, "GET", f"/api/v1/demo/student/assignments/{active['id']}/review-history"),
        ]
        self.assertTrue(all(response.status == 404 for response in responses))
        self.assertTrue(all(response.payload["error"]["code"] == "not_found" for response in responses))
        self.assertTrue(all(response.payload["error"]["message"] == "resource was not found" for response in responses))

    def test_review_history_rejects_malformed_cursor_and_limit(self) -> None:
        assignment, _ = self.publish()
        base = f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-history"
        cases = [
            ("?after_sequence=bad", "invalid_cursor"),
            ("?after_sequence=-1", "invalid_cursor"),
            ("?after_sequence=0&after_sequence=1", "invalid_cursor"),
            ("?after_sequence=", "invalid_cursor"),
            ("?limit=0", "invalid_page_limit"),
            ("?limit=51", "invalid_page_limit"),
            ("?limit=", "invalid_page_limit"),
            ("?limit=1&limit=2", "invalid_cursor"),
        ]
        for suffix, code in cases:
            with self.subTest(suffix=suffix):
                response = request(self.api, "GET", base + suffix)
                self.assertEqual(400, response.status)
                self.assertEqual(code, response.payload["error"]["code"])

    def test_review_reason_minimum_counts_non_whitespace_characters(self) -> None:
        _, workspace = self.start()
        submission = self.submit(workspace)
        response = self.review(
            submission, self.api._workspace(workspace["id"]).revision,
            reason="请       好", key="review-whitespace-only",
        )
        self.assertEqual(422, response.status)
        self.assertEqual("reason_too_short", response.payload["error"]["code"])

    def test_non_allowlisted_artifact_and_too_short_explanation_are_rejected(self) -> None:
        _, workspace = self.start()
        response = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["../../private.txt"], "artifact_contents": {"../../private.txt": "not allowed"}, "student_explanation": EXPLANATION}, key="bad-artifact", revision=workspace["revision"],
        )
        self.assertEqual(422, response.status)
        self.assertNotIn("../../private.txt", json.dumps(response.payload, ensure_ascii=False))
        self.assertNotIn("not allowed", json.dumps(response.payload, ensure_ascii=False))
        short = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py"], "artifact_contents": {"main.py": ARTIFACT_CONTENTS["main.py"]}, "student_explanation": "Agent 已帮我完成。"}, key="short-note", revision=workspace["revision"],
        )
        self.assertEqual(422, short.status)
        self.assertNotIn("Agent 已帮我完成。", json.dumps(short.payload, ensure_ascii=False))

    def test_submission_artifact_snapshots_are_exact_bounded_and_hashed(self) -> None:
        assignment, workspace = self.start()
        payload = {
            "artifact_refs": ["main.py", "orders.csv"],
            "artifact_contents": ARTIFACT_CONTENTS,
            "student_explanation": EXPLANATION,
        }
        response = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            payload, key="artifact-snapshot", revision=workspace["revision"],
        )
        self.assertEqual(201, response.status)
        submission = response.payload["data"]["submission"]
        snapshots = submission["artifact_snapshots"]
        self.assertEqual(set(ARTIFACT_CONTENTS), {item["logical_name"] for item in snapshots})
        for item in snapshots:
            content = ARTIFACT_CONTENTS[item["logical_name"]]
            encoded = content.encode("utf-8")
            self.assertEqual(content, item["content"])
            self.assertEqual(len(encoded), item["size_bytes"])
            self.assertEqual(hashlib.sha256(encoded).hexdigest(), item["sha256"])

        queue = request(self.api, "GET", f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-queue")
        self.assertEqual(snapshots, queue.payload["data"]["submissions"][0]["artifact_snapshots"])

        missing = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {**payload, "artifact_contents": {"main.py": ARTIFACT_CONTENTS["main.py"]}},
            key="artifact-snapshot-missing", revision=self.api._workspace(workspace["id"]).revision,
        )
        self.assertEqual("invalid_artifact_contents", missing.payload["error"]["code"])

        nul_content = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py"], "artifact_contents": {"main.py": "bad\x00text"}, "student_explanation": EXPLANATION},
            key="artifact-snapshot-nul", revision=self.api._workspace(workspace["id"]).revision,
        )
        self.assertEqual("invalid_artifact_contents", nul_content.payload["error"]["code"])
        non_text = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py"], "artifact_contents": {"main.py": 12}, "student_explanation": EXPLANATION},
            key="artifact-snapshot-not-text", revision=self.api._workspace(workspace["id"]).revision,
        )
        self.assertEqual("invalid_artifact_contents", non_text.payload["error"]["code"])

        oversized_file = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py"], "artifact_contents": {"main.py": "x" * 8193}, "student_explanation": EXPLANATION},
            key="artifact-snapshot-file-too-large", revision=self.api._workspace(workspace["id"]).revision,
        )
        self.assertEqual(413, oversized_file.status)
        oversized_set = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": {"main.py": "x" * 6500, "orders.csv": "y" * 6500}, "student_explanation": EXPLANATION},
            key="artifact-snapshot-total-too-large", revision=self.api._workspace(workspace["id"]).revision,
        )
        self.assertEqual("artifacts_too_large", oversized_set.payload["error"]["code"])

    def test_student_can_read_only_the_latest_submission_including_accepted_state(self) -> None:
        assignment, workspace = self.publish()
        path = f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest"
        initial_internal = self.api._workspace(workspace["id"])
        initial_revision = initial_internal.revision
        initial_event_count = len(initial_internal.events)
        empty = request(self.api, "GET", path)
        self.assertEqual(200, empty.status)
        self.assertEqual({"submission": None}, empty.payload["data"])
        self.assertEqual(initial_revision, initial_internal.revision)
        self.assertEqual(initial_event_count, len(initial_internal.events))

        started = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start",
            key="latest-start", revision=workspace["revision"],
        )
        live_workspace = started.payload["data"]["workspace"]
        first = self.submit(live_workspace, key="latest-submit-first")
        after_first_submit = self.api._workspace(workspace["id"])
        revision_before_read = after_first_submit.revision
        event_count_before_read = len(after_first_submit.events)
        latest_first = request(self.api, "GET", path).payload["data"]["submission"]
        self.assertEqual(revision_before_read, after_first_submit.revision)
        self.assertEqual(event_count_before_read, len(after_first_submit.events))
        self.assertEqual(first, latest_first)
        self.assertEqual(1, latest_first["version"])
        self.assertEqual("SUBMITTED", latest_first["state"])
        self.assertEqual(assignment["version"], latest_first["assignment_version"])
        self.assertEqual(workspace["id"], latest_first["workspace_id"])
        self.assertEqual(ARTIFACT_CONTENTS, {item["logical_name"]: item["content"] for item in latest_first["artifact_snapshots"]})
        for snapshot in latest_first["artifact_snapshots"]:
            encoded = ARTIFACT_CONTENTS[snapshot["logical_name"]].encode("utf-8")
            self.assertEqual(len(encoded), snapshot["size_bytes"])
            self.assertEqual(hashlib.sha256(encoded).hexdigest(), snapshot["sha256"])
        created_event = next(event for event in self.api._workspace(workspace["id"]).events if event["sequence"] == latest_first["created_event_sequence"])
        self.assertEqual("submission.created", created_event["event_type"])
        self.assertEqual(first["id"], created_event["resource_ref"])

        feedback = self.review(first, self.api._workspace(workspace["id"]).revision, key="latest-review-feedback")
        self.assertEqual(201, feedback.status)
        after_feedback = self.api._workspace(workspace["id"])
        second = self.submit(
            {"id": workspace["id"], "revision": after_feedback.revision},
            key="latest-submit-second",
        )
        latest_second = request(self.api, "GET", path).payload["data"]["submission"]
        self.assertEqual(second, latest_second)
        self.assertEqual(2, latest_second["version"])
        self.assertNotEqual(first["id"], latest_second["id"])

        accepted = self.review(
            second, self.api._workspace(workspace["id"]).revision,
            kind="ACKNOWLEDGE", reason="已核对最新提交快照及补正说明。", key="latest-review-accepted",
        )
        self.assertEqual(201, accepted.status)
        latest_accepted = request(self.api, "GET", path).payload["data"]["submission"]
        self.assertEqual(second["id"], latest_accepted["id"])
        self.assertEqual(2, latest_accepted["version"])
        self.assertEqual("ACCEPTED", latest_accepted["state"])

    def test_latest_submission_read_is_student_only_and_requires_owned_published_workspace(self) -> None:
        _, workspace = self.publish()
        path = f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest"
        teacher = request(self.api, "GET", f"/api/v1/demo/teacher/workspaces/{workspace['id']}/submissions/latest")
        self.assertEqual(404, teacher.status)
        self.assertEqual("not_found", teacher.payload["error"]["code"])

        missing = request(self.api, "GET", "/api/v1/demo/student/workspaces/workspace-missing/submissions/latest")
        self.assertEqual(404, missing.status)
        self.assertEqual("not_found", missing.payload["error"]["code"])

        internal = self.api._workspace(workspace["id"])
        internal.student_actor_ref = "different-demo-actor"
        wrong_owner = request(self.api, "GET", path)
        self.assertEqual(404, wrong_owner.status)
        self.assertEqual("not_found", wrong_owner.payload["error"]["code"])

        internal.student_actor_ref = "student-demo"
        self.api._assignment(internal.assignment_id).state = "DRAFT"
        unpublished = request(self.api, "GET", path)
        self.assertEqual(404, unpublished.status)
        self.assertEqual("not_found", unpublished.payload["error"]["code"])

    def test_student_reads_and_start_hide_workspace_owned_by_another_demo_actor_without_side_effects(self) -> None:
        assignment, workspace = self.publish()
        started = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start",
            key="owned-demo-student-start", revision=workspace["revision"],
        )
        self.assertEqual(200, started.status)
        workspace = started.payload["data"]["workspace"]
        internal = self.api._workspace(workspace["id"])
        paths = (
            f"/api/v1/demo/student/workspaces/{workspace['id']}",
            f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest",
            f"/api/v1/demo/student/workspaces/{workspace['id']}/remediation",
            f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence=0&limit=50",
        )
        before_revision = internal.revision
        before_state = internal.state
        before_submissions = list(internal.submissions)
        before_events = list(internal.events)
        before_submission_counter = self.api.store._next_submission
        before_idempotency = dict(self.api._idempotent)
        internal.student_actor_ref = "student-other"

        for path in paths:
            with self.subTest(path=path):
                response = request(self.api, "GET", path)
                self.assertEqual(404, response.status)
                self.assertEqual("not_found", response.payload["error"]["code"])

        denied_start = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start",
            key="other-demo-student-start", revision=before_revision,
        )
        self.assertEqual(404, denied_start.status)
        self.assertEqual("not_found", denied_start.payload["error"]["code"])
        self.assertEqual(before_state, internal.state)
        self.assertEqual(before_revision, internal.revision)
        self.assertEqual(before_submissions, internal.submissions)
        self.assertEqual(before_events, internal.events)

        denied_writes = (
            ("pause", "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/pause", {}, "other-pause"),
            ("agent turn", "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns", {"question": "请解释任务目标"}, "other-agent-turn"),
            ("proposal decision", "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/proposed-actions/proposal-missing/decision", {"decision": "ACCEPTED"}, "other-proposal-decision"),
            ("submission", "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions", {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION}, "other-submission"),
        )
        for label, method, write_path, payload, key in denied_writes:
            with self.subTest(write=label):
                response = request(self.api, method, write_path, payload, key=key, revision=before_revision)
                self.assertEqual(404, response.status)
                self.assertEqual("not_found", response.payload["error"]["code"])

        self.assertEqual(before_state, internal.state)
        self.assertEqual(before_revision, internal.revision)
        self.assertEqual(before_submissions, internal.submissions)
        self.assertEqual(before_submission_counter, self.api.store._next_submission)
        self.assertEqual(before_events, internal.events)
        self.assertEqual(before_idempotency, self.api._idempotent)

        internal.student_actor_ref = "student-demo"
        owned_read = request(self.api, "GET", paths[0])
        self.assertEqual(200, owned_read.status)
        self.assertEqual(assignment["id"], owned_read.payload["data"]["assignment_id"])

    def test_agent_is_fixed_scripted_and_does_not_accept_provider_or_tool_fields(self) -> None:
        _, workspace = self.start()
        response = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns",
            {"question": "如何核对金额？", "provider": "external", "enable_tools": True}, key="bad-agent", revision=workspace["revision"],
        )
        self.assertEqual(400, response.status)
        good = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns",
            {"question": "如何核对金额？"}, key="agent-1", revision=workspace["revision"],
        )
        self.assertEqual("scripted-demo", good.payload["data"]["turn"]["provider_mode"])
        self.assertNotIn("如何核对金额？", json.dumps(good.payload, ensure_ascii=False))

    def test_qa_only_assignment_does_not_return_a_file_change_proposal(self) -> None:
        qa_task = {**TASK, "collaboration_mode": "QA_ONLY"}
        created = request(self.api, "POST", "/api/v1/demo/teacher/assignments", qa_task, key="qa-create")
        published = request(self.api, "POST", f"/api/v1/demo/teacher/assignments/{created.payload['data']['id']}/publish", key="qa-publish", revision=created.payload["data"]["revision"])
        workspace = published.payload["data"]["workspace"]
        started = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="qa-start", revision=workspace["revision"])
        turn = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns", {"question": "请解释任务目标"}, key="qa-turn", revision=started.payload["revision"])
        self.assertEqual(200, turn.status)
        self.assertEqual("scripted-demo", turn.payload["data"]["turn"]["provider_mode"])
        self.assertNotIn("proposed_action", turn.payload["data"])

    def test_proposal_decision_is_student_controlled_and_does_not_execute(self) -> None:
        _, workspace = self.start()
        turn = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns", {"question": "检查思路"}, key="agent-1", revision=workspace["revision"])
        updated_revision = turn.payload["revision"]
        proposal_id = turn.payload["data"]["proposed_action"]["id"]
        decision = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/proposed-actions/{proposal_id}/decision", {"decision": "ACCEPTED"}, key="decision-1", revision=updated_revision)
        self.assertEqual("ACCEPTED", decision.payload["data"]["proposed_action"]["status"])
        self.assertFalse(decision.payload["data"].get("execution_enabled", False))

    def test_idempotent_agent_turn_replay_preserves_original_response_snapshot(self) -> None:
        _, workspace = self.start()
        original = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns",
            {"question": "检查思路"}, key="agent-stable-replay", revision=workspace["revision"],
        )
        proposal_id = original.payload["data"]["proposed_action"]["id"]
        request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/proposed-actions/{proposal_id}/decision",
            {"decision": "ACCEPTED"}, key="decision-after-agent", revision=original.payload["revision"],
        )
        replay = request(
            self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns",
            {"question": "检查思路"}, key="agent-stable-replay", revision=workspace["revision"],
        )
        self.assertEqual("PROPOSED", replay.payload["data"]["proposed_action"]["status"])

    def test_run_shell_or_filesystem_endpoints_do_not_exist(self) -> None:
        _, workspace = self.start()
        for endpoint in ("run", "shell", "files", "install-dependencies"):
            response = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/{endpoint}", {}, key=f"forbidden-{endpoint}", revision=workspace["revision"])
            self.assertEqual(404, response.status, endpoint)

    def test_teacher_only_review_queue_student_only_workspace_mutations(self) -> None:
        _, workspace = self.start()
        forbidden = request(self.api, "POST", f"/api/v1/demo/teacher/workspaces/{workspace['id']}/start", key="teacher-start", revision=workspace["revision"])
        self.assertEqual(404, forbidden.status)
        teacher_list = request(self.api, "GET", "/api/v1/demo/teacher/assignments")
        self.assertEqual(200, teacher_list.status)

    def test_events_have_server_order_and_support_bounded_cursor(self) -> None:
        _, workspace = self.publish()
        start = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="start-1", revision=workspace["revision"])
        live = start.payload["data"]["workspace"]
        self.submit(live)
        all_events = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence=0")
        events = all_events.payload["data"]["events"]
        self.assertEqual(sorted(event["sequence"] for event in events), [event["sequence"] for event in events])
        self.assertTrue(all(event["event_id"].startswith("event-") for event in events))
        cursor = events[0]["sequence"]
        rest = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence={cursor}")
        self.assertTrue(all(event["sequence"] > cursor for event in rest.payload["data"]["events"]))
        first_page = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence=0&limit=1")
        self.assertEqual(1, len(first_page.payload["data"]["events"]))
        self.assertTrue(first_page.payload["data"]["has_more"])
        next_page = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence={first_page.payload['data']['next_sequence']}&limit=1")
        self.assertGreater(next_page.payload["data"]["events"][0]["sequence"], first_page.payload["data"]["next_sequence"])

    def test_event_cursor_expiry_and_page_limits_are_explicit(self) -> None:
        _, workspace = self.publish()
        live = self.api._workspace(workspace["id"])
        for index in range(260):
            self.api.store.event(live, "student", "synthetic.test_event", f"resource-{index}")
        expired = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence=0")
        self.assertEqual(409, expired.status)
        self.assertEqual("cursor_expired", expired.payload["error"]["code"])
        invalid_zero = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?limit=0")
        invalid_large = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?limit=51")
        duplicate = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?limit=2&limit=3")
        empty_limit = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?limit=")
        empty_cursor = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence=")
        self.assertEqual("invalid_page_limit", invalid_zero.payload["error"]["code"])
        self.assertEqual("invalid_page_limit", invalid_large.payload["error"]["code"])
        self.assertEqual("invalid_cursor", duplicate.payload["error"]["code"])
        self.assertEqual("invalid_page_limit", empty_limit.payload["error"]["code"])
        self.assertEqual("invalid_cursor", empty_cursor.payload["error"]["code"])

    def test_core_response_objects_have_required_fields_and_event_request_id(self) -> None:
        created = self.create_assignment()
        self.assertTrue({"id", "version", "state", "revision", "task", "workspace"} <= created.keys())
        self.assertTrue({"title", "goal", "starter_project_id", "student_responsibility", "submission_requirements", "collaboration_mode", "execution_enabled"} <= created["task"].keys())
        publish_response = request(
            self.api, "POST", f"/api/v1/demo/teacher/assignments/{created['id']}/publish",
            key="shape-publish", revision=created["revision"],
        )
        assignment = publish_response.payload["data"]["assignment"]
        workspace = publish_response.payload["data"]["workspace"]
        self.assertTrue({"id", "assignment_id", "assignment_version", "state", "revision", "execution_enabled", "artifact_refs"} <= workspace.keys())
        self.assertTrue({"id", "logical_name", "media_type", "source", "integrity_status"} <= workspace["artifact_refs"][0].keys())
        publish_event = self.api._workspace(workspace["id"]).events[0]
        self.assertTrue({"event_id", "sequence", "schema_version", "workspace_id", "actor_role", "event_type", "resource_ref", "request_id", "occurred_at"} <= publish_event.keys())
        self.assertEqual(publish_response.payload["request_id"], publish_event["request_id"])

        started = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="shape-start", revision=workspace["revision"])
        live_workspace = started.payload["data"]["workspace"]
        turn = request(self.api, "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns", {"question": "如何验证？"}, key="shape-agent", revision=live_workspace["revision"])
        self.assertTrue({"id", "provider_mode", "response_text", "availability", "event_sequence"} <= turn.payload["data"]["turn"].keys())
        self.assertTrue({"id", "kind", "target_artifact_ref", "status", "diff"} <= turn.payload["data"]["proposed_action"].keys())
        submission = self.submit({**live_workspace, "revision": turn.payload["revision"]}, key="shape-submit")
        self.assertTrue({"id", "workspace_id", "assignment_version", "version", "artifact_refs", "student_explanation", "state", "created_event_sequence"} <= submission.keys())
        review = self.review(submission, self.api._workspace(workspace["id"]).revision, key="shape-review")
        review_action = review.payload["data"]["review_action"]
        self.assertTrue({"id", "submission_id", "submission_version", "kind", "reason", "created_event_sequence"} <= review_action.keys())
        remediation = request(self.api, "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/remediation").payload["data"]["remediations"][0]
        self.assertTrue({"id", "review_action_id", "submission_id", "requested_action", "reason", "state"} <= remediation.keys())

    def test_body_limit_and_malformed_json_fail_closed(self) -> None:
        too_large = self.api.handle("POST", "/api/v1/demo/teacher/assignments", b" " * 20_000, idempotency_key="large")
        malformed = self.api.handle("POST", "/api/v1/demo/teacher/assignments", "not-json", idempotency_key="broken")
        self.assertEqual(413, too_large.status)
        self.assertEqual(400, malformed.status)

    def test_artifact_reference_does_not_claim_uncomputed_integrity(self) -> None:
        _, workspace = self.start()
        submission = self.submit(workspace)
        references = submission["artifact_refs"]
        self.assertTrue(references)
        self.assertTrue(all(item["integrity_status"] == "NOT_COMPUTED" for item in references))
        self.assertTrue(all("sha256" not in item and "path" not in item for item in references))


if __name__ == "__main__":
    unittest.main()
