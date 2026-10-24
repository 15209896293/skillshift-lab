# Workspace Uncertain Review Readback Report

- Task ID: `R0-WORKSPACE-UNCERTAIN-REVIEW-READBACK-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for review outcome readback; overall UI/API integration remains PARTIAL**
- Commit: `NONE`

## Scope

The teacher review page previously reloaded the queue after an uncertain write but could not distinguish a committed review with a lost receipt from an unresolved outcome. This bounded change adds an explicit API readback check for an unavailable/invalid write receipt. It does not make validation failures or version conflicts appear successful.

Only the fixed synthetic API and DTOs are in scope. No real teacher/student data, credentials, models, ECS, external network, persistence, port, browser or code execution was used.

## Behavior

- For `ACKNOWLEDGE`, the page reports a readback confirmation only when the same workspace is returned in `CLOSED` state.
- For remediation requests, the page reports confirmation only when the same workspace is `FEEDBACK_REQUIRED` and its open remediation matches the current submission ID, requested action kind, and exact reason sent by the teacher.
- A mismatch or failed readback preserves the original unavailable/unknown message. The confirmation path runs only when `errorStateFor` classifies the write as `unavailable`; 4xx validation and 409 conflict responses do not enter it.
- `getAssignment` and `getWorkspace` now reject a valid-shaped response that identifies a different resource than the requested ID.
- While a valid review action is in flight, the page disables the review buttons and retains the submission context captured at click time, so duplicate clicks cannot start competing readback flows against a replaced page context.

These are current fixed-demo state checks. They are not a production identity/concurrency guarantee.

## Changes

- `apps/workspace-client.mjs`: exported `confirmReviewOutcome` to perform exact readback checks and bound resource identity in assignment/workspace reads.
- `apps/teacher-web/app.js`: on unavailable review write receipts only, query current workspace/remediation state and display confirmation with the API-read reason only if it matches; otherwise retain the original error state.
- `tests/workspace-client.test.mjs`: added matching/mismatching remediation and closed/not-closed acknowledgement cases.
- `tests/test_workspace_frontend_html.py`: locks the unavailable-only guard and readback helper call into the teacher page wiring.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`: document behavior, scope, current tests and remaining runtime limits.

## Commands and results

- `node --test tests/workspace-client.test.mjs`: **15/15 PASS**.
- First static-test invocation `python -m unittest tests.test_workspace_frontend_html -v` failed at import (`No module named 'tests.test_workspace_frontend_html'`); no test ran. Correct repository invocation, `python -m unittest discover -s tests -p test_workspace_frontend_html.py -v`: **3/3 PASS**.
- `python -m unittest discover -s tests -v`: **152 tests, 151 passed, 1 skipped**, latest run exit 0, 48.445 seconds. The skipped Windows symlink test was blocked by `WinError 1314`; it is not symlink-safety evidence.
- `node --check apps/workspace-client.mjs`, `node --check apps/teacher-web/app.js`, `node --check apps/student-web/app.js`: passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`, `python -m py_compile ...` for the existing Workspace API/WSGI/schema test files, and `git diff --check`: passed.

## Acceptance

| Check | Result | Boundary |
| --- | --- | --- |
| Matching remediation readback confirms only exact current submission/action/reason | PASS | Unit tests use synthetic DTOs. |
| Acknowledgement confirms only a closed workspace | PASS | Unit tests cover `CLOSED` and non-closed states. |
| Duplicate teacher review clicks cannot start a competing in-flight action | PASS | Page disables review buttons and uses the captured submission context. |
| Conflicts and validation errors cannot enter success readback path | PASS | Static page guard plus existing client error-category tests. |
| Readback unavailable or mismatched | PASS | Helper returns false; UI retains original uncertain/error message. |
| Real HTTP/browser behavior | NOT RUN | No current integrated preview route; no service, port or browser started. |
| Production readiness | NOT CLAIMED | Fixed demo roles are not authentication; process-memory state; non-production. |

## Current phase

P3 code-level API/DTO connection and failure-state handling continues. The synthetic teacher-publish → student-discover/start/collaborate/submit → teacher-review/remediation → student-resubmit loop is covered at direct API/WSGI and client-test level. This readback behavior closes one uncertain teacher-write outcome; the total UI/API integration stays **PARTIAL** until an authorized compliant runtime/visual path is verified.

## Git

- Branch: `codex/r0-teacher-task-authoring`.
- Existing dirty and untracked work was preserved. No cleanup, reset, commit, push, server launch, browser launch or deployment occurred.
- Commit: `NONE`.
