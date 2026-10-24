# P3 task lifecycle and review isolation report

## Task R0-P3-104: student active-state and teacher task-choice browser validation

- Gate: R0 P3 local synthetic product validation; overall result remains **PARTIAL**.
- Read-only audits `R0-P3-104A-STUDENT-FLOW-COVERAGE-AUDIT` and `R0-P3-104B-TEACHER-FLOW-COVERAGE-AUDIT` found no additional student lifecycle defect. They identified a missing browser record for `IN_PROGRESS` and a teacher usability risk: repeated generic task-action button names made keyboard/screen-reader task identity unclear.
- Minimal product change: `apps/teacher-web/app.js` now gives each task action a task-specific `aria-label` for queue retry, detail retry, and opening details. Visible copy and routing are unchanged. `tests/test_workspace_frontend_html.py` checks all three accessible-name variants.
- Microsoft Edge 154 / Playwright, loopback-only WSGI Harness, synthetic in-memory data:
  - Student explicitly selected assignment A in `student-switch-workspace-fail`. `IN_PROGRESS` displayed as “进行中” in the selector and task card; pause and submission controls were enabled. At 390×844 and 1280×900, `clientWidth == scrollWidth`; screenshots were visually inspected.
  - Teacher `teacher-multi-queue` rendered three distinct task-specific accessible names. Keyboard focus and Enter on task B opened B; the selected detail title matched that row. Screenshot was visually inspected.
- Browser evidence: `browser-r0-p3-task-choice-a11y-2026-09-26/`. `browser-run.json` SHA-256 `1814ECC44CC42EC002DCED823C56E654A4077EEF089775695C713310DD3A3C6B`. Screenshots: student 390px `A8711918F2C891F87D04D988EFD57303B996A69CAA5526BC116347172F7D631A`; student 1280px `6CF62B5526010D72076694FD41FD61CA4D9191C5457C10E1902207E4174FAD25`; teacher keyboard B `2FCEABFEF91B8F1EDC20C5F7111F3E27FEA60C438098EB5004349FA1787E9E37`.
- Current verification: full Python suite 212 tests, 211 passed/1 skipped; Node client 43/43; Workspace API 38/38; WSGI 11/11; frontend static 48/48; three JS syntax checks, Python compileall, Harness py_compile, Schema JSON parse, `git diff --check` passed. The skip remains Windows symlink-creation permission and is not symlink-safety evidence.
- An initial availability probe treated Harness HTTP 404 as startup failure; the probe was corrected to use the requested route. An initial student assertion expected an exact card label while the UI intentionally appends “· 合成”; it was corrected to assert the state prefix. No product defect was inferred from these probe mistakes.
- An initial targeted unittest package-name command failed because `tests/` is not an importable package; the three suites were rerun directly as `python tests/test_workspace_api.py`, `python tests/test_workspace_wsgi.py`, and `python tests/test_workspace_frontend_html.py`, all passing.
- Limitations: finite browser states and viewport sizes; this is not a WCAG conformance audit, full P4, production HTTP/service evidence, persistence, real identity/data/model/ECS/deployment, or secure code execution. No owner decision required. Commit: `NONE`.

## Task R0-P3-105: catalog failure during an explicit task switch

- Gate: R0 P3 local synthetic product validation; result **PASS for this bounded browser path**, overall project remains **PARTIAL**.
- Read-only gap audit found that initial assignment-catalog failure and a selected task's Workspace failure had browser evidence, but catalog failure specifically while switching after pausing an active task did not. This path is relevant to active `REQUIREMENTS_SPEC.md` error/conflict boundaries and `QUALITY_SPEC.md` failure visibility/recovery expectations.
- Harness change only: `p3_teacher_generation_fault_server.py` now offers `student-switch-catalog-fail`, seeding two synthetic assignments with A active/B assigned and returning a one-shot WSGI 503 on the third student assignment-directory read (initial page read, explicit A selection read, then switch-to-B read). Retry reads pass through normally. No product behavior changed.
- Edge 154 / Playwright at 390×844: A was explicitly selected and paused; B was explicitly selected; the directory GET returned 503. The page showed “读取失败 · 未知”, hid the old A Workspace and task rail, and issued no B assignment detail, B Workspace, or start request before retry. The retry retained the already explicit B choice; subsequent B detail/Workspace reads succeeded and exactly one start POST targeted B's Workspace. No A task title appeared in recovered B details; no horizontal overflow. Screenshots were visually inspected.
- A first harness attempt faulted on read #2 because selecting A itself performs a directory refresh; the deterministic fault was moved to read #3. A first assertion compared an assignment ID with the distinct Workspace ID; it was corrected to bind the start request to the Workspace ID in B's assignment DTO. These were test-script/fixture corrections, not product failures.
- Evidence directory: `browser-r0-p3-switch-catalog-failure-2026-09-26/`. `browser-run.json` SHA-256 `265777F3C91F51D9D1F23A786CD4C4B3CD6A9504A8F15DDF6EF3E91E260BF629`; failure screenshot `3492B8191B4DEC9917E3B35EC3B10E6E38C74D6BD30C216279A8417AC5D69C93`; recovered B screenshot `01E92CE8B633EF3565F6B9B01B7A7A18C42F794972AE1E9CAB391325CFAE29E0`; Harness stderr `0D5E6FF3B9B6002A43F02134706DAB543C5E19A25734E152085CA7BBB634071E`; stdout `F16F2EC122CE88512ED4BE3C311E07A5457E2A3F71CDEF87C949E20077256824`.
- Post-change verification: `python -m unittest discover -s tests` — 212 tests, 211 pass/1 skip; `node --test tests/workspace-client.test.mjs` — 43/43; `python tests/test_workspace_api.py` — 38/38; `python tests/test_workspace_wsgi.py` — 11/11; `python tests/test_workspace_frontend_html.py` — 48/48; JS syntax checks, Python compileall, Harness py_compile, Schema JSON parse, and `git diff --check` passed. The only skip remains Windows symlink-creation permission and is not symlink-safety evidence.
- Limitations: one loopback synthetic WSGI server, fixed demo role/data, one viewport, and a finite fault ordering. This is not production integration, multi-process persistence, full P4, or secure execution evidence. No owner decision required. Commit: `NONE`.

## Task R0-P3-106: committed pause with lost browser receipt

- Gate: R0 P3 local synthetic product validation; bounded behavior **PASS after minimal fix**, overall project remains **PARTIAL**.
- A read-only audit selected this unverified transition: server commits A's pause but browser never receives the receipt; UI must preserve the recovery action and keep B blocked until authoritative readback confirms PAUSED.
- Confirmed defect and fix: while pause outcome was unknown, attempting to select B correctly restored A, but overwrote the “重读任务状态” control with plain text. `apps/student-web/app.js` now uses a toast for the blocked attempt so the in-place recovery action remains available. `tests/test_workspace_frontend_html.py` asserts this guard does not replace the recovery control.
- Microsoft Edge 154 / Playwright at 390×844, using `student-agent-delay` loopback WSGI seed (synthetic A active, B assigned). Browser routing called `route.fetch()` for the real synthetic pause POST, observed server HTTP 200, then aborted the browser's original route. The page showed pause outcome unknown. An explicit B selection reverted to A and left the readback button visible. Readback returned PAUSED; only then did selecting B load B and issue one start POST bound to B's Workspace. A was re-read after the switch and remained PAUSED. Screenshot geometry: client width 390, scroll width 390.
- Evidence directory: `browser-r0-p3-pause-receipt-lost-2026-09-26/`. `browser-run.json` SHA-256 `A760A35B98F5706D1E587E3D0C4A3A1A16BF02D5573B7BFF21A96DF728C83CCE`; unknown-state screenshot `4F57D9935F2DF7FA8E15F9089172714E54ACAF9361AAC7B514F5E9570E068B5B`; confirmed pause and switch screenshot `FF3BFE631640109A8B6B84E7E669EE01843BD22D3BDEEE7B2F3E20CE01834372`; Harness stderr `264C4ADF7CA57A3FD3ABF947C8D5A9BF09C65CBCBB700CF8BA1A836E378D5BA8`; stdout `F98B8AE007DC8A3FFC68BD7D679F3CD3C7C50BD6E4FF10DED889970EED610857`.
- Post-fix verification: full Python 212 tests, 211 pass/1 skip; Node 43/43; Workspace API 38/38; WSGI 11/11; frontend static 48/48. JS syntax checks, Python compileall, Harness py_compile, Schema JSON parse, and `git diff --check` passed. The sole skip is Windows symlink-creation permission, not symlink-safety evidence.
- Limitations: Playwright route interception simulated the browser losing the response after a server 200; it is not proof of packet loss on a real network. Synthetic process memory, fixed role, one viewport; not durable or production integration, full P4, or secure execution evidence. No owner decision required. Commit: `NONE`.

## Task R0-P3-107: teacher create receipt lost and same-request retry

- Gate: R0 P3 local synthetic browser validation; bounded behavior **PASS**, overall project remains **PARTIAL**.
- Read-only audit selected the unverified ordering where a teacher task is created but the browser loses the create receipt. Existing write-attempt logic was not changed.
- Microsoft Edge 154 / Playwright at 1280×900 with the loopback `empty` Harness. The first `POST /api/v1/demo/teacher/assignments` was fetched to the actual synthetic WSGI API (201), then the browser route was aborted. The teacher saw “创建回执未确认”; form fields and new-task entry were frozen; only the original publish operation remained enabled. Retrying that operation resent the exact same JSON DTO and Idempotency-Key; the API replayed the create receipt (201), then published once (200). The task directory contained exactly one published task with the intended title and one bound Workspace. Pending and recovered screenshots were visually inspected.
- Evidence directory: `browser-r0-p3-teacher-create-receipt-lost-2026-09-26/`. `browser-run.json` SHA-256 `D6880A9086D73EE2CFB12BE276127ABCA46BE0102132DC663211DC3F57B846AD`; pending screenshot `2AE4E062191DA0DEA42C4D93B5A4130CBC9515C45A4AEEB34843B941D4F2C97A`; recovered task list `86FC07D22100094525A8FB727106D1B691F9C02F0CE9963081225F6E55E9DF59`; Harness stderr `1110D81E0C7AAB3BE6E64C417DC9C90F9233E703FD8FE7759C001608BBAC1587`; stdout `A4EAD367E6883849E8D627C5CEA57AAB7EF63A31FBE9C5D0D8BF5C850F43C881`.
- The first browser script iteration intercepted the initial GET as well as the create POST, so it did not reach the intended failure state; the final run filtered on POST and confirmed the first create was committed before dropping the receipt. This was harness-script correction only.
- No product/test code changed for Task107. The post-Task106 current regression remains the verified matrix: Python 212 (211 pass/1 skip), Node 43/43, Workspace API 38/38, WSGI 11/11, frontend static 48/48; syntax/compile/schema/diff checks passed. The skip is Windows symlink creation permission, not symlink-safety evidence.
- Limitations: fixed synthetic DTO and in-memory service; browser-boundary receipt loss, not real packet loss, durable idempotency or production integration. No owner decision required. Commit: `NONE`.

- Task ID: `R0-WORKSPACE-P3-TASK-SWITCH-REVIEW-ISOLATION-001`
- Gate: R0 P3 local synthetic prototype
- Result: **PARTIAL** (core browser workflows, selected responsive breakpoints, teacher event/history/remediation isolation, and student task-read/uncertain-turn recovery and two delayed student read-retry switch orderings pass locally; other delayed orderings and full device coverage remain unverified)
- Date: 2026-09-26

## Scope and changes

Implemented the supplied single-active-task rule in the local synthetic control plane. A student can pause an `IN_PROGRESS` workspace into `PAUSED`, resume a paused workspace, and start another task only when no other workspace is `IN_PROGRESS`. The API returns HTTP 409 `active_task_exists` without changing the requested task when another task is active. Pause and start/resume use the existing idempotency key, `If-Match` revision, and per-workspace event sequence rules.

The student page now requires an explicit choice when multiple published tasks exist, presents an empty state when none exist, blocks task switching during an active task or unresolved writes, and keeps file drafts, Agent messages, and proposal display state keyed by assignment in page memory. Remediation reads use generation guards so a prior task response cannot overwrite the selected task. During a task read, the prior workspace panel is hidden; task-directory and selected-task read failures are unknown and independently retryable. An unresolved Agent-turn receipt blocks pause and switching until the exact question is retried or its outcome is resolved. The teacher page shows a per-task review overview with title, publication state, pending count or explicit unknown/error, and only opens details after selection. A failed event read is isolated to the event region with its own retry control. Per-task queue and remediation reads remain individually caught; history and remediation errors retain separate unknown states and retries; generation guards continue to reject stale page responses.

Files changed:

- `apps/agent-first/agent_first/workspace_api.py` — pause/resume transition and single active workspace enforcement.
- `apps/workspace-client.mjs` — accept `PAUSED` workspace DTO and validate pause receipt.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` — include the `PAUSED` wire state.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` — document pause/resume and mutual exclusion.
- `apps/student-web/app.js`, `apps/student-web/index.html`, `apps/student-web/styles.css` — explicit task selector, pause control, task-scoped drafts, stale-load guards, hidden previous-task details during reads, task-read retry, unresolved Agent-turn switch block, and long snapshot wrapping.
- `apps/teacher-web/app.js`, `apps/teacher-web/index.html`, `apps/teacher-web/styles.css` — explicit task review selection, per-task failure visibility, event-local retry, stale timeline clearing, readable collaboration labels, narrow review layout, and correct per-task remediation error messages.
- Both page HTML files now set a role-specific `<base>` URL so the documented no-trailing-slash entry loads relative assets and module imports correctly.
- `tests/test_workspace_api.py`, `tests/test_workspace_frontend_html.py`, `tests/test_workspace_wsgi.py`, `tests/workspace-client.test.mjs` — direct API lifecycle and source/client/static-route/responsive-style guard coverage.

## Verification

- `python -m unittest discover -s tests -p 'test_*.py'` — **189 total, 188 passed, 1 skipped**. The skip is Windows symlink creation permission (`WinError 1314`); it is not symlink-safety evidence.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_frontend_html.py'` — **28/28 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_wsgi.py'` — **11/11 passed**.
- `node --test tests/workspace-client.test.mjs` — **37/37 passed**.
- `node --check apps/student-web/app.js` — passed.
- `node --check apps/teacher-web/app.js` — passed.
- `node --check apps/workspace-client.mjs` — passed.
- `python -m compileall -q apps/agent-first tests` — passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` — passed.
- `git diff --check` — passed.
- Direct API lifecycle test creates and publishes two tasks, starts A, verifies B is rejected, pauses A, starts B, verifies A cannot resume while B runs, then resumes A. It submits different snapshots to A/B, creates a remediation only for B, and confirms latest submissions and remediation reads remain workspace-scoped.
- Local HTTP browser walk-through at `http://127.0.0.1:8765/demo/student/` and `/demo/teacher/` used two synthetic tasks. It verified no implicit selection, active-task switch rejection, pause, B start, independent A/B drafts and scripted-demo conversation state, return to A, A-only submission snapshot, teacher overview counts, explicit A selection, request-remediation, student version-2 resubmission, and teacher acknowledge/close.
- Both no-trailing-slash entry paths (`/demo/student` and `/demo/teacher`) were also opened. This found that relative CSS/module URLs resolved from `/demo/`; adding each page's role-specific `<base>` fixed initialization, and both pages then loaded live task data. Desktop screenshots were visually inspected.
- Follow-up responsive checks used explicit browser viewport overrides. At 390 CSS px, student empty/multi-task and loaded-submission views and teacher task center, review overview, and selected review detail showed no document-level horizontal overflow (document widths stayed at or below the viewport). Teacher review layout changed from one column at 760 px to two columns at 761 px without page overflow. Student long snapshot hashes/content initially expanded the document to 477 px at 390 px; CSS wrapping reduced document width to the 390 px viewport. Teacher task-template body initially collapsed to 18 px, and selected review details expanded the page to 485 px; mobile flex/grid minimums and readable mode labels corrected these. Browser screenshots were visually checked at 390 px.
- Temporary loopback WSGI wrappers injected one 503 first for task B's review-queue GET and then for task B's event GET. For the event test, both synthetic tasks had independent pending submissions; the browser showed task A's successful timeline, then on switching to B showed “事件状态未知，读取失败”, an empty timeline (no A events retained), and a dedicated “重读事件” button. Retrying succeeded and displayed only B events (`assignment-2`, `workspace-2`, `submission-2`). A and B overview rows remained visible.
- A temporary threaded loopback WSGI server delayed task A's event response by five seconds. The browser selected A and immediately selected B while A was pending; after the delayed A response completed, the selected review remained B and the timeline still contained only B's `assignment-2`, `workspace-2`, and `submission-2` events. This validates the teacher event generation/context guard for the tested ordering; it does not cover every possible network interleaving.
- Read-only subagent audits identified a stale teacher timeline risk on event-read failure, missing student workspace-loader generation checks, an unresolved Agent-turn attempt that did not block task switching, and stale prior-task details during a failed task read. The teacher event loader clears the prior timeline before each read. Student assignment/workspace loading uses a generation guard and keeps the picker disabled during reads; latest-submission receipts require both the active request generation and matching Workspace ID. Source regression tests cover these guards.
- A synthetic one-shot 503 for the student task catalog showed a visible unknown state, a dedicated “重新读取任务” action, and no workspace editor until retry; retry loaded the task. A one-shot 503 for task B's assignment read after pausing A hid A's workspace details and remediation state; retry loaded B. A one-shot Agent-turn 503 on A left the exact question pending; attempting to switch to B or pause was blocked, retrying the same question succeeded, and only then could A be paused and B selected. These are bounded local browser checks, not production integration.
- One-shot 503s for task B review-history and workspace B remediation reads were injected together. Task A's successful history action and open remediation remained visible; B appeared as unknown in the corresponding sections with the full retryable API failure reason. Explicitly selecting B retried the page reads and restored both tasks' history/remediation records. The browser run found and the implementation fixed a rendering mismatch (error versus message) that had previously displayed undefined.

## Evidence limits and risks

This remains an in-memory local synthetic API and local browser demonstration. No real identity, real student/teacher data, real model, production database, deployment, or student code execution was used. Draft restoration exists only in the current page memory; refresh clears drafts. Workspace-level backend records and revisions remain independently keyed. This does not establish cross-process atomicity or production concurrency safety. Queue failure isolation was browser-verified with a one-shot 503. The teacher event delayed-response race was browser-verified for one controlled ordering. Teacher history and remediation failures were also browser-injected once each, with successful results retained per task and retry restoring both. Two delayed student read-retry orderings (latest-submission and remediation failure after an explicit task switch) were browser-tested in Tasks044–045. Other delayed student read/write and network interleavings remain untested. Responsive QA covered 390, 760, and 761 CSS px, not the full device matrix or widths below the documented 360 px minimum.

Historical baseline in `WORKSPACE_P3_DTO_CONFLICT_RETRY_GUARDS_REPORT_2026-09-26.md` remains historical; this run's counts above are the freshly executed values.

## Acceptance

- Single active workspace, pause/switch/resume, no implicit API switch: **PASS** for direct in-memory API tests.
- Student task choice, empty/multiple states, page-memory state separation, unresolved-write switch block: **PASS** for tested local browser/API flow; page-memory drafts do not survive refresh.
- Teacher task overview and explicit selection, request-remediation, resubmission review, and acknowledge/close: **PASS** for the tested local synthetic browser flow.
- Per-task queue failure isolation: **PASS** for one browser-injected synthetic 503; A's successful queue result remained visible while B was explicitly unknown and retryable.
- Teacher event-timeline clearing, independent retry, and stale A-response rejection after selecting B: **PASS** for the tested synthetic 503/retry and one five-second delayed-response ordering. Teacher history/remediation task-local error visibility and recovery: **PASS** for the tested synthetic 503 paths; the rendering mismatch found in the first fault run was corrected and covered by the frontend static test. Student task-read failure isolation/retry and unresolved Agent-turn pause/switch blocking: **PASS** for the tested synthetic 503 paths. Student stale-response isolation after switching during delayed latest-submission and remediation retries: **PASS** for the two tested synthetic orderings (Tasks044–045); other delayed student response orderings remain **PARTIAL**.
- No-trailing-slash static page entry initialization: **PASS** after the role-specific `<base>` fix.
- Selected responsive checks at 390, 760, and 761 CSS px: **PASS** for the tested pages and layouts; not a full device matrix.
- Production / P4 readiness: **NOT CLAIMED**.

## Git

- Branch: `codex/r0-teacher-task-authoring`
- Commit: `NONE`
- The checkout already contained extensive uncommitted and untracked user work before this task. No unrelated files were reverted or removed.

## Follow-up verification — 2026-09-26

Task ID: `R0-WORKSPACE-P3-PAUSE-READBACK-AND-TEACHER-GENERATION-004`  
Gate: R0 P3 local synthetic  
Result: **PARTIAL**

This follow-up addresses two read-only audit findings without changing product scope:

- A student pause error now retains the exact Workspace ID and original revision, shows a dedicated readback action, and blocks switching while the outcome is unresolved. `PAUSED` readback confirms pause. `IN_PROGRESS` after an uncertain write offers an exact retry with the original revision and the client's pending idempotency key. If that exact write is definitively rejected, a subsequent authoritative readback updates the revision and enables a fresh, explicit pause action. Failed readback remains unknown and locked.
- Teacher full review loads, review-history reads, and event reads now use separate request generations. A full review refresh invalidates an older event request; a history retry no longer cancels the rest of a full review load; older same-Workspace event retries cannot overwrite a newer response.

Files changed in this follow-up:

- `apps/student-web/app.js` — pause attempt phase/revision, exact retry, explicit Workspace readback, and fail-closed task-switch guard.
- `apps/teacher-web/app.js` — independent full-load, history, and event generation guards.
- `tests/test_workspace_frontend_html.py` — source regression checks for pause recovery and separate teacher generations.
- `tests/workspace-client.test.mjs` — response-drop retry retains the original Idempotency-Key and If-Match revision even when the Workspace read reports a newer revision.
- `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_pause_readback_fault_server.py` — reusable loopback-only in-memory fault harness; it commits one pause while returning 503, then returns 503 for the first exact-Workspace GET.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md` — current evidence and stage description synchronization.

Fault-injection evidence: two fresh local synthetic runs used the loopback harness and browser. In the first, pause committed but the response was replaced with HTTP 503; the first exact-Workspace GET also returned 503. The page showed unknown, disabled task interactions, and offered “重读任务状态”; the next read showed `PAUSED` and unlocked task switching. In the second run, the injected pause response was dropped before mutation; a fixed scripted-demo turn advanced the Workspace revision from 3 to 4, then the first exact-state GET returned 503. The page retained the unresolved attempt and, after the next read returned `IN_PROGRESS`, offered “重试原暂停请求”. Retrying that exact attempt returned the expected stale-revision 409; a following authoritative read synchronized revision 4, cleared the rejected attempt, and enabled the student to explicitly pause again. That fresh pause succeeded and the page displayed `PAUSED`. These are bounded browser interactions against the local synthetic WSGI adapter, not production integration. Teacher history/full-load/event concurrency permutations remain source-level only.

Latest verification commands and results for this follow-up:

- `python -m unittest discover -s tests -p 'test_*.py'` — **191 total, 190 passed, 1 skipped**. The skip remains the Windows symlink-creation privilege limitation and is not symlink-safety evidence.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_wsgi.py'` — **11/11 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_frontend_html.py'` — **30/30 passed**.
- `node --test tests/workspace-client.test.mjs` — **38/38 passed**.
- JavaScript syntax checks for student, teacher, and shared client; Python compile check; JSON Schema parse; and `git diff --check` — passed.

The initial full-suite run printed Windows AppContainer runner location diagnostics but exited successfully; the symlink test remained the sole skip. No real users, data, model, ECS, external service, or student code were used. The local fault server was stopped after the check. P3 remains **PARTIAL** because teacher request-order races and student delayed-read ordering remain browser-unverified, and responsive coverage is not a full device matrix. No owner decision is needed.

## Follow-up verification — 2026-09-26 (continuation)

Task ID: `R0-WORKSPACE-P3-UNCERTAIN-PAUSE-AND-READ-ISOLATION-005`  
Gate: R0 P3 local synthetic  
Result: **PARTIAL**

This continuation fixed two audit findings and added controlled browser evidence for the associated UI boundaries:

- A pause receipt with HTTP 200 but an invalid DTO is now treated as an uncertain write, not a definitive rejection. `WorkspaceApiError.definitiveRejection` is true only for an actual HTTP 4xx response; malformed or unreadable success receipts keep the pending idempotency key. If an authoritative read shows `IN_PROGRESS` at a newer revision, the student UI retains the pause attempt and retries with the original revision/key instead of issuing a fresh pause.
- If a teacher has a successfully loaded submission queue but the selected Workspace detail read fails, the review overview now exposes an explicit unknown state and changes that selected task's button to “重试详情读取”. A subsequent click retries the selected task. Retry start also clears any prior nested detail error; a successful detail load restores the page connection status.
- Same-scope successful results are retained during a later failed read: student remediation/latest-submission regions preserve the last successful result when a follow-up read fails; teacher review history retains actions from the last successful page while showing the new page's failure; teacher events retain the last successful timeline for the same Workspace while marking the latest read unknown. Task/Workspace selection starts from a fresh region so a previous task's content is not carried forward.

