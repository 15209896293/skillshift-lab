"""Loopback-only, synthetic web/API adapter for the R0 Gate A workflow.

This module is deliberately not a production web service.  It has no identity
provider, persistence, credential resolver, model runtime, network client, or
student-computer capability.  Its only purpose is to make the deterministic
workflow visible through a small local browser demonstration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from http import HTTPStatus
import json
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from .domain import EducationWorkflow, ReviewKind, WorkflowError, build_synthetic_template
from .scripted_guidance import ScriptedGuidanceAdapter


TEACHER_DEMO_ID = "teacher-demo"
STUDENT_DEMO_ID = "student-demo"
MAX_REQUEST_BYTES = 16_384
STATIC_ROOT = Path(__file__).resolve().parents[1] / "web"


@dataclass(frozen=True)
class ApiResponse:
    status: int
    payload: dict[str, Any] | str
    content_type: str = "application/json; charset=utf-8"


class LocalSyntheticWorkflowStore:
    """An intentionally ephemeral store for one or more frozen demo workflows."""

    def __init__(self) -> None:
        self._workflows: dict[str, EducationWorkflow] = {}
        self._next_id = 1

    def create(
        self,
        *,
        actor_id: str,
        title: str,
        goal: str,
        student_responsibility: str,
        submission_requirement: str,
    ) -> tuple[str, EducationWorkflow]:
        if actor_id != TEACHER_DEMO_ID:
            raise WorkflowError("only the fixed synthetic teacher can create an assignment")
        assignment_id = f"assignment-{self._next_id}"
        template = build_synthetic_template(
            task_id=f"synthetic-teacher-task-{self._next_id}-v1",
            title=title,
            goal=goal,
            student_responsibility=student_responsibility,
            submission_requirement=submission_requirement,
        )
        workflow = EducationWorkflow(
            teacher_id=TEACHER_DEMO_ID,
            student_id=STUDENT_DEMO_ID,
            template=template,
            adapter=ScriptedGuidanceAdapter(),
        )
        workflow.create_and_assign(actor_id=actor_id)
        self._workflows[assignment_id] = workflow
        self._next_id += 1
        return assignment_id, workflow

    def get(self, assignment_id: str) -> EducationWorkflow:
        try:
            return self._workflows[assignment_id]
        except KeyError as error:
            raise LookupError("synthetic assignment was not found") from error

    def list(self) -> list[tuple[str, EducationWorkflow]]:
        return list(self._workflows.items())


class LocalWebApplication:
    """Small JSON router plus a fixed static asset allowlist."""

    def __init__(self, store: LocalSyntheticWorkflowStore | None = None) -> None:
        self.store = store or LocalSyntheticWorkflowStore()

    def handle(self, method: str, path: str, body: bytes | str = b"") -> ApiResponse:
        parsed_path = urlsplit(path).path
        normalized_method = method.upper()
        try:
            if parsed_path.startswith("/api/"):
                return self._handle_api(normalized_method, parsed_path, body)
            if normalized_method != "GET":
                return self._error(HTTPStatus.METHOD_NOT_ALLOWED, "method_not_allowed", "only GET serves static assets")
            return self._static_asset(parsed_path)
        except LookupError as error:
            return self._error(HTTPStatus.NOT_FOUND, "not_found", str(error))
        except WorkflowError as error:
            return self._error(HTTPStatus.CONFLICT, "workflow_conflict", str(error))
        except ValueError as error:
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_request", str(error))

    def _handle_api(self, method: str, path: str, body: bytes | str) -> ApiResponse:
        if method == "GET" and path == "/api/health":
            return self._json(HTTPStatus.OK, {"status": "ok", "mode": "local-synthetic-demo"})
        if method == "GET" and path == "/api/assignments":
            return self._json(
                HTTPStatus.OK,
                {"assignments": [self._assignment_view(assignment_id, workflow) for assignment_id, workflow in self.store.list()]},
            )
        if method == "POST" and path == "/api/assignments":
            payload = self._json_body(body)
            actor_id = self._actor(payload)
            if actor_id != TEACHER_DEMO_ID:
                raise WorkflowError("only the fixed synthetic teacher can create an assignment")
            allowed_fields = {
                "actor_id",
                "title",
                "goal",
                "student_responsibility",
                "submission_requirement",
            }
            if set(payload) != allowed_fields:
                raise ValueError("task creation requires only the declared synthetic task fields")
            assignment_id, workflow = self.store.create(
                actor_id=actor_id,
                title=self._text(payload, "title"),
                goal=self._text(payload, "goal"),
                student_responsibility=self._text(payload, "student_responsibility"),
                submission_requirement=self._text(payload, "submission_requirement"),
            )
            return self._json(HTTPStatus.CREATED, self._assignment_view(assignment_id, workflow))

        parts = [part for part in path.split("/") if part]
        if len(parts) < 3 or parts[:2] != ["api", "assignments"]:
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "route was not found")
        assignment_id = parts[2]
        workflow = self.store.get(assignment_id)
        if len(parts) == 3 and method == "GET":
            return self._json(HTTPStatus.OK, self._assignment_view(assignment_id, workflow))
        if len(parts) == 4 and parts[3] == "manifest" and method == "GET":
            return self._json(HTTPStatus.OK, workflow.manifest())

        payload = self._json_body(body)
        actor_id = self._actor(payload)
        if len(parts) == 4 and parts[3] == "start" and method == "POST":
            workflow.start(actor_id=actor_id)
            return self._json(HTTPStatus.OK, self._assignment_view(assignment_id, workflow))
        if len(parts) == 4 and parts[3] == "guidance" and method == "POST":
            guidance = workflow.ask_guidance(actor_id=actor_id, question=self._text(payload, "question"))
            return self._json(
                HTTPStatus.OK,
                {
                    "text": guidance.text,
                    "adapter_version": guidance.adapter_version,
                    "source": guidance.source,
                    "availability": guidance.availability,
                },
            )
        if len(parts) == 4 and parts[3] == "submissions" and method == "POST":
            response = workflow.submit(
                actor_id=actor_id,
                response_text=self._text(payload, "response_text"),
                responsibility_kind=self._text(payload, "responsibility_kind"),
            )
            return self._json(HTTPStatus.CREATED, {"response": asdict(response), "assignment": self._assignment_view(assignment_id, workflow)})
        if len(parts) == 4 and parts[3] == "reviews" and method == "POST":
            try:
                kind = ReviewKind(self._text(payload, "kind"))
            except ValueError as error:
                raise ValueError("unsupported review kind") from error
            review = workflow.review(actor_id=actor_id, kind=kind, reason=self._text(payload, "reason"))
            return self._json(HTTPStatus.CREATED, {"review": {**asdict(review), "kind": review.kind.value}, "assignment": self._assignment_view(assignment_id, workflow)})
        return self._error(HTTPStatus.NOT_FOUND, "not_found", "route was not found")

    @staticmethod
    def _actor(payload: dict[str, Any]) -> str:
        return LocalWebApplication._text(payload, "actor_id")

    @staticmethod
    def _text(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _json_body(body: bytes | str) -> dict[str, Any]:
        raw = body.encode("utf-8") if isinstance(body, str) else body
        if len(raw) > MAX_REQUEST_BYTES:
            raise ValueError("request body exceeds the synthetic demo limit")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body must be valid UTF-8 JSON") from error
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    @staticmethod
    def _assignment_view(assignment_id: str, workflow: EducationWorkflow) -> dict[str, Any]:
        latest_response = asdict(workflow.responses[-1]) if workflow.responses else None
        latest_review = workflow.review_actions[-1] if workflow.review_actions else None
        return {
            "assignment_id": assignment_id,
            "task": asdict(workflow.template),
            "status": workflow.status.value,
            "student_response": latest_response,
            "teacher_feedback": (
                {"kind": latest_review.kind.value, "reason": latest_review.reason}
                if latest_review
                else None
            ),
            "event_count": len(workflow.events),
            "demo_notice": "仅限本机合成演示；重启服务后任务会清空。",
        }

    @staticmethod
    def _json(status: HTTPStatus, payload: dict[str, Any]) -> ApiResponse:
        return ApiResponse(status=int(status), payload=payload)

    @staticmethod
    def _error(status: HTTPStatus, code: str, message: str) -> ApiResponse:
        return ApiResponse(status=int(status), payload={"error": {"code": code, "message": message}})

    @staticmethod
    def _static_asset(path: str) -> ApiResponse:
        if path == "/favicon.ico":
            return ApiResponse(status=int(HTTPStatus.NO_CONTENT), payload="", content_type="image/x-icon")
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "application/javascript; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
        }
        try:
            filename, content_type = assets[path]
        except KeyError:
            return LocalWebApplication._error(HTTPStatus.NOT_FOUND, "not_found", "static asset was not found")
        try:
            return ApiResponse(status=int(HTTPStatus.OK), payload=(STATIC_ROOT / filename).read_text(encoding="utf-8"), content_type=content_type)
        except OSError:
            return LocalWebApplication._error(HTTPStatus.INTERNAL_SERVER_ERROR, "asset_unavailable", "local demo asset is unavailable")

    def wsgi(self, environ: dict[str, Any], start_response: Callable[[str, list[tuple[str, str]]], Any]) -> list[bytes]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            content_length = 0
        if content_length > MAX_REQUEST_BYTES:
            response = self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "payload_too_large", "request body exceeds the synthetic demo limit")
        else:
            body = environ.get("wsgi.input").read(content_length) if content_length else b""
            response = self.handle(environ.get("REQUEST_METHOD", "GET"), environ.get("PATH_INFO", "/"), body)
        encoded = (
            json.dumps(response.payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            if isinstance(response.payload, dict)
            else response.payload.encode("utf-8")
        )
        status = f"{response.status} {HTTPStatus(response.status).phrase}"
        start_response(status, [("Content-Type", response.content_type), ("Content-Length", str(len(encoded))), ("Cache-Control", "no-store")])
        return [encoded]
