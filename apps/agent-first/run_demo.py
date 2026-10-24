"""Run four bounded synthetic Agent-first workflow cases and save an Artifact."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_first import EducationWorkflow, ReviewKind, ScriptedGuidanceAdapter, build_synthetic_template


def _workflow() -> EducationWorkflow:
    workflow = EducationWorkflow(
        teacher_id="teacher-synthetic",
        student_id="student-synthetic",
        template=build_synthetic_template(),
        adapter=ScriptedGuidanceAdapter(),
    )
    workflow.create_and_assign(actor_id="teacher-synthetic")
    workflow.start(actor_id="student-synthetic")
    workflow.ask_guidance(actor_id="student-synthetic", question="我应如何验证我的判断？")
    return workflow


def _case(name: str, first_kind: ReviewKind, final_kind: ReviewKind | None = None) -> dict[str, object]:
    workflow = _workflow()
    workflow.submit(
        actor_id="student-synthetic",
        responsibility_kind="verification",
        response_text="我先比对记录中的两个字段，再用原始规则核对这一条记录是否一致。",
    )
    workflow.review(actor_id="teacher-synthetic", kind=first_kind, reason=f"{name} 的合成教师复核理由")
    if final_kind is not None:
        workflow.submit(
            actor_id="student-synthetic",
            responsibility_kind="remediation",
            response_text="我补充了规则来源，并重新核对字段关系；现在可说明原判断为何成立。",
        )
        workflow.review(actor_id="teacher-synthetic", kind=final_kind, reason="补正后的合成复核理由")
    return {"case": name, "manifest": workflow.manifest()}


def main() -> None:
    cases = [
        _case("normal_completion", ReviewKind.ACKNOWLEDGE),
        _case("explanation_requested", ReviewKind.REQUEST_EXPLANATION, ReviewKind.ACKNOWLEDGE),
        _case("remediation_requested", ReviewKind.REQUEST_REMEDIATION, ReviewKind.ACKNOWLEDGE),
        _case("environment_issue", ReviewKind.ENVIRONMENT_ISSUE, ReviewKind.ACKNOWLEDGE),
    ]
    output = ROOT / "artifacts" / "R0-AGENT-FIRST-VERTICAL-SLICE" / "demo.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"schema_version": "agent-first-demo/v1", "cases": cases}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