Dynamic local browser evidence, using one synthetic in-memory task/submission at a time:

- Teacher Workspace-detail GET was injected as a one-shot 503 after the review queue succeeded. The page kept the task overview and queue count, displayed “状态未知” and “重试详情读取”; retry loaded the submission, Workspace revision, and event timeline, and removed the stale error.
- For the same selected teacher task, the first event GET was held for 12 seconds and then returned synthetic 503. While it was pending, a second explicit selection of the same task started a newer full review load; that event GET succeeded. After the delayed 503 completed, the browser still showed “事件读取成功” and the same three events. This verifies the same-Workspace old-failure/new-success ordering for this controlled sequence.
- The first teacher review-history GET was held for 20 seconds and then returned synthetic 503. While it was pending, a second review-page refresh started a newer full review load; the newer history GET succeeded at 11:37:11, and the old request returned 503 at 11:37:20. After both completed, the browser continued to show “历史读取成功”. This verifies the history-generation guard for this controlled full-load/retry ordering; it does not cover concurrent pagination or every request permutation.
- A subsequent teacher-history read was injected as a one-shot 503 after one successful review action had loaded. The page marked the new history read unknown while retaining the previous action in the history list.
- A same-Workspace event reread was injected as a one-shot 503 after a successful timeline read. The page marked the new read unknown, retained the prior three events, and exposed “重读事件”. Changing Workspaces still clears the prior timeline before reading the new Workspace.
- Student task A's latest-submission GET was delayed for 8 seconds after A was explicitly selected. During the pending read, the student selected task B and its Workspace started normally. When A's valid response completed late, the page remained on B, showed B's Workspace as `IN_PROGRESS`, and kept B's empty latest-submission state; A's submission did not leak into B's page.
- Student task A's remediation GET was separately delayed for 8 seconds while A had a synthetic open remediation. During the pending read, the student explicitly selected task B; after A's valid remediation response completed late, B remained selected and continued to show “当前没有待补正请求,” with no A remediation text. This confirms the remediation-region workspace/generation guard for this controlled ordering.

Subagent audits also identified that a malformed HTTP 200 pause receipt had not been covered by the previous transport-drop test, the teacher Workspace detail error was written into a hidden region, and same-region retries discarded previously successful display data. The local implementation and source regression assertions now cover those findings. The event race previously attempted with only one observed event request is not counted as evidence; the 12-second two-request sequence above is the valid same-task interleaving.

Verification commands and results for this continuation:

- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_wsgi.py'` — **11/11 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_frontend_html.py'` — **31/31 passed**.
- `node --check apps/student-web/app.js`, `node --check apps/teacher-web/app.js`, and `node --check apps/workspace-client.mjs` — passed.
- `python -m compileall -q apps/agent-first tests` and `python -m py_compile artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py` — passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` — passed.
- `git diff --check` — passed.

The full-suite run emitted AppContainer runner path diagnostics but exited successfully; the sole skip remains Windows symlink-creation privilege and is not symlink-safety evidence. The final student-remediation and teacher-history harness variants were Python-compiled separately after the full-suite command; they use the same bounded loopback WSGI/browser route and add no product code or automated test. The temporary fault server was stopped after the runs. These are local loopback WSGI/browser checks only. There are still no real users, identities, data, models, ECS calls, deployments, or student-code execution. P3 remains **PARTIAL** pending broader multi-task fault combinations and responsive/device coverage. No owner decision is needed.

## Follow-up verification — 2026-09-26 (same-scope retry retention and residual audit)

Task ID: `R0-WORKSPACE-P3-SAME-SCOPE-RETRY-RETENTION-006`  
Gate: R0 P3 local synthetic  
Result: **PARTIAL**

This stage preserves the last successful display result when a same-scope refresh fails, while still marking the latest read unknown and exposing the relevant retry. A task/Workspace change starts a fresh region, so prior-task content is not carried over. The implementation details and dynamic teacher checks are recorded in the continuation above.

Three bounded parallel audits were completed:

- Student Agent request acknowledgment and task-switch guards: no concrete source gap found. The client retains the original Workspace ID, revision and question for unresolved retries; switching and pausing stay blocked while unresolved. Evidence remains source assertions and client transport tests, not a browser interaction for this specific path.
- Teacher task queue, review history, remediation and event isolation: no additional concrete source gap found. Per-task failures and retry affordances are present; a failed selected Workspace detail read remains visible without discarding the queue. Remaining weakness is dynamic verification of additional combined failure permutations.
- Narrow layouts: both pages enforce a 360px minimum width, so 320px viewports would overflow by at least 40px. No product requirement defines 320px as supported; record this as an unverified support boundary, not a confirmed defect. A real Chrome 132 geometry probe at 360px and 390px measured document width equal to viewport for both pages; the student task picker and teacher task-choice row fit within their containing regions. At 320px, both pages measured 360px document width, confirming the expected 40px overflow. Long-title wrapping and empty/unknown/conflict/retry state visual fit still need rendered review.

A one-off rendered geometry check used the existing system Python Playwright package with the installed Chrome 132 executable; no project dependency was added. Student and teacher pages were measured at 320px, 360px and 390px. At 360px and 390px, document width matched the viewport; the teacher task-choice row and student selector fit their containing boxes. At 320px, both pages retained a 360px document width. A synthetic Workspace GET 503 rendered the student unknown/read-failure state at 320px. The first default Playwright Chromium launch could not run because its bundled browser executable is absent; the installed Chrome path provided the geometry run. This checks layout geometry, not a full visual review. The attempted teacher 503 sequence did not yield reliable new evidence and is excluded; prior teacher detail 503/retry browser evidence remains the cited result. The local server was stopped afterward.

The full local suites already run for this continuation remain the latest test evidence: Python 192 total (191 passed, 1 skipped), Node 39/39, Workspace API 35/35, WSGI 11/11, frontend static 31/31; JavaScript syntax checks, Python compile checks, harness compile, Schema parse, and `git diff --check` passed. The sole skip is Windows symlink-creation privilege and is not security evidence. No product source change was made in this stage.

Known limits remain: same-scope student retry retention has static-source assertions but no dynamic browser injection in this stage; teacher combined failure permutations and full responsive/device coverage are incomplete. No owner decision is needed. Commit: `NONE`.

## Follow-up verification — 2026-09-26 (student readback and teacher multi-task fault isolation)

Task ID: `R0-WORKSPACE-P3-MULTI-TASK-QUEUE-AND-STUDENT-READBACK-010`  
Gate: R0 P3 local synthetic  
Result: **PARTIAL**

This stage added two loopback-only fault-harness modes to `p3_teacher_generation_fault_server.py` and used the installed Chrome 132 with Python Playwright for bounded browser checks. No student source was executed.

Dynamic browser evidence:

- **Teacher multi-task queue and remediation isolation:** three synthetic assignments A/B/C were seeded, each with a text-only submission; C also has an open remediation action. A's review-queue GET and remediation GET each returned one real loopback HTTP 503. The page simultaneously showed A's queue and remediation as unknown, B's queue count as 1, C's open remediation and review history, and no cross-task overwrite. Explicitly opening B displayed B's detail. Clicking A's explicit retry refreshed A successfully; A and B both then showed one pending submission, while C's remediation and history remained visible. The retry button explicitly selects A's detail as expected; a first test assertion that expected B to remain selected after clicking A was corrected to match that user action. No product code changed.
- **Student remediation read/retry:** the first exact Workspace remediation GET returned 503. The student page showed an independent unknown state and “重新读取补正状态”. Clicking it returned the seeded open remediation; the latest-submission region continued to show its independent successful read.
- **Student latest-submission retention after success:** the student explicitly selected the seeded task and first read `submission-1` successfully. Submitting the requested synthetic correction returned HTTP 201; the following exact-Workspace latest-submission GET returned loopback HTTP 503. The page retained the original submission ID, version and text snapshots, marked the latest read unknown, exposed “重新读取提交记录”, and separately stated that the submission write had been accepted.

Three bounded parallel audits found no additional student Agent acknowledgment or teacher source-level queue/history/remediation isolation defect. The student audit confirmed the latest-submission refresh path is reachable through successful submission followed by readback. A same-scope refresh of remediation after a successful read has no visible entry point: the loader is invoked on task selection, which resets/hides that region, or through the retry shown after failure. Its prior-success retention branch is therefore not dynamically user-triggerable from the current UI. Initial remediation failure and retry are now browser-verified; this limitation is recorded rather than adding a new refresh control without a product requirement.

Harness changes are test-only and local: `teacher-multi-queue` seeds three synthetic tasks and independently faults A's queue and remediation reads; `student-retention` faults the second latest-submission GET after a successful initial read; `student-remediation-fail` faults the first remediation GET. Existing fault modes are retained. The server bound only to `127.0.0.1` and was stopped after each run.

Verification commands and results:

- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_wsgi.py'` — **11/11 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_frontend_html.py'` — **31/31 passed**.
- JS syntax checks for student, teacher and shared client; `python -m compileall -q apps/agent-first tests`; harness `py_compile`; Schema JSON parse; and `git diff --check` — passed.
- Browser harness commands: `python artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py teacher-multi-queue`, `... student-retention`, and `... student-remediation-fail`; assertions ran through Python Playwright against installed Chrome 132.

The full-suite output included AppContainer runner path diagnostics but exited successfully. The sole skip remains Windows symlink-creation privilege and is not symlink-safety evidence. Historical handoff values (Python 179/178/1; Node 36/36) remain historical; the current live suite remains Python 192/191/1 and Node 39/39. No real users, data, model, ECS, external service, deployment, or student code was used. More teacher concurrency permutations, same-scope remediation refresh after a prior success, and complete responsive visual QA remain open. No owner decision is needed. Commit: `NONE`.

## Follow-up verification — 2026-09-26 (teacher review-history pagination failure)

Task ID: `R0-WORKSPACE-P3-TEACHER-HISTORY-PAGINATION-012`  
Gate: R0 P3 local synthetic  
Result: **PARTIAL**

The previous source audit identified that no dynamic test reached the teacher history “load more” path. The loopback harness now has a `teacher-history-pagination` mode that seeds 51 legitimate, fixed synthetic review actions through the local API workflow (submission, REQUEST_EXPLANATION, and a subsequent synthetic submission), then returns one real loopback HTTP 503 for a nonzero `after_sequence` history page.

Chrome 132 browser evidence:

- The initial review-history page displayed 50 action rows and exposed the next-page control.
- Clicking “load more” caused the second page GET to return 503. The page displayed a task-scoped unknown/error row and retry affordance while retaining all 50 action rows from page one.
- Clicking the history retry reloaded page one successfully and retained all 50 actions; the next-page control remained available.
- Clicking “load more” again returned the final action successfully. The page displayed all 51 actions and hid the retry control.

The API log confirmed the failed request used the next cursor (`after_sequence=102`) and returned HTTP 503, followed by a successful first-page reload and a successful second-page retry. No production UI code changed. The audit also reconfirmed student pause/switch generation guards and that 320px is not specified as supported; 360/390px geometry was already measured, while the broader state-by-state visual matrix remains incomplete.

Files changed in this stage:

- `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py` — adds the 51-action pagination fault mode using only fixed synthetic API records and text snapshots; no execution path is invoked.
- This report and `docs/CURRENT_STATE.md`, `README.md`, `docs/README.md` — record pagination evidence, current gate and remaining coverage boundaries.

Verification commands and results:

- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_wsgi.py'` — **11/11 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_frontend_html.py'` — **31/31 passed**.
- JS syntax checks for student, teacher and shared client; `python -m compileall -q apps/agent-first tests`; harness `py_compile`; Schema JSON parse; and `git diff --check` — passed.
- Browser harness: `python artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py teacher-history-pagination`; assertions ran through Python Playwright against installed Chrome 132.

The AppContainer runner printed temporary-path diagnostics but the full suite exited 0. The sole skip remains the Windows symlink-creation privilege limitation and is not security evidence. Historical handoff values (Python 179/178/1; Node 36/36) remain historical; current live results are Python 192/191/1 and Node 39/39. No real identities, student/teacher data, model, ECS, deployment or student code were used. Remaining P3 work includes other teacher request-order combinations, the remediation same-scope refresh branch without a visible trigger, and full visual state coverage at 360px and 390px; the product-supported minimum viewport remains undefined. No owner decision is needed. Commit: `NONE`.

## Task R0-WORKSPACE-P3-RESPONSIVE-STATE-REVIEW-013 — 360/390px failure-state visual QA

Scope: rendered review of two already-covered failure paths at 360px and 390px using the local synthetic WSGI/HTTP harness and installed Chrome 132. No product source changes were made.

Student remediation read failure:

- At both viewport widths, selecting the explicit synthetic task caused the remediation GET to return an actual loopback HTTP 503. The page showed the remediation state as unknown with a visible “重新读取补正状态” control; the independently successful latest-submission snapshot remained visible.
- `document.documentElement.scrollWidth` equaled the viewport width at 360px and 390px. The retry control was visible within the remediation status region. Screenshots: `browser-r0-p3-state-qa-2026-09-26/student-remediation-503-360px.png` and `student-remediation-503-390px.png`.

Teacher history pagination failure:

- After the first 50 synthetic history rows loaded, loading the next page caused a real loopback HTTP 503. At both widths, the interface kept the 50 first-page actions, showed a history-unknown status and “重试读取”, and hid “加载更多” while the page request was in error. The rendered list contained 51 children (50 retained action rows plus the task-scoped error row).
- Document width matched each viewport; the history status, retry control and history list fit their containers without horizontal overflow. Screenshots: `browser-r0-p3-state-qa-2026-09-26/teacher-history-503-360px.png` and `teacher-history-503-390px.png`.

Subagent read-only audits confirmed the relevant student and teacher selectors and the boundary that no product requirement currently defines a 320px supported minimum. These screenshots cover the named failure states only; they do not complete the broader empty/conflict/long-title/breakpoint visual matrix or establish accessibility or production browser support. The CSS 360px minimum remains an observed implementation boundary, not an approved product decision. Both local loopback servers were stopped after capture.

Verification commands for this visual-only step:

- `python artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py student-remediation-fail` and `... teacher-history-pagination` — local synthetic servers bound to `127.0.0.1`; browser logs confirmed actual HTTP 503 responses for the targeted reads.
- Python Playwright against installed Chrome 132 — assertions/readouts at 360px and 390px, screenshots listed above; document widths were 360 and 390 respectively.
- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**; the skip is Windows symlink-creation privilege unavailable, not security evidence.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**; API **35/35**, WSGI **11/11**, frontend static **31/31**.
- JS syntax checks for student, teacher and shared client; `python -m compileall -q apps/agent-first tests`; harness `py_compile`; Schema JSON parse; and `git diff --check` — passed. The full Python run exited 0 despite temporary AppContainer runner path diagnostics.

No owner decision is needed to continue checks at 360px/390px. A product decision would be needed only to claim a supported minimum below the existing CSS 360px floor. Product gate remains PARTIAL; Commit: `NONE`.

## Task R0-WORKSPACE-P3-STUDENT-CATALOG-UNKNOWN-RETRY-015 — explicit selection and retry recovery

Scope: test the student task-catalog failure/retry in a real local browser and close a product-rule violation. The product contract requires explicit student choice and forbids implicit task selection.

Evidence and implementation:

- A new one-shot `student-catalog-fail` mode in the synthetic loopback harness returned an actual HTTP 503 for the initial student assignments GET.
- Browser evidence at 360px and 390px showed task state unknown, a visible “重新读取任务” control, no selected task, hidden `.work-area` and `.task-rail`, and no document horizontal overflow.
- Before the fix, the successful retry automatically opened the sole published task. Server logs confirmed the retry was followed by assignment detail and workspace GETs without a student task choice. This violated the explicit-selection rule even though the directory contained only one task.
- `apps/student-web/app.js` now requires an explicit selected task for every non-empty catalog, without a single-entry implicit fallback. A successful catalog reload with no selected ID leaves the workspace hidden, presents “请选择一个任务”, and clears the stale “读取失败 · 未知” picker status. `tests/test_workspace_frontend_html.py` locks the unconditional selection guard and absence of `publishedAssignments[0]` fallback.
- Retest: the first catalog GET returned HTTP 503; clicking retry returned HTTP 200 and kept selection empty with one explicit task option and hidden workspace; selecting that option then fetched and displayed the matching task. The status changed from unknown to “请选择任务”. The same failure state was checked at 360px and 390px with document widths 360 and 390. Screenshots are in `browser-r0-p3-state-qa-2026-09-26/student-catalog-503-360px.png`, `student-catalog-503-390px.png`, and `student-catalog-retry-390px.png`.

Files changed in this stage:

- `apps/student-web/app.js` — remove implicit first-task selection and clear stale read-failure status after catalog retry.
- `tests/test_workspace_frontend_html.py` — regression assertions for explicit selection and no first-item fallback.
- `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py` — add the one-shot synthetic task-directory 503 mode; loopback only.
- This report, `docs/CURRENT_STATE.md`, `README.md`, and `docs/README.md` — record the evidence, fix, remaining P3 risks and test results.

Verification:

- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**; `test_workspace_wsgi.py` — **11/11 passed**; `test_workspace_frontend_html.py` — **31/31 passed**.
- JS syntax checks, `python -m compileall -q apps/agent-first tests`, harness `py_compile`, Schema JSON parse and `git diff --check` — passed. The full Python test process printed temporary AppContainer runner path diagnostics but exited 0; the sole skip remains Windows symlink-creation privilege unavailable and is not security evidence.
- Browser harness: `python artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py student-catalog-fail`; Python Playwright against installed Chrome 132. Logs confirmed one actual 503, successful catalog retries, no workspace/detail request until explicit choice, then matching task detail/workspace reads.

The reported hash above for Task 013 is superseded by this update to the same rolling report path; the new hash is recorded in the latest `CURRENT_STATE.md` entry. Other remaining P3 work: dynamically verify student in-flight delayed successful Agent receipt during pause/switch, teacher delayed successful detail response after task selection changes, and broader responsive empty/conflict/long-title/breakpoint states. No owner decision is needed for those synthetic checks. Product gate remains PARTIAL; Commit: `NONE`.

## Task R0-WORKSPACE-P3-STUDENT-AGENT-DELAYED-RECEIPT-016 — pending Agent write isolation

Scope: inject a delay before one synthetic Agent-turn request is handled, then verify the in-flight UI blocks pause/switch and the eventual successful reply remains task-scoped. No production source code changed.

Evidence:

- Added `student-agent-delay` to the loopback harness. It seeds two fixed synthetic assignments, starts A without submitting it, and delays the first A `agent-turns` POST for five seconds before passing it to the existing WSGI API. This preserves a real, successful API response after the delay; it does not mock the browser response or call a model.
- Chrome 132 sent exactly one Agent-turn POST. During its pending interval, selecting B reverted the picker to A and showed a pending-request message; clicking pause produced no pause POST. After the successful Agent reply arrived, its question/reply appeared in A. Only then did pause POST succeed and switch to B complete.
- B loaded with its own title and state; its Agent pane did not contain A’s question or reply. The harness log showed the delayed A turn response followed by A pause, then B workspace read/start. No overlapping in-progress task was observed.
- Screenshots: `browser-r0-p3-state-qa-2026-09-26/student-agent-delay-pending-A.png`, `student-agent-delay-resolved-A.png`, and `student-agent-delay-selected-B.png`.

Files changed in this stage: `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py` adds the isolated no-submission A/B seed and one-shot delayed successful Agent-turn mode; this report and `docs/CURRENT_STATE.md` record evidence. The read-only student subagent independently identified this exact uncovered scenario and acceptance criteria.

Regression commands after the catalog fix and Agent-delay harness change:

- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**; `test_workspace_wsgi.py` — **11/11 passed**; `test_workspace_frontend_html.py` — **31/31 passed**.
- JS syntax checks, Python compileall, harness py_compile, JSON Schema parse and `git diff --check` — passed. The full Python run exited 0 with temporary AppContainer path diagnostics; the only skip remains inability to create a symlink under this Windows permission profile and is not security evidence.

Remaining P3 work: the teacher selected-A detail success arriving after B selection is still only source-audited, not dynamically verified; broad responsive empty/conflict/long-title/breakpoint coverage also remains incomplete. No owner decision is needed. Product gate remains PARTIAL; Commit: `NONE`.

## Task R0-WORKSPACE-P3-TEACHER-DETAIL-STALE-SUCCESS-017 — stale detail response isolation

Scope: dynamically test the teacher generation guard when a successful Workspace-detail response for A returns after the teacher has selected B. No product source code changed.

Evidence:

- Added `teacher-detail-delay` to the local synthetic harness. It seeds three fixed synthetic review tasks with independent submissions, then delays the first exact GET for A’s teacher Workspace detail by five seconds before allowing the real WSGI API to answer.
- In Chrome 132, the teacher explicitly selected A and initiated the delayed GET, then selected B while A was pending. B’s title, B-only submission snapshots and B events loaded before A returned.
- The delayed A GET returned HTTP 200. After it returned, the selected title, B snapshot hash/text, and B timeline remained unchanged. Browser request capture showed one event GET, for `workspace-2` (B); no event GET was emitted for stale `workspace-1` (A).
- Screenshots: `browser-r0-p3-state-qa-2026-09-26/teacher-detail-delay-pending-A-selected-B.png` and `teacher-detail-delay-resolved-A-still-B.png`.
- This reproduces the stale-success ordering identified by the read-only teacher audit. Existing generation guard prevented the old response from entering the selected detail path; no product fix was needed.

Files changed in this stage: the test-only `p3_teacher_generation_fault_server.py` adds `teacher-detail-delay` mode; this report and `docs/CURRENT_STATE.md` capture results. The three-task seed is reused; the existing queue-fault mode remains unchanged. No real identities/data, models, ECS, deployment or student code were involved.

Final regression for Tasks 015–017:

- `python -m unittest discover -s tests -p 'test_*.py'` — **192 total, 191 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**; `test_workspace_wsgi.py` — **11/11 passed**; `test_workspace_frontend_html.py` — **31/31 passed**.
- JS syntax checks, Python compileall, harness py_compile, JSON Schema parse and `git diff --check` — passed. The full Python run exited 0 despite temporary AppContainer runner path diagnostics; the sole skip remains Windows symlink-creation privilege unavailable and is not security evidence.

Remaining P3 work includes broader responsive state coverage (empty/conflict/long title/breakpoints), any untested student Agent delayed-readback variants, and the product boundary for adding a same-scope remediation refresh trigger. Product gate remains PARTIAL; no owner decision is needed for more bounded synthetic checks; Commit: `NONE`.

## Task R0-WORKSPACE-P3-PENDING-CONFLICT-VISUAL-018 — narrow pending Agent conflict state

Scope: rendered Chrome review of task switch and pause attempts while a real synthetic Agent-turn request is pending, at 360px and 390px.

Evidence:

- With A’s Agent-turn POST delayed by the `student-agent-delay` loopback mode, selecting B reverted the picker to A. Clicking the still-visible pause control did not send a pause POST; the status read “有请求尚未确认，暂不能暂停或切换。”
- At both widths, the selected task remained A and document width matched the viewport (360/360 and 390/390). The native task select, pause button and status text stayed visible; status wrapped onto a separate line as needed without clipping or overlap. The pause button remained visually enabled, with the click guard providing the explicit explanation and no write request. The independent subagent audit found no specification requiring a disabled control instead of this guarded interaction.
- Screenshots: `browser-r0-p3-state-qa-2026-09-26/student-agent-pending-conflict-360px.png` and `student-agent-pending-conflict-390px.png`.

This stage changed no product code. It reuses the actual delayed success path; the server returned HTTP 200 after the screenshots and was stopped. Full suite and static regression immediately before this visual-only stage: Python 192 (191 pass, 1 skip), Node 39/39, API 35/35, WSGI 11/11, frontend static 31/31; JS/Python compilation, Schema JSON and `git diff --check` passed. The only skip remains inability to create a symlink with current Windows privileges, not security evidence.

Remaining: empty/unknown and long-title/reason responsive states, teacher task/detail states at narrow widths, and the full breakpoint matrix. Product minimum width is still unspecified; 320px overflow remains an observed boundary, not an established requirements defect. No owner decision is needed to continue 360/390px checks. Product gate remains PARTIAL; Commit: `NONE`.

## Task R0-WORKSPACE-P3-TEACHER-MULTI-TASK-NARROW-019 — teacher overview and selected detail at 360/390px

Scope: inspect the three-task teacher review overview and explicitly selected task B details at 360px and 390px in Chrome 132, including full-page snapshots and event history.

Evidence:

- All three synthetic task rows and their selection buttons remained visible at both widths. Each button had a nonzero bounding box within `#review-task-list`; list `scrollWidth` equaled its `clientWidth` (269/269 at 360px, 299/299 at 390px).
- After selecting B, the selected title and submitted text snapshots identified B; its event timeline contained `assignment-2`, `workspace-2`, and `submission-2`. `#review-details`, `#review-snapshots` and `#evidence-timeline` fit their containers; document widths were exactly 360 and 390px. The page used a single-column review layout at both widths, and the full-page screenshots showed readable wrapped titles, snapshot hashes/content, feedback controls, remediation panel and history rows without overlap or horizontal clipping.
- Screenshots: `teacher-multitask-overview-full-360px.png`, `teacher-multitask-overview-full-390px.png`, `teacher-multitask-detail-B-full-360px.png`, `teacher-multitask-detail-B-full-390px.png` in the browser QA directory.
- Independent read-only teacher audit confirmed the relevant selectors and CSS boundaries. It flagged same-named “查看此任务” buttons and dynamic overview announcement as accessibility verification risks; no project accessibility acceptance target exists, so these are unverified risks, not confirmed defects.

