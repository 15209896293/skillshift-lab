"""Synthetic-only API contract for separate teacher/student project workspaces.

This in-memory application is a test adapter, not authentication, durable
persistence, model access, host filesystem access, code execution, or a deployable
service. It accepts only bounded allowlisted synthetic text snapshots at submit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from copy import deepcopy
from contextvars import ContextVar
from hashlib import sha256
from http import HTTPStatus
import json
import re
from threading import RLock
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from .domain import build_synthetic_template
from .scripted_guidance import ScriptedGuidanceAdapter


API_VERSION = "skillshift-api/v1"
MAX_BODY_BYTES = 16_384
MAX_ARTIFACT_BYTES = 8_192
MAX_SUBMISSION_ARTIFACT_BYTES = 12_288
MAX_EVENT_PAGE_SIZE = 50
MAX_RETAINED_EVENTS_PER_WORKSPACE = 256
DEMO_PROJECT_ID = "orders-audit-v1"
DEMO_ACTORS = {"teacher": "teacher-demo", "student": "student-demo"}
ALLOWED_ARTIFACTS = {
    "main.py": "text/x-python",
    "orders.csv": "text/csv",
    "README.md": "text/markdown",
}
REVIEW_KINDS = {
    "ACKNOWLEDGE",
    "REQUEST_EXPLANATION",
    "REQUEST_EVIDENCE",
    "REQUEST_REMEDIATION",
    "ENVIRONMENT_ISSUE",
}
_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_REQUEST_ID: ContextVar[str] = ContextVar("skillshift_demo_request_id", default="req-demo")


@dataclass(frozen=True)
class ApiResponse:
    status: int
    payload: dict[str, Any]


@dataclass
class Workspace:
    workspace_id: str
    assignment_id: str
    student_actor_ref: str = DEMO_ACTORS["student"]
    state: str = "ASSIGNED"
    revision: int = 1
    submissions: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    remediations: list[dict[str, Any]] = field(default_factory=list)
    proposals: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    events_pruned: bool = False


@dataclass
class Assignment:
    assignment_id: str
    task: dict[str, Any]
    state: str = "DRAFT"
    revision: int = 1
    workspace: Workspace | None = None


class SyntheticWorkspaceStore:
    """Explicitly ephemeral fixed-demo state for unit and local acceptance tests."""

    def __init__(self) -> None:
        self.assignments: dict[str, Assignment] = {}
        self._next_assignment = 1
        self._next_workspace = 1
        self._next_event = 1
        self._next_submission = 1
        self._next_review = 1
        self._next_remediation = 1

    def event(self, workspace: Workspace, role: str, event_type: str, resource_ref: str) -> dict[str, Any]:
        event = {
            "event_id": f"event-{self._next_event}",
            "sequence": self._next_event,
            "schema_version": "evidence-event/v1",
            "workspace_id": workspace.workspace_id,
            "actor_role": role,
            "event_type": event_type,
            "resource_ref": resource_ref,
            "request_id": _REQUEST_ID.get(),
            "occurred_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        self._next_event += 1
        workspace.events.append(event)
        if len(workspace.events) > MAX_RETAINED_EVENTS_PER_WORKSPACE:
            del workspace.events[0]
            workspace.events_pruned = True
        workspace.revision += 1
        return event


class WorkspaceApi:
    """A bounded JSON router. Demo role is derived from a fixed route prefix.

    `/demo/teacher` and `/demo/student` are intentionally insecure role fixtures
    for tests only. A deployable adapter must replace them with server-side auth.
    """

    def __init__(self, store: SyntheticWorkspaceStore | None = None) -> None:
        self.store = store or SyntheticWorkspaceStore()
        self._idempotent: dict[tuple[str, str], tuple[str, ApiResponse]] = {}
        self._guidance = ScriptedGuidanceAdapter()
        self._request_lock = RLock()

    def handle(
        self,
        method: str,
        path: str,
        body: bytes | str = b"",
        *,
        idempotency_key: str | None = None,
        if_match: str | None = None,
    ) -> ApiResponse:
        token = _REQUEST_ID.set(f"req-demo-{uuid4().hex}")
        try:
            # This process-memory adapter is called by a threaded WSGI server.
            # Serialize each request so revision checks, active-task transitions,
            # and idempotency lookup/mutation/replay are atomic within this instance.
            with self._request_lock:
                return self._handle_request(
                    method, path, body,
                    idempotency_key=idempotency_key,
                    if_match=if_match,
                )
        finally:
            _REQUEST_ID.reset(token)

    def _handle_request(
        self,
        method: str,
        path: str,
        body: bytes | str = b"",
        *,
        idempotency_key: str | None = None,
        if_match: str | None = None,
    ) -> ApiResponse:
        parsed = urlsplit(path)
        parts = [part for part in parsed.path.split("/") if part]
        if parts == ["api", "v1", "health"] and method.upper() == "GET":
            return self._success(HTTPStatus.OK, {"mode": "local-synthetic-demo", "status": "ok"})
        if len(parts) < 4 or parts[:2] != ["api", "v1"] or parts[2] != "demo":
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "route was not found")
        role = parts[3]
        if role not in DEMO_ACTORS:
            return self._error(HTTPStatus.NOT_FOUND, "not_found", "route was not found")
        route = parts[4:]
        try:
            payload = self._body(body) if method.upper() in {"POST", "PUT", "PATCH"} else {}
            if method.upper() in {"POST", "PUT", "PATCH"}:
                if payload.pop("schema_version", None) != API_VERSION:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_schema_version", "request must declare the supported schema_version")
            return self._dispatch(
                method.upper(), role, route, payload, parse_qs(parsed.query, keep_blank_values=True),
                idempotency_key=idempotency_key, if_match=if_match,
            )
        except ApiFault as fault:
            return self._error(fault.status, fault.code, fault.message)
        except (ValueError, TypeError):
            return self._error(HTTPStatus.BAD_REQUEST, "invalid_request", "request fields do not match the declared schema")

    def _dispatch(
        self,
        method: str,
        role: str,
        route: list[str],
        payload: dict[str, Any],
        query: dict[str, list[str]],
        *,
        idempotency_key: str | None,
        if_match: str | None,
    ) -> ApiResponse:
        if route == ["assignments"] and method == "POST" and role == "teacher":
            allowed = {"title", "goal", "student_responsibility", "submission_requirement", "starter_project_id", "collaboration_mode"}
            self._fields(payload, allowed)
            clean = {
                "title": self._text(payload, "title", 128),
                "goal": self._text(payload, "goal", 4096),
                "student_responsibility": self._text(payload, "student_responsibility", 2048),
                "submission_requirement": self._text(payload, "submission_requirement", 2048),
            }
            if payload["starter_project_id"] != DEMO_PROJECT_ID:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_project", "only the fixed synthetic project is available")
            if payload["collaboration_mode"] not in {"QA_ONLY", "PROPOSE_WITH_STUDENT_CONFIRMATION"}:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_mode", "unsupported collaboration mode")
            clean.update({
                "starter_project_id": DEMO_PROJECT_ID,
                "collaboration_mode": payload["collaboration_mode"],
                "submission_requirements": [clean.pop("submission_requirement")],
                "execution_enabled": False,
            })

            def create() -> ApiResponse:
                task_id = f"synthetic-task-{self.store._next_assignment}-v1"
                template = build_synthetic_template(
                    task_id=task_id,
                    title=clean["title"],
                    goal=clean["goal"],
                    student_responsibility=clean["student_responsibility"],
                    submission_requirement=clean["submission_requirements"][0],
                )
                assignment_id = f"assignment-{self.store._next_assignment}"
                self.store._next_assignment += 1
                task_data = asdict(template)
                task_data.pop("submission_requirement", None)
                assignment = Assignment(assignment_id, {**task_data, **clean, "id": assignment_id, "version": 1})
                self.store.assignments[assignment_id] = assignment
                return self._success(HTTPStatus.CREATED, self._assignment_view(assignment))

            return self._mutate(role, idempotency_key, payload, "create-assignment", create)

        if route == ["assignments"] and method == "GET":
            if role == "teacher":
                assignments = [self._assignment_view(item) for item in self.store.assignments.values()]
            else:
                assignments = [self._assignment_view(item) for item in self.store.assignments.values() if item.state == "PUBLISHED"]
            return self._success(HTTPStatus.OK, {"assignments": assignments})

        if len(route) >= 2 and route[0] == "assignments":
            if route[2:] == ["review-history"] and method == "GET":
                # Keep this read surface teacher-demo only and hide assignment
                # existence/state behind one consistent not-found response.
                if role != "teacher":
                    raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
                assignment = self.store.assignments.get(route[1])
                if assignment is None or assignment.state != "PUBLISHED" or assignment.workspace is None:
                    raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
                cursors = query.get("after_sequence", ["0"])
                if len(cursors) != 1:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "review-history cursor must be a single integer")
                try:
                    after = int(cursors[0])
                except ValueError as error:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "review-history cursor must be a single integer") from error
                limits = query.get("limit", [str(MAX_EVENT_PAGE_SIZE)])
                if len(limits) != 1:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "review-history page limit must be a single integer")
                try:
                    limit = int(limits[0])
                except ValueError as error:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_page_limit", "review-history page limit must be an integer") from error
                if after < 0:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "review-history cursor must not be negative")
                if not 1 <= limit <= MAX_EVENT_PAGE_SIZE:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_page_limit", f"page limit must be between 1 and {MAX_EVENT_PAGE_SIZE}")

                workspace = assignment.workspace
                available = sorted(
                    (action for action in workspace.reviews if action["created_event_sequence"] > after),
                    key=lambda action: action["created_event_sequence"],
                )
                page = available[:limit]
                review_actions = [
                    {
                        "id": action["id"],
                        "submission_id": action["submission_id"],
                        "submission_version": action["submission_version"],
                        "kind": action["kind"],
                        "reason": action["reason"],
                        "created_event_sequence": action["created_event_sequence"],
                    }
                    for action in page
                ]
                next_sequence = review_actions[-1]["created_event_sequence"] if review_actions else after
                return self._success(HTTPStatus.OK, {
                    "review_actions": review_actions,
                    "next_sequence": next_sequence,
                    "has_more": len(available) > len(review_actions),
                })

            assignment = self._assignment(route[1])
            if len(route) == 2 and method == "GET":
                if role == "student" and assignment.state != "PUBLISHED":
                    raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
                return self._success(HTTPStatus.OK, self._assignment_view(assignment))
            if route[2:] == ["publish"] and method == "POST" and role == "teacher":
                self._empty_fields(payload)

                def publish() -> ApiResponse:
                    self._match_revision(if_match, assignment.revision)
                    if assignment.state != "DRAFT":
                        raise ApiFault(HTTPStatus.CONFLICT, "state_conflict", "only a draft assignment can be published")
                    assignment.state = "PUBLISHED"
                    assignment.revision += 1
                    workspace = Workspace(f"workspace-{self.store._next_workspace}", assignment.assignment_id)
                    self.store._next_workspace += 1
                    assignment.workspace = workspace
                    event = self.store.event(workspace, role, "assignment.published", assignment.assignment_id)
                    return self._success(HTTPStatus.OK, {"assignment": self._assignment_view(assignment), "workspace": self._workspace_view(workspace), "event": event}, revision=assignment.revision)

                return self._mutate(role, idempotency_key, payload, f"publish:{assignment.assignment_id}", publish, if_match=if_match)

            if route[2:] == ["review-queue"] and method == "GET" and role == "teacher":
                workspace = assignment.workspace
                submissions = workspace.submissions if workspace else []
                return self._success(HTTPStatus.OK, {"submissions": [self._submission_view(workspace, item) for item in submissions if item["state"] in {"SUBMITTED", "RESUBMITTED"}]})

        if len(route) >= 2 and route[0] == "workspaces":
            workspace = self._workspace(route[1])
            assignment = self._assignment(workspace.assignment_id)
            self._authorize_workspace(role, workspace, assignment)
            if len(route) == 2 and method == "GET":
                return self._success(HTTPStatus.OK, self._workspace_view(workspace, assignment))
            if route[2:] == ["submissions", "latest"] and method == "GET":
                # This synthetic read path is intentionally limited to the fixed
                # student demo role. Teachers use the assignment review queue.
                if role != "student":
                    raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
                latest = deepcopy(workspace.submissions[-1]) if workspace.submissions else None
                return self._success(HTTPStatus.OK, {"submission": latest})
            if route[2:] == ["start"] and method == "POST" and role == "student":
                self._empty_fields(payload)

                def start() -> ApiResponse:
                    self._match_revision(if_match, workspace.revision)
                    was_paused = workspace.state == "PAUSED"
                    if workspace.state not in {"ASSIGNED", "PAUSED", "FEEDBACK_REQUIRED"}:
                        raise ApiFault(HTTPStatus.CONFLICT, "state_conflict", "only an assigned, paused, or feedback-required workspace can be started")
                    if any(
                        item.workspace is not None
                        and item.workspace.workspace_id != workspace.workspace_id
                        and item.workspace.state == "IN_PROGRESS"
                        for item in self.store.assignments.values()
                    ):
                        raise ApiFault(HTTPStatus.CONFLICT, "active_task_exists", "请先暂停当前进行中的任务，再开始此任务。")
                    workspace.state = "IN_PROGRESS"
                    event = self.store.event(workspace, role, "student.work_resumed" if was_paused else "student.work_started", workspace.workspace_id)
                    return self._success(HTTPStatus.OK, {"workspace": self._workspace_view(workspace, assignment), "event": event}, revision=workspace.revision)

                return self._mutate(role, idempotency_key, payload, f"start:{workspace.workspace_id}", start, if_match=if_match)
            if route[2:] == ["pause"] and method == "POST" and role == "student":
                self._empty_fields(payload)

                def pause() -> ApiResponse:
                    self._match_revision(if_match, workspace.revision)
                    if workspace.state != "IN_PROGRESS":
                        raise ApiFault(HTTPStatus.CONFLICT, "state_conflict", "only an in-progress workspace can be paused")
                    workspace.state = "PAUSED"
                    event = self.store.event(workspace, role, "student.work_paused", workspace.workspace_id)
                    return self._success(HTTPStatus.OK, {"workspace": self._workspace_view(workspace, assignment), "event": event}, revision=workspace.revision)

                return self._mutate(role, idempotency_key, payload, f"pause:{workspace.workspace_id}", pause, if_match=if_match)
            if route[2:] == ["agent-turns"] and method == "POST" and role == "student":
                self._fields(payload, {"question"})
                question = self._text(payload, "question", 2048)

                def agent_turn() -> ApiResponse:
                    self._match_revision(if_match, workspace.revision)
                    if workspace.state != "IN_PROGRESS":
                        raise ApiFault(HTTPStatus.CONFLICT, "state_conflict", "Agent guidance is unavailable in this workspace state")
                    response = self._guidance.guide(task_id=assignment.task["task_id"], task_goal=assignment.task["goal"], student_question=question)
                    turn_id = f"agent-turn-{workspace.revision + 1}"
                    proposal = None
                    if assignment.task["collaboration_mode"] == "PROPOSE_WITH_STUDENT_CONFIRMATION":
                        proposal_id = f"proposal-{workspace.revision + 1}"
                        proposal = {
                            "id": proposal_id,
                            "kind": "FILE_PATCH_PREVIEW",
                            "target_artifact_ref": "artifact-main-py-v1",
                            "status": "PROPOSED",
                            "diff": "固定差异预览：先计算 expected，再比较金额；不会写入或运行代码。",
                        }
                        workspace.proposals[proposal_id] = proposal
                    event = self.store.event(workspace, role, "agent.turn_created", turn_id)
                    data = {"turn": {"id": turn_id, "provider_mode": "scripted-demo", "response_text": response.text, "availability": "AVAILABLE", "event_sequence": event["sequence"]}, "workspace_revision": workspace.revision}
                    if proposal is not None:
                        data["proposed_action"] = proposal
                    return self._success(HTTPStatus.OK, data, revision=workspace.revision)

                return self._mutate(role, idempotency_key, payload, f"agent-turn:{workspace.workspace_id}", agent_turn, if_match=if_match)

            if len(route) == 5 and route[2] == "proposed-actions" and route[4] == "decision" and method == "POST" and role == "student":
                self._fields(payload, {"decision"})
                decision = payload["decision"]
                if decision not in {"ACCEPTED", "REJECTED", "STUDENT_TAKEOVER"}:
                    raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_decision", "unsupported proposal decision")
                proposal_id = route[3]

                def decide() -> ApiResponse:
                    self._match_revision(if_match, workspace.revision)
                    proposal = workspace.proposals.get(proposal_id)
                    if proposal is None:
                        raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
                    if proposal["status"] != "PROPOSED":
                        raise ApiFault(HTTPStatus.CONFLICT, "state_conflict", "proposal already has a decision")
                    proposal["status"] = decision
                    event = self.store.event(workspace, role, "agent.proposed_action_decided", proposal_id)
                    proposal["decision_event_sequence"] = event["sequence"]
                    return self._success(HTTPStatus.OK, {"proposed_action": proposal, "workspace_revision": workspace.revision}, revision=workspace.revision)

                return self._mutate(role, idempotency_key, payload, f"proposal:{workspace.workspace_id}:{proposal_id}", decide, if_match=if_match)

            if route[2:] == ["submissions"] and method == "POST" and role == "student":
                self._fields(payload, {"artifact_refs", "artifact_contents", "student_explanation"})
                explanation = self._text(payload, "student_explanation", 4096)
                if len(explanation) < 20:
                    raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "explanation_too_short", "write at least 20 characters about verification or uncertainty")
                refs = self._artifact_refs(payload["artifact_refs"])
                snapshots = self._artifact_snapshots(refs, payload["artifact_contents"])

                def submit() -> ApiResponse:
                    self._match_revision(if_match, workspace.revision)
                    if workspace.state not in {"IN_PROGRESS", "FEEDBACK_REQUIRED"}:
                        raise ApiFault(HTTPStatus.CONFLICT, "state_conflict", "submission is unavailable in this workspace state")
                    version = len(workspace.submissions) + 1
                    submission = {
                        "id": f"submission-{self.store._next_submission}",
                        "workspace_id": workspace.workspace_id,
                        "assignment_version": assignment.task["version"],
                        "version": version,
                        "artifact_refs": refs,
                        "artifact_snapshots": snapshots,
                        "student_explanation": explanation,
                        "state": "SUBMITTED" if version == 1 else "RESUBMITTED",
                    }
                    self.store._next_submission += 1
                    workspace.submissions.append(submission)
                    workspace.state = "REVIEW_REQUIRED" if version == 1 else "RESUBMITTED"
                    for remediation in workspace.remediations:
                        if remediation["state"] == "OPEN":
                            remediation["state"] = "RESPONDED"
                            remediation["response_submission_id"] = submission["id"]
                    event = self.store.event(workspace, role, "submission.created", submission["id"])
                    submission["created_event_sequence"] = event["sequence"]
                    return self._success(HTTPStatus.CREATED, {"submission": submission, "workspace_revision": workspace.revision}, revision=workspace.revision)

                return self._mutate(role, idempotency_key, payload, f"submission:{workspace.workspace_id}", submit, if_match=if_match)

            if route[2:] == ["remediation"] and method == "GET":
                return self._success(HTTPStatus.OK, {"remediations": workspace.remediations})

            if route[2:] == ["events"] and method == "GET":
                cursors = query.get("after_sequence", ["0"])
                if len(cursors) != 1:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "event cursor must be a single integer")
                try:
                    after = int(cursors[0])
                except ValueError as error:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "event cursor must be a single integer") from error
                limits = query.get("limit", [str(MAX_EVENT_PAGE_SIZE)])
                if len(limits) != 1:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "event page limit must be a single integer")
                try:
                    limit = int(limits[0])
                except ValueError as error:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_page_limit", "event page limit must be an integer") from error
                if after < 0:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_cursor", "event cursor must not be negative")
                if not 1 <= limit <= MAX_EVENT_PAGE_SIZE:
                    raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_page_limit", f"page limit must be between 1 and {MAX_EVENT_PAGE_SIZE}")
                if workspace.events_pruned and workspace.events and after < workspace.events[0]["sequence"] - 1:
                    raise ApiFault(HTTPStatus.CONFLICT, "cursor_expired", "event cursor is older than the retained synthetic history; refresh the workspace")
                available = [event for event in workspace.events if event["sequence"] > after]
                events = available[:limit]
                next_sequence = events[-1]["sequence"] if events else after
                return self._success(HTTPStatus.OK, {
                    "events": events,
                    "next_sequence": next_sequence,
                    "has_more": len(available) > len(events),
                })

        if len(route) == 3 and route[0] == "submissions" and route[2] == "review-actions" and method == "POST" and role == "teacher":
            submission_id = route[1]
            workspace, assignment, submission = self._submission(submission_id)
            self._authorize_workspace(role, workspace, assignment)
            self._fields(payload, {"kind", "reason"})
            kind = payload["kind"]
            reason = self._text(payload, "reason", 1024)
            if kind not in REVIEW_KINDS:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_review_kind", "unsupported review action")
            if sum(not character.isspace() for character in reason) < 8:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "reason_too_short", "every review action requires at least 8 non-whitespace characters")

            def review() -> ApiResponse:
                self._match_revision(if_match, workspace.revision)
                if submission is not workspace.submissions[-1] or submission["state"] not in {"SUBMITTED", "RESUBMITTED"}:
                    raise ApiFault(HTTPStatus.CONFLICT, "stale_submission", "only the latest open submission can be reviewed")
                review_action = {
                    "id": f"review-{self.store._next_review}",
                    "submission_id": submission["id"],
                    "submission_version": submission["version"],
                    "kind": kind,
                    "reason": reason,
                }
                self.store._next_review += 1
                workspace.reviews.append(review_action)
                if kind == "ACKNOWLEDGE":
                    workspace.state = "CLOSED"
                    submission["state"] = "ACCEPTED"
                    for remediation in workspace.remediations:
                        if (
                            remediation["state"] == "RESPONDED"
                            and remediation.get("response_submission_id") == submission["id"]
                        ):
                            remediation["state"] = "CLOSED"
                else:
                    workspace.state = "FEEDBACK_REQUIRED"
                    submission["state"] = "FEEDBACK_REQUIRED"
                    remediation = {
                        "id": f"remediation-{self.store._next_remediation}",
                        "review_action_id": review_action["id"],
                        "submission_id": submission["id"],
                        "requested_action": kind,
                        "reason": reason,
                        "state": "OPEN",
                    }
                    self.store._next_remediation += 1
                    workspace.remediations.append(remediation)
                event = self.store.event(workspace, role, "review.action_recorded", review_action["id"])
                review_action["created_event_sequence"] = event["sequence"]
                return self._success(HTTPStatus.CREATED, {"review_action": review_action, "workspace_revision": workspace.revision}, revision=workspace.revision)

            return self._mutate(role, idempotency_key, payload, f"review:{submission_id}", review, if_match=if_match)

        return self._error(HTTPStatus.NOT_FOUND, "not_found", "route was not found")

    def _mutate(
        self,
        role: str,
        key: str | None,
        payload: dict[str, Any],
        operation_name: str,
        operation: Callable[[], ApiResponse],
        *,
        if_match: str | None = None,
    ) -> ApiResponse:
        if not isinstance(key, str) or not _OPAQUE_ID.fullmatch(key):
            raise ApiFault(HTTPStatus.BAD_REQUEST, "idempotency_key_required", "a bounded Idempotency-Key header is required")
        normalized_if_match = if_match.strip('"') if isinstance(if_match, str) else None
        fingerprint = sha256(json.dumps([operation_name, payload, normalized_if_match], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        cached = self._idempotent.get((role, key))
        if cached:
            if cached[0] != fingerprint:
                raise ApiFault(HTTPStatus.CONFLICT, "idempotency_conflict", "Idempotency-Key was reused with different request content")
            replay = deepcopy(cached[1])
            replay.payload["request_id"] = _REQUEST_ID.get()
            return replay
        response = operation()
        self._idempotent[(role, key)] = (fingerprint, deepcopy(response))
        return deepcopy(response)

    def _assignment(self, assignment_id: str) -> Assignment:
        item = self.store.assignments.get(assignment_id)
        if item is None:
            raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
        return item

    def _workspace(self, workspace_id: str) -> Workspace:
        for item in self.store.assignments.values():
            if item.workspace and item.workspace.workspace_id == workspace_id:
                return item.workspace
        raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")

    def _submission(self, submission_id: str) -> tuple[Workspace, Assignment, dict[str, Any]]:
        for assignment in self.store.assignments.values():
            workspace = assignment.workspace
            if workspace:
                for submission in workspace.submissions:
                    if submission["id"] == submission_id:
                        return workspace, assignment, submission
        raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")

    @staticmethod
    def _authorize_workspace(role: str, workspace: Workspace, assignment: Assignment) -> None:
        if role == "student" and workspace.student_actor_ref != DEMO_ACTORS[role]:
            raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")
        if role == "student" and assignment.state != "PUBLISHED":
            raise ApiFault(HTTPStatus.NOT_FOUND, "not_found", "resource was not found")

    def _workspace_view(self, workspace: Workspace, assignment: Assignment | None = None) -> dict[str, Any]:
        assignment = assignment or self._assignment(workspace.assignment_id)
        return {
            "id": workspace.workspace_id,
            "assignment_id": assignment.assignment_id,
            "assignment_version": assignment.task["version"],
            "state": workspace.state,
            "revision": workspace.revision,
            "execution_enabled": False,
            "artifact_refs": [
                {"id": f"artifact-{name.replace('.', '-')}-v1", "logical_name": name, "media_type": media_type, "source": "FIXED_SYNTHETIC", "integrity_status": "NOT_COMPUTED"}
                for name, media_type in ALLOWED_ARTIFACTS.items()
            ],
        }

    def _assignment_view(self, assignment: Assignment) -> dict[str, Any]:
        return {
            "id": assignment.assignment_id,
            "version": assignment.task["version"],
            "state": assignment.state,
            "revision": assignment.revision,
            "task": assignment.task,
            "workspace": self._workspace_view(assignment.workspace, assignment) if assignment.workspace else None,
            "demo_notice": "仅限固定合成本机演示；刷新/服务重启恢复边界以本机适配器为准。",
        }

    @staticmethod
    def _submission_view(workspace: Workspace, submission: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_id": workspace.workspace_id, "workspace_revision": workspace.revision, **submission}

    @staticmethod
    def _fields(payload: dict[str, Any], allowed: set[str]) -> None:
        if set(payload) != allowed:
            raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_fields", "request fields do not match the declared schema")

    @staticmethod
    def _empty_fields(payload: dict[str, Any]) -> None:
        if payload:
            raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_fields", "this request accepts no body fields")

    @staticmethod
    def _text(payload: dict[str, Any], key: str, max_bytes: int) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_text", "required text is missing")
        value = value.strip()
        if len(value.encode("utf-8")) > max_bytes:
            raise ApiFault(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "text_too_large", "text exceeds its byte limit")
        return value

    @staticmethod
    def _artifact_refs(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list) or not value or len(value) > len(ALLOWED_ARTIFACTS):
            raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_artifacts", "select one or more fixed synthetic project artifacts")
        refs = []
        seen = set()
        for name in value:
            if not isinstance(name, str) or name not in ALLOWED_ARTIFACTS or name in seen:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_artifacts", "artifact is not in the fixed synthetic allowlist")
            seen.add(name)
            media_type = ALLOWED_ARTIFACTS[name]
            refs.append({"id": f"artifact-{name.replace('.', '-')}-v1", "logical_name": name, "media_type": media_type, "source": "FIXED_SYNTHETIC", "integrity_status": "NOT_COMPUTED"})
        return refs

    @staticmethod
    def _artifact_snapshots(refs: list[dict[str, Any]], value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, dict) or set(value) != {ref["logical_name"] for ref in refs}:
            raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_artifact_contents", "provide text content for exactly the selected fixed synthetic files")
        snapshots = []
        total_bytes = 0
        for ref in refs:
            name = ref["logical_name"]
            content = value[name]
            if not isinstance(content, str) or "\x00" in content:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_artifact_contents", "artifact content must be bounded UTF-8 text")
            try:
                encoded = content.encode("utf-8", errors="strict")
            except UnicodeEncodeError as error:
                raise ApiFault(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_artifact_contents", "artifact content must be valid UTF-8 text") from error
            if len(encoded) > MAX_ARTIFACT_BYTES:
                raise ApiFault(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "artifact_too_large", "an artifact exceeds its byte limit")
            total_bytes += len(encoded)
            if total_bytes > MAX_SUBMISSION_ARTIFACT_BYTES:
                raise ApiFault(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "artifacts_too_large", "selected artifacts exceed the combined byte limit")
            snapshots.append({
                "logical_name": name,
                "media_type": ref["media_type"],
                "size_bytes": len(encoded),
                "sha256": sha256(encoded).hexdigest(),
                "content": content,
            })
        return snapshots

    @staticmethod
    def _match_revision(if_match: str | None, revision: int) -> None:
        if if_match is None:
            raise ApiFault(HTTPStatus.PRECONDITION_REQUIRED, "revision_required", "If-Match is required for state changes")
        if if_match.strip('"') != str(revision):
            raise ApiFault(HTTPStatus.CONFLICT, "stale_revision", "workspace changed; refresh before trying again")

    @staticmethod
    def _body(body: bytes | str) -> dict[str, Any]:
        raw = body.encode("utf-8") if isinstance(body, str) else body
        if len(raw) > MAX_BODY_BYTES:
            raise ApiFault(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "payload_too_large", "request body exceeds the 16 KiB limit")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_json", "request body must be UTF-8 JSON") from error
        if not isinstance(value, dict):
            raise ApiFault(HTTPStatus.BAD_REQUEST, "invalid_json", "request body must be a JSON object")
        return value

    @staticmethod
    def _success(status: HTTPStatus, data: dict[str, Any], *, revision: int | None = None) -> ApiResponse:
        request_id = _REQUEST_ID.get()
        payload: dict[str, Any] = {"schema_version": API_VERSION, "request_id": request_id, "data": data}
        if revision is not None:
            payload["revision"] = revision
        return ApiResponse(int(status), payload)

    @staticmethod
    def _error(status: HTTPStatus, code: str, message: str) -> ApiResponse:
        return ApiResponse(int(status), {"schema_version": API_VERSION, "request_id": _REQUEST_ID.get(), "error": {"code": code, "message": message, "retryable": status in {HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.SERVICE_UNAVAILABLE}}})


class ApiFault(Exception):
    def __init__(self, status: HTTPStatus, code: str, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message
        super().__init__(message)
