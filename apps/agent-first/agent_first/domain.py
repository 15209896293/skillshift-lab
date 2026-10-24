"""Small, deterministic domain model for the Agent-first R0 vertical slice.

It intentionally has no filesystem, network, subprocess, browser, credential, or
model-provider capability.  It represents only in-platform synthetic workflow facts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .scripted_guidance import Guidance, GuidanceAdapter


class WorkflowError(ValueError):
    """Raised when a role or state transition violates the task contract."""


class WorkStatus(str, Enum):
    DRAFT = "DRAFT"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FEEDBACK_REQUIRED = "FEEDBACK_REQUIRED"
    RESUBMITTED = "RESUBMITTED"
    CLOSED = "CLOSED"


class ReviewKind(str, Enum):
    ACKNOWLEDGE = "ACKNOWLEDGE"
    REQUEST_EXPLANATION = "REQUEST_EXPLANATION"
    REQUEST_REMEDIATION = "REQUEST_REMEDIATION"
    ENVIRONMENT_ISSUE = "ENVIRONMENT_ISSUE"


@dataclass(frozen=True)
class TaskTemplate:
    task_id: str
    version: str
    title: str
    goal: str
    collaboration_mode: str
    student_responsibility: str
    submission_requirement: str


@dataclass(frozen=True)
class DomainEvent:
    sequence: int
    event_type: str
    actor_id: str
    reason: str
    version: str = "event/v1"


@dataclass(frozen=True)
class StudentResponse:
    response_id: str
    student_id: str
    text: str
    responsibility_kind: str
    revision: int


@dataclass(frozen=True)
class ReviewAction:
    action_id: str
    teacher_id: str
    kind: ReviewKind
    reason: str


TASK_TEXT_MAX_BYTES = {
    "title": 128,
    "goal": 4096,
    "student_responsibility": 2048,
    "submission_requirement": 2048,
}


def _bounded_task_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized.encode("utf-8")) > TASK_TEXT_MAX_BYTES[field]:
        raise ValueError(f"{field} exceeds the synthetic task text limit")
    return normalized


def build_synthetic_template(
    *,
    task_id: str = "synthetic-data-check-v1",
    title: str = "识别并解释一条不一致的数据记录",
    goal: str = "识别给定表格中的一条不一致记录，并说明你如何检查判断。",
    student_responsibility: str = "提交判断、一个可检查的验证步骤和不确定之处。",
    submission_requirement: str = "一段任务关联的验证或解释文本。",
) -> TaskTemplate:
    """Build a bounded synthetic task from the frozen example's editable text."""

    if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 128:
        raise ValueError("task_id must be a bounded non-empty identifier")
    return TaskTemplate(
        task_id=task_id.strip(),
        version="task-template/v1",
        title=_bounded_task_text(title, "title"),
        goal=_bounded_task_text(goal, "goal"),
        collaboration_mode="引导需确认",
        student_responsibility=_bounded_task_text(student_responsibility, "student_responsibility"),
        submission_requirement=_bounded_task_text(submission_requirement, "submission_requirement"),
    )