No source files changed. The `teacher-detail-delay` harness was used as an ordinary three-task synthetic data source; its delayed A branch was not triggered during this viewport-only inspection. No real accounts/data or student code were used. 320px minimum support remains unspecified. Product gate remains PARTIAL; Commit: `NONE`.

## Task R0-WORKSPACE-P3-EMPTY-CATALOG-RETRY-020 — empty state and recovered catalog distinction

Scope: audit and verify successful empty catalogs separately from failed reads, at student and teacher views, including a student 503 followed by an empty 200 response. Only the local loopback synthetic WSGI service and fixed empty data were used.

Specification audit:

- The read-only subagent checked `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`, `specs/R0-STUDENT-WORKSPACE/README.md`, and `specs/R0-TEACHER-WORKSPACE/README.md`. The control-plane contract requires explicit UI states for an empty queue and service failure; the student/teacher specs require visible failure/empty states and do not prescribe exact copy. No source conflict was found.
- A successful empty student catalog after an earlier failure must clear the prior unknown label because the current read is confirmed and empty. A teacher with no published tasks must explicitly say there is no review queue. Both changes are consistent with the active requirements.

Evidence and changes:

- Browser inspection of a successful empty catalog at 360px and 390px showed no selected task, a disabled “当前没有可用任务” selector, hidden workspace and task rail, and document width equal to the viewport.
- Before this fix, retrying after a failed catalog read with a successful empty response left the old “读取失败 · 未知” label beside the empty selector. `apps/student-web/app.js` now displays “暂无可用任务” in this branch.
- Before this fix, the teacher review view with an empty catalog showed generic copy asking the teacher to choose a task. `apps/teacher-web/app.js` now explicitly reports “当前没有已发布任务，因此没有可复核队列。” and clears selection/details/count.
- Added `student-empty-retry` to the local-only test harness: first student catalog GET is actual HTTP 503; retry is actual HTTP 200 with an empty catalog. Chrome 132 at 390px confirmed the state changes from unknown to empty, remains unselected, keeps workspace/rail hidden, and has 390px document width. Request capture and service logs recorded `[503, 200]`.
- Teacher empty review and student empty catalog were checked at both 360px and 390px with no horizontal overflow. Screenshots: `student-empty-360px.png`, `student-empty-390px.png`, `teacher-empty-review-360px.png`, `teacher-empty-review-390px.png`, `student-empty-retry-failed-390px.png`, `student-empty-retry-success-390px.png` under `browser-r0-p3-state-qa-2026-09-26/`.
- `tests/test_workspace_frontend_html.py` now asserts the recovered empty picker label and explicit teacher empty-queue copy.

Files changed in this stage: `apps/student-web/app.js`, `apps/teacher-web/app.js`, `tests/test_workspace_frontend_html.py`, and `p3_teacher_generation_fault_server.py` implement and verify the minimal empty/retry distinction; this report, `docs/CURRENT_STATE.md`, `README.md`, and `docs/README.md` record the current evidence and limits.

Verification:

- `python -m unittest discover -s tests` — **193 total, 192 passed, 1 skipped**. The full run exited 0. Temporary AppContainer runner path diagnostics appeared; the only skip is inability to create a symlink under the current Windows permission profile, not security evidence.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**; `test_workspace_wsgi.py` — **11/11 passed**; `test_workspace_frontend_html.py` — **32/32 passed**.
- `node --check apps/student-web/app.js`, `node --check apps/teacher-web/app.js`, `node --check apps/workspace-client.mjs`; `python -m compileall -q apps tests`; harness `py_compile`; and `git diff --check` — passed. `git diff --check` reported only the existing CRLF-to-LF notice for `docs/CURRENT_STATE.md`.
- A first targeted unittest invocation by module path failed because this repository's `tests` directory is not an importable package; no tests ran in that invocation. Re-running the same files with `unittest discover -s tests -p ...` passed.

Historical recorded values before this live run: Python 192 total (191 passed, 1 skipped), Node 39/39, API 35/35, WSGI 11/11, frontend static 31/31. Current site evidence: Python 193 (192 passed, 1 skipped), Node 39/39, API 35/35, WSGI 11/11, frontend static 32/32. Earlier baseline values Python 179 (178 passed, 1 skipped) and Node 36/36 remain historical only.

The product gate remains PARTIAL. No real users, data, models, ECS, deployment, student code or external AI detection were involved. Remaining work includes long-title/reason wrapping at narrow widths, selected failure/retry combinations, and the wider breakpoint matrix; 320px support remains unspecified. No owner decision is needed for these bounded checks. Commit: `NONE`.

## Task R0-WORKSPACE-P3-LONG-COPY-CONSTRAINTS-021 — narrow task views and UTF-8 limits

Scope: verify maximum-length teacher task/review text at 360/390px, inspect actual synthetic writes against the active wire limits, and repair only the front-end validation/layout issues found. No feedback action was committed; no live/real data was used.

Specification and independent review:

- The active API contract states free text is limited by UTF-8 byte count (`specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`, section 5). The Schema caps task titles at 128 UTF-8 bytes (`workspace-api-v1.schema.json` assignment and Task DTOs) and review reasons at 1024 bytes. Teacher HTML separately allows 100 title characters and 400 reason characters.
- Two read-only agents audited the narrow layout and text limits. They found no owner-level responsive acceptance spec or fixed-copy requirement, and recommended using the existing field maxima as synthetic probes. No source conflict was found.

Evidence and implementation:

- Initial browser submission of a 100-CJK-character title was accepted by the HTML `maxlength=100` input but the real local API returned HTTP 413. The server-side validator and wire Schema both apply the existing 128-byte limit. A 400-CJK-character feedback reason similarly exceeds the existing 1024-byte Schema cap even though it fits the textarea character limit.
- `apps/teacher-web/app.js` now validates the trimmed title and reason with `TextEncoder` against their existing API byte ceilings and displays a native field validation error before any request. This keeps the interface aligned to the accepted wire contract without changing field character maxima or the API.
- `apps/teacher-web/styles.css` constrains the task list grid track to its container and gives review task rows a wrapping label with a non-shrinking action button. Real seeded task-center content previously expanded to 843px in a 300px content region on a 390px screen; the task-center and review-list page widths now match 360/390px viewports.
- Chrome 132 confirmed a 100-CJK title is marked invalid (300 UTF-8 bytes) and clicking publish emits no assignment POST. An existing API-valid 100-character ASCII synthetic title appears in the task list; the compact task-center card continues to show its existing ellipsis treatment. In the review overview the title is wrapped in the row label rather than expanding the page.
- Chrome confirmed a 400-CJK reason (1200 UTF-8 bytes) is invalid and clicking “请求说明” emits no review-action POST. A 400-character mixed Chinese/ASCII reason (800 bytes) remains valid. At 360/390px the reason box fits its card, action buttons are below and reachable, and the page has no horizontal overflow. The feedback was not submitted.
- Screenshots: `teacher-task-center-long-title-360px.png`, `teacher-task-center-long-title-390px.png`, `teacher-long-title-utf8-rejected-390px.png`, `teacher-long-reason-utf8-rejected-390px.png`, `teacher-long-reason-entry-360px.png`, `teacher-long-reason-entry-390px.png` under `browser-r0-p3-state-qa-2026-09-26/`.
- Added static assertions for title/reason byte validation and constrained task/review rows.

Files changed in this stage: `apps/teacher-web/app.js` adds early UTF-8 size validation; `apps/teacher-web/styles.css` constrains task-center grid rows and wraps review task labels; `tests/test_workspace_frontend_html.py` locks the byte guards and layout rules. This rolling report, `docs/CURRENT_STATE.md`, `README.md`, and `docs/README.md` record results and limits.

Verification:

- `python -m unittest discover -s tests` — **195 total, 194 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**; WSGI — **11/11 passed**; frontend static — **34/34 passed**.
- `node --check` for student/teacher/workspace client scripts; `python -m compileall -q apps tests`; harness `py_compile`; Workspace Schema JSON parse; and `git diff --check` — passed. Full Python exited 0 with transient AppContainer runner-path diagnostics. Its single skip is still Windows symlink creation permission unavailable, not security evidence.
- Browser: local test-only loopback harness `teacher-multi-queue`, Chrome 132 via Python Playwright. It returned actual synthetic API responses; all feedback write paths remained uncalled. The first 100-CJK-title POST reproduced the actual 413 before the guard was implemented.

The product gate remains PARTIAL. The compact teacher task-center card intentionally retains existing ellipsis styling; the complete title remains in the API DTO and review row. No student or teacher real data, model, ECS, deployment, or student-code execution was involved. Long title/reason states now have a bounded 360/390px sample, but full P4 breakpoint and failure-state matrix remains open. No owner decision was required. Commit: `NONE`.

## Task R0-WORKSPACE-P3-STUDENT-SWITCH-READ-FAILURE-022 — failed B selection remains explicit and retryable

Scope: reproduce the student flow A in progress → pause → select B → B workspace GET failure → retry → resume task-scoped drafts. Only fixed synthetic local API data and non-executable editor text were used.

Independent audit and implementation:

- A read-only student audit checked the active single-workspace contract and the student page selection/read flow. It confirmed failures hide workspace-specific content and that a retry reuses the selected assignment ID, but noted a browser test was still needed to prove the entire transition.
- Dynamic testing found that `loadStudentWorkspace(B)` rebuilt the task selector before reading B and left the native selector displaying the generic empty prompt after B's workspace request failed. The hidden workspace and unknown status were correct, but the student could not see which task the retry button would reread.
- `apps/student-web/app.js` now restores the explicit selected assignment ID in the rebuilt picker before attempting its detail reads. If the read fails, B remains visibly selected with its own retry button; no workspace content is rendered until reads succeed.
- Added `student-switch-workspace-fail` to the loopback-only harness. It seeds A as the one active task and B as assigned, then returns one actual HTTP 503 for B's exact Workspace GET; retry passes through to the real WSGI API.

Browser evidence:

- Chrome 132 at 390px: select A, enter a unique A-only unsaved editor draft, pause A, select B. B's exact Workspace GET returned 503. B remained selected; the page showed “任务读取失败，当前状态未知” and “读取失败 · 未知”; workspace, task rail, latest submission and remediation regions were hidden. No B start POST occurred before that read failure.
- Clicking B's retry caused a new catalog read, exact B assignment/Workspace reads returning 200, then the start write. B loaded with its own task title and without A's draft. After editing B, pausing it, and returning to A, A's unique draft was restored and B's text was absent. The request trace shows at most one in-progress task through pause/start ordering.
- At 360px the same A-pause/B-503 path kept B selected, kept all previous task details hidden, and retained page width 360/360. Retry returned B and the page remained 360/360.
- Screenshots: `student-switch-B-workspace-503-unknown-390px.png`, `student-switch-B-workspace-retry-390px.png`, `student-switch-A-draft-restored-390px.png`, `student-switch-B-workspace-503-unknown-360px.png`, `student-switch-B-workspace-retry-360px.png` under `browser-r0-p3-state-qa-2026-09-26/`.

Files changed in this stage: `apps/student-web/app.js` retains the selected task ID in the selector while its reads are pending/failing; `tests/test_workspace_frontend_html.py` asserts this behavior; `p3_teacher_generation_fault_server.py` adds a test-only two-task/one-shot workspace 503 mode. This report, `docs/CURRENT_STATE.md`, `README.md`, and `docs/README.md` record results.

Verification:

- `python -m unittest discover -s tests` — **195 total, 194 passed, 1 skipped**.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- API 35/35, WSGI 11/11, frontend static 34/34 via `python -m unittest discover -s tests -p ...`.
- JS syntax checks, `python -m compileall -q apps tests`, harness `py_compile`, Schema JSON parse, `git diff --check` — passed. Full Python exits 0 despite the existing temporary AppContainer runner path diagnostics; the one skip is Windows symlink creation permission, not security evidence.
- The harness bound only `127.0.0.1`; the server was stopped after the run. No student code was executed, no real model was called, and no feedback/submission write was made.

The P3 product gate remains PARTIAL; this closes one concrete selected-task failure/retry transition, not the entire P3 or P4 browser matrix. No owner decision was needed. Commit: `NONE`.

## Task R0-WORKSPACE-P4-RESPONSIVE-REGRESSION-SAMPLING-023 — desktop and breakpoint regression

Scope: regression-check the teacher task grid/review layouts at desktop and around existing CSS breakpoints after the narrow-width changes, and confirm the student B workspace remains usable on desktop. This does not define a new supported-minimum viewport.

Evidence:

- Chrome 132 checked the teacher task center and explicitly selected B review view at widths 360, 390, 759, 760, 761, 768, 1079, 1080, 1081 and 1280 CSS pixels. For every viewport, `documentElement.scrollWidth` equaled `innerWidth`. The task list and template card stayed inside their container. At 761px, the review uses its existing two-column rule; both columns stayed inside the review details area (submission column about 181px, side column 280px) without page overflow. This is geometry evidence, not a design sign-off for every intermediate width.
- At 1280px, the teacher task center rendered the template plus three synthetic published tasks; the selected B review showed B snapshots and events in the existing two-column layout. The student explicitly selected B and showed matching task and rail titles, workspace and sidebar visible, and document width 1280/1280.
- Full-page Chrome screenshots: `teacher-task-center-1280px.png`, `teacher-review-B-1280px.png`, `student-task-B-1280px.png` under `browser-r0-p3-state-qa-2026-09-26/`.
- No source code changed in this visual-only stage. Browser used `teacher-multi-queue` loopback test data and was stopped afterward.

Verification baseline from immediately before this visual-only sampling: Python 195 total (194 pass, 1 skip), Node 39/39, API 35/35, WSGI 11/11, frontend static 34/34; JS/Python compilation, Schema JSON parse and `git diff --check` passed. The only skipped case remains Windows symlink creation privilege unavailable and is not symlink-safety evidence.

P4 remains PARTIAL. The responsive sample now includes 360/390, several existing CSS breakpoints, and 1280px. It does not establish a 320px support requirement or production/browser matrix. No real users, data, models, deployment, ECS or student-code execution were involved. No owner decision was needed. Commit: `NONE`.

## Task R0-WORKSPACE-P3-START-LOST-RECEIPT-024 — committed start with lost response

Scope: verify the student-facing state when a start request changes server state but its success receipt is replaced by a local synthetic 503, followed by a user retry. This is test-only loopback fault injection; no product API behavior was changed.

Independent sub-agent audits:

- The write-path audit found create/publish, start/pause, submission, Agent/proposal and teacher review paths retain exact pending DTO/revision/idempotency identity for uncertain responses where required. Client tests cover malformed 2xx and transport failures in several write paths, but they are mock/client evidence, not browser evidence. Pending request identity is page-memory only and page reload loses it; the active contract already records this synthetic-stage limitation. No source conflict or owner decision was identified.
- The read-isolation audit found the teacher remediation area reports a failed read as unknown but has no dedicated remediation-only retry button; rereading the review flow is the current recovery path. Other audited areas have their own retry or explicit unknown state. This remains a usability follow-up, not a source-rule conflict.

Test harness:

- Added `student-start-lost` to `p3_teacher_generation_fault_server.py`. It seeds one assigned synthetic task. For the first exact student start POST it calls the real in-process WSGI API, discards its successful response, and returns a one-shot loopback HTTP 503. Later reads pass through to the same in-memory API.
- Command: `python artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py student-start-lost`.
- Browser: Playwright with installed Microsoft Edge 154.0.4258.37; this is local browser evidence and does not claim Chrome-specific or production behavior.

Observed result:

- At both 390px and 360px, selecting the task caused exactly one start POST, which returned 503 from the test harness after the API had committed the state transition. The page showed a task-read-unknown state and kept workspace details hidden.
- Clicking the visible “重新读取任务” control read the same assignment/workspace; the API returned `IN_PROGRESS`, so the UI displayed the workspace without sending a second start POST. The request trace remained exactly one start POST. At both widths, document width equaled viewport width.
- Screenshots: `student-start-commit-response-lost-390px.png`, `student-start-readback-recovered-390px.png`, `student-start-commit-response-lost-360px.png`, and `student-start-readback-recovered-360px.png` in `browser-r0-p3-state-qa-2026-09-26/`.
- Added a static test in `tests/test_workspace_frontend_html.py` that pins the retry-to-reread behavior and confirms an already `IN_PROGRESS` workspace takes the read branch rather than issuing another start request.
- The loopback server was stopped after each width. No submission, Agent call, real identity/data/model/ECS/deployment, or student code execution occurred.

Verification after this change:

- `python -m unittest discover -s tests` — **196 total, 195 passed, 1 skipped**; exit 0. The existing skip remains Windows symlink creation permission unavailable and is not symlink-safety evidence. Transient AppContainer copied-runner path messages appeared during the passing run.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- API — **35/35**; WSGI — **11/11**; frontend static — **35/35**.
- Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, Schema JSON parse and `git diff --check` passed.

P3/P4 remains PARTIAL. This closes one browser-tested write-unknown path but does not close all malformed-receipt combinations, refresh-durable idempotency, the complete responsive/browser matrix, or production integration. No owner decision was required. Commit: `NONE`.

## Task R0-WORKSPACE-P3-TEACHER-REMEDIATION-RETRY-025 — task-scoped retry preserves neighboring results

Scope: give an individual teacher remediation-read failure its own retry action so recovering one task does not reread/reset the review queue, review history, or remediation results from other tasks.

Change:

- apps/teacher-web/app.js now retains remediation read results by assignment ID. Each failed task row shows an explicit unknown state and the button 重试此任务补正状态. The retry reads only that assignment's remediation endpoint, uses a per-assignment generation plus current review-view generation guard, and rerenders the retained result map so other assignments stay visible. A review-page reload invalidates any late retry response.
- tests/test_workspace_frontend_html.py adds static assertions for assignment-scoped retry, response-generation guards, and no call back into the whole review loader.
- The local test harness's existing teacher-multi-queue mode seeds A/B/C; A's first remediation and queue reads fail once, while B/C reads succeed and C has an existing remediation record.

Browser evidence:

- Microsoft Edge 154.0.4258.37 at 390px opened the three-task review overview. A showed queue/remediation failure state; successful task entries, review history, and task C's remediation were present.
- Clicking A's remediation retry recovered only A's remediation read. The review-task overview and review-history text were byte-for-byte unchanged in the DOM comparison; C's remediation record remained visible and A's unknown error cleared. The page stayed 390/390px wide.
- Screenshots: teacher-remediation-one-task-failed-390px.png and teacher-remediation-one-task-retry-isolated-390px.png under browser-r0-p3-state-qa-2026-09-26/.
- This demonstrates local synthetic browser behavior only. No real user, production browser matrix, identity, data, model, ECS, deployment, or student-code execution was involved. The loopback service was stopped.

Verification after Task025:

- python -m unittest discover -s tests — 197 total, 196 passed, 1 skipped, exit 0. The one skip is Windows symlink creation permission unavailable and is not symlink-safety evidence. Temporary AppContainer copied-runner path diagnostics appeared despite exit 0.
- node --test tests/workspace-client.test.mjs — 39/39 passed.
- Workspace API — 35/35; WSGI — 11/11; frontend static — 36/36.
- Student/teacher/client JS checks, Python compileall, test harness py_compile, Workspace Schema JSON parse, and git diff --check passed.

P3/P4 remains PARTIAL. This adds an isolated recovery control, not production recovery durability, API contract acceptance, or full browser/P4 sign-off. No owner decision was needed. Commit: NONE.

## Task R0-WORKSPACE-P3-TEACHER-QUEUE-RETRY-026 — queue retry isolates one task and preserves explicit selection

Audit finding and change:

- The P3-B read-only audit found that a failed task-row retry previously re-entered the complete teacher review loader, refetching history, all remediations, all task queues and selected details. That could disturb independent successful regions.
- `apps/teacher-web/app.js` now keeps review-queue read results by assignment ID. Failed rows expose a queue-only retry control. Retry sends only `GET /assignments/{id}/review-queue`, uses an assignment-scoped retry generation and current review-view generation, updates only that map entry and rerenders the retained rows. A successful retry turns the row into an explicit View action; it does not enter task details automatically. If another task is already selected, its details remain visible.
- `tests/test_workspace_frontend_html.py` asserts the isolated endpoint, both generation guards, retry-handler priority over normal task selection, and that the helper cannot call the whole-page loader.
- Added the test-only `teacher-multi-queue-persistent` mode. Assignment A queue reads return 503; other seeded tasks succeed. The existing one-shot `teacher-multi-queue` mode covers recovery to 200.

Browser evidence:

- Microsoft Edge 154.0.4258.37 at 390px: with A's queue persistently failing, explicitly selected B and opened B's detail. Retrying A returned 503; the request delta was exactly one GET to A's review-queue endpoint. B detail, overview text, review-history text and remediation text were unchanged; page width was 390/390.
- In the one-shot mode, A initially returned 503. Retrying only A returned 200; A's row became an explicit View action. History, remediation and B/C overview rows stayed unchanged, and details remained hidden until a separate user selection. The request delta was exactly one GET to A's review-queue endpoint; page width was 390/390.
- Screenshots: `teacher-A-queue-retry-preserves-B-history-remediation-390px.png` and `teacher-A-queue-retry-recovers-explicit-choice-390px.png` under `browser-r0-p3-state-qa-2026-09-26/`.
- All data remained fixed synthetic in the loopback process. The service was stopped after each run. No real user/data/model/ECS/deployment or student code execution was involved.

Verification after Task026:

- `python -m unittest discover -s tests` — **198 total, 197 passed, 1 skipped**, exit 0. The one skip is Windows symlink creation permission unavailable; it is not symlink-safety evidence. Temporary AppContainer copied-runner path diagnostics appeared despite exit 0.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- Workspace API — **35/35**; WSGI — **11/11**; frontend static — **37/37**.
- Student/teacher/client JS checks, Python compileall, test harness `py_compile`, Workspace Schema JSON parse and `git diff --check` passed.

This closes the identified queue-retry isolation gap for the tested local synthetic path. P3/P4 still remains PARTIAL: other error interleavings, malformed browser write receipts, viewport support below 360px and production integration are not closed. No owner decision was required. Commit: NONE.

## Task R0-WORKSPACE-P3-ACTIVE-TASK-RELOAD-027 — refresh requires explicit reselect and recovers existing active task

The P3-A read-only audit found one remaining dynamic evidence gap: reload with a server-side IN_PROGRESS assignment had source-level no-auto-selection behavior, but no browser proof that reselecting the task reads it without issuing another start.

Browser check:

- Reused test-only `student-switch-workspace-fail`, which seeds A as IN_PROGRESS and B as ASSIGNED and fails B's first exact Workspace GET once. Microsoft Edge 154.0.4258.37 at 390px.
- On initial load, no task was selected and workspace details were hidden. After explicitly selecting A, its existing IN_PROGRESS workspace appeared without a start POST.
- Reload cleared the page selection and hid workspace details while preserving the backend task state. The page did not select A or B automatically. Explicitly selecting A again restored the existing IN_PROGRESS workspace and still sent no start POST.
- Trying to select B while A was active was rejected and the picker stayed on A; no B start was sent. After pausing A, selecting B left B explicitly selected and unknown on its first Workspace GET 503. Retrying the same selected B read succeeded and then sent exactly one B start POST. This does not infer an unconfirmed state from the failed read.
- Page width was 390/390 throughout. Screenshots: `student-active-task-reload-explicit-empty-390px.png`, `student-active-task-reload-explicit-A-restored-390px.png`, `student-B-workspace-failure-after-pausing-A-390px.png`, and `student-B-workspace-retry-after-A-reload-390px.png` in `browser-r0-p3-state-qa-2026-09-26/`.
- The fixed synthetic loopback service was stopped after the run. No real user/data/model/ECS/deployment or student code was involved.

No product source change was needed; the observed UI behavior matched the active contract. Existing post-Task026 test results remain the validation baseline: Python **198 total, 197 passed, 1 skipped**; Node **39/39**; Workspace API **35/35**; WSGI **11/11**; frontend static **37/37**. The single skip is still Windows symlink creation permission unavailable, not symlink-safety evidence. P3/P4 remain PARTIAL because broader malformed receipt/error interleavings and full browser matrix remain open. No owner decision was required. Commit: NONE.

## Task R0-WORKSPACE-P3-TEACHER-DETAIL-RETRY-029 — isolate selected Workspace detail retry

The read-only teacher multi-task audit found that the selected task's Workspace-detail GET could fail after its queue had succeeded. The page showed an unknown state, but the button retained the ordinary assignment-selection action; clicking it restarted the whole review loader and reread history, all remediations, every queue, Workspace details, and events.

Implementation:

