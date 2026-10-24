# Teacher Review History Readback Report

- Task ID: `R0-WORKSPACE-TEACHER-REVIEW-HISTORY-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for the covered review-history DTO, paging, role/error states and refresh UI; overall UI/API integration remains PARTIAL**
- Contract status: **Proposed local-synthetic extension; not an Accepted production API**
- Commit: `NONE`

## Objective and read-only audit

After `ACKNOWLEDGE`, the API changes the Submission state to `ACCEPTED`, so that item disappears from the teacher review queue. The `ReviewAction` remained in the process-memory workspace, but no teacher GET returned it; workspace events contained only a resource reference, and remediation did not include ACK. A teacher reload therefore could not see the recorded action. Three parallel read-only audits confirmed the gap and bounded its security scope before implementation.

## Proposed extension

The Proposed route is `GET /api/v1/demo/teacher/assignments/{assignment_id}/review-history?after_sequence=n&limit=n`. It requires the fixed teacher-demo role plus a published assignment and its workspace, returns a uniformly masked `404 not_found` for a student role or unavailable resource, and pages 1–50 existing ReviewActions by server `created_event_sequence`. Its response contains only action ID, submission ID/version, kind, reason, and event sequence; it never includes submission text, snapshots, or student explanation. Empty history is an explicit successful empty page. Reads do not change workspace revision/events.

This adds no storage or retention. It does make existing review reasons readable again to the fixed teacher demo route. The fixture cannot prove real teacher-to-assignment authorization: production identity, ownership, tenancy, retention, and deployment are still undefined.

## Changes

- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: records the route as a Proposed synthetic extension and states that a visible historical ACK does not identify a particular request whose write receipt was previously unknown.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json`: adds strict `ReviewHistoryData` pagination and makes `created_event_sequence` required on the `ReviewAction` response DTO.
- `apps/agent-first/agent_first/workspace_api.py`: implements teacher-demo-only published-assignment history reads, strict cursor/limit validation, ordered pages, a field allowlist, and no revision/event writes.
- `apps/workspace-client.mjs`: adds `reviewHistory(assignmentId, afterSequence=0, limit=50)` with fixed teacher-role enforcement, bounded page validation, exact action fields, ordering/cursor checks, and visible HTTP/network errors.
- `apps/teacher-web/app.js` and `apps/teacher-web/index.html`: display history for published assignments separately from the active review queue and remediation list, render action metadata with `textContent`, show empty/error/unknown distinctly, offer retry and “load more,” and never use history to confirm a lost ACK request.
- `apps/teacher-web/app.js`: review history and the full queue load path use request generations; stale async responses cannot replace newer remediation, queue, snapshot, timeline, count, or history UI.
- Tests: `tests/test_workspace_api.py`, `tests/test_workspace_json_schema.py`, `tests/workspace-client.test.mjs`, and `tests/test_workspace_frontend_html.py` cover API and schema pages, role/resource denials, empty/ACK/non-ACK history, cursor/no-duplicate behavior, no read side effects, DTO/error handling, page failure/paging states, and stale-request guards.

## Commands and results

- `python -m unittest discover -s tests -v`: **171 total, 170 passed, 1 skipped; exit 0; 48.661 seconds**.
- `node --test tests/workspace-client.test.mjs`: **33/33 PASS**.
- `python tests/test_workspace_frontend_html.py`: **14/14 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py`: **34/34 PASS**.
- `python -m unittest discover -s tests -p test_workspace_json_schema.py`: **8/8 PASS**.
- `node --check apps/student-web/app.js`; `node --check apps/teacher-web/app.js`; `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `python -m py_compile apps/agent-first/agent_first/workspace_api.py apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_api.py tests/test_workspace_json_schema.py tests/test_workspace_wsgi.py`: **PASS**.
- `git diff --check`: **PASS for tracked changes**; changed source/spec/test files are untracked in this existing checkout and have separate SHA-256 entries below.

The single skipped full-suite test is the Windows symbolic-link-creation case (`WinError 1314`); it is not symbolic-link safety evidence. Synthetic isolation probes emitted temporary copied-runner path diagnostics and passed. No student project was executed.

## Acceptance and limits

- Teacher can read paged ReviewAction metadata after ACK removes the Submission from review queue: **PASS in direct API, schema and client tests**.
- Student/missing/draft/no-workspace reads return the same 404 shape: **PASS in API tests**.
- History pages do not expose Submission snapshots/explanation and do not mutate revision/events: **PASS in API/schema tests**.
- Empty history, API failure, paging, and stale async results remain visible/truthful in the teacher source: **PASS for static source assertions, not browser interaction**.
- A historical ACK is the exact result of a particular pre-reload unknown write: **NOT CLAIMED**. Browser storage and persistent idempotency correlation were not added.
- HTTP/browser interaction and visual QA: **PARTIAL / not run** under the preview boundary.

## Hashes

SHA-256 is over the current file bytes; re-run `Get-FileHash -Algorithm SHA256` after any later edit.

| File | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_api.py` | `9DFB8AD3E91948DC08E9E6633B16DDE3EE84ACAD497E389E00964D02FD28B644` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | `DAC669C550539A0BDED3CAA9A41F8DFCE569D7446037511C7124CB7A93ABAD96` |
| `apps/workspace-client.mjs` | `6BFD06D97DD8A7653A4FE131B232A37F89E3E4B6FF25F4AD1BB062EEB70E7CE0` |
| `apps/teacher-web/app.js` | `25CBA2529FCF4826D5B7DFDEF6E5FB8CEBF1EAE7F26BE15FE9C04B14823C90BC` |
| `apps/teacher-web/index.html` | `E5B03BC042E62DA6AF7D3074F5EF88486F7EFD4D480EACE972FAC0784E5661E5` |
| `tests/test_workspace_api.py` | `CE8986E4C14D83FDF384FFAA476B5F4067ADF2DE1B6A3D9500B0A0F16F13187E` |
| `tests/test_workspace_json_schema.py` | `567BDD57A54EA4B2C5A127FE275324DFAD4CAF7BF153125DC6C08150A4ED4BF8` |
| `tests/workspace-client.test.mjs` | `30A63A2DA285C7B14A8F40870E3F8A82DC3637E6B3653B4C5D7D9BAB4403DB3A` |
| `tests/test_workspace_frontend_html.py` | `F195C8AE8B4AD49BDDA90CD77AEADC251FA066BC4B0569B3A801921B757F43FB` |

## Risks and next step

The API remains process-memory-only and non-production. Fixed URL roles do not authenticate teachers or prove assignment ownership. The page’s pending write/idempotency attempt is still lost on reload; history is contextual evidence, not a request receipt. Continue bounded P3 DTO/error-state work; keep HTTP/browser/P4 visual QA deferred unless a compliant preview path is established. Real identity, data retention, deployment, real users, models, and code execution remain closed for this stage. No user decision is needed for the next synthetic-only step.

## Git summary

The checkout had extensive existing modifications and untracked assets before this task and they were preserved. No files were staged, committed, pushed, deleted, reset, or cleaned. Commit: `NONE`.
