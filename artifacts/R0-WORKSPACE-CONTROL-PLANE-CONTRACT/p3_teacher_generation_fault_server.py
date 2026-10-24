"""Threaded loopback harness for teacher review failure and race verification.

It seeds one fixed synthetic assignment/submission. Use ``events`` to delay the
first event request and replace it with 503, or ``detail`` to replace the first
teacher Workspace-detail read with 503. All state stays in this process.
"""

from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path
from socketserver import ThreadingMixIn
from threading import Lock
from time import sleep
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.workspace_api import WorkspaceApi  # noqa: E402
from agent_first.workspace_wsgi import WorkspaceWsgiApp  # noqa: E402


HOST = "127.0.0.1"
PORT = 8767
DELAY_SECONDS = 20.0
SYNTHETIC_503 = json.dumps(
    {
        "schema_version": "skillshift-api/v1",
        "request_id": "req-delayed-event-fault",
        "error": {"code": "service_unavailable", "message": "旧合成事件请求延迟失败。", "retryable": True},
    },
    ensure_ascii=False,
    separators=(",", ":"),
).encode("utf-8")
SYNTHETIC_SUBMISSION_409 = json.dumps(
    {
        "schema_version": "skillshift-api/v1",
        "request_id": "req-rejected-submission-retry",
        "error": {"code": "stale_submission", "message": "合成提交版本冲突。", "retryable": False},
    },
    ensure_ascii=False,
    separators=(",", ":"),
).encode("utf-8")


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class DelayedFirstEventFailure:
    def __init__(self, fault: str) -> None:
        self.api = WorkspaceApi()
        self.app = WorkspaceWsgiApp(self.api)
        self.fault = fault
        self.lock = Lock()
        self.event_reads = 0
        self.workspace_reads = 0
        self.history_reads = 0
        self.teacher_detail_reads = 0
        self.multi_queue_reads: dict[str, int] = {}
        self.student_latest_reads = 0
        self.student_remediation_reads = 0
        self.student_catalog_reads = 0
        self.student_switch_workspace_reads = 0
        self.student_agent_turn_reads = 0
        self.teacher_directory_reads = 0
        if fault in {"empty", "student-empty-retry"}:
            pass
        elif fault in {"student-start-lost", "student-start-lost-multi"}:
            self.seed_student_start_lost()
        elif fault == "student-submit-rejected-retry":
            self.seed_student_submit_rejected_retry()
        elif fault in {"student-switch-workspace-fail", "student-switch-catalog-fail"}:
            self.seed_student_switch_workspace_fail()
        elif fault == "student-agent-delay":
            self.seed_student_agent_delay()
        elif fault == "student-proposal-decision":
            self.seed_student_proposal_decision()
        elif fault in {"teacher-history-pagination", "teacher-history-pagination-race"}:
            self.seed_history_pagination()
        elif fault in {"teacher-multi-queue", "teacher-multi-queue-persistent", "teacher-detail-delay", "teacher-queue-retry-delay", "teacher-remediation-retry-delay", "teacher-history-retry-delay", "teacher-event-retry-delay", "teacher-review-write-lost", "teacher-review-directory-fail"}:
            self.seed_multi_task_queue()
        else:
            self.seed_synthetic_review()

    def seed_student_start_lost(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        assignment = call("POST", "/api/v1/demo/teacher/assignments", {
            "title": "学生开始任务回执丢失验证",
            "goal": "只验证开始请求已生效但响应丢失后的未知状态与重读恢复。",
            "student_responsibility": "查看明确的任务状态并判断是否可以继续。",
            "submission_requirement": "本场景不提交任何内容。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "QA_ONLY",
        }, key="student-start-lost-create")
        published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="student-start-lost-publish", revision=assignment["revision"])
        self.student_start_lost_workspace_id = published["workspace"]["id"]
        if self.fault == "student-start-lost-multi":
            second = call("POST", "/api/v1/demo/teacher/assignments", {
                "title": "学生开始请求未知后切换隔离 B",
                "goal": "验证另一任务不会在 A 的开始结果未确认时被接管。",
                "student_responsibility": "确认当前任务状态后再决定是否切换。",
                "submission_requirement": "本场景不提交任何内容。",
                "starter_project_id": "orders-audit-v1",
                "collaboration_mode": "QA_ONLY",
            }, key="student-start-lost-create-b")
            call("POST", f"/api/v1/demo/teacher/assignments/{second['id']}/publish", key="student-start-lost-publish-b", revision=second["revision"])
        self.student_start_lost_writes = 0

    def seed_student_submit_rejected_retry(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        assignment = call("POST", "/api/v1/demo/teacher/assignments", {
            "title": "学生提交明确拒绝恢复验证",
            "goal": "只验证提交请求被明确拒绝后不伪装成回执未知。",
            "student_responsibility": "核验合成提交状态并遵循明确反馈。",
            "submission_requirement": "提交固定合成文本与说明。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "QA_ONLY",
        }, key="student-rejected-submit-create")
        published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="student-rejected-submit-publish", revision=assignment["revision"])
        self.student_rejected_submit_workspace_id = published["workspace"]["id"]
        self.student_rejected_submit_writes = 0
        call("POST", f"/api/v1/demo/student/workspaces/{self.student_rejected_submit_workspace_id}/start", key="student-rejected-submit-start", revision=published["workspace"]["revision"])

    def seed_student_switch_workspace_fail(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        workspaces = []
        for suffix, title in (("a", "学生任务切换失败隔离 A"), ("b", "学生任务切换失败隔离 B")):
            assignment = call("POST", "/api/v1/demo/teacher/assignments", {
                "title": title,
                "goal": "只验证任务选择、状态隔离和失败后重读。",
                "student_responsibility": "分别处理本任务的固定合成工作并保留验证说明。",
                "submission_requirement": "不提交，只验证合成任务状态。",
                "starter_project_id": "orders-audit-v1",
                "collaboration_mode": "QA_ONLY",
            }, key=f"student-switch-create-{suffix}")
            published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key=f"student-switch-publish-{suffix}", revision=assignment["revision"])
            workspaces.append(published["workspace"])
        call("POST", f"/api/v1/demo/student/workspaces/{workspaces[0]['id']}/start", key="student-switch-start-a", revision=workspaces[0]["revision"])
        self.student_switch_fault_workspace_id = workspaces[1]["id"]

    def seed_synthetic_review(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        assignment = call("POST", "/api/v1/demo/teacher/assignments", {
            "title": "教师复核局部失败验证",
            "goal": "只用合成提交验证详情读取失败和事件响应次序。",
            "student_responsibility": "说明核验步骤和不确定处。",
            "submission_requirement": "提交合成结果与核验说明。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "QA_ONLY",
        }, key="fault-harness-create")
        published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="fault-harness-publish", revision=assignment["revision"])
        workspace = published["workspace"]
        started = call("POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="fault-harness-start", revision=workspace["revision"])["workspace"]
        submission_result = call("POST", f"/api/v1/demo/student/workspaces/{started['id']}/submissions", {
            "artifact_refs": ["main.py", "orders.csv"],
            "artifact_contents": {"main.py": "# 固定合成提交；不执行。\n", "orders.csv": "order_id,quantity,unit_price,amount\nO-105,2,89.00,160.00\n"},
            "student_explanation": "我核对了数量、单价与金额关系，并保留业务规则待确认。",
        }, key="fault-harness-submit", revision=started["revision"])
        submission = submission_result["submission"]
        if self.fault in {"teacher-history-retain", "teacher-history-directory-fail"}:
            current_workspace = call("GET", f"/api/v1/demo/teacher/workspaces/{started['id']}")
            call("POST", f"/api/v1/demo/teacher/submissions/{submission['id']}/review-actions", {
                "kind": "REQUEST_EXPLANATION",
                "reason": "请补充这一条固定合成复核历史记录。",
            }, key="fault-harness-history-action", revision=current_workspace["revision"])
        self.student_latest_retry_workspace_id = started["id"]
        if self.fault in {"student-submission", "student-remediation", "student-retention", "student-remediation-fail", "student-agent-delay", "student-latest-retry-delay", "student-remediation-retry-delay"}:
            if self.fault in {"student-remediation", "student-retention", "student-remediation-fail", "student-remediation-retry-delay"}:
                current_workspace = call("GET", f"/api/v1/demo/teacher/workspaces/{started['id']}")
                call("POST", f"/api/v1/demo/teacher/submissions/{submission['id']}/review-actions", {
                    "kind": "REQUEST_REMEDIATION",
                    "reason": "请只在任务 A 补充一项合成验证步骤。",
                }, key="fault-harness-review-a", revision=current_workspace["revision"])
            second = call("POST", "/api/v1/demo/teacher/assignments", {
                "title": "学生延迟读取隔离验证 B",
                "goal": "切换后不显示其他任务的提交状态。",
                "student_responsibility": "只核验本任务状态。",
                "submission_requirement": "本机合成状态检查。",
                "starter_project_id": "orders-audit-v1",
                "collaboration_mode": "QA_ONLY",
            }, key="fault-harness-create-b")
            call("POST", f"/api/v1/demo/teacher/assignments/{second['id']}/publish", key="fault-harness-publish-b", revision=second["revision"])

    def seed_student_agent_delay(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        def create_published(title: str, suffix: str):
            assignment = call("POST", "/api/v1/demo/teacher/assignments", {
                "title": title,
                "goal": "只验证合成 Agent 回执等待期间的任务隔离。",
                "student_responsibility": "由学生明确选择任务并复核回复。",
                "submission_requirement": "不提交、不执行，仅验证协作状态。",
                "starter_project_id": "orders-audit-v1",
                "collaboration_mode": "QA_ONLY",
            }, key=f"agent-delay-create-{suffix}")
            published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key=f"agent-delay-publish-{suffix}", revision=assignment["revision"])
            return assignment, published["workspace"]

        assignment_a, workspace_a = create_published("学生 Agent 延迟回执隔离 A", "a")
        call("POST", f"/api/v1/demo/student/workspaces/{workspace_a['id']}/start", key="agent-delay-start-a", revision=workspace_a["revision"])
        create_published("学生 Agent 延迟回执隔离 B", "b")

    def seed_student_proposal_decision(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        assignment = call("POST", "/api/v1/demo/teacher/assignments", {
            "title": "学生建议决定回执丢失验证 A",
            "goal": "核对固定合成订单并决定是否采纳页面内存建议。",
            "student_responsibility": "明确选择建议决定并复核项目内容。",
            "submission_requirement": "本场景不提交内容，也不运行代码。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "PROPOSE_WITH_STUDENT_CONFIRMATION",
        }, key="proposal-receipt-create-a")
        published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="proposal-receipt-publish-a", revision=assignment["revision"])
        started = call("POST", f"/api/v1/demo/student/workspaces/{published['workspace']['id']}/start", key="proposal-receipt-start-a", revision=published["workspace"]["revision"])
        self.student_proposal_receipt_workspace_id = started["workspace"]["id"]
        second = call("POST", "/api/v1/demo/teacher/assignments", {
            "title": "学生建议决定切换隔离 B",
            "goal": "验证 A 的未确认决定不会转移到另一个任务。",
            "student_responsibility": "只在任务明确选择后继续。",
            "submission_requirement": "本场景不提交内容，也不运行代码。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "QA_ONLY",
        }, key="proposal-receipt-create-b")
        call("POST", f"/api/v1/demo/teacher/assignments/{second['id']}/publish", key="proposal-receipt-publish-b", revision=second["revision"])

    def seed_multi_task_queue(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}")
            return response.payload["data"]

        self.multi_queue_assignment_ids: list[str] = []
        self.multi_queue_workspace_ids: list[str] = []
        self.multi_queue_submission_ids: list[str] = []
        for label in ("A", "B", "C"):
            assignment = call("POST", "/api/v1/demo/teacher/assignments", {
                "title": f"教师多任务队列隔离验证 {label}",
                "goal": "验证单个任务复核队列读取失败不覆盖其他任务。",
                "student_responsibility": "说明合成核验步骤与不确定处。",
                "submission_requirement": "提交固定合成文本快照。",
                "starter_project_id": "orders-audit-v1",
                "collaboration_mode": "QA_ONLY",
            }, key=f"fault-harness-multi-create-{label}")
            published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key=f"fault-harness-multi-publish-{label}", revision=assignment["revision"])
            workspace = published["workspace"]
            started = call("POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key=f"fault-harness-multi-start-{label}", revision=workspace["revision"])["workspace"]
            submitted = call("POST", f"/api/v1/demo/student/workspaces/{started['id']}/submissions", {
                "artifact_refs": ["main.py", "orders.csv"],
                "artifact_contents": {"main.py": f"# 任务 {label} 的固定合成提交；不执行。\n", "orders.csv": "order_id,quantity,unit_price,amount\nO-105,2,89.00,160.00\n"},
                "student_explanation": f"任务 {label}：我已核对固定合成订单记录，并记录仍待确认之处。",
            }, key=f"fault-harness-multi-submit-{label}", revision=started["revision"])
            self.multi_queue_assignment_ids.append(assignment["id"])
            self.multi_queue_workspace_ids.append(started["id"])
            self.multi_queue_submission_ids.append(submitted["submission"]["id"])
        self.multi_queue_fault_assignment_id = self.multi_queue_assignment_ids[0]
        self.multi_queue_fault_workspace_id = self.multi_queue_workspace_ids[0]
        self.teacher_review_write_lost_count = 0
        workspace_c = call("GET", f"/api/v1/demo/teacher/workspaces/{self.multi_queue_workspace_ids[2]}")
        call("POST", f"/api/v1/demo/teacher/submissions/{self.multi_queue_submission_ids[2]}/review-actions", {
            "kind": "REQUEST_REMEDIATION",
            "reason": "任务 C：请补充一项固定合成核验步骤。",
        }, key="fault-harness-multi-review-C", revision=workspace_c["revision"])

    def seed_history_pagination(self) -> None:
        def call(method: str, path: str, payload: dict | None = None, *, key: str | None = None, revision: int | None = None):
            body = json.dumps({"schema_version": "skillshift-api/v1", **(payload or {})}, ensure_ascii=False) if method.upper() in {"POST", "PUT", "PATCH"} else b""
            response = self.api.handle(method, path, body, idempotency_key=key, if_match=str(revision) if revision is not None else None)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"synthetic seed failed: {method} {path} => {response.status}: {response.payload}")
            return response.payload["data"]

        assignment = call("POST", "/api/v1/demo/teacher/assignments", {
            "title": "教师复核历史分页隔离验证",
            "goal": "使用多个固定合成复核动作验证后续页失败不清除已读第一页。",
            "student_responsibility": "逐次补充固定合成核验说明。",
            "submission_requirement": "保留任务关联的说明记录。",
            "starter_project_id": "orders-audit-v1",
            "collaboration_mode": "QA_ONLY",
        }, key="fault-harness-history-page-create")
        published = call("POST", f"/api/v1/demo/teacher/assignments/{assignment['id']}/publish", key="fault-harness-history-page-publish", revision=assignment["revision"])
        workspace = published["workspace"]
        started = call("POST", f"/api/v1/demo/student/workspaces/{workspace['id']}/start", key="fault-harness-history-page-start", revision=workspace["revision"])["workspace"]
        submission = call("POST", f"/api/v1/demo/student/workspaces/{started['id']}/submissions", {
            "artifact_refs": ["main.py"],
            "artifact_contents": {"main.py": "# 固定合成提交；不执行。\n"},
            "student_explanation": "我先核对固定合成文件，记录待确认的业务规则。",
        }, key="fault-harness-history-page-submit-0", revision=started["revision"])["submission"]
        self.history_page_assignment_id = assignment["id"]
        self.history_page_reads = 0
        self.history_page_first_reads = 0
        for index in range(1, 52):
            current_workspace = call("GET", f"/api/v1/demo/teacher/workspaces/{started['id']}")
            call("POST", f"/api/v1/demo/teacher/submissions/{submission['id']}/review-actions", {
                "kind": "REQUEST_EXPLANATION",
                "reason": f"固定合成分页记录 {index}：请说明这一项核验依据。",
            }, key=f"fault-harness-history-action-{index}", revision=current_workspace["revision"])
            if index < 51:
                current_workspace = call("GET", f"/api/v1/demo/teacher/workspaces/{started['id']}")
                submission = call("POST", f"/api/v1/demo/student/workspaces/{started['id']}/submissions", {
                    "artifact_refs": ["main.py"],
                    "artifact_contents": {"main.py": f"# 固定合成第 {index + 1} 次说明；不执行。\n"},
                    "student_explanation": f"第 {index + 1} 次：我重新核对固定合成文件，并说明待确认的业务规则。",
                }, key=f"fault-harness-history-page-submit-{index}", revision=current_workspace["revision"])["submission"]

        if self.fault == "teacher-history-pagination-race":
            other = call("POST", "/api/v1/demo/teacher/assignments", {
                "title": "教师分页竞态隔离验证 B",
                "goal": "仅用于触发教师复核视图新一代读取。",
                "student_responsibility": "只确认当前任务选择。",
                "submission_requirement": "不提交内容。",
                "starter_project_id": "orders-audit-v1",
                "collaboration_mode": "QA_ONLY",
            }, key="fault-harness-history-race-create-B")
            call("POST", f"/api/v1/demo/teacher/assignments/{other['id']}/publish", key="fault-harness-history-race-publish-B", revision=other["revision"])

    def __call__(self, environ: dict, start_response):
        path = environ.get("PATH_INFO", "")
        if self.fault in {"teacher-history-directory-fail", "teacher-review-directory-fail"} and environ.get("REQUEST_METHOD") == "GET" and path == "/api/v1/demo/teacher/assignments":
            with self.lock:
                self.teacher_directory_reads += 1
                should_fail = self.teacher_directory_reads == 3
            if should_fail:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "teacher-review-write-lost" and environ.get("REQUEST_METHOD") == "POST" and path == f"/api/v1/demo/teacher/submissions/{self.multi_queue_submission_ids[0]}/review-actions":
            with self.lock:
                self.teacher_review_write_lost_count += 1
                lose_response = self.teacher_review_write_lost_count == 1
            if lose_response:
                self.app(environ, lambda _status, _headers, _exc_info=None: None)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-submit-rejected-retry" and environ.get("REQUEST_METHOD") == "POST" and path == f"/api/v1/demo/student/workspaces/{self.student_rejected_submit_workspace_id}/submissions":
            with self.lock:
                self.student_rejected_submit_writes += 1
                attempt = self.student_rejected_submit_writes
            if attempt == 1:
                self.app(environ, lambda _status, _headers, _exc_info=None: None)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
            if attempt == 2:
                start_response("409 Conflict", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_SUBMISSION_409))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_SUBMISSION_409]
        if self.fault in {"student-start-lost", "student-start-lost-multi"} and environ.get("REQUEST_METHOD") == "POST" and path == f"/api/v1/demo/student/workspaces/{self.student_start_lost_workspace_id}/start":
            with self.lock:
                self.student_start_lost_writes += 1
                lose_response = self.student_start_lost_writes == 1
            if lose_response:
                self.app(environ, lambda _status, _headers, _exc_info=None: None)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "teacher-detail-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/teacher/workspaces/{self.multi_queue_fault_workspace_id}":
            with self.lock:
                self.teacher_detail_reads += 1
                should_delay = self.teacher_detail_reads == 1
            if should_delay:
                print("FIRST_TEACHER_DETAIL_READ_PENDING", flush=True)
                sleep(5)
        if self.fault == "teacher-queue-retry-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/teacher/assignments/{self.multi_queue_fault_assignment_id}/review-queue":
            with self.lock:
                self.multi_queue_reads[path] = self.multi_queue_reads.get(path, 0) + 1
                queue_read = self.multi_queue_reads[path]
            if queue_read in {1, 2}:
                if queue_read == 2:
                    print("STALE_TEACHER_QUEUE_RETRY_PENDING", flush=True)
                    sleep(5)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "teacher-remediation-retry-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/teacher/workspaces/{self.multi_queue_fault_workspace_id}/remediation":
            with self.lock:
                self.multi_queue_reads[path] = self.multi_queue_reads.get(path, 0) + 1
                remediation_read = self.multi_queue_reads[path]
            if remediation_read in {1, 2}:
                if remediation_read == 2:
                    print("STALE_TEACHER_REMEDIATION_RETRY_PENDING", flush=True)
                    sleep(5)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "teacher-history-retry-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/teacher/assignments/{self.multi_queue_fault_assignment_id}/review-history":
            with self.lock:
                self.multi_queue_reads[path] = self.multi_queue_reads.get(path, 0) + 1
                history_read = self.multi_queue_reads[path]
            if history_read in {1, 2}:
                if history_read == 2:
                    print("STALE_TEACHER_HISTORY_RETRY_PENDING", flush=True)
                    sleep(5)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "teacher-event-retry-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/teacher/workspaces/{self.multi_queue_fault_workspace_id}/events":
            with self.lock:
                event_read = self.multi_queue_reads.get(path, 0) + 1
                self.multi_queue_reads[path] = event_read
            if event_read in {1, 2}:
                if event_read == 2:
                    print("STALE_TEACHER_EVENT_RETRY_PENDING", flush=True)
                    sleep(5)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-agent-delay" and environ.get("REQUEST_METHOD") == "POST" and path.endswith("/agent-turns"):
            with self.lock:
                self.student_agent_turn_reads += 1
                should_delay = self.student_agent_turn_reads == 1
            if should_delay:
                print("FIRST_STUDENT_AGENT_TURN_PENDING", flush=True)
                sleep(5)
        if self.fault == "student-switch-workspace-fail" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/student/workspaces/{self.student_switch_fault_workspace_id}":
            with self.lock:
                self.student_switch_workspace_reads += 1
                should_fail = self.student_switch_workspace_reads == 1
            if should_fail:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault in {"student-catalog-fail", "student-empty-retry", "student-switch-catalog-fail"} and environ.get("REQUEST_METHOD") == "GET" and path == "/api/v1/demo/student/assignments":
            with self.lock:
                self.student_catalog_reads += 1
                should_fail = self.student_catalog_reads == (3 if self.fault == "student-switch-catalog-fail" else 1)
            if should_fail:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault in {"teacher-multi-queue", "teacher-multi-queue-persistent"} and environ.get("REQUEST_METHOD") == "GET":
            failed_paths = {
                f"/api/v1/demo/teacher/assignments/{self.multi_queue_fault_assignment_id}/review-queue",
                f"/api/v1/demo/teacher/workspaces/{self.multi_queue_fault_workspace_id}/remediation",
            }
            if path in failed_paths:
                with self.lock:
                    self.multi_queue_reads[path] = self.multi_queue_reads.get(path, 0) + 1
                    should_fail = self.fault == "teacher-multi-queue-persistent" and path.endswith("/review-queue") or self.multi_queue_reads[path] == 1
                if should_fail:
                    start_response("503 Service Unavailable", [
                        ("Content-Type", "application/json; charset=utf-8"),
                        ("Content-Length", str(len(SYNTHETIC_503))),
                        ("Cache-Control", "no-store"),
                    ])
                    return [SYNTHETIC_503]
        if self.fault == "teacher-history-pagination-race" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/teacher/assignments/{self.history_page_assignment_id}/review-history":
            cursors = parse_qs(environ.get("QUERY_STRING", "")).get("after_sequence", ["0"])
            if cursors == ["0"]:
                with self.lock:
                    self.history_page_first_reads += 1
                    fail_refresh = self.history_page_first_reads in {2, 3}
                if fail_refresh:
                    start_response("503 Service Unavailable", [
                        ("Content-Type", "application/json; charset=utf-8"),
                        ("Content-Length", str(len(SYNTHETIC_503))),
                        ("Cache-Control", "no-store"),
                    ])
                    return [SYNTHETIC_503]
            else:
                with self.lock:
                    self.history_page_reads += 1
                    delay_page = self.history_page_reads == 1
                if delay_page:
                    print("DELAYED_HISTORY_PAGE_REQUEST_PENDING", flush=True)
                    sleep(5)
                    print("DELAYED_HISTORY_PAGE_REQUEST_RELEASED", flush=True)
        if self.fault == "teacher-history-pagination" and environ.get("REQUEST_METHOD") == "GET" and path.endswith("/review-history"):
            cursors = parse_qs(environ.get("QUERY_STRING", "")).get("after_sequence", ["0"])
            if cursors != ["0"]:
                with self.lock:
                    self.history_page_reads += 1
                    should_fail = self.history_page_reads == 1
                if should_fail:
                    start_response("503 Service Unavailable", [
                        ("Content-Type", "application/json; charset=utf-8"),
                        ("Content-Length", str(len(SYNTHETIC_503))),
                        ("Cache-Control", "no-store"),
                    ])
                    return [SYNTHETIC_503]
        if self.fault in {"events", "events-retain"} and environ.get("REQUEST_METHOD") == "GET" and path.endswith("/events"):
            with self.lock:
                self.event_reads += 1
                first_read = self.event_reads == 1
                retained_history_fault = self.fault == "events-retain" and self.event_reads == 2
            if first_read and self.fault == "events":
                print("FIRST_EVENT_READ_PENDING", flush=True)
                sleep(DELAY_SECONDS)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
            if retained_history_fault:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        workspace_path = path.split("/workspaces/", 1)[1] if "/workspaces/" in path else ""
        if self.fault == "detail" and environ.get("REQUEST_METHOD") == "GET" and workspace_path.startswith("workspace-") and "/" not in workspace_path:
            with self.lock:
                self.workspace_reads += 1
                first_read = self.workspace_reads == 1
            if first_read:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-latest-retry-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/student/workspaces/{self.student_latest_retry_workspace_id}/submissions/latest":
            with self.lock:
                self.student_latest_reads += 1
                latest_read = self.student_latest_reads
            if latest_read in {1, 2}:
                if latest_read == 2:
                    print("STALE_STUDENT_LATEST_RETRY_PENDING", flush=True)
                    sleep(15)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-remediation-retry-delay" and environ.get("REQUEST_METHOD") == "GET" and path == f"/api/v1/demo/student/workspaces/{self.student_latest_retry_workspace_id}/remediation":
            with self.lock:
                self.student_remediation_reads += 1
                remediation_read = self.student_remediation_reads
            if remediation_read in {1, 2}:
                if remediation_read == 2:
                    print("STALE_STUDENT_REMEDIATION_RETRY_PENDING", flush=True)
                    sleep(5)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-retention" and environ.get("REQUEST_METHOD") == "GET" and path.endswith("/submissions/latest"):
            with self.lock:
                self.student_latest_reads += 1
                should_fail = self.student_latest_reads == 2
            if should_fail:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-remediation-fail" and environ.get("REQUEST_METHOD") == "GET" and path.endswith("/remediation"):
            with self.lock:
                self.student_remediation_reads += 1
                should_fail = self.student_remediation_reads == 1
            if should_fail:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        if self.fault == "student-submission" and environ.get("REQUEST_METHOD") == "GET" and path.endswith("/submissions/latest"):
            with self.lock:
                self.workspace_reads += 1
                first_read = self.workspace_reads == 1
            if first_read:
                print("FIRST_STUDENT_SUBMISSION_READ_PENDING", flush=True)
                sleep(DELAY_SECONDS)
        if self.fault == "student-remediation" and environ.get("REQUEST_METHOD") == "GET" and path.endswith("/remediation"):
            with self.lock:
                self.workspace_reads += 1
                first_read = self.workspace_reads == 1
            if first_read:
                print("FIRST_STUDENT_REMEDIATION_READ_PENDING", flush=True)
                sleep(DELAY_SECONDS)
        if self.fault in {"teacher-history", "teacher-history-retain"} and environ.get("REQUEST_METHOD") == "GET" and "/review-history" in path:
            with self.lock:
                self.history_reads += 1
                first_read = self.history_reads == 1
                retained_history_fault = self.fault == "teacher-history-retain" and self.history_reads == 2
            if first_read and self.fault == "teacher-history":
                print("FIRST_TEACHER_HISTORY_READ_PENDING", flush=True)
                sleep(DELAY_SECONDS)
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
            if retained_history_fault:
                start_response("503 Service Unavailable", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(SYNTHETIC_503))),
                    ("Cache-Control", "no-store"),
                ])
                return [SYNTHETIC_503]
        return self.app(environ, start_response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fault", choices=("empty", "events", "events-retain", "detail", "student-submission", "student-remediation", "student-retention", "student-remediation-fail", "student-latest-retry-delay", "student-remediation-retry-delay", "student-proposal-decision", "student-catalog-fail", "student-empty-retry", "student-start-lost", "student-start-lost-multi", "student-submit-rejected-retry", "student-switch-workspace-fail", "student-switch-catalog-fail", "student-agent-delay", "teacher-history", "teacher-history-retain", "teacher-history-directory-fail", "teacher-review-directory-fail", "teacher-multi-queue", "teacher-multi-queue-persistent", "teacher-detail-delay", "teacher-queue-retry-delay", "teacher-remediation-retry-delay", "teacher-history-retry-delay", "teacher-event-retry-delay", "teacher-review-write-lost", "teacher-history-pagination", "teacher-history-pagination-race"))
    fault = parser.parse_args().fault
    with make_server(HOST, PORT, DelayedFirstEventFailure(fault), server_class=ThreadingWSGIServer, handler_class=WSGIRequestHandler) as server:
        print(f"Synthetic local browser check: http://{HOST}:{PORT}/demo/teacher/")
        seeded_count = 0 if fault in {"empty", "student-empty-retry"} else (3 if fault in {"teacher-multi-queue", "teacher-detail-delay", "teacher-queue-retry-delay", "teacher-remediation-retry-delay", "teacher-history-retry-delay", "teacher-event-retry-delay", "teacher-review-write-lost", "teacher-review-directory-fail"} else (2 if fault in {"student-agent-delay", "student-switch-workspace-fail", "student-switch-catalog-fail", "student-start-lost-multi", "student-latest-retry-delay", "student-remediation-retry-delay", "student-proposal-decision", "teacher-history-pagination-race"} else 1))
        seeded_actions = 0 if fault in {"empty", "student-empty-retry", "student-switch-workspace-fail", "student-switch-catalog-fail"} else (51 if fault in {"teacher-history-pagination", "teacher-history-pagination-race"} else 1)
        print(f"Loopback only. {seeded_count} synthetic assignment(s), {seeded_actions} synthetic review action(s); mode={fault}; delayed read={DELAY_SECONDS}s.", flush=True)
        server.serve_forever()
