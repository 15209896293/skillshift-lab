import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

out = Path("artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-student-agent-turn-receipt-lost-2026-09-26")
requests = []
network = []
dropped = False
question = "请给出一个可以检查的金额核对建议。"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})

    def intercept(route):
        global dropped
        request = route.request
        if request.method == "POST" and request.url.endswith("/agent-turns"):
            phase = "first" if not dropped else "retry"
            response = route.fetch()
            requests.append({
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

    page.route("**/api/v1/demo/student/workspaces/*/agent-turns", intercept)
    page.on("request", lambda request: network.append({"method": request.method, "url": request.url}))
    page.goto("http://127.0.0.1:8767/demo/student/", wait_until="domcontentloaded")
    page.wait_for_function("document.querySelectorAll('#task-picker option').length >= 3")
    page.locator("#task-picker").select_option("assignment-1")
    page.wait_for_function("document.querySelector('#task-picker').value === 'assignment-1' && !document.querySelector('#agent-input').disabled")
    original_editor = page.locator("#code-editor").input_value()
    page.locator("#agent-input").fill(question)
    page.locator("#send-agent").click()
    page.wait_for_function("document.querySelector('#api-state').textContent.includes('上一问题的回执尚未确认')")
    unknown = {
        "input": page.locator("#agent-input").input_value(),
        "send_disabled": page.locator("#send-agent").is_disabled(),
        "message_articles": page.locator("#agent-messages .agent-message").count(),
        "proposal_buttons": page.locator("#agent-messages [data-action='show-diff']").count(),
        "api_state": page.locator("#api-state").inner_text(),
        "selected_task": page.locator("#task-picker").input_value(),
        "editor": page.locator("#code-editor").input_value(),
        "width": page.evaluate("({client:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth})"),
    }
    page.screenshot(path=str(out / "agent-turn-unknown-390px.png"), full_page=True)
    assert len(requests) == 1 and requests[0]["status"] == 200

    page.locator("#agent-input").fill("请把不同问题作为新回合发送。")
    page.locator("#send-agent").click()
    page.wait_for_timeout(100)
    rejected_new_question = {
        "input_preserved": page.locator("#agent-input").input_value(),
        "agent_post_count": sum(1 for item in network if item["method"] == "POST" and item["url"].endswith("/agent-turns")),
        "api_state": page.locator("#api-state").inner_text(),
    }
    page.locator("#agent-input").fill(question)
    page.locator("#send-agent").click()
    page.wait_for_function("!document.querySelector('#send-agent').disabled && document.querySelectorAll('#agent-messages [data-action=show-diff]').length === 1")
    workspace_id = re.search(r"/workspaces/([^/]+)/agent-turns$", requests[0]["url"]).group(1)
    first_data = json.loads(requests[0]["receipt"])["data"]
    second_data = json.loads(requests[1]["receipt"])["data"]
    events = page.evaluate("async (id) => (await fetch('/api/v1/demo/student/workspaces/' + id + '/events?after_sequence=0&limit=50')).json()", workspace_id)
    turn_id = first_data["turn"]["id"]
    turn_events = [event for event in events.get("data", {}).get("events", []) if event.get("event_type") == "agent.turn_created" and event.get("resource_ref") == turn_id]
    data = {
        "browser": "Edge via Playwright",
        "viewport": "390x844",
        "workspace_id": workspace_id,
        "turn_id": turn_id,
        "proposal_id": first_data.get("proposed_action", {}).get("id"),
        "unknown_state": unknown,
        "different_question_attempt": rejected_new_question,
        "requests": requests,
        "same_request": all(requests[0][key] == requests[1][key] for key in ("method", "url", "body", "idempotency_key", "if_match")),
        "same_turn_receipt_data": first_data == second_data,
        "turn_events": turn_events,
        "turn_event_count": len(turn_events),
        "question_bubbles": page.locator("#agent-messages .user-message").count(),
        "agent_bubbles": page.locator("#agent-messages .agent-message").count(),
        "proposal_buttons": page.locator("#agent-messages [data-action='show-diff']").count(),
        "api_state_after_retry": page.locator("#api-state").inner_text(),
        "editor_unchanged": page.locator("#code-editor").input_value() == original_editor,
        "workspace_state": page.evaluate("async (id) => (await fetch('/api/v1/demo/student/workspaces/' + id)).json()", workspace_id).get("data", {}).get("state"),
        "agent_post_count": sum(1 for item in network if item["method"] == "POST" and item["url"].endswith("/agent-turns")),
        "pause_posts": sum(1 for item in network if item["method"] == "POST" and item["url"].endswith("/pause")),
        "submission_posts": sum(1 for item in network if item["method"] == "POST" and "/submissions" in item["url"]),
        "width": page.evaluate("({client:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth})"),
    }
    assert len(requests) == 2 and [request["status"] for request in requests] == [200, 200]
    assert data["same_request"] and data["same_turn_receipt_data"] and data["turn_event_count"] == 1
    assert unknown["input"] == question and unknown["message_articles"] == 0 and unknown["proposal_buttons"] == 0
    assert "把原问题放回输入框后重试" in unknown["api_state"] and "刷新会丢失本页重试信息" in unknown["api_state"]
    assert rejected_new_question["input_preserved"] == "请把不同问题作为新回合发送。" and rejected_new_question["agent_post_count"] == 1
    assert data["question_bubbles"] == data["agent_bubbles"] == data["proposal_buttons"] == 1
    assert data["editor_unchanged"] and data["workspace_state"] == "IN_PROGRESS"
    assert data["agent_post_count"] == 2 and data["pause_posts"] == data["submission_posts"] == 0
    assert "已确认上一 Agent 回合" in data["api_state_after_retry"]
    assert data["width"]["client"] == data["width"]["scroll"] == 390
    page.screenshot(path=str(out / "agent-turn-retried-390px.png"), full_page=True)
    (out / "browser-run.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: data[key] for key in ("same_request", "same_turn_receipt_data", "turn_event_count", "question_bubbles", "agent_bubbles", "proposal_buttons", "agent_post_count", "pause_posts", "submission_posts", "width")}, ensure_ascii=True, indent=2))
    browser.close()
