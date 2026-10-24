# Teacher Create and Publish Retry Report

- Task ID: `R0-WORKSPACE-TEACHER-CREATE-PUBLISH-RETRY-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for bounded teacher create/publish recovery logic; overall UI/API integration remains PARTIAL**
- Commit: `NONE`

## Plain-language objective

If the teacher clicks create or publish and the page cannot tell whether the API received it, the page must not silently create a second task or say the task was published. It must remember the exact task contents and whether it was creating or publishing, then safely retry or read back that same task.

## Audit and implementation

Independent contract and code reviews identified two gaps: the teacher could edit or replace the task while retrying an older DTO, and a definite publish conflict discarded the already-created assignment so the next click could create another draft. The bounded correction keeps one page-memory `taskWriteAttempt` with the immutable create DTO, intended action, current phase, and assignment/revision when known.

- Unknown CREATE response: retain the original DTO and retry the create route with the same request body and Idempotency-Key. Do not start PUBLISH before CREATE has a valid receipt.
- Unknown PUBLISH response: retain the original assignment ID/revision and retry only that publish route with the same body, If-Match, and Idempotency-Key. Do not run CREATE again.
- While an attempt is unresolved: freeze task fields and new-task/template entry points; expose only the original action and show the original task title and current step.
- Definite PUBLISH 4xx/409: read the original assignment by ID. Confirm published state only when the returned assignment ID matches, its state is `PUBLISHED`, its Workspace is bound to that assignment, and code execution is false. If it is still `DRAFT`, retain that assignment and latest revision and wait for the teacher to click publish again. If readback fails or returns an unexpected state, retain the attempt and allow readback only; do not create or automatically republish.
- Definite CREATE rejection clears the attempt and restores editing. A confirmed write remains confirmed if refreshing the task list later fails.

The current product remains local synthetic and non-production. This is page/client-memory recovery only: reloading the page loses the unresolved attempt and pending client key. No persistence or cross-reload recovery policy was added.

## Files changed

- `apps/teacher-web/app.js`: added the create/publish attempt state, same-step retries, pending form freeze, publish conflict readback, and fail-closed recovery behavior.
- `tests/test_workspace_frontend_html.py`: added static state-path assertions for frozen content, original task/step, publish readback conditions, DRAFT revision refresh, readback-only recovery, and create rejection unlock.
- `tests/workspace-client.test.mjs`: added fetch-failure tests proving teacher create and publish retries preserve route, body, Idempotency-Key, and publish If-Match.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: updated current verification evidence and linked this report.

## Commands and results

- `node --check apps/teacher-web/app.js`: PASS.
- `node --test tests/workspace-client.test.mjs`: **17/17 PASS**; CREATE and PUBLISH response-loss retries checked for identical request identity.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py -v`: **5/5 PASS**; static source-structure evidence only.
- `python -m unittest discover -s tests -v`: **155 tests, 154 passed, 1 skipped**, exit code 0, 49.174 seconds.
- The single skip is Windows symlink creation denied with `WinError 1314`; it is not evidence of symlink safety.
- `node --check apps/student-web/app.js`, `node --check tests/workspace-client.test.mjs`, Schema JSON parsing, Python compilation, and `git diff --check`: PASS.

## Acceptance and remaining limits

| Check | Result | Evidence boundary |
| --- | --- | --- |
| Unknown CREATE retains and retries original task DTO | PASS | Client request fault injection plus static page-state assertions. |
| Unknown PUBLISH retries the existing assignment only | PASS | Static phase-branch assertion plus client request identity test. |
| PUBLISH conflict does not create a replacement task | PASS | Static assertion for original-ID readback and DRAFT retry-ready state. |
| Published state is confirmed only against original assignment and bound non-executing Workspace | PASS | Static condition assertion; no live API/DOM scenario was executed. |
| Unresolved attempt freezes editable task fields and new/template actions | PASS | Static source assertion; no browser interaction. |
| API validation/409 failures cannot be reported as a successful publish | PASS | Explicit error branch/readback conditions and static assertion. |
| Page reload recovers unresolved requests | NOT SUPPORTED | Attempt and idempotency keys are in memory only. |
| Browser rendering, live HTTP, multiple browser tabs, real users/data | NOT VERIFIED | No HTTP service, port, or browser was started. |

This task's P3 code and bounded tests are **PASS**. The broader UI/API integration remains **PARTIAL**; P4 visual QA has not been performed. The API and page use fixed demo roles, not authentication. The flow is local synthetic, process-memory-only, non-production, and never executes submitted code. Foundation Spike remains PARTIAL; the skipped symlink test does not close that gap.

## Collaboration and Git

The work was split among agents for implementation, independent contract audit, test authoring, and independent code review. The first review found form mismatch and publish-conflict context gaps; implementation was revised before the final regression run.

- Branch: `codex/r0-teacher-task-authoring`.
- Existing modified and untracked work was preserved. No staging, cleanup, reset, deletion, commit, push, deployment, server launch, or browser launch occurred.
- Commit: `NONE`.
- Next: continue static/direct-call review of teacher/student error paths; defer browser visual QA until there is a compliant preview path.
