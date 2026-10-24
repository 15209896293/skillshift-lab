import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-teacher-review-variants-receipt-loss-118-2026-09-26")
lost_receipts = []
teacher_posts = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})

    def intercept(route):
        request = route.request
        if request.method == "POST" and re.search(r"/api/v1/demo/teacher/submissions/[^/]+/review-actions$", request.url):
            response = route.fetch()
            teacher_posts.append({
                "status": response.status,
                "url": request.url,
                "body": request.post_data,
                "idempotency_key": request.headers.get("idempotency-key"),
                "if_match": request.headers.get("if-match"),
                "receipt": response.text(),
            })
            lost_receipts.append(request.url)
            route.abort("failed")
            return
        route.continue_()

    page.route("**/api/v1/demo/teacher/submissions/*/review-actions", intercept)
    page.goto("http://127.0.0.1:8767/demo/teacher/", wait_until="domcontentloaded")
    page.locator('[data-view="reviews"]').click()
    page.wait_for_function("document.querySelectorAll('#review-task-list .review-task-choice').length === 3")

    def select_teacher_task(label):
        row = page.locator("#review-task-list .review-task-choice").filter(has_text=label)
        row.locator("[data-review-assignment]").click()
        page.wait_for_function(
            "!document.querySelector('#review-details').hidden && "
            f"document.querySelector('#review-assignment-title').textContent.includes({json.dumps(label, ensure_ascii=False)})"
        )

    def submit_review(task_label, action_selector, reason):
        select_teacher_task(task_label)
        page.locator("#feedback-reason").fill(reason)
        page.locator(f'[data-review="{action_selector}"]').click()
        page.wait_for_function(
            f"document.querySelector('#remediation-status').textContent.includes({json.dumps(reason, ensure_ascii=False)})"
        )
        assignment_id = "assignment-1" if " A" in task_label else "assignment-2"
        workspace_id = "workspace-1" if " A" in task_label else "workspace-2"
        submission_id = "submission-1" if " A" in task_label else "submission-2"
        return page.evaluate("""async ([assignmentId, workspaceId, submissionId]) => {
          const [queueResponse, remediationResponse, eventsResponse, historyResponse] = await Promise.all([
            fetch(`/api/v1/demo/teacher/assignments/${assignmentId}/review-queue`),
            fetch(`/api/v1/demo/teacher/workspaces/${workspaceId}/remediation`),
            fetch(`/api/v1/demo/teacher/workspaces/${workspaceId}/events?after_sequence=0&limit=50`),
            fetch(`/api/v1/demo/teacher/assignments/${assignmentId}/review-history?after_sequence=0&limit=50`)
          ]);
          return {
            queue: await queueResponse.json(), remediation: await remediationResponse.json(),
            events: await eventsResponse.json(), history: await historyResponse.json(), submissionId
          };
        }""", [assignment_id, workspace_id, submission_id])

    task_label_a = "教师多任务队列隔离验证 A"
    task_label_b = "教师多任务队列隔离验证 B"
    reason_a = "请说明你如何核对订单金额，并写出仍待确认的规则。"
    reason_b = "请补充可复核的计算步骤和对应订单证据。"
    readback_a = submit_review(task_label_a, "explanation", reason_a)
    a_after_review = page.locator("#review-task-list .review-task-choice").all_inner_texts()
    readback_b = submit_review(task_label_b, "evidence", reason_b)
    b_after_review = page.locator("#review-task-list .review-task-choice").all_inner_texts()
    page.screenshot(path=str(OUT / "teacher-review-variants-after-readback-390px.png"), full_page=True)

    page.goto("http://127.0.0.1:8767/demo/student/", wait_until="domcontentloaded")
    page.wait_for_function("document.querySelectorAll('#task-picker option').length >= 3")

    def select_student_task(title, reason):
        option = page.locator("#task-picker option").filter(has_text=title)
        value = option.get_attribute("value")
        page.locator("#task-picker").select_option(value)
        page.wait_for_function(
            "document.querySelector('#task-title').textContent.includes(" + json.dumps(title, ensure_ascii=False) + ") && "
            "document.querySelector('#remediation-state').dataset.readState === 'confirmed' && "
            "document.querySelector('#remediation-state').textContent.includes(" + json.dumps(reason, ensure_ascii=False) + ")"
        )
        return {
            "selected_title": page.locator("#task-title").inner_text(),
            "workspace_state": page.locator("#task-picker-state").inner_text(),
            "remediation": page.locator("#remediation-state").inner_text(),
            "viewport": page.evaluate("({innerWidth, clientWidth: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth})"),
        }

    student_a = select_student_task(task_label_a, reason_a)
    page.screenshot(path=str(OUT / "student-request-explanation-visible-390px.png"), full_page=True)
    student_b = select_student_task(task_label_b, reason_b)
    page.screenshot(path=str(OUT / "student-request-evidence-visible-390px.png"), full_page=True)

    def matches(record, action, reason, submission_id):
        action_matches = [item for item in record["history"].get("data", {}).get("review_actions", []) if item.get("submission_id") == submission_id and item.get("kind") == action and item.get("reason") == reason]
        remediation_matches = [item for item in record["remediation"].get("data", {}).get("remediations", []) if item.get("submission_id") == submission_id and item.get("requested_action") == action and item.get("reason") == reason and item.get("state") == "OPEN"]
        event_ids = {item["id"] for item in action_matches}
        event_matches = [item for item in record["events"].get("data", {}).get("events", []) if item.get("event_type") == "review.action_recorded" and item.get("resource_ref") in event_ids]
        return {"review_actions": action_matches, "open_remediations": remediation_matches, "matching_events": event_matches}

    match_a = matches(readback_a, "REQUEST_EXPLANATION", reason_a, "submission-1")
    match_b = matches(readback_b, "REQUEST_EVIDENCE", reason_b, "submission-2")
    post_receipts = [json.loads(item["receipt"]) for item in teacher_posts]
    action_ids = [item["data"]["review_action"]["id"] for item in post_receipts]
    result = {
        "browser": "Microsoft Edge via Playwright",
        "viewport": "390x844",
        "fault_boundary": "Each review POST reached the local in-memory API and returned 201; Playwright then aborted the response to the teacher page. The teacher UI confirmed by API readback.",
        "lost_response_posts": teacher_posts,
        "readback_A_request_explanation": readback_a,
        "readback_B_request_evidence": readback_b,
        "matching_A": match_a,
        "matching_B": match_b,
        "queue_after_A": a_after_review,
        "queue_after_B": b_after_review,
        "student_after_explicit_A_selection": student_a,
        "student_after_explicit_B_selection": student_b,
        "assertions": {
            "only_one_post_per_variant": len(teacher_posts) == 2 and len(set(lost_receipts)) == 2,
            "both_api_writes_committed": all(item["status"] == 201 for item in teacher_posts),
            "each_variant_has_one_matching_action_remediation_event": len(match_a["review_actions"]) == len(match_a["open_remediations"]) == len(match_a["matching_events"]) == 1 and len(match_b["review_actions"]) == len(match_b["open_remediations"]) == len(match_b["matching_events"]) == 1,
            "review_ids_match_readback": [item["id"] for item in match_a["review_actions"] + match_b["review_actions"]] == action_ids,
            "queue_after_A_isolated": any(task_label_a in row and "待复核 0 项" in row for row in a_after_review) and any(task_label_b in row and "待复核 1 项" in row for row in a_after_review),
            "queue_after_B_isolated": any(task_label_a in row and "待复核 0 项" in row for row in b_after_review) and any(task_label_b in row and "待复核 0 项" in row for row in b_after_review),
            "student_A_sees_its_explanation_request": task_label_a in student_a["selected_title"] and reason_a in student_a["remediation"] and "等待你补正" in student_a["workspace_state"],
            "student_B_sees_its_evidence_request": task_label_b in student_b["selected_title"] and reason_b in student_b["remediation"] and "等待你补正" in student_b["workspace_state"],
            "no_horizontal_overflow": all(item["viewport"]["clientWidth"] == item["viewport"]["scrollWidth"] == 390 for item in (student_a, student_b)),
        },
        "observed_student_state_wording": "Both REQUEST_EXPLANATION and REQUEST_EVIDENCE are currently shown as FEEDBACK_REQUIRED / 等待你补正. The browser run observes this shared state mapping; it does not independently validate wording or instructional clarity.",
    }
    assert all(result["assertions"].values()), json.dumps(result, ensure_ascii=False, indent=2)
    (OUT / "browser-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    browser.close()
