"""Field-level log classification, redaction, and error sanitization.

Synthetic-only: no credential value, endpoint, or network capability is present.
This module is a local pre-write contract.  It does not implement log retention,
rotation, or a production log pipeline, and it does not claim that a redacted
record is safe to retain forever.

Design rules:
- Every field must be explicitly classified; an unknown field is refused.
- Personal fields are minimized to a placeholder, never stored raw.
- Secret-shaped fields and forbidden-inference conclusions are refused outright,
  not redacted-and-kept, so the sink never holds them even briefly.
- No function emits a cheating, ability, external-AI-use, or auto-grading verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from .secret_scan import REDACTION_PLACEHOLDER, SecretLeakDetected, SinkKind, require_clean


MAX_ERROR_MESSAGE_CHARS = 400


class LogFieldClass(str, Enum):
    OPERATIONAL = "operational"
    PERSONAL = "personal"
    SECRET = "secret"
    FORBIDDEN_INFERENCE = "forbidden_inference"


class UnclassifiedLogField(ValueError):
    """Raised when a log field has no explicit classification."""


class SecretFieldRefused(SecretLeakDetected):
    """Raised when a secret-shaped field would enter a sink."""


class ForbiddenInferenceDetected(ValueError):
    """Raised when text asserts a prohibited conclusion about a student."""


# Explicit, minimal field vocabulary.  Anything absent here is refused.
LOG_FIELD_CLASSIFICATION: dict[str, LogFieldClass] = {
    # operational: safe to record without a personal-data decision
    "event_type": LogFieldClass.OPERATIONAL,
    "action": LogFieldClass.OPERATIONAL,
    "action_id": LogFieldClass.OPERATIONAL,
    "sequence": LogFieldClass.OPERATIONAL,
    "revision": LogFieldClass.OPERATIONAL,
    "status": LogFieldClass.OPERATIONAL,
    "schema_version": LogFieldClass.OPERATIONAL,
    "adapter_version": LogFieldClass.OPERATIONAL,
    "availability": LogFieldClass.OPERATIONAL,
    "fallback_from": LogFieldClass.OPERATIONAL,
    "source": LogFieldClass.OPERATIONAL,
    "kind": LogFieldClass.OPERATIONAL,
    "responsibility_kind": LogFieldClass.OPERATIONAL,
    "reason_code": LogFieldClass.OPERATIONAL,
    "task_id": LogFieldClass.OPERATIONAL,
    "version": LogFieldClass.OPERATIONAL,
    "content_hash": LogFieldClass.OPERATIONAL,
    "occurred_at": LogFieldClass.OPERATIONAL,
    "actor_role": LogFieldClass.OPERATIONAL,
    "duration_ms": LogFieldClass.OPERATIONAL,
    "outcome": LogFieldClass.OPERATIONAL,
    # personal: minimized before any durable write
    "actor_id": LogFieldClass.PERSONAL,
    "student_id": LogFieldClass.PERSONAL,
    "teacher_id": LogFieldClass.PERSONAL,
    "response_id": LogFieldClass.PERSONAL,
    "text": LogFieldClass.PERSONAL,
    "student_response": LogFieldClass.PERSONAL,
    "response_text": LogFieldClass.PERSONAL,
    "student_question": LogFieldClass.PERSONAL,
    "reason": LogFieldClass.PERSONAL,
    "email": LogFieldClass.PERSONAL,
    "display_name": LogFieldClass.PERSONAL,
    # secret: refused outright
    "api_key": LogFieldClass.SECRET,
    "apikey": LogFieldClass.SECRET,
    "password": LogFieldClass.SECRET,
    "access_key": LogFieldClass.SECRET,
    "credential": LogFieldClass.SECRET,
    "credential_reference": LogFieldClass.SECRET,
    "authorization": LogFieldClass.SECRET,
    "private_key": LogFieldClass.SECRET,
    # forbidden inference: refused outright
    "cheating_verdict": LogFieldClass.FORBIDDEN_INFERENCE,
    "ability_score": LogFieldClass.FORBIDDEN_INFERENCE,
    "external_ai_verdict": LogFieldClass.FORBIDDEN_INFERENCE,
    "auto_grade": LogFieldClass.FORBIDDEN_INFERENCE,
}

_FORBIDDEN_INFERENCE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "inference.cheating_verdict",
        re.compile(r"(判定|认定|证明|检测到|已确认|结论[:：]?).{0,12}(作弊|抄袭|代写)"),
    ),
    (
        "inference.external_ai_verdict",
        re.compile(r"(判定|认定|证明|检测到|已确认|结论[:：]?).{0,12}(外部\s?AI|AI\s?代写)"),
    ),
    (
        "inference.ability_verdict",
        re.compile(r"(学生|该生|此人|该同学).{0,10}(能力|水平).{0,8}(不足|偏低|较差|很差|评分|等级|画像)"),
    ),
    ("inference.auto_score", re.compile(r"(自动评分|自动打分|能力画像|AI\s?替代率|替代率)")),
    (
        "inference.cheating_verdict_en",
        re.compile(r"(?i)\b(detected|proven|confirmed|concluded|verdict)\b.{0,24}\b(cheating|plagiarism|ghostwriting|external\s+ai)\b"),
    ),
    ("inference.ability_verdict_en", re.compile(r"(?i)\b(ability|capability)\s+(score|level|rating|profile)\b")),
    ("inference.auto_score_en", re.compile(r"(?i)\bauto-?grad(?:e|ing)\b")),
)

_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[A-Za-z]:\\{1,2}(?:Users|Documents and Settings)\\[^\s\"'`,;)]+"),
    re.compile(r"/(?:home|Users)/[^\s\"'`,;)]+"),
)
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


@dataclass(frozen=True)
class RedactionOutcome:
    record: dict[str, Any]
    redacted_fields: tuple[str, ...]
    placeholder: str = REDACTION_PLACEHOLDER


def find_forbidden_inference(text: str) -> tuple[str, ...]:
    """Return the rule IDs of any prohibited conclusion asserted by the text."""

    return tuple(rule_id for rule_id, pattern in _FORBIDDEN_INFERENCE_RULES if pattern.search(text))


def assert_no_forbidden_inference(text: str) -> None:
    """Raise ForbiddenInferenceDetected when text asserts a prohibited conclusion."""

    rules = find_forbidden_inference(text)
    if rules:
        raise ForbiddenInferenceDetected(
            f"prohibited conclusion refused [{', '.join(rules)}]; no cheating, ability, "
            "external-AI-use, or auto-grading claim may be emitted"
        )


def redact_log_record(
    record: dict[str, Any],
    *,
    sink: SinkKind = SinkKind.LOG,
    location: str = "$",
) -> RedactionOutcome:
    """Classify and minimize a log record.  Unknown fields are refused."""

    if not isinstance(record, dict):
        raise UnclassifiedLogField("a log record must be a mapping of explicitly classified fields")
    require_clean(record, sink=sink, location=location)
    redacted: list[str] = []
    minimized = _redact_mapping(record, location=location, redacted=redacted)
    return RedactionOutcome(record=minimized, redacted_fields=tuple(redacted))


def _redact_mapping(record: dict[str, Any], *, location: str, redacted: list[str]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in record.items():
        field_class = LOG_FIELD_CLASSIFICATION.get(_normalize(key))
        child = f"{location}.{key}"
        if field_class is None:
            raise UnclassifiedLogField(f"log field '{key}' has no classification; add it before writing")
        if field_class is LogFieldClass.SECRET:
            raise SecretFieldRefused(f"secret-shaped log field '{key}' is refused, not redacted")
        if field_class is LogFieldClass.FORBIDDEN_INFERENCE:
            raise ForbiddenInferenceDetected(f"prohibited-inference log field '{key}' is refused")
        if field_class is LogFieldClass.PERSONAL:
            redacted.append(child)
            output[key] = REDACTION_PLACEHOLDER
            continue
        if isinstance(value, str):
            assert_no_forbidden_inference(value)
        output[key] = _redact_value(value, location=child, redacted=redacted)
    return output


def _redact_value(value: Any, *, location: str, redacted: list[str]) -> Any:
    if isinstance(value, dict):
        return _redact_mapping(value, location=location, redacted=redacted)
    if isinstance(value, (list, tuple)):
        return [_redact_value(item, location=f"{location}[{index}]", redacted=redacted) for index, item in enumerate(value)]
    return value


def sanitize_error_message(message: str) -> str:
    """Return a bounded, path- and email-scrubbed error message.

    Credential-shaped content and prohibited conclusions are refused rather than
    rewritten, so an error path can never carry either one forward.
    """

    if not isinstance(message, str):
        raise TypeError("an error message must be a string")
    require_clean(message, sink=SinkKind.ERROR)
    assert_no_forbidden_inference(message)
    scrubbed = message
    for pattern in _PATH_PATTERNS:
        scrubbed = pattern.sub(REDACTION_PLACEHOLDER, scrubbed)
    scrubbed = _EMAIL_PATTERN.sub(REDACTION_PLACEHOLDER, scrubbed)
    if len(scrubbed) > MAX_ERROR_MESSAGE_CHARS:
        scrubbed = scrubbed[:MAX_ERROR_MESSAGE_CHARS] + "…"
    return scrubbed


def _normalize(key: Any) -> str:
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")
