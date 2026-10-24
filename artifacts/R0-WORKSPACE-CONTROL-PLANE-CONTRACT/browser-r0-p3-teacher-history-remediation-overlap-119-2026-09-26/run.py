import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

OUT = Path("artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-teacher-history-remediation-overlap-119-2026-09-26")
remediation_faults = []
requests = []
remediation_count = {"workspace-1": 0}

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.on("request", lambda request: requests.append({"method": request.method, "url": request.url}))

    def intercept(route):
        request = route.request
        parsed = urlsplit(request.url)
        if request.method == "GET" and parsed.path == "/api/v1/demo/teacher/workspaces/workspace-1/remediation":
            remediation_count["workspace-1"] += 1
            attempt = remediation_count["workspace-1"]
            if attempt in {1, 2}:
                remediation_faults.append({"url": request.url, "status": 503, "attempt": attempt, "injected_at_browser_boundary": True})
                route.fulfill(
                    status=503,
                    content_type="application/json; charset=utf-8",
                    body=json.dumps({
                        "schema_version": "skillshift-api/v1",
                        "request_id": f"req-remediation-overlap-{attempt}",
                        "error": {"code": "synthetic_remediation_failure", "message": "固定合成补正读取故障。"},
                    }, ensure_ascii=False),
                )
                return
            response = route.fetch()
            remediation_faults.append({"url": request.url, "status": response.status, "attempt": attempt, "injected_at_browser_boundary": False})
            route.fulfill(response=response)
            return
        route.continue_()

    page.route("**/api/v1/demo/teacher/workspaces/*/remediation**", intercept)
    page.goto("http://127.0.0.1:8767/demo/teacher/", wait_until="domcontentloaded")
    page.locator('[data-view="reviews"]').click()
    page.wait_for_function(
        "document.querySelectorAll('#review-task-list .review-task-choice').length === 3 && "
        "!document.querySelector('#review-history-retry').hidden && "
        "document.querySelector('#remediation-status [data-remediation-retry=\"assignment-1\"]') !== null"
    )

    def snapshot():
        return page.evaluate("""() => ({
          queueRows: [...document.querySelectorAll('#review-task-list .review-task-choice')].map(x => x.textContent.trim()),
          reviewCount: document.querySelector('#review-count').textContent,
          historyState: document.querySelector('#review-history-state').textContent,
          historyRows: [...document.querySelectorAll('#review-history-list li')].map(x => x.textContent.trim()),
          historyRetryVisible: !document.querySelector('#review-history-retry').hidden && document.querySelector('#review-history-retry').getClientRects().length > 0,
          remediationText: document.querySelector('#remediation-status').innerText,
          remediationRetryVisible: Boolean(document.querySelector('#remediation-status [data-remediation-retry="assignment-1"]')?.getClientRects().length),
          detailsVisible: !document.querySelector('#review-details').hidden,
          viewport: { innerWidth, clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth }
        })""")

    initial_state = snapshot()
    history_request_count_before_refresh = sum(1 for request in requests if "/review-history" in request["url"])
    queue_request_count_before_refresh = sum(1 for request in requests if "/review-queue" in request["url"])
    page.locator("#review-history-retry").click()
    page.wait_for_function("document.querySelector('#review-history-state').textContent.includes('正在读取已发布任务的复核历史')")
    for _ in range(100):
        count = sum(1 for request in requests if "/review-history" in request["url"])
        if count >= history_request_count_before_refresh + 3:
            break
        page.wait_for_timeout(50)
    else:
        raise AssertionError("Manual history refresh did not start all three task reads.")

    page.locator('#remediation-status [data-remediation-retry="assignment-1"]').click()
    page.wait_for_function("document.querySelector('#remediation-status [data-remediation-retry=\"assignment-1\"]') !== null && document.querySelector('#remediation-status').innerText.includes('补正读取失败，状态未知')")
    pending_overlap_state = snapshot()
    page.screenshot(path=str(OUT / "history-pending-remediation-retry-failed-1280px.png"), full_page=True)
    assert "正在读取已发布任务的复核历史" in pending_overlap_state["historyState"], pending_overlap_state
    assert pending_overlap_state["remediationRetryVisible"] and "补正读取失败，状态未知" in pending_overlap_state["remediationText"], pending_overlap_state
    assert pending_overlap_state["queueRows"] == initial_state["queueRows"] and pending_overlap_state["reviewCount"] == initial_state["reviewCount"], pending_overlap_state

    page.wait_for_function("document.querySelector('#review-history-state').textContent.includes('历史状态未知') && !document.querySelector('#review-history-retry').hidden")
    after_history_failure = snapshot()
    page.screenshot(path=str(OUT / "history-and-remediation-unknown-1280px.png"), full_page=True)
    assert after_history_failure["remediationRetryVisible"] and "补正读取失败，状态未知" in after_history_failure["remediationText"], after_history_failure
    history_rows_before_remediation_recovery = list(after_history_failure["historyRows"])
    history_request_count_before_remediation_recovery = sum(1 for request in requests if "/review-history" in request["url"])
    queue_request_count_before_remediation_recovery = sum(1 for request in requests if "/review-queue" in request["url"])

    page.locator('#remediation-status [data-remediation-retry="assignment-1"]').click()
    page.wait_for_function("document.querySelector('#remediation-status').innerText.includes('任务 C：请补充一项固定合成核验步骤。') && !document.querySelector('#remediation-status [data-remediation-retry=\"assignment-1\"]')")
    recovered_state = snapshot()
    page.screenshot(path=str(OUT / "remediation-recovered-history-still-unknown-1280px.png"), full_page=True)
    history_request_count_after_remediation_recovery = sum(1 for request in requests if "/review-history" in request["url"])
    queue_request_count_after_remediation_recovery = sum(1 for request in requests if "/review-queue" in request["url"])

    result = {
        "browser": "Microsoft Edge via Playwright",
        "viewport": "1280x900",
        "fault_boundary": "Existing teacher-history-retry-delay loopback Harness delayed the second A history read then returned 503. Playwright injected the first two A remediation 503 responses and let the third A remediation request reach the local in-memory API.",
        "remediation_responses": remediation_faults,
        "history_request_count_before_refresh": history_request_count_before_refresh,
        "history_request_count_before_remediation_recovery": history_request_count_before_remediation_recovery,
        "history_request_count_after_remediation_recovery": history_request_count_after_remediation_recovery,
        "queue_request_count_before_refresh": queue_request_count_before_refresh,
        "queue_request_count_before_remediation_recovery": queue_request_count_before_remediation_recovery,
        "queue_request_count_after_remediation_recovery": queue_request_count_after_remediation_recovery,
        "initial_state": initial_state,
        "history_pending_with_remediation_retry_failed": pending_overlap_state,
        "both_regions_unknown": after_history_failure,
        "remediation_recovered_history_still_failed": recovered_state,
        "assertions": {
            "first_history_and_remediation_reads_failed_independently": len(remediation_faults) == 3 and remediation_faults[0]["status"] == 503 and remediation_faults[1]["status"] == 503,
            "history_remained_pending_during_remediation_retry": "正在读取已发布任务的复核历史" in pending_overlap_state["historyState"],
            "remediation_failure_did_not_replace_history_pending_state": "正在读取已发布任务的复核历史" in pending_overlap_state["historyState"],
            "queue_remained_unchanged_during_failures": initial_state["queueRows"] == pending_overlap_state["queueRows"] == after_history_failure["queueRows"],
            "history_failure_preserved_remediation_retry": after_history_failure["remediationRetryVisible"],
            "remediation_retry_recovered_only_its_region": "任务 C：请补充一项固定合成核验步骤。" in recovered_state["remediationText"] and not recovered_state["remediationRetryVisible"] and recovered_state["historyRows"] == history_rows_before_remediation_recovery and "历史状态未知" in recovered_state["historyState"],
            "remediation_recovery_did_not_refetch_history_or_queue": history_request_count_before_remediation_recovery == history_request_count_after_remediation_recovery and queue_request_count_before_remediation_recovery == queue_request_count_after_remediation_recovery,
            "no_horizontal_overflow": all(item["viewport"]["clientWidth"] == item["viewport"]["scrollWidth"] == 1280 for item in (initial_state, pending_overlap_state, after_history_failure, recovered_state)),
        },
    }
    assert remediation_faults[2]["status"] == 200, result
    assert all(result["assertions"].values()), json.dumps(result, ensure_ascii=False, indent=2)
    (OUT / "browser-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    browser.close()