class EducationWorkflow:
    """One teacher, one student, one synthetic task and append-only facts."""

    def __init__(self, *, teacher_id: str, student_id: str, template: TaskTemplate, adapter: GuidanceAdapter) -> None:
        self.teacher_id = teacher_id
        self.student_id = student_id
        self.template = template
        self.adapter = adapter
        self.status = WorkStatus.DRAFT
        self.events: list[DomainEvent] = []
        self.interactions: list[Guidance] = []
        self.responses: list[StudentResponse] = []
        self.review_actions: list[ReviewAction] = []

    def _event(self, event_type: str, actor_id: str, reason: str) -> None:
        self.events.append(
            DomainEvent(
                sequence=len(self.events) + 1,
                event_type=event_type,
                actor_id=actor_id,
                reason=reason,
            )
        )

    def create_and_assign(self, *, actor_id: str) -> None:
        self._require_teacher(actor_id)
        if self.status is not WorkStatus.DRAFT:
            raise WorkflowError("only a draft task can be assigned")
        self.status = WorkStatus.ASSIGNED
        self._event("assignment.created", actor_id, "fixed synthetic template selected")
        self._event("assignment.assigned", actor_id, "synthetic student assigned")

    def start(self, *, actor_id: str) -> None:
        self._require_student(actor_id)
        if self.status is not WorkStatus.ASSIGNED:
            raise WorkflowError("only an assigned task can start")
        self.status = WorkStatus.IN_PROGRESS
        self._event("student.work_started", actor_id, "student opened assigned task")

    def ask_guidance(self, *, actor_id: str, question: str) -> Guidance:
        self._require_student(actor_id)
        if self.status is not WorkStatus.IN_PROGRESS:
            raise WorkflowError("guidance is available only while work is in progress")
        guidance = self.adapter.guide(task_id=self.template.task_id, task_goal=self.template.goal, student_question=question)
        self.interactions.append(guidance)
        self._event("agent.guidance_requested", actor_id, "task-scoped student question")
        if guidance.availability == "AVAILABLE":
            self._event("agent.guidance_returned", "agent", guidance.adapter_version)
        else:
            self._event("agent.guidance_fallback_used", "agent", guidance.fallback_from or guidance.adapter_version)
        return guidance

    def submit(self, *, actor_id: str, response_text: str, responsibility_kind: str) -> StudentResponse:
        self._require_student(actor_id)
        if self.status not in {WorkStatus.IN_PROGRESS, WorkStatus.FEEDBACK_REQUIRED}:
            raise WorkflowError("submission is unavailable in the current state")
        normalized = response_text.strip()
        if len(normalized) < 20:
            raise WorkflowError("student response must contain a task-related verification or explanation")
        if responsibility_kind not in {"verification", "explanation", "correction", "remediation"}:
            raise WorkflowError("unsupported student responsibility kind")
        response = StudentResponse(
            response_id=f"response-{len(self.responses) + 1}",
            student_id=self.student_id,
            text=normalized,
            responsibility_kind=responsibility_kind,
            revision=len(self.responses) + 1,
        )
        self.responses.append(response)
        self.status = WorkStatus.RESUBMITTED if response.revision > 1 else WorkStatus.REVIEW_REQUIRED
        self._event("submission.created", actor_id, responsibility_kind)
        return response

    def review(self, *, actor_id: str, kind: ReviewKind, reason: str) -> ReviewAction:
        self._require_teacher(actor_id)
        if self.status not in {WorkStatus.REVIEW_REQUIRED, WorkStatus.RESUBMITTED}:
            raise WorkflowError("review is unavailable in the current state")
        normalized = reason.strip()
        if len(normalized) < 8:
            raise WorkflowError("review action requires an explainable reason")
        action = ReviewAction(
            action_id=f"review-{len(self.review_actions) + 1}",
            teacher_id=self.teacher_id,
            kind=kind,
            reason=normalized,
        )
        self.review_actions.append(action)
        self.status = WorkStatus.CLOSED if kind is ReviewKind.ACKNOWLEDGE else WorkStatus.FEEDBACK_REQUIRED
        self._event("review.action_recorded", actor_id, kind.value)
        return action

    def manifest(self) -> dict[str, Any]:
        if not self.responses:
            raise WorkflowError("a submission manifest requires a student response")
        return {
            "schema_version": "agent-first-submission/v1",
            "task": {"id": self.template.task_id, "version": self.template.version},
            "guidance_adapter_version": self.adapter.version,
            "guidance_records": [
                {
                    "adapter_version": guidance.adapter_version,
                    "source": guidance.source,
                    "availability": guidance.availability,
                    "fallback_from": guidance.fallback_from,
                }
                for guidance in self.interactions
            ],
            "status": self.status.value,
            "student_response": asdict(self.responses[-1]),
            "review_actions": [
                {**asdict(action), "kind": action.kind.value} for action in self.review_actions
            ],
            "event_references": [event.sequence for event in self.events],
        }

    def _require_teacher(self, actor_id: str) -> None:
        if actor_id != self.teacher_id:
            raise WorkflowError("teacher action denied")

    def _require_student(self, actor_id: str) -> None:
        if actor_id != self.student_id:
            raise WorkflowError("student action denied")