- Added a per-assignment cached detail failure state and a dedicated `data-review-detail-retry` action. The retry uses the already explicit assignment and cached queue submission, then rereads only that submission's Workspace.
- Guards reject stale view generations, retry generations, changed assignment selection, or changed submission identity. A successful read restores the selected detail and leaves event retrieval on its existing independent guarded path. A failed retry keeps the explicit unknown state and offers the same scoped retry.
- Added static assertions for local retry scope and generation checks. No API, schema, or product behavior beyond failure recovery changed.
- During validation, one WSGI test assertion searched the entire error envelope for `999`, and the generated random `request_id` happened to contain that substring. Narrowed the assertion to the error message, which is the field relevant to whether the stale revision value is exposed.

Browser evidence:

- Edge 154, 390px, existing test-only `detail` loopback harness: selected submission queue succeeded, first Workspace GET returned HTTP 503, and the page exposed `重试详情读取` with details hidden and task still explicitly selected.
- Before retry, request counts were queue 2 (initial queue plus existing count refresh), history 2, remediation 2, Workspace detail 1. After retry: queue 2, history 2, remediation 2, Workspace detail 2. Thus the retry added only one Workspace GET. Detail recovered for `教师复核局部失败验证`; viewport/document width was 390/390 and no other detail retry remained.
- Screenshot: `browser-r0-p3-state-qa-2026-09-26/teacher-detail-retry-isolated-390px.png`. The loopback service was stopped after the run. No real user/data/model/ECS/deployment or student code was involved.

Verification after Task029:

- `python -m unittest discover -s tests` — **198 total, 197 passed, 1 skipped**, exit 0. AppContainer temporary copied-runner diagnostics appeared; the single skip remains Windows symlink creation permission unavailable and is not symlink-safety evidence.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- `python -m unittest discover -s tests -p 'test_workspace_api.py'` — **35/35 passed**; WSGI — **11/11 passed** after the assertion was narrowed to its intended message field; frontend static — **37/37 passed**.
- `node --check` for student app, teacher app, and workspace client; `python -m compileall -q apps tests`; harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` passed. `git diff --check` reports only the existing CRLF-to-LF notices for README and CURRENT_STATE.

Task029 closes the selected Workspace-detail retry isolation gap for this local synthetic path. Overall P3/P4 remains PARTIAL: additional request interleavings, remaining failure/retry combinations, viewport support below 360px, and production integration are not closed. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-TEACHER-QUEUE-COUNT-030 — use cached task queues for the review badge

A follow-on read-only audit found that, after details and events succeeded, the page made a second selected-task review-queue GET only to overwrite the navigation badge. A failure in that redundant GET was caught as a detail failure even though the detail had already rendered. The badge is the aggregate count for “提交复核”; the task rows separately show each task's count. A partial aggregate cannot be presented as a complete numeric total while a task queue is unknown.

Implementation:

- Removed the post-render queue GET. The badge now uses the queue results already gathered for the review view; selecting a detail no longer makes an extra read solely to update the count.
- The shared badge renderer shows `?` while any assignment queue is loading or failed, and sums all known task counts after reads are complete. A successful assignment-scoped queue retry recalculates the aggregate from the updated cache; detail and history/remediation regions are not reloaded.
- Added static coverage for partial/unknown badge behavior and the cached aggregate path. No API, schema, or product scope changed.

Browser evidence:

- Edge 154, 390px, `teacher-detail-delay` synthetic harness: the overview loaded three assignment queues (3 GETs). Explicitly opening task B caused the established review refresh of all three queues (total 6 GETs); after B's details and events rendered, there was no seventh selected-queue GET. Badge `2` matched the two pending submissions in A and B; C had none. B remained selected, document width 390/390. Screenshot: `browser-r0-p3-state-qa-2026-09-26/teacher-review-count-from-initial-queues-390px.png`.
- Edge 154, 390px, `teacher-multi-queue` synthetic harness: initial A queue 503 with B/C reads successful displayed badge `?`. Retrying A added exactly one queue GET (3→4), recovered aggregate badge `2`, and document width stayed 390/390. Screenshot: `browser-r0-p3-state-qa-2026-09-26/teacher-review-count-unknown-then-recovered-390px.png`.
- Both loopback services were stopped after their runs. No real user/data/model/ECS/deployment or student code was involved.

Verification after Task030:

- `python -m unittest discover -s tests` — **199 total, 198 passed, 1 skipped**, exit 0. The one skip is Windows symlink creation permission unavailable; it is not symlink-safety evidence. AppContainer temporary copied-runner diagnostics appeared despite exit 0.
- `node --test tests/workspace-client.test.mjs` — **39/39 passed**.
- Workspace API — **35/35**; WSGI — **11/11**; frontend static — **38/38**.
- Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. `git diff --check` only reported existing README/CURRENT_STATE CRLF-to-LF notices.

Task030 closes the redundant selected-queue count refresh and makes incomplete aggregate state explicit in the tested local synthetic path. Overall R0 P3/P4 remains PARTIAL: other request interleavings, full browser matrix, minimum supported viewport below 360px, and production integration remain open. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-START-UNKNOWN-SWITCH-036 — lock task switching until uncertain start readback

The P3-A audit found a fail-open path: when `POST /start` could have succeeded but its response was lost, the student page showed an unknown state and readback button, then re-enabled the task picker. A student could leave a task whose start outcome was not confirmed. A successful readback of `IN_PROGRESS` also needed to retire the old client idempotency key, or a later resume after pause could reuse a key whose original operation had already been confirmed.

Implementation:

- Track the pending start by assignment ID, workspace ID, and revision before dispatch. Network/5xx/malformed-receipt outcomes keep that attempt and disable switching; the change handler independently rejects a different assignment even if the disabled control is programmatically bypassed.
- The existing “重新读取任务” action stays bound to the same selected assignment. If readback confirms `IN_PROGRESS`, the page restores that workspace without another start POST and releases the picker lock. Definitive 4xx rejection clears the pending lock; it is not treated as an uncertain write.
- When `getWorkspace` authoritatively returns `IN_PROGRESS`, the client retires that exact workspace's pending start key. This prevents a later start after pause from replaying the old confirmed attempt. Added a Node regression test covering lost start response → IN_PROGRESS readback → pause → new start with a fresh key.
- Extended the test-only harness with `student-start-lost-multi`: A/B synthetic tasks, with A's first start applied and the HTTP response replaced by 503. No API/schema/product scope changes.

Browser evidence:

- Edge 154 at 390px: selecting A caused exactly one start POST; the harness applied it and returned HTTP 503. The picker remained locked to A and the UI showed unknown/read-failure with a same-task readback action. Forcing a B change event through the DOM was rejected, the selected task returned to A, and no B Workspace read/start was sent.
- Retrying A read its Workspace as `IN_PROGRESS`; the view restored A and total A start POST count remained 1. After explicitly pausing A, B could be selected and exactly one B start POST succeeded. Page width was 390/390. Screenshots: `student-start-unknown-locks-switch-390px.png` and `student-start-unknown-readback-recovers-A-390px.png` in `browser-r0-p3-state-qa-2026-09-26/`.
- Harness bound only to loopback and was stopped after the run. No real account/data/model/ECS/deployment or student code was involved.

Verification after Task036:

- `python -m unittest discover -s tests` — **199 total, 198 passed, 1 skipped**, exit 0 (the one skip is Windows symlink creation permission unavailable; not symlink-safety evidence). AppContainer temporary copied-runner path diagnostics appeared during execution; final summary passed.
- `node --test tests/workspace-client.test.mjs` — **40/40 passed**.
- Workspace API — **35/35**; WSGI — **11/11**; frontend static — **38/38**.
- Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. `git diff --check` reported only existing README/CURRENT_STATE CRLF-to-LF notices.

Task036 closes the unknown-start switching path for the tested local synthetic scenario. Overall R0 P3/P4 remains PARTIAL: broader state-transition interleavings, remaining error/retry combinations, full browser matrix, minimum supported viewport below 360px, and production integration are not closed. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STALE-QUEUE-RETRY-037 — discard a delayed retry after task switch

The teacher task-switch audit found no source-proven stale-write bug, but identified a missing dynamic race check for switching assignments while an assignment-scoped queue retry was pending.

Test harness/evidence:

- Added test-only `teacher-queue-retry-delay`: three synthetic assignments; A's first queue read returns 503, A's manual retry delays five seconds then returns 503, while a new selected-task view can independently reread A successfully.
- Edge 154, 390px: after retry A entered pending state, the teacher selected B. The new view loaded B's details/events and reloaded A successfully. When A's older delayed retry later returned 503, generation guards discarded it; B remained selected, A remained a successful “查看此任务” row with one pending item, and the aggregate badge stayed `2`.
- Captured requests: A queue GET 3 times (initial failure, delayed stale retry failure, new-view success); B and C 2 times each (overview plus selected-view refresh). After the delayed failure, A had no retry button, B's title/snapshot/events remained displayed, and document width was 390/390.
- Screenshots: `teacher-stale-queue-retry-pending-B-selected-390px.png` and `teacher-stale-queue-retry-discarded-after-B-selection-390px.png` in `browser-r0-p3-state-qa-2026-09-26/`.
- The loopback harness was stopped after the run. No product source, real user/data/model/ECS/deployment, or student code execution was involved.

Verification after Task037:

- `python -m unittest discover -s tests` — **199 total, 198 passed, 1 skipped**, exit 0. AppContainer temporary copied-runner path diagnostics appeared; the single skip remains Windows symlink creation permission unavailable and is not symlink-safety evidence.
- `node --test tests/workspace-client.test.mjs` — **40/40 passed**; Workspace API — **35/35**; WSGI — **11/11**; frontend static — **38/38**.
- Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. Only CRLF-to-LF notices appeared for README and CURRENT_STATE.

Task037 adds dynamic evidence for a stale task-scoped retry response being discarded after selection changes. Overall P3/P4 remains PARTIAL; remaining interleavings and the full browser matrix are not closed. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STALE-REMEDIATION-RETRY-038 — discard a delayed remediation retry after task switch

The teacher switching audit separately identified a dynamic-evidence gap for assignment-scoped remediation retries. This stage exercises the existing view and assignment retry generations; no product-source change was needed.

Browser evidence:

- Added test-only `teacher-remediation-retry-delay`: A's first remediation GET returns 503, its manual retry delays five seconds then returns 503, and the next view's A remediation read succeeds independently.
- Edge 154 at 390px: while A's retry was pending, the teacher selected B. The refreshed view loaded B's detail/events, reread A successfully, and retained C's remediation record. When the delayed old A retry 503 arrived, its stale generation was discarded; B remained selected, no A remediation retry error was shown, and C's record remained visible.
- Captured remediation reads: A 3 (initial failure, delayed retry failure, new-view success), B 2, C 2. Document width was 390/390. Screenshot: `teacher-stale-remediation-retry-discarded-after-B-selection-390px.png` in `browser-r0-p3-state-qa-2026-09-26/`.
- Loopback harness stopped after the run. No product source, real identities/data/models/ECS/deployment, or student code execution was involved.

Verification after Task038:

- Final regression: `python -m unittest discover -s tests` — 199 tests, 198 passed, 1 skipped, exit 0; the only skip is Windows symlink creation permission and is not symlink-safety evidence. `node --test tests/workspace-client.test.mjs` — 40/40; Workspace API — 35/35; WSGI — 11/11; frontend static — 38/38.
- Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. Full-test output included temporary AppContainer runner-path diagnostics without affecting exit 0; diff check emitted only CRLF-to-LF notices for README and CURRENT_STATE.

Task038 adds dynamic evidence for stale remediation retry isolation after task selection changes. Overall P3/P4 remains PARTIAL; other interleavings and the full browser matrix remain open. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STALE-HISTORY-RETRY-039 — discard a delayed history retry after task switch

The teacher history retry has its own generation guard; this stage checks a delayed failure arriving after a new selected-task view has loaded. No product source change was needed.

Browser evidence:

- Added test-only `teacher-history-retry-delay`: A's initial history read returns 503; the manual history retry delays five seconds then returns 503; the newly selected view can reread all histories successfully.
- Edge 154 at 390px: while history retry was pending, the teacher selected B. B's details/events loaded, A/B/C histories were reread successfully, and C's existing history action remained visible. When old A retry 503 arrived, the stale generation was discarded: B remained selected, history showed no stale read error, and C's record remained visible.
- Captured A/B/C history GET counts were 3/3/3 (initial read, retry, new view); document width was 390/390. Screenshot: `teacher-stale-history-retry-discarded-after-B-selection-390px.png` in `browser-r0-p3-state-qa-2026-09-26/`.
- Loopback harness stopped after the run. No product source, real identity/data/model/ECS/deployment, or student code execution was involved.

Verification after Tasks038–039:

- Final regression: `python -m unittest discover -s tests` — 199 tests, 198 passed, 1 skipped, exit 0; the only skip is Windows symlink creation permission and is not symlink-safety evidence. `node --test tests/workspace-client.test.mjs` — 40/40; Workspace API — 35/35; WSGI — 11/11; frontend static — 38/38.
- Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. Full-test output included temporary AppContainer runner-path diagnostics without affecting exit 0; diff check emitted only CRLF-to-LF notices for README and CURRENT_STATE.

Tasks037–039 dynamically cover stale queue, remediation, and history retries after teacher task selection changes. Overall R0 P3/P4 remains PARTIAL: other state/error interleavings, full browser matrix, minimum supported viewport, and production integration remain open. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-SUBMISSION-DEFINITIVE-REJECTION-040 — keep a definitive submit rejection distinct from an unknown receipt

The student submission catch path re-read Workspace after a failed POST and changed any `REVIEW_REQUIRED` or `RESUBMITTED` readback into `unknown`, even for an explicit non-retryable 4xx. Since the client clears a mutation idempotency key on 4xx, this could leave the page offering “retry same submission” after an authoritative rejection. The UI now applies this pending-state inference only when the failure was not a definitive rejection. A 4xx retains its conflict/validation status, refreshes the visible Workspace state, clears the pending attempt and does not trigger a latest-submission read as if the result remained unknown.

Evidence:

- Added a Node client regression: a 409 `stale_submission` is marked as definitive, maps to conflict, clears the rejected request key, and a later explicit new attempt gets a new key. Client suite is 41/41.
- Added a frontend static assertion that a `REVIEW_REQUIRED`/`RESUBMITTED` readback cannot override `definitiveRejection` and that latest-submission recovery is gated on unknown state. Frontend static suite is 39/39.
- Loopback browser fault mode `student-submit-rejected-retry` applied the first submission in the in-memory API and returned 503, then rejected the same UI retry with a synthetic 409. The page initially exposed “重试同一提交” while unknown; after the explicit 409, it showed “提交成果遇到版本冲突，请刷新后核对当前状态；没有覆盖已有内容。” Workspace state readback was `REVIEW_REQUIRED`; the submit button returned to its ordinary text, the explanation became editable, and no stale retry lock remained. Server log evidence: exactly two submission POSTs (503 then 409), two Workspace reads and one latest-submission read after the first unknown response; the definitive rejection did not cause another latest-submission read. All data was fixed and synthetic, held only in the local process.
- Browser observation used the Codex in-app browser at its default viewport; no Edge/Chrome version or narrow-screen claim is made. Browser page width and a saved screenshot are not part of this run's evidence.
- Changed product code: `apps/student-web/app.js`. Regression coverage: `tests/test_workspace_frontend_html.py`, `tests/workspace-client.test.mjs`. Fault injection only: `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/p3_teacher_generation_fault_server.py`.

Verification: `python -m unittest discover -s tests` — 200 tests, 199 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 41/41; Workspace API — 35/35; WSGI — 11/11; frontend static — 39/39. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. AppContainer temporary runner-path diagnostics appeared during full Python tests but did not affect exit 0. The sole skip is Windows symlink creation permission; it is not symlink safety evidence. Diff check emitted only the existing README/CURRENT_STATE CRLF-to-LF notices. This stage remains synthetic and PARTIAL; it does not establish browser support across viewports or production integration. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STALE-EVENT-RETRY-041 — discard a delayed event retry after task switch

The event timeline audit found that source generation guards and event-local retry behavior were already present, while one interleaving lacked dynamic evidence. Added test-only `teacher-event-retry-delay`; no product source change was made.

Browser evidence:

- A's first events GET returned 503. The teacher manually retried A's event region; that request was delayed five seconds and then returned 503. During the delay, the teacher explicitly selected B.
- B's workspace detail and events loaded successfully. After the delayed A 503 arrived, B remained selected, B's event status stayed `事件读取成功。`, and B's three own timeline entries remained visible. The old request did not replace the new task's event region.
- Server logs confirmed A events requests in order: initial 503, delayed retry 503. During the delay, B Workspace and events both returned 200. Browser observation used the Codex in-app browser at the default viewport (1281px); no Edge/Chrome version or narrow-screen claim is made. No screenshot was saved for this scenario.
- Loopback harness was stopped; all assignments, submissions and events were synthetic in-memory values. No real identities/data/models/ECS/deployment or student code execution.
- Changed file: this Artifact Harness `p3_teacher_generation_fault_server.py`; no product files changed. The test suites remain unchanged from Task040.

Final regression after Task041: `python -m unittest discover -s tests` — 200 tests, 199 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 41/41; Workspace API — 35/35; WSGI — 11/11; frontend static — 39/39. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. Temporary AppContainer runner-path diagnostics did not affect the successful full-suite exit. The sole skip remains Windows symlink creation permission, not symlink safety evidence. The available event retry/switch evidence is stronger, but P3/P4 remains PARTIAL: other delayed-write interleavings, full viewport matrix, and production integration are not closed. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-REVIEW-WRITE-UNKNOWN-SWITCH-042 — keep an uncertain teacher review bound to its selected submission

The read-only review-write audit found no product-source defect but identified a missing browser interleaving. Added test-only `teacher-review-write-lost`, which applies A's ACK in the in-memory API and returns a synthetic 503 for the first response; the same idempotent retry then returns the original API result.

Browser evidence:

- After the first 503, the page said the receipt was unconfirmed, identified A/version 1/ACK and fixed reason, and allowed only the same action. While this write remained unknown, explicitly attempting to select B left A's detail/reason bound to the pending attempt; reason editing and other review actions stayed disabled.
- Retrying the same ACK received the cached 201 result. Server logs showed one POST response 503 followed by one POST response 201 for `submission-1/review-actions`; the API history contained one A ACK. Afterward, the previously selected B detail loaded, A's queue was 0 and B's queue remained 1.
- Browser observation used the Codex in-app browser at its default viewport (1281px); no browser-version/narrow-screen claim and no screenshot saved. Loopback service was stopped. Data was synthetic/in-memory only; no real identities/data/models/ECS/deployment or student code execution.
- Changed file: only the test-only Artifact Harness `p3_teacher_generation_fault_server.py`; no product code change. Existing Node retry tests check exact DTO/revision/idempotency-key replay.

Verification after Task042: `python -m unittest discover -s tests` — 200 tests, 199 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 41/41; Workspace API — 35/35; WSGI — 11/11; frontend static — 39/39. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. Temporary AppContainer runner-path diagnostics did not affect the successful full-suite exit. The sole skip remains Windows symlink creation permission and is not symlink-safety evidence. Overall P3/P4 remains PARTIAL; fixed demo identity, full browser matrix and production integration remain outside the evidence. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-PROPOSAL-ACCEPT-UNKNOWN-043 — prevent a competing decision while accept is unconfirmed

Read-only audit found that the ACCEPTED catch path retained `proposalAcceptAttempt` for `error`/`unknown`, but reset the action controls with `retryAction=null` unless kind was `unavailable`. It could therefore re-enable REJECT/TAKEOVER while ACCEPTED remained unresolved. The matching REJECT/TAKEOVER handler also lacked an independent guard against a pending accept.

The UI now keeps only the same ACCEPT action enabled whenever `proposalAcceptAttempt` remains non-null, regardless of error kind. `decideProposal()` also rejects any competing decision in that state, including programmatic handler dispatch. Existing exact attempt context, Workspace, proposal, decision, revision and client idempotency replay remain unchanged. Added frontend static regression assertions for the control state and handler guard. The pre-existing assertion expecting only `unavailable` was updated to the accepted broader pending-attempt invariant.

Evidence scope: direct source/static assertions only. The generic unexpected-error branch cannot be produced by the current HTTP client path without injecting a non-client exception; the code adds a defensive guard and does not claim browser runtime verification for this branch. No synthetic harness mode or product spec change was necessary. Files changed: `apps/student-web/app.js`, `tests/test_workspace_frontend_html.py`. The Task039 historical status wording in CURRENT_STATE was clarified to note its test-pending text was a point-in-time snapshot subsequently closed by Task040/042.

Verification after Task043: `python -m unittest discover -s tests` — 201 tests, 200 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 41/41; Workspace API — 35/35; WSGI — 11/11; frontend static — 40/40. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, API Schema JSON parse and `git diff --check` passed. AppContainer temporary runner-path diagnostics did not affect exit 0. The sole skip is Windows symlink creation permission and is not symlink-safety evidence. Overall P3/P4 remains PARTIAL; no owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STUDENT-LATEST-RETRY-SWITCH-044 — discard delayed latest-submission failure after task switch

The student submission-scope audit found no cross-task source defect, but dynamic evidence did not cover an old latest-submission retry failing after switching. Added test-only `student-latest-retry-delay`; no product source change.

Browser evidence:

- A (`教师复核局部失败验证`) was explicitly selected. Its first latest-submission GET returned 503 and exposed the local “重新读取提交记录” retry. The manual retry delayed five seconds and then returned 503.
- During that delay, the student explicitly selected B. B loaded and entered `IN_PROGRESS`; its latest-submission read returned 200 with no submission. When the delayed A 503 arrived, B remained selected, the page still showed B's `IN_PROGRESS` state and B's confirmed empty latest-submission result, with no stale A error.
- Server logs show A latest reads 503/503, while B Workspace/start/remediation/latest calls succeeded (200). Browser observation used Codex in-app browser at default 1281px; no version-specific or narrow viewport claim and no screenshot saved. Synthetic in-memory data only; no real student data, model, ECS, deployment or student code.
- Changed file: test-only Artifact Harness `p3_teacher_generation_fault_server.py`; no product code change.

Verification after Task044: `python -m unittest discover -s tests` — 201 tests, 200 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 41/41; Workspace API — 35/35; WSGI — 11/11; frontend static — 40/40. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. AppContainer temporary runner-path diagnostics did not affect exit 0; the sole skip is Windows symlink creation permission, not symlink safety evidence. Overall P3/P4 remains PARTIAL. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STUDENT-REMEDIATION-RETRY-SWITCH-045 — discard delayed remediation failure after task switch

The student submission-scope audit found no cross-task source defect; the remaining evidence gap was a delayed remediation read failure returning after a task switch. Added test-only `student-remediation-retry-delay` to the local Harness. No product-source change was made.

Browser evidence:

- Explicitly selected A (`教师复核局部失败验证`). Its Workspace state was `FEEDBACK_REQUIRED`; first remediation GET returned 503 and the page exposed its remediation retry. The retry delayed five seconds, then returned 503.
- While that retry was pending, explicitly selected B (`学生延迟读取隔离验证 B`). B loaded and entered `IN_PROGRESS`; its remediation GET returned 200 with no pending remediation and its latest-submission GET returned 200 with no submission.
- After the delayed A 503 arrived, the visible page still showed B selected and `IN_PROGRESS`, with B's confirmed no-remediation and no-submission messages. The old A failure did not replace B's state. Server log order confirms A remediation 503, delayed A remediation 503, then B Workspace/start/remediation/latest 200. The default Codex in-app browser viewport was used; no browser-version, narrow-viewport or screenshot claim is made.
- Loopback Harness was stopped after the run. Synthetic in-memory values only; no real identities, student/teacher data, model, ECS, deployment, or student code execution. Changed file: test-only Artifact Harness `p3_teacher_generation_fault_server.py`.

Verification after Task045: `python -m unittest discover -s tests` — 201 tests, 200 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 41/41; Workspace API — 35/35; WSGI — 11/11; frontend static — 40/40. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. AppContainer temporary runner-path diagnostics appeared during the full Python suite but did not affect exit 0. The only skip is Windows symlink creation permission and is not symlink-safety evidence. `git diff --check` emitted only the existing README/CURRENT_STATE CRLF-to-LF notices.

Task045 adds dynamic evidence that a late student remediation failure is isolated after switching tasks; it does not establish broader browser support or production integration. Overall R0 P3/P4 remains PARTIAL. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-ACTIVE-LOADER-GUARD-048 — make the student loader's active-task defense reachable

A read-only transition-matrix audit found that `loadStudentWorkspace()` cleared `workspaceState`, `workspaceId`, and `currentAssignmentId` before checking whether a different assignment was being loaded while the previous task remained `IN_PROGRESS`. The picker handler already blocks ordinary user switches and the API independently rejects starting a second active task, so this was a dead defense rather than an observed normal-UI bypass.

The loader now checks the selected assignment against the still-preserved active assignment and state before incrementing the load generation or clearing the current context. If called to load another task while the current task is `IN_PROGRESS`, it restores the picker to the active task, explains that the student must pause first, and returns without hiding or clearing the current workspace. Removed the unreachable later check. Added a source-structure regression requiring this guard to precede context clearing and forbidding the dead guard form.

Files changed for Task048: `apps/student-web/app.js`, `tests/test_workspace_frontend_html.py`. The earlier rolling README/CURRENT_STATE and Task045 report context remains intact. This is a defensive loader-level guard; no browser claim is made for direct invocation of the private loader path. Existing dynamic evidence still covers the normal picker path and API mutual-exclusion behavior.

Verification after Task048: `python -m unittest discover -s tests` — 202 tests, 201 passed, 1 skipped, exit 0; frontend static — 41/41; Workspace API — 35/35; WSGI — 11/11; `node --test tests/workspace-client.test.mjs` — 41/41. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. AppContainer temporary runner-path diagnostics appeared during the full Python suite but did not affect exit 0. The only skip is Windows symlink creation permission; it is not symlink-safety evidence. Diff check emitted only the existing README/CURRENT_STATE CRLF-to-LF notices.

The transition matrix remains **PARTIAL**: the dead loader guard is now effective and statically protected, but this defensive direct-call branch was not separately exercised in a browser. No real identity/data/model/ECS/deployment or student code execution. No owner decision required. Commit: NONE.

## Task R0-WORKSPACE-P3-STALE-HISTORY-PAGINATION-052 — discard a stale page before mutating current history

The remaining-history audit found two related hazards: each new full history view reused the previous page's mutable `actions` array, and `loadMoreReviewHistory()` appended a page response before checking whether its history generation was stale. A late pagination result could therefore mutate data shared with a newer page even though the old callback later skipped rendering.

The new view now copies retained actions into its own array. A pagination callback checks its captured generation immediately after the API response and before changing actions, cursor, `hasMore`, or error state. The existing post-batch guard still prevents an old callback from re-enabling the current button or rendering the old page. The prior static test failed before the fix because arrays were shared; its regression now requires detached arrays and a generation check before the append.

Dynamic synthetic browser evidence:

- Test-only Harness mode `teacher-history-pagination-race` seeded two synthetic tasks and 51 review actions on A. Initial A history showed 50 entries and a load-more control.
- Started A's `after_sequence=102` page request with a five-second delay. While it was pending, explicitly selected B, starting a newer history view. The new A first-page GET returned 503; B history read returned 200. The view retained A's 50 previously read actions and showed a separate A history-unknown row.
- The old A pagination request then returned 200. After it completed, the new view remained at 50 A actions plus its error row (51 list rows total); it had not acquired the stale 51st action. Retrying the history read once more under a synthetic 503 retained the same 50 actions. A subsequent successful retry loaded A's first 50; explicit load-more then returned the 51st action and removed the error. This confirms the current view discards the stale generation while preserving independent retry and pagination recovery.
- Browser: Codex in-app browser default viewport; no narrow-screen or browser-version claim, no screenshot saved. Loopback service stopped. All records remained fixed in-memory synthetic data; no real identities/data/models/ECS/deployment or student code execution.
- Changed files: `apps/teacher-web/app.js`, `tests/test_workspace_frontend_html.py`, and test-only Harness `p3_teacher_generation_fault_server.py`.
- A preliminary timing run was excluded because the delayed page completed before task reselection; the accepted run's request order is confirmed by server logs.

Verification after Task052: `python -m unittest discover -s tests` — 202 tests, 201 passed, 1 skipped, exit 0; frontend static — 41/41; Workspace API — 35/35; WSGI — 11/11; `node --test tests/workspace-client.test.mjs` — 41/41. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. AppContainer temporary runner-path diagnostics appeared during the full Python suite but did not affect exit 0. The only skip is Windows symlink creation permission; it is not symlink-safety evidence. Diff check emitted only the existing README/CURRENT_STATE CRLF-to-LF notices.

This closes the identified stale history-pagination mutation path for the tested generation interleaving. Overall R0 P3/P4 remains **PARTIAL**; the full browser matrix and production integration remain outside this evidence. No owner decision required. Commit: NONE.

## Task R0-P4-TEACHER-HISTORY-360PX-057 — correct narrow viewport overflow and verify history failure recovery

A bounded P4 recheck used the test-only `teacher-history-pagination` mode in the local loopback Harness. Two independent read-only agents audited the prior evidence and docs: Task052 covered the pagination race only at the default in-app viewport with no saved screenshot; earlier 360/390px checks did not capture root `clientWidth` separately from viewport width. The Harness seeded one synthetic assignment and 51 synthetic review actions.

### Evidence and change

- Before the fix at 360px: `innerWidth=360`, `documentElement.clientWidth=345`, `documentElement.scrollWidth=360`; the screenshot showed a horizontal scrollbar. `apps/teacher-web/styles.css` forced `body` to `min-width:360px`, exceeding the available root content width by 15px when the vertical scrollbar occupied 15px.
- At 390px before the fix, root client and scroll widths both measured 375px; no horizontal overflow was observed.
- The student empty state also reproduced the root-width problem before its fix at 360px: `innerWidth=360`, root `clientWidth=345`, `scrollWidth=360`; the screenshot showed a horizontal scrollbar. The student CSS had the same forced body minimum.
- Removed the forced 360px body minimum from both teacher and student demo pages. No product decision about support below 360px was made. Added one static regression per page in `tests/test_workspace_frontend_html.py` to prevent reintroducing those body minimums.
- After the fix at 360px: root `clientWidth=345`, `scrollWidth=345`; no horizontal scrollbar was visible in the page screenshot. Initial history showed 50 actions. A synthetic page-read 503 retained all 50 actions, showed the history-local unknown/failure state and “重试读取”, and hid “加载更多”. Retrying the history area restored the first page; only an explicit “加载更多” action then added action 51. Root width remained 345/345 throughout.
- After the fix at 390px: root client and scroll widths both measured 375px. The earlier 390px failure/retry path also preserved 50 actions plus its separate error row (51 DOM rows total), hid “加载更多”, then recovered to 51 actions after explicit retry and pagination.
- Student empty catalog after the fix: at 360px root client/scroll widths were 345/345 and at 390px they were 375/375. No task was selected or started; no student project code was run.
- Browser: Codex in-app browser, temporary viewport override at 360x800 and 390x844, loopback only at `127.0.0.1:8767`. Screenshots were captured and visually inspected during this run, but no image file was saved into the Artifact. The viewport override was reset and the service stopped.

Changed files: `apps/teacher-web/styles.css` and `apps/student-web/styles.css` (remove forced body min-width causing overflow at 360px); `tests/test_workspace_frontend_html.py` (guard both pages against reintroducing the width constraint). No Harness change.

Verification after Task057: `python -m unittest discover -s tests` — 204 tests, 203 passed, 1 skipped, exit 0; frontend static — 43/43; Workspace API — 35/35; WSGI — 11/11; Node client — 41/41. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, Workspace API Schema JSON parse, and `git diff --check` passed. AppContainer temporary runner-path diagnostics appeared during Python execution but did not affect exit 0. The only skip remains Windows symlink creation permission; it is not symlink-safety evidence. `git diff --check` emitted only the existing README/CURRENT_STATE CRLF-to-LF notices. An initial targeted unittest module invocation used a package path unsupported by this repository, and an initial schema path was incorrect; both were corrected and the intended checks then passed.

This is a bounded teacher-history visual check at two widths, not a complete P4 matrix or a support decision below 360px. It does not establish production browser integration, accessibility, real identity/data, persistence, model use, deployment, safe code execution, or Foundation Spike completion. Overall R0 remains **PARTIAL**. No owner decision required. Commit: NONE.

## Task R0-P4-STUDENT-CATALOG-FAILURE-360PX-060 — inspect student catalog unknown and retry states

Using the existing test-only `student-catalog-fail` mode on the local loopback Harness, the Codex in-app browser opened `/demo/student/` at 360x800. The first assignment-catalog read returned synthetic HTTP 503; the page showed “任务读取失败，当前状态未知” and “重新读取任务”. Root `clientWidth=345`, `scrollWidth=345`; no horizontal scrollbar was visible. Clicking the local retry produced a 200 catalog response, restored the available synthetic assignment, kept the picker value empty, and displayed the explicit-choice explanation; root widths stayed 345/345. Browser screenshots were captured and visually inspected during the run, but no image file was saved into the Artifact.

No task was selected or started, no student code was run, and no Harness/source/test files were changed for Task060. The temporary viewport override was reset and the local service stopped. This only covers the empty/unknown/retry catalog state at one in-app viewport; it does not test task switching, an active workspace, 320px behavior, other browsers, accessibility, or production integration. The overall project remains **PARTIAL**; no owner decision required. Commit: NONE.

## Task R0-P3-ACTIVE-TASK-CONFLICT-AND-API-CONCURRENCY-066

### API concurrency boundary

The shared in-memory `WorkspaceApi` can receive overlapping calls from the threaded WSGI adapter. `WorkspaceApi.handle()` now serializes dispatch through a per-instance `RLock`, keeping active-task checks/transitions, revision checks, and idempotency lookup/mutation/replay atomic within that one shared process-memory instance. This is a local adapter guarantee only; it does not establish cross-process locking, durable transactions, or production concurrency safety.

Three API regressions cover simultaneous starts on two published synthetic assignments (one 200 and one `active_task_exists` 409, exactly one active workspace/start event), simultaneous identical create requests (same 201 receipt and one stored assignment), and overlapping dispatch serialization. Targeted Workspace API tests pass 38/38.

### Student active-task conflict state

The student UI previously routed a definitive `active_task_exists` 409 through the generic task-read failure renderer, labeling a known rejection “读取失败 · 未知” and retrying the same selected assignment. The UI now renders a separate “所选任务没有开始：另一个任务正在进行” state, with an explicit “重新读取任务目录” action. That action reads the catalog with no selected assignment, leaving the selector empty and requiring a fresh explicit student choice. A static regression protects the branch and prevents conflating it with unknown read failures.

Bounded Edge browser run against local loopback `student-start-lost-multi` at 390x844 reproduced the path: A start applied but returned synthetic 503; explicit reread recovered A; pause A; explicitly start B; reload and explicitly select paused A; API returned 409; page displayed the definite conflict; directory retry left the picker empty. Captured start responses were 503 for A, 200 for B, then 409 for A. At final state, viewport, root client width and scroll width were all 390px. No task was silently selected, and no student project code was run. The loopback service was stopped after the run.

### Verification

- `python -m unittest discover -s tests` — 208 total, 207 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 41/41.
- `python -m unittest discover -s tests -p test_workspace_api.py` — 38/38.
- `python -m unittest discover -s tests -p test_workspace_wsgi.py` — 11/11.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py` — 44/44.
- `node --check` for student app, teacher app and workspace client; `python -m compileall -q apps tests`; Harness `py_compile`; API Schema JSON parse; and `git diff --check` passed.
- The only skip remains the Windows symlink-creation permission limitation; it is not symlink-safety evidence. Python full-suite output included temporary AppContainer runner-path diagnostics, but completed with exit 0. `git diff --check` emitted only the existing README/CURRENT_STATE CRLF-to-LF notices.

