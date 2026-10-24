# Workspace Read DTO Validation Report

- Task ID: `R0-WORKSPACE-READ-DTO-VALIDATION-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for read-receipt validation; overall UI/API integration remains PARTIAL**
- Commit: `NONE`

## Scope

The preceding response-schema task validated the API's response DTOs against the JSON Schema, and the browser client validated minimum receipts for writes. This bounded follow-up closes the corresponding client-side gap for successful read responses consumed by the teacher and student pages. It does not implement a general JSON Schema runtime.

All exercised inputs are fixed synthetic DTOs. No real teacher/student data, credentials, model, ECS, external network, business port, persistence, host path or code execution was used.

## Read-only preview-path audit

- `apps/agent-first/run_local_web.py` launches the legacy `LocalWebApplication`.
- `apps/agent-first/agent_first/local_web.py` serves allowlisted static files, but its API is under `/api/` and uses a different legacy contract.
- The current pages call `/api/v1/demo/{role}`. `apps/agent-first/agent_first/workspace_wsgi.py` adapts that current API but has no static asset route.
- Therefore no single existing entry serves the current pages and current API under the agreed boundary. Neither server was launched, and no browser was opened or alternate browser entry used.

This confirms the existing no-HTTP/no-browser limit; it does not block static, unit or direct-call work.

## Changes

- `apps/workspace-client.mjs`: added minimum shape validators for assignment/task, workspace, submission references and snapshots, remediation, and evidence-event DTOs. Read methods now validate task list/detail, review queue, workspace, remediation list and event page before returning data to the UI. Snapshot validation checks the UTF-8 byte count and recomputes SHA-256 with Web Crypto before the teacher page receives the DTO.
- `tests/workspace-client.test.mjs`: added coverage for valid read DTOs and rejection of malformed 2xx `data` for all six read families.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: states the scope and limit of the client-side read validation.
- `docs/README.md`, `docs/CURRENT_STATE.md`: record the current test count, read receipt coverage and verified preview-path gap.

## Commands and results

- Read-only source inspection with `Get-Content` and `rg`: confirmed the legacy/current route mismatch and that the current WSGI adapter serves API calls only. No launcher was run.
- `node --test tests/workspace-client.test.mjs`: **14/14 PASS**.
- `python -m unittest discover -s tests -v`: **152 tests, 151 passed, 1 skipped**, latest run exit 0, 47.656 seconds. The skipped Windows symlink test failed to create a symlink due to `WinError 1314`; this is not symlink-safety evidence.
- `node --check apps/workspace-client.mjs`, `node --check apps/teacher-web/app.js`, `node --check apps/student-web/app.js`: passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: passed.
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py apps\agent-first\agent_first\workspace_wsgi.py tests\test_workspace_api.py tests\test_workspace_wsgi.py tests\test_workspace_json_schema.py`: passed.
- `git diff --check`: passed, exit 0.

## Acceptance

| Check | Result | Boundary |
| --- | --- | --- |
| Assignment list/detail reads reject malformed success DTOs | PASS | Minimum fields used by the UI; not full JSON Schema validation. |
| Review queue validates the submission and bounded snapshot structures | PASS | UTF-8 size and SHA-256 are recomputed from returned content. |
| Workspace, remediation and event reads validate page-facing DTO fields | PASS | Synthetic client mock tests; real HTTP not exercised. |
| Malformed 2xx read responses cannot reach page code as valid data | PASS | Mapped to `invalid_response`; visual behavior not browser-verified. |
| Current web preview path | NOT AVAILABLE | Legacy static/API path mismatches current `/api/v1` contract; current WSGI adapter is API-only. |
| HTTP/browser and visual QA | NOT RUN | No service, port or browser was opened. |
| Production readiness | NOT CLAIMED | Demo roles are not auth; page/API data is ephemeral; code execution remains closed. |

## Current phase

We are completing P3: code-level DTO mapping and error-state handling between the fixed teacher/student pages and the local synthetic Workspace API. The defined teacher-publish → student-discover/start/collaborate/submit snapshot → teacher-review/request remediation → student-resubmit path is covered by DTO/client tests and direct WSGI tests. P4 HTTP/browser runtime and visual QA remain unverified, so the overall integration is **PARTIAL**.

## Limitations and next step

- The two existing local web components cannot be combined by launching an existing compliant preview entry. A future preview integration would need a scoped implementation and review before any runtime QA; this report does not authorize opening a port.
- Client read validators cover the DTO structure and fields consumed by the current pages; they are not a general JSON Schema implementation. API JSON Schema tests remain the stricter wire-contract evidence.
- The starter fixture is still a candidate source while the student page holds an embedded copy. Do not choose a canonical source implicitly.
- No user decision is needed for the next synthetic-only static/unit/direct-call work. A runtime preview or any real identity/data/model/deployment/code execution change remains outside this authorization.

## Git

- Branch: `codex/r0-teacher-task-authoring`.
- Existing dirty and untracked files were preserved. This report and the edited source/test files remain part of the existing uncommitted workspace; no cleanup, reset, commit, push, server launch, browser launch or deployment occurred.
- Commit: `NONE`.
