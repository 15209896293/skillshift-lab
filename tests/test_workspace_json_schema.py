from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.workspace_api import WorkspaceApi


SCHEMA_PATH = ROOT / "specs" / "R0-WORKSPACE-CONTROL-PLANE-CONTRACT" / "workspace-api-v1.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
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


class WorkspaceJsonSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = WorkspaceApi()

    def dto(self, name: str, value: dict) -> None:
        root_schema = {
            "$schema": SCHEMA["$schema"],
            "$defs": SCHEMA["$defs"],
            "$ref": f"#/$defs/{name}",
        }
        Draft202012Validator(root_schema, format_checker=FormatChecker()).validate(value)

    def success(self, response) -> None:
        self.dto("SuccessEnvelope", response.payload)

    def post(self, path: str, payload: dict, *, key: str, revision: int | None = None):
        payload = {"schema_version": "skillshift-api/v1", **payload}
        return self.api.handle(
            "POST", path, json.dumps(payload, ensure_ascii=False),
            idempotency_key=key,
            if_match=str(revision) if revision is not None else None,
        )

    def test_schema_document_is_valid_and_all_core_wire_dtos_validate(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)

        health = self.api.handle("GET", "/api/v1/health")
        self.success(health)
        self.dto("HealthData", health.payload["data"])
        created = self.post("/api/v1/demo/teacher/assignments", TASK, key="schema-create")
        self.success(created)
        assignment = created.payload["data"]
        self.dto("Assignment", assignment)
        self.dto("Task", assignment["task"])
        teacher_catalog = self.api.handle("GET", "/api/v1/demo/teacher/assignments")
        self.success(teacher_catalog)
        self.dto("AssignmentListData", teacher_catalog.payload["data"])

        published = self.post(
            f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", {},
            key="schema-publish", revision=assignment["revision"],
        )
        publish_data = published.payload["data"]
        self.success(published)
        self.dto("AssignmentPublishData", publish_data)
        self.dto("Assignment", publish_data["assignment"])
        workspace = publish_data["workspace"]
        self.dto("Workspace", workspace)
        latest_submission = self.api.handle(
            "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest",
        )
        self.success(latest_submission)
        self.dto("LatestSubmissionData", latest_submission.payload["data"])
        self.assertIsNone(latest_submission.payload["data"]["submission"])
        for artifact in workspace["artifact_refs"]:
            self.dto("ArtifactReference", artifact)
        self.dto("EvidenceEvent", publish_data["event"])
        student_catalog = self.api.handle("GET", "/api/v1/demo/student/assignments")
        self.success(student_catalog)
        self.dto("AssignmentListData", student_catalog.payload["data"])
        assignment_read = self.api.handle("GET", f"/api/v1/demo/student/assignments/{assignment['id']}")
        self.success(assignment_read)
        self.dto("Assignment", assignment_read.payload["data"])

        started = self.post(
            f"/api/v1/demo/student/workspaces/{workspace['id']}/start", {},
            key="schema-start", revision=workspace["revision"],
        )
        self.success(started)
        self.dto("WorkspaceStartData", started.payload["data"])
        self.dto("EvidenceEvent", started.payload["data"]["event"])
        workspace = started.payload["data"]["workspace"]
        self.dto("Workspace", workspace)
        workspace_read = self.api.handle("GET", f"/api/v1/demo/student/workspaces/{workspace['id']}")
        self.success(workspace_read)
        self.dto("Workspace", workspace_read.payload["data"])
        turn_response = self.post(
            f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns", {"question": "如何核验？"},
            key="schema-turn", revision=workspace["revision"],
        )
        self.success(turn_response)
        turn_data = turn_response.payload["data"]
        self.dto("AgentTurnData", turn_data)
        self.dto("AgentTurn", turn_data["turn"])
        proposal = turn_data["proposed_action"]
        self.dto("ProposedAction", proposal)
        decision = self.post(
            f"/api/v1/demo/student/workspaces/{workspace['id']}/proposed-actions/{proposal['id']}/decision",
            {"decision": "ACCEPTED"}, key="schema-decision", revision=turn_response.payload["revision"],
        )
        self.success(decision)
        self.dto("ProposedActionDecisionData", decision.payload["data"])
        self.dto("ProposedAction", decision.payload["data"]["proposed_action"])

        workspace_state = self.api._workspace(workspace["id"])
        submission_response = self.post(
            f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION},
            key="schema-submit", revision=workspace_state.revision,
        )
        self.success(submission_response)
        self.dto("SubmissionData", submission_response.payload["data"])
        submission = submission_response.payload["data"]["submission"]
        self.dto("Submission", submission)
        latest_submission = self.api.handle(
            "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest",
        )
        self.success(latest_submission)
        self.dto("LatestSubmissionData", latest_submission.payload["data"])
        self.assertEqual(submission, latest_submission.payload["data"]["submission"])
        for artifact in submission["artifact_refs"]:
            self.dto("ArtifactReference", artifact)
        for snapshot in submission["artifact_snapshots"]:
            self.dto("ArtifactSnapshot", snapshot)
        review_queue = self.api.handle("GET", f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-queue")
        self.success(review_queue)
        self.dto("ReviewQueueData", review_queue.payload["data"])
        self.assertEqual(submission, review_queue.payload["data"]["submissions"][0])

        workspace_state = self.api._workspace(workspace["id"])
        review = self.post(
            f"/api/v1/demo/teacher/submissions/{submission['id']}/review-actions",
            {"kind": "REQUEST_EXPLANATION", "reason": "请解释你如何核验金额规则。"},
            key="schema-review", revision=workspace_state.revision,
        )
        self.success(review)
        self.dto("ReviewActionData", review.payload["data"])
        self.dto("ReviewAction", review.payload["data"]["review_action"])
        review_history = self.api.handle("GET", f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-history?after_sequence=0&limit=50")
        self.success(review_history)
        self.dto("ReviewHistoryData", review_history.payload["data"])
        self.assertEqual([review.payload["data"]["review_action"]], review_history.payload["data"]["review_actions"])
        history_validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/ReviewHistoryData"})
        self.assertFalse(history_validator.is_valid({"review_actions": [{k: v for k, v in review.payload["data"]["review_action"].items() if k != "created_event_sequence"}], "next_sequence": 0, "has_more": False}))
        self.assertFalse(history_validator.is_valid({"review_actions": [{**review.payload["data"]["review_action"], "student_explanation": EXPLANATION}], "next_sequence": 0, "has_more": False}))
        self.assertFalse(history_validator.is_valid({"review_actions": [{**review.payload["data"]["review_action"], "artifact_snapshots": ARTIFACT_CONTENTS}], "next_sequence": 0, "has_more": False}))
        remediation = self.api.handle("GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/remediation")
        self.success(remediation)
        self.dto("RemediationListData", remediation.payload["data"])
        self.dto("Remediation", remediation.payload["data"]["remediations"][0])
        self.assertEqual("OPEN", remediation.payload["data"]["remediations"][0]["state"])

        workspace_state = self.api._workspace(workspace["id"])
        resubmitted_response = self.post(
            f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions",
            {"artifact_refs": ["main.py", "orders.csv"], "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION + " 补正说明已补充。"},
            key="schema-resubmit", revision=workspace_state.revision,
        )
        self.success(resubmitted_response)
        self.dto("SubmissionData", resubmitted_response.payload["data"])
        resubmitted = resubmitted_response.payload["data"]["submission"]
        self.assertEqual(2, resubmitted["version"])
        self.assertEqual("RESUBMITTED", resubmitted["state"])
        latest_submission = self.api.handle(
            "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest",
        )
        self.success(latest_submission)
        self.dto("LatestSubmissionData", latest_submission.payload["data"])
        self.assertEqual(resubmitted, latest_submission.payload["data"]["submission"])

        remediation = self.api.handle("GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/remediation")
        self.success(remediation)
        self.dto("RemediationListData", remediation.payload["data"])
        responded = remediation.payload["data"]["remediations"][0]
        self.dto("Remediation", responded)
        self.assertEqual("RESPONDED", responded["state"])
        self.assertEqual(resubmitted["id"], responded["response_submission_id"])
        review_queue = self.api.handle("GET", f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-queue")
        self.success(review_queue)
        self.dto("ReviewQueueData", review_queue.payload["data"])
        self.assertEqual(resubmitted["id"], review_queue.payload["data"]["submissions"][0]["id"])

        workspace_state = self.api._workspace(workspace["id"])
        acknowledged = self.post(
            f"/api/v1/demo/teacher/submissions/{resubmitted['id']}/review-actions",
            {"kind": "ACKNOWLEDGE", "reason": "已核对补正说明和提交快照。"},
            key="schema-acknowledge", revision=workspace_state.revision,
        )
        self.success(acknowledged)
        self.dto("ReviewActionData", acknowledged.payload["data"])
        final_workspace = self.api.handle("GET", f"/api/v1/demo/student/workspaces/{workspace['id']}")
        self.success(final_workspace)
        self.dto("Workspace", final_workspace.payload["data"])
        self.assertEqual("CLOSED", final_workspace.payload["data"]["state"])
        latest_submission = self.api.handle(
            "GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/submissions/latest",
        )
        self.success(latest_submission)
        self.dto("LatestSubmissionData", latest_submission.payload["data"])
        self.assertEqual(resubmitted["id"], latest_submission.payload["data"]["submission"]["id"])
        self.assertEqual("ACCEPTED", latest_submission.payload["data"]["submission"]["state"])
        final_queue = self.api.handle("GET", f"/api/v1/demo/teacher/assignments/{assignment['id']}/review-queue")
        self.success(final_queue)
        self.dto("ReviewQueueData", final_queue.payload["data"])
        self.assertEqual([], final_queue.payload["data"]["submissions"])

        page = self.api.handle("GET", f"/api/v1/demo/student/workspaces/{workspace['id']}/events?after_sequence=0&limit=2")
        self.success(page)
        self.dto("EventPage", page.payload["data"])
        for event in page.payload["data"]["events"]:
            self.dto("EvidenceEvent", event)

    def test_all_frontend_write_request_dtos_have_strict_schema_versions(self) -> None:
        create_request = {"schema_version": "skillshift-api/v1", **TASK}
        self.dto("AssignmentCreateRequest", create_request)
        self.dto("EmptyRequest", {"schema_version": "skillshift-api/v1"})
        self.dto("AgentTurnRequest", {"schema_version": "skillshift-api/v1", "question": "如何核验？"})
        self.dto("ProposedActionDecisionRequest", {"schema_version": "skillshift-api/v1", "decision": "ACCEPTED"})
        self.dto("SubmissionCreateRequest", {
            "schema_version": "skillshift-api/v1", "artifact_refs": ["main.py", "orders.csv"],
            "artifact_contents": ARTIFACT_CONTENTS, "student_explanation": EXPLANATION,
        })
        self.dto("ReviewActionRequest", {
            "schema_version": "skillshift-api/v1", "kind": "REQUEST_EXPLANATION",
            "reason": "请解释你如何核验金额规则。",
        })
        self.assertFalse(Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/AssignmentCreateRequest"}).is_valid({**create_request, "actor_id": "student-demo"}))
        self.assertFalse(Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/EmptyRequest"}).is_valid({"schema_version": "skillshift-api/v0"}))

    def test_schemas_reject_unknown_fields_wrong_enums_and_oversized_pages(self) -> None:
        strict_validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/ArtifactReference"})
        valid = {"id": "artifact-main", "logical_name": "main.py", "media_type": "text/x-python", "source": "FIXED_SYNTHETIC", "integrity_status": "NOT_COMPUTED"}
        self.assertTrue(strict_validator.is_valid(valid))
        self.assertFalse(strict_validator.is_valid({**valid, "student_content": "unreviewed"}))
        self.assertFalse(strict_validator.is_valid({**valid, "source": "CLIENT_UPLOAD"}))

        snapshot_validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/ArtifactSnapshot"})
        snapshot = {"logical_name": "main.py", "media_type": "text/x-python", "size_bytes": 2, "sha256": "a" * 64, "content": "ok"}
        self.assertTrue(snapshot_validator.is_valid(snapshot))
        self.assertFalse(snapshot_validator.is_valid({**snapshot, "local_path": "C:/private"}))
        self.assertFalse(snapshot_validator.is_valid({**snapshot, "logical_name": "../../outside.py"}))
        self.assertFalse(snapshot_validator.is_valid({**snapshot, "content": "x" * 8193, "size_bytes": 8193}))

        page_validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/EventPage"})
        self.assertFalse(page_validator.is_valid({"events": [{}] * 51, "next_sequence": 51, "has_more": False}))

    def test_review_reason_schema_rejects_eight_spaces_disguised_as_length(self) -> None:
        review_validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/ReviewAction"})
        base = {"id": "review-1", "submission_id": "submission-1", "submission_version": 1, "kind": "ACKNOWLEDGE", "created_event_sequence": 3}
        self.assertFalse(review_validator.is_valid({**base, "reason": "请       好"}))
        self.assertTrue(review_validator.is_valid({**base, "reason": "请解释如何核验。"}))

    def test_error_envelope_has_a_strict_declared_shape(self) -> None:
        response = self.api.handle("GET", "/api/v1/unknown")
        self.assertEqual(404, response.status)
        self.dto("ErrorEnvelope", response.payload)

    def test_response_data_wrappers_are_strict_and_qa_turn_may_omit_proposal(self) -> None:
        health = {"mode": "local-synthetic-demo", "status": "ok"}
        self.dto("HealthData", health)
        validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/HealthData"})
        self.assertFalse(validator.is_valid({**health, "host_path": "C:/private"}))

        qa_api = WorkspaceApi()
        create_body = json.dumps({"schema_version": "skillshift-api/v1", **TASK, "collaboration_mode": "QA_ONLY"}, ensure_ascii=False)
        created = qa_api.handle("POST", "/api/v1/demo/teacher/assignments", create_body, idempotency_key="qa-schema-create")
        assignment = created.payload["data"]
        published = qa_api.handle(
            "POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish",
            json.dumps({"schema_version": "skillshift-api/v1"}), idempotency_key="qa-schema-publish",
            if_match=str(assignment["revision"]),
        )
        workspace = published.payload["data"]["workspace"]
        started = qa_api.handle(
            "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start",
            json.dumps({"schema_version": "skillshift-api/v1"}), idempotency_key="qa-schema-start",
            if_match=str(workspace["revision"]),
        )
        workspace = started.payload["data"]["workspace"]
        turn = qa_api.handle(
            "POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/agent-turns",
            json.dumps({"schema_version": "skillshift-api/v1", "question": "如何核验？"}, ensure_ascii=False),
            idempotency_key="qa-schema-turn", if_match=str(workspace["revision"]),
        )
        self.assertNotIn("proposed_action", turn.payload["data"])
        self.success(turn)
        self.dto("AgentTurnData", turn.payload["data"])

    def test_success_envelope_rejects_undeclared_data_shapes(self) -> None:
        validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/SuccessEnvelope"})
        base = {"schema_version": "skillshift-api/v1", "request_id": f"req-demo-{'a' * 32}"}
        self.assertTrue(validator.is_valid({**base, "data": {"mode": "local-synthetic-demo", "status": "ok"}}))
        for data in ({}, [], {"unexpected": "success"}):
            with self.subTest(data=data):
                self.assertFalse(validator.is_valid({**base, "data": data}))

    def test_latest_submission_data_allows_only_full_submission_or_null(self) -> None:
        validator = Draft202012Validator({"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": "#/$defs/LatestSubmissionData"})
        self.assertTrue(validator.is_valid({"submission": None}))
        submission = {
            "id": "submission-1", "workspace_id": "workspace-1", "assignment_version": 1, "version": 1,
            "artifact_refs": [{"id": "artifact-main-py-v1", "logical_name": "main.py", "media_type": "text/x-python", "source": "FIXED_SYNTHETIC", "integrity_status": "NOT_COMPUTED"}],
            "artifact_snapshots": [{"logical_name": "main.py", "media_type": "text/x-python", "size_bytes": 2, "sha256": "a" * 64, "content": "ok"}],
            "student_explanation": "我检查了结果，逐项核对计算过程，并记录了验证步骤和仍需确认的地方。", "state": "SUBMITTED", "created_event_sequence": 2,
        }
        self.assertTrue(validator.is_valid({"submission": submission}))
        self.assertFalse(validator.is_valid({"submission": {"id": "submission-1"}}))
        self.assertFalse(validator.is_valid({"submission": None, "history": []}))


if __name__ == "__main__":
    unittest.main()
