from __future__ import annotations

from io import BytesIO
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.local_web import LocalWebApplication, STUDENT_DEMO_ID, TEACHER_DEMO_ID


def post(app: LocalWebApplication, path: str, payload: dict[str, str]):
    return app.handle("POST", path, json.dumps(payload, ensure_ascii=False))


DEFAULT_TASK = {
    "title": "识别并解释一条不一致的数据记录",
    "goal": "识别给定表格中的一条不一致记录，并说明你如何检查判断。",
    "student_responsibility": "提交判断、一个可检查的验证步骤和不确定之处。",
    "submission_requirement": "一段任务关联的验证或解释文本。",
}


class LocalWebPrototypeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = LocalWebApplication()

    def create_assignment(self) -> str:
        response = post(self.app, "/api/assignments", {"actor_id": TEACHER_DEMO_ID, **DEFAULT_TASK})
        self.assertEqual(201, response.status)
        return response.payload["assignment_id"]

    def start_assignment(self, assignment_id: str) -> None:
        response = post(self.app, f"/api/assignments/{assignment_id}/start", {"actor_id": STUDENT_DEMO_ID})
        self.assertEqual(200, response.status)
        self.assertEqual("IN_PROGRESS", response.payload["status"])

    def submit(self, assignment_id: str, *, kind: str = "verification"):
        return post(
            self.app,
            f"/api/assignments/{assignment_id}/submissions",
            {
                "actor_id": STUDENT_DEMO_ID,
                "responsibility_kind": kind,
                "response_text": "我比对了两个字段和任务规则，验证这一条记录存在不一致，并说明仍需核对的材料位置。",
            },
        )

    def test_full_teacher_student_explanation_and_resubmission_path(self) -> None:
        assignment_id = self.create_assignment()
        self.start_assignment(assignment_id)
        guidance = post(
            self.app,
            f"/api/assignments/{assignment_id}/guidance",
            {"actor_id": STUDENT_DEMO_ID, "question": "我应该先检查什么？"},
        )
        self.assertEqual(200, guidance.status)
        self.assertEqual("scripted-guidance/v1", guidance.payload["adapter_version"])
        first = self.submit(assignment_id)
        self.assertEqual("REVIEW_REQUIRED", first.payload["assignment"]["status"])
        feedback = post(
            self.app,
            f"/api/assignments/{assignment_id}/reviews",
            {"actor_id": TEACHER_DEMO_ID, "kind": "REQUEST_EXPLANATION", "reason": "请补充你判断所依据的任务规则。"},
        )
        self.assertEqual("FEEDBACK_REQUIRED", feedback.payload["assignment"]["status"])
        second = self.submit(assignment_id, kind="remediation")
        self.assertEqual("RESUBMITTED", second.payload["assignment"]["status"])
        closed = post(
            self.app,
            f"/api/assignments/{assignment_id}/reviews",
            {"actor_id": TEACHER_DEMO_ID, "kind": "ACKNOWLEDGE", "reason": "补充后的说明和验证步骤可以复核。"},
        )
        self.assertEqual("CLOSED", closed.payload["assignment"]["status"])
        manifest = self.app.handle("GET", f"/api/assignments/{assignment_id}/manifest")
        self.assertEqual(200, manifest.status)
        self.assertEqual("CLOSED", manifest.payload["status"])
        self.assertEqual(2, manifest.payload["student_response"]["revision"])

    def test_role_and_state_errors_are_visible(self) -> None:
        assignment_id = self.create_assignment()
        wrong_actor = post(self.app, f"/api/assignments/{assignment_id}/start", {"actor_id": TEACHER_DEMO_ID})
        self.assertEqual(409, wrong_actor.status)
        no_manifest = self.app.handle("GET", f"/api/assignments/{assignment_id}/manifest")
        self.assertEqual(409, no_manifest.status)
        malformed = self.app.handle("POST", f"/api/assignments/{assignment_id}/start", "not-json")
        self.assertEqual(400, malformed.status)
        missing = self.app.handle("GET", "/api/assignments/assignment-404")
        self.assertEqual(404, missing.status)

    def test_teacher_cannot_create_as_student_and_invalid_review_is_rejected(self) -> None:
        denied = post(self.app, "/api/assignments", {"actor_id": STUDENT_DEMO_ID})
        self.assertEqual(409, denied.status)
        assignment_id = self.create_assignment()
        self.start_assignment(assignment_id)
        self.submit(assignment_id)
        invalid = post(
            self.app,
            f"/api/assignments/{assignment_id}/reviews",
            {"actor_id": TEACHER_DEMO_ID, "kind": "AUTOMATIC_GRADE", "reason": "这个动作不在合成演示范围内。"},
        )
        self.assertEqual(400, invalid.status)

    def test_static_assets_are_allowlisted_and_wsgi_serves_index_without_network(self) -> None:
        index = self.app.handle("GET", "/")
        self.assertEqual(200, index.status)
        self.assertIn("合成演示", index.payload)
        self.assertIn("刷新会重新载入最近任务", index.payload)
        self.assertNotIn("http://", index.payload)
        self.assertNotIn("https://", index.payload)
        self.assertEqual(204, self.app.handle("GET", "/favicon.ico").status)
        missing = self.app.handle("GET", "/../../private.txt")
        self.assertEqual(404, missing.status)
        captured: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            captured["status"] = status
            captured["headers"] = headers

        body = self.app.wsgi(
            {"REQUEST_METHOD": "GET", "PATH_INFO": "/", "CONTENT_LENGTH": "0", "wsgi.input": BytesIO()},
            start_response,
        )
        self.assertTrue(str(captured["status"]).startswith("200"))
        self.assertIn(b"SkillShift", b"".join(body))

    def test_assignment_list_supports_refresh_recovery_with_latest_ephemeral_task(self) -> None:
        first_id = self.create_assignment()
        self.start_assignment(first_id)
        second_id = self.create_assignment()
        response = self.app.handle("GET", "/api/assignments")
        self.assertEqual(200, response.status)
        self.assertEqual([first_id, second_id], [item["assignment_id"] for item in response.payload["assignments"]])
        self.assertEqual("ASSIGNED", response.payload["assignments"][-1]["status"])

    def test_teacher_authored_fields_round_trip_into_student_view_and_manifest(self) -> None:
        authored = {
            "title": "检查合成表格中的日期冲突",
            "goal": "找出一处日期冲突，并写出可以复核的比较步骤。",
            "student_responsibility": "说明判断依据并指出尚未确认的地方。",
            "submission_requirement": "提交结论、比较步骤和一个不确定点。",
        }
        response = post(self.app, "/api/assignments", {"actor_id": TEACHER_DEMO_ID, **authored})
        self.assertEqual(201, response.status)
        assignment_id = response.payload["assignment_id"]
        task = response.payload["task"]
        for field, value in authored.items():
            self.assertEqual(value, task[field])
        self.assertEqual("引导需确认", task["collaboration_mode"])
        self.assertTrue(task["task_id"].startswith("synthetic-teacher-task-"))

        student_view = self.app.handle("GET", f"/api/assignments/{assignment_id}")
        self.assertEqual(task, student_view.payload["task"])
        self.start_assignment(assignment_id)
        self.submit(assignment_id)
        manifest = self.app.handle("GET", f"/api/assignments/{assignment_id}/manifest")
        self.assertEqual(task["task_id"], manifest.payload["task"]["id"])
        self.assertEqual(task["version"], manifest.payload["task"]["version"])

    def test_task_creation_refuses_missing_oversized_or_undeclared_fields(self) -> None:
        missing = post(self.app, "/api/assignments", {"actor_id": TEACHER_DEMO_ID, **{k: v for k, v in DEFAULT_TASK.items() if k != "goal"}})
        self.assertEqual(400, missing.status)

        oversized_title = {**DEFAULT_TASK, "title": "测" * 43}
        oversized = post(self.app, "/api/assignments", {"actor_id": TEACHER_DEMO_ID, **oversized_title})
        self.assertEqual(400, oversized.status)
        self.assertNotIn("测", oversized.payload["error"]["message"])

        undeclared = post(
            self.app,
            "/api/assignments",
            {"actor_id": TEACHER_DEMO_ID, **DEFAULT_TASK, "student_name": "synthetic-only"},
        )
        self.assertEqual(400, undeclared.status)

    def test_frontend_uses_only_relative_api_paths_and_escapes_user_text(self) -> None:
        frontend = (ROOT / "apps" / "agent-first" / "web" / "app.js").read_text(encoding="utf-8")
        server = (ROOT / "apps" / "agent-first" / "agent_first" / "local_web.py").read_text(encoding="utf-8")
        launcher = (ROOT / "apps" / "agent-first" / "run_local_web.py").read_text(encoding="utf-8")
        self.assertIn("function escapeHtml", frontend)
        self.assertIn('document.querySelector("#task-title").value', frontend)
        self.assertIn('document.querySelector("#task-submission").value', frontend)
        self.assertIn('request("/api/assignments")', frontend)
        self.assertIn("restoreLatestAssignment();", frontend)
        self.assertNotIn("http://", frontend)
        self.assertNotIn("https://", frontend)
        self.assertNotIn("urllib.request", server)
        self.assertIn('LOOPBACK_HOST = "127.0.0.1"', launcher)
        for prohibited in ("作弊", "外部 AI", "能力结论", "自动评分"):
            self.assertNotIn(prohibited, frontend)


if __name__ == "__main__":
    unittest.main()
