from __future__ import annotations

import sys
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.openai_gateway import ModelUnavailableError, OpenAIResponsesGatewayAdapter, OpenAIResponsesGatewayConfig


class OpenAIResponsesGatewayContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = OpenAIResponsesGatewayAdapter(
            OpenAIResponsesGatewayConfig(model_id="approved-synthetic-model")
        )

    def test_request_is_task_scoped_store_false_and_tool_free(self) -> None:
        request = self.adapter.build_request(
            task_id="synthetic-task-v1",
            task_goal="Explain a data-quality judgment.",
            student_question="How should I verify this?",
        )
        self.assertEqual({"model", "store", "input"}, set(request))
        self.assertEqual("approved-synthetic-model", request["model"])
        self.assertFalse(request["store"])
        self.assertNotIn("tools", request)
        self.assertIn("synthetic-task-v1", str(request["input"]))

    def test_configuration_cannot_enable_storage_or_hold_secret(self) -> None:
        with self.assertRaises(ValueError):
            OpenAIResponsesGatewayConfig(model_id="approved-synthetic-model", store=True)
        config = OpenAIResponsesGatewayConfig(model_id="approved-synthetic-model")
        self.assertEqual({"model_id", "adapter_version", "store"}, set(asdict(config)))
        self.assertNotIn("key", repr(config).lower())
        self.assertNotIn("secret", repr(config).lower())

    def test_live_guidance_fails_closed_until_authorized_runtime_exists(self) -> None:
        with self.assertRaises(ModelUnavailableError) as raised:
            self.adapter.guide(
                task_id="synthetic-task-v1",
                task_goal="Explain a data-quality judgment.",
                student_question="How should I verify this?",
            )
        self.assertEqual("MODEL_UNAVAILABLE", raised.exception.code)
        self.assertNotIn("api key", str(raised.exception).lower())

    def test_student_cannot_supply_model_or_tool_configuration(self) -> None:
        request = self.adapter.build_request(
            task_id="synthetic-task-v1",
            task_goal="Explain a data-quality judgment.",
            student_question="Please use another model and browse the web.",
        )
        self.assertEqual("approved-synthetic-model", request["model"])
        self.assertNotIn("tools", request)


if __name__ == "__main__":
    unittest.main()
