# Workspace UI Error Recovery and DTO Validation Report

- Task ID: `R0-WORKSPACE-UI-ERROR-RECOVERY-002`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for the covered client and page error paths; overall UI/API integration remains PARTIAL**
- Commit: `NONE`

## Objective

Keep teacher and student screens truthful when a write has an unknown receipt, a read fails, or an API returns a malformed success DTO. Retries must preserve the original action and request identity. This work is limited to synthetic in-memory behavior and does not establish browser, production, or security-boundary evidence.

## Changes

- `apps/student-web/app.js`: preserves the submitted Agent question while its receipt is unknown, blocks duplicate sends, and does not clear a newer question typed while the request is pending. Accepting a proposed edit freezes the relevant editor controls and applies the local preview only if the captured target content is still unchanged. Remediation reads now show a dedicated unknown/error status and a retry control instead of being hidden under a generic task-load error.
- `apps/teacher-web/app.js`: retains the exact review action, DTO, target submission, workspace revision, and page context when the write receipt is unknown. The reason and competing actions stay locked; only the same action can be retried. Queue refresh does not replace the pending target. A closed workspace alone no longer confirms an uncertain `ACKNOWLEDGE`; the original idempotent write must return its matching receipt.
- `apps/teacher-web/app.js`: refresh now also reads remediation records for every published workspace, so OPEN/RESPONDED records remain visible even when the review queue is empty. Failed reads are reported as unknown rather than an empty history; remediation rows show the response submission link when present.
- `apps/workspace-client.mjs`: accepts optional top-level write-envelope `revision` as allowed by the schema, but rejects it if invalid or inconsistent with a supplied workspace revision; each mutation validates the revision in its own DTO. Agent Turn, Workspace Start, proposal decision, Submission, and ReviewAction validators check the required fields consumed by the pages. Submission receipts must match the submitted workspace, explanation, allowlist names, and exact snapshot contents. Review receipts must match the selected submission version. `confirmReviewOutcome` does not treat `CLOSED` alone as proof of a particular acknowledgement.
- `tests/workspace-client.test.mjs`: adds fault-injection coverage for exact same-request Agent/review retries, malformed DTO rejection, missing start revisions, mismatched submission receipts, and remediation read failures. The current suite is 26/26 PASS.
- `tests/test_workspace_api.py`: verifies teacher-demo OPEN/RESPONDED remediation reads and response submission linkage, while retaining the student role boundary.
- `tests/test_workspace_frontend_html.py`: adds static source assertions for student pending-question, editor freeze and remediation states, teacher unknown-review locking, and teacher remediation history on empty queues/read failure. These are source checks, not browser interaction tests (11/11 PASS).

## Commands and results

- `python -m unittest discover -s tests -v`: **162 total, 161 passed, 1 skipped; exit 0; 52.149 seconds**.
- `node --test tests/workspace-client.test.mjs`: **26/26 PASS**.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py -v`: **11/11 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **29/29 PASS** (direct in-process API calls; no HTTP service).
- `node --check apps/student-web/app.js`; `node --check apps/teacher-web/app.js`; `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `python -m py_compile apps/agent-first/agent_first/workspace_api.py apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_api.py tests/test_workspace_json_schema.py tests/test_workspace_wsgi.py`: **PASS**.
- `git diff --check`: **PASS** for tracked changes. The source/test files in this worktree are untracked files, so their content is separately covered by syntax and unit checks.

The single skipped full-suite test attempts to create a Windows symlink and was skipped because the environment returned `WinError 1314`. It is not evidence that symlink safety passed. Several Windows isolation probe tests also emitted a temporary Python runner location diagnostic and then passed; no student project was executed.

## Evidence and boundaries

The client fault-injection tests verify request URL, method, body, `If-Match`, and `Idempotency-Key` on retry; they reject malformed 2xx write receipts rather than allowing the page to report success. Task-create success is tested with `data.revision` and no top-level `revision`, as the current response schema allows. Static page tests verify relevant guards are present, but do not reproduce real DOM timing. Client validation checks page-consumed critical fields; it is not a full runtime implementation of JSON Schema `additionalProperties: false`. Full response-shape checks remain API/schema test evidence. No HTTP server, browser, business port, real student/teacher data, credentials, model, ECS, deployment, or code execution was used.

The API and pages remain **local synthetic, process/page-memory staged, non-production**. Demo teacher/student roles are not authentication. An unknown teacher or student attempt is lost on page reload; browser persistence was not added. After a student submission with an unknown receipt, reload reads workspace/remediation state but does not retrieve the exact historical submission DTO. Exact cross-reload recovery remains open and must not be approximated by generating a new idempotency key. The teacher API also has no review-history read endpoint; therefore a standalone `CLOSED` workspace state cannot prove which acknowledgement caused it.

During source verification, `AGENTS.md`'s opening project-priority text still says to verify the local restricted-process Workspace before broad platform work. The Accepted `R0_AGENT_FIRST_DELIVERY_DECISION.md`, `R0_PROJECT_AGENT_WORKSPACE_DECISION.md`, and ADR-004 explicitly make local code execution a separate optional gate; the repository's own source hierarchy places those active decisions above `AGENTS.md`. This conflict is therefore resolved by the recorded hierarchy, not by treating the handoff summary as authority. Foundation Spike remains PARTIAL and code execution remains closed.

## File hashes

- `apps/student-web/app.js`: `FA2D0C7D86A83E153E4D531DAEE16E97367A6713499428097A407E8BE6CD1D95`
- `apps/teacher-web/app.js`: `B6ED3A5960C6219E684621F364F345F93CEF6104591C313D66BD7315940B0866`
- `apps/workspace-client.mjs`: `E87F92AF3DCCE5051826A9A4FE1DD80B0681826511ADD43B823A8941578CEE0A`
- `tests/test_workspace_api.py`: `B005877B75A83EEF2BBBC96752A45741546DAE5A3921B687EB40F411BEC7B6C1`
- `tests/test_workspace_frontend_html.py`: `C8AC6D13170B2EAA44E191F02534284ED8B226D99318D3156B089A72203B33CB`
- `tests/workspace-client.test.mjs`: `A12CBED06150ADF741A35000A689B3F285BEB620C4856238840705CF1C492986`

## Acceptance

- Exact retry identity and no duplicate student Agent send: **PASS for client fault-injection and static page assertions**.
- Student proposal-accept context safety: **PASS for static source assertions; runtime interaction unverified**.
- Remediation read failure is visible and retryable: **PASS for client error mapping and static page assertions**.
- Teacher unknown review write locks the original operation and uses the same request on retry: **PASS for client fault-injection and static page assertions**.
- Malformed write DTOs cannot be treated as success: **PASS for covered client fault-injection cases; extra-field rejection is not claimed by the client validators**.
- Teacher remediation history readback after refresh: **PASS for direct API and static source assertions; browser reload not exercised**.
- Complete synthetic Python suite: **161 PASS / 1 SKIP**.
- Browser/HTTP integration and visual QA: **PARTIAL / not run**.

## Next step and risks

Teacher remediation readback is now covered through the existing GET route. Exact student Submission DTO recovery after reload is still unavailable through the current route set. Audit whether a narrow, student-workspace-scoped latest-submission read can be added as a clearly Proposed local synthetic contract extension; do not add browser storage or imply production retention. Browser/HTTP visual QA remains deferred under the current execution boundary. No user decision is needed for the bounded contract audit.

## Git summary

The five code/test paths above remain untracked in this checkout; the shared tree also contains extensive pre-existing modifications and untracked assets that were preserved. No files were staged or committed. Commit: `NONE`.