The current test evidence supersedes the prior validated 204/203+1, Node41, API35, WSGI11, frontend43 snapshot; those earlier values remain historical in preceding entries. Overall R0 P3/P4 remains **PARTIAL**. Remaining boundaries include broader failure interleavings, full P4 browser/viewport matrix (including the undefined 320px support range), multiple processes, persistence, production HTTP/authentication, real identities/data/models/ECS/deployment, and safe student code execution. No owner decision required. Commit: NONE.

## Task R0-P3-TEACHER-CATALOG-STALE-READ-069

### Finding and change

A read-only P3-C audit found that overlapping teacher assignment-catalog requests had no generation guard. A slow startup request could replace a newer post-publish list or overwrite its success state with an old failure; the startup error path also had no catalog-local retry.

`refreshAssignments()` now assigns each request a monotonically increasing generation, renders only the current response, and ignores stale failures before touching UI state. Startup success status and post-write success status are also guarded against an intervening newer read. A current catalog failure is shown in a new task-list-local `#assignment-list-state` region as an unknown catalog state with a “重试读取任务目录” button; this does not replace the global API status used by other teacher areas. If a task create/publish receipt was already confirmed, the failure message preserves that fact and retrying does not repeat the write.

Files changed: `apps/teacher-web/app.js`, `apps/teacher-web/index.html`, `tests/test_workspace_frontend_html.py`; this rolling Artifact, `README.md`, `docs/README.md`, and `docs/CURRENT_STATE.md` record the evidence and current status.

### Dynamic synthetic browser evidence

Using the existing `empty` loopback Harness and Edge at 1280x900, the first teacher catalog GET was captured as an empty 200 response and held. A synthetic task was then created and published; a second GET returned the new task and rendered the confirmed publish state. The delayed first response was then released. The published task card remained visible exactly once and the success status was unchanged. A second run replaced the delayed startup response with 503 after the newer successful publish; the stale failure was discarded and did not replace the card or success status. A final run at 390x844 first repeated the stale 503 case, then returned 503 for the current catalog read; the page showed the task-list-local unknown state, and an explicit retry made one additional GET, restored the synthetic task card and displayed recovery in that same region. In the success-after-delay run and the final combined run, no stale response replaced the current task card or global success status. All data was synthetic and process-local; the loopback service was stopped after each run. No student code was run.

### Verification

- `python -m unittest discover -s tests` — 209 total, 208 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 41/41.
- `python -m unittest discover -s tests -p test_workspace_api.py` — 38/38; `test_workspace_wsgi.py` — 11/11; `test_workspace_frontend_html.py` — 45/45.
- `node --check` for student app, teacher app and workspace client; `python -m compileall -q apps tests`; Harness `py_compile`; API Schema JSON parse; and `git diff --check` passed.
- The sole skip remains Windows symlink creation permission and is not symlink-safety evidence. Temporary AppContainer runner-path diagnostics appeared during the full Python suite but did not affect its exit 0.

This closes the identified teacher overview stale-read path for the tested response order and provides a retry for a current catalog failure. It does not cover every possible teacher read interleaving or complete P4/production behavior. Overall R0 P3/P4 remains **PARTIAL**; no owner decision required. Commit: NONE.


## Task R0-P3-STALE-TEACHER-DETAIL-RETRY-072

### Finding and change

A read-only review found a stale-evidence path in teacher detail retry. If loading the selected Workspace detail failed, a second synthetic teacher could acknowledge the submission before the first teacher retried. The retry previously refreshed the Workspace revision while continuing to use the cached submission, so the UI could present a closed submission as actionable even though the API would reject its review write as stale.

`retryTeacherWorkspaceDetail()` now refreshes that assignment's review queue first and requires the same submission ID, version and Workspace ID to remain in `SUBMITTED` or `RESUBMITTED`. It then refreshes Workspace and requires `REVIEW_REQUIRED` or `RESUBMITTED`. If either check fails, it clears the actionable context, hides detail controls, keeps the refreshed queue count, and tells the teacher to select a current pending task. Queue or Workspace read errors retain an explicit unknown/retry state. The existing static test now verifies queue-before-Workspace ordering and both state guards.

Files changed for this task: `apps/teacher-web/app.js`, `tests/test_workspace_frontend_html.py`; this rolling Artifact and the project entry/current-state documents record the evidence. The change is limited to the teacher detail retry path.

### Dynamic synthetic browser evidence

Edge at 1280x900 used the loopback `detail` fault mode and one process-local synthetic assignment/submission. The first selected-detail Workspace GET returned injected HTTP 503 after its configured delay; the page showed the selected detail as unknown with an explicit retry. A second synthetic teacher then ACKed that submission through the local API (HTTP 201). On retry, the page refreshed the queue, showed `待复核 0 项`, displayed the message that the submission is no longer pending, kept `#review-details` hidden, and left review action buttons disabled. The retry made no stale review write. The loopback process was stopped after the check; no real identities, data, models or student code were used.

### Verification

- `python -m unittest discover -s tests` — 209 tests, 208 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 41/41.
- `python -m unittest discover -s tests -p test_workspace_api.py` — 38/38; `test_workspace_wsgi.py` — 11/11; `test_workspace_frontend_html.py` — 45/45.
- `node --check` for student app, teacher app and workspace client; `python -m compileall -q apps tests`; API Schema JSON parse; and `git diff --check` passed.
- The sole skip remains Windows symlink creation permission and is not symlink-safety evidence. AppContainer runner-path diagnostics appeared during the full Python suite but did not affect exit 0.

A→B→A event timeline browser evidence was also completed in Edge at 1280x900 against the process-local three-task Harness. A event retry #2 was delayed and configured to return 503; while it was pending, B was explicitly selected and its events loaded successfully, then A was selected again and its newer event read returned 200. When the old A retry returned 503, A remained selected, its three-event timeline and “事件读取成功” state were unchanged, and the retry button stayed hidden. Observed A event responses were 503, 200, 503 in that order. The loopback process was stopped. The read-only audit had found the generation/current-Workspace guards in `loadReviewEvents()` and this browser order found no defect. Overall R0 P3/P4 remains **PARTIAL**; no owner decision is required. Commit: NONE.


## Task R0-P3-C-REVIEW-QUEUE-RETRY-075

### Finding and change

The detail retry now performs a review-queue read before it can trust the cached submission. A read-only audit found that if this prerequisite queue read failed, the catch path incorrectly described a Workspace detail failure and left the old queue count visible as confirmed.

`retryTeacherWorkspaceDetail()` now tracks whether the queue or Workspace read failed. On queue failure, it marks only that assignment's queue result unknown, updates the aggregate count to `?`, clears the old review context and detail result, hides detail controls, disables review actions, and exposes the task-local queue retry. Workspace detail failures remain separately labeled and retryable. A static regression test protects these branches.

### Dynamic synthetic browser evidence

Edge at 1280x900 used the loopback `detail` Harness. The first Workspace detail read returned injected 503. A second synthetic teacher then ACKed the submission (HTTP 201). During the first teacher's detail retry, the prerequisite review-queue read was intercepted as 503. The task row changed to “待复核数量未知”, the aggregate badge changed to `?`, the message identified the queue read failure, detail stayed hidden and review controls stayed disabled. Clicking the task-local queue retry then returned the actual empty queue and rendered “待复核 0 项”; the stale submission detail was not resurrected. The loopback was stopped after the check.

## Task R0-P3-A-ASSIGNMENT-WORKSPACE-BINDING-076

### Finding and change

A read-only student switching audit found that the page trusted the Workspace nested in the selected assignment without checking its `assignment_id`. It also trusted a Workspace GET or start receipt based only on Workspace shape and ID. A mismatched but structurally valid response could pair task B's title with task A's Workspace.

The student loader now rejects a nested Workspace whose `assignment_id` differs from the explicitly selected assignment, checks the same relationship after Workspace GET and after a start receipt, and routes mismatches through `invalid_response` into the task-local unknown state. It keeps the work area hidden until the binding is confirmed. A static regression checks all three guards and confirms the first two run before any start call.

### Dynamic synthetic browser evidence

Edge at 1280x900 used the `student-switch-workspace-fail` loopback Harness with synthetic A and B assignments. After A was paused, a browser route supplied B's assignment DTO with A's structurally valid nested Workspace. The student page reported “读取失败 · 未知”, kept both work area and task rail hidden, and sent no Workspace start request. The mismatched DTO was rejected before Workspace GET/start or submission handling. This verifies the fail-closed path only; retry recovery after restoring a valid B DTO was not claimed by this browser run. The loopback was stopped after verification.

### Verification

- `python -m unittest discover -s tests` — 210 tests, 209 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 41/41.
- `python -m unittest discover -s tests -p test_workspace_api.py` — 38/38; `test_workspace_wsgi.py` — 11/11; `test_workspace_frontend_html.py` — 46/46.
- `node --check` for student app, teacher app and workspace client; `python -m compileall -q apps tests`; Harness `py_compile`; API Schema JSON parse; and `git diff --check` passed.
- The sole skip remains Windows symlink creation permission and is not symlink-safety evidence. AppContainer runner-path diagnostics appeared during the full Python suite but did not affect exit 0.

Both changes are limited to stale/invalid read handling and preserve explicit selection. Overall R0 P3/P4 remains **PARTIAL**; no owner decision is required. Commit: NONE.


## Task R0-P3-C-TEACHER-CROSS-ASSIGNMENT-BINDING-077

### Finding and change

A read-only audit found a conditional cross-task DTO risk: the current in-memory API scopes queues correctly, but a structurally valid queue response could still contain a submission from another assignment. The client checked only the submission shape. The teacher page could then fetch the submission's declared Workspace and label its evidence with the selected assignment.

The shared client now requires every queue item to be `SUBMITTED` or `RESUBMITTED` and optionally validates its Workspace ID and assignment version. The teacher page uses a `readReviewQueueForAssignment()` helper that first requires the assignment's embedded Workspace to point back to the same assignment, then asks the client to validate every queue DTO against that Workspace, version and pending-state contract. Before creating the review context, both initial detail loading and detail retry also require the fetched Workspace `assignment_id` to match the selected assignment. Any mismatch becomes a local unknown queue/detail result and cannot enable cross-task review actions. Regression assertions cover the client parameters and UI guards.

### Dynamic synthetic browser evidence

Edge at 1280x900 used the three-task `teacher-event-retry-delay` loopback Harness. A browser route replaced assignment A's review-queue submissions with assignment B's shape-valid submission. A was shown as `待复核数量未知`; B still showed one pending item and C zero. No Workspace GET for B was issued while processing A's queue, and review details stayed hidden. After explicitly selecting B, the page loaded B's own title, details and event timeline successfully. This validates local failure isolation and that B remains selectable; no cross-task review write was attempted. The loopback was stopped.

This is conditional malformed-response defense. It does not claim the current server emits cross-bound data; the API queue and history routes are assignment scoped in the local implementation.

### Verification

- `python -m unittest discover -s tests` — 210 tests, 209 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 41/41.
- `python -m unittest discover -s tests -p test_workspace_api.py` — 38/38; `test_workspace_wsgi.py` — 11/11; `test_workspace_frontend_html.py` — 46/46.
- `node --check` for student app, teacher app and workspace client; `python -m compileall -q apps tests`; Harness `py_compile`; API Schema JSON parse; and `git diff --check` passed.
- The sole skip remains Windows symlink creation permission and is not symlink-safety evidence. AppContainer runner-path diagnostics appeared during the full Python suite but did not affect exit 0.

Overall R0 P3/P4 remains **PARTIAL**. There is no owner decision required. Commit: NONE.


## Task R0-P3-C-REVIEW-HISTORY-PRESERVE-084

### Finding and change

A bounded failure-isolation audit found that a failed teacher assignment-directory refresh replaced the review-history pages with one empty error row, discarding history that had already been read successfully. The history view now keeps those prior rows and reports the directory refresh failure separately as unknown, with a retry. The retry start message says that existing history is retained.

The same audit found that an empty published-assignment list passed through the renderer's “API returned no review actions” branch, even though no review-history request had been sent. The history view now distinguishes “no published tasks; history API not requested” from an API-confirmed empty action list. The workspace API contract already defines empty history as an empty array; this change does not alter that contract.

### Evidence and verification

- Source/test audit confirmed no authority conflict. The active quality rule requires failures and incomplete states to remain visible; the API contract defines the successful empty-history response. This implementation makes the directory and history API states explicit.
- Static regression coverage now asserts prior page preservation, an independent directory-refresh error, the no-published-task state, and the distinction from a successful empty history response.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py` — 46/46.
- `python -m unittest discover -s tests` — 210 tests, 209 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 43/43; Workspace API — 38/38; WSGI — 11/11.
- Student, teacher and shared-client `node --check`; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` passed.
- The Python run printed AppContainer temporary runner-path diagnostics, but exited 0. The sole skip is Windows symlink creation permission, not symlink-safety evidence.

No browser interaction was performed for these two view states in this step; behavior is covered by static assertions and the independent client/API test layers. Overall R0 remains **PARTIAL**. Commit: NONE.


## Task R0-P3-A-PAUSE-ASSIGNMENT-BINDING-085

### Finding and change

A student single-active-task audit found that pause success, pause retry success, and pause-state readback trusted a returned Workspace state without confirming that it belonged to the task whose pause was being resolved. The shared client now accepts an optional expected assignment ID for Workspace reads and pause receipts and rejects a cross-assignment DTO. The student page supplies the captured assignment ID for the initial pause, retry of the same pause request, and recovery readback. A mismatched 2xx receipt therefore follows the existing unknown-write recovery path and cannot unlock task switching as a confirmed pause.

### Evidence and verification

- `node --test tests/workspace-client.test.mjs` — 43/43, including cross-assignment pause receipt and Workspace readback rejection.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py` — 46/46, including the expected assignment binding on all three student pause paths.
- The full Python, API, WSGI, syntax, compile, Schema JSON, and `git diff --check` results are the same run recorded under Task084 immediately above.
- No browser interaction was performed for a malformed pause receipt; the student unknown/locked outcome is established by the page catch path plus client rejection tests and static assertions. This is not evidence that the current local API emits cross-bound pause receipts.

This change protects the explicit “pause before switching” invariant under malformed or cross-bound responses and does not claim production concurrency or identity guarantees. Overall R0 P3/P4 remains **PARTIAL**; no owner decision required. Commit: NONE.


## Task R0-P3-B-ASSIGNMENT-DIRECTORY-UNIQUE-IDS-088

### Finding and change

A teacher task-selection audit found that the shared client validated each Assignment DTO in a directory response but did not require assignment IDs to be unique. A malformed response could render duplicate task choices while the teacher's result Map collapsed them to one entry, making the visible selection ambiguous. `listAssignments()` now rejects a response with duplicate IDs as `invalid_response`; the existing directory error/retry path then keeps the failure explicit rather than showing an ambiguous list.

### Verification

- Added a Node client regression with two individually valid Assignment DTOs sharing the same ID but differing revisions; the directory read now rejects the envelope.
- `node --test tests/workspace-client.test.mjs` — 43/43.
- `python -m unittest discover -s tests` — 210 tests, 209 passed, 1 skipped; exit 0. The sole skip is Windows symlink creation permission, not symlink-safety evidence. The run printed AppContainer temporary runner-path diagnostics without affecting its exit status.
- Workspace API — 38/38; WSGI — 11/11; frontend static — 46/46.
- Student, teacher, and shared-client `node --check`; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` passed.
- This malformed-directory path was not browser-tested; the client DTO rejection and existing page error/retry contract are the available evidence. Normal API uniqueness is not disputed.

