from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.module_scripts: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "script" and values.get("type") == "module" and values.get("src"):
            self.module_scripts.add(values["src"] or "")


class WorkspaceFrontendHtmlTests(unittest.TestCase):
    def test_app_id_selectors_exist_in_their_html_pages(self) -> None:
        for role in ("teacher", "student"):
            with self.subTest(role=role):
                page = ROOT / "apps" / f"{role}-web" / "index.html"
                script = ROOT / "apps" / f"{role}-web" / "app.js"
                parser = IdCollector()
                parser.feed(page.read_text(encoding="utf-8"))
                referenced = set(re.findall(r'document\.querySelector(?:All)?\("#([A-Za-z0-9_-]+)"\)', script.read_text(encoding="utf-8")))
                self.assertEqual(set(), referenced - parser.ids)
                self.assertIn("./app.js", parser.module_scripts)

    def test_both_pages_mark_the_synthetic_api_as_non_production(self) -> None:
        for role in ("teacher", "student"):
            page = (ROOT / "apps" / f"{role}-web" / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="api-state"', page)
            self.assertIn("非生产", page)

    def test_teacher_and_student_scripts_keep_the_workspace_dto_call_chain_wired(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        for call in (
            "api.createAssignment(attempt.dto)",
            "api.publishAssignment(attempt.assignment.id, attempt.assignment.revision)",
            "assignments.filter((item) => item.state === \"PUBLISHED\" && item.workspace)",
            "readReviewQueueForAssignment(assignment)",
            "submission.artifact_snapshots.map(renderSnapshot)",
            "mapReviewActionToDto(button.dataset.review, reason)",
            'if (state.kind === "unavailable")',
            "syncReviewAttemptControls();",
            "confirmReviewOutcome(api, context.submission, reviewDto)",
        ):
            with self.subTest(role="teacher", call=call):
                self.assertIn(call, teacher)
        for call in (
            "api.listAssignments()",
            "item.state === \"PUBLISHED\" && item.workspace",
            "api.getAssignment(assignment.id)",
            "api.getWorkspace(workspaceIdFromAssignment)",
            "api.startWorkspace(workspace.id, workspace.revision, assignment.id)",
            "api.agentTurn(attempt.workspaceId, attempt.question, attempt.revision)",
            "mapFilesToSubmissionDto(workingContent, submissionNote.value)",
            "api.submit(attempt.workspaceId, attempt.dto, attempt.revision)",
            "api.remediations(workspaceIdToRead)",
            "setProposalDecisionPending(true)",
            "setProposalDecisionPending(false)",
            'setProposalDecisionPending(false, proposalAcceptAttempt !== null ? "accept" : null)',
            'decideProposal("REJECTED", "reject")',
            'decideProposal("STUDENT_TAKEOVER", "takeover")',
        ):
            with self.subTest(role="student", call=call):
                self.assertIn(call, student)

    def test_student_start_unknown_retry_reads_state_before_dispatching_another_start(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("let pendingStartAttempt = null", student)
        failure_start = student.index("function renderStudentTaskReadFailure(")
        failure_end = student.index("\nfunction setWorkspaceState(", failure_start)
        self.assertIn("loadStudentWorkspace(selectedAssignmentId)", student[failure_start:failure_end])

        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index('\ndocument.querySelector("#task-picker")', loader_start)
        loader = student[loader_start:loader_end]
        self.assertIn('if (workspace.state === "ASSIGNED" || workspace.state === "PAUSED") {', loader)
        self.assertIn("started = await api.startWorkspace(workspace.id, workspace.revision, assignment.id);", loader)
        self.assertLess(loader.index("pendingStartAttempt = { assignmentId: assignment.id"), loader.index("api.startWorkspace(workspace.id, workspace.revision, assignment.id)"))
        self.assertIn('if (outcome.kind !== "unavailable" && outcome.kind !== "error") pendingStartAttempt = null;', loader)
        self.assertIn("picker.disabled = picker.options.length <= 1 || pendingStartAttempt !== null", loader)
        self.assertIn("} else {\n      workspaceRevision = workspace.revision;", loader)
        self.assertIn("renderStudentTaskReadFailure(state.message, selectedAssignmentId);", loader)

        change_start = student.index('document.querySelector("#task-picker").addEventListener("change"')
        change_end = student.index('\ndocument.querySelector("#pause-task")', change_start)
        change = student[change_start:change_end]
        self.assertIn("if (pendingStartAttempt && nextAssignmentId !== pendingStartAttempt.assignmentId)", change)
        self.assertIn('event.target.value = pendingStartAttempt.assignmentId;', change)

    def test_student_active_task_conflict_is_not_mislabeled_as_unknown_read_failure(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        renderer_start = student.index("function renderStudentActiveTaskConflict(")
        renderer_end = student.index("\nfunction setWorkspaceState(", renderer_start)
        renderer = student[renderer_start:renderer_end]
        self.assertIn("所选任务没有开始：另一个任务正在进行。", renderer)
        self.assertIn('retry.textContent = "重新读取任务目录";', renderer)
        self.assertIn("retry.addEventListener(\"click\", () => loadStudentWorkspace());", renderer)

        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index('\ndocument.querySelector("#task-picker")', loader_start)
        loader = student[loader_start:loader_end]
        conflict = loader.index('if (error?.code === "active_task_exists")')
        self.assertLess(conflict, loader.index("renderStudentActiveTaskConflict(state.message);", conflict))
        self.assertIn('pickerState.textContent = "启动冲突 · 需重新选择";', loader)
        self.assertIn('pickerState.textContent = "读取失败 · 未知";', loader)

    def test_teacher_task_catalog_discards_stale_reads_and_has_local_retry(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        teacher_html = (ROOT / "apps" / "teacher-web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("let assignmentListReadGeneration = 0", teacher)
        self.assertIn('id="assignment-list-state"', teacher_html)

        failure_start = teacher.index("function renderAssignmentListReadFailure(")
        failure_end = teacher.index("\nasync function refreshAssignments(", failure_start)
        failure = teacher[failure_start:failure_end]
        self.assertIn('document.querySelector("#assignment-list-state")', failure)
        self.assertIn('retry.textContent = "重试读取任务目录";', failure)
        self.assertIn("refreshAssignments()", failure)
        self.assertIn("写入状态不会重试。", teacher)

        refresh_start = teacher.index("async function refreshAssignments(")
        refresh_end = teacher.index("\nfunction isUnknownWriteOutcome(", refresh_start)
        refresh = teacher[refresh_start:refresh_end]
        self.assertRegex(refresh, r"const generation = \+\+assignmentListReadGeneration;")
        self.assertIn('status.textContent = "正在读取任务目录。";', refresh)
        self.assertLess(refresh.index("if (generation !== assignmentListReadGeneration)"), refresh.index("createdTasks.replaceChildren();"))
        self.assertIn("if (generation === assignmentListReadGeneration)", refresh)

        startup = teacher[teacher.index("updatePreview();\nrefreshAssignments()"):]
        self.assertIn("!result.stale && result.generation === assignmentListReadGeneration", startup)

    def test_frontend_write_controls_prevent_double_dispatch_and_preserve_unknown_submission(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("if (taskWritePending) return false;", teacher)
        self.assertIn("taskWritePending = true;", teacher)
        self.assertIn("taskWritePending = false;", teacher)
        self.assertIn("if (submissionInFlight) return;", student)
        self.assertIn("const attempt = pendingSubmission ||", student)
        self.assertIn("api.submit(attempt.workspaceId, attempt.dto, attempt.revision)", student)
        self.assertIn("setSubmissionContentFrozen(true);", student)
        self.assertIn("页面已冻结本次提交内容", student)
        self.assertIn('confirmButton.textContent = "重试同一提交";', student)
        self.assertIn("pendingSubmission = null;", student)

    def test_definitive_submission_rejection_is_not_reclassified_as_unknown_by_workspace_readback(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        submit_start = student.index('submissionForm.addEventListener("submit"')
        submit_end = student.index('\nsubmissionNote.addEventListener("input"', submit_start)
        submit_handler = student[submit_start:submit_end]
        self.assertIn('error?.definitiveRejection !== true && ["REVIEW_REQUIRED", "RESUBMITTED"].includes(latest.state)', submit_handler)
        self.assertLess(submit_handler.index('error?.definitiveRejection !== true'), submit_handler.index('state = { kind: "unknown"'))
        self.assertIn('if (state.kind === "unknown") await loadLatestSubmission(attempt.workspaceId);', submit_handler)

    def test_teacher_task_retry_preserves_create_and_publish_intent(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        start = teacher.index("async function saveTask(publish) {")
        end = teacher.index("\nfunction renderSnapshot(", start)
        save_task = teacher[start:end]

        # A second click while a write is pending must not dispatch another write.
        self.assertRegex(save_task, r"if\s*\(taskWritePending\)\s*return\s+false\s*;")
        self.assertRegex(teacher, r"let\s+taskWriteAttempt\s*=\s*null\s*;")

        # The attempt carries a frozen DTO and requested action across an unknown receipt.
        self.assertRegex(save_task, r"if\s*\(!taskWriteAttempt\)\s*\{[\s\S]{0,180}?taskWriteAttempt\s*=\s*\{")
        self.assertRegex(save_task, r"\bdto\s*:\s*Object\.freeze\(mapTaskFormToCreateDto\(draftState\)\)")
        self.assertIn("      publish,", save_task)
        self.assertRegex(save_task, r"\bphase\s*:\s*[\"']CREATE[\"']")

        # Retrying CREATE uses the saved DTO; retrying PUBLISH uses the saved assignment
        # and cannot re-enter the create path.
        self.assertRegex(save_task, r"api\.createAssignment\(attempt\.dto\)")
        publish_phase = re.search(
            r"if\s*\(attempt\.phase\s*===\s*[\"']PUBLISH[\"']\)\s*\{(?P<body>[^{}]*)\}",
            save_task,
        )
        self.assertIsNotNone(publish_phase, "publish retry must have an explicit phase branch")
        assert publish_phase is not None
        self.assertRegex(publish_phase.group("body"), r"api\.publishAssignment\(attempt\.assignment\.id,\s*attempt\.assignment\.revision\)")
        self.assertNotIn("createAssignment", publish_phase.group("body"))

        # Opposite-action clicks cannot replace the pending action. Any unresolved
        # attempt freezes the source inputs and entry points but leaves its retry button.
        self.assertRegex(save_task, r"taskWriteAttempt\s*&&\s*taskWriteAttempt\.publish\s*!==\s*publish")
        self.assertIn("isUnknownWriteOutcome(error)", save_task)
        sync_start = teacher.index("function syncTaskWriteButtons() {")
        sync_end = teacher.index("\nfunction isPublishedAttemptAssignment(", sync_start)
        sync_controls = teacher[sync_start:sync_end]
        self.assertIn('form.querySelectorAll("input, textarea, select, button")', sync_controls)
        self.assertIn('"[data-action=\'new-task\'], [data-action=\'use-template\']"', sync_controls)
        self.assertIn("const hasPendingAttempt = taskWriteAttempt !== null;", sync_controls)
        self.assertIn("button.disabled = taskWritePending || hasPendingAttempt;", sync_controls)
        self.assertIn('button.dataset.retryPending = "true";', sync_controls)

        # Status surfaces identify the original task and step while keeping the form frozen.
        self.assertRegex(teacher, r"function setPublishRecoveryStatus\(message\)[\s\S]{0,300}taskWriteAttempt\?\.dto\?\.title")
        self.assertRegex(teacher, r"taskWriteAttempt\?\.dto\?\.title[\s\S]{0,180}当前任务内容与新建入口已冻结")
        self.assertRegex(save_task, r"待处理原任务.*attempt\.dto\.title.*冻结")

        # A definite publish response is not itself proof of the postcondition: read
        # back the original assignment and require its matching published workspace.
        explicit_error_at = save_task.index("if (!isUnknownWriteOutcome(error)) {")
        unknown_status_at = save_task.index("const pendingAction =", explicit_error_at)
        definite_error = save_task[explicit_error_at:unknown_status_at]
        self.assertIn("if (attempt.phase === \"PUBLISH\" && attempt.assignment)", definite_error)
        self.assertIn("api.getAssignment(attempt.assignment.id)", definite_error)
        self.assertIn("isPublishedAttemptAssignment(latest, attempt)", definite_error)
        published_check = re.search(
            r"function isPublishedAttemptAssignment\(assignment, attempt\)\s*\{(?P<body>[^{}]*)\}",
            teacher,
        )
        self.assertIsNotNone(published_check)
        assert published_check is not None
        for condition in (
            "assignment?.id === attempt.assignment?.id",
            'assignment.state === "PUBLISHED"',
            "assignment.workspace?.assignment_id === assignment.id",
            "assignment.workspace.execution_enabled === false",
        ):
            self.assertIn(condition, published_check.group("body"))

        # Readback of the same assignment as DRAFT captures its latest revision but
        # waits for a separate teacher click before sending another publish request.
        self.assertIn("latest.id === attempt.assignment.id && latest.state === \"DRAFT\"", definite_error)
        self.assertIn("attempt.assignment = latest;", definite_error)
        self.assertIn('attempt.phase = "PUBLISH_RETRY_READY";', definite_error)
        self.assertIn('if (attempt.phase === "PUBLISH_RETRY_READY") attempt.phase = "PUBLISH";', save_task)
        self.assertIn("api.publishAssignment(attempt.assignment.id, attempt.assignment.revision)", save_task)

        # Failed/ambiguous readback keeps the publish attempt. The next click only
        # reads the same assignment; it cannot fall through to CREATE or auto-publish.
        readback_start = save_task.index('if (attempt.phase === "PUBLISH_READBACK_REQUIRED") {')
        readback_end = save_task.index('\n  try {\n    if (attempt.phase === "PUBLISH_RETRY_READY")', readback_start)
        readback_branch = save_task[readback_start:readback_end]
        self.assertIn("api.getAssignment(attempt.assignment.id)", readback_branch)
        self.assertNotIn("createAssignment", readback_branch)
        self.assertNotIn("publishAssignment", readback_branch)
        readback_catch_start = readback_branch.index("catch (error) {")
        readback_catch_end = readback_branch.index("} finally {", readback_catch_start)
        readback_failure = readback_branch[readback_catch_start:readback_catch_end]
        self.assertNotIn("taskWriteAttempt = null", readback_failure)
        self.assertIn("setPublishRecoveryStatus", readback_failure)

        # Explicit CREATE rejection may clear the attempt and unfreeze the form;
        # explicit PUBLISH failure retains it until readback resolves the same ID.
        self.assertRegex(definite_error, r"if\s*\(attempt\.phase === \"PUBLISH\" && attempt\.assignment\)[\s\S]*?\} else \{\s*taskWriteAttempt = null;")
        self.assertRegex(definite_error, r"taskWriteAttempt = null;[\s\S]{0,180}任务创建被本机合成 API 明确拒绝")
        unknown_classifier = re.search(
            r"function isUnknownWriteOutcome\(error\)\s*\{(?P<body>[^{}]*)\}",
            teacher,
        )
        self.assertIsNotNone(unknown_classifier)
        assert unknown_classifier is not None
        self.assertRegex(unknown_classifier.group("body"), r"error\.status\s*>=\s*500")
        self.assertRegex(unknown_classifier.group("body"), r"error\.status\s*===\s*0")
        self.assertNotRegex(unknown_classifier.group("body"), r"error\.status\s*===\s*409")
        self.assertRegex(save_task, r"showToast\(state\.message\)")
        self.assertRegex(save_task, r"return\s+false\s*;\s*\}\s*finally")

    def test_teacher_review_unknown_receipt_retains_the_same_review_attempt(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        self.assertRegex(teacher, r"let\s+reviewWriteAttempt\s*=\s*null")
        review_start = teacher.index('document.querySelectorAll("[data-review]").forEach((button) => {\n  button.addEventListener("click"')
        review_end = teacher.index('document.querySelectorAll(".submission-tab")', review_start)
        handler = teacher[review_start:review_end]

        # Source-structure assertion only: this test does not dispatch DOM events.
        # The retry must preserve the selected submission, exact DTO, and revision.
        self.assertRegex(handler, r"reviewWriteAttempt\s*=\s*attempt")
        self.assertRegex(handler, r"api\.review\(attempt\.targetSubmissionId,\s*reviewDto,\s*attempt\.revision,\s*context\.submission\.version\)")
        self.assertRegex(handler, r"dto:\s*Object\.freeze\(mapReviewActionToDto")
        self.assertRegex(handler, r"targetSubmissionId:\s*reviewContext\.submission\.id")
        self.assertRegex(handler, r"revision:\s*reviewContext\.revision")
        self.assertRegex(handler, r"button\.dataset\.review\s*!==\s*attempt\.action")
        self.assertRegex(handler, r"state\.kind\s*===\s*[\"']unavailable[\"']")
        self.assertIn("markReviewAttemptUnknown(attempt, state.message)", handler)
        self.assertRegex(handler, r"reviewWriteAttempt\s*=\s*null")
        self.assertRegex(handler, r"review-result[\"']\)\.textContent\s*=\s*state\.message")
        controls_start = teacher.index("function syncReviewAttemptControls()")
        controls_end = teacher.index("\nfunction markReviewAttemptUnknown(", controls_start)
        controls = teacher[controls_start:controls_end]
        self.assertIn("button.disabled = attempt", controls)
        self.assertIn('attempt.phase !== "UNKNOWN"', handler)
        self.assertIn("reviewWriteAttempt", teacher[teacher.index("function markReviewAttemptUnknown") :])

    def test_teacher_review_lists_remediation_history_for_all_published_workspaces(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        load_start = teacher.index("async function loadReviewQueue()")
        load_end = teacher.index('\ndocument.querySelectorAll("[data-action=', load_start)
        loader = teacher[load_start:load_end]
        self.assertIn('assignments.filter((item) => item.state === "PUBLISHED" && item.workspace)', loader)
        self.assertIn("const remediationResults = await Promise.all(published.map(async (assignment) =>", loader)
        self.assertIn("api.remediations(assignment.workspace.id)", loader)
        self.assertIn("remediationResults.flatMap", loader)
        self.assertIn("remediationReadResults = new Map(remediationResults.map((item) => [item.assignment.id, item]));", loader)
        self.assertIn("renderTeacherRemediationResults();", loader)
        self.assertIn("if (!remediationReadComplete) markRemediationStatusUnknown(error);", loader)

        render_start = teacher.index("function renderRemediationStatus(entries, errors = []) {")
        render_end = teacher.index("\nfunction markRemediationStatusUnknown(", render_start)
        renderer = teacher[render_start:render_end]
        self.assertIn('OPEN: "等待学生回应"', renderer)
        self.assertIn('RESPONDED: "已收到学生回应"', renderer)
        self.assertIn("remediation.response_submission_id", renderer)
        self.assertIn("回应提交 ${remediation.response_submission_id}", renderer)
        self.assertIn("errors.forEach(({ assignment, error }) => {", renderer)
        self.assertIn("补正读取失败，状态未知：${error}", renderer)
        self.assertIn('retry.dataset.remediationRetry = assignment.id;', renderer)
        self.assertIn('retry.textContent = "重试此任务补正状态";', renderer)
        self.assertIn("renderTeacherRemediationResults()", teacher)

        # The no-pending-submission branch keeps the separately rendered history visible.
        no_pending_start = loader.index("if (!reviewContext) {")
        no_pending_end = loader.index("    const { assignment, submission } = reviewContext;", no_pending_start)
        no_pending = loader[no_pending_start:no_pending_end]
        self.assertIn("remediationEntries.length", no_pending)
        self.assertIn("下方仍显示已发布任务的补正记录及状态", no_pending)
        self.assertLess(loader.index("renderTeacherRemediationResults()"), no_pending_start)

    def test_teacher_remediation_retry_is_assignment_scoped_and_discards_stale_results(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        retry_start = teacher.index("async function retryTeacherRemediation(assignmentId)")
        retry_end = teacher.index('\ndocument.querySelector("#remediation-status")', retry_start)
        retry = teacher[retry_start:retry_end]
        self.assertIn("previous.assignment.workspace.id", retry)
        self.assertIn("api.remediations(previous.assignment.workspace.id)", retry)
        self.assertIn("const viewGeneration = reviewLoadGeneration", retry)
        self.assertIn("viewGeneration !== reviewLoadGeneration", retry)
        self.assertIn("requestGeneration !== remediationRetryGenerations.get(assignmentId)", retry)
        self.assertIn("remediationReadResults.set(assignmentId", retry)
        self.assertNotIn("loadReviewQueue()", retry)

    def test_teacher_review_queue_retry_is_assignment_scoped_and_preserves_selected_detail(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        renderer_start = teacher.index("function renderReviewTaskChoices(items)")
        renderer_end = teacher.index("\nfunction collaborationModeLabel(", renderer_start)
        renderer = teacher[renderer_start:renderer_end]
        self.assertIn('button.dataset.reviewQueueRetry = item.assignment.id;', renderer)
        self.assertIn('button.dataset.reviewAssignment = item.assignment.id;', renderer)
        self.assertIn('button.setAttribute("aria-label", `查看“${taskTitle}”的复核详情`);', renderer)
        self.assertIn('button.setAttribute("aria-label", `重试“${taskTitle}”的复核队列`);', renderer)
        self.assertIn('button.setAttribute("aria-label", `重试“${taskTitle}”的复核详情读取`);', renderer)

        handler_start = teacher.index('document.querySelector("#review-task-list").addEventListener("click"')
        handler_end = teacher.index("async function loadReviewQueue()", handler_start)
        handler = teacher[handler_start:handler_end]
        self.assertIn('event.target.closest("[data-review-queue-retry]")', handler)
        self.assertLess(handler.index("retryTeacherReviewQueue(retry.dataset.reviewQueueRetry)"), handler.index("selectedReviewAssignmentId = button.dataset.reviewAssignment"))

        retry_start = teacher.index("async function retryTeacherReviewQueue(assignmentId)")
        retry_end = teacher.index("async function loadReviewQueue()", retry_start)
        retry = teacher[retry_start:retry_end]
        self.assertIn("readReviewQueueForAssignment(previous.assignment)", retry)
        self.assertIn("reviewQueueResults.set(assignmentId", retry)
        self.assertIn("viewGeneration !== reviewLoadGeneration", retry)
        self.assertIn("requestGeneration !== reviewQueueRetryGenerations.get(assignmentId)", retry)
        self.assertNotIn("api.listAssignments()", retry)
        self.assertNotIn("loadReviewQueue()", retry)

    def test_teacher_review_history_reads_all_published_assignments_and_fails_closed(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        loader_start = teacher.index("async function loadReviewHistory(published, requestId")
        loader_end = teacher.index("\nasync function retryReviewHistory()", loader_start)
        loader = teacher[loader_start:loader_end]
        self.assertIn("actions: [...(previous?.actions || [])]", loader)
        self.assertIn("api.reviewHistory(page.assignment.id, 0, 50)", loader)
        self.assertIn("result.review_actions", loader)
        self.assertIn("page.nextSequence = result.next_sequence", loader)
        self.assertIn("page.hasMore = result.has_more", loader)
        self.assertIn("const generation = requestId", loader)
        self.assertIn("if (generation !== reviewHistoryGeneration) return", loader)
        self.assertIn("catch (error)", loader)
        self.assertIn('errorStateFor(error, "读取复核历史")', loader)
        more_start = teacher.index("async function loadMoreReviewHistory()")
        more_end = teacher.index("\nasync function retryReviewHistory()", more_start)
        more_loader = teacher[more_start:more_end]
        self.assertIn("api.reviewHistory(page.assignment.id, page.nextSequence, 50)", more_loader)
        self.assertIn("page.actions.push(...result.review_actions)", more_loader)
        self.assertIn("const generation = reviewHistoryGeneration", more_loader)
        response = more_loader.index("const result = (await api.reviewHistory(page.assignment.id, page.nextSequence, 50)).data")
        stale_guard = more_loader.index("if (generation !== reviewHistoryGeneration) return", response)
        self.assertLess(stale_guard, more_loader.index("page.actions.push(...result.review_actions)"))
        self.assertLess(more_loader.index("if (generation !== reviewHistoryGeneration) return"), more_loader.index("button.disabled = false"))

        renderer_start = teacher.index("function renderReviewHistory(entries)")
        renderer_end = teacher.index("\nfunction markReviewHistoryUnknown(", renderer_start)
        renderer = teacher[renderer_start:renderer_end]
        for field in ("action.kind", "action.submission_id", "action.submission_version", "action.reason", "action.created_event_sequence"):
            self.assertIn(field, renderer)
        self.assertIn('ACKNOWLEDGE: "认可并关闭"', renderer)
        self.assertIn("当前没有复核动作记录", renderer)
        self.assertIn("不能确认页面中某次回执未知的请求", renderer)
        self.assertIn("item.textContent =", renderer)

        unknown_start = teacher.index("function markReviewHistoryUnknown(error)")
        unknown_end = teacher.index("\nasync function loadReviewHistory(", unknown_start)
        unknown = teacher[unknown_start:unknown_end]
        self.assertIn("reviewHistoryDirectoryError = state.message", unknown)
        self.assertIn("reviewHistoryPages.flatMap", unknown)
        self.assertIn("reviewHistoryGeneration += 1", unknown)
        self.assertIn("复核历史读取失败，状态未知", renderer)
        self.assertIn("任务目录刷新失败，目录状态未知", renderer)
        self.assertIn("保留已成功读取的历史记录", renderer)
        self.assertIn("当前没有已发布任务可读取复核历史。", renderer)
        self.assertIn("未请求历史 API", renderer)
        self.assertIn("!reviewHistoryPages.length && !reviewHistoryDirectoryError", renderer)
        self.assertLess(renderer.index("当前没有已发布任务可读取复核历史。"), renderer.index("API 返回：当前没有复核动作记录。"))
        retry_start = teacher.index("async function retryReviewHistory()")
        retry_end = teacher.index('\ndocument.querySelector("#review-history-retry")', retry_start)
        retry_handler = teacher[retry_start:retry_end]
        self.assertIn("正在刷新已发布任务目录；保留当前历史记录。", retry_handler)
        self.assertIn("if (generation === reviewHistoryGeneration) markReviewHistoryUnknown(error)", retry_handler)
        self.assertIn('document.querySelector("#review-history-retry").addEventListener("click", retryReviewHistory)', teacher)
        page = (ROOT / "apps" / "teacher-web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="review-history-list"', page)
        self.assertIn('id="review-history-more"', page)

    def test_teacher_review_queue_discards_stale_requests_before_any_state_write(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        start = teacher.index("async function loadReviewQueue()")
        end = teacher.index('\ndocument.querySelectorAll("[data-action=', start)
        loader = teacher[start:end]
        self.assertIn("const historyRequestId = ++reviewLoadGeneration", loader)
        self.assertIn('document.querySelector("#review-count").textContent = "?";', loader)
        self.assertIn("reviewEventGeneration += 1", loader)
        self.assertIn("await loadReviewHistory(published);\n    if (historyRequestId !== reviewLoadGeneration) return;", loader)
        self.assertRegex(loader, r"const assignments = \(await api\.listAssignments\(\)\)\.data\.assignments;\s+if \(historyRequestId !== reviewLoadGeneration\) return;")
        remediation_results = loader[loader.index("const remediationResults = await Promise.all"):loader.index("const remediationEntries =")]
        self.assertIn("if (historyRequestId !== reviewLoadGeneration) return;", remediation_results)
        loaded_assignments = loader[loader.index("const loadedAssignments = await Promise.all"):loader.index("const pendingAssignment =")]
        self.assertIn("if (historyRequestId !== reviewLoadGeneration) return;", loaded_assignments)
        self.assertRegex(loader, r"const workspace = await api\.getWorkspace\(submission\.workspace_id\);")
        self.assertIn("workspace.data.assignment_id !== pendingAssignment.assignment.id", loader)
        self.assertLess(loader.index("workspace.data.assignment_id !== pendingAssignment.assignment.id"), loader.index("reviewContext = { assignment: pendingAssignment.assignment"))
        self.assertRegex(loader, r"await showReviewSubmissionDetails\(reviewContext, historyRequestId\);\s+if \(historyRequestId !== reviewLoadGeneration\) return;")
        details_start = teacher.index("async function showReviewSubmissionDetails(")
        details_end = teacher.index("async function retryTeacherReviewQueue(", details_start)
        details = teacher[details_start:details_end]
        self.assertRegex(details, r"await loadReviewEvents\(submission\.workspace_id\);\s+if \(viewGeneration !== reviewLoadGeneration \|\| reviewContext\?\.submission\?\.id !== submission\.id\) return;")
        self.assertIn("updateTeacherReviewCount();", loader)
        self.assertNotIn("const refreshedQueue = await api.reviewQueue(assignment.id)", loader)
        self.assertIn("if (!reviewHistoryLoaded)", loader)
        self.assertIn("markReviewHistoryUnknown(error)", loader)
        self.assertIn("当前提交详情读取失败，状态未知", loader)

    def test_teacher_review_badge_is_unknown_for_partial_queue_reads_and_reuses_cached_total(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        start = teacher.index("function updateTeacherReviewCount()")
        end = teacher.index("\nfunction collaborationModeLabel(", start)
        helper = teacher[start:end]
        self.assertIn('results.some((item) => item.error || item.loading)', helper)
        self.assertIn('? "?"', helper)
        self.assertIn("results.reduce((total, item) => total + item.submissions.length, 0)", helper)

    def test_teacher_review_retries_use_independent_generations(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("let reviewHistoryGeneration = 0", teacher)
        self.assertIn("let reviewLoadGeneration = 0", teacher)
        self.assertIn("let reviewEventGeneration = 0", teacher)
        retry_start = teacher.index("async function retryReviewHistory()")
        retry_end = teacher.index('\ndocument.querySelector("#review-history-retry")', retry_start)
        retry = teacher[retry_start:retry_end]
        self.assertIn("++reviewHistoryGeneration", retry)
        self.assertNotIn("reviewLoadGeneration", retry)
        event_start = teacher.index("async function loadReviewEvents(")
        event_end = teacher.index('\ndocument.querySelector("#evidence-retry")', event_start)
        events = teacher[event_start:event_end]
        self.assertIn("const requestId = ++reviewEventGeneration", events)
        self.assertIn("requestId !== reviewEventGeneration", events)
        self.assertNotIn("reviewHistoryGeneration", events)
        history_start = teacher.index("async function loadReviewHistory(")
        history_end = teacher.index("\nasync function loadMoreReviewHistory()", history_start)
        history = teacher[history_start:history_end]
        self.assertIn("previousPagesByAssignment", history)
        self.assertIn("actions: [...(previous?.actions || [])]", history)

    def test_teacher_workspace_detail_failure_is_visible_and_retryable(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        load_start = teacher.index("async function loadReviewQueue()")
        load_end = teacher.index("document.querySelectorAll(\"[data-action='new-task']", load_start)
        loader = teacher[load_start:load_end]
        catch_start = loader.index("} catch (error) {")
        catch = loader[catch_start:]
        self.assertIn("所选任务详情读取失败，状态未知", catch)
        self.assertIn('empty.hidden = false', catch)
        self.assertIn("reviewDetailResults.set(selectedReviewAssignmentId", catch)

        handler_start = teacher.index('document.querySelector("#review-task-list").addEventListener("click"')
        handler_end = teacher.index("async function showReviewSubmissionDetails(", handler_start)
        handler = teacher[handler_start:handler_end]
        self.assertIn('event.target.closest("[data-review-detail-retry]")', handler)
        self.assertLess(handler.index("retryTeacherWorkspaceDetail(detailRetry.dataset.reviewDetailRetry)"), handler.index("selectedReviewAssignmentId = button.dataset.reviewAssignment"))

        retry_start = teacher.index("async function retryTeacherWorkspaceDetail(assignmentId)")
        retry_end = teacher.index("async function showReviewSubmissionDetails(", retry_start)
        retry = teacher[retry_start:retry_end]
        self.assertIn("readReviewQueueForAssignment(previous.assignment)", retry)
        self.assertIn("const submission = submissions.find((item) => item.id === previous.submission.id", retry)
        self.assertIn('["SUBMITTED", "RESUBMITTED"].includes(item.state)', retry)
        self.assertIn('["REVIEW_REQUIRED", "RESUBMITTED"].includes(workspace.data.state)', retry)
        self.assertLess(retry.index("readReviewQueueForAssignment(previous.assignment)"), retry.index("api.getWorkspace(submission.workspace_id)"))
        self.assertIn("此提交已不在当前待复核队列中。", retry)
        self.assertIn("api.getWorkspace(submission.workspace_id)", retry)
        self.assertIn('let retryStage = "review queue"', retry)
        self.assertIn('retryStage = "workspace detail"', retry)
        self.assertIn('const failedRead = retryStage === "review queue" ? "读取复核队列" : "读取工作区详情"', retry)
        self.assertIn('reviewQueueResults.set(assignmentId, { ...queue, loading: false, error: message })', retry)
        self.assertIn('待复核数量与提交状态未知', retry)
        self.assertIn('document.querySelector("#review-details").hidden = true', retry)
        self.assertIn("reviewContext = null", retry)
        self.assertIn("viewGeneration !== reviewLoadGeneration", retry)
        self.assertIn("selectedReviewAssignmentId !== assignmentId", retry)
        self.assertIn("reviewDetailRetryGenerations.get(assignmentId)", retry)
        self.assertNotIn("api.listAssignments()", retry)
        self.assertNotIn("loadReviewQueue()", retry)

        bound_queue_start = teacher.index("async function readReviewQueueForAssignment(")
        bound_queue_end = teacher.index("\n\n", bound_queue_start)
        bound_queue = teacher[bound_queue_start:bound_queue_end]
        self.assertIn("assignment.workspace.assignment_id !== assignment.id", bound_queue)
        self.assertIn("api.reviewQueue(assignment.id, assignment.workspace.id, assignment.version)", bound_queue)
        self.assertIn("workspace.data.assignment_id !== previous.assignment.id", retry)

    def test_student_agent_turn_unknown_receipt_retries_exact_question_and_freezes_input(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        self.assertRegex(student, r"let\s+(?:agentTurnAttempt|pendingAgentTurn)\s*=\s*null")
        send_start = student.index("async function sendQuestion(")
        send_end = student.index("\ndocument.querySelectorAll(\".file-item\")", send_start)
        send_question = student[send_start:send_end]

        # Source-structure assertion only; no browser event or visual behavior is inferred.
        self.assertRegex(send_question, r"agentTurnAttempt\s*\|\|\s*\{\s*workspaceId,\s*revision:\s*workspaceRevision,\s*question\s*\}")
        self.assertRegex(send_question, r"api\.agentTurn\([^\n]*(?:attempt|pendingAgentTurn)")
        for saved_field in ("workspaceId", "question", "revision"):
            self.assertRegex(send_question, rf"(?:attempt|pendingAgentTurn)\.{saved_field}")
        self.assertRegex(send_question, r"question\s*!==\s*agentTurnAttempt\.question")
        self.assertRegex(send_question, r"当前新输入已保留")
        self.assertIn("function syncAgentTurnControls()", student)
        self.assertRegex(student, r"syncAgentTurnControls\(\)[\s\S]{0,220}#send-agent")
        self.assertRegex(send_question, r"agentTurnAttempt\s*=\s*null")
        self.assertRegex(send_question, r"errorStateFor\(error,\s*[\"']发送问题[\"']\)")
        self.assertRegex(send_question, r"重试")
        self.assertIn("本机合成 API 已确认上一 Agent 回合", send_question)
        self.assertIn("把原问题放回输入框后重试；刷新会丢失本页重试信息", send_question)

    def test_student_unavailable_agent_turn_is_not_rendered_as_a_successful_reply(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        start = student.index("async function sendQuestion(")
        end = student.index("\ndocument.querySelectorAll(\".file-item\")", start)
        handler = student[start:end]
        unavailable = handler.index('if (result.data.turn.availability === "UNAVAILABLE")')
        normal_reply = handler.index("addApiReply(result.data.turn.response_text", unavailable)
        unavailable_branch = handler[unavailable:normal_reply]
        self.assertIn("agentTurnAttempt = null", unavailable_branch)
        self.assertIn("没有收到成功引导", unavailable_branch)
        self.assertNotIn('agentInput.value = ""', unavailable_branch)
        self.assertNotIn("addApiReply", unavailable_branch)
        self.assertNotIn("收到本机 scripted-demo 固定回复", unavailable_branch)

    def test_remediation_read_failure_has_a_specific_visible_student_state(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        start = student.index("async function loadStudentWorkspace(")
        end = student.index("\nfunction renderLineNumbers()", start)
        loader = student[start:end]

        # Require a failure path attached to the remediation read and a dedicated
        # visible status. This is a source assertion, not a rendered UI check.
        remediation_start = student.index("async function loadRemediations(")
        remediation_end = student.index("\nasync function loadStudentWorkspace(", remediation_start)
        remediation_tail = student[remediation_start:remediation_end]
        self.assertRegex(remediation_tail, r"catch\s*\(error\)")
        self.assertRegex(remediation_tail, r"renderRemediationStatus\(`补正状态未知，API 读取失败。\$\{state\.message\}`")
        self.assertIn('region.dataset.readState = "confirmed-with-error"', remediation_tail)
        self.assertIn("以下保留上次成功记录", remediation_tail)
        self.assertRegex(remediation_tail, r"errorStateFor\(error,\s*[\"']读取补正状态[\"']\)")
        self.assertIn("workspaceIdToRead", remediation_tail)
        self.assertIn("重新读取补正状态", student)
        self.assertNotRegex(remediation_tail, r"catch\s*\(error\)[\s\S]*?本机合成 API 已确认")

    def test_student_latest_submission_readback_is_separate_safe_and_truthful(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        page = (ROOT / "apps" / "student-web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="latest-submission-state"', page)
        self.assertIn('role="status" aria-live="polite" hidden', page)

        loader_start = student.index("async function loadLatestSubmission(")
        loader_end = student.index("\nfunction saveTaskDraft()", loader_start)
        loader = student[loader_start:loader_end]
        self.assertIn("api.latestSubmission(workspaceIdToRead)", loader)
        self.assertIn(".data.submission", loader)
        self.assertIn("const requestGeneration = ++latestSubmissionReadGeneration", loader)
        self.assertGreaterEqual(loader.count("requestGeneration !== latestSubmissionReadGeneration"), 2)
        self.assertGreaterEqual(loader.count("workspaceIdToRead !== workspaceId"), 2)
        self.assertNotIn("latestSubmissionReadInFlight", student)
        self.assertRegex(loader, r"catch\s*\(error\)")
        self.assertIn("重新读取提交记录", student)
        self.assertIn("本机合成 API 当前没有提交记录", student)
        self.assertIn("最近提交读取失败，当前状态未知", student)
        self.assertIn('region.dataset.readState = "confirmed-with-error"', loader)
        self.assertIn("以下保留上次成功记录", loader)
        self.assertIn("不能证明某次回执未知的提交请求就是这条记录", student)

        render_start = student.index("function renderLatestSubmission(submission) {")
        render_end = student.index("\nasync function loadLatestSubmission(", render_start)
        renderer = student[render_start:render_end]
        for field in ("submission.id", "submission.version", "submission.state", "submission.student_explanation", "snapshot.logical_name", "snapshot.size_bytes", "snapshot.sha256", "snapshot.content"):
            self.assertIn(field, renderer)
        self.assertIn("content.textContent = snapshot.content", renderer)
        self.assertNotIn("innerHTML", renderer)
        self.assertIn("await loadLatestSubmission(workspace.id)", student)
        self.assertIn("await loadLatestSubmission(attempt.workspaceId)", student)

        # The separate API readback only renders server state; it cannot resolve or
        # clear the frozen exact-request retry guard.
        self.assertNotIn("pendingSubmission = null", loader)
        self.assertIn("pendingSubmission = attempt", student)

    def test_student_empty_assignment_state_disables_workspace_interactions(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        state_start = student.index("function setWorkspaceState(state) {")
        state_end = student.index("\nfunction setSubmissionContentFrozen", state_start)
        state_body = student[state_start:state_end]
        self.assertIn('["IN_PROGRESS", "FEEDBACK_REQUIRED"].includes(state)', state_body)
        self.assertIn("setSubmissionContentFrozen(!workspaceInteractive", state_body)
        self.assertIn("syncAgentTurnControls();", state_body)

    def test_student_workspace_state_labels_are_human_readable_without_changing_wire_states(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        mapper_start = student.index("function workspaceStateLabel(state) {")
        mapper_end = student.index("\nfunction setWorkspaceState(state)", mapper_start)
        mapper = student[mapper_start:mapper_end]
        for state, label in (
            ("ASSIGNED", "已分配，准备开始"),
            ("IN_PROGRESS", "进行中"),
            ("PAUSED", "已暂停"),
            ("REVIEW_REQUIRED", "等待教师复核"),
            ("FEEDBACK_REQUIRED", "等待你补正"),
            ("RESUBMITTED", "已补交，等待教师复核"),
            ("CLOSED", "本轮已结束"),
        ):
            with self.subTest(state=state):
                self.assertIn(f'{state}: "{label}"', mapper)
        self.assertIn('if (!state) return "未连接";', mapper)
        self.assertIn('return labels[state] || "状态未知";', mapper)
        state_body = student[student.index("function setWorkspaceState(state) {"):student.index("\nfunction setSubmissionContentFrozen", student.index("function setWorkspaceState(state) {"))]
        self.assertIn('workspaceInteractive = ["IN_PROGRESS", "FEEDBACK_REQUIRED"].includes(state);', state_body)
        self.assertIn("workspaceStateLabel(state)", state_body)
        self.assertIn('document.querySelector("#task-picker-state").textContent = workspaceStateLabel(state);', state_body)
        self.assertIn("workspaceStateLabel(workspace.state)", student)
        submit_start = student.index('submissionForm.addEventListener("submit", async (event) => {')
        submit_end = student.index('\nsubmissionNote.addEventListener("input"', submit_start)
        submit_handler = student[submit_start:submit_end]
        self.assertIn('setWorkspaceState(result.data.submission.version === 1 ? "REVIEW_REQUIRED" : "RESUBMITTED");', submit_handler)
        self.assertNotIn('document.querySelector("#task-state").lastChild.textContent = " 已提交 · 合成";', submit_handler)

        freeze_start = student.index("function setSubmissionContentFrozen(frozen) {")
        freeze_end = student.index("\nfunction syncAgentTurnControls", freeze_start)
        self.assertIn("!workspaceInteractive", student[freeze_start:freeze_end])
        controls_start = student.index("function syncAgentTurnControls()")
        controls_end = student.index("\nfunction renderRemediationStatus", controls_start)
        self.assertIn("pending = !workspaceInteractive", student[controls_start:controls_end])

    def test_student_multiple_published_assignments_do_not_select_one_silently(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index("\nfunction renderLineNumbers", loader_start)
        loader = student[loader_start:loader_end]
        self.assertIn("const publishedAssignments = assignments.filter", loader)
        self.assertIn("if (!publishedAssignments.length)", loader)
        self.assertIn("picker.value = selectedAssignmentId", loader)
        self.assertIn('pickerState.textContent = "暂无可用任务"', loader)
        self.assertIn('if (!selectedAssignmentId)', loader)
        self.assertNotIn('publishedAssignments[0]', loader)
        self.assertIn('pickerState.textContent = "请选择任务"', loader)
        self.assertIn("请选择一个任务。系统不会按目录顺序或更新时间替你选择", loader)
        self.assertIn('publishedAssignments.find((item) => item.id === selectedAssignmentId)', loader)
        self.assertIn('id="task-picker"', (ROOT / "apps" / "student-web" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("api.pauseWorkspace(workspaceId, workspaceRevision, currentAssignmentId)", student)
        self.assertIn("taskDrafts.set(currentAssignmentId", student)
        self.assertIn("agentMessages: [...agentMessages.childNodes].map((node) => node.cloneNode(true))", student)
        self.assertIn("agentMessages.replaceChildren", student)
        self.assertIn("requestGeneration !== remediationReadGeneration", student)
        self.assertIn("agentTurnAttempt || proposalAcceptAttempt", student)

    def test_student_workspace_loader_blocks_active_task_switch_before_clearing_context(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index("\nfunction renderLineNumbers", loader_start)
        loader = student[loader_start:loader_end]
        guard = 'if (selectedAssignmentId && selectedAssignmentId !== currentAssignmentId && workspaceState === "IN_PROGRESS")'

        guard_index = loader.index(guard)
        reset_index = loader.index("setWorkspaceState(null)")
        self.assertLess(guard_index, reset_index)
        self.assertIn('picker.value = currentAssignmentId || ""', loader[guard_index:reset_index])
        self.assertIn("请先暂停当前任务，再切换到另一个任务。", loader[guard_index:reset_index])
        self.assertNotIn("if (workspaceId && workspaceId !== assignment.workspace.id && workspaceState === \"IN_PROGRESS\")", loader)

    def test_student_loader_rejects_cross_assignment_workspace_bindings(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index('\ndocument.querySelector("#task-picker").addEventListener', loader_start)
        loader = student[loader_start:loader_end]
        assignment_binding = loader.index("current.workspace.assignment_id !== assignment.id")
        workspace_binding = loader.index("workspace.assignment_id !== assignment.id")
        start_receipt_binding = loader.index("started.data.workspace.assignment_id !== assignment.id")
        self.assertIn("api.startWorkspace(workspace.id, workspace.revision, assignment.id)", loader)
        start_request = loader.index("api.startWorkspace(workspace.id, workspace.revision, assignment.id)")
        self.assertLess(assignment_binding, start_request)
        self.assertLess(workspace_binding, start_request)
        self.assertLess(start_receipt_binding, loader.index("workspaceRevision = started.revision"))
        self.assertIn('code: "invalid_response"', loader)
        self.assertIn("renderStudentTaskReadFailure(state.message, selectedAssignmentId)", loader)

    def test_student_workspace_and_latest_submission_reads_ignore_stale_tasks(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index('\ndocument.querySelector("#task-picker").addEventListener', loader_start)
        loader = student[loader_start:loader_end]
        self.assertIn("const loadGeneration = ++workspaceLoadGeneration", loader)
        self.assertGreaterEqual(loader.count("loadGeneration !== workspaceLoadGeneration"), 5)
        self.assertIn("loadGeneration === workspaceLoadGeneration", loader)
        self.assertIn("picker.disabled = true", loader)
        latest_start = student.index("async function loadLatestSubmission(")
        latest_end = student.index("\nfunction saveTaskDraft", latest_start)
        latest = student[latest_start:latest_end]
        self.assertIn("workspaceIdToRead !== workspaceId", latest)
        self.assertGreaterEqual(latest.count("workspaceIdToRead !== workspaceId"), 2)

    def test_student_task_read_failure_has_a_dedicated_retry(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        renderer_start = student.index("function renderStudentTaskReadFailure(")
        renderer_end = student.index("\nfunction setWorkspaceState(", renderer_start)
        renderer = student[renderer_start:renderer_end]
        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index('\ndocument.querySelector("#task-picker").addEventListener', loader_start)
        loader = student[loader_start:loader_end]
        self.assertIn('retry.textContent = "重新读取任务"', renderer)
        self.assertIn("loadStudentWorkspace(selectedAssignmentId)", renderer)
        self.assertIn("renderStudentTaskReadFailure(state.message, selectedAssignmentId)", loader)
        self.assertIn('pickerState.textContent = "读取失败 · 未知"', loader)

    def test_student_unknown_pause_requires_readback_before_switching(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        switch_start = student.index('document.querySelector("#task-picker").addEventListener')
        switch_end = student.index('document.querySelector("#pause-task").addEventListener', switch_start)
        switch = student[switch_start:switch_end]
        self.assertIn("if (pauseAttempt)", switch)
        pause_guard_start = switch.index("if (pauseAttempt)")
        pause_guard_end = switch.index("pendingSubmission ||", pause_guard_start)
        pause_guard = switch[pause_guard_start:pause_guard_end]
        self.assertIn('showToast("暂停结果尚未确认；请先重读当前任务状态。")', pause_guard)
        self.assertNotIn('#task-picker-state").textContent =', pause_guard)

        pause_start = student.index('document.querySelector("#pause-task").addEventListener')
        readback_start = student.index("async function readPauseAttemptState()", pause_start)
        pause_handler = student[pause_start:readback_start]
        self.assertIn("revision: workspaceRevision", pause_handler)
        self.assertIn('phase: error?.definitiveRejection === true ? "REJECTED_READBACK" : "UNKNOWN_WRITE"', pause_handler)
        self.assertIn("重读任务状态", pause_handler)
        self.assertIn("api.pauseWorkspace(workspaceId, workspaceRevision, currentAssignmentId)", pause_handler)
        self.assertIn("api.pauseWorkspace(attempt.workspaceId, attempt.revision, attempt.assignmentId)", pause_handler)
        self.assertIn("button.disabled = workspaceState !== \"IN_PROGRESS\" || pauseAttempt !== null", pause_handler)

        readback_end = student.index("\nfunction renderLineNumbers", readback_start)
        readback = student[readback_start:readback_end]
        self.assertIn("api.getWorkspace(attempt.workspaceId, attempt.assignmentId)", readback)
        self.assertIn('result.data.state === "PAUSED"', readback)
        self.assertIn('["IN_PROGRESS", "PAUSED"].includes(result.data.state)', readback)
        self.assertIn('attempt.phase === "REJECTED_READBACK"', readback)
        self.assertIn("retryPauseAttempt(attempt)", readback)
        self.assertIn("切换保持锁定", readback)


    def test_student_hides_previous_workspace_until_selected_task_is_read(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        loader_start = student.index("async function loadStudentWorkspace(")
        loader_end = student.index('\ndocument.querySelector("#task-picker").addEventListener', loader_start)
        loader = student[loader_start:loader_end]
        self.assertIn('document.querySelector("#remediation-state").hidden = true', loader)
        self.assertIn("workArea.hidden = true", loader)
        self.assertIn("taskRail.hidden = true", loader)
        self.assertIn("workArea.hidden = false", loader)
        self.assertIn("taskRail.hidden = false", loader)

    def test_student_unconfirmed_agent_turn_blocks_pause_and_task_switch(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        switch_start = student.index('document.querySelector("#task-picker").addEventListener')
        pause_start = student.index('document.querySelector("#pause-task").addEventListener', switch_start)
        pause_end = student.index('\ndocument.querySelector("#send-agent")', pause_start)
        switch = student[switch_start:pause_start]
        pause = student[pause_start:pause_end]
        self.assertIn("agentTurnAttempt", switch)
        self.assertIn("agentTurnAttempt", pause)
        self.assertIn("有请求尚未确认", switch)
        self.assertIn("有请求尚未确认", pause)

    def test_student_narrow_submission_snapshots_wrap_without_page_overflow(self) -> None:
        styles = (ROOT / "apps" / "student-web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".api-state {", styles)
        self.assertIn("overflow-wrap: anywhere;", styles)
        self.assertIn(".api-state pre { white-space: pre-wrap; overflow-wrap: anywhere; }", styles)

    def test_teacher_multiple_review_tasks_require_explicit_selection_and_keep_failures_visible(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        page = (ROOT / "apps" / "teacher-web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="review-task-list"', page)
        self.assertIn("function renderReviewTaskChoices(items)", teacher)
        self.assertIn("item.assignment.task.title", teacher)
        self.assertIn("待复核数量未知", teacher)
        self.assertIn('selectedReviewAssignmentId = button.dataset.reviewAssignment', teacher)
        self.assertIn('loadedAssignments.find((item) => item.assignment.id === selectedReviewAssignmentId)', teacher)
        self.assertNotIn('loadedAssignments.find((item) => item.submissions.length)', teacher)

    def test_teacher_review_directory_failure_has_scoped_retry_control(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        page = (ROOT / "apps" / "teacher-web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="review-directory-retry"', page)
        self.assertIn('failureStage = "读取任务目录";', teacher)
        self.assertIn('if (failureStage === "读取任务目录") {', teacher)
        self.assertIn('directoryRetry.hidden = false;', teacher)
        self.assertIn('empty.textContent = `任务目录刷新失败，复核任务列表状态未知：${state.message}`;', teacher)
        self.assertIn('document.querySelector("#api-state").textContent = failureStage === "读取任务目录"', teacher)
        self.assertIn('document.querySelector("#review-task-list").hidden = true;', teacher)
        self.assertIn('document.querySelector("#api-state").textContent = "教师任务目录读取成功；其他复核区域状态分别显示。";', teacher)
        self.assertIn('document.querySelector("#review-directory-retry").addEventListener("click", () => loadReviewQueue())', teacher)

    def test_teacher_empty_review_catalog_has_explicit_empty_queue_state(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("if (!published.length)", teacher)
        self.assertIn("当前没有已发布任务，因此没有可复核队列。", teacher)

    def test_teacher_title_validation_matches_api_utf8_byte_limit(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        preview_start = teacher.index("function updatePreview()")
        preview_end = teacher.index("\nfunction renderAssignment", preview_start)
        preview = teacher[preview_start:preview_end]
        self.assertIn('new TextEncoder().encode(task.title).length', preview)
        self.assertIn("titleBytes > 128", preview)
        self.assertIn('titleInput.setCustomValidity', preview)

    def test_teacher_review_reason_validation_matches_api_utf8_byte_limit(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('new TextEncoder().encode(field.value.trim()).length', teacher)
        self.assertIn("byteLength > 1024", teacher)
        self.assertIn('document.querySelector("#feedback-reason").addEventListener("input", validateReviewReasonBytes)', teacher)
        self.assertIn("if (!validateReviewReasonBytes())", teacher)

    def test_teacher_narrow_task_cards_keep_copy_readable(self) -> None:
        styles = (ROOT / "apps" / "teacher-web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".task-list { display: grid; grid-template-columns: minmax(0, 1fr); gap: 11px; }", styles)
        self.assertIn(".review-task-choice > span { min-width: 0; overflow-wrap: anywhere; }", styles)
        narrow_start = styles.index("@media (max-width: 760px)")
        narrow_end = styles.index("@media (prefers-reduced-motion", narrow_start)
        narrow = styles[narrow_start:narrow_end]
        self.assertIn(".welcome-art { display: none; }", narrow)
        self.assertIn(".template-body { flex: 1 1 calc(100% - 56px); }", narrow)
        self.assertIn(".editor-grid, .review-layout { grid-template-columns: minmax(0, 1fr); }", narrow)
        self.assertIn(".review-meta { flex-wrap: wrap; }", narrow)
        self.assertIn(".remediation-note { align-items: flex-start; flex-wrap: wrap; }", narrow)
        self.assertIn(".remediation-status { flex: 1 1 calc(100% - 33px); margin-left: 33px; white-space: normal; }", narrow)

    def test_teacher_page_does_not_force_a_360px_body_minimum(self) -> None:
        styles = (ROOT / "apps" / "teacher-web" / "styles.css").read_text(encoding="utf-8")
        self.assertNotRegex(styles, r"(?m)^body\s*\{[^}]*min-width\s*:\s*360px")

    def test_student_page_does_not_force_a_360px_body_minimum(self) -> None:
        styles = (ROOT / "apps" / "student-web" / "styles.css").read_text(encoding="utf-8")
        self.assertNotRegex(styles, r"(?m)^body\s*\{[^}]*min-width\s*:\s*360px")

    def test_teacher_review_uses_human_readable_collaboration_mode(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('if (mode === "QA_ONLY") return "仅问答"', teacher)
        self.assertIn('if (mode === "PROPOSE_WITH_STUDENT_CONFIRMATION") return "协作需确认"', teacher)
        self.assertIn('return "协作方式未知"', teacher)
        self.assertIn("collaborationModeLabel(assignment.task.collaboration_mode)", teacher)

    def test_teacher_event_read_failure_is_local_and_retryable(self) -> None:
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        helper_start = teacher.index("async function loadReviewEvents(")
        helper_end = teacher.index('\ndocument.querySelector("#evidence-retry").addEventListener', helper_start)
        helper = teacher[helper_start:helper_end]
        self.assertIn("api.events(workspaceId, 0, 50)", helper)
        self.assertIn("事件状态未知，读取失败", helper)
        self.assertIn("retry.hidden = false", helper)
        self.assertIn("preserveSameWorkspaceEvents", helper)
        self.assertIn("保留此工作区上次成功读取的事件", helper)
        self.assertIn("loadReviewEvents(reviewContext.submission.workspace_id)", teacher)
        self.assertLess(helper.index("timeline.replaceChildren()"), helper.index("try {"))

    def test_student_submission_success_advances_revision_from_required_dto(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        start = student.index('submissionForm.addEventListener("submit"')
        end = student.index("\n});", start)
        handler = student[start:end]
        self.assertIn("workspaceRevision = result.data.workspace_revision ?? result.revision ?? workspaceRevision", handler)

    def test_accepting_a_proposal_freezes_edit_inputs_until_api_outcome_is_known(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        accept_start = student.index('document.querySelector("[data-action=\'accept\']")')
        accept_end = student.index('document.querySelector("[data-action=\'reject\']")', accept_start)
        accept_handler = student[accept_start:accept_end]
        self.assertIn("setProposalDecisionPending(true)", accept_handler)
        self.assertRegex(accept_handler, r"catch\s*\(error\)[\s\S]*?setProposalDecisionPending\(false,\s*proposalAcceptAttempt\s*!==\s*null\s*\?\s*[\"']accept[\"']\s*:\s*null\)")
        self.assertRegex(accept_handler, r"proposalAcceptAttempt\s*=\s*attempt")
        self.assertRegex(accept_handler, r"api\.decideProposal\(attempt\.workspaceId,\s*attempt\.proposalId,\s*[\"']ACCEPTED[\"'],\s*attempt\.revision\)")
        self.assertRegex(accept_handler, r"targetFile:\s*currentFile[\s\S]{0,120}targetContent:\s*editor\.value")
        self.assertRegex(accept_handler, r"workingContent\[attempt\.targetFile\]\s*===\s*targetContent")
        freeze_start = student.index("function setSubmissionContentFrozen(")
        freeze_end = student.index("\nfunction syncAgentTurnControls(", freeze_start)
        freeze_controls = student[freeze_start:freeze_end]
        self.assertRegex(freeze_controls, r"proposalAcceptAttempt\s*!==\s*null")
        self.assertIn("editor.disabled = editorFrozen", freeze_controls)
        self.assertIn("button.disabled = editorFrozen", freeze_controls)
        self.assertRegex(student, r"if\s*\(proposalAcceptAttempt\s*!==\s*null\)\s*return")

    def test_student_reject_and_takeover_unknown_outcomes_keep_exact_attempt(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("let proposalDecisionAttempt = null", student)
        start = student.index("async function decideProposal(decision, action)")
        end = student.index("\ndocument.querySelector(\"[data-action='reject']\")", start)
        handler = student[start:end]
        self.assertIn("proposalDecisionAttempt ||", handler)
        self.assertIn("proposalId,", handler)
        self.assertIn("workspaceId,", handler)
        self.assertIn("revision: workspaceRevision", handler)
        self.assertIn("decision,", handler)
        self.assertIn("api.decideProposal(attempt.workspaceId, attempt.proposalId, attempt.decision, attempt.revision)", handler)
        self.assertIn('state.kind === "unavailable" ? action : null', handler)
        self.assertRegex(handler, r"if\s*\(!\['unavailable', 'error', 'unknown'\]\.includes\(state\.kind\)\)[\s\S]*?proposalDecisionAttempt\s*=\s*null")
        controls_start = student.index("function syncAgentTurnControls()")
        controls_end = student.index("function renderRemediationStatus", controls_start)
        self.assertIn("proposalDecisionAttempt !== null", student[controls_start:controls_end])
        send_start = student.index("async function sendQuestion(")
        self.assertIn("proposalDecisionAttempt !== null", student[send_start:start])
        self.assertIn("result.data.workspace_revision ?? result.revision ?? workspaceRevision", handler)
        self.assertIn("setApiState(\"本机合成 API 已确认提案决定", handler)
        self.assertIn("留在当前页面，使用原按钮重试同一请求", handler)
        self.assertIn('decideProposal("REJECTED", "reject")', student)
        self.assertIn('decideProposal("STUDENT_TAKEOVER", "takeover")', student)

    def test_unconfirmed_proposal_accept_blocks_reject_and_takeover_even_for_generic_errors(self) -> None:
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        accept_start = student.index('document.querySelector("[data-action=\'accept\']")')
        accept_end = student.index('document.querySelector("[data-action=\'reject\']")', accept_start)
        accept_handler = student[accept_start:accept_end]
        self.assertIn('setProposalDecisionPending(false, proposalAcceptAttempt !== null ? "accept" : null);', accept_handler)
        self.assertIn("setApiState(\"本机合成 API 已确认接受建议", accept_handler)
        self.assertIn("留在当前页面，使用“接受并查看修改”重试同一请求", accept_handler)
        self.assertIn("if (!['unavailable', 'error', 'unknown'].includes(state.kind))", accept_handler)
        decision_start = student.index("async function decideProposal(decision, action)")
        decision_end = student.index('\ndocument.querySelector("[data-action=\'reject\']")', decision_start)
        decision_handler = student[decision_start:decision_end]
        self.assertRegex(decision_handler, r"async function decideProposal\(decision, action\)\s*\{\s*if\s*\(proposalAcceptAttempt\s*!==\s*null\)\s*return")
        self.assertLess(decision_handler.index("if (proposalAcceptAttempt !== null) return;"), decision_handler.index("api.decideProposal("))

    def test_strict_dto_response_failures_are_visible_and_never_claim_success(self) -> None:
        client = (ROOT / "apps" / "workspace-client.mjs").read_text(encoding="utf-8")
        self.assertIn('code: "invalid_response"', client)
        self.assertIn('kind: "unavailable"', client)
        self.assertIn("服务响应格式不符合本机合成 DTO", client)
        teacher = (ROOT / "apps" / "teacher-web" / "app.js").read_text(encoding="utf-8")
        student = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        for source in (teacher, student):
            with self.subTest(page="teacher" if source is teacher else "student"):
                self.assertIn("errorStateFor(error", source)
                self.assertRegex(source, r"state\.message")
        self.assertRegex(client, r"if\s*\(!envelope\s*\|\|\s*envelope\.schema_version\s*!==\s*[\"']skillshift-api/v1[\"']\s*\|\|\s*!hasText\(envelope\.request_id\)\s*\|\|\s*!validData\)")


if __name__ == "__main__":
    unittest.main()
