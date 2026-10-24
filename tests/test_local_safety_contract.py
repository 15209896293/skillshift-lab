"""Local synthetic safety-contract tests for PCP-13, PCP-18, and PCP-20.

Every credential below is a clearly fake synthetic string.  No real key, password,
private key, AccessKey, or network call is used anywhere in this file.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first import EducationWorkflow, ReviewKind, ScriptedGuidanceAdapter, build_synthetic_template
from agent_first.audit_log import (
    AppendOnlyAuditLog,
    AuditAccessDenied,
    AuditAction,
    AuditContractError,
    AuditRole,
    REASON_CODES,
    read_events,
)
from agent_first.log_redaction import (
    ForbiddenInferenceDetected,
    LOG_FIELD_CLASSIFICATION,
    LogFieldClass,
    SecretFieldRefused,
    UnclassifiedLogField,
    redact_log_record,
    sanitize_error_message,
)
from agent_first.secret_scan import SecretLeakDetected, SinkKind, require_clean, scan

# Clearly fake synthetic credential text.  None of these is a real credential.
FAKE_PROVIDER_KEY = "sk-synthetic-not-a-real-key-0000"
FAKE_CLOUD_KEY = "AKIASYNTHETICEXAMPLE000"
FAKE_PASSWORD_LINE = "password: synthetic-not-a-real-password"
FAKE_PEM_BLOCK = "-----BEGIN PRIVATE KEY-----\nsynthetic-not-a-real-key-body\n-----END PRIVATE KEY-----"
FAKE_BEARER = "Bearer synthetic-not-a-real-token-0000"

ALL_SINKS = (SinkKind.MANIFEST, SinkKind.LOG, SinkKind.ERROR, SinkKind.ARTIFACT)


def _require(value, sink) -> None:
    require_clean(value, sink=sink)


def synthetic_manifest() -> dict:
    workflow = EducationWorkflow(
        teacher_id="teacher-synthetic",
        student_id="student-synthetic",
        template=build_synthetic_template(),
        adapter=ScriptedGuidanceAdapter(),
    )
    workflow.create_and_assign(actor_id="teacher-synthetic")
    workflow.start(actor_id="student-synthetic")
    workflow.submit(
        actor_id="student-synthetic",
        responsibility_kind="verification",
        response_text="我比较了任务中的字段与规则，验证这条合成记录的不一致，并写明需要再次确认的材料位置。",
    )
    workflow.review(actor_id="teacher-synthetic", kind=ReviewKind.ACKNOWLEDGE, reason="合成教师复核理由")
    return workflow.manifest()


class SecretScanTests(unittest.TestCase):
    """PCP-13: credential-shaped content is refused at every sink."""

    def test_manifest_sink_refuses_credential_like_field_name(self) -> None:
        payload = {"schema_version": "agent-first-submission/v1", "api_key": "placeholder"}
        with self.assertRaises(SecretLeakDetected):
            _require(payload, SinkKind.MANIFEST)

    def test_log_sink_refuses_fake_provider_key_value(self) -> None:
        payload = {"outcome": f"provider rejected {FAKE_PROVIDER_KEY}"}
        with self.assertRaises(SecretLeakDetected):
            _require(payload, SinkKind.LOG)

    def test_error_sink_refuses_fake_password_assignment(self) -> None:
        with self.assertRaises(SecretLeakDetected):
            _require(f"startup failed because {FAKE_PASSWORD_LINE}", SinkKind.ERROR)

    def test_artifact_sink_refuses_fake_private_key_block(self) -> None:
        with self.assertRaises(SecretLeakDetected):
            _require(f"appendix\n{FAKE_PEM_BLOCK}\nend", SinkKind.ARTIFACT)

    def test_cloud_access_key_and_bearer_token_are_detected(self) -> None:
        for text in (FAKE_CLOUD_KEY, FAKE_BEARER):
            with self.subTest(text=text):
                findings = scan(text, sink=SinkKind.ARTIFACT)
                self.assertTrue(findings)

    def test_findings_never_carry_the_matched_value(self) -> None:
        findings = scan({"outcome": FAKE_PROVIDER_KEY}, sink=SinkKind.LOG)
        rendered = repr(findings)
        self.assertNotIn(FAKE_PROVIDER_KEY, rendered)
        self.assertNotIn("synthetic-not-a-real-key", rendered)
        self.assertTrue(any(finding.rule_id == "value.provider_api_key" for finding in findings))

    def test_refusal_message_never_carries_the_matched_value(self) -> None:
        with self.assertRaises(SecretLeakDetected) as raised:
            _require(FAKE_PROVIDER_KEY, SinkKind.ERROR)
        self.assertNotIn(FAKE_PROVIDER_KEY, str(raised.exception))
        self.assertIn("value.provider_api_key", str(raised.exception))

    def test_benign_token_field_names_are_not_flagged(self) -> None:
        payload = {"max_tokens": 600, "token_budget": 10000, "token_count": 3}
        for sink in ALL_SINKS:
            with self.subTest(sink=sink):
                self.assertEqual((), scan(payload, sink=sink))

    def test_credential_like_field_names_are_flagged_in_every_sink(self) -> None:
        payload = {"credential_reference": "school-deepseek-synthetic", "access_key": "placeholder"}
        for sink in ALL_SINKS:
            with self.subTest(sink=sink):
                rules = {finding.rule_id for finding in scan(payload, sink=sink)}
                self.assertEqual({"field.credential_like_name"}, rules)

    def test_clean_synthetic_manifest_passes_every_sink(self) -> None:
        manifest = synthetic_manifest()
        for sink in ALL_SINKS:
            with self.subTest(sink=sink):
                _require(manifest, sink)


class LogRedactionTests(unittest.TestCase):
    """PCP-18: classification, minimization, and error sanitization."""

    def test_operational_fields_are_kept_and_personal_fields_are_minimized(self) -> None:
        outcome = redact_log_record(
            {
                "action": "submission.recorded",
                "sequence": 3,
                "reason_code": "submission.task_related_response",
                "student_id": "student-synthetic",
                "text": "合成学生回答文本",
            }
        )
        self.assertEqual("submission.recorded", outcome.record["action"])
        self.assertEqual(3, outcome.record["sequence"])
        self.assertEqual("[redacted]", outcome.record["student_id"])
        self.assertEqual("[redacted]", outcome.record["text"])
        self.assertEqual(("$.student_id", "$.text"), outcome.redacted_fields)

    def test_unknown_field_is_refused(self) -> None:
        with self.assertRaises(UnclassifiedLogField):
            redact_log_record({"action": "task.created", "surprise_field": "value"})

    def test_secret_field_is_refused_rather_than_redacted(self) -> None:
        with self.assertRaises(SecretLeakDetected):
            redact_log_record({"action": "task.created", "authorization": "placeholder"})

    def test_secret_field_class_is_explicit_in_the_vocabulary(self) -> None:
        self.assertIs(LogFieldClass.SECRET, LOG_FIELD_CLASSIFICATION["credential_reference"])
        self.assertIs(LogFieldClass.PERSONAL, LOG_FIELD_CLASSIFICATION["text"])
        self.assertIs(LogFieldClass.OPERATIONAL, LOG_FIELD_CLASSIFICATION["action"])

    def test_forbidden_inference_field_is_refused(self) -> None:
        with self.assertRaises(ForbiddenInferenceDetected):
            redact_log_record({"action": "task.created", "cheating_verdict": "placeholder"})

    def test_log_text_asserting_a_cheating_verdict_is_refused(self) -> None:
        with self.assertRaises(ForbiddenInferenceDetected):
            redact_log_record({"action": "task.created", "outcome": "系统判定该生作弊"})

    def test_operational_log_text_without_a_verdict_passes(self) -> None:
        outcome = redact_log_record({"action": "task.created", "outcome": "task-scoped submission recorded"})
        self.assertEqual("task-scoped submission recorded", outcome.record["outcome"])
        self.assertEqual((), outcome.redacted_fields)

    def test_error_message_redacts_absolute_paths_and_addresses(self) -> None:
        message = r"failed to open C:\Users\synthetic\workspace\manifest.json for teacher-synthetic@example.invalid"
        sanitized = sanitize_error_message(message)
        self.assertNotIn(r"C:\Users\synthetic", sanitized)
        self.assertNotIn("teacher-synthetic@example.invalid", sanitized)
        self.assertIn("[redacted]", sanitized)

    def test_error_message_is_bounded(self) -> None:
        sanitized = sanitize_error_message("detail " * 400)
        self.assertLessEqual(len(sanitized), 401)

    def test_error_message_refuses_secret_shaped_text(self) -> None:
        with self.assertRaises(SecretLeakDetected):
            sanitize_error_message(f"transport error near {FAKE_BEARER}")

    def test_error_message_refuses_prohibited_conclusions(self) -> None:
        for message in ("系统判定该生作弊", "AI 替代率 42%", "auto-grading enabled"):
            with self.subTest(message=message):
                with self.assertRaises(ForbiddenInferenceDetected):
                    sanitize_error_message(message)


class AuditLogTests(unittest.TestCase):
    """PCP-20: append-only events, stable IDs, and a default-deny read boundary."""

    def setUp(self) -> None:
        self.fixed_time = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)
        self.log = AppendOnlyAuditLog(clock=lambda: self.fixed_time)

    def _append(self, **overrides):
        payload = {
            "actor_role": AuditRole.STUDENT,
            "actor_id": "student-synthetic",
            "action": AuditAction.SUBMISSION_RECORDED,
            "reason_code": "submission.task_related_response",
            "target_reference": "assignment-synthetic-1",
        }
        payload.update(overrides)
        return self.log.append(**payload)

    def test_event_carries_stable_id_role_time_action_and_reason(self) -> None:
        event = self._append()
        self.assertEqual("audit-000001-" + event.content_hash[:12], event.event_id)
        self.assertEqual(1, event.sequence)
        self.assertEqual("2026-09-24T12:00:00+00:00", event.occurred_at)
        self.assertIs(AuditRole.STUDENT, event.actor_role)
        self.assertIs(AuditAction.SUBMISSION_RECORDED, event.action)
        self.assertIn(event.reason_code, REASON_CODES)
        self.assertEqual("control-plane-audit/v1", event.schema_version)

    def test_event_id_is_deterministic_for_the_same_input(self) -> None:
        first = self._append()
        other = AppendOnlyAuditLog(clock=lambda: self.fixed_time)
        repeated = other.append(
            actor_role=AuditRole.STUDENT,
            actor_id="student-synthetic",
            action=AuditAction.SUBMISSION_RECORDED,
            reason_code="submission.task_related_response",
            target_reference="assignment-synthetic-1",
        )
        self.assertEqual(first.event_id, repeated.event_id)

    def test_log_is_append_only_and_the_chain_verifies(self) -> None:
        self._append()
        self._append(action=AuditAction.REVIEW_RECORDED, actor_role=AuditRole.TEACHER, actor_id="teacher-synthetic", reason_code="review.teacher_recorded")
        events = self.log.events()
        self.assertIsInstance(events, tuple)
        self.assertEqual(2, len(events))
        self.assertEqual("0" * 64, events[0].previous_hash)
        self.assertEqual(events[0].content_hash, events[1].previous_hash)
        self.assertTrue(self.log.verify_chain())

    def test_no_mutation_api_is_exposed(self) -> None:
        for forbidden in ("update", "delete", "remove", "replace", "clear"):
            self.assertFalse(hasattr(self.log, forbidden), forbidden)

    def test_reason_code_outside_the_vocabulary_is_refused(self) -> None:
        with self.assertRaises(AuditContractError):
            self._append(reason_code="free.text.reason")

    def test_non_opaque_actor_reference_is_refused(self) -> None:
        for reference in ("student@example.invalid", "student synthetic", ""):
            with self.subTest(reference=reference):
                with self.assertRaises(AuditContractError):
                    self._append(actor_id=reference)

    def test_credential_shaped_reference_is_refused(self) -> None:
        with self.assertRaises(SecretLeakDetected):
            self._append(target_reference=FAKE_PROVIDER_KEY)

    def test_student_reads_only_own_events(self) -> None:
        self._append(actor_id="student-synthetic")
        self._append(actor_id="student-other")
        visible = read_events(self.log, reader_role=AuditRole.STUDENT, reader_actor_id="student-synthetic")
        self.assertEqual(1, len(visible))
        self.assertEqual("student-synthetic", visible[0].actor_id)

    def test_platform_operator_cannot_read_student_content_events(self) -> None:
        self._append()
        visible = read_events(self.log, reader_role=AuditRole.PLATFORM_OPERATOR, reader_actor_id="operator-synthetic")
        self.assertEqual((), visible)

    def test_system_role_has_no_read_access(self) -> None:
        with self.assertRaises(AuditAccessDenied):
            read_events(self.log, reader_role=AuditRole.SYSTEM, reader_actor_id="system")

    def test_requesting_an_action_outside_the_policy_is_denied(self) -> None:
        with self.assertRaises(AuditAccessDenied):
            read_events(
                self.log,
                reader_role=AuditRole.TEACHER,
                reader_actor_id="teacher-synthetic",
                actions=[AuditAction.BUDGET_RESERVED],
            )

    def test_project_owner_can_read_every_action(self) -> None:
        self._append()
        self._append(action=AuditAction.BUDGET_RESERVED, actor_role=AuditRole.SCHOOL_ADMIN, actor_id="admin-synthetic", reason_code="budget.synthetic_reservation")
        visible = read_events(self.log, reader_role=AuditRole.PROJECT_OWNER, reader_actor_id="owner-synthetic")
        self.assertEqual(2, len(visible))

    def test_audit_events_carry_no_free_text_reason(self) -> None:
        event = self._append()
        self.assertFalse(hasattr(event, "reason"))
        self.assertFalse(hasattr(event, "text"))


if __name__ == "__main__":
    unittest.main()
