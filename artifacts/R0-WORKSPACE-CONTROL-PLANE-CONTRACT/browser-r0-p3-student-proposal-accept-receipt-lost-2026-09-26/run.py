import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

out = Path("artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-student-proposal-accept-receipt-lost-2026-09-26")
records = []
network = []
dropped = False

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})

    def intercept(route):
        global dropped
        request = route.request
        if request.method == "POST" and "/proposed-actions/" in request.url and request.url.endswith("/decision"):
            phase = "first" if not dropped else "retry"
            response = route.fetch()
            records.append({
                "phase": phase,
                "status": response.status,
                "method": request.method,
                "url": request.url,
                "body": request.post_data,
                "idempotency_key": request.headers.get("idempotency-key"),
                "if_match": request.headers.get("if-match"),
                "receipt": response.text(),
            })
            if not dropped:
                dropped = True
                route.abort("failed")
            else:
                route.fulfill(response=response)
        else:
            route.continue_()

    page.route("**/api/v1/demo/student/workspaces/*/proposed-actions/*/decision", intercept)
    page.on("request", lambda request: network.append({"method": request.method, "url": request.url}))
    page.goto("http://127.0.0.1:8767/demo/student/", wait_until="domcontentloaded")
    page.wait_for_function("document.querySelectorAll('#task-picker option').length >= 3")
    page.locator("#task-picker").select_option("assignment-1")
    page.wait_for_function("document.querySelector('#task-picker').value === 'assignment-1' && !document.querySelector('#agent-input').disabled")
    page.locator("#agent-input").fill("请给出一个可以检查的金额核对建议。")
    page.locator("#send-agent").click()
    page.wait_for_function("document.querySelector('[data-action=show-diff]') !== null")
    page.locator("[data-action='show-diff']").click()
    page.wait_for_function("!document.querySelector('#diff-card').hidden && !document.querySelector('[data-action=accept]').disabled")
    original = page.locator("#code-editor").input_value()
    page.locator("[data-action='accept']").click()
    page.wait_for_function("document.querySelector('[data-action=accept]').disabled === false && document.querySelector('[data-action=reject]').disabled && document.querySelector('[data-action=takeover]').disabled && document.querySelector('#code-editor').disabled")
    unknown = {
        "proposal_status": page.locator("#proposal-status").inner_text(),
        "api_state": page.locator("#api-state").inner_text(),
        "decision_disabled": {action: page.locator(f"[data-action='{action}']").is_disabled() for action in ["accept", "reject", "takeover"]},
        "send_disabled": page.locator("#send-agent").is_disabled(),
        "submit_disabled": page.locator("[data-action='open-submit']").is_disabled(),
        "editor_disabled": page.locator("#code-editor").is_disabled(),
        "editor": page.locator("#code-editor").input_value(),
        "selected_title": page.locator("#task-title").inner_text(),
        "width": page.evaluate("({client:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth})"),
    }
    page.screenshot(path=str(out / "proposal-accept-unknown-390px.png"), full_page=True)

    page.locator("#task-picker").select_option("assignment-2")
    page.locator("#pause-task").click()
    blocked = {
        "picker_value": page.locator("#task-picker").input_value(),
        "selected_title": page.locator("#task-title").inner_text(),
        "editor": page.locator("#code-editor").input_value(),
        "api_state": page.locator("#api-state").inner_text(),
    }
    page.locator("[data-action='accept']").click()
    page.wait_for_function("!document.querySelector('#send-agent').disabled && document.querySelector('#code-editor').disabled === false && document.querySelector('[data-action=accept]').disabled")

    workspace_id = re.search(r"/workspaces/([^/]+)/proposed-actions/", records[0]["url"]).group(1)
    proposal_id = re.search(r"/proposed-actions/([^/]+)/decision", records[0]["url"]).group(1)
    events = page.evaluate("async (id) => (await fetch('/api/v1/demo/student/workspaces/' + id + '/events?after_sequence=0&limit=50')).json()", workspace_id)
    decision_events = [event for event in events.get("data", {}).get("events", []) if event.get("event_type") == "agent.proposed_action_decided" and event.get("resource_ref") == proposal_id]
    after = page.locator("#code-editor").input_value()
    workspace = page.evaluate("async (id) => (await fetch('/api/v1/demo/student/workspaces/' + id)).json()", workspace_id)
    data = {
        "browser": "Edge via Playwright",
        "viewport": "390x844",
        "workspace_id": workspace_id,
        "proposal_id": proposal_id,
        "unknown_state": unknown,
        "while_unknown_switch_pause": blocked,
        "decision_requests": records,
        "same_request": all(records[0][key] == records[1][key] for key in ("method", "url", "body", "idempotency_key", "if_match")),
        "same_receipt_data": json.loads(records[0]["receipt"])["data"] == json.loads(records[1]["receipt"])["data"],
        "decision_events": decision_events,
        "decision_event_count": len(decision_events),
        "original_editor": original,
        "editor_after_retry": after,
        "replacement_occurrences": after.count("expected = quantity * unit_price"),
        "dirty_indicator_visible": page.locator("#dirty-dot").is_visible(),
        "proposal_status_after_retry": page.locator("#proposal-status").inner_text(),
        "api_state_after_retry": page.locator("#api-state").inner_text(),
        "workspace_state": workspace.get("data", {}).get("state"),
        "pause_posts": sum(1 for item in network if item["method"] == "POST" and item["url"].endswith("/pause")),
        "submission_posts": sum(1 for item in network if item["method"] == "POST" and "/submissions" in item["url"]),
        "decision_posts": sum(1 for item in network if item["method"] == "POST" and "/proposed-actions/" in item["url"] and item["url"].endswith("/decision")),
        "width": page.evaluate("({client:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth})"),
    }
    assert [item["status"] for item in records] == [200, 200]
    assert data["same_request"] and data["same_receipt_data"]
    assert unknown["editor"] == original and unknown["editor_disabled"] and unknown["decision_disabled"] == {"accept": False, "reject": True, "takeover": True}
    assert "仍未确认" in unknown["api_state"] and "接受并查看修改" in unknown["api_state"] and "刷新会丢失本页重试信息" in unknown["api_state"]
    assert blocked["picker_value"] == "assignment-1" and blocked["editor"] == original
    assert data["editor_after_retry"] == original.replace('            if amount != quantity * unit_price:\n                issues.append(row["order_id"])', '            expected = quantity * unit_price\n            if amount != expected:\n                print("需要核对", row["order_id"], expected)\n                issues.append(row["order_id"])')
    assert data["replacement_occurrences"] == 1 and data["dirty_indicator_visible"]
    assert data["decision_event_count"] == 1 and data["workspace_state"] == "IN_PROGRESS"
    assert data["pause_posts"] == 0 and data["submission_posts"] == 0 and data["decision_posts"] == 2
    assert "状态未确认" not in data["api_state_after_retry"]
    assert data["width"]["client"] == data["width"]["scroll"] == 390
    page.screenshot(path=str(out / "proposal-accept-retried-390px.png"), full_page=True)
    (out / "browser-run.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: data[key] for key in ("same_request", "same_receipt_data", "decision_event_count", "replacement_occurrences", "workspace_state", "pause_posts", "submission_posts", "decision_posts", "api_state_after_retry", "width")}, ensure_ascii=True, indent=2))
    browser.close()
