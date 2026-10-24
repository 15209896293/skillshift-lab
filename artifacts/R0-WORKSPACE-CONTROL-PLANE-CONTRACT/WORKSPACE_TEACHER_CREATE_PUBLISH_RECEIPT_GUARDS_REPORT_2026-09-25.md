# Teacher Create / Publish Receipt Guard Report

- Task ID: `R0-WORKSPACE-TEACHER-CREATE-PUBLISH-RECEIPT-GUARDS-001`
- Current Gate: P3 teacher/student synthetic API DTO wiring and failure-state evidence
- Result: **PASS for the client DTO guards, retry identity, and WSGI stale-publish path; overall product integration remains PARTIAL**
- Contract status: Proposed local synthetic API; process memory; non-production
- Commit: `NONE`

> Evidence snapshot note: this report records the teacher receipt-guard stage before the subsequent student latest-read race fix. Its client/test hashes and full-suite timing identify that earlier snapshot; the latest code/test hashes and final 172-test result are in `WORKSPACE_STUDENT_LATEST_READ_RACE_GUARD_REPORT_2026-09-25.md`.

## Read-only finding

A delegated independent review compared teacher `saveTask` recovery with the API/WSGI errors. Real create validation errors happen before the in-memory assignment is created; a stale publish returns `409 stale_revision`, leaving the assignment a draft. The teacher page has explicit branches for these failures and for unknown responses. No 4xx-to-success path was found.

The review did find a malformed-2xx DTO gap: CREATE accepted only `{id,state,revision}`, and PUBLISH did not validate full Assignment/Workspace DTOs or their relationship. A defective 2xx response could therefore have cleared the teacher attempt and appeared successful. The publish envelope also carries the Assignment revision, while the newly created Workspace begins at its own revision; the generic client revision check could reject a valid publish if both revisions were supplied.

## Changes

- `apps/workspace-client.mjs`
  - CREATE now requires a valid page-consumable Assignment DTO in `DRAFT` with no Workspace.
  - PUBLISH requires a valid `PUBLISHED` Assignment DTO and valid `ASSIGNED` Workspace DTO; the requested assignment ID, Workspace ownership and nested/returned Workspace IDs must agree; execution must remain disabled through the existing `isWorkspace` guard.
  - Write-envelope revision consistency now checks the field appropriate to the response: Assignment revision for publish responses, Workspace revision for Workspace writes, and explicit `workspace_revision` where supplied.
  - Invalid 2xx remains `invalid_response` / unknown outcome, preserving the pending idempotency key for same-request retry.
- `tests/workspace-client.test.mjs`: valid create/publish fixtures now match the strict wire DTOs. New fault-injection coverage rejects an incomplete create receipt and a publish receipt bound to another assignment, verifies both remain visibly unconfirmed, and verifies same-key/body/If-Match retry.
- `tests/test_workspace_wsgi.py`: adds direct-call evidence that stale publish gets 409/no-store, readback remains DRAFT with no Workspace, and a separate explicit publish using the current revision succeeds. The earlier vertical flow test includes scripted-demo collaboration, latest-submission reads and paged teacher review history.
- `apps/agent-first/agent_first/workspace_wsgi.py`: treats invalid non-string WSGI `REMOTE_ADDR` as a fail-closed 403 alongside invalid IP text.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, and `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: update the latest evidence pointer and limits.

## Commands and results

- `node --test tests/workspace-client.test.mjs`: **34/34 PASS**.
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **9/9 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **34/34 PASS**.
- `python tests/test_workspace_frontend_html.py`: **14/14 PASS**.
- `python -m unittest discover -s tests -v`: **172 total, 171 passed, 1 skipped; exit 0; 48.623 seconds**. The skip is the Windows symlink-creation permission case (`WinError 1314`); it is not symlink-safety evidence. Temporary copied-runner path diagnostics appeared in isolation tests and the affected tests passed.
- `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m py_compile apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_wsgi.py`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS** (schema unchanged by this task).
- `git diff --check`: **PASS for tracked changes**. New and previously untracked project code/artifacts do not appear in Git's tracked diff check; changed source, tests and docs were also checked for trailing whitespace.

## Acceptance and limits

| Acceptance | Result |
|---|---|
| Incomplete CREATE 2xx cannot be shown as saved | PASS; classified `invalid_response`, pending request identity retained |
| PUBLISH 2xx must identify the right published Assignment and its disabled-execution Workspace | PASS |
| Malformed 2xx retry preserves exact idempotency key, request body and publish revision | PASS in client fault-injection test |
| Actual stale publish is visible as 409 and leaves draft state unchanged until an explicit fresh-revision request | PASS through direct WSGI callable |
| Teacher UI state machine executed in a browser | NOT TESTED; static source assertions remain the UI evidence |
| WSGI served over an HTTP socket, loopback-only network binding, authentication or production authorization | NOT TESTED |
| Full schema validation of every response field | NOT CLAIMED; runtime guards cover the fields and relationships used by this page |

The test proves direct invocation of the WSGI adapter with an HTTP-shaped environ, not a live network server. Fixed URL demo roles are labels, not authentication. The API and retry keys are in process/page memory, with no persistence or reload recovery guarantee. No real data, credentials, model, ECS, business port, browser, deployment or code execution was used.

## SHA-256 evidence

Hashes are over current file bytes; recompute after any later edit.

| File | SHA-256 |
|---|---|
| `apps/workspace-client.mjs` | `A5206CB2AC12D59015648DCB77D9158574C7D7F9C6EF51D0EF256FA7127DF919` |
| `tests/workspace-client.test.mjs` | `9FFBA2AA04771A8F26383EFE7930B4A1452F4C0D4F2A3AA54F8F48421B44F6C5` |
| `apps/agent-first/agent_first/workspace_wsgi.py` | `704C2425C321CAC32627C6D81071E0B54E3E3DB4CC0F8AC66C0A4913C5757018` |
| `tests/test_workspace_wsgi.py` | `BB8B76D7A8A4FCD21C3498B8520E3F386E95F46DC9EF84F73C9E43B36E9E743A` |
| `README.md` | `79A43386C47FDC156E2E4DF5C4842850B30EFCF31E4F77880024E8B9CF7FD59A` |
| `docs/README.md` | `FECD4485EF1AF6A71870A6BFBDF8C18AC9BF4F8358FDADCA25A269C098D8AC54` |
| `docs/CURRENT_STATE.md` | `0E88147925E5576C8B2B7F63097810DAC70DE1662D7F953B955129AEF466A540` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `F94442EF6AA44107E72F8C95DBB13C171E52EDB362C82A3890E4EAAEE23B9AB9` |

The prior `WORKSPACE_WSGI_VERTICAL_READBACK_REPORT_2026-09-25.md` captured an earlier version of the vertical test at 8/8 WSGI and 171 Python tests. This report supersedes those test-file hashes/counts for the current checkout; the earlier report remains the evidence for its then-current snapshot.

## Git summary and next step

The checkout has extensive pre-existing modifications and untracked files. They were preserved. No file was staged, committed, pushed, deleted, reset or cleaned. `git diff --stat` covers only tracked modifications and omits most untracked project code. Commit: `NONE`.

Continue with the next bounded static/direct-call audit for student-side latest-submission and retry error handling, then review whether another UI state mismatch warrants a minimal regression. Browser/HTTP visual QA remains open and must not be bypassed.
