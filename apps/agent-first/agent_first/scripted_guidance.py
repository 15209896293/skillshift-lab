"""A deterministic, deliberately local-only guidance adapter for Gate A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from .deepseek_usage import DeepSeekUsage


@dataclass(frozen=True)
class Guidance:
    text: str
    adapter_version: str
    task_id: str
    source: str = "scripted"
    availability: str = "AVAILABLE"
    fallback_from: str | None = None
    provider_usage: DeepSeekUsage | None = None


class GuidanceAdapter(Protocol):
    version: str

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance: ...


class ScriptedGuidanceAdapter:
    """Return bounded task guidance without network, host, or browser tools."""

    version = "scripted-guidance/v1"

    def guide(self, *, task_id: str, task_goal: str, student_question: str) -> Guidance:
        normalized = student_question.strip()
        if not normalized:
            raise ValueError("student_question must not be empty")

        return Guidance(
            task_id=task_id,
            adapter_version=self.version,
            source="scripted",
            text=(
                f"围绕任务“{task_goal}”，先写出你的判断，再用一个可检查的例子验证。"
                "提交时说明：你采用了什么建议、如何验证，以及还有什么不确定之处。"
            ),
        )
