"""Task128: verify a full teacher-page reload reads back a committed publish without reposting."""

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
    netloc = f"{host}:{port}"
    origin = f"http://{netloc}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    request_urls: list[str] = []
    responses: list[dict] = []
    first_publish = {"dropped": False, "upstream_status": None}
    checks: dict[str, bool] = {}
    title = "发布回执丢失后刷新目录核验"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            teacher = browser.new_page(viewport={"width": 1280, "height": 900})
            teacher.on("request", lambda request: request_urls.append(request.url))
            teacher.on("response", lambda response: responses.append({
                "method": response.request.method,
                "path": urlsplit(response.url).path,
                "status": response.status,
            }))

            def lose_publish_receipt(route):
                response = route.fetch()
                first_publish["upstream_status"] = response.status
                if not first_publish["dropped"]:
                    first_publish["dropped"] = True
                    route.abort("failed")
                else:
                    route.fulfill(response=response)

            teacher.route("**/api/v1/demo/teacher/assignments/*/publish", lose_publish_receipt)
            teacher.goto(origin + "/demo/teacher/", wait_until="networkidle")
            teacher.locator("[data-action='use-template']").click()
            teacher.locator("#task-title").fill(title)
            teacher.locator("#task-goal").fill("检查合成订单金额关系，说明核对依据。")
            teacher.locator("#task-responsibility").fill("指出异常、说明验证步骤与待确认规则。")
            teacher.locator("#task-deliverable").fill("提交固定合成快照和说明。")
            teacher.locator("[data-action='simulate-publish']").click()
            teacher.locator("#api-state").filter(has_text="发布回执未确认").wait_for(timeout=10000)
            assignment_id = next(reversed(api.store.assignments))
            assignment = api.store.assignments[assignment_id]
            checks["first_publish_was_committed_before_only_browser_receipt_was_dropped"] = (
                first_publish["dropped"] and first_publish["upstream_status"] == 200
                and assignment.state == "PUBLISHED" and assignment.workspace is not None
            )
            checks["pre_reload_ui_keeps_unknown_publish_and_original_title"] = (
                "发布回执未确认" in teacher.locator("#api-state").inner_text()
                and title in teacher.locator("#api-state").inner_text()
            )
            teacher.screenshot(path=str(OUT / "publish-unknown-before-refresh-1280px.png"), full_page=True)

            publish_path = f"/api/v1/demo/teacher/assignments/{assignment_id}/publish"
            publish_count_before = sum(urlsplit(url).path == publish_path for url in request_urls)
            directory_count_before = sum(
                response["method"] == "GET" and response["path"] == "/api/v1/demo/teacher/assignments"
                for response in responses
            )
            teacher.reload(wait_until="networkidle")
            cards = teacher.locator("#created-tasks .created-task-card")
            cards.filter(has_text=title).wait_for(timeout=10000)
            publish_count_after = sum(urlsplit(url).path == publish_path for url in request_urls)
            directory_count_after = sum(
                response["method"] == "GET" and response["path"] == "/api/v1/demo/teacher/assignments"
                for response in responses
            )
            checks["reload_performed_a_fresh_directory_read"] = directory_count_after == directory_count_before + 1
            checks["reload_did_not_send_another_publish_post"] = publish_count_before == publish_count_after == 1
            checks["directory_shows_exactly_one_confirmed_published_card"] = (
                cards.count() == 1
                and title in cards.first.inner_text()
                and "已发布 · 合成" in cards.first.inner_text()
            )
            checks["server_state_has_one_assignment_workspace_and_publish_event"] = (
                len(api.store.assignments) == 1
                and assignment.state == "PUBLISHED"
                and assignment.workspace is not None
                and sum(event["event_type"] == "assignment.published" for event in assignment.workspace.events) == 1
            )
            checks["all_browser_request_attempts_stayed_on_loopback"] = all(urlsplit(url).netloc == netloc for url in request_urls)
            checks["1280px_no_horizontal_overflow"] = teacher.evaluate("document.documentElement.scrollWidth === innerWidth")
            teacher.screenshot(path=str(OUT / "publish-read-back-after-refresh-1280px.png"), full_page=True)

            result = {
                "task_id": "R0-P3-128-TEACHER-PUBLISH-RELOAD-READBACK",
                "browser": "Microsoft Edge via Playwright",
                "origin": {"host": host, "port": port},
                "synthetic_in_memory_only": True,
                "request_attempt_count": len(request_urls),
                "non_loopback_request_attempts": [url for url in request_urls if urlsplit(url).netloc != netloc],
                "assignment_id": assignment_id,
                "checks": checks,
                "publish_request_count_before_reload": publish_count_before,
                "publish_request_count_after_reload": publish_count_after,
                "directory_read_count_before_reload": directory_count_before,
                "directory_read_count_after_reload": directory_count_after,
                "responses": responses,
                "request_urls": request_urls,
                "postcondition": {
                    "assignment_count": len(api.store.assignments),
                    "assignment_state": assignment.state,
                    "workspace_id": assignment.workspace.workspace_id if assignment.workspace else None,
                    "publish_event_count": sum(event["event_type"] == "assignment.published" for event in assignment.workspace.events) if assignment.workspace else 0,
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
