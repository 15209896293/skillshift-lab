"""Minimal append-only audit events and a default-deny read boundary.

Synthetic-only: no credential value, endpoint, HTTP client, or network capability.
This is a local contract, not a production audit store.  It does not implement
retention, rotation, tamper-proof external storage, or operator identity.

Design rules:
- Append-only by construction: the API exposes no update or delete path.
- Every event carries a stable ID, role, UTC timestamp, bounded action, and a
  bounded reason code.  Events carry opaque references, never student content.
- Each event chains to its predecessor by hash, so a silent edit is detectable.
- Reads are default-deny per role, and a platform operator never reads
  content-bearing student events.
- No event may assert a cheating, ability, external-AI-use, or auto-grading claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Callable, Iterable

from .log_redaction import assert_no_forbidden_inference
from .secret_scan import SinkKind, require_clean


AUDIT_SCHEMA_VERSION = "control-plane-audit/v1"
GENESIS_HASH = "0" * 64
MAX_REFERENCE_CHARS = 128


class AuditRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    SCHOOL_ADMIN = "school_admin"
    PLATFORM_OPERATOR = "platform_operator"
    PROJECT_OWNER = "project_owner"
    SYSTEM = "system"


class AuditAction(str, Enum):
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    STUDENT_WORK_STARTED = "student.work_started"
    GUIDANCE_REQUESTED = "guidance.requested"
    GUIDANCE_RETURNED = "guidance.returned"
    GUIDANCE_FALLBACK_USED = "guidance.fallback_used"
    SUBMISSION_RECORDED = "submission.recorded"
    REVIEW_RECORDED = "review.recorded"
    BUDGET_RESERVED = "budget.reserved"
    BUDGET_LIMIT_REJECTED = "budget.limit_rejected"
    SECRET_LEAK_REJECTED = "security.secret_leak_rejected"
    LOG_RECORD_REDACTED = "security.log_record_redacted"
    AUDIT_READ_GRANTED = "audit.read_granted"
    AUDIT_READ_DENIED = "audit.read_denied"


REASON_CODES = frozenset(
    {
        "task.scope.question",
        "task.template.frozen_synthetic",
        "task.assignment.synthetic_student",
        "task.work.started",
        "submission.task_related_response",
        "review.teacher_recorded",
        "budget.synthetic_reservation",
        "budget.synthetic_hard_limit",
        "security.credential_like_content",
        "security.personal_field_minimized",
        "audit.policy_evaluated",
    }
)

# Default deny: a role absent here has no audit read access at all.
AUDIT_READ_POLICY: dict[AuditRole, frozenset[AuditAction]] = {
    AuditRole.STUDENT: frozenset(
        {
            AuditAction.STUDENT_WORK_STARTED,
            AuditAction.GUIDANCE_REQUESTED,
            AuditAction.GUIDANCE_RETURNED,
            AuditAction.GUIDANCE_FALLBACK_USED,
            AuditAction.SUBMISSION_RECORDED,
        }
    ),
    AuditRole.TEACHER: frozenset(
        {
            AuditAction.TASK_CREATED,
            AuditAction.TASK_ASSIGNED,
            AuditAction.SUBMISSION_RECORDED,
            AuditAction.REVIEW_RECORDED,
            AuditAction.GUIDANCE_FALLBACK_USED,
        }
    ),
    AuditRole.SCHOOL_ADMIN: frozenset(
        {
            AuditAction.TASK_CREATED,
            AuditAction.TASK_ASSIGNED,
            AuditAction.REVIEW_RECORDED,
            AuditAction.BUDGET_RESERVED,
            AuditAction.BUDGET_LIMIT_REJECTED,
        }
    ),
    AuditRole.PLATFORM_OPERATOR: frozenset(
        {
            AuditAction.SECRET_LEAK_REJECTED,
            AuditAction.LOG_RECORD_REDACTED,
            AuditAction.BUDGET_LIMIT_REJECTED,
            AuditAction.AUDIT_READ_GRANTED,
            AuditAction.AUDIT_READ_DENIED,
        }
    ),
    AuditRole.PROJECT_OWNER: frozenset(AuditAction),
}


class AuditContractError(ValueError):
    """Raised when an audit event would violate the append-only contract."""


class AuditAccessDenied(PermissionError):
    """Raised when a reader role or action is outside the audit read policy."""


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    sequence: int
    occurred_at: str
    actor_role: AuditRole
    actor_id: str
    action: AuditAction
    reason_code: str
    target_reference: str
    previous_hash: str
    content_hash: str
    schema_version: str = AUDIT_SCHEMA_VERSION


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AppendOnlyAuditLog:
    """In-memory append-only audit contract with a verifiable hash chain."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or _utc_now
        self._events: list[AuditEvent] = []

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def append(
        self,
        *,
        actor_role: AuditRole,
        actor_id: str,
        action: AuditAction,
        reason_code: str,
        target_reference: str,
        occurred_at: datetime | None = None,
    ) -> AuditEvent:
        if not isinstance(actor_role, AuditRole):
            raise AuditContractError("actor_role must be an AuditRole")
        if not isinstance(action, AuditAction):
            raise AuditContractError("action must be a bounded AuditAction")
        if reason_code not in REASON_CODES:
            raise AuditContractError(f"reason_code '{reason_code}' is outside the bounded vocabulary")
        actor_reference = _require_reference(actor_id, "actor_id")
        target = _require_reference(target_reference, "target_reference")

        payload = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "sequence": len(self._events) + 1,
            "occurred_at": (occurred_at or self._clock()).astimezone(timezone.utc).isoformat(),
            "actor_role": actor_role.value,
            "actor_id": actor_reference,
            "action": action.value,
            "reason_code": reason_code,
            "target_reference": target,
            "previous_hash": self._events[-1].content_hash if self._events else GENESIS_HASH,
        }
        _require_audit_payload_safe(payload)
        content_hash = sha256(_canonical(payload)).hexdigest()
        event = AuditEvent(
            event_id=f"audit-{payload['sequence']:06d}-{content_hash[:12]}",
            sequence=payload["sequence"],
            occurred_at=payload["occurred_at"],
            actor_role=actor_role,
            actor_id=actor_reference,
            action=action,
            reason_code=reason_code,
            target_reference=target,
            previous_hash=payload["previous_hash"],
            content_hash=content_hash,
        )
        self._events.append(event)
        return event

    def verify_chain(self) -> bool:
        previous = GENESIS_HASH
        for index, event in enumerate(self._events, start=1):
            payload = {
                "schema_version": event.schema_version,
                "sequence": event.sequence,
                "occurred_at": event.occurred_at,
                "actor_role": event.actor_role.value,
                "actor_id": event.actor_id,
                "action": event.action.value,
                "reason_code": event.reason_code,
                "target_reference": event.target_reference,
                "previous_hash": event.previous_hash,
            }
            if event.sequence != index or event.previous_hash != previous:
                return False
            if sha256(_canonical(payload)).hexdigest() != event.content_hash:
                return False
            if event.event_id != f"audit-{event.sequence:06d}-{event.content_hash[:12]}":
                return False
            previous = event.content_hash
        return True


