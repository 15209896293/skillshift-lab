import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

OUT = Path("artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-teacher-event-local-failure-117-2026-09-26")
events = []
queue_reads = []
failed = {"once": False}

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    def intercept(route):
        request = route.request
        if request.method == "GET" and urlsplit(request.url).path.endswith("/api/v1/demo/teacher/workspaces/workspace-1/events"):
            if not failed["once"]:
                failed["once"] = True
                events.append({"url": request.url, "status": 503, "injected_at_browser_boundary": True})
                route.fulfill(
                    status=503,
                    content_type="application/json; charset=utf-8",
                    body=json.dumps({
                        "schema_version": "skillshift-api/v1",
                        "request_id": "req-browser-injected-event-failure",
                        "error": {"code": "synthetic_event_read_failure", "message": "固定合成事件读取故障。"},
                    }, ensure_ascii=False),
                )
                return
            response = route.fetch()
            events.append({"url": request.url, "status": response.status, "injected_at_browser_boundary": False})
            route.fulfill(response=response)
            return
        route.continue_()

    page.route("**/api/v1/demo/teacher/workspaces/*/events**", intercept)
    page.on("request", lambda request: queue_reads.append(request.url)
            if request.method == "GET" and "/review-queue" in request.url else None)
    page.goto("http://127.0.0.1:8767/demo/teacher/", wait_until="domcontentloaded")
    page.locator('[data-view="reviews"]').click()
    page.wait_for_function("document.querySelectorAll('#review-task-list .review-task-choice').length === 3")
    page.locator("#review-task-list .review-task-choice").filter(
        has_text="教师多任务队列隔离验证 A"
    ).locator('[data-review-assignment]').click()
    page.wait_for_function(
        "!document.querySelector('#review-details').hidden && "
        "document.querySelector('#review-assignment-title').textContent.includes('教师多任务队列隔离验证 A')"
    )
    page.wait_for_timeout(1000)

    def snapshot():
        return page.evaluate("""() => ({
          viewport: { innerWidth, clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth },
          detailsVisible: !document.querySelector('#review-details').hidden,
          title: document.querySelector('#review-assignment-title').textContent,
          submissionState: document.querySelector('#review-submission-state').textContent,
          explanation: document.querySelector('#review-student-explanation').textContent,
          queueRows: [...document.querySelectorAll('#review-task-list .review-task-choice')].map(x => x.textContent.trim()),
          evidenceState: document.querySelector('#evidence-state').textContent,
          retryVisible: !document.querySelector('#evidence-retry').hidden && document.querySelector('#evidence-retry').getClientRects().length > 0,
          retryLabel: document.querySelector('#evidence-retry').textContent.trim(),
          timeline: [...document.querySelectorAll('#evidence-timeline li')].map(x => x.textContent.trim()),
          reviewCount: document.querySelector('#review-count').textContent
        })""")

    failed_state = snapshot()
    assert failed_state["retryVisible"] and "事件状态未知" in failed_state["evidenceState"], failed_state
    page.screenshot(path=str(OUT / "teacher-event-local-failure-unknown-1280px.png"), full_page=True)
    queue_reads_before_retry = len(queue_reads)
    page.locator("#evidence-retry").click()
    page.wait_for_function("document.querySelector('#evidence-state').textContent === '事件读取成功。'")
    recovered_state = snapshot()
    queue_reads_after_retry = len(queue_reads)
    page.screenshot(path=str(OUT / "teacher-event-local-failure-recovered-1280px.png"), full_page=True)

    result = {
        "browser": "Microsoft Edge via Playwright",
        "viewport": "1280x900",
        "fault_boundary": "Playwright fulfilled one synthetic 503 for A's teacher events GET; the local WSGI API served all other requests and the subsequent event retry.",
        "event_requests": events,
        "review_queue_reads_before_retry": queue_reads_before_retry,
        "review_queue_reads_after_retry": queue_reads_after_retry,
        "unknown_state": failed_state,
        "recovered_state": recovered_state,
        "assertions": {
            "A_details_visible_during_event_failure": failed_state["detailsVisible"],
            "A_submission_state_not_unknown": "未知" not in failed_state["submissionState"],
            "three_task_queue_retained": len(failed_state["queueRows"]) == 3,
            "event_region_unknown_and_retryable": "事件状态未知" in failed_state["evidenceState"] and failed_state["retryVisible"],
            "event_retry_returned_success": recovered_state["evidenceState"] == "事件读取成功。" and not recovered_state["retryVisible"],
            "queue_not_refetched_by_event_retry": queue_reads_before_retry == queue_reads_after_retry,
            "A_details_preserved_after_retry": recovered_state["detailsVisible"] and recovered_state["title"] == failed_state["title"] and recovered_state["submissionState"] == failed_state["submissionState"],
            "no_horizontal_overflow": all(item["viewport"]["clientWidth"] == item["viewport"]["scrollWidth"] == 1280 for item in (failed_state, recovered_state)),
        },
    }
    assert len(events) == 2 and events[0]["status"] == 503 and events[1]["status"] == 200
    assert all(result["assertions"].values()), result
    assert queue_reads_before_retry == queue_reads_after_retry
    (OUT / "browser-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    browser.close()
