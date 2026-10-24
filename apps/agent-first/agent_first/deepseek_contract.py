"""No-network DeepSeek Chat Completions contract for the first Gate B probe.

The module formats only the bounded payload required by the selected provider.
It does not contain an endpoint, HTTP client, SDK, raw credential, or live call.
"""

from __future__ import annotations

from .model_gateway import AccessMode, ModelGatewayPolicyError, ModelProfile, ModelUnavailableError, ProviderId
from .scripted_guidance import Guidance


DEEPSEEK_SYNTHETIC_MODEL_ID = "deepseek-flash"
DEEPSEEK_SYNTHETIC_MAX_TOKENS = 600
DEEPSEEK_SYNTHETIC_MAX_INPUT_BYTES = 16_384


def build_deepseek_school_synthetic_profile(*, credential_reference: str) -> ModelProfile:
    """Return the first selected provider profile without storing a credential."""

    return ModelProfile(
        profile_id="deepseek-school-synthetic-guidance-v1",
        provider=ProviderId.DEEPSEEK,
        model_id=DEEPSEEK_SYNTHETIC_MODEL_ID,
        model_version="deepseek-flash/provider-current",
        prompt_version="deepseek-guidance-prompt/v1",
        access_mode=AccessMode.SCHOOL_MANAGED,
        credential_reference=credential_reference,
    )


class DeepSeekChatContractAdapter:
    """Build the provider request shape, then fail closed until separately authorized."""

    def __init__(self, profile: ModelProfile, *, max_tokens: int = DEEPSEEK_SYNTHETIC_MAX_TOKENS) -> None:
        if profile.provider is not ProviderId.DEEPSEEK:
            raise ModelGatewayPolicyError("the DeepSeek adapter requires a DeepSeek profile")
        if profile.access_mode is not AccessMode.SCHOOL_MANAGED:
            raise ModelGatewayPolicyError("the first DeepSeek probe is school-managed only")
        if profile.model_id != DEEPSEEK_SYNTHETIC_MODEL_ID:
            raise ModelGatewayPolicyError("the first DeepSeek probe is allowlisted to deepseek-flash")
        if not 1 <= max_tokens <= DEEPSEEK_SYNTHETIC_MAX_TOKENS:
            raise ModelGatewayPolicyError("max_tokens must stay within the Gate B synthetic cap")
        self.profile = profile
        self.max_tokens = max_tokens
        self.version = f"deepseek-chat-contract/v1:{profile.profile_id}:{profile.model_version}"

    def build_request(self, *, task_id: str, task_goal: str, student_question: str) -> dict[str, object]:
        if not all(isinstance(value, str) for value in (task_id, task_goal, student_question)):
            raise ModelGatewayPolicyError("task-scoped input must be text")
        if not task_id.strip() or not task_goal.strip() or not student_question.strip():
            raise ModelGatewayPolicyError("task-scoped input is required")
        request = {
            "model": self.profile.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a task-scoped education guide. Do not grade, infer ability, "
                        "or claim to detect external AI use. Do not use tools or web search."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Task ID: {task_id}\nTask goal: {task_goal}\n"
                        f"Student question: {student_question.strip()}"
                    ),
                },
            ],
            "thinking": {"type": "disabled"},
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        try:
            content_bytes = sum(
                len(message["content"].encode("utf-8"))
                for message in request["messages"]
            )
        except UnicodeEncodeError as error:
            raise ModelGatewayPolicyError("task-scoped input is not valid UTF-8 text") from error
        if content_bytes > DEEPSEEK_SYNTHETIC_MAX_INPUT_BYTES:
            raise ModelGatewayPolicyError("task-scoped input exceeds the synthetic byte limit")
        return request

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance:
        self.build_request(task_id=task_id, task_goal=task_goal, student_question=student_question)
        raise ModelUnavailableError(
            "MODEL_UNAVAILABLE: the selected DeepSeek synthetic probe has no authorized server runtime"
        )