Overall R0 P3/P4 remains **PARTIAL**; no owner decision required. Commit: NONE.


## Task R0-P3-A-START-ASSIGNMENT-RECEIPT-BINDING-094

### Finding and change

The active contract binds a start request to its addressed Workspace and revision, and the Workspace DTO carries an assignment ID. The Student page already rejected a start response for a different assignment before installing it, so the normal local API showed no defect. The shared client boundary itself did not accept an expected assignment ID, however, leaving direct callers without the same protection.

`startWorkspace` now accepts an optional expected assignment ID and rejects a response bound to another assignment. The Student page passes the assignment selected by the student. Existing callers that omit the optional value remain supported. A Node regression supplies a shape-valid response for another assignment and confirms `invalid_response`; the frontend static test confirms the selected ID is passed.

### Verification

- `node --test tests/workspace-client.test.mjs` — 43/43.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py` — 46/46.
- Full Python suite and the common syntax/schema/diff checks are recorded under Task095 below.
- This is malformed-response boundary hardening; it is not evidence that the normal API returned a cross-assignment receipt.

## Task R0-P3-C-REVIEW-HISTORY-DIRECTORY-RETRY-BROWSER-095

### Synthetic browser evidence

Added the Harness-only `teacher-history-directory-fail` mode. It seeds one published synthetic assignment and one successful `REQUEST_EXPLANATION` action, then returns a synthetic 503 on the third teacher assignment-directory GET. No production runtime code changed for this fault injection.

The Codex in-app browser exercised the loopback page at `127.0.0.1:8767`: first the review queue and review history loaded successfully, then revisiting the review view caused the directory refresh to fail. The prior history list item remained visible with its explanation reason; the history region independently said the directory state was unknown and that successful history was retained, with a visible “重试读取” button. Clicking that button recovered the directory/history view while preserving the same action. The queue region separately showed its own unavailable state during the failed navigation. At 360×800, document and body `scrollWidth` equaled `clientWidth` (345 CSS px with the vertical scrollbar; viewport 360px), so the page had no horizontal overflow. The viewport was reset, temporary tabs were closed, and the loopback process was stopped.

One preliminary attempt was invalid because a diagnostic directory request consumed the injected third-read failure before the intended sequence. The harness was restarted, the sequence was rerun without that diagnostic request, and only the latter run is counted as evidence.

### Verification

- `python -m unittest discover -s tests` — 210 tests, 209 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 43/43.
- Workspace API — 38/38; WSGI — 11/11; frontend static — 46/46.
- Student, teacher, shared-client `node --check`; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` passed.
- The sole skip is Windows symlink creation permission; it is not symlink-safety evidence. The full suite printed AppContainer temporary runner-path diagnostics but exited 0.

This is local synthetic loopback and limited 360px browser evidence. It does not establish production HTTP integration, real identity, persistent history, or complete P4 visual coverage. Overall R0 remains **PARTIAL**. No owner decision required. Commit: NONE.


## Task R0-P3-C-STUDENT-SAME-WORKSPACE-STALE-REMEDIATION-096

### Dynamic synthetic browser evidence

The existing `student-remediation-retry-delay` Harness mode was reused without source changes. In the in-app browser, assignment A first returned a synthetic 503 for remediation. The student retried A; that second A remediation GET was delayed and would return 503. While it was pending, the student selected B, the page started B's synthetic Workspace, the student paused B, and then explicitly returned to A. A's newer remediation read returned 200 with the task A remediation. The Harness access log shows that successful A GET before the older A GET returned its delayed 503. After the stale failure arrived, A remained selected and its confirmed task-specific remediation text stayed visible; the latest-submission region also remained confirmed and unchanged. This exercises the same Workspace ID before and after switching, not only a late A response while B remains selected.

At 360×800, `documentElement` and body each reported clientWidth and scrollWidth of 345 CSS px (the 360px viewport includes the vertical scrollbar); no horizontal overflow was present. The browser screenshot was captured and visually inspected but not saved to the Artifact. The page's displayed code remained inert; no student code or real data was run. The synthetic B task was paused before returning to A, so two tasks were never active simultaneously.

### Verification

- Browser and Harness access log confirm order: delayed A remediation retry → B selection/start → B pause → A remediation GET 200 → older A remediation GET 503.
- The final A remediation region remained confirmed after the delayed failure; latest-submission display remained confirmed and separate.
- `node --check` for student app, teacher app and shared client; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` passed in the same Task095 verification run. No runtime code changed after that run.

This is limited local synthetic browser evidence at 360px. It does not establish other browsers, 320px support, persistent state, production HTTP, authentication, or full P4 acceptance. Overall R0 remains **PARTIAL**. No owner decision required. Commit: NONE.


## Task R0-P3-C-STUDENT-SAME-WORKSPACE-STALE-LATEST-097

### Dynamic synthetic browser evidence

The first browser attempt did not establish the requested ordering: the earlier A 503 returned before the browser completed the B pause and A re-read. It is excluded from PASS evidence. To make the local sequence observable without changing product behavior, the Harness-only `student-latest-retry-delay` mode now waits 15 seconds before returning its second-read 503 (previously 5 seconds).

On the valid rerun, A's first latest-submission read returned 503; the student retried that same A Workspace, starting a delayed second read. While it was pending, the student selected B, B started, the student paused B, and the student explicitly returned to A. A's newer latest-submission GET returned 200 with `submission-1`, version 1, `SUBMITTED` before the older A GET returned its delayed 503. The Harness access log confirms this order. After the stale 503 arrived, A remained selected and the confirmed snapshot and explanation were still visible; no stale-failure notice replaced them. The student did not have two active tasks. The displayed synthetic Python text was not executed.

At 360×800, root and body `scrollWidth` equaled `clientWidth` at 345 CSS px (360px viewport including the vertical scrollbar); at 1280×800 both equaled 1265 CSS px. Screenshots were captured and visually inspected but not saved. A second valid run preserved the raw Harness outputs under `browser-r0-p3-latest-race-2026-09-26/`: `harness.http.log` records the request order and `harness.stdout.log` records the mode and stale-request marker. SHA-256 values are `00E36D1D638A1C82727CEE717D77128B8FE3BA795496A683746170D15B0EFDEB` and `ECD9BF9ED5F0ECE9F564E1FE629B966ACD8F3071BD1841FB8C009C5909A1381E`, respectively. The viewport was reset, the temporary tab closed, and the loopback server stopped.

### Verification

- Browser and Harness log confirm: A latest read #1 503 → A retry #2 pending → B start → B pause → A latest read #3 200 → older A retry #2 503.
- `python -m unittest discover -s tests` — 210 tests, 209 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 43/43.
- Workspace API — 38/38; WSGI — 11/11; frontend static — 46/46.
- Student, teacher and shared-client `node --check`; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` passed.
- The only skip is Windows symlink creation permission, not symlink-safety evidence. Full Python output included temporary AppContainer runner-path diagnostics and exited 0.

The only source change in this task is the test Harness wait duration; there is no product runtime change. Evidence remains local synthetic, limited browser coverage and process memory. It does not establish production HTTP, real identity, persistence, 320px support or full P4 acceptance. Overall R0 remains **PARTIAL**. No owner decision required. Commit: NONE.

## Task R0-P3-C-TEACHER-REVIEW-DIRECTORY-RETRY-098

### Finding and change

A read-only P3-B/C audit confirmed that per-assignment queue failures, task selection and task-local retries already have browser evidence (Tasks 025/026/030/037–039/075). The uncovered case was the assignment directory itself failing during a teacher review refresh. On a directory 503, the prior overview DOM could remain visible even though its backing result Map had been cleared; its old “查看此任务” button was still clickable. The review-history region already preserved successful history and exposed its own retry, but there was no review-page control that restored the task overview and queue results together.

The teacher review loader now tracks directory failure separately, marks the task list as unknown, hides the stale task-choice region, and shows a dedicated “重试读取任务目录” control. A successful directory retry clears the control and refreshes the top-level API status without claiming other regions succeeded. Existing history rows remain visible during the directory failure. The local-only Harness adds `teacher-review-directory-fail`, which seeds three synthetic tasks and returns one actual loopback 503 on the third teacher assignment-directory GET.

### Dynamic synthetic browser evidence

Microsoft Edge was driven through Playwright at 360×800. The test loaded the task directory and review overview, left and re-entered the review page, then observed assignment-directory responses `200 → 200 → 503`. During the 503 state, the task list was hidden (so stale task actions could not be used), the directory status explicitly said the review-task list was unknown, the dedicated retry was visible, and the previously loaded review-history row remained visible. Clicking the dedicated retry produced `200`; all three task rows returned (A and B each had one pending submission, C had zero), the retry control disappeared, and the API status reported directory-read success. Root and body client/scroll widths were each 360/360 CSS px.

Screenshots are stored in `browser-r0-p3-directory-retry-2026-09-26/`: `directory-failure-360px.png` and `directory-recovered-360px.png`. `browser-run.json` records the request order, states, dimensions and evidence limits; `harness.stderr.log` preserves the raw loopback HTTP access log and `harness.stdout.log` preserves the Harness startup record. Temporary loopback service and browser were stopped. An earlier attempt against a reused Harness process and an assertion expecting a unique pending row were excluded; the final run used a fresh process and verified both valid pending rows.

### Verification

- `python -m unittest discover -s tests -p test_workspace_frontend_html.py` — 47/47.
- `python -m unittest discover -s tests` — 211 tests, 210 passed, 1 skipped; exit 0. The one skip is unavailable Windows symlink-creation permission and is not symlink-safety evidence; temporary AppContainer runner-path diagnostics did not affect the exit code.
- `node --test tests/workspace-client.test.mjs` — 43/43.
- Workspace API — 38/38; WSGI — 11/11.
- `node --check` for Student, Teacher and shared client; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` — passed.

Changed files for this task: `apps/teacher-web/app.js` (unknown directory state, hide stale choices, scoped retry, refresh-success status), `apps/teacher-web/index.html` (retry control), `tests/test_workspace_frontend_html.py` (regression assertions), Harness `p3_teacher_generation_fault_server.py` (test-only deterministic fault mode), this report, the Artifact evidence directory, and project entry/current-state documents. `docs/CURRENT_STATE.md` also relabels 49 older snapshot headings as historical records so they cannot be mistaken for the latest state.

Raw evidence SHA-256: HTTP access log `harness.stderr.log` `A311973B0D80C98530667681DA68D12A73A9300F5E2FE89C92AB1CBDEEF9052C`; Harness stdout `harness.stdout.log` `8E7B6DC0FFF09A4AED8A6D34015AB846C049CE234E5D868129FB5E6B013A5BD8`; browser summary `browser-run.json` `F00042E83C4C115FA13B82C18DC763B5031751A176AC8635BC96A991EC749C31`.

This closes one local review-directory failure/retry path only. Gate remains PARTIAL: full responsive state/device coverage and production integration are not established; 320px support remains unspecified. No real identity/data/model/ECS/deployment or student code execution was used. No owner decision is required. Commit: `NONE`.

## Task R0-P3-A-STUDENT-WORKSPACE-STATE-LABELS-099

### Finding and change

The student workspace picker and current-task status displayed most valid Workspace wire states as raw enum values. Added a display-only Chinese label mapper for the seven states in the active API Schema: `ASSIGNED` (“已分配，准备开始”), `IN_PROGRESS` (“进行中”), `PAUSED` (“已暂停”), `REVIEW_REQUIRED` (“等待教师复核”), `FEEDBACK_REQUIRED` (“等待你补正”), `RESUBMITTED` (“已补交，等待教师复核”), and `CLOSED` (“本轮已结束”). Empty state remains “未连接”; an unmapped value renders “状态未知”. Existing behavior continues to use the raw state enum. The specific remediation request remains rendered in its separate region. No wire values, transitions or failure handling changed.

An independent read-only product-copy review confirmed the distinctions against `REQUIREMENTS_SPEC.md` and the Workspace Schema; it recommended softening ASSIGNED so the label does not assert a start has already happened. The implemented label is “已分配，准备开始”. `NOT_STARTED`, `WAITING_STUDENT` and `SUBMITTED` were not added as Workspace states.

### Verification

- `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 43/43.
- Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48.
- Student, teacher and shared-client `node --check`; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` — passed.
- The sole Python skip is unavailable Windows symlink-creation permission; it is not symlink-safety evidence. Full-suite AppContainer helper emitted temporary runner-path diagnostics but exited 0.

Changed files: `apps/student-web/app.js` (display labels only), `tests/test_workspace_frontend_html.py` (all seven values, unknown/empty fallback, and unchanged raw-state behavior assertion), this report, and project status/entry documents. No browser visual pass was run for this copy-only mapping; dynamic HTTP, state transitions, authentication, production integration and full P4 are not claimed. Overall gate remains PARTIAL. No owner decision required. Commit: `NONE`.

## Task R0-P3-A-FAILED-START-NO-SIDE-EFFECT-100

### Finding and change

A read-only API audit confirmed service-side active-workspace exclusion and found the double-workspace test did not explicitly prove that B's rejected start left either workspace or its event stream unchanged. Expanded `test_student_can_only_have_one_active_workspace_and_pause_switch_resume_isolated` to snapshot both event arrays before the blocked B start, then assert after `409 active_task_exists` that A remains `IN_PROGRESS` at its prior revision, B remains `ASSIGNED` at its prior revision, and both event arrays are byte-for-byte equivalent as decoded DTO arrays. After pausing A, the test retries B with the same idempotency key and original B revision and asserts success. This changes regression evidence only; API behavior and production code are unchanged.

Independent review confirmed the rejection-side invariants and same-key retry assertion. The test's subsequent flow continues through B remediation, blocks A resume while B is active, then resumes A; the existing test checks task-scoped submissions/remediation.

### Verification

- Targeted Workspace API suite — 38/38.
- Final Python full suite — 212 tests, 211 passed, 1 skipped; exit 0.
- Node client — 43/43; WSGI — 11/11; frontend static — 48/48.
- JS syntax checks, Python compileall, Harness py_compile, Schema JSON parse, and `git diff --check` — passed.
- The single skip remains Windows symlink-creation permission, not symlink-safety evidence; temporary AppContainer runner-path diagnostics appeared, but the full suite exited 0.

Changed files for Task100: `tests/test_workspace_api.py` (failed-start no-side-effect and retry-idempotency assertions), this Artifact report, and current project entry/status documents. This verifies the in-process synthetic API only, not multi-process or production concurrency. Gate remains PARTIAL. No owner decision required. Commit: `NONE`.

## Task R0-P3-C-STALE-TEACHER-EVENT-SUCCESS-101

### Dynamic synthetic browser evidence

The existing browser evidence covered delayed stale event failures. To check the complementary late-success case without changing product code or the Harness, Microsoft Edge was driven with the existing `teacher-multi-queue` loopback fixture. Playwright intercepted task A's real nonempty `/events` HTTP 200 after `route.fetch()` and held that unchanged response at the browser boundary. While held, the teacher explicitly selected task B and B's own events loaded successfully. Releasing A's original 200 left B selected, B's timeline unchanged, and its event-success state unchanged. Browser-run JSON records the A/B IDs, event GET URLs/statuses, timeline before/after, and assertion results. Two earlier script attempts were excluded: one asserted a nonexistent workspace ID in the event DTO; another waited for a status string without its final punctuation. They did not modify application or Harness code and produced no PASS evidence.

Screenshots `browser-r0-p3-stale-event-success-2026-09-26/task-b-before-stale-a-response-1280px.png` and `task-b-after-stale-a-200-1280px.png` were captured and visually inspected. The final run used synthetic process-memory tasks only; no review write or student code execution occurred. This simulates client-visible delay by holding the actual loopback response in Playwright; it does not establish server-side response delay.

### Verification

- Browser: installed Microsoft Edge through Python Playwright, 1280×900; A event GET returned nonempty 200; B event GET returned 200 before release; after the stale A 200, B title, timeline and status remained identical.
- The implementation remained unchanged. The immediately preceding final matrix for Tasks099/100 passed: Python 212 tests (211 passed, 1 skipped), Node 43/43, Workspace API 38/38, WSGI 11/11, frontend static 48/48, syntax/compile/schema and `git diff --check` all pass.
- Screenshots and machine-readable run record are in `browser-r0-p3-stale-event-success-2026-09-26/`; the deterministic request evidence is the response ordering recorded in `browser-run.json`.

Changed files for Task101: the report, `browser-run.json`, and two screenshots only. No product code or Harness source changed. Event generation guards are dynamically exercised for stale success on this path; this remains finite local synthetic browser evidence, not full P4 or production integration. Overall Gate remains PARTIAL. No owner decision required. Commit: `NONE`.

## Task R0-P3-A-STUDENT-STATE-LABEL-BROWSER-102

### Dynamic synthetic browser evidence

Microsoft Edge via Playwright verified the student-facing state labels at 390×844 using existing loopback-only Harness modes. In `events`, explicit task selection displayed “等待教师复核”. In `student-remediation-fail`, the Workspace displayed “等待你补正” while its separate remediation region showed a one-shot HTTP 503, “补正状态未知” and its own retry control. In `student-switch-workspace-fail`, task A was already IN_PROGRESS; the student paused it and the page showed “已暂停” with the switch prompt. All three runs reported `documentElement.clientWidth == scrollWidth == 390`. Screenshots were captured and visually inspected. Each Harness process was stopped after its browser run; all records are synthetic process memory.

The first attempted FEEDBACK_REQUIRED run used `student-remediation`, which waits 20 seconds and returns success rather than failure; the script incorrectly awaited an error and timed out. It is excluded from PASS. The final FEEDBACK_REQUIRED run uses `student-remediation-fail`, which deterministically returns one 503. The initial failed attempt's Harness log and the successful events screenshot are retained in the evidence directory; the successful rerun supersedes that attempt for the feedback state.

Evidence directory: `browser-r0-p3-student-state-labels-2026-09-26/`. `browser-run.json` SHA-256 `F19E84D48DF9CF9B6788428F751FDA42A4F821B64A162FDC8004CB4BDC7B7864`; screenshot SHA-256 values: events `F15320670B9BD8400A0A395F3CC9A63BF604637AAB9E34ECBC6F79F5223BB82D`, FEEDBACK_REQUIRED with remediation failure `F19C0CFA23E469A8010938BCD45CCAA2E44BBBA20DF2811C4AE175335856D9C8`, PAUSED `A547A4DA5AF45B3A6E0BEFB825686F8D670DDD2DA0C9DCB8896242572B923571`. Harness stdout SHA-256: events `B55CB4B9FA4670F1675AC1E2506D5DB3F853EC6E697C8177533D6B520A04F51E`, remediation failure `EB52152F385AF5382441D4BAB1A2324F29623C39EDDA6A6A1990F8D98F1CABD6`, pause `62BB9D53ADB8E288CA21F98BA11BA2E03BA9EB1415425EF5F9572CA697BB50EC`.

This demonstrates only three local synthetic states and 390px layout. The remaining ASSIGNED, IN_PROGRESS, RESUBMITTED and CLOSED labels are statically covered; this is not exhaustive visual QA, persistence, production HTTP, identity verification, or full P4. No product or Harness source changed for Task102. Overall Gate remains PARTIAL. No owner decision required. Commit: `NONE`.

## Task R0-P3-A-RESUBMITTED-CLOSED-UI-SYNC-103

### Finding and change

The browser feasibility review exposed a concrete display defect in successful student submissions: the handler first mapped Workspace state to `REVIEW_REQUIRED` or `RESUBMITTED`, then immediately overwrote the task card with generic “已提交 · 合成”; it also left the task picker status at its prior state. Updated `setWorkspaceState` to synchronize the task-picker status from the same display mapper, and removed the conflicting generic overwrite. Wire state, transitions and submission behavior are unchanged. Added static regression assertions for both status regions and to prevent reintroducing the overwrite.

### Dynamic synthetic browser evidence

Microsoft Edge through Playwright exercised a full local loopback flow at 390×844: student explicitly selected a `FEEDBACK_REQUIRED` task; the first remediation read returned 503 and its dedicated retry returned 200; student submitted version 2 and immediately saw “已补交，等待教师复核” in both the current-task and picker regions; teacher selected that exact task and acknowledged the new submission (HTTP 201); the queue then showed zero pending items; student refreshed, explicitly reselected the task, read Workspace state `CLOSED`, and saw “本轮已结束” in both regions. Both student screenshots were visually inspected. For each screenshot, root client and scroll widths were 390/390. No student code was run.

Evidence directory `browser-r0-p3-resubmitted-closed-2026-09-26/`: browser-run JSON SHA-256 `04D5F83938D140EF1FF324D81ED3D6FA9989C2D0FAC93F924042BF2CD9D38F0F`; resubmitted screenshot `0B6B55D5D03B58D673D58A95A794BD0CDBDF292E636CFC28A81AAEC711C58AA9`; closed screenshot `4CE5CF34438D5CD57802B07C12C94EF6B27F2AB2335F44257BCC5BBD1D0909B0`; raw Harness stdout `DD4782178A1E1846251D8C2C4AADA9FEF033B31A9219FC2096C24C44B7560731`.

### Verification

- `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped; exit 0.
- `node --test tests/workspace-client.test.mjs` — 43/43.
- Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48.
- Student, teacher and shared-client `node --check`; `python -m compileall -q apps tests`; Harness `py_compile`; Workspace API Schema JSON parse; and `git diff --check` — passed.
- The one skip is Windows symlink-creation permission, not symlink-safety evidence. Temporary AppContainer helper runner-path diagnostics appeared in full Python output; exit status was 0.

Changed files for Task103: `apps/student-web/app.js` (keep mapped RESUBMITTED/CLOSED state visible and sync picker), `tests/test_workspace_frontend_html.py` (regression guards), this Artifact report, browser-run JSON/screenshots/raw Harness output, and current status/entry docs. Evidence remains local process-memory synthetic flow with fixed demo roles; it does not establish persistent storage, real identity, production integration, or full P4. Overall Gate remains PARTIAL. No owner decision required. Commit: `NONE`.





## Task R0-P3-STUDENT-SUBMIT-RECEIPT-LOSS-108 — verify exact retry after a committed submission loses its browser receipt

A read-only audit found the student submission path retains `{workspaceId, revision, dto}` and the client retains its idempotency key after transport failure. Existing API/client tests covered replay, but browser-visible unknown state and a committed server write followed by a lost browser response had not been exercised together. No product source change was needed.

Browser evidence:

- Edge via Playwright, loopback `student-agent-delay` Harness, 390×844 viewport, synthetic assignments A/B. After explicitly selecting A, the browser submitted a fixed synthetic text snapshot. The route handler let the real in-memory API process the first POST and recorded HTTP 201, then aborted only the response to the browser.
- The student page reported that the result was not confirmed, retained “重试同一提交”, and froze the explanation and editor. The view stayed 390px wide (`clientWidth=scrollWidth=390`).
- The explicit retry used the same POST method, workspace URL, byte-identical JSON body, `If-Match` revision, and `Idempotency-Key`; the API replayed HTTP 201 with the original `submission-1` receipt. UI moved to waiting for teacher review and closed the dialog.
- Readback corroboration: latest submission refers to `submission-1`; event history contained exactly one `submission.created` event, referencing `submission-1`. The replayed idempotency receipt is the primary correlation evidence; latest readback alone would not identify the unknown request.
- Browser run JSON SHA-256: `04D19D075828851D90969B9565CB4B014C0A2E3072D205642CE1B695144AED0C`. Screenshots were visually inspected: unknown `62E4DF71448DAFAF6E2A0A143ECFB9310738905E7483B551D98E6A09C6C74517`; recovered `A544A39122360125ACCE08576A43F9BC99B3F4F2FC0C1C4621D722B380F979C8`. Evidence and the reproducible Playwright runner are under `browser-r0-p3-student-submit-receipt-lost-2026-09-26/`.
- This is finite local synthetic browser evidence against an in-memory WSGI Harness. It does not establish durable storage, browser matrix coverage, real accounts/data/models, production HTTP, or secure execution. No real student code ran.