def read_events(
    log: AppendOnlyAuditLog,
    *,
    reader_role: AuditRole,
    reader_actor_id: str,
    actions: Iterable[AuditAction] | None = None,
) -> tuple[AuditEvent, ...]:
    """Return the events a reader role may see.  Absence from the policy denies."""

    if not isinstance(reader_role, AuditRole):
        raise AuditAccessDenied("reader_role must be an AuditRole")
    allowed = AUDIT_READ_POLICY.get(reader_role)
    if allowed is None:
        raise AuditAccessDenied(f"role '{reader_role.value}' has no audit read access")
    if actions is not None:
        requested = set(actions)
        outside = sorted(action.value for action in requested if action not in allowed)
        if outside:
            raise AuditAccessDenied(f"role '{reader_role.value}' may not read [{', '.join(outside)}]")
    selected = [event for event in log.events() if event.action in allowed]
    if reader_role is AuditRole.STUDENT:
        reference = _require_reference(reader_actor_id, "reader_actor_id")
        selected = [event for event in selected if event.actor_id == reference]
    return tuple(selected)


def _require_reference(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuditContractError(f"{label} must be a non-empty opaque reference")
    normalized = value.strip()
    if len(normalized) > MAX_REFERENCE_CHARS:
        raise AuditContractError(f"{label} exceeds the opaque reference size limit")
    if "@" in normalized or any(character.isspace() for character in normalized):
        raise AuditContractError(f"{label} must be an opaque reference, not a name or address")
    return normalized


def _require_audit_payload_safe(payload: dict[str, object]) -> None:
    require_clean(payload, sink=SinkKind.LOG, location="audit")
    for value in payload.values():
        if isinstance(value, str):
            assert_no_forbidden_inference(value)


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
