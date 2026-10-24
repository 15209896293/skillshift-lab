"""No-network OpenAI Responses gateway contract for the R0 Gate B preparation.

This module intentionally cannot make an API request. It keeps provider settings
server-owned, creates a safe request shape, and fails closed until a separately
authorized runtime integration exists.
"""

from __future__ import annotations

from dataclasses import dataclass

from .scripted_guidance import Guidance


class ModelUnavailableError(RuntimeError):
    code = "MODEL_UNAVAILABLE"


@dataclass(frozen=True)
class OpenAIResponsesGatewayConfig:
    model_id: str
    adapter_version: str = "openai-responses-gateway/v0"
    store: bool = False

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id must be a server-owned allowlist value")
        if self.store:
            raise ValueError("Gate B requires store=False")


class OpenAIResponsesGatewayAdapter:
    """Build a constrained request or fail closed; no credentials are accepted here."""

    def __init__(self, config: OpenAIResponsesGatewayConfig) -> None:
        self.config = config
        self.version = config.adapter_version

    def build_request(self, *, task_id: str, task_goal: str, student_question: str) -> dict[str, object]:
        if not task_id.strip() or not task_goal.strip() or not student_question.strip():
            raise ValueError("task-scoped input is required")
        return {
            "model": self.config.model_id,
            "store": False,
            "input": (
                "You are a task-scoped education guide. Do not grade, infer ability, "
                "or claim to detect external AI use.\n"
                f"Task ID: {task_id}\nTask goal: {task_goal}\nStudent question: {student_question.strip()}"
            ),
        }

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance:
        self.build_request(task_id=task_id, task_goal=task_goal, student_question=student_question)
        raise ModelUnavailableError(
            "MODEL_UNAVAILABLE: the OpenAI server gateway has not been configured for a live synthetic probe"
        )