Verification after Task108: `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped, exit 0; the sole skip is Windows symlink-creation privilege and provides no symlink-safety evidence. `node --test tests/workspace-client.test.mjs` — 43/43; `python tests/test_workspace_api.py` — 38/38; `python tests/test_workspace_wsgi.py` — 11/11; `python tests/test_workspace_frontend_html.py` — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. Temporary AppContainer runner-path diagnostics appeared during the full suite but exit was 0. The Task108 browser run added no product-source change; this remains finite synthetic local-browser evidence. Commit: NONE.


## Task R0-P3-TEACHER-ACK-RECEIPT-LOSS-109 — verify the teacher browser recovers an ACK whose API receipt was dropped

A read-only gap audit found that Task042 already exercised a committed ACK followed by a Harness-generated 503, but the stronger browser-boundary case was missing: the real in-memory API returns 201 and Playwright drops only that response. A neutral `teacher-detail-delay` synthetic Harness supplied three reviewable task queues; the Playwright route handler intercepted only the selected A ACK.

Browser evidence:

- Edge via Playwright at 390×844. The teacher explicitly selected synthetic task A and saw its version 1 `SUBMITTED` item. The first ACK POST was processed by the actual local API and returned HTTP 201; the route handler then aborted the browser response.
- The page showed an unconfirmed ACK message bound to A/version 1/action/reason. The reason and submission tabs were disabled; only the same ACK action remained available. An attempted selection of B did not replace A's detail or the fixed reason; the persistent API status region continued to show the unknown receipt and exact-retry instruction.
- Repeating the same action sent byte-identical JSON, same submission URL, `If-Match`, and `Idempotency-Key`; the API replayed HTTP 201 with the same `review-2` action ID. Task-specific readback showed A queue 0, B queue 1, C queue 0, and total pending 1. Assignment A's review-history read returned exactly one matching ACK; workspace events returned exactly one `review.action_recorded` event referencing that action ID. The replayed API receipt/action identity is the request-correlation evidence; history is corroboration.
- Root width remained 390/390. Three screenshots are under `browser-r0-p3-teacher-ack-receipt-lost-2026-09-26/`; hashes: unknown A `60BB85DD6CF16D0208DBDE6DA45E7C3F0D78E3F3EED310622F82E9F3D3DB623C`, attempted B selection `1AB2573864D72CC291704DB811D01574AEEEBE1513611B91AB694E6F0A7D5452`, recovered queues/history `CA5833ACB26B5A98281C93B59E2544D266314DC2DA9F84922EFB324EA45C9D0A`. Browser-run JSON SHA-256: `9E630E27EB95B199B10CDC66F696E124DC68B54EB8E4D14D7EB99B61331FCBE1`.
- A first harness selection was excluded because that Harness itself transformed the ACK response to 503, so it did not prove browser-side receipt loss. The accepted rerun used an unaffected in-memory API response and route-level abort. This finite local synthetic evidence does not establish persistence, reload recovery, real identity/data, production HTTP, or secure execution. Page-refresh recovery of an unknown ACK remains uncontracted; the UI attempt and idempotency key are page-memory state, and history cannot associate an entry with a particular lost request. Do not infer the contract or persist it without a product decision.
- No product source or test-suite file changed; the evidence runner and browser artifacts are in the evidence directory. No real code was executed.



Final regression after Task109: `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped, exit 0; the sole skip is Windows symlink-creation privilege and is not symlink-safety evidence. `node --test tests/workspace-client.test.mjs` — 43/43; Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, Python `compileall`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. Temporary AppContainer runner-path diagnostics did not affect the successful full-suite exit. Task109 changed only its evidence runner/report; no product code or test-suite source changed. Commit: NONE.


## Task R0-P3-TEACHER-ACK-UNKNOWN-AFTER-RELOAD-110 — record the current recovery boundary

A read-only source audit found no accepted product contract for persisting a teacher ACK attempt across refresh. The primary control-plane spec says the in-page attempt/idempotency key is lost at reload and review history cannot identify which unknown request produced an ACK; the teacher workflow does not choose a reload strategy. A bounded browser check confirms the current behavior without changing it.

Browser evidence:

- Edge via Playwright at 390×844. A real local synthetic API ACK returned 201 and the browser route dropped that response. Before reload, the UI showed the ACK as unknown. After a full page reload and opening the review view, no original pending-attempt result remained and neither localStorage nor sessionStorage contained an attempt key.
- Current state was rendered as A queue 0, B queue 1; review history showed A's ACK, reason and event sequence, while its own heading explicitly warned that history cannot confirm a particular pre-refresh unknown request. The general API banner only reported directory-read success. This check does not link the history item to the dropped browser request.
- Root/document width stayed 390/390. Screenshot SHA-256: `F014F18B9582DA200BDE980850CC2758E1D8EE0D385ED3A13B604F4B04510706`; browser-run JSON SHA-256: `770546AFC0C1B847A48A99AB92E413CEDB89E89038D90E453CA545730C2C4AE8`. Evidence and runner: `browser-r0-p3-teacher-ack-reload-unknown-2026-09-26/`.
- This is current synthetic behavior evidence, not an accepted recovery design. Do not silently add browser storage for the teacher's reason and idempotency key, or infer request identity from history. If exact refresh recovery is required, the owner must select a contract: tab-scoped attempt persistence and cleanup; no attempt persistence plus explicit uncorrelated-state instructions/manual action; or a later authenticated server-side receipt-recovery API. Until then, local behavior stays within the existing in-memory contract.
- No product code or test-suite source changed; no real identities/data/models/ECS/deployment or student code were used.



## Task R0-P3-TEACHER-REMEDIATION-RECEIPT-LOSS-111 — verify exact readback confirmation and the student-facing correction loop

A read-only audit found the non-ACK teacher review recovery branch differs from ACK: after a lost response it reads Workspace plus remediation records, and confirms only an exact open remediation matching submission, action and reason. Browser evidence for that branch was missing. The accepted run used a fresh `teacher-detail-delay` synthetic process with three tasks and an open review queue.

Browser evidence:

- Edge via Playwright at 390×844. The teacher explicitly opened synthetic task A/version 1 and chose “要求补正”. The real local API processed the POST and returned HTTP 201; Playwright then aborted only the browser response. Exactly one review-action POST was observed; the UI did not send a duplicate write.
- After the lost response, the client read A's Workspace and remediation list. The local request trace confirmed these readbacks preceded the directory/queue refresh. The teacher page then displayed A's OPEN remediation with the exact reason; the task list showed A queue 0 and B queue 1. Read-only API corroboration found one matching ReviewAction, one OPEN remediation with the same review_action_id/submission/action/reason, and one `review.action_recorded` event referencing that action.
- The student explicitly selected A. The wire Workspace state was `FEEDBACK_REQUIRED`, the visible state label was “等待你补正”, and the student-facing remediation message contained the exact teacher reason. Teacher and student viewports both stayed 390/390. Screenshots were visually inspected: teacher `618ECCD32809C9A520BBCF848580805F9B7CFD666FF2648974798373E75900D4`; student `B88E77365D7521C62AD45D1DBF32D47667C3A132081752B8D02E62A5D06646B3`. Browser-run JSON SHA-256: `0A2671E126FB148FD7AE69AD30801F52E0482710857C03150B83077B1890BB8C`. Reproducible runner/evidence: `browser-r0-p3-teacher-remediation-receipt-lost-2026-09-26/`.
- Two exploratory attempts were excluded: one looked for a transient message after the page had refreshed its review overview; another reused a Harness process after its in-memory A remediation had already been written. The final accepted run used a fresh process and asserted exact readback order, one POST, matching records, student state and viewport.
- No product source or test-suite file changed. This remains synthetic in-memory evidence and does not establish durable storage, production integration, real identities/data/models, deployment, or safe student-code execution.



Final regression after Task111: `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped, exit 0; the sole skip is Windows symlink-creation privilege and is not symlink-safety evidence. `node --test tests/workspace-client.test.mjs` — 43/43; Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, Python `compileall`, Harness `py_compile`, API Schema JSON parse, and `git diff --check` passed. Temporary AppContainer runner-path diagnostics did not affect the successful full-suite exit. Tasks109–111 changed no product or test-suite source; only report and synthetic browser evidence artifacts were added. Commit: NONE.


## Task R0-P3-STUDENT-PROPOSAL-DECISION-RECEIPT-LOSS-112 — verify exact retry after a committed proposal rejection loses its browser receipt

A bounded read-only audit found the client retains the original proposal/workspace/revision/decision attempt and idempotency key after an unavailable response. Existing client/API tests did not exercise the browser boundary with a server-committed decision and one event. The audit also notes that reload recovery is not specified; this task does not add persistence.

Browser evidence:

- Edge via Playwright against a fresh local in-memory WSGI Harness at 390×844. The student explicitly selected task A, requested the fixed scripted-demo suggestion, opened its proposal, and chose REJECTED. The local API processed the first POST with HTTP 200; Playwright then aborted only that browser response.
- The page reported unknown, retained the proposal/editor and original rejection as the only enabled decision. A attempted selection of B reverted to A; pause was blocked without a pause POST, submission stayed disabled/no submission POST, and a competing takeover click generated no write. The editor content remained unchanged.
- Retrying rejection used the same method, URL, body, proposal/workspace, If-Match revision 4 and Idempotency-Key. The API replayed the identical decision DTO/revision. Event readback contained exactly one `agent.proposed_action_decided` event for proposal-4; Workspace remained IN_PROGRESS. Root width remained 390/390. No code was written or executed.
- The browser exposed a UI defect: after the retry succeeded, the old top-level unknown banner remained beside the success toast. Updated the success path to replace it with a clear API-confirmed message and added a frontend regression assertion. The fresh rerun now shows no stale unknown state; both screenshots were visually inspected.
- Browser-run JSON SHA-256: `6765D69F2A7A67547E39B7C04834D2CA67B3CE2304EA547266A3C3EFCF526E69`; unknown screenshot: `D71E07A9D6E37E91BFBFB5FF22A2274C5CFEC4EB7BD7FB3D362B2D7FC95B762B`; recovered screenshot: `9868644C0F98242B019B453A2DE00EC0118F85AB3CBE56DF326CD0BAE789701F`. Evidence and runner are under `browser-r0-p3-student-proposal-decision-receipt-lost-2026-09-26/`. Test-only Harness fixture mode `student-proposal-decision` seeds synthetic A/B tasks and the proposed action.
- The first exploratory attempts used an incorrect wait condition and did not reach the decision UI; they are not acceptance evidence. The accepted run used a fresh Harness and verified the proposal became visible before deciding.

Final regression after Task112: `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 43/43; Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness/runner `py_compile`, Workspace Schema JSON parse and `git diff --check` passed. The one skip is Windows symlink-creation privilege and provides no symlink-safety evidence; AppContainer runner-path diagnostics appeared in the successful Python suite.

Task112 changed `apps/student-web/app.js` (clear stale unknown banner only after confirmed proposal-decision receipt), `tests/test_workspace_frontend_html.py` (regression assertion), this evidence directory, the test-only Harness fixture, this rolling report, and status/entry docs. Overall remains PARTIAL: synthetic in-memory local browser evidence only, no production HTTP/durable persistence/real identity/data/model/ECS/deployment/safe code execution. Teacher ACK reload recovery remains uncontracted and no storage was added. No owner decision required for Task112. Commit: NONE.


## Task R0-P3-STUDENT-PROPOSAL-ACCEPT-RECEIPT-LOSS-113 — verify an accepted proposal is applied once only after exact retry

A separate read-only audit confirmed the ACCEPTED handler retains the captured proposal/workspace/revision/target-content attempt after an unavailable response, freezes the editor and applies the in-memory patch only after a confirmed decision receipt and only if the captured content is still unchanged. Prior coverage was static/client mock evidence, not a browser-boundary run.

Browser evidence:

- Edge via Playwright against a fresh local in-memory WSGI Harness at 390×844. The student explicitly selected task A, generated and opened its fixed proposal, then chose “接受并查看修改”. The actual local API returned HTTP 200 for the first decision write; Playwright dropped only that response.
- In the unknown state, the editor and file tabs were frozen; only the same Accept action was enabled. The original page-memory source was unchanged. Attempting to select B reverted to A; pause and submission were blocked without POSTs.
- Retrying used byte-identical body, route, If-Match revision and Idempotency-Key. The API replayed the same ACCEPTED DTO. One matching `agent.proposed_action_decided` event existed; the target text was changed exactly once in page memory (the expected replacement occurred once), and one dirty marker appeared. Workspace remained IN_PROGRESS. No file write, code execution, pause or submission occurred. Root width remained 390/390.
- The UI retained stale unknown copy after successful acceptance, and unknown copy incorrectly advised refreshing despite loss of the in-page retry key on reload. Updated both proposal-decision branches: successful accepted/rejected decisions clear stale unknown status; uncertain accepted/rejected/takeover decisions tell the student to retry the same action in the current page and disclose that refresh loses its retry information. Frontend assertions and fresh browser reruns verify these messages.
- Browser-run JSON SHA-256: `90FBED395B38D47ADFCBB01EF0B5DB8408F8F5524FC73250DCFF82008ED6D04D`; unknown screenshot: `CD7D544CF96D10198544100A88A1F603C065F8867EA92D2467A97DD2F214BAD0`; recovered screenshot: `54DFE91883E96951525A5EDDD7FD71093975393757CB89ACA271B11104E88A12`. Evidence and runner are under `browser-r0-p3-student-proposal-accept-receipt-lost-2026-09-26/`. Task112 was rerun after the shared copy change; updated browser-run JSON SHA-256 is `7723B9F29DB4C944EFF251C858CE1953085AA0A03B4AD5F7E1F0B8E6898B1F95`, unknown screenshot `EC39892B6AAAF9D0416010ED229D36DA9861D579E7007D6C7E2F3F2365EF53B5`, recovered screenshot `9868644C0F98242B019B453A2DE00EC0118F85AB3CBE56DF326CD0BAE789701F`. Both screenshot pairs were visually inspected.
- As with Task112, the accepted path is local synthetic process-memory/browser evidence only. Refresh recovery for proposal attempts is not specified; no persistence was added. No real model, student data, file write or code execution was used.

Final regression after Task113: `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped, exit 0; Node client — 43/43; Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness and both runner `py_compile`, Workspace Schema JSON parse, and `git diff --check` passed. The sole skip is Windows symlink-creation privilege and is not symlink-safety evidence; AppContainer runner-path diagnostics appeared during the successful Python suite. These live rerun values match the historical Task111 snapshot values; earlier artifact hashes are historical and this report's hash is recalculated after the Task112/113 additions.

Task113 changed `apps/student-web/app.js` (clear stale confirmed-state banner and give safe same-page retry guidance), `tests/test_workspace_frontend_html.py` (regression assertions), its browser evidence/runner, and this report/status docs; Task112's Harness fixture and evidence also remain in the preceding section. Overall Gate remains PARTIAL. No owner decision required for Tasks112–113. Commit: NONE.


## Task R0-P3-STUDENT-AGENT-TURN-RECEIPT-LOSS-114 — verify an Agent turn committed before its browser receipt was lost

A read-only gap audit found existing API/client idempotency checks and browser coverage for a delayed in-flight turn, but no browser-boundary check where the real synthetic API completed a turn and only its browser response was lost.

Browser evidence:

- Edge via Playwright against a fresh local in-memory WSGI Harness at 390×844. The student explicitly selected A and sent a fixed question. Playwright let the local API process the first AgentTurn POST (HTTP 200), recorded its turn/proposal DTO, and aborted only the response to the browser.
- While unknown, no user or assistant message had been recorded in the page conversation. The original question remained in the input. A different question was kept in the input but produced no second AgentTurn POST. Restoring the exact original question and retrying reused the same method, URL, JSON body, workspace, If-Match revision and Idempotency-Key.
- The API replayed identical turn/proposal data. Event readback showed exactly one `agent.turn_created` event for the turn; the DOM rendered exactly one user question, one fixed scripted-demo reply and one proposal button. Workspace remained IN_PROGRESS; no pause or submission POST occurred; page source stayed unchanged and no code ran. Root width remained 390/390.
- The browser revealed that the generic unknown message advised refreshing despite the in-page attempt/key being required to replay the exact original question. Updated the AgentTurn error and success messages to give the supported current-page retry instructions and clear the stale banner after confirmed replay. The runner asserts both messages.
- Browser-run JSON SHA-256: `0A664EDF7853F3B2EA4411FE4BCC475D41E0E26BB8E5D14A5A56D23021F966A0`; unknown screenshot: `00EE8985468E492B333CCDC4BF5E41EC85CA0FAB0CC9DE283735712CBAA1F7E2`; recovered screenshot: `E09CFFDD4BCA5B7BAA7A514A4E6A819C36240799BE3C69D5CACDB3045EE4882B`. Runner and evidence are under `browser-r0-p3-student-agent-turn-receipt-lost-2026-09-26/`. Both screenshots were visually inspected.
- This is a finite one-process synthetic browser result. Agent attempt/key and local demo state are not persistent across reload; no refresh recovery contract was introduced. No real model, student data, file write, execution or production service was used.

Final regression after Task114: `python -m unittest discover -s tests` — 212 tests, 211 passed, 1 skipped, exit 0; Node client — 43/43; Workspace API — 38/38; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness and three browser-runner `py_compile`, Workspace Schema JSON parse, and `git diff --check` passed. The sole skip is Windows symlink-creation privilege and is not symlink-safety evidence; the successful Python full suite printed temporary AppContainer runner-path diagnostics. Current counts equal the Task111 historical snapshot counts, now independently rerun after Tasks112–114.

Task114 changed `apps/student-web/app.js` (clear stale success state and make uncertain AgentTurn recovery instructions accurate), `tests/test_workspace_frontend_html.py` (regression assertions), this browser runner/evidence, the rolling report and entry/current-state docs. Tasks112–114 remain local synthetic validation; overall Gate PARTIAL. No owner decision required. Commit: NONE.


## Task R0-P3-TEACHER-ENVIRONMENT-ISSUE-115 — observe receipt-loss readback without deciding product semantics

A read-only audit found that the teacher's `ENVIRONMENT_ISSUE` action follows the shared non-ACK review recovery path, but its meaning for the student is underspecified. To document the current behavior without declaring that behavior correct, a synthetic browser run dropped only the browser response after the local API committed the action.

Browser evidence:

- Edge via Playwright on a fresh `teacher-detail-delay` loopback WSGI Harness at 390×844. The teacher explicitly selected task A and marked its version 1 submission with `ENVIRONMENT_ISSUE`, using a concrete synthetic reason. The local API returned HTTP 201; Playwright aborted only that response.
- The UI read back exactly one matching ReviewAction, one OPEN remediation with `requested_action=ENVIRONMENT_ISSUE`, and one `review.action_recorded` event. The queue showed A=0 pending, B=1, C=0. The server-committed receipt and matching readback—not just queue count—correlated this request.
- The student explicitly selected A. Current wire state was `FEEDBACK_REQUIRED`; the UI showed “等待你补正” and displayed the reason. This is a description of present code behavior only. It does not prove that an environment incident should be assigned to the student as correction work. The teacher also used generic “补正要求已记录” wording.
- Teacher and student browser roots remained 390/390. Screenshots were visually inspected. No source or test-suite files changed for this observational check. No real identities/data/models, files, or code execution were used.
- Browser-run JSON SHA-256: `34DA76B381D99378CBBAE93601247264720AA98BFAF8293FA3C7E3DCACCBF0B2`; teacher screenshot: `B26A0978956075264338E2197A603D1FBBE46808CFF947E6B3D64BE2FCD6A994`; student screenshot: `F5AF5689CA414AD3BF01C1090F9D13B6F33E9CC169346E1DEC4446AD1DA9530E`; runner SHA-256 `E81EEF83EA55FF46F91AFF061A56D50BB6C99C5DECB4E814983F0F37B12BB9F2`. Evidence is under `browser-r0-p3-teacher-environment-issue-receipt-115-2026-09-26/`.

Product decision boundary: the active API currently maps all non-ACK actions to `FEEDBACK_REQUIRED` and an OPEN remediation, and the student UI labels that “等待你补正”. The specifications name `ENVIRONMENT_ISSUE` but do not say whether it should request student correction, record a neutral environment incident, or block/wait on another actor. A product owner must decide before changing this behavior or encoding it as the intended contract. This uncertainty does not block unrelated P3 validation.

Task115 changed only the evidence runner, JSON/screenshots and this report/status docs. The last full regression after Task114 remains the current code-suite result: Python 212 tests (211 passed, 1 skipped), Node 43/43, Workspace API 38/38, WSGI 11/11, frontend static 48/48; JS syntax, Python compileall, Harness/runners py_compile, Schema JSON and `git diff --check` passed. Task115's new runner `py_compile`, browser assertions and visual review passed; Task115 made no product-source change. The single Python skip remains Windows symlink-creation privilege, not symlink-safety evidence. Overall Gate PARTIAL; Commit: NONE.


## Task R0-P3-CROSS-STUDENT-WORKSPACE-WRITE-DENIAL-116 — verify foreign demo actor cannot mutate a workspace

A read-only cross-task authorization audit found that the existing test already denied reads and workspace start for a workspace whose stored demo actor differs from the fixed student route actor. It did not cover the other student mutation endpoints. Extended that same API test with pause, Agent turn, proposal decision, and submission attempts.

Evidence:

- `tests/test_workspace_api.py::test_student_reads_and_start_hide_workspace_owned_by_another_demo_actor_without_side_effects` publishes and starts a synthetic workspace as `student-demo`, snapshots its state, revision, submissions, events, submission counter and idempotency store, then changes its stored owner reference to `student-other`.
- GET workspace/latest submission/remediation/events and POST start/pause/Agent turn/proposal decision/submission all return the same `404 not_found` under the fixed student-demo route. The test confirms the attempted writes do not change state, revision, submission list/counter, event list or idempotency store. Restoring `student-demo` restores successful workspace read.
- A child-agent audit independently confirmed the common `_authorize_workspace` check is reached before workspace subroute dispatch. It noted the test verifies a fixed synthetic actor-reference comparison only; no real identity or authorization system exists.

Verification after this test edit: `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; Node client — 43/43; Workspace API — 39/39; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness and Tasks112–115 runner `py_compile`, and Workspace Schema JSON parse passed. `git diff --check` passed with existing CRLF-to-LF notices for README.md and docs/CURRENT_STATE.md. The sole Python skip is Windows symlink-creation privilege and is not symlink-safety evidence. Temporary AppContainer runner-path diagnostics printed during the full suite; it still exited 0.

Task116 changed only the API test. No browser run was needed for this server-side guard. This proves no more than the in-memory synthetic owner-reference check on these API routes. It does not prove real authentication, tenant isolation, assignment authorization or production access control. Overall Gate remains PARTIAL; no owner decision is required for this test-only result. Commit: NONE.


## Task R0-P3-C-TEACHER-EVENT-FAILURE-ISOLATION-117 — keep successful review data when only the event region fails

A read-only UI audit found that tests asserted event-local error handling in source, but no current browser run visibly proved that the teacher submission and multi-task queue remained usable during an isolated event read failure. Added a browser-only fault injection runner; no application source or test-suite code changed.

Browser evidence:

- Microsoft Edge via Playwright at 1280×900 opened the three-task `teacher-detail-delay` loopback Harness and explicitly selected task A. Playwright fulfilled one 503 for A's event GET at the browser boundary. All other requests, including the subsequent retry, reached the local in-memory WSGI API.
- During the injected event failure, A's submission details remained visible with its `SUBMITTED` state, and the A/B/C queue stayed visible with counts 1/1/0. Only the event region showed an unknown read state and its visible “重读事件” control.
- Clicking “重读事件” produced the second A events GET, which returned 200 and rendered three events. The review-queue GET count stayed 6 before and after that retry; the selected submission and its state remained unchanged. At both captured states `innerWidth=clientWidth=scrollWidth=1280`. Both screenshots were visually inspected.
- Browser-run JSON SHA-256 `316D03A4C67000379B9A3FE2E315C1EAF11F6790E43A8F7EA23963EA17265FF4`; unknown-state screenshot `A022FC521BE8213DD3B9A497E3E34CAA64B8A51CC8BE8498C68BBB0D35438AD9`; recovered screenshot `56996F7F3579B4F9F8E078B09771B3721184A196C6517245354522B589EFFFE0`; runner `20D158AAFFE9914AF87DCC09BBC1AB008F38D083CDF592A39122AA3653A54E79`. Files are under `browser-r0-p3-teacher-event-local-failure-117-2026-09-26/`.
- Initial exploratory runner attempts were excluded: first the Playwright route pattern missed the query-bearing URL; then the route was fixed but the unknown/recovered screenshots were captured after recovery. The final runner matches the URL path with query parameters, asserts both API statuses and queue-read counts, and captures screenshots at the correct states. These attempts made no product-source changes.

