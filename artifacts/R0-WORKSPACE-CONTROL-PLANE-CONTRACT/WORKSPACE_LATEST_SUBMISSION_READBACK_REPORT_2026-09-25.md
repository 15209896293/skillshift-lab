# Latest Submission Readback Extension Report

- Task ID: `R0-WORKSPACE-LATEST-SUBMISSION-READBACK-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for the bounded readback extension and covered failure/role paths; overall UI/API integration remains PARTIAL**
- Contract status: **Proposed local-synthetic extension; not an Accepted production API**
- Commit: `NONE`

## Objective

Allow the fixed student demo page to reread the latest complete Submission after a page reload, without adding browser storage or implying that the latest record proves a prior lost POST receipt. The endpoint reads the existing in-process synthetic record only.

## Read-only gap audit

The previous contract exposed POST submissions, student/teacher remediation reads, workspace state, events, and the teacher-only review queue, but no student Submission read. Workspace GET does not contain Submission DTOs. The student page therefore could see a workspace state such as `REVIEW_REQUIRED`, but could not identify the current submission ID, version, explanation, snapshot content, UTF-8 size, or SHA-256 after reload. The teacher queue cannot be reused because the student role is denied access. These facts were independently checked against the route table, API, client, page, schema, and role tests before implementation.

## Changes

- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: documents `GET /workspaces/{id}/submissions/latest` as a Proposed, student-demo-only local synthetic extension. It returns `{ "submission": null }` before a submission or one complete latest DTO; it does not return history or confirm that a lost request created that record.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json`: adds strict `LatestSubmissionData`, allowing only `null` or a complete `Submission` DTO.
- `apps/agent-first/agent_first/workspace_api.py`: adds the read-only route. It first applies the existing student workspace owner and published-assignment check, denies teacher role on this route with the same `404 not_found` as a missing workspace, returns a copy of the latest record, and does not mutate revision/events.
- `apps/workspace-client.mjs`: adds `latestSubmission(workspaceId)` and validates workspace binding, complete submission fields, allowlisted refs/snapshots, matching logical names and media types, UTF-8 byte count and SHA-256, and the complete supported post-review state enum.
- `apps/student-web/app.js`, `apps/student-web/index.html`: read latest on initial workspace load/reload, after successful submission, and after an unknown submission result. A separate status region shows empty, loading, latest record, or read failure/retry; it renders returned snapshot contents using text nodes and does not overwrite the editor. It explicitly says the latest record cannot identify a lost prior request.
- Tests: `tests/test_workspace_api.py`, `tests/test_workspace_json_schema.py`, `tests/workspace-client.test.mjs`, and `tests/test_workspace_frontend_html.py` add direct API, strict-schema, mock-fetch DTO/failure, and static page-state coverage.

## Commands and results

- `python -m unittest discover -s tests -v`: **166 total, 165 passed, 1 skipped; exit 0; 54.987 seconds**.
- `node --test tests/workspace-client.test.mjs`: **30/30 PASS**.
- `python tests/test_workspace_frontend_html.py`: **12/12 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py`: **31/31 PASS**.
- `python -m unittest discover -s tests -p test_workspace_json_schema.py`: **8/8 PASS**.
- `node --check apps/student-web/app.js`; `node --check apps/teacher-web/app.js`; `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `python -m py_compile apps/agent-first/agent_first/workspace_api.py apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_api.py tests/test_workspace_json_schema.py tests/test_workspace_wsgi.py`: **PASS**.
- `git diff --check`: **PASS for tracked changes**; source and test files remain untracked in this checkout, so their content is covered by syntax/unit checks and SHA-256 below.

The sole skipped full-suite test requires Windows symbolic-link creation permission (`WinError 1314`). It is not evidence that symbolic-link safety passed. Isolation probes may print a temporary copied-runner location diagnostic before passing; no student project was run.

## Acceptance and evidence limits

- Empty workspace returns a strict explicit `null`: **PASS**.
- Readback returns only the newest version and preserves full text snapshot, byte count, SHA-256, version, state, and event reference: **PASS in direct API/schema tests**.
- Feedback/accepted states remain readable; a teacher still uses the review queue: **PASS**.
- Teacher, missing workspace, wrong student owner, and unpublished workspace receive uniform `404 not_found`: **PASS in API tests**.
- Repeated GET does not change workspace revision or event count: **PASS in API tests**.
- Malformed/cross-workspace/mismatched snapshot DTOs, including media-type mismatch, are rejected by the client: **PASS in client mock-fetch tests**.
- Student page has distinct empty/latest/error states and keeps the latest record separate from the editor: **PASS for static source assertions only**.
- Identifying the latest returned record as the exact result of a prior unknown request: **NOT CLAIMED**. The page-memory idempotency key and attempt still disappear on reload.
- HTTP, browser interaction and visual QA: **PARTIAL / not run** under the stated preview boundary.

## Hashes

SHA-256 is over the current file bytes. Re-run `Get-FileHash -Algorithm SHA256` if any file changes after this report.

| File | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/workspace_api.py` | `2FCBCEF6C69CCF634D86EF59C3376B85B843EDFC509EF46840EBF7DD7CCBD7FE` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | `B5A80945F02BC382C985185E26A8AE0C7D1EB6A5673BAC7CE18746BA60C6BDF7` |
| `apps/workspace-client.mjs` | `6847E4FE535750AD6A27327C4407DF1284BEB06C63EC7C7DE15C34A752002FD8` |
| `apps/student-web/app.js` | `614ADD67D641D367DB1E994A39976706554F46BA6D38F2CD1907F2138DBAD7D4` |
| `apps/student-web/index.html` | `B010E00C23F5F77AB370E4B72114E072ACC37A5A93F0C16282AC8D91A74E2458` |
| `tests/test_workspace_api.py` | `CDE6A06758CF7EEBAC30CE4C9CEE43CA014C58FA6F9A5A450716B88DDC1B615D` |
| `tests/test_workspace_json_schema.py` | `C162AE32A169293A9AB427580B6AFB8A50904C22FAD3E56D82A4EA0591CD6AD0` |
| `tests/workspace-client.test.mjs` | `4685515CE3715E3A582947C4A232625A706AEAF0FAFE8F80D841669BA6722171` |
| `tests/test_workspace_frontend_html.py` | `FA9295353AFCE73B28BCFA5F2D0410E0F138E61B44CB78CE9E696FBCFAA63AB7` |

## Risks and next step

This remains a single fixed synthetic student fixture, fixed demo URL roles, and process-memory state. The extension is not production identity/authorization evidence, a retention policy, a review-history API, or a cross-reload idempotency receipt. Do not deploy it, connect real people or data, or use it as a real authorization boundary. Continue P3 error-state and DTO work in a bounded slice; browser/HTTP QA remains unrun, and code execution remains closed under its separate security Gate. No user decision is required for the next synthetic-only code/test step.

## Git summary

The repository already contains extensive user modifications and untracked assets; all were preserved. No files were staged, committed, pushed, deleted, reset, or cleaned. Commit: `NONE`.
