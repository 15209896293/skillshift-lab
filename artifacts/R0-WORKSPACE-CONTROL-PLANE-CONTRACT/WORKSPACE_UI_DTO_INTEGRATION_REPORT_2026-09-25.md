# Workspace UI DTO Integration Report

- Task ID: `R0-WORKSPACE-UI-DTO-INTEGRATION-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PARTIAL** — code-level mapping and direct-call acceptance are in place; HTTP/browser integration remains unverified.
- Commit: `NONE`

## Scope and evidence boundary

This stage implements the requested teacher/student DTO calls against the bounded synthetic workspace API. The UI code calls a fixed `/api/v1/demo/{role}` path, uses the API's revision and idempotency headers, and treats only a valid API envelope as success. Tests use mocked `fetch` and direct WSGI calls. No HTTP service was started, no browser was opened, and no business port was opened.

The interfaces remain local synthetic prototypes. Demo paths are fixed presentation roles, not authentication. Assignment, workspace, submission, and artifact snapshot state exists only in the API process memory. Student edits remain in page memory. No model, real identity, real user data, host file path, ECS, deployment, or code execution was used.

## Changes

- `apps/workspace-client.mjs`: shared teacher/student API client; maps the teacher form, review actions, and allowlist text snapshots into wire DTOs; sends `Idempotency-Key` and `If-Match`; displays validation, conflict, and uncertain-receipt states. An uncertain write retains its key in the current page so an identical retry replays the same request.
- `apps/teacher-web/app.js`, `index.html`, `styles.css`: list/create/publish tasks through the API; load the current review queue; show exact API explanation, artifact text, byte size, SHA-256 and event sequence; require at least eight non-whitespace characters for every review action; display returned feedback and read back state after a publish error.
- `apps/student-web/app.js`, `index.html`, `styles.css`: discover published assignments; load/start the workspace; send scripted-demo turns and proposal decisions; submit only the three fixed logical text files; display the teacher's specific remediation reason; refresh workspace state after an uncertain submission. Code execution remains disabled.
- `apps/agent-first/agent_first/workspace_api.py`: remediation DTO now returns the teacher's reason; `QA_ONLY` no longer returns a file-change proposal.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`, `workspace-api-v1.schema.json`: describe the remediation reason and distinguish code-level wiring from HTTP/browser verification.
- `tests/test_workspace_api.py`, `tests/test_workspace_wsgi.py`, `tests/workspace-client.test.mjs`, `tests/test_workspace_frontend_html.py`: cover collaboration-mode behavior, remediation reason, the full direct WSGI synthetic loop, DTO mapping, mock-fetch headers/errors/idempotent retry, and static page selector/role markers.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, `apps/README.md`: update the current code-level integration status and keep the browser/runtime evidence boundary explicit.

## Commands and results

- Baseline before edits — `python -m unittest discover -s tests -v`: **142 tests, 141 passed, 1 skipped**, exit 0.
- Final Python suite — `python -m unittest discover -s tests -v`: **146 tests, 145 passed, 1 skipped**, exit 0, 46.550 seconds.
- `node --test tests/workspace-client.test.mjs`: **7/7 passed**.
- `node --check apps/workspace-client.mjs`, `node --check apps/teacher-web/app.js`, `node --check apps/student-web/app.js`: all passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: passed.
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py apps\agent-first\agent_first\workspace_wsgi.py tests\test_workspace_api.py tests\test_workspace_wsgi.py tests\test_workspace_json_schema.py`: passed.
- `git diff --check`: final check passed after the report and contract metadata were saved; exit 0, no whitespace errors.
- The one Python skip is the existing Windows symlink-creation test (`WinError 1314`); it is not evidence that symlink safety passed.

The direct WSGI test exercises create → publish → student catalog/workspace → start → submit allowlist snapshot → teacher review queue → remediation with reason → student resubmit → teacher acknowledge/close, then confirms a stale submission is rejected with `409 stale_revision`. This is direct in-process acceptance, not a running HTTP or browser test.

## Acceptance

| Check | Result | Boundary |
| --- | --- | --- |
| Teacher form and action DTO mapping | PASS | Mock-fetch/unit and server DTO tests; browser interaction not run. |
| Student task discovery and workspace DTO flow | PASS for synthetic service path | Direct WSGI and existing API tests; no network server/browser. |
| Allowlist contents and computed snapshot hash returned to teacher | PASS for bounded API behavior | API test verifies exact UTF-8 text, byte count and recomputed SHA-256; direct WSGI test verifies queue equality. |
| Teacher review explanation and student remediation reason | PASS for synthetic DTO | Reason now appears in the remediation response and strict schema. |
| Validation/conflict/unavailable states do not produce UI success | PASS in client tests and code paths | Includes `409 stale_revision`, schema rejection, network failure, and same-key retry; no browser QA. |
| Browser visual QA and live HTTP integration | NOT RUN | No compliant preview route was available; no alternate browser route or service was started. |
| Production readiness | NOT CLAIMED | Contract is Proposed; demo role is not auth; process memory only; no identity, persistence, or secure execution. |

## Hash evidence

The handoff value `9C4DAAE105B3DCD490BD18F3B9D6C64AF43ADF4D7EC8402D54193C38A1A6263B` was recomputed and matches the bytes of `WORKSPACE_ARTIFACT_SNAPSHOT_REPORT_2026-09-25.md`. It is the report file hash, not an individual submission snapshot hash. Snapshot content itself is not saved as a project file; API tests independently recompute each returned snapshot's SHA-256 from its UTF-8 bytes.

Final SHA-256 checks (2026-09-25):

| File | SHA-256 |
| --- | --- |
| `apps/workspace-client.mjs` | `A62A1A86A64C10F5F3AF38806F445E6C1D5F5F7A8C06B4B4791D0811368A4F63` |
| `apps/agent-first/agent_first/workspace_api.py` | `F6FEA2A90B329E4DC9BD69BEC4F5E1035F7D8C1ED068F80340A11C47FC15E841` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json` | `47D09FCA8051C9FD8D315ADD0B09BBB6AB1DF3BF6418BDB38DC1D81690F75288` |
| `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_ARTIFACT_SNAPSHOT_REPORT_2026-09-25.md` | `9C4DAAE105B3DCD490BD18F3B9D6C64AF43ADF4D7EC8402D54193C38A1A6263B` |

## Known limits and risks

- No browser/HTTP QA: relative module loading and same-origin API routing still need verification through a compliant preview path before claiming P4 runtime integration.
- The WSGI adapter still does not serve the static pages and must not be started or deployed as a product service.
- The fixture remains a candidate; the student page still contains a tested copy, and initial-file integrity is not a single shared source.
- Current-page idempotency keys are not persisted across a reload. The UI reads assignment/workspace/review state after load, but uncertain decisions without a readable current-state endpoint remain an integration limitation.
- No credentials scan was added in this stage. The contract's explicit credential-scan acceptance remains open.
- Foundation Spike remains PARTIAL; the symlink permission skip, OS-level isolation and code execution gates remain unchanged.

## Next

Continue synthetic-only code and contract work. Preserve the current `PARTIAL` classification until a compliant preview path exists for browser/HTTP verification. Revisit the fixed fixture as a shared source only after a scoped source/ownership review. No user decision is required for the current code-only test work.

## Git

- Branch: `codex/r0-teacher-task-authoring`.
- Existing dirty and untracked work was preserved; no cleanup, reset, commit, push, server launch, browser launch or deployment occurred.
- Commit: `NONE`.
