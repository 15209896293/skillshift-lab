"""Server-runtime seam for an authorized synthetic DeepSeek probe.

No credential is stored here.  A future server must inject both a secret resolver
and an atomic budget permit.  Without both, this adapter fails closed before any
transport call.  Tests use fakes only; this module has never sent a live request.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .deepseek_contract import DeepSeekChatContractAdapter
from .model_gateway import ModelGatewayPolicyError, ModelProfile, ModelUnavailableError
from .scripted_guidance import Guidance
from .deepseek_usage import parse_deepseek_usage


DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"


class CredentialResolver(Protocol):
    """Future server-owned secret store; it returns a value only at invocation time."""

    def resolve(self, credential_reference: str) -> str | None: ...


class SyntheticProbePermit(Protocol):
    """Future atomic budget/authorization service; False means no provider request."""

    def authorize(self, *, profile: ModelProfile, request: Mapping[str, object]) -> bool: ...


class JsonTransport(Protocol):
    """Transport boundary. Production transport is intentionally not implemented here."""

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> Mapping[str, object]: ...


class DeepSeekSyntheticRuntimeAdapter:
    """Call DeepSeek only after an injected server permit and synthetic-only validation."""

    def __init__(
        self,
        *,
        contract: DeepSeekChatContractAdapter,
        credential_resolver: CredentialResolver,
        permit: SyntheticProbePermit,
        transport: JsonTransport,
        timeout_seconds: float = 15.0,
    ) -> None:
        if not 0 < timeout_seconds <= 30:
            raise ModelGatewayPolicyError("synthetic runtime timeout must be between 0 and 30 seconds")
        self.contract = contract
        self.credential_resolver = credential_resolver
        self.permit = permit
        self.transport = transport
        self.timeout_seconds = timeout_seconds
        self.version = f"deepseek-synthetic-runtime/v1:{contract.version}"

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance:
        profile = self.contract.profile
        if profile.data_classification != "synthetic-task-only":
            raise ModelGatewayPolicyError("the first hosted DeepSeek probe accepts synthetic-task-only data")
        request = self.contract.build_request(
            task_id=task_id,
            task_goal=task_goal,
            student_question=student_question,
        )
        if not self.permit.authorize(profile=profile, request=request):
            raise ModelUnavailableError("MODEL_UNAVAILABLE: synthetic probe permit or budget is unavailable")
        if not profile.credential_reference:
            raise ModelUnavailableError("MODEL_UNAVAILABLE: no server credential reference is configured")
        credential = self.credential_resolver.resolve(profile.credential_reference)
        if not credential:
            raise ModelUnavailableError("MODEL_UNAVAILABLE: server credential is unavailable or revoked")
        response = self.transport.post_json(
            url=DEEPSEEK_CHAT_COMPLETIONS_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credential}",
            },
            payload=request,
            timeout_seconds=self.timeout_seconds,
        )
        text = self._response_text(response)
        try:
            usage = parse_deepseek_usage(response)
        except ValueError as error:
            raise ModelUnavailableError("MODEL_UNAVAILABLE: provider usage metadata is malformed") from error
        return Guidance(
            task_id=task_id,
            adapter_version=self.version,
            text=text,
            source="deepseek",
            provider_usage=usage,
        )

    @staticmethod
    def _response_text(response: Mapping[str, object]) -> str:
        try:
            choices = response["choices"]
            first_choice = choices[0]  # type: ignore[index]
            message = first_choice["message"]  # type: ignore[index]
            text = message["content"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as error:
            raise ModelUnavailableError("MODEL_UNAVAILABLE: provider response is malformed") from error
        if not isinstance(text, str) or not text.strip():
            raise ModelUnavailableError("MODEL_UNAVAILABLE: provider response has no guidance text")
        return text.strip()
