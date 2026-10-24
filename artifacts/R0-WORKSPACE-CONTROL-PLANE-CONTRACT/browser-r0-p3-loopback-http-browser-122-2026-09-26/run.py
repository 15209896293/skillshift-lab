"""Task 122: run a bounded real-browser vertical flow against loopback WSGI."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, make_server

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))
from agent_first.workspace_api import WorkspaceApi  # noqa: E402
from agent_first.workspace_wsgi import WorkspaceWsgiApp  # noqa: E402

OUT = Path(__file__).resolve().parent


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


def main() -> None:
    api = WorkspaceApi()
    server = make_server("127.0.0.1", 0, WorkspaceWsgiApp(api), handler_class=QuietHandler)
    host, port = server.server_address[:2]
    assert host == "127.0.0.1"
    base = f"http://127.0.0.1:{port}"
    server_thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    server_thread.start()
    trace: list[dict] = []
    checks: dict[str, bool] = {}
    assignment_id = None
    title = "回环浏览器合成闭环核验"
    reason = "请补充订单金额核对依据并说明仍不确定的业务规则。"
    reason_second = "第二轮请补充对边界订单的核验步骤。"
    screenshots: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            teacher = browser.new_page(viewport={"width": 1280, "height": 900})
            student = browser.new_page(viewport={"width": 390, "height": 844})

            def record_response(response):
                request = response.request
                parsed = urlsplit(response.url)
                if parsed.netloc != f"127.0.0.1:{port}":
                    trace.append({"external_or_wrong_origin": response.url, "status": response.status})
                    return
                entry = {"method": request.method, "path": parsed.path, "status": response.status}
                if request.method == "POST":
                    entry["idempotency_key_sent"] = bool(request.headers.get("idempotency-key"))
                    entry["if_match_sent"] = bool(request.headers.get("if-match"))
                    if parsed.path.endswith("/teacher/assignments") and response.status == 201:
                        try:
                            entry["assignment_id"] = response.json()["data"]["id"]
                        except Exception:
                            pass
                trace.append(entry)

            teacher.on("response", record_response)
            student.on("response", record_response)

            # Teacher creates and publishes the task through the actual page UI.
            teacher.goto(base + "/demo/teacher/", wait_until="networkidle")
            teacher.locator("[data-action='use-template']").click()
            teacher.locator("#task-title").fill(title)
            teacher.locator("#task-goal").fill("核对合成订单金额和数量、单价关系，并说明检查依据。")
            teacher.locator("#task-responsibility").fill("指出异常、写明验证步骤，并说明尚未确定的规则。")
            teacher.locator("#task-deliverable").fill("提交合成项目快照和验证说明。")
            teacher.locator("[data-action='simulate-publish']").click()
            teacher.get_by_text("本机合成 API 已发布任务", exact=False).wait_for(timeout=10000)
            assignment_id = next((item.get("assignment_id") for item in trace if item.get("assignment_id")), None)
            assert assignment_id, "create assignment HTTP receipt was not observed"
            checks["teacher_created_and_published_in_browser"] = True

            # Student explicitly selects the published task; selecting it starts its workspace.
            student.goto(base + "/demo/student/", wait_until="networkidle")
            picker = student.locator("#task-picker")
            picker.locator(f"option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            picker.select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            checks["student_explicitly_selected_and_started"] = student.locator("#task-title").inner_text() == title
            checks["student_state_in_progress"] = "进行中" in student.locator("#task-state").inner_text()
            checks["student_390px_no_horizontal_overflow"] = student.evaluate("document.documentElement.scrollWidth === innerWidth")
            student.screenshot(path=str(OUT / "student-selected-started-390px.png"), full_page=True)
            screenshots.append("student-selected-started-390px.png")

            # Submit from the student UI.
            editor = student.locator("#code-editor")
            editor.fill(editor.input_value() + "\n# 本轮由学生在合成页面添加的说明\n")
            student.locator("[data-action='open-submit']").click()
            student.locator("#submission-note").fill("我核对了样例订单金额关系，并记录仍需教师确认的规则。")
            student.locator("#confirm-submit").click()
            student.get_by_text("提交已由本机合成 API 接收", exact=False).wait_for(timeout=10000)
            checks["student_submission_v1_confirmed_in_browser"] = "等待教师复核" in student.locator("#task-state").inner_text()

            # Teacher explicitly selects the task and requests the specified remediation action.
            teacher.locator("[data-view='reviews']").click()
            choices = teacher.locator("#review-task-list [data-review-assignment]")
            choices.wait_for(timeout=10000)
            teacher.locator(f"#review-task-list [data-review-assignment='{assignment_id}']").click()
            teacher.locator("#review-details:not([hidden])").wait_for(timeout=10000)
            checks["teacher_selected_task_and_saw_submission"] = title in teacher.locator("#review-details").inner_text()
            teacher.locator("#feedback-reason").fill(reason)
            teacher.locator("[data-review='remediation']").click()
            teacher.get_by_text("补正要求已记录", exact=False).wait_for(timeout=10000)
            checks["teacher_remediation_reason_confirmed"] = reason in teacher.locator("#remediation-status").inner_text()
            teacher.screenshot(path=str(OUT / "teacher-remediation-confirmed-1280px.png"), full_page=True)
            screenshots.append("teacher-remediation-confirmed-1280px.png")

            # Student reloads and explicitly reselects; verify the remediation reason and submit v2.
            student.reload(wait_until="networkidle")
            picker = student.locator("#task-picker")
            picker.locator(f"option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            picker.select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            remediation = student.locator("#remediation-state")
            student.get_by_text(reason, exact=False).wait_for(timeout=10000)
            checks["student_saw_matching_remediation_reason"] = reason in remediation.inner_text()
            student.locator("#code-editor").fill(student.locator("#code-editor").input_value() + "\n# 补正：增加金额关系核对说明\n")
            student.locator("[data-action='open-submit']").click()
            student.locator("#submission-note").fill("我按反馈补充了金额核对依据，并保留尚未确定的业务规则。")
            student.locator("#confirm-submit").click()
            student.get_by_text("提交已由本机合成 API 接收", exact=False).wait_for(timeout=10000)
            checks["student_resubmission_v2_confirmed_in_browser"] = "等待教师复核" in student.locator("#task-state").inner_text()
            checks["student_390px_after_remediation_no_horizontal_overflow"] = student.evaluate("document.documentElement.scrollWidth === innerWidth")
            student.screenshot(path=str(OUT / "student-remediated-resubmitted-390px.png"), full_page=True)
            screenshots.append("student-remediated-resubmitted-390px.png")

            # A second, distinct remediation is tied to submission v2.
            teacher.reload(wait_until="networkidle")
            teacher.locator("[data-view='reviews']").click()
            teacher.locator(f"#review-task-list [data-review-assignment='{assignment_id}']").wait_for(timeout=10000)
            teacher.locator(f"#review-task-list [data-review-assignment='{assignment_id}']").click()
            teacher.locator("#review-details:not([hidden])").wait_for(timeout=10000)
            checks["teacher_selected_resubmission_v2_for_second_remediation"] = "第 2 版" in teacher.locator("#review-details").inner_text()
            teacher.locator("#feedback-reason").fill(reason_second)
            teacher.locator("[data-review='remediation']").click()
            teacher.get_by_text("补正要求已记录", exact=False).wait_for(timeout=10000)
            checks["second_remediation_recorded_against_v2"] = reason_second in teacher.locator("#remediation-status").inner_text()

            # Student explicitly reads both remediation records, then submits version 3.
            student.reload(wait_until="networkidle")
            picker = student.locator("#task-picker")
            picker.locator(f"option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            picker.select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            reason_history = student.locator("#remediation-state").inner_text()
            checks["student_saw_current_open_remediation_reason"] = reason_second in reason_history
            student.locator("#code-editor").fill(student.locator("#code-editor").input_value() + "\n# 第二轮补正：补充边界订单核验步骤\n")
            student.locator("[data-action='open-submit']").click()
            student.locator("#submission-note").fill("我已回应第二轮反馈，补充边界订单核验步骤。")
            student.locator("#confirm-submit").click()
            student.get_by_text("提交已由本机合成 API 接收", exact=False).wait_for(timeout=10000)
            checks["student_submitted_version_3"] = "等待教师复核" in student.locator("#task-state").inner_text()

            # Teacher reloads so the current v3 queue is authoritative, then explicitly ACKs it.
            teacher.reload(wait_until="networkidle")
            teacher.locator("[data-view='reviews']").click()
            teacher.locator(f"#review-task-list [data-review-assignment='{assignment_id}']").wait_for(timeout=10000)
            teacher.locator(f"#review-task-list [data-review-assignment='{assignment_id}']").click()
            teacher.locator("#review-details:not([hidden])").wait_for(timeout=10000)
            checks["teacher_selected_resubmission_v3"] = "第 3 版" in teacher.locator("#review-details").inner_text()
            teacher.locator("#feedback-reason").fill("已复核第三版补正提交中的核对说明和合成快照。")
            teacher.locator("[data-review='approve']").click()
            teacher.locator("#remediation-status").filter(has_text="已关闭").wait_for(timeout=10000)
            checks["teacher_acknowledged_in_browser"] = True
            remediation_display = teacher.locator("#remediation-status").inner_text()
            checks["teacher_preserved_old_response_and_closed_current_one"] = "已收到学生回应" in remediation_display and "API 记录为已关闭" in remediation_display
            checks["teacher_1280px_no_horizontal_overflow"] = teacher.evaluate("document.documentElement.scrollWidth === innerWidth")
            teacher.screenshot(path=str(OUT / "teacher-acknowledged-1280px.png"), full_page=True)
            screenshots.append("teacher-acknowledged-1280px.png")

            student.reload(wait_until="networkidle")
            picker = student.locator("#task-picker")
            picker.locator(f"option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            picker.select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            checks["student_read_back_closed_state_in_browser"] = "本轮已结束" in student.locator("#task-state").inner_text()
            student.screenshot(path=str(OUT / "student-closed-state-390px.png"), full_page=True)
            screenshots.append("student-closed-state-390px.png")

            # Read authoritative postconditions through the API after browser actions.
            assignment = api.store.assignments[assignment_id]
            workspace = assignment.workspace
            checks["api_postcondition_closed_accepted_three_versions"] = (
                workspace is not None and workspace.state == "CLOSED"
                and len(workspace.submissions) == 3
                and workspace.submissions[-1]["state"] == "ACCEPTED"
                and len(workspace.reviews) == 3
                and workspace.reviews[0]["kind"] == "REQUEST_REMEDIATION"
                and workspace.reviews[1]["kind"] == "REQUEST_REMEDIATION"
                and workspace.reviews[-1]["kind"] == "ACKNOWLEDGE"
                and len(workspace.remediations) == 2
                and workspace.remediations[0]["state"] == "RESPONDED"
                and workspace.remediations[0]["response_submission_id"] == "submission-2"
                and workspace.remediations[1]["state"] == "CLOSED"
                and workspace.remediations[1]["response_submission_id"] == "submission-3"
            )
            checks["execution_remained_disabled"] = workspace is not None and assignment.task["execution_enabled"] is False
            checks["all_browser_requests_used_loopback_origin"] = not any("external_or_wrong_origin" in item for item in trace)
            mutations = [item for item in trace if item.get("method") == "POST"]
            checks["all_browser_mutations_used_idempotency_and_revision"] = all(
                item.get("idempotency_key_sent")
                and (item.get("if_match_sent") or item["path"].endswith("/teacher/assignments"))
                for item in mutations
            )
            result = {
                "task_id": "R0-P3-122-LOOPBACK-HTTP-BROWSER-VERTICAL",
                "listener": {"host": host, "port": port, "actual_address": list(server.socket.getsockname()[:2])},
                "synthetic_only": True,
                "external_calls": 0,
                "fixture_python_executed": False,
                "assignment_id": assignment_id,
                "checks": checks,
                "browser_request_count": len(trace),
                "browser_requests": trace,
                "screenshots": screenshots,
                "pass": all(checks.values()),
            }
            raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            (OUT / "browser-http-run.json").write_bytes(raw)
            if not result["pass"]:
                raise AssertionError(json.dumps(checks, ensure_ascii=False))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"artifact_sha256={sha256(raw).hexdigest().upper()}")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
        assert not server_thread.is_alive(), "loopback server thread did not stop"
        assert server.socket.fileno() < 0, "loopback listener socket remained open"


if __name__ == "__main__":
    main()
