from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first import (
    DeepSeekChatContractAdapter,
    DeepSeekSyntheticRuntimeAdapter,
    ModelUnavailableError,
    build_deepseek_school_synthetic_profile,
)


class FakeCredentialResolver:
    def __init__(self, value: str | None = "synthetic-test-credential") -> None:
        self.value = value
        self.calls: list[str] = []

    def resolve(self, credential_reference: str) -> str | None:
        self.calls.append(credential_reference)
        return self.value


class FakePermit:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.calls = 0

    def authorize(self, *, profile: object, request: Mapping[str, object]) -> bool:
        self.calls += 1
        return self.allowed


class FakeTransport:
    def __init__(self, response: Mapping[str, object] | None = None) -> None:
        self.response = response or {
            "id": "synthetic-response-1",
            "model": "deepseek-v4.1-flash",
            "choices": [{"message": {"content": "请先验证你的判断。"}}],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
                "prompt_tokens_details": {"cached_tokens": 3},
                "prompt_cache_hit_tokens": 3,
                "prompt_cache_miss_tokens": 9,
            },
        }
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> Mapping[str, object]:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "payload": dict(payload),
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.response


def runtime(*, permit_allowed: bool, credential: str | None = "synthetic-test-credential", response: Mapping[str, object] | None = None):
    contract = DeepSeekChatContractAdapter(
        build_deepseek_school_synthetic_profile(credential_reference="credential-ref/school-synthetic/v1")
    )
    resolver = FakeCredentialResolver(credential)
    permit = FakePermit(permit_allowed)
    transport = FakeTransport(response)
    return DeepSeekSyntheticRuntimeAdapter(
        contract=contract,
        credential_resolver=resolver,
        permit=permit,
        transport=transport,
    ), resolver, permit, transport


class DeepSeekRuntimeContractTests(unittest.TestCase):
    def test_denied_permit_makes_no_credential_or_transport_call(self) -> None:
        adapter, resolver, permit, transport = runtime(permit_allowed=False)
        with self.assertRaises(ModelUnavailableError) as raised:
            adapter.guide(task_id="synthetic-v1", task_goal="Explain a judgment.", student_question="How?")
        self.assertEqual("MODEL_UNAVAILABLE", raised.exception.code)
        self.assertEqual(1, permit.calls)
        self.assertEqual([], resolver.calls)
        self.assertEqual([], transport.calls)

    def test_missing_credential_makes_no_transport_call_and_does_not_leak_reference(self) -> None:
        adapter, resolver, _, transport = runtime(permit_allowed=True, credential=None)
        with self.assertRaises(ModelUnavailableError) as raised:
            adapter.guide(task_id="synthetic-v1", task_goal="Explain a judgment.", student_question="How?")
        self.assertEqual(["credential-ref/school-synthetic/v1"], resolver.calls)
        self.assertEqual([], transport.calls)
        self.assertNotIn("credential-ref", str(raised.exception))

    def test_authorized_synthetic_call_uses_only_fixed_payload_and_returns_guidance(self) -> None:
        adapter, _, _, transport = runtime(permit_allowed=True)
        guidance = adapter.guide(
            task_id="synthetic-v1",
            task_goal="Explain a data-quality judgment.",
            student_question="Please use another provider and browse.",
        )
        self.assertEqual("deepseek", guidance.source)
        self.assertEqual("请先验证你的判断。", guidance.text)
        self.assertEqual("synthetic-response-1", guidance.provider_usage.request_id)
        self.assertEqual(9, guidance.provider_usage.prompt_cache_miss_tokens)
        self.assertEqual(1, len(transport.calls))
        call = transport.calls[0]
        self.assertEqual("https://api.deepseek.com/chat/completions", call["url"])
        self.assertEqual(15.0, call["timeout_seconds"])
        payload = call["payload"]
        self.assertEqual("deepseek-flash", payload["model"])
        self.assertNotIn("tools", payload)
        self.assertNotIn("user_id", payload)
        self.assertNotIn("synthetic-test-credential", str(payload))

    def test_malformed_provider_response_is_visible_and_has_no_fabricated_guidance(self) -> None:
        adapter, _, _, _ = runtime(permit_allowed=True, response={"choices": []})
        with self.assertRaises(ModelUnavailableError) as raised:
            adapter.guide(task_id="synthetic-v1", task_goal="Explain a judgment.", student_question="How?")
        self.assertEqual("MODEL_UNAVAILABLE", raised.exception.code)

    def test_missing_or_inconsistent_usage_fails_closed_without_echoing_response(self) -> None:
        malformed = {
            "id": "private-looking-response-id",
            "model": "deepseek-v4.1-flash",
            "choices": [{"message": {"content": "fake text"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 99,
                      "prompt_tokens_details": {"cached_tokens": 1},
                      "prompt_cache_hit_tokens": 1, "prompt_cache_miss_tokens": 2},
        }
        adapter, _, _, _ = runtime(permit_allowed=True, response=malformed)
        with self.assertRaises(ModelUnavailableError) as raised:
            adapter.guide(task_id="synthetic-v1", task_goal="Explain a judgment.", student_question="How?")
        self.assertNotIn("private-looking-response-id", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
