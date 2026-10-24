from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first import DeepSeekUsage, EducationWorkflow, ReviewKind, ScriptedGuidanceAdapter, WorkflowError, build_synthetic_template
from agent_first.scripted_guidance import Guidance


def started_workflow() -> EducationWorkflow:
    workflow = EducationWorkflow(
        teacher_id="teacher-1",
        student_id="student-1",
        template=build_synthetic_template(),
        adapter=ScriptedGuidanceAdapter(),
    )
    workflow.create_and_assign(actor_id="teacher-1")
    workflow.start(actor_id="student-1")
    return workflow


class AgentFirstVerticalSliceTests(unittest.TestCase):
    def test_normal_completion_generates_versioned_manifest(self) -> None:
        workflow = started_workflow()
        guidance = workflow.ask_guidance(actor_id="student-1", question="如何开始？")
        self.assertEqual("scripted-guidance/v1", guidance.adapter_version)
        workflow.submit(
            actor_id="student-1",
            responsibility_kind="verification",
            response_text="我比较两个字段，再依据任务给出的规则验证这一条记录是否一致。",
        )
        workflow.review(actor_id="teacher-1", kind=ReviewKind.ACKNOWLEDGE, reason="验证步骤与判断均已说明")
        manifest = workflow.manifest()
        self.assertEqual("CLOSED", manifest["status"])
        self.assertEqual("agent-first-submission/v1", manifest["schema_version"])
        self.assertGreaterEqual(len(manifest["event_references"]), 6)

    def test_explanation_request_allows_resubmission(self) -> None:
        workflow = started_workflow()
        workflow.submit(
            actor_id="student-1",
            responsibility_kind="explanation",
            response_text="我判断这条记录不一致，因为两个字段的组合与任务规则相互矛盾。",
        )
        workflow.review(actor_id="teacher-1", kind=ReviewKind.REQUEST_EXPLANATION, reason="请说明所用规则的来源")
        workflow.submit(
            actor_id="student-1",
            responsibility_kind="remediation",
            response_text="我补充规则来自任务材料第二项，并按该规则再次检查字段的对应关系。",
        )
        workflow.review(actor_id="teacher-1", kind=ReviewKind.ACKNOWLEDGE, reason="补充后的解释和验证步骤可复核")
        self.assertEqual("CLOSED", workflow.manifest()["status"])
        self.assertEqual(2, workflow.manifest()["student_response"]["revision"])

    def test_empty_or_agent_only_submission_is_rejected(self) -> None:
        workflow = started_workflow()
        with self.assertRaises(WorkflowError):
            workflow.submit(actor_id="student-1", responsibility_kind="verification", response_text="太短")
        with self.assertRaises(WorkflowError):
            workflow.manifest()

    def test_teacher_and_student_permissions_are_separate(self) -> None:
        workflow = started_workflow()
        with self.assertRaises(WorkflowError):
            workflow.review(actor_id="student-1", kind=ReviewKind.ACKNOWLEDGE, reason="学生不应复核")
        with self.assertRaises(WorkflowError):
            workflow.ask_guidance(actor_id="teacher-1", question="教师不应作为学生提问")

    def test_guidance_is_deterministic_and_task_scoped(self) -> None:
        workflow = started_workflow()
        one = workflow.ask_guidance(actor_id="student-1", question="请给一个检查步骤")
        two = workflow.ask_guidance(actor_id="student-1", question="请给一个检查步骤")
        self.assertEqual(one, two)
        self.assertEqual(workflow.template.task_id, one.task_id)
        self.assertNotIn("http", one.text.lower())

    def test_remediation_and_environment_issue_have_visible_return_paths(self) -> None:
        for kind in (ReviewKind.REQUEST_REMEDIATION, ReviewKind.ENVIRONMENT_ISSUE):
            with self.subTest(kind=kind):
                workflow = started_workflow()
                workflow.submit(
                    actor_id="student-1",
                    responsibility_kind="verification",
                    response_text="我通过比对字段和任务规则，验证了这条记录中的不一致关系。",
                )
                workflow.review(actor_id="teacher-1", kind=kind, reason="需要学生处理并重新提交该合成任务")
                self.assertEqual("FEEDBACK_REQUIRED", workflow.status.value)
                workflow.submit(
                    actor_id="student-1",
                    responsibility_kind="remediation",
                    response_text="我补充了检查步骤，并重新说明判断与任务规则之间的关系。",
                )
                workflow.review(actor_id="teacher-1", kind=ReviewKind.ACKNOWLEDGE, reason="重新提交后的任务响应可复核")
                self.assertEqual("CLOSED", workflow.manifest()["status"])

    def test_manifest_records_facts_without_prohibited_inferences(self) -> None:
        workflow = started_workflow()
        workflow.submit(
            actor_id="student-1",
            responsibility_kind="explanation",
            response_text="我说明了检查字段关系的理由，并注明还需要核对的任务材料位置。",
        )
        manifest_text = str(workflow.manifest()).lower()
        for prohibited in ("作弊", "能力", "外部ai", "cheating", "ability"):
            self.assertNotIn(prohibited, manifest_text)

    def test_provider_usage_metadata_never_enters_submission_manifest(self) -> None:
        workflow = started_workflow()
        workflow.interactions.append(Guidance(
            text="synthetic guidance",
            adapter_version="deepseek-runtime-test",
            task_id=workflow.template.task_id,
            source="deepseek",
            provider_usage=DeepSeekUsage("synthetic-secret-id", "synthetic-model", 2, 1, 3, 1, 1),
        ))
        workflow.submit(
            actor_id="student-1",
            responsibility_kind="explanation",
            response_text="我根据任务规则核对了字段，并解释了为什么该记录需要进一步验证。",
        )
        serialized = str(workflow.manifest())
        self.assertNotIn("synthetic-secret-id", serialized)
        self.assertNotIn("prompt_tokens", serialized)
        self.assertNotIn("provider_usage", serialized)
        self.assertNotIn("estimated_cost_fen", serialized)


if __name__ == "__main__":
    unittest.main()
