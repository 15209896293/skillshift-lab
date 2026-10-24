"""Local pre-write guard against credential-shaped content reaching a durable sink.

Synthetic-only: this module holds no credential value, endpoint, HTTP client, or
network capability.  It is a bounded static check used before writing a Manifest,
log record, error message, or Artifact.  It is not a production secret manager and
it makes no claim that a scanned value is safe.

Design rules:
- A finding never carries the matched value, so the guard cannot itself leak.
- A refusal message carries only the rule ID and a value-scrubbed location.
- Unknown shapes are walked, not trusted; nothing is silently skipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any


REDACTION_PLACEHOLDER = "[redacted]"


class SinkKind(str, Enum):
    """Durable or observable destinations that must never receive a credential."""

    MANIFEST = "manifest"
    LOG = "log"
    ERROR = "error"
    ARTIFACT = "artifact"


class SecretKind(str, Enum):
    PROVIDER_API_KEY = "provider_api_key"
    CLOUD_ACCESS_KEY = "cloud_access_key"
    PRIVATE_KEY_BLOCK = "private_key_block"
    BEARER_TOKEN = "bearer_token"
    PASSWORD_ASSIGNMENT = "password_assignment"
    CREDENTIAL_LIKE_FIELD = "credential_like_field"


@dataclass(frozen=True)
class ScanFinding:
    """A refusal record.  It deliberately never carries the matched value."""

    sink: SinkKind
    kind: SecretKind
    rule_id: str
    location: str


class SecretLeakDetected(ValueError):
    """Raised before a credential-shaped value reaches a sink."""


# Field names that are benign even though they contain a risky substring.
_BENIGN_FIELD_NAMES = frozenset({"max_tokens", "token_budget", "token_count", "token_limit"})

# Compound or whole-word markers that make a field name credential-like.
_RISKY_FIELD_MARKERS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "accesskey",
    "access_key",
    "api_key",
    "apikey",
    "private_key",
    "privatekey",
    "credential",
    "token",
)

# Value shapes.  Every pattern is a synthetic detection rule, never a real key.
_VALUE_RULES: tuple[tuple[str, SecretKind, re.Pattern[str]], ...] = (
    ("value.provider_api_key", SecretKind.PROVIDER_API_KEY, re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}")),
    ("value.cloud_access_key", SecretKind.CLOUD_ACCESS_KEY, re.compile(r"\b(?:AKIA|LTAI)[A-Za-z0-9]{12,}")),
    ("value.private_key_block", SecretKind.PRIVATE_KEY_BLOCK, re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("value.bearer_token", SecretKind.BEARER_TOKEN, re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}")),
    (
        "value.password_assignment",
        SecretKind.PASSWORD_ASSIGNMENT,
        re.compile(r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*\S{4,}"),
    ),
)


def _normalize_field_name(name: str) -> str:
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def _is_credential_like_field(name: str) -> bool:
    normalized = _normalize_field_name(name)
    if normalized in _BENIGN_FIELD_NAMES:
        return False
    return any(marker in normalized for marker in _RISKY_FIELD_MARKERS)


def scrub_location(location: str) -> str:
    """Return a location string with any credential-shaped substring removed."""

    scrubbed = location
    for _rule_id, _kind, pattern in _VALUE_RULES:
        scrubbed = pattern.sub(REDACTION_PLACEHOLDER, scrubbed)
    return scrubbed


def _scan_text(text: str, *, sink: SinkKind, location: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    safe_location = scrub_location(location)
    for rule_id, kind, pattern in _VALUE_RULES:
        if pattern.search(text):
            findings.append(ScanFinding(sink=sink, kind=kind, rule_id=rule_id, location=safe_location))
    return findings


def _walk(value: Any, *, sink: SinkKind, location: str, findings: list[ScanFinding]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{location}.{key}"
            if _is_credential_like_field(key):
                findings.append(
                    ScanFinding(
                        sink=sink,
                        kind=SecretKind.CREDENTIAL_LIKE_FIELD,
                        rule_id="field.credential_like_name",
                        location=scrub_location(child),
                    )
                )
            _walk(nested, sink=sink, location=child, findings=findings)
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _walk(nested, sink=sink, location=f"{location}[{index}]", findings=findings)
    elif isinstance(value, str):
        findings.extend(_scan_text(value, sink=sink, location=location))


def scan(value: Any, *, sink: SinkKind, location: str = "$") -> tuple[ScanFinding, ...]:
    """Return every refusal finding for a value, without ever echoing a value."""

    if not isinstance(sink, SinkKind):
        raise TypeError("sink must be a SinkKind")
    findings: list[ScanFinding] = []
    _walk(value, sink=sink, location=location, findings=findings)
    return tuple(findings)


def require_clean(value: Any, *, sink: SinkKind, location: str = "$") -> None:
    """Raise SecretLeakDetected if a value carries credential-shaped content."""

    findings = scan(value, sink=sink, location=location)
    if findings:
        rules = ", ".join(sorted({finding.rule_id for finding in findings}))
        raise SecretLeakDetected(f"{sink.value} refused: credential-shaped content detected [{rules}]")


def describe_findings(findings: tuple[ScanFinding, ...]) -> list[dict[str, str]]:
    """Render findings for an Artifact.  Values are absent by construction."""

    return [
        {
            "sink": finding.sink.value,
            "kind": finding.kind.value,
            "rule_id": finding.rule_id,
            "location": finding.location,
        }
        for finding in findings
    ]
