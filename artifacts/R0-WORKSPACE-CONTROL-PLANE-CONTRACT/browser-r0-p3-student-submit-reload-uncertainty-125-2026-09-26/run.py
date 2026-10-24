"""Task 125: observe student UI after a committed submission receipt is lost and page reloads."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
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
    origin = f"http://127.0.0.1:{port}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    requests: list[dict] = []
    dropped = {"value": False}
    checks: dict[str, bool] = {}
    screenshots: list[str] = []
    assignment_id = None
    workspace_id = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            teacher = browser.new_page(viewport={"width": 1280, "height": 900})
            student = browser.new_page(viewport={"width": 390, "height": 844})

            def capture(response):
                request = response.request
                parsed = urlsplit(response.url)
                requests.append({"method": request.method, "path": parsed.path, "status": response.status})

            teacher.on("response", capture)
            student.on("response", capture)

            teacher.goto(origin + "/demo/teacher/", wait_until="networkidle")
            teacher.locator("[data-action='use-template']").click()
            teacher.locator("#task-title").fill("回执丢失后刷新状态核验")
            teacher.locator("#task-goal").fill("检查固定合成订单中的金额关系，并说明验证依据。")
            teacher.locator("#task-responsibility").fill("说明核对步骤与仍不确定的规则。")
            teacher.locator("#task-deliverable").fill("提交合成快照和核验说明。")
            teacher.locator("[data-action='simulate-publish']").click()
            teacher.get_by_text("本机合成 API 已发布任务", exact=False).wait_for(timeout=10000)
            assignment_id = next(reversed(api.store.assignments))

            def lose_only_first_browser_receipt(route):
                request = route.request
                response = route.fetch()
                if request.method == "POST" and re.search(r"/api/v1/demo/student/workspaces/[^/]+/submissions$", request.url) and not dropped["value"]:
                    body = response.json()
                    workspace_id = body["data"]["submission"]["workspace_id"]
                    requests.append({
                        "method": request.method,
                        "path": urlsplit(request.url).path,
                        "status": response.status,
                        "idempotency_key": request.headers.get("idempotency-key"),
                        "if_match": request.headers.get("if-match"),
                        "body": request.post_data,
                        "submission_id": body["data"]["submission"]["id"],
                        "response_dropped_after_server_commit": True,
                    })
                    dropped["value"] = True
                    route.abort("failed")
                else:
                    requests.append({"method": request.method, "path": urlsplit(request.url).path, "status": response.status})
                    route.fulfill(response=response)

            student.route("**/api/v1/demo/student/workspaces/*/submissions", lose_only_first_browser_receipt)
            student.goto(origin + "/demo/student/", wait_until="networkidle")
            student.locator(f"#task-picker option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            student.locator("#task-picker").select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            student.locator("[data-action='open-submit']").click()
            student.locator("#submission-note").fill("固定合成核对说明：逐项检查金额关系并记录待确认规则。")
            student.locator("#confirm-submit").click()
            student.locator("#api-state").filter(has_text="提交结果暂未确认").wait_for(timeout=10000)
            first_unknown_text = student.locator("#api-state").inner_text()
            checks["server_committed_submission_but_browser_receipt_was_lost"] = (
                dropped["value"] and len(api.store.assignments[assignment_id].workspace.submissions) == 1
            )
            checks["same_page_shows_unknown_and_same_request_retry"] = (
                "提交结果暂未确认" in first_unknown_text
                and student.locator("#confirm-submit").inner_text() == "重试同一提交"
            )
            student.screenshot(path=str(OUT / "before-refresh-unknown-390px.png"), full_page=True)
            screenshots.append("before-refresh-unknown-390px.png")

            before_reload_posts = sum(1 for item in requests if item.get("method") == "POST" and item.get("path", "").endswith("/submissions"))
            student.unroute("**/api/v1/demo/student/workspaces/*/submissions", lose_only_first_browser_receipt)
            student.reload(wait_until="networkidle")
            student.locator(f"#task-picker option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            after_reload_posts = sum(1 for item in requests if item.get("method") == "POST" and item.get("path", "").endswith("/submissions"))
            checks["reload_did_not_automatically_post_again"] = before_reload_posts == after_reload_posts == 1
            checks["reload_did_not_silently_select_task"] = student.locator("#task-picker").input_value() == ""
            student.locator("#task-picker").select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            latest_text = student.locator("#latest-submission-state").inner_text()
            checks["latest_readback_is_caveated_as_not_proving_original_request"] = (
                "不能证明某次回执未知的提交请求就是这条记录" in latest_text
            )
            checks["latest_submission_is_visible_after_explicit_reselection"] = (
                "submission-1" in latest_text and "第 1 版" in latest_text
                and "等待教师复核" in student.locator("#task-picker-state").inner_text()
            )
            checks["submission_control_not_available_in_review_required_state"] = student.locator("[data-action='open-submit']").is_disabled()
            checks["student_reload_view_has_no_horizontal_overflow"] = student.evaluate("document.documentElement.scrollWidth === innerWidth")
            student.screenshot(path=str(OUT / "after-refresh-explicit-readback-390px.png"), full_page=True)
            screenshots.append("after-refresh-explicit-readback-390px.png")

            workspace = api.store.assignments[assignment_id].workspace
            submission_posts = [item for item in requests if item.get("method") == "POST" and item.get("path", "").endswith("/submissions")]
            checks["exactly_one_submission_exists_and_no_new_idempotency_key_was_minted"] = (
                len(workspace.submissions) == 1 and len(submission_posts) == 1
                and bool(submission_posts[0].get("idempotency_key"))
            )
            checks["workspace_remains_review_required_with_one_event_linked_submission"] = (
                workspace.state == "REVIEW_REQUIRED" and len(workspace.submissions) == 1
            )
            result = {
                "task_id": "R0-P3-125-STUDENT-SUBMISSION-RELOAD-UNCERTAINTY",
                "browser": "Microsoft Edge via Playwright",
                "origin": {"host": host, "port": port},
                "synthetic_in_memory_only": True,
                "external_calls": 0,
                "fixture_code_executed": False,
                "assignment_id": assignment_id,
                "workspace_id": workspace.workspace_id,
                "checks": checks,
                "submission_post_records": submission_posts,
                "workspace_postcondition": {
                    "state": workspace.state,
                    "revision": workspace.revision,
                    "submission_count": len(workspace.submissions),
                    "submission_ids": [item["id"] for item in workspace.submissions],
                },
                "request_count": len(requests),
                "requests": requests,
                "screenshots": screenshots,
                "pass": all(checks.values()),
            }
            raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            (OUT / "browser-run.json").write_bytes(raw)
            if not result["pass"]:
                raise AssertionError(json.dumps(checks, ensure_ascii=False))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"artifact_sha256={sha256(raw).hexdigest().upper()}")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive(), "loopback server thread did not stop"
        assert server.socket.fileno() < 0, "loopback listener remained open"


if __name__ == "__main__":
    main()
