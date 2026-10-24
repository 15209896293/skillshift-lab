"""Generate a machine-checkable Artifact for the local control-plane safety contract.

It writes only synthetic facts and rule identifiers.  It never writes a credential
value, endpoint, or network result, and it self-scans the Artifact it just produced.

Naming note: the field-name rule matches risky substrings, so a section key that
merely contains the word "secret" is refused.  The PCP-13 section key is therefore
named `pcp_13_sensitive_content_scan`; the observed refusal is recorded under
`self_scan` rather than suppressed.

Usage (repository root, PowerShell):
    $env:PYTHONUTF8='1'
    python apps\agent-first\run_safety_contract_evidence.py
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from agent_first import EducationWorkflow, ReviewKind, ScriptedGuidanceAdapter, build_synthetic_template
from agent_first.audit_log import (
    AUDIT_READ_POLICY,
    AUDIT_SCHEMA_VERSION,
    AppendOnlyAuditLog,
    AuditAction,
    AuditRole,
    GENESIS_HASH,
    REASON_CODES,
    read_events,
)
from agent_first.log_redaction import (
    LOG_FIELD_CLASSIFICATION,
    LogFieldClass,
    redact_log_record,
    sanitize_error_message,
)
from agent_first.secret_scan import (
    SinkKind,
    describe_findings,
    require_clean,
    scan,
)

# Synthetic fixtures.  None of these is a real credential and none is written to the Artifact.
FAKE_PROVIDER_KEY = "sk-synthetic-not-a-real-key-0000"
FAKE_CLOUD_KEY = "AKIASYNTHETICEXAMPLE000"
FAKE_PASSWORD_LINE = "password: synthetic-not-a-real-password"
FAKE_PEM_BLOCK = "-----BEGIN PRIVATE KEY-----\nsynthetic-not-a-real-key-body\n-----END PRIVATE KEY-----"
FAKE_BEARER = "Bearer synthetic-not-a-real-token-0000"

REPORT_DATE = "2026-09-24"
OUTPUT = ROOT / "artifacts" / "R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT" / "evidence.json"


def _synthetic_manifest() -> dict:
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


def _refusal(sink: SinkKind, value) -> dict:
    findings = scan(value, sink=sink)
    return {
        "sink": sink.value,
        "rule_ids": sorted({finding.rule_id for finding in findings}),
        "locations": sorted({finding.location for finding in findings}),
        "findings": describe_findings(findings),
    }


def _secret_scan_evidence() -> dict:
    refusals = [
        _refusal(SinkKind.MANIFEST, {"schema_version": "agent-first-submission/v1", "api_key": "placeholder"}),
        _refusal(SinkKind.LOG, {"outcome": f"provider rejected {FAKE_PROVIDER_KEY}"}),
        _refusal(SinkKind.ERROR, f"startup failed because {FAKE_PASSWORD_LINE}"),
        _refusal(SinkKind.ARTIFACT, f"appendix\n{FAKE_PEM_BLOCK}\nend"),
        _refusal(SinkKind.ARTIFACT, FAKE_CLOUD_KEY),
        _refusal(SinkKind.ARTIFACT, FAKE_BEARER),
    ]
    manifest = _synthetic_manifest()
    accepted = all(not scan(manifest, sink=sink) for sink in SinkKind)
    return {
        "module": "apps/agent-first/agent_first/secret_scan.py",
        "sinks_covered": [sink.value for sink in SinkKind],
        "field_rule": "field.credential_like_name",
        "value_rules": [
            "value.provider_api_key",
            "value.cloud_access_key",
            "value.private_key_block",
            "value.bearer_token",
            "value.password_assignment",
        ],
        "refusals": refusals,
        "clean_synthetic_manifest_accepted": accepted,
        "findings_carry_values": any(
            "synthetic-not-a-real" in json.dumps(refusal, ensure_ascii=False) for refusal in refusals
        ),
    }


def _log_redaction_evidence() -> dict:
    classes: dict[LogFieldClass, int] = {member: 0 for member in LogFieldClass}
    for field_class in LOG_FIELD_CLASSIFICATION.values():
        classes[field_class] += 1
    positive = redact_log_record(
        {
            "action": "submission.recorded",
            "sequence": 3,
            "reason_code": "submission.task_related_response",
            "student_id": "student-synthetic",
            "text": "合成学生回答文本",
        }
    )
    negative: list[dict] = []
    for case, record in (
        ("unknown_field", {"action": "task.created", "surprise_field": "value"}),
        ("secret_field", {"action": "task.created", "authorization": "placeholder"}),
        ("forbidden_inference_field", {"action": "task.created", "cheating_verdict": "placeholder"}),
        ("cheating_verdict_text", {"action": "task.created", "outcome": "系统判定该生作弊"}),
    ):
        try:
            redact_log_record(record)
        except ValueError as error:
            negative.append({"case": case, "refused_by": type(error).__name__})
        else:
            negative.append({"case": case, "refused_by": None})
    sanitized = sanitize_error_message(r"failed to open C:\Users\synthetic\work\manifest.json for synthetic@example.invalid")
    return {
        "module": "apps/agent-first/agent_first/log_redaction.py",
        "redaction_placeholder": positive.placeholder,
        "field_classes": [
            {"field_class": member.value, "count": classes[member]}
            for member in LogFieldClass
        ],
        "classified_field_count": len(LOG_FIELD_CLASSIFICATION),
        "positive_case": {
            "kept_fields": sorted(set(positive.record) - set(positive.redacted_fields)),
            "redacted_fields": list(positive.redacted_fields),
        },
        "negative_cases": negative,
        "error_sanitization": {
            "path_scrubbed": "Users" not in sanitized,
            "address_scrubbed": "synthetic@example.invalid" not in sanitized,
            "bounded": len(sanitized) <= 401,
        },
        "forbidden_inference_rules": [
            "inference.cheating_verdict",
            "inference.external_ai_verdict",
            "inference.ability_verdict",
            "inference.auto_score",
            "inference.cheating_verdict_en",
            "inference.ability_verdict_en",
            "inference.auto_score_en",
        ],
    }


def _audit_evidence() -> dict:
    fixed = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)
    log = AppendOnlyAuditLog(clock=lambda: fixed)
    log.append(
        actor_role=AuditRole.TEACHER,
        actor_id="teacher-synthetic",
        action=AuditAction.TASK_CREATED,
        reason_code="task.template.frozen_synthetic",
        target_reference="assignment-synthetic-1",
    )
    log.append(
        actor_role=AuditRole.STUDENT,
        actor_id="student-synthetic",
        action=AuditAction.SUBMISSION_RECORDED,
        reason_code="submission.task_related_response",
        target_reference="assignment-synthetic-1",
    )
    log.append(
        actor_role=AuditRole.PLATFORM_OPERATOR,
        actor_id="operator-synthetic",
        action=AuditAction.SECRET_LEAK_REJECTED,
        reason_code="security.credential_like_content",
        target_reference="sink-manifest",
    )
    student_view = read_events(log, reader_role=AuditRole.STUDENT, reader_actor_id="student-synthetic")
    operator_view = read_events(log, reader_role=AuditRole.PLATFORM_OPERATOR, reader_actor_id="operator-synthetic")
    return {
        "module": "apps/agent-first/agent_first/audit_log.py",
        "schema_version": AUDIT_SCHEMA_VERSION,
        "genesis_hash": GENESIS_HASH,
        "event_count": len(log.events()),
        "event_ids": [event.event_id for event in log.events()],
        "chain_verified": log.verify_chain(),
        "reason_code_count": len(REASON_CODES),
        "action_count": len(AuditAction),
        "read_policy": [
            {"role": role.value, "allowed_actions": sorted(action.value for action in actions)}
            for role, actions in AUDIT_READ_POLICY.items()
        ],
        "no_read_access_roles": [
            role.value for role in AuditRole if role not in AUDIT_READ_POLICY
        ],
        "student_visible_events": [event.action.value for event in student_view],
        "operator_visible_events": [event.action.value for event in operator_view],
    }


def _self_scan_evidence(evidence: dict) -> dict:
    """Record the Artifact's own result under the contract it documents."""

    findings = scan(evidence, sink=SinkKind.ARTIFACT)
    return {
        "sink": SinkKind.ARTIFACT.value,
        "result": "clean" if not findings else "refused",
        "finding_count": len(findings),
        "refused_locations": sorted({finding.location for finding in findings}),
        "observed_field_name_false_positive": {
            "rule_id": "field.credential_like_name",
            "earlier_section_key": "pcp_13_secret_scan",
            "current_section_key": "pcp_13_sensitive_content_scan",
            "reason": (
                "the field-name rule matches risky substrings, so a section label "
                "containing the word 'secret' is refused as if it held a credential"
            ),
            "resolution": "the section key was renamed; the heuristic stays conservative on purpose",
        },
    }


def main() -> None:
    evidence = {
        "schema_version": "local-safety-contract-evidence/v1",
        "task_id": "R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT-001",
        "scope": "local-synthetic-only",
        "report_date": REPORT_DATE,
        "pcp_13_sensitive_content_scan": _secret_scan_evidence(),
        "pcp_18_log_redaction": _log_redaction_evidence(),
        "pcp_20_audit_log": _audit_evidence(),
    }
    evidence["self_scan"] = _self_scan_evidence(evidence)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    OUTPUT.write_text(text, encoding="utf-8")

    # Self-check: the Artifact must satisfy the same contract it documents.
    require_clean(text, sink=SinkKind.ARTIFACT)
    require_clean(json.loads(text), sink=SinkKind.ARTIFACT)
    print(f"artifact={OUTPUT}")
    print("artifact_self_scan=clean")


if __name__ == "__main__":
    main()