Final code regression after Task116 (Task117 changes only its Artifact runner/evidence): `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; Node client — 43/43; Workspace API — 39/39; WSGI — 11/11; frontend static — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Harness and Task117 runner `py_compile`, and Workspace Schema JSON parse passed. `git diff --check` passed with existing CRLF-to-LF notices for README.md and docs/CURRENT_STATE.md. The sole Python skip is Windows symlink-creation privilege and is not symlink-safety evidence; temporary AppContainer runner-path diagnostics printed during the successful full suite.

This is a finite browser check against a local synthetic Harness. The 503 was injected between the browser and local API; this is not evidence of a real network or production HTTP outage. No owner decision is required. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-TEACHER-EXPLANATION-EVIDENCE-RECEIPT-LOSS-118 — verify the two specified review variants after browser receipt loss

A read-only action-variant audit found API coverage for `REQUEST_EXPLANATION` and `REQUEST_EVIDENCE`, but no browser run had observed their UI-specific receipt-loss/readback path and student-facing result. Added one parameterized browser evidence runner for tasks A and B. No application source or test-suite code changed.

Browser evidence:

- Microsoft Edge via Playwright at 390×844 used the three-task `teacher-detail-delay` local in-memory Harness. The teacher explicitly selected A and chose `REQUEST_EXPLANATION`, then explicitly selected B and chose `REQUEST_EVIDENCE`, each with a concrete synthetic reason. For each POST, Playwright observed local API HTTP 201 and aborted only the response to the browser.
- The existing teacher UI confirmed both uncertain writes by API readback. Exactly one review POST was sent for each task; readback matched action IDs `review-2` and `review-3`, the requested kind and reason, one OPEN remediation and one `review.action_recorded` event per write. After A's decision A showed 0 pending and B remained 1; after B's decision both A and B showed 0, with C unchanged at 0.
- The student then explicitly selected A and B in turn. A showed the `REQUEST_EXPLANATION` reason; B showed the `REQUEST_EVIDENCE` reason. Both currently surface as `FEEDBACK_REQUIRED` / “等待你补正”. This records the present shared state wording; the run does not establish that the two actions should have identical guidance or completion language. The 390px client width equaled document scroll width for both selections.
- Browser-run JSON SHA-256 `BA24FFC9A68AE610304CD5213B1DCBA5F19F46C003821F63A48D9563AE8A9FC5`; teacher screenshot `7E3788769FA1A33D2A5346E799A7FF13343439B750E73B5A5E1A94347FFDBFF9`; A student screenshot `F944B160D20CADD51825C4A5F483AB6986C1218FA18366CFAFBA44BF67E78C49`; B student screenshot `843B4F7C8EDD791124D32DB0DC0C1EF20BB5895522BB9D128F27551597CCF719`; runner `E6350856783B8A797FE71A367355EF32AD1D38761C44CF602186D652A914FC3D`. Files are under `browser-r0-p3-teacher-review-variants-receipt-loss-118-2026-09-26/`. All screenshots were visually inspected.

Task118 runner `py_compile`, browser assertions, API state/event readback, and visual review passed. The complete code suite last ran after Task117's evidence-only change: Python 213 tests (212 passed, 1 skipped), Node 43/43, Workspace API 39/39, WSGI 11/11, frontend static 48/48; syntax, compileall, Schema JSON and diff checks passed. Task118 changed only its Artifact runner/evidence, so no application/test source changed after that regression. The only Python skip is Windows symlink-creation privilege and is not symlink-safety evidence.

This is finite browser evidence against a local synthetic WSGI Harness. The API committed each action in process memory before Playwright aborted its browser response; it is not a real HTTP outage, durable recovery, production authentication or live teacher/student data. No owner decision is needed to record this result; any later change to distinguish student-facing meaning or wording must follow the relevant product decision boundary. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-C-TEACHER-HISTORY-REMEDIATION-OVERLAP-119 — keep history and remediation failures isolated while their requests overlap

A read-only audit found that separate tests and browser evidence covered teacher history failure, remediation failure, event-local failure and multi-task queue isolation, but did not show history and remediation refreshes failing in overlapping requests on the same page. Used the existing `teacher-history-retry-delay` Harness profile plus one-shot browser-boundary remediation failures; no application source or Harness source changed.

Browser evidence:

- Microsoft Edge via Playwright at 1280×900 opened the three-task synthetic teacher page. A's initial review-history GET returned the Harness 503; Playwright fulfilled a one-shot 503 for A's initial remediation GET. The task queue remained A/B/C = 1/1/0.
- The teacher started a history refresh. The existing Harness delayed A's second history GET and then returned 503. While that request was still pending, the teacher retried A's remediation read; Playwright fulfilled a separate 503. The history area remained in its own loading state, the remediation area independently remained unknown with its own retry, and the task queue remained unchanged.
- After the history request completed, its A error remained visible while the remediation area remained independently retryable. Retrying remediation then let the local API return 200; the remediation region recovered and preserved C's existing remediation, while A's history error and history rows remained unchanged. The remediation retry did not issue another history or queue GET. All four captured states measured `innerWidth=clientWidth=scrollWidth=1280`; all screenshots were visually inspected.
- Browser-run JSON SHA-256 `14F6D7860D215A8F340C9908CEA740AF23441B5D4C9EA88BA41B3E46AAE0BCAC`; pending-overlap screenshot `AFB1EA31E6E34507B1B48C54504D0BC2D70FB6426E77881832E8B740B04127E3`; both-unknown screenshot `AF70B4175F1BE1F20429F3853D7EB2E10FEB285D43FB6B0ED7AC9DDAD2E848F3`; remediation-recovered screenshot `CD8CBDC5B18A16D8824E0CA508CEC15B6CD4D5E8BC74E4DCB7192482828F02EE`; runner `583CE8D6DFC736D94F070AA9A446544084F718EA04C8EBB4126CAFDF651C117E`. Files are under `browser-r0-p3-teacher-history-remediation-overlap-119-2026-09-26/`.

Task119 runner `py_compile`, all eight browser assertions, response/read request counts and screenshot review passed. Task119 changed only its Artifact runner/evidence; no app/test source changed. The most recent full code regression remains Task117: Python 213 tests (212 passed, 1 skipped), Node 43/43, Workspace API 39/39, WSGI 11/11 and frontend static 48/48; Node syntax, Python compileall, Harness/runner compile, Schema JSON and `git diff --check` passed. The single Python skip is Windows symlink-creation privilege and is not symlink-safety evidence.

This is a finite synthetic browser-fault check at the browser/API boundary, not a production outage or service guarantee. No owner decision is needed. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-121 — run the current P3 synthetic workflow over an actual loopback HTTP socket

A read-only startup audit found that the repository's older `run_local_web.py` serves the earlier Gate A API, while the current P3 `WorkspaceWsgiApp` has no standalone launcher. The active local-demo ADR limits the prototype to loopback and synthetic in-memory data. A task-specific runner therefore starts the current WSGI app on an ephemeral port explicitly bound to `127.0.0.1`; it does not change the product entry point or add a general-purpose server command.

Evidence:

- The runner verified the server's bound address with `server_address` and the open socket, then sent 22 requests through Python's HTTP client to the WSGI server: health, both allowlisted page assets, teacher assignment create/publish, stale publish and readback, student directory/read/start, allowlist snapshot submit and an identical idempotent replay, teacher queue/workspace/review, student remediation/read/resubmit, teacher ACK, student latest submission and evidence events.
- Every check passed. A stale publish returned 409 and readback stayed DRAFT with no Workspace. Replaying the same first submission returned its original ID and left exactly one item in the review queue. The remediation reason matched its review action; the corrected submission was version 2; ACK was visible as `ACCEPTED`; six or more evidence events were readable. Writes carried idempotency keys and revision preconditions except initial assignment creation, which has no prior revision to compare. Execution remained disabled.
- The service used a fresh `WorkspaceApi` process-memory store and fixed `orders-audit-v1` fixture. The fixture's Python file was read only as text and never executed. No external call was made. The server thread was joined and its listener socket closed before the runner exited; the selected ephemeral port had no remaining listener.
- Final post-fix Artifact JSON SHA-256: `071696C3BBE7291052775CF4CEA3E83F4DD140F1CBCEE5BA67AC79772AFA0C41`; runner SHA-256: `C595E60B2AF2090FAC49B4AAC2EDEF7EC7A7E2DFFC655BDBAB2463400A473AF5`. Both files are under `browser-r0-p3-loopback-http-smoke-121-2026-09-26/`.

Verification after Task121: `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 43/43; `python tests/test_workspace_api.py` — 39/39; `python tests/test_workspace_wsgi.py` — 11/11; `python tests/test_workspace_frontend_html.py` — 48/48. Student/teacher/client `node --check`, `python -m compileall -q apps tests`, Task121 runner `py_compile`, active Schema JSON parse and `git diff --check` passed. The sole Python skip remains Windows symlink-creation privilege and is not symlink-safety evidence. The AppContainer helper printed temporary runner-path diagnostics during the full test suite; the suite still exited 0.

This is actual local HTTP transport evidence for the synthetic WSGI adapter, not a browser session against that socket, production service integration, external network deployment, persistence, real identity or authorization proof. Fixed demo URL roles remain test fixtures. No owner decision is needed for this bounded acceptance check. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-122 — complete the P3 teacher/student loop in a browser over loopback HTTP

The independent selector and risk audit found the current pages can share one process-local `WorkspaceApi` through a loopback-only WSGI server. The Task122 runner bound an ephemeral `127.0.0.1` port, launched Microsoft Edge with Playwright, and exercised the current teacher and student pages against the same in-memory store. No browser request left that loopback origin.

Browser evidence:

- Teacher created and published a fixed synthetic task in the page. Student explicitly selected it, the page started its Workspace, and the student submitted a bounded allowlist text snapshot (version 1). Teacher selected the task and requested `REQUEST_REMEDIATION`; student reloaded, explicitly reselected the task, saw the matching reason, and submitted version 2. Teacher then requested a second remediation specifically against version 2. Student saw that current request and submitted version 3. Teacher explicitly selected version 3 and acknowledged it. Student reloaded and explicitly reselected again; the page showed `ACCEPTED` / “本轮已结束”.
- All 23 browser assertions passed. Final API state was `CLOSED`, three submissions, and three review actions. The first remediation remains `RESPONDED` and linked to submission 2; the second is `CLOSED` and linked to submission 3. Teacher UI showed both records with those separate states. This confirms ACK does not rewrite the older response association. Other checks covered disabled code execution, idempotency/revision headers, loopback-only requests and no horizontal overflow at student 390px / teacher 1280px. There were 110 loopback HTTP requests. Five screenshots were visually inspected. Server thread stopped and socket closed.
- Final Artifact JSON SHA-256: `303F85D73B5D446870755D69627E7A54440DDD9E5E4127951959F29FF92CEE1A`; final runner SHA-256: `75E42DF7D9EB0971CDF888322CC2478B6F4EAC6C9F8DDFA611AA657D69025A60`. Screenshots: `student-selected-started-390px.png` (`0E672D755089DF53905985100902CB0D5F6841BE880EB9C9F5792CBE1F591E4F`), `teacher-remediation-confirmed-1280px.png` (`8C26032E7EE1518D1D2510EC7320970DCE197CB6EFBF8E73411E96A630427BD6`), `student-remediated-resubmitted-390px.png` (`7B324833A8817D44C948DA5389C64C19D80435AA9E67C49CC4BB3C0272BD91DC`), `teacher-acknowledged-1280px.png` (`33AF44A482B3B484637A4F04FF585C14EAA1FF5554B76457B395D5C14C477B0F`), and `student-closed-state-390px.png` (`A791210FF497BF4E31FBF13F563C90B866C3BCAB1FFCD58BD801DACDB9917CE0`). Files are under `browser-r0-p3-loopback-http-browser-122-2026-09-26/`.

The first browser cycle exposed a state gap: after ACK, the Workspace was CLOSED and the latest Submission ACCEPTED, but its responded remediation remained RESPONDED. This conflicted with the current product flow's “认可并关闭” action and the wire contract's `CLOSED` remediation state. `workspace_api.py` now closes only RESPONDED remediation records whose `response_submission_id` matches the submission being acknowledged; `test_workspace_wsgi.py` asserts both CLOSED and that matching submission reference. A second browser cycle then confirmed the boundary: ACK of version 3 closed the remediation answered by version 3 while retaining the earlier remediation as RESPONDED and linked to version 2. The independent state-transition audit agreed this is the narrow evidence-linked behavior supported by the workflow and DTO.

Verification after the fix: `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 43/43; Workspace API 39/39; WSGI 11/11; frontend static 48/48. Node syntax for student, teacher and shared client, Python `compileall`, Task121/122 runner `py_compile`, Schema JSON and `git diff --check` passed. The sole skip is Windows symlink-creation privilege, not symlink-safety evidence. Temporary AppContainer runner-path diagnostics appeared during the successful suite.

This is finite R0 synthetic, in-memory HTTP+browser evidence, not production service, identity, persistence or code-execution proof. Teacher/student routes remain fixed demo role fixtures. The bounded test used only `REQUEST_REMEDIATION` and `ACKNOWLEDGE`; unconfirmed student-facing meanings for `ENVIRONMENT_ISSUE`, `REQUEST_EXPLANATION` and `REQUEST_EVIDENCE` remain outside the pass claim. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-125 — observe student submit uncertainty after a full page reload

The read-only UI audit found that the same-page retry preserves the immutable submission DTO and client idempotency key, while a full reload clears both in-memory attempts. The latest-submission panel already carries an explicit caveat that a latest record cannot prove it belongs to a particular request whose receipt was unknown. This task checks that boundary in the real browser without changing product behavior or adding persistence.

Browser evidence:

- Microsoft Edge via Playwright used a fresh local in-memory `WorkspaceApi` served by WSGI on an ephemeral `127.0.0.1` port. Teacher created and published a fixed synthetic task; student explicitly selected and started it. On the submission POST, Playwright let the API process the request (HTTP 201 and `submission-1` stored), then aborted only the browser response.
- Before refresh the student saw “提交结果暂未确认” and the same-page “重试同一提交” control. The screenshot records the open submission dialog. The runner only asserts this label; it does not click the retry or claim that this task rechecked key/body replay semantics.
- After full reload, the task picker was empty and the page issued no second submission POST. The student explicitly selected the task. The page showed the latest `submission-1` / version 1 and its existing warning: “不能证明某次回执未知的提交请求就是这条记录”. The workspace displayed “等待教师复核”; the normal submission entry was disabled. API postconditions were one stored submission, state `REVIEW_REQUIRED`, revision 4. The reload view had no horizontal overflow at 390px.
- Ten browser/API assertions passed; 32 loopback page/API request records were retained. The sole submission POST record includes method, route, body, `If-Match`, idempotency key, upstream API status, submission ID, and explicit `response_dropped_after_server_commit` marker. Server thread stopped and socket closed. No external requests, real identities/data/models, filesystem writes or code execution were used.
- Screenshots were visually inspected: `before-refresh-unknown-390px.png` SHA-256 `BBC694BCBB8E083B3599A274EEAEE5B0820EAF25AA3067997A641E18BCAB1D10`; `after-refresh-explicit-readback-390px.png` SHA-256 `13A696A9FA68B809624AA761615C9262AE1B7CA3BAB589A7A472B6D1FFEC4BC2`. JSON SHA-256 `1BC9646666825481355EFD691694277E28217B49529723C234944D579AD50CF1`; runner SHA-256 `96BA3C5BD4F5A76D6ED8958A45ED3A7F9707E79E96AC543A34DF4634BB6E6DC8`. Files are under `browser-r0-p3-student-submit-reload-uncertainty-125-2026-09-26/`.
- Independent read-only artifact review found the runner, JSON and screenshots consistent. The evidence supports only this committed-before-reload path. It does not verify a server-side non-commit followed by reload, an unavailable latest-read after reload, or same-page retry key/body equivalence in this task. No new idempotency key was minted because no post was sent after reload; this is not a general key-lifecycle claim.

Verification after Task125 (no product/test-suite source changes): `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped; Node client — 43/43; Workspace API — 39/39; WSGI — 11/11; frontend static — 48/48. Student, teacher and shared client JS syntax, `python -m compileall -q apps tests`, Task125 runner `py_compile`, Workspace Schema JSON parse, and `git diff --check` passed. The single skip is Windows symlink-creation privilege and is not symlink-safety evidence; AppContainer runner-path diagnostics appeared during the successful full Python suite.

Task125 changed only its browser evidence runner/JSON/screenshots and this rolling report plus current entry/state documents. It confirms the current UI's explicit uncertainty caveat and non-repetition on refresh when the API has committed. It does not resolve whether pending write identity should persist across refresh; that would alter storage/privacy behavior and remains a separate product decision if pursued. Overall P3/P4 remains PARTIAL; Commit: NONE.


## Task R0-P3-126 — verify pre-commit submission failure and isolated latest-record retry

The next branch tested an interrupted submission that never reached the API, followed by an isolated failure reading the latest submission after page reload. A read-only UI audit confirmed the latest-record region has its own unknown state and retry button, while Workspace state is loaded separately.

Browser evidence:

- Microsoft Edge via Playwright used a new ephemeral loopback WSGI server and fresh in-memory API. After explicit student task selection/start, the runner aborted the first submission POST before calling `route.fetch`; API state remained `IN_PROGRESS` with zero stored submissions. The page did not report a successful submission; it kept an unknown-result message and same-page retry control.
- The student refreshed; no task was auto-selected and no second submission POST occurred. After explicit reselection, the runner returned one synthetic HTTP 503 only for `GET .../submissions/latest`. The latest-submission region alone showed “最近提交读取失败，当前状态未知” and “重新读取提交记录”; the separate Workspace state remained “进行中”.
- The student clicked that region's retry. It returned HTTP 200 with an empty submission result; the UI changed to “本机合成 API 当前没有提交记录”. Workspace stayed `IN_PROGRESS`, revision 3, with zero submissions and no additional POST. Ten assertions passed; request trace contains 36 entries including the one aborted-before-API action and one browser-boundary 503. The 390px view had no horizontal overflow; the loopback server thread and socket closed.
- Screenshots were visually inspected: `precommit-and-read-failure-390px.png` SHA-256 `A0AE3B5D9264B969839A7A8B7268144CE4ACE240D475F58ADCB5B4A8C9ADA8C0`; `latest-read-failed-390px.png` SHA-256 `869D559BCC6EAFA0B64B4FD7DB41F07933AC1E4B682879FB0DC372A24ABB6792`; `latest-read-recovered-empty-390px.png` SHA-256 `AEA40C63BE38DF922AB0A922B9FEBB3EBBE4CDC6AF10055DB39C1A224CF4EF4C`. JSON SHA-256 `B6A423A427446D3292746CC8C4F471E46C27E5644A8E879D838733C870064E5A`; runner SHA-256 `0039B180281A9124349A5A98693E42238AFD641DA703977DDC20643F4FCC55D9`. Files are under `browser-r0-p3-student-submit-no-commit-read-failure-126-2026-09-26/`.
- This is boundary injection between browser and local API, not a real network outage. It verifies the API never received the submitted bytes in this run, but does not prove how a remote server can disambiguate a write that committed while every later read remains unavailable. No retry POST was sent, and no persistent recovery state was added.

Task126 changed only its browser runner, JSON/screenshots and this rolling report plus current entry/state documents. Product and test-suite source did not change. Verification commands and results are recorded after the final suite rerun below. The product remains R0 P3/P4 PARTIAL; no owner decision is needed to record these observations. Any design to persist a pending write identity across refresh remains a separate storage/privacy choice. Commit: NONE.

Final verification after Tasks125–126 and documentation synchronization: `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 43/43; `python tests/test_workspace_api.py` — 39/39; `python tests/test_workspace_wsgi.py` — 11/11; `python tests/test_workspace_frontend_html.py` — 48/48. `node --check` for student app, teacher app and shared client passed; `python -m compileall -q apps tests` and `py_compile` for both Task125/126 runners passed; Workspace API Schema JSON and both browser-run JSON files parsed; `git diff --check` passed with only existing CRLF-to-LF notices for README.md and docs/CURRENT_STATE.md. The sole Python skip is Windows symlink-creation privilege and does not establish symlink safety. AppContainer temporary runner-path diagnostics printed during the successful full suite. No product source or test-suite file changed in Tasks125–126. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-127 — verify teacher publish recovery after the browser loses the write receipt

A read-only gap audit found no browser-boundary test for a publish POST that committed but whose response was lost; prior evidence covered task creation and review/submission writes. This run used the existing same-page retry flow without changing application code.

Browser evidence:

- Microsoft Edge via Playwright used a fresh ephemeral loopback WSGI server and in-memory API at 1280×900. The teacher created one fixed synthetic task. Playwright then called the local API for the first publish POST, observed its upstream HTTP 200, and aborted only that response before the page received it.
- The teacher page retained the named original task and showed “发布回执未确认”. The entire task form (inputs, textareas, selects and buttons), save-draft action, all new-task entries and the template entry were disabled; the only enabled task-write action was the original publish retry, with accessible name “重试原发布请求”. Before retry, the API had exactly one assignment in `PUBLISHED`, one bound Workspace, and one `assignment.published` event.
- The teacher clicked that original retry. The second publish request had byte-identical method, path and JSON body, the same `If-Match: 1`, and the same idempotency key. The page then showed the single confirmed published task card. Final API state remained one assignment, one Workspace (`workspace-1`), and one publish event. All nine assertions passed. The runner recorded all nine browser request starts, including the request whose response was aborted; every attempted URL used the local loopback origin and the 1280px view had no horizontal overflow.
- Screenshots were visually inspected: `publish-unknown-1280px.png` SHA-256 `16389262B5C05F573A24C82C13AEAAA66D2234D07D447161D7F488CF4DDD23AA`; `publish-recovered-1280px.png` SHA-256 `B1852630BFB2F45D1F71992D730E97D040093818F540A4039B0C5B0943BEDF24`. JSON SHA-256 `5CF3C186C17FB696AA5A12B7EB3137886F70F14577856D324AB12CB8A3B33D6C`; runner SHA-256 `28BCA62FA16625D1872FEE85D3DCA2C9A6B00180EA01B8147E97975AC612C2FC`. Files are under `browser-r0-p3-teacher-publish-receipt-loss-127-2026-09-26/`.
- This is a finite synthetic in-memory browser run. It does not test a real network outage, persistence, authentication, concurrent publishers, or production service behavior. No student data, external calls or code execution were used.

Task127 changed only its browser evidence runner, JSON/screenshots and this report/current entry documents. No product or test-suite source changed. Final verification after Task127 is recorded below. Overall R0 P3/P4 remains PARTIAL; Commit: NONE.

Final verification after Tasks125–127: `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 43/43; `python tests/test_workspace_api.py` — 39/39; `python tests/test_workspace_wsgi.py` — 11/11; `python tests/test_workspace_frontend_html.py` — 48/48. `node --check` for student app, teacher app and shared client passed; `python -m compileall -q apps tests` and `py_compile` for all three browser runners passed; API Schema JSON and all three browser-run JSON artifacts parsed; `git diff --check` passed with only existing CRLF-to-LF notices for README.md and docs/CURRENT_STATE.md. The sole Python skip is Windows symlink-creation privilege and is not symlink-safety evidence. AppContainer temporary runner-path diagnostics printed during the successful full suite. No product code or test-suite file changed in Tasks125–127. Overall Gate remains PARTIAL; Commit: NONE.


## Task R0-P3-128 — verify task-directory readback after a lost teacher publish receipt and full refresh

The next audit identified a distinct path from Task127: do not click the same-page publish retry; instead reload the teacher page and read the current task directory from the still-running process-local API.

Browser evidence:

- Microsoft Edge via Playwright used a fresh ephemeral loopback WSGI server at 1280×900. Teacher created a fixed synthetic task. The first publish was processed by the API (upstream HTTP 200), after which Playwright dropped only that browser-facing response. Before reload, the page retained the original task title and displayed “发布回执未确认”.
- The teacher page was fully reloaded. The directory GET count increased from 1 to 2; the publish POST count remained exactly 1. The directory showed exactly one card for the task marked `已发布 · 合成`. API state remained one assignment, one Workspace (`workspace-1`), one `assignment.published` event. Eight assertions passed; all 12 recorded browser request starts used the loopback origin; the 1280px page had no horizontal overflow.
- Screenshots were visually inspected: `publish-unknown-before-refresh-1280px.png` SHA-256 `0DA65ED76E58E26EC3F48F955D7733EBB465007E2C55D3896D178BF0C3C6E590`; `publish-read-back-after-refresh-1280px.png` SHA-256 `8466BDF620AC198CCB8FEE23671E81E2FAC826C6BFBCF1A9A787D3B30A9B295B`. JSON SHA-256 `5A59F1C20E4F0D741D1E7E0D573D06DEC7F750BA258079B7B01A98BD4C278179`; runner SHA-256 `DAE15CC5FD28A7C90EA69C887BFB876D4326E743A602DCD79687AA783A6F2AC8`. Files are under `browser-r0-p3-teacher-publish-reload-readback-128-2026-09-26/`.
- This verifies directory readback in the same still-running in-memory API process; it does not prove that a page reload can recover after server restart, data loss, or production service failure. The card reports current directory state; it does not establish causal identity between the card and the exact write whose receipt was lost. No retry publish POST was sent.

Task128 changed only its browser runner, JSON/screenshots and this report/current entry documents. No product or test-suite source changed. Final verification after Task128 is recorded below. Overall R0 P3/P4 remains PARTIAL; Commit: NONE.

Final verification after Tasks125–128: `python -m unittest discover -s tests` — 213 tests, 212 passed, 1 skipped, exit 0; `node --test tests/workspace-client.test.mjs` — 43/43; `python tests/test_workspace_api.py` — 39/39; `python tests/test_workspace_wsgi.py` — 11/11; `python tests/test_workspace_frontend_html.py` — 48/48. `node --check` for student app, teacher app and shared client passed; `python -m compileall -q apps tests` and `py_compile` for all four browser runners passed; API Schema JSON and the four browser-run JSON artifacts parsed; `git diff --check` passed (line-ending notices may appear for existing CRLF documents). The sole Python skip is Windows symlink-creation privilege and is not symlink-safety evidence. AppContainer temporary runner-path diagnostics appeared during the successful full suite. No product code or test-suite source changed in Tasks125–128. Overall Gate remains PARTIAL; Commit: NONE.
