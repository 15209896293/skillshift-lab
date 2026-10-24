"""Task126: verify pre-commit submit failure and isolated latest-read retry after reload."""

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
    origin = f"http://{host}:{port}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    requests: list[dict] = []
    injected = {"post": False, "latest_503": False, "after_reload": False}
    checks: dict[str, bool] = {}
    assignment_id = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            teacher = browser.new_page(viewport={"width": 1280, "height": 900})
            student = browser.new_page(viewport={"width": 390, "height": 844})
            for page in (teacher, student):
                def capture(response):
                    path = urlsplit(response.url).path
                    if path.endswith("/submissions/latest") and response.status == 503 and injected["latest_503"]:
                        return  # The injected boundary failure is recorded once by its route handler.
                    requests.append({"method": response.request.method, "path": path, "status": response.status})

                page.on("response", capture)

            teacher.goto(origin + "/demo/teacher/", wait_until="networkidle")
            teacher.locator("[data-action='use-template']").click()
            teacher.locator("#task-title").fill("提交未到达与最近记录重读核验")
            teacher.locator("#task-goal").fill("核对固定合成订单金额关系并记录依据。")
            teacher.locator("#task-responsibility").fill("说明核对过程和未确认规则。")
            teacher.locator("#task-deliverable").fill("提交有限合成文本快照和说明。")
            teacher.locator("[data-action='simulate-publish']").click()
            teacher.get_by_text("本机合成 API 已发布任务", exact=False).wait_for(timeout=10000)
            assignment_id = next(reversed(api.store.assignments))

            def inject_faults(route):
                request = route.request
                path = urlsplit(request.url).path
                if request.method == "POST" and path.endswith("/submissions") and not injected["post"]:
                    injected["post"] = True
                    requests.append({"method": "POST", "path": path, "injected": "aborted_before_api"})
                    route.abort("failed")
                    return
                if request.method == "GET" and path.endswith("/submissions/latest") and injected["after_reload"] and not injected["latest_503"]:
                    injected["latest_503"] = True
                    requests.append({"method": "GET", "path": path, "status": 503, "injected": "browser_boundary"})
                    route.fulfill(status=503, content_type="application/json", body=json.dumps({"code": "synthetic_read_failure"}))
                    return
                response = route.fetch()
                requests.append({"method": request.method, "path": path, "status": response.status})
                route.fulfill(response=response)

            student.route("**/api/v1/demo/student/workspaces/*/submissions**", inject_faults)
            student.goto(origin + "/demo/student/", wait_until="networkidle")
            student.locator(f"#task-picker option[value='{assignment_id}']").wait_for(state="attached", timeout=10000)
            student.locator("#task-picker").select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            student.locator("[data-action='open-submit']").click()
            student.locator("#submission-note").fill("合成核对完成，保留未确认规则。")
            student.locator("#confirm-submit").click()
            student.locator("#api-state").filter(has_text="提交结果暂未确认").wait_for(timeout=10000)
            checks["post_was_aborted_before_api_commit"] = injected["post"] and len(api.store.assignments[assignment_id].workspace.submissions) == 0
            checks["first_page_unknown_did_not_claim_submission_success"] = "提交结果暂未确认" in student.locator("#api-state").inner_text()
            student.screenshot(path=str(OUT / "precommit-and-read-failure-390px.png"), full_page=True)

            submission_post_count = sum(item.get("method") == "POST" and item.get("path", "").endswith("/submissions") for item in requests)
            injected["after_reload"] = True
            student.reload(wait_until="networkidle")
            checks["reload_did_not_auto_select_or_resend"] = (
                student.locator("#task-picker").input_value() == ""
                and sum(item.get("method") == "POST" and item.get("path", "").endswith("/submissions") for item in requests) == submission_post_count == 1
            )
            student.locator("#task-picker").select_option(assignment_id)
            student.locator(".work-area:not([hidden])").wait_for(timeout=10000)
            read_region = student.locator("#latest-submission-state")
            read_region.filter(has_text="最近提交读取失败，当前状态未知").wait_for(timeout=10000)
            checks["latest_read_region_is_explicitly_unknown_with_its_own_retry"] = (
                read_region.get_attribute("data-read-state") == "unknown"
                and read_region.get_by_role("button", name="重新读取提交记录").is_visible()
            )
            checks["latest_get_503_is_confined_to_latest_submission_region"] = (
                "重新读取提交记录" in read_region.inner_text()
                and "提交结果暂未确认" not in student.locator("#api-state").inner_text()
            )
            checks["workspace_still_shows_in_progress_during_latest_read_failure"] = "进行中" in student.locator("#task-picker-state").inner_text()
            student.screenshot(path=str(OUT / "latest-read-failed-390px.png"), full_page=True)

            read_region.get_by_role("button", name="重新读取提交记录").click()
            student.wait_for_function("document.querySelector('#latest-submission-state').textContent.includes('当前没有提交记录')", timeout=10000)
            checks["local_retry_recovers_to_confirmed_empty_state"] = "当前没有提交记录" in read_region.inner_text()
            checks["retry_did_not_change_workspace_or_create_submission"] = (
                api.store.assignments[assignment_id].workspace.state == "IN_PROGRESS"
                and not api.store.assignments[assignment_id].workspace.submissions
                and sum(item.get("method") == "POST" and item.get("path", "").endswith("/submissions") for item in requests) == 1
            )
            checks["retry_was_local_to_latest_region"] = sum(
                item.get("method") == "GET" and item.get("path", "").endswith("/workspaces/workspace-1") for item in requests
            ) == 3
            checks["390px_no_horizontal_overflow"] = student.evaluate("document.documentElement.scrollWidth === innerWidth")
            student.screenshot(path=str(OUT / "latest-read-recovered-empty-390px.png"), full_page=True)

            result = {
                "task_id": "R0-P3-126-STUDENT-SUBMIT-NO-COMMIT-READ-FAILURE",
                "browser": "Microsoft Edge via Playwright",
                "origin": {"host": host, "port": port},
                "synthetic_in_memory_only": True,
                "external_calls": 0,
                "fixture_code_executed": False,
                "assignment_id": assignment_id,
                "checks": checks,
                "requests": requests,
                "workspace_postcondition": {
                    "state": api.store.assignments[assignment_id].workspace.state,
                    "revision": api.store.assignments[assignment_id].workspace.revision,
                    "submission_count": len(api.store.assignments[assignment_id].workspace.submissions),
                },
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
        assert not thread.is_alive()
        assert server.socket.fileno() < 0


if __name__ == "__main__":
    main()
