"""Task127: verify the teacher can retry the original publish after its browser receipt is lost."""

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
    origin = f"http://{host}:{port}"
    loopback_netloc = f"{host}:{port}"
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    requests: list[dict] = []
    publish_attempts: list[dict] = []
    dropped = {"value": False}
    checks: dict[str, bool] = {}
    title = "教师发布回执丢失核验"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            teacher = browser.new_page(viewport={"width": 1280, "height": 900})

            def capture(response):
                request = response.request
                parsed = urlsplit(response.url)
                requests.append({"method": request.method, "path": parsed.path, "status": response.status, "netloc": parsed.netloc})

            teacher.on("response", capture)
            request_urls: list[str] = []
            teacher.on("request", lambda request: request_urls.append(request.url))

            def lose_first_publish_receipt(route):
                request = route.request
                response = route.fetch()
                record = {
                    "method": request.method,
                    "path": urlsplit(request.url).path,
                    "status": response.status,
                    "body": request.post_data,
                    "idempotency_key": request.headers.get("idempotency-key"),
                    "if_match": request.headers.get("if-match"),
                    "upstream_response_dropped": False,
                }
                if not dropped["value"]:
                    dropped["value"] = True
                    record["upstream_response_dropped"] = True
                    publish_attempts.append(record)
                    route.abort("failed")
                    return
                publish_attempts.append(record)
                route.fulfill(response=response)

            teacher.route("**/api/v1/demo/teacher/assignments/*/publish", lose_first_publish_receipt)
            teacher.goto(origin + "/demo/teacher/", wait_until="networkidle")
            teacher.locator("[data-action='use-template']").click()
            teacher.locator("#task-title").fill(title)
            teacher.locator("#task-goal").fill("核对固定合成订单金额关系，说明验证依据。")
            teacher.locator("#task-responsibility").fill("指出异常、写明检查方法与待确认规则。")
            teacher.locator("#task-deliverable").fill("提交合成快照和核验说明。")
            teacher.locator("[data-action='simulate-publish']").click()
            teacher.locator("#api-state").filter(has_text="发布回执未确认").wait_for(timeout=10000)

            assignment_id = next(reversed(api.store.assignments))
            assignment = api.store.assignments[assignment_id]
            publish_button = teacher.locator("[data-action='simulate-publish']")
            checks["publish_committed_before_browser_response_was_dropped"] = (
                dropped["value"] and assignment.state == "PUBLISHED" and assignment.workspace is not None
            )
            checks["unknown_publish_state_keeps_original_task_named"] = title in teacher.locator("#api-state").inner_text()
            checks["only_original_publish_action_is_enabled"] = (
                publish_button.is_enabled()
                and publish_button.get_attribute("aria-label") == "重试原发布请求"
                and teacher.locator("[data-action='save-draft']").is_disabled()
                and teacher.locator("#task-form input, #task-form textarea, #task-form select, #task-form button").evaluate_all("items => items.length > 0 && items.every(item => item.disabled)")
                and teacher.locator("[data-action='new-task']").evaluate_all("items => items.every(item => item.disabled)")
                and teacher.locator("[data-action='use-template']").is_disabled()
                and teacher.locator("#task-title").is_disabled()
            )
            checks["one_assignment_and_one_publish_event_before_retry"] = (
                len(api.store.assignments) == 1
                and sum(event["event_type"] == "assignment.published" for event in assignment.workspace.events) == 1
            )
            teacher.screenshot(path=str(OUT / "publish-unknown-1280px.png"), full_page=True)

            teacher.get_by_role("button", name="重试原发布请求").click()
            teacher.get_by_text("本机合成 API 已发布任务", exact=False).wait_for(timeout=10000)
            cards = teacher.locator("#created-tasks .created-task-card")
            checks["retry_reaches_confirmed_published_task_card_once"] = (
                cards.count() == 1 and title in cards.first.inner_text() and "已发布 · 合成" in cards.first.inner_text()
            )
            checks["retry_reuses_identical_publish_request_identity"] = (
                len(publish_attempts) == 2
                and all(publish_attempts[0][key] == publish_attempts[1][key] for key in ("method", "path", "body", "idempotency_key", "if_match"))
                and bool(publish_attempts[0]["idempotency_key"])
                and publish_attempts[0]["if_match"] is not None
            )
            checks["retry_did_not_create_or_publish_duplicate"] = (
                len(api.store.assignments) == 1
                and assignment.state == "PUBLISHED"
                and assignment.workspace is not None
                and sum(event["event_type"] == "assignment.published" for event in assignment.workspace.events) == 1
                and len(publish_attempts) == 2
            )
            checks["all_browser_request_attempts_stayed_on_loopback"] = all(urlsplit(url).netloc == loopback_netloc for url in request_urls)
            checks["1280px_no_horizontal_overflow"] = teacher.evaluate("document.documentElement.scrollWidth === innerWidth")
            teacher.screenshot(path=str(OUT / "publish-recovered-1280px.png"), full_page=True)

            result = {
                "task_id": "R0-P3-127-TEACHER-PUBLISH-RECEIPT-LOSS",
                "browser": "Microsoft Edge via Playwright",
                "origin": {"host": host, "port": port},
                "synthetic_in_memory_only": True,
                "request_attempt_count": len(request_urls),
                "non_loopback_request_attempts": [url for url in request_urls if urlsplit(url).netloc != loopback_netloc],
                "student_code_executed": False,
                "assignment_id": assignment_id,
                "checks": checks,
                "publish_attempts": publish_attempts,
                "requests": requests,
                "request_urls": request_urls,
                "workspace_postcondition": {
                    "assignment_count": len(api.store.assignments),
                    "assignment_state": assignment.state,
                    "workspace_id": assignment.workspace.workspace_id if assignment.workspace else None,
                    "published_event_count": sum(event["event_type"] == "assignment.published" for event in assignment.workspace.events) if assignment.workspace else 0,
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
