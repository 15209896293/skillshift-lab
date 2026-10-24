"""No-network domestic multi-model gateway contract for R0 Gate B.

This module deliberately contains no provider SDK, endpoint, credential value, or
network code.  It models only server-owned, allowlisted configuration and the
visible fallback needed before a separately authorized runtime integration.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .scripted_guidance import Guidance, GuidanceAdapter


class ModelGatewayPolicyError(ValueError):
    """Raised when a server-owned model profile violates the R0 policy."""


class ModelUnavailableError(RuntimeError):
    """A visible, recoverable condition; it is never a fabricated model answer."""

    code = "MODEL_UNAVAILABLE"


class ProviderId(str, Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    DOUBAO = "doubao"
    ZHIPU = "zhipu"
    KIMI = "kimi"
    SCHOOL_LOCAL = "school_local"


class AccessMode(str, Enum):
    PLATFORM_BASIC = "platform_basic"
    SCHOOL_MANAGED = "school_managed"
    TEACHER_BYOK = "teacher_byok"
    SCHOOL_LOCAL = "school_local"


@dataclass(frozen=True)
class ModelProfile:
    """Trusted server configuration; no field can contain a raw API key or URL."""

    profile_id: str
    provider: ProviderId
    model_id: str
    model_version: str
    prompt_version: str
    access_mode: AccessMode
    data_classification: str = "synthetic-task-only"
    credential_reference: str | None = None
    tools_allowed: bool = False
    web_search_allowed: bool = False

    def __post_init__(self) -> None:
        for value_name, value in (
            ("profile_id", self.profile_id),
            ("model_id", self.model_id),
            ("model_version", self.model_version),
            ("prompt_version", self.prompt_version),
        ):
            if not value.strip():
                raise ModelGatewayPolicyError(f"{value_name} must be a server-owned non-empty value")
        if not isinstance(self.provider, ProviderId):
            raise ModelGatewayPolicyError("provider must be a pre-approved ProviderId")
        if not isinstance(self.access_mode, AccessMode):
            raise ModelGatewayPolicyError("access_mode must be a server-owned AccessMode")
        if self.tools_allowed or self.web_search_allowed:
            raise ModelGatewayPolicyError("R0 Gate B model profiles must not enable tools or web search")
        if self.access_mode in {AccessMode.SCHOOL_MANAGED, AccessMode.TEACHER_BYOK} and not self.credential_reference:
            raise ModelGatewayPolicyError("managed and BYOK profiles require a server-side credential reference")
        if self.access_mode in {AccessMode.PLATFORM_BASIC, AccessMode.SCHOOL_LOCAL} and self.credential_reference:
            raise ModelGatewayPolicyError("basic and school-local profiles cannot carry a provider credential reference")


class DomesticModelGatewayAdapter:
    """Build a bounded request shape, then fail closed until runtime is authorized."""

    def __init__(self, profile: ModelProfile) -> None:
        self.profile = profile
        self.version = f"domestic-model-gateway/v1:{profile.profile_id}:{profile.model_version}"

    def build_request(self, *, task_id: str, task_goal: str, student_question: str) -> dict[str, str]:
        if not task_id.strip() or not task_goal.strip() or not student_question.strip():
            raise ModelGatewayPolicyError("task-scoped input is required")
        return {
            "provider": self.profile.provider.value,
            "model": self.profile.model_id,
            "model_version": self.profile.model_version,
            "data_classification": self.profile.data_classification,
            "input": (
                "You are a task-scoped education guide. Do not grade, infer ability, "
                "or claim to detect external AI use. Do not use tools or web search.\n"
                f"Task ID: {task_id}\nTask goal: {task_goal}\nStudent question: {student_question.strip()}"
            ),
        }

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance:
        self.build_request(task_id=task_id, task_goal=task_goal, student_question=student_question)
        raise ModelUnavailableError(
            "MODEL_UNAVAILABLE: no domestic provider runtime or credential has been authorized for this profile"
        )


class FallbackGuidanceAdapter:
    """Use the deterministic adapter only after a visible unavailable condition."""

    def __init__(self, *, primary: GuidanceAdapter, fallback: GuidanceAdapter) -> None:
        self.primary = primary
        self.fallback = fallback
        self.version = f"fallback-guidance/v1:{primary.version}->{fallback.version}"

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance:
        try:
            return self.primary.guide(
                task_id=task_id,
                task_goal=task_goal,
                student_question=student_question,
            )
        except ModelUnavailableError:
            fallback_guidance = self.fallback.guide(
                task_id=task_id,
                task_goal=task_goal,
                student_question=student_question,
            )
            return replace(
                fallback_guidance,
                availability=ModelUnavailableError.code,
                fallback_from=self.primary.version,
            )
